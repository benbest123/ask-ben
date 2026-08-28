from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from ask_ben.chunks import Chunk
from ask_ben.ingest import (
    build_index,
    build_records,
    embed_documents,
    embed_query,
    load_index,
    write_index,
    write_records,
)


class FakeEmbedResponse:
    def __init__(self, embeddings: list[list[float]]) -> None:
        self.embeddings = embeddings


class FakeVoyage:
    """Returns a deterministic, deliberately non-normalised vector per text.

    Non-normalised so the tests can assert that normalisation actually happens
    here rather than being something Voyage happens to do for us.
    """

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def embed(self, texts: list[str], model: str, input_type: str) -> FakeEmbedResponse:
        self.calls.append({"texts": texts, "model": model, "input_type": input_type})
        return FakeEmbedResponse([[float(len(t)), 3.0] + [0.0] * 1022 for t in texts])


def test_embed_documents_uses_document_input_type() -> None:
    client = FakeVoyage()
    embed_documents(["hello"], client)
    assert client.calls[0]["input_type"] == "document"
    assert client.calls[0]["model"] == "voyage-4-lite"


def test_embed_query_uses_query_input_type() -> None:
    """Voyage embeds queries and documents asymmetrically.

    Getting this wrong does not raise -- it returns vectors that are merely
    worse, so retrieval degrades silently. That makes it worth asserting.
    """
    client = FakeVoyage()
    embed_query("hello", client)
    assert client.calls[0]["input_type"] == "query"


def test_embeddings_are_l2_normalised() -> None:
    """Normalising here is what makes cosine similarity a plain dot product."""
    vectors = embed_documents(["abcd", "ab"], FakeVoyage())
    assert np.allclose(np.linalg.norm(vectors, axis=1), 1.0)


def test_embed_documents_returns_float32_of_the_right_shape() -> None:
    vectors = embed_documents(["a", "b", "c"], FakeVoyage())
    assert vectors.shape == (3, 1024)
    assert vectors.dtype == np.float32


def test_embed_query_returns_a_single_vector() -> None:
    assert embed_query("a", FakeVoyage()).shape == (1024,)


def test_build_index_embeds_chunk_text_not_just_body() -> None:
    client = FakeVoyage()
    build_index([Chunk(id="a", title="Title", tags=("t",), body="Body")], client)
    assert client.calls[0]["texts"] == ["Title\n\nBody"]


def test_index_round_trips_through_disk(tmp_path: Path) -> None:
    chunks = [
        Chunk(id="a", title="A", tags=("x",), body="Body A"),
        Chunk(id="b", title="B", tags=(), body="Body B"),
    ]
    records, vectors = build_index(chunks, FakeVoyage())
    corpus_json = tmp_path / "corpus.json"
    embeddings_npy = tmp_path / "embeddings.npy"
    write_index(records, vectors, corpus_json=corpus_json, embeddings_npy=embeddings_npy)

    loaded_chunks, loaded_vectors = load_index(
        corpus_json=corpus_json, embeddings_npy=embeddings_npy
    )
    assert loaded_chunks == chunks
    assert np.allclose(loaded_vectors, vectors)


def test_load_index_rejects_a_row_count_mismatch(tmp_path: Path) -> None:
    """The array is positional, so a length mismatch means every vector is wrong.

    Nothing about that would raise on its own -- retrieval would return
    confident, plausible, wrong chunks -- so it has to be checked explicitly.
    """
    records, vectors = build_index([Chunk(id="a", title="A", tags=(), body="Body A")], FakeVoyage())
    corpus_json = tmp_path / "corpus.json"
    embeddings_npy = tmp_path / "embeddings.npy"
    write_index(records, vectors, corpus_json=corpus_json, embeddings_npy=embeddings_npy)
    np.save(embeddings_npy, np.zeros((5, 1024), dtype=np.float32))

    with pytest.raises(ValueError, match="out of sync"):
        load_index(corpus_json=corpus_json, embeddings_npy=embeddings_npy)


def test_load_index_rejects_a_dimension_mismatch(tmp_path: Path) -> None:
    records, vectors = build_index([Chunk(id="a", title="A", tags=(), body="Body A")], FakeVoyage())
    corpus_json = tmp_path / "corpus.json"
    embeddings_npy = tmp_path / "embeddings.npy"
    write_index(records, vectors, corpus_json=corpus_json, embeddings_npy=embeddings_npy)
    np.save(embeddings_npy, np.zeros((1, 512), dtype=np.float32))

    with pytest.raises(ValueError, match="out of sync"):
        load_index(corpus_json=corpus_json, embeddings_npy=embeddings_npy)


def test_records_are_byte_stable_across_rebuilds(tmp_path: Path) -> None:
    """CI diffs a rebuild against the committed file, so the bytes must be stable."""
    chunks = [Chunk(id="b", title="B", tags=("z", "a"), body="Body B")]
    first = tmp_path / "one.json"
    second = tmp_path / "two.json"
    vectors = np.zeros((1, 1024), dtype=np.float32)
    write_index(
        build_records(chunks), vectors, corpus_json=first, embeddings_npy=tmp_path / "a.npy"
    )
    write_index(
        build_records(chunks), vectors, corpus_json=second, embeddings_npy=tmp_path / "b.npy"
    )
    assert first.read_bytes() == second.read_bytes()


def test_records_only_rebuild_needs_no_client(tmp_path: Path) -> None:
    """CI proves corpus.json still matches the corpus without an API key.

    Embeddings are not byte-reproducible -- a remote model offers no such
    guarantee -- so the freshness check covers chunk content and ordering,
    which is where drift actually happens.
    """
    corpus_json = tmp_path / "corpus.json"
    chunks = [Chunk(id="a", title="A", tags=("x",), body="Body A")]

    write_records(build_records(chunks), corpus_json)

    written = corpus_json.read_text(encoding="utf-8")
    assert '"id": "a"' in written
    assert written.endswith("\n")
