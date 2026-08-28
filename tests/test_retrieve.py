from __future__ import annotations

import numpy as np
import pytest

from ask_ben.chunks import Chunk
from ask_ben.retrieve import (
    Bm25Retriever,
    EmbeddingRetriever,
    FullContextRetriever,
    build_retriever,
)

CHUNKS = [
    Chunk(id="iam", title="Isolation in IAM", tags=(), body="Partner isolation drawn in IAM."),
    Chunk(id="qlik", title="Qlik dashboards", tags=(), body="Embedding Qlik dashboards in React."),
    Chunk(id="race", title="A race condition", tags=(), body="Polling was the wrong fix."),
]


def test_bm25_ranks_the_lexically_matching_chunk_first() -> None:
    hits = Bm25Retriever(CHUNKS).search("why was isolation drawn in IAM", k=2)
    assert hits[0].chunk.id == "iam"


def test_bm25_returns_at_most_k_hits() -> None:
    assert len(Bm25Retriever(CHUNKS).search("IAM", k=2)) == 2


def test_bm25_hits_are_ordered_by_descending_score() -> None:
    hits = Bm25Retriever(CHUNKS).search("Qlik dashboards React", k=3)
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_bm25_is_named_for_the_gate_threshold_lookup() -> None:
    assert Bm25Retriever(CHUNKS).name == "bm25"


def test_bm25_normalises_the_query_before_scoring() -> None:
    """ "your" appears in no chunk, so an un-rewritten query wastes a token."""
    second_person = Bm25Retriever(CHUNKS).search("how did you draw your isolation", k=1)
    third_person = Bm25Retriever(CHUNKS).search("how did Ben draw Ben's isolation", k=1)
    assert second_person[0].chunk.id == third_person[0].chunk.id
    assert second_person[0].score == pytest.approx(third_person[0].score)


def test_embedding_retriever_ranks_by_cosine_similarity() -> None:
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.7071, 0.7071]], dtype=np.float32)
    retriever = EmbeddingRetriever(
        CHUNKS, vectors, lambda _q: np.array([1.0, 0.0], dtype=np.float32)
    )
    hits = retriever.search("anything", k=3)
    assert [h.chunk.id for h in hits] == ["iam", "race", "qlik"]
    assert hits[0].score == pytest.approx(1.0)


def test_embedding_retriever_embeds_the_query_exactly_once() -> None:
    """One network call per question, and the rate limit makes that worth asserting."""
    calls: list[str] = []

    def embed(query: str) -> np.ndarray:
        calls.append(query)
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

    EmbeddingRetriever(CHUNKS, np.eye(3, dtype=np.float32), embed).search("a question", k=1)
    assert len(calls) == 1


def test_embedding_retriever_embeds_the_normalised_query() -> None:
    """The corpus never says "you", so the raw form is embedded further from every chunk."""
    calls: list[str] = []

    def embed(query: str) -> np.ndarray:
        calls.append(query)
        return np.array([1.0, 0.0, 0.0], dtype=np.float32)

    EmbeddingRetriever(CHUNKS, np.eye(3, dtype=np.float32), embed).search("what is your role", k=1)
    assert calls == ["what is Ben's role"]


def test_embedding_retriever_rejects_a_length_mismatch() -> None:
    with pytest.raises(ValueError, match="disagree on length"):
        EmbeddingRetriever(CHUNKS, np.eye(2, dtype=np.float32), lambda _q: np.zeros(2))


def test_full_context_returns_every_chunk_regardless_of_k() -> None:
    """The control arm. k is accepted and ignored -- prompt-stuffing has no top-k."""
    assert len(FullContextRetriever(CHUNKS).search("anything at all", k=1)) == 3


def test_full_context_scores_are_uniform() -> None:
    hits = FullContextRetriever(CHUNKS).search("anything", k=1)
    assert {h.score for h in hits} == {1.0}


def test_build_retriever_rejects_an_unknown_name() -> None:
    with pytest.raises(ValueError, match="unknown retriever"):
        build_retriever("faiss")


def test_retrieve_module_never_imports_generation() -> None:
    """Retrieval must stay ignorant of generation, or the eval cannot swap arms.

    Parses the import statements rather than grepping the source -- the module
    is allowed to *discuss* Claude in a docstring, and an earlier version of
    this test failed on exactly that.
    """
    import ast
    from pathlib import Path

    import ask_ben.retrieve as retrieve

    tree = ast.parse(Path(retrieve.__file__ or "").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
            imported.add(node.module)

    assert "anthropic" not in imported
    assert not any(name.endswith(("prompt", "answer")) for name in imported), imported
