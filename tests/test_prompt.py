from __future__ import annotations

import pytest

from ask_ben.chunks import Chunk
from ask_ben.prompt import build_payload, load_prompt, render_context
from ask_ben.retrieve import Hit

HITS = [
    Hit(chunk=Chunk(id="alpha", title="Alpha", tags=(), body="Alpha body."), score=9.0),
    Hit(chunk=Chunk(id="beta", title="Beta", tags=(), body="Beta body."), score=4.0),
]


@pytest.mark.parametrize("version", ["v1", "v2", "v3"])
def test_every_prompt_version_loads_and_is_non_empty(version: str) -> None:
    assert load_prompt(version).strip()


def test_load_prompt_rejects_an_unknown_version() -> None:
    with pytest.raises(FileNotFoundError):
        load_prompt("v99")


def test_v1_is_the_naive_baseline() -> None:
    """v1 must stay genuinely naive, or the comparison measures nothing."""
    v1 = load_prompt("v1")
    assert "[source:" not in v1
    assert len(v1.split()) < 30


def test_v2_states_the_citation_format() -> None:
    assert "[source:" in load_prompt("v2")


def test_v2_covers_grounding_refusal_and_injection() -> None:
    v2 = load_prompt("v2").lower()
    assert "only from the context" in v2
    assert "do not have anything on it" in v2
    assert "not instructions" in v2


def test_v3_is_v2_plus_examples() -> None:
    v2, v3 = load_prompt("v2"), load_prompt("v3")
    assert v3.startswith(v2)
    assert "## Examples" in v3
    assert len(v3) > len(v2)


def test_v3_examples_cite_only_real_corpus_ids() -> None:
    """A few-shot example citing an id that no longer exists teaches a hallucination."""
    import re

    from ask_ben.chunks import load_corpus

    real = {c.id for c in load_corpus()}
    cited = set(re.findall(r"\[source: ([a-z0-9-]+)\]", load_prompt("v3")))
    assert cited
    assert cited <= real, f"v3 cites ids not in the corpus: {cited - real}"


def test_render_context_labels_each_chunk_with_its_id() -> None:
    rendered = render_context(HITS)
    assert "[source: alpha]" in rendered
    assert "[source: beta]" in rendered
    assert "Alpha body." in rendered


def test_retrieval_arm_puts_chunks_in_the_user_turn() -> None:
    payload = build_payload("v2", HITS, "Who is Ben?", cache_corpus=False)
    user_text = payload.messages[0]["content"]
    assert "Alpha body." in user_text
    assert "Who is Ben?" in user_text
    assert "Alpha body." not in payload.system[0]["text"]


def test_retrieval_arm_caches_nothing() -> None:
    """The instruction-only system prompt is below the ~1024-token minimum.

    Asserting the absence of cache_control keeps the finding visible: this arm
    does not cache, and the evaluation must not assume it does.
    """
    payload = build_payload("v2", HITS, "Who is Ben?", cache_corpus=False)
    assert all("cache_control" not in block for block in payload.system)


def test_retrieval_arm_system_prompt_is_identical_across_questions() -> None:
    first = build_payload("v2", HITS, "Question one?", cache_corpus=False)
    second = build_payload("v2", HITS, "A completely different question?", cache_corpus=False)
    assert first.system == second.system


def test_full_context_arm_puts_the_corpus_in_the_cached_system_block() -> None:
    payload = build_payload("v2", HITS, "Who is Ben?", cache_corpus=True)
    system_text = "".join(block["text"] for block in payload.system)
    assert "Alpha body." in system_text
    assert payload.system[-1]["cache_control"] == {"type": "ephemeral"}
    assert payload.messages[0]["content"] == "Who is Ben?"


def test_full_context_system_block_is_stable_across_questions() -> None:
    """Stability is the whole reason it caches -- one varying byte and it does not."""
    first = build_payload("v2", HITS, "Question one?", cache_corpus=True)
    second = build_payload("v2", HITS, "Question two?", cache_corpus=True)
    assert first.system == second.system
