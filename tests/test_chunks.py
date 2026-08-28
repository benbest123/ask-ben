from pathlib import Path

import pytest

from ask_ben.chunks import Chunk, CorpusError, load_corpus, parse_chunk

FIXTURES = Path(__file__).parent / "fixtures" / "corpus"


def test_parse_chunk_reads_frontmatter_and_body() -> None:
    raw = "---\nid: alpha\ntitle: The first chunk\ntags: [one, two]\n---\nAlpha body text.\n"
    chunk = parse_chunk(raw, source="alpha.md")
    assert chunk == Chunk(
        id="alpha", title="The first chunk", tags=("one", "two"), body="Alpha body text."
    )


def test_chunk_text_joins_title_and_body() -> None:
    chunk = Chunk(id="a", title="Title", tags=(), body="Body")
    assert chunk.text == "Title\n\nBody"


def test_parse_chunk_rejects_missing_frontmatter() -> None:
    with pytest.raises(CorpusError, match="no frontmatter"):
        parse_chunk("Just a body.\n", source="bad.md")


def test_parse_chunk_rejects_missing_id() -> None:
    raw = "---\ntitle: No id here\n---\nBody.\n"
    with pytest.raises(CorpusError, match="missing 'id'"):
        parse_chunk(raw, source="bad.md")


def test_parse_chunk_rejects_missing_title() -> None:
    raw = "---\nid: a\n---\nBody.\n"
    with pytest.raises(CorpusError, match="missing 'title'"):
        parse_chunk(raw, source="bad.md")


def test_parse_chunk_rejects_empty_body() -> None:
    raw = "---\nid: a\ntitle: T\n---\n\n"
    with pytest.raises(CorpusError, match="empty body"):
        parse_chunk(raw, source="bad.md")


def test_parse_chunk_rejects_non_list_tags() -> None:
    raw = "---\nid: a\ntitle: T\ntags: one\n---\nBody.\n"
    with pytest.raises(CorpusError, match="'tags' must be a list"):
        parse_chunk(raw, source="bad.md")


def test_parse_chunk_allows_missing_tags() -> None:
    chunk = parse_chunk("---\nid: a\ntitle: T\n---\nBody.\n", source="a.md")
    assert chunk.tags == ()


def test_load_corpus_returns_chunks_sorted_by_id() -> None:
    chunks = load_corpus(FIXTURES)
    assert [c.id for c in chunks] == ["alpha", "beta"]


def test_load_corpus_rejects_duplicate_ids(tmp_path: Path) -> None:
    (tmp_path / "one.md").write_text("---\nid: dupe\ntitle: A\n---\nBody.\n", encoding="utf-8")
    (tmp_path / "two.md").write_text("---\nid: dupe\ntitle: B\n---\nBody.\n", encoding="utf-8")
    with pytest.raises(CorpusError, match="duplicate id 'dupe'"):
        load_corpus(tmp_path)


def test_load_corpus_rejects_an_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(CorpusError, match="no chunks"):
        load_corpus(tmp_path)
