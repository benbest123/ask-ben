from __future__ import annotations

from typing import Any

import pytest

from ask_ben.answer import QuestionTooLongError, answer_question, extract_citations
from ask_ben.chunks import Chunk
from ask_ben.retrieve import Hit

CHUNKS = [
    Chunk(id="role-visa", title="Visa", tags=(), body="Ben was an Associate Data Engineer."),
    Chunk(id="education", title="Education", tags=(), body="BEng at Auckland."),
]


class StubRetriever:
    def __init__(self, name: str, hits: list[Hit]) -> None:
        self.name = name
        self._hits = hits

    def search(self, query: str, k: int) -> list[Hit]:
        return self._hits


class StubBlock:
    def __init__(self, text: str) -> None:
        self.type = "text"
        self.text = text


class StubUsage:
    input_tokens = 120
    output_tokens = 40
    cache_read_input_tokens = 0
    cache_creation_input_tokens = 0


class StubMessage:
    def __init__(self, text: str) -> None:
        self.content = [StubBlock(text)]
        self.usage = StubUsage()


class StubMessages:
    def __init__(self, text: str) -> None:
        self._text = text
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> StubMessage:
        self.calls.append(kwargs)
        return StubMessage(self._text)


class StubClient:
    def __init__(
        self, text: str = "He was an Associate Data Engineer [source: role-visa]."
    ) -> None:
        self.messages = StubMessages(text)


def test_extract_citations_returns_ids_in_order_of_appearance() -> None:
    text = "First [source: education], then [source: role-visa]."
    assert extract_citations(text, {"education", "role-visa"}) == ["education", "role-visa"]


def test_extract_citations_deduplicates() -> None:
    text = "[source: role-visa] and again [source: role-visa]"
    assert extract_citations(text, {"role-visa"}) == ["role-visa"]


def test_extract_citations_drops_ids_that_were_not_retrieved() -> None:
    """A fabricated citation must never reach the UI as if it were real.

    Rendering an invented id as a working source link is worse than showing
    nothing, because it looks like evidence.
    """
    text = "Claim [source: invented-chunk] and [source: role-visa]."
    assert extract_citations(text, {"role-visa"}) == ["role-visa"]


def test_extract_citations_tolerates_whitespace_in_the_marker() -> None:
    assert extract_citations("[source:  role-visa ]", {"role-visa"}) == ["role-visa"]


def test_answer_returns_text_and_sources() -> None:
    result = answer_question(
        "What did Ben do at Visa?",
        retriever=StubRetriever("bm25", [Hit(chunk=CHUNKS[0], score=9.0)]),
        client=StubClient(),
    )
    assert result.refused is False
    assert result.sources == ["role-visa"]
    assert "Associate Data Engineer" in result.text


def test_low_scoring_retrieval_is_refused_without_calling_the_api() -> None:
    """The relevance gate. Off-topic questions must cost nothing."""
    client = StubClient()
    result = answer_question(
        "What is the capital of Peru?",
        retriever=StubRetriever("embedding", [Hit(chunk=CHUNKS[0], score=0.01)]),
        client=client,
    )
    assert result.refused is True
    assert result.sources == []
    assert client.messages.calls == []


def test_a_gated_question_reports_zero_tokens() -> None:
    """Gated questions are free, and the eval's cost column depends on saying so."""
    result = answer_question(
        "Off topic",
        retriever=StubRetriever("embedding", [Hit(chunk=CHUNKS[0], score=0.01)]),
        client=StubClient(),
    )
    assert result.meta["gated"] is True
    assert result.meta["input_tokens"] == 0
    assert result.meta["output_tokens"] == 0


def test_no_hits_at_all_is_gated() -> None:
    client = StubClient()
    result = answer_question("Anything", retriever=StubRetriever("bm25", []), client=client)
    assert result.refused is True
    assert client.messages.calls == []


def test_full_context_retriever_is_never_gated() -> None:
    result = answer_question(
        "Anything",
        retriever=StubRetriever("full", [Hit(chunk=c, score=1.0) for c in CHUNKS]),
        client=StubClient(),
    )
    assert result.refused is False


def test_full_context_arm_sends_a_cached_system_block() -> None:
    client = StubClient()
    answer_question(
        "Anything",
        retriever=StubRetriever("full", [Hit(chunk=c, score=1.0) for c in CHUNKS]),
        client=client,
    )
    assert client.messages.calls[0]["system"][-1]["cache_control"] == {"type": "ephemeral"}


def test_retrieval_arm_sends_a_plain_system_block() -> None:
    client = StubClient()
    answer_question(
        "Anything",
        retriever=StubRetriever("bm25", [Hit(chunk=CHUNKS[0], score=9.0)]),
        client=client,
    )
    assert "cache_control" not in client.messages.calls[0]["system"][-1]


def test_the_answer_token_cap_is_applied() -> None:
    """Output is billed at 5x input, so this cap is the main abuse lever."""
    from ask_ben.config import MAX_ANSWER_TOKENS

    client = StubClient()
    answer_question(
        "Anything",
        retriever=StubRetriever("bm25", [Hit(chunk=CHUNKS[0], score=9.0)]),
        client=client,
    )
    assert client.messages.calls[0]["max_tokens"] == MAX_ANSWER_TOKENS


def test_meta_records_what_the_evaluation_needs() -> None:
    result = answer_question(
        "What did Ben do?",
        retriever=StubRetriever("bm25", [Hit(chunk=CHUNKS[0], score=9.0)]),
        client=StubClient(),
    )
    assert result.meta["retriever"] == "bm25"
    assert result.meta["retrieved_ids"] == ["role-visa"]
    assert result.meta["top_score"] == 9.0
    assert result.meta["cache_read_input_tokens"] == 0
    assert result.meta["model"] == "claude-haiku-4-5-20251001"


def test_an_over_long_question_is_rejected_before_retrieval() -> None:
    with pytest.raises(QuestionTooLongError):
        answer_question("x" * 501, retriever=StubRetriever("bm25", []), client=StubClient())


def test_a_blank_question_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        answer_question("   ", retriever=StubRetriever("bm25", []), client=StubClient())
