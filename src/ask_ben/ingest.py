"""Build the committed index. Run with `python -m ask_ben.ingest`.

There is no database here on purpose. Twenty-nine chunks at 1024 float32 is
about 119KB, which is smaller than most of the dependencies a vector store would
drag in, and a brute-force comparison against all of them is one matrix
multiply. See the spec's "Retrieval" section, and `corpus/askben-no-vector-db.md`
for the version of this argument the widget itself will give you.

Both artifacts are committed. CI rebuilds `corpus.json` and fails if it differs,
which closes the standard RAG failure mode where the corpus and the index drift
apart and retrieval quietly starts answering from stale text.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Protocol, TypedDict, cast

import numpy as np

from ask_ben.chunks import Chunk, load_corpus
from ask_ben.config import CORPUS_JSON, EMBED_DIM, EMBED_MODEL, EMBEDDINGS_NPY, INDEX_DIR


class ChunkRecord(TypedDict):
    id: str
    title: str
    tags: list[str]
    body: str


class EmbedResponse(Protocol):
    # A read-only property rather than an attribute, which makes it covariant.
    # Voyage types this as list[list[float]] | list[list[int]] (int for quantised
    # output dtypes), and an invariant attribute would reject that union.
    @property
    def embeddings(self) -> Sequence[Sequence[float]]: ...


class EmbedClient(Protocol):
    """The slice of `voyageai.Client` this project uses.

    Depending on a protocol rather than the concrete client is what lets every
    test run with no API key -- see `tests/test_ingest.py`.
    """

    def embed(self, texts: list[str], model: str, input_type: str) -> EmbedResponse: ...


def _normalise(vectors: np.ndarray) -> np.ndarray:
    """L2-normalise rows so cosine similarity is a plain dot product later.

    Doing it once at ingest keeps the division out of the query hot path and
    keeps the retriever trivially testable -- a dot product has no tolerance
    argument to get wrong.
    """
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return cast(np.ndarray, (vectors / norms).astype(np.float32))


def embed_documents(texts: list[str], client: EmbedClient) -> np.ndarray:
    """Embed corpus text. `input_type="document"` is not optional.

    Voyage embeds documents and queries asymmetrically. Using the wrong one does
    not raise; it returns vectors that are merely worse, so the failure shows up
    as unexplained mediocre retrieval rather than as an error.
    """
    response = client.embed(texts, model=EMBED_MODEL, input_type="document")
    return _normalise(np.asarray(response.embeddings, dtype=np.float32))


def embed_query(text: str, client: EmbedClient) -> np.ndarray:
    """Embed a visitor question. The counterpart to `embed_documents`."""
    response = client.embed([text], model=EMBED_MODEL, input_type="query")
    return cast(np.ndarray, _normalise(np.asarray(response.embeddings, dtype=np.float32))[0])


def build_records(chunks: list[Chunk]) -> list[ChunkRecord]:
    return [ChunkRecord(id=c.id, title=c.title, tags=list(c.tags), body=c.body) for c in chunks]


def build_index(chunks: list[Chunk], client: EmbedClient) -> tuple[list[ChunkRecord], np.ndarray]:
    """Embed `chunk.text`, not `chunk.body` -- the title carries retrieval signal."""
    return build_records(chunks), embed_documents([c.text for c in chunks], client)


def write_records(records: list[ChunkRecord], corpus_json: Path = CORPUS_JSON) -> None:
    """Write just the chunk half of the index.

    Split out from `write_index` so CI can rebuild and diff it without an API
    key. Embeddings are not byte-reproducible anyway -- a remote model gives no
    such guarantee -- so the freshness check covers chunk content and ordering,
    which is where drift actually happens.
    """
    corpus_json.parent.mkdir(parents=True, exist_ok=True)
    # sort_keys and the trailing newline keep the artifact byte-stable. That is
    # what lets CI diff a rebuild against the committed copy and mean something.
    corpus_json.write_text(
        json.dumps(records, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_index(
    records: list[ChunkRecord],
    vectors: np.ndarray,
    *,
    corpus_json: Path = CORPUS_JSON,
    embeddings_npy: Path = EMBEDDINGS_NPY,
) -> None:
    write_records(records, corpus_json)
    np.save(embeddings_npy, vectors)


def load_index(
    *,
    corpus_json: Path = CORPUS_JSON,
    embeddings_npy: Path = EMBEDDINGS_NPY,
) -> tuple[list[Chunk], np.ndarray]:
    """Load the committed index, refusing to return a mismatched pair.

    The embeddings array is positional: row i belongs to chunk i. If the two
    files disagree, every vector maps to the wrong chunk. Nothing about that
    raises on its own and retrieval still returns confident, plausible, wrong
    answers, so the check has to be explicit and has to happen at load time.
    """
    records = cast(list[ChunkRecord], json.loads(corpus_json.read_text(encoding="utf-8")))
    vectors = np.load(embeddings_npy)

    if len(records) != vectors.shape[0]:
        raise ValueError(
            f"index is out of sync: {len(records)} chunks but {vectors.shape[0]} vectors. "
            "Run `python -m ask_ben.ingest`."
        )
    if vectors.shape[1] != EMBED_DIM:
        raise ValueError(
            f"index is out of sync: expected {EMBED_DIM} dimensions, "
            f"found {vectors.shape[1]}. Run `python -m ask_ben.ingest`."
        )

    chunks = [
        Chunk(id=r["id"], title=r["title"], tags=tuple(r["tags"]), body=r["body"]) for r in records
    ]
    return chunks, vectors


def main(argv: Sequence[str] | None = None) -> None:
    """Rebuild the index. `--records-only` skips embedding, and so skips the API.

    CI uses `--records-only` to prove the committed `corpus.json` still matches
    the corpus on disk, without needing a key or spending tokens.
    """
    args = sys.argv[1:] if argv is None else list(argv)
    chunks = load_corpus()
    INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if "--records-only" in args:
        write_records(build_records(chunks))
        print(f"Wrote {len(chunks)} chunk records to {CORPUS_JSON} (embeddings untouched)")
        return

    from voyageai.client import Client

    records, vectors = build_index(chunks, Client())
    write_index(records, vectors)
    print(f"Wrote {len(records)} chunks to {CORPUS_JSON} and {EMBEDDINGS_NPY}")


if __name__ == "__main__":
    main()
