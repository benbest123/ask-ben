"""Deterministic evaluation metrics.

Nothing here calls an API. That is the whole reason these are separated from
`judge.py`: they are free and repeatable, so they gate every pull request. The
judged metrics are neither, so they run on manual dispatch.

The split is on cost, not on importance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from ask_ben.config import EVALS_DIR

GOLDEN_PATH = EVALS_DIR / "golden.yaml"

# Bare-domain form too ("example.com"), since a fabricated reference does not
# have to be a well-formed URL to mislead a reader.
URL = re.compile(r"(?:https?://|www\.)[^\s<>\)\]\"']+|\b[a-z0-9-]+\.(?:com|uk|io|dev|org|net)\b")


@dataclass(frozen=True)
class GoldenQuestion:
    id: str
    question: str
    category: str
    expected: str
    must_cite: tuple[str, ...]
    reference: str | None


def load_golden(path: Path | None = None) -> list[GoldenQuestion]:
    raw = yaml.safe_load((path or GOLDEN_PATH).read_text(encoding="utf-8"))
    return [
        GoldenQuestion(
            id=entry["id"],
            question=entry["question"].strip(),
            category=entry["category"],
            expected=entry["expected"],
            must_cite=tuple(entry.get("must_cite") or ()),
            reference=entry.get("reference"),
        )
        for entry in raw
    ]


def recall_at_k(retrieved_ids: list[str], must_cite: tuple[str, ...], k: int) -> float:
    """Fraction of required chunks appearing in the top k.

    Returns 1.0 when nothing is required. An out-of-scope question has no
    correct chunks, and scoring it 0.0 would penalise the retriever for the
    absence of an answer that should not exist.
    """
    if not must_cite:
        return 1.0
    return len(set(retrieved_ids[:k]) & set(must_cite)) / len(must_cite)


def reciprocal_rank(retrieved_ids: list[str], must_cite: tuple[str, ...]) -> float:
    """1/rank of the first required chunk. Rewards getting it near the top.

    Recall says whether the right chunk was in the window at all; this says how
    far down. They disagree exactly when k is carrying a weak retriever, which
    is worth being able to see.
    """
    if not must_cite:
        return 1.0
    required = set(must_cite)
    for position, chunk_id in enumerate(retrieved_ids, start=1):
        if chunk_id in required:
            return 1.0 / position
    return 0.0


def citation_validity(cited: list[str], retrieved_ids: list[str]) -> bool:
    """True when every citation points at a chunk that was actually retrieved.

    Citing nothing is valid -- a correct refusal has no sources.
    """
    return set(cited).issubset(set(retrieved_ids))


def declined(refused: bool, sources: list[str]) -> bool:
    """Did the system decline, by either of its two routes?

    `refused` covers only the relevance gate. The model can also see the context
    and decide in prose that it does not answer the question, which costs a
    request and leaves `refused` False. Both are declines from a visitor's point
    of view, and a refusal metric that counted only the first would score a
    well-behaved system as broken.

    A grounded answer must cite something -- prompt v2 requires it -- so
    "answered without citing anything" is the deterministic signature of a prose
    decline.
    """
    return refused or not sources


def refusal_correct(expected: str, *, refused: bool, sources: list[str]) -> bool:
    return (expected == "refuse") == declined(refused, sources)


def fabricated_urls(text: str, corpus_text: str) -> list[str]:
    """URLs in an answer that appear nowhere in the corpus.

    Added after a live run produced `[Snip, which uses raw SQL with no ORM](https://example.com)`
    -- the model reading the `[source: id]` citation instruction as markdown link
    syntax and inventing a href to fill the slot. The citation extractor already
    refuses to treat that as a source, but the fake link is still in the prose a
    visitor reads, so it needs its own number.
    """
    haystack = corpus_text.lower()
    seen: list[str] = []
    for match in URL.finditer(text):
        candidate = match.group(0).rstrip(".,;:").lower()
        bare = candidate.removeprefix("https://").removeprefix("http://").removeprefix("www.")
        if bare not in haystack and candidate not in seen:
            seen.append(candidate)
    return seen
