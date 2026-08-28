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


def refusal_correct(expected: str, *, declined: bool) -> bool:
    """Did the system do the right thing about answering at all?

    `declined` comes from two places: the relevance gate (deterministic and free)
    or, for anything the gate let through, the judge. It deliberately does NOT
    come from "were there any sources", which is what an earlier version used.

    That heuristic was confounded: prompt v1 never asks for citations, so every
    v1 answer had empty sources and was scored as a refusal. v1's refusal
    accuracy came out at 0.367 -- a number that measured whether the prompt
    requested citations, not whether the system declined. The confound flattered
    v2 and v3 against the baseline they exist to be compared with.
    """
    return (expected == "refuse") == declined


def retrieval_metrics_apply(retriever_name: str) -> bool:
    """Recall@k and MRR are ranking metrics; the control arm does no ranking.

    FullContextRetriever returns all 29 chunks in corpus order, so recall@4
    scores the first four alphabetically and MRR reports a position that means
    nothing. On one run this gave recall@4 = 0.0 for a question whose chunk had
    in fact been retrieved. Reporting that as a retrieval score would be a
    fabricated comparison, so these are recorded as not-applicable instead.
    """
    return retriever_name != "full"


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
