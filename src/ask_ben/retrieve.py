"""Retrieval strategies behind one interface.

This module deliberately knows nothing about Claude, prompts or citations. It
maps a query to ranked chunks and stops. That separation is what lets the
evaluation swap retrievers without touching generation, and it is why
`retrieve.py` must never import `anthropic`.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from rank_bm25 import BM25Okapi

from ask_ben.chunks import Chunk
from ask_ben.normalise import normalise_question

TOKEN = re.compile(r"[a-z0-9]+")


def tokenise(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Retriever(Protocol):
    name: str

    def search(self, query: str, k: int) -> list[Hit]: ...


class Bm25Retriever:
    """Lexical retrieval. No API call, no key, no vendor, no rate limit.

    Scores are unbounded, which is why the relevance-gate threshold is keyed by
    retriever name in config rather than shared with the embedding retriever.
    """

    name = "bm25"

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks
        self._bm25 = BM25Okapi([tokenise(c.text) for c in chunks])

    def search(self, query: str, k: int) -> list[Hit]:
        scores = self._bm25.get_scores(tokenise(normalise_question(query)))
        order = np.argsort(scores)[::-1][:k]
        return [Hit(chunk=self._chunks[i], score=float(scores[i])) for i in order]


class EmbeddingRetriever:
    """Dense retrieval.

    Vectors are L2-normalised at ingest, so cosine similarity is a single dot
    product against a 29x1024 matrix -- no vector database, no index structure,
    no approximate search. At this size, comparing against everything already
    is the fast path.
    """

    name = "embedding"

    def __init__(
        self,
        chunks: list[Chunk],
        vectors: np.ndarray,
        embed_fn: Callable[[str], np.ndarray],
    ) -> None:
        if len(chunks) != vectors.shape[0]:
            raise ValueError(
                f"chunks and vectors disagree on length: {len(chunks)} vs {vectors.shape[0]}"
            )
        self._chunks = chunks
        self._vectors = vectors
        self._embed = embed_fn

    def search(self, query: str, k: int) -> list[Hit]:
        scores = self._vectors @ self._embed(normalise_question(query))
        order = np.argsort(scores)[::-1][:k]
        return [Hit(chunk=self._chunks[i], score=float(scores[i])) for i in order]


class FullContextRetriever:
    """The control arm: no retrieval at all, the whole corpus every time.

    `k` is accepted and ignored. Prompt-stuffing has no notion of top-k, and
    honouring the parameter would quietly turn the control arm into a fourth
    retriever, which would make the comparison meaningless.

    It does not normalise the query because it does not read the query. That is
    the whole point of the arm.
    """

    name = "full"

    def __init__(self, chunks: list[Chunk]) -> None:
        self._chunks = chunks

    def search(self, query: str, k: int) -> list[Hit]:
        return [Hit(chunk=c, score=1.0) for c in self._chunks]


def build_retriever(
    name: str,
    *,
    embed_fn: Callable[[str], np.ndarray] | None = None,
) -> Retriever:
    """Construct a retriever by name against the committed index.

    `embed_fn` is injectable so the evaluation and the tests can drive the dense
    arm without a Voyage client -- and so a rate-limited or unavailable
    embeddings API cannot take the other two arms down with it.
    """
    from ask_ben.ingest import load_index

    chunks, vectors = load_index()

    if name == "bm25":
        return Bm25Retriever(chunks)
    if name == "full":
        return FullContextRetriever(chunks)
    if name == "embedding":
        if embed_fn is None:
            from voyageai.client import Client

            from ask_ben.ingest import embed_query

            client = Client()

            def embed_fn_default(query: str) -> np.ndarray:
                return embed_query(query, client)

            embed_fn = embed_fn_default
        return EmbeddingRetriever(chunks, vectors, embed_fn)

    raise ValueError(f"unknown retriever '{name}'; expected bm25, embedding or full")
