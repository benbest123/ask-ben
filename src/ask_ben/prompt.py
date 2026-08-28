"""Prompt assembly.

The system/user split here is chosen for prompt-cache behaviour, and the benefit
is **uneven across arms** -- which is the interesting part, and something an
earlier draft of the spec got wrong.

Retrieval arms put the volatile chunks in the user turn, because chunks vary per
query and would invalidate any cached prefix. But their system prompt is
instructions only, a few hundred tokens, which is below Anthropic's ~1024-token
minimum cacheable prefix. So the retrieval arms **cache nothing at all.**

The full-context arm is the opposite: the whole corpus is identical on every
request, so it sits in the system block behind a cache breakpoint and caches
cleanly at roughly a tenth of the input cost on a hit.

The consequence is counter-intuitive and the evaluation has to account for it:
prompt-stuffing looks expensive until you notice that it caches and retrieval
does not. `usage.cache_read_input_tokens` is the proof, and it is recorded per
call in `answer.py`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ask_ben.config import PROMPTS_DIR
from ask_ben.retrieve import Hit


@dataclass(frozen=True)
class PromptPayload:
    system: list[dict[str, Any]]
    messages: list[dict[str, Any]]


def load_prompt(version: str) -> str:
    path = PROMPTS_DIR / f"{version}.md"
    if not path.exists():
        raise FileNotFoundError(f"no prompt version '{version}' at {path}")
    return path.read_text(encoding="utf-8")


def render_context(hits: list[Hit]) -> str:
    """Label each passage with its chunk id.

    The id is what the model cites and what the citation check scores against,
    so the label is an interface rather than formatting.
    """
    return "\n\n".join(f"[source: {h.chunk.id}] {h.chunk.title}\n{h.chunk.body}" for h in hits)


def build_payload(
    version: str,
    hits: list[Hit],
    question: str,
    *,
    cache_corpus: bool,
) -> PromptPayload:
    """Assemble the request. `cache_corpus` selects which arm's layout to use."""
    instructions = load_prompt(version)
    context = render_context(hits)

    if cache_corpus:
        # Full-context arm: the corpus is byte-identical on every request, so it
        # goes in the system block behind a cache breakpoint and is billed at
        # roughly a tenth of input cost on a hit.
        system: list[dict[str, Any]] = [
            {"type": "text", "text": instructions},
            {
                "type": "text",
                "text": f"## Context\n\n{context}",
                "cache_control": {"type": "ephemeral"},
            },
        ]
        return PromptPayload(system=system, messages=[{"role": "user", "content": question}])

    # Retrieval arms: chunks vary per query, so they belong in the user turn.
    # Nothing here caches -- the instructions alone are under the minimum -- and
    # that is a measured finding rather than an oversight.
    return PromptPayload(
        system=[{"type": "text", "text": instructions}],
        messages=[
            {
                "role": "user",
                "content": f"## Context\n\n{context}\n\n## Question\n\n{question}",
            }
        ],
    )
