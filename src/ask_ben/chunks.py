"""Corpus loading.

One markdown file is one chunk. There is deliberately no splitting logic in this
module and there should never be any: the corpus is authored at chunk size
(150-320 words per file), which declines the chunking problem rather than
solving it. See the spec's "Corpus and chunking" section for why that is a
defensible choice at this scale and what would have to change at a larger one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

from ask_ben.config import CORPUS_DIR

FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", re.DOTALL)


class CorpusError(Exception):
    """Raised when the corpus on disk is malformed.

    Every failure is loud and names the offending file. A corpus that loads
    silently wrong is the worst outcome here -- retrieval would still return
    something, so nothing would look broken.
    """


@dataclass(frozen=True)
class Chunk:
    id: str
    title: str
    tags: tuple[str, ...]
    body: str

    @property
    def text(self) -> str:
        """What gets embedded, indexed and shown to the model.

        The title is included because it carries retrieval signal the body often
        does not -- "Why partner isolation lived in IAM, not application code"
        carries words a question is likely to use, while the prose beneath such
        a title often does not.
        """
        return f"{self.title}\n\n{self.body}"


def parse_chunk(raw: str, *, source: str) -> Chunk:
    """Parse one markdown file with YAML frontmatter into a Chunk."""
    match = FRONTMATTER.match(raw)
    if match is None:
        raise CorpusError(f"{source}: no frontmatter block")

    meta = yaml.safe_load(match.group(1)) or {}
    if not isinstance(meta, dict):
        raise CorpusError(f"{source}: frontmatter is not a mapping")

    chunk_id = meta.get("id")
    if not chunk_id:
        raise CorpusError(f"{source}: missing 'id' in frontmatter")

    title = meta.get("title")
    if not title:
        raise CorpusError(f"{source}: missing 'title' in frontmatter")

    body = match.group(2).strip()
    if not body:
        raise CorpusError(f"{source}: empty body")

    raw_tags = meta.get("tags") or []
    if not isinstance(raw_tags, list):
        raise CorpusError(f"{source}: 'tags' must be a list")

    return Chunk(
        id=str(chunk_id),
        title=str(title),
        tags=tuple(str(t) for t in raw_tags),
        body=body,
    )


def load_corpus(corpus_dir: Path | None = None) -> list[Chunk]:
    """Load every chunk in a directory, sorted by id.

    Sorting matters beyond tidiness: the embeddings array is positional, so the
    ingest and query paths must agree on chunk order or every vector maps to the
    wrong chunk -- silently, and while still returning plausible-looking results.
    """
    directory = corpus_dir if corpus_dir is not None else CORPUS_DIR
    chunks: list[Chunk] = []
    seen: set[str] = set()

    for path in sorted(directory.glob("*.md")):
        chunk = parse_chunk(path.read_text(encoding="utf-8"), source=path.name)
        if chunk.id in seen:
            raise CorpusError(f"{path.name}: duplicate id '{chunk.id}'")
        seen.add(chunk.id)
        chunks.append(chunk)

    if not chunks:
        raise CorpusError(f"{directory}: no chunks found")

    return sorted(chunks, key=lambda c: c.id)
