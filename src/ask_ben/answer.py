"""Orchestration: gate, generate, extract citations.

This is the only module that knows about both retrieval and Claude. Everything
below it is deliberately ignorant of the other half -- `retrieve.py` has never
heard of a prompt, and `prompt.py` has never heard of an API client.

There are two distinct ways a question ends up unanswered, and they are not the
same thing:

- **Gated.** The top retrieval score is below the threshold, so no API call is
  made at all and `refused` is True. Off-topic questions cost nothing, and
  hostile text never reaches the model.
- **Declined in prose.** The gate passed, the model saw the context, and decided
  the context did not answer the question. That is a generation outcome, it
  costs a request, and `refused` stays False.

Conflating them would make the refusal metric meaningless, because a system that
never gates would look identical to one that gates everything.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from ask_ben.config import (
    ANSWER_MODEL,
    DEFAULT_K,
    DEFAULT_PROMPT_VERSION,
    GATE_THRESHOLDS,
    MAX_ANSWER_TOKENS,
    MAX_QUESTION_CHARS,
    REFUSAL_TEXT,
)
from ask_ben.prompt import build_payload
from ask_ben.retrieve import Retriever

CITATION = re.compile(r"\[source:\s*([a-z0-9-]+)\s*\]")


class QuestionTooLongError(ValueError):
    """Raised when a question exceeds MAX_QUESTION_CHARS."""


class AnthropicLike(Protocol):
    messages: Any


@dataclass(frozen=True)
class Answer:
    text: str
    sources: list[str]
    refused: bool
    meta: dict[str, Any] = field(default_factory=dict)


def extract_citations(text: str, valid_ids: set[str]) -> list[str]:
    """Return cited ids in order of first appearance, dropping any that are not real.

    `valid_ids` is what was actually retrieved for *this* question, not the whole
    corpus. A model citing a real corpus id it was never shown has still
    fabricated the attribution, and rendering that as a working link would be
    worse than showing nothing -- it would look like evidence.
    """
    seen: list[str] = []
    for match in CITATION.finditer(text):
        chunk_id = match.group(1)
        if chunk_id in valid_ids and chunk_id not in seen:
            seen.append(chunk_id)
    return seen


def answer_question(
    question: str,
    *,
    retriever: Retriever,
    client: AnthropicLike,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    model: str = ANSWER_MODEL,
    k: int = DEFAULT_K,
) -> Answer:
    """Answer one question, or refuse before spending anything."""
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("question is empty")
    if len(cleaned) > MAX_QUESTION_CHARS:
        raise QuestionTooLongError(
            f"question exceeds {MAX_QUESTION_CHARS} characters ({len(cleaned)})"
        )

    hits = retriever.search(cleaned, k)
    top_score = hits[0].score if hits else float("-inf")
    # Thresholds are keyed by retriever because BM25 scores are unbounded and
    # cosine similarity is not. The full-context arm maps to -inf: it returns
    # every chunk by definition, so there is nothing for a gate to decide.
    threshold = GATE_THRESHOLDS.get(retriever.name, 0.0)

    base_meta: dict[str, Any] = {
        "retriever": retriever.name,
        "prompt_version": prompt_version,
        "model": model,
        "k": k,
        "top_score": top_score,
        "retrieved_ids": [h.chunk.id for h in hits],
    }

    if top_score < threshold:
        return Answer(
            text=REFUSAL_TEXT,
            sources=[],
            refused=True,
            meta={
                **base_meta,
                "gated": True,
                "input_tokens": 0,
                "output_tokens": 0,
                "cache_read_input_tokens": 0,
                "cache_creation_input_tokens": 0,
            },
        )

    payload = build_payload(prompt_version, hits, cleaned, cache_corpus=(retriever.name == "full"))
    response = client.messages.create(
        model=model,
        max_tokens=MAX_ANSWER_TOKENS,
        system=payload.system,
        messages=payload.messages,
    )

    text = "".join(block.text for block in response.content if block.type == "text")
    sources = extract_citations(text, {h.chunk.id for h in hits})

    return Answer(
        text=text,
        sources=sources,
        refused=False,
        meta={
            **base_meta,
            "gated": False,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            # The cache fields are what turn the caching asymmetry from an
            # assumption into a measurement. The retrieval arms should report
            # zero here forever; the full-context arm should not.
            "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0) or 0,
            "cache_creation_input_tokens": (
                getattr(response.usage, "cache_creation_input_tokens", 0) or 0
            ),
        },
    )
