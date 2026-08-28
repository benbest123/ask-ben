from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from ask_ben.chunks import Chunk
from ask_ben.retrieve import Hit
from ask_ben.service import Deps, create_app

CHUNK = Chunk(id="role-visa", title="Visa", tags=(), body="Ben was an Associate Data Engineer.")


class StubRetriever:
    # "embedding" rather than "bm25": BM25's gate is disabled in config (its
    # score distributions invert, so no threshold separates them), so a stub
    # named bm25 can never demonstrate gating.
    name = "embedding"

    def __init__(self, score: float = 9.0) -> None:
        self._score = score

    def search(self, query: str, k: int) -> list[Hit]:
        return [Hit(chunk=CHUNK, score=self._score)]


class StubBlock:
    type = "text"
    text = "He was an Associate Data Engineer [source: role-visa]."


class StubUsage:
    input_tokens = 100
    output_tokens = 30
    cache_read_input_tokens = 0
    cache_creation_input_tokens = 0


class StubMessage:
    content = [StubBlock()]
    usage = StubUsage()


class StubMessages:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs: Any) -> StubMessage:
        self.calls += 1
        return StubMessage()


class StubClient:
    def __init__(self) -> None:
        self.messages = StubMessages()


def client(score: float = 9.0) -> TestClient:
    return TestClient(create_app(Deps(retriever=StubRetriever(score), client=StubClient())))


def test_health_returns_ok() -> None:
    assert client().get("/health").json() == {"status": "ok"}


def test_ask_returns_answer_sources_and_meta() -> None:
    response = client().post("/ask", json={"question": "What did Ben do at Visa?"})
    assert response.status_code == 200
    body = response.json()
    assert "Associate Data Engineer" in body["answer"]
    assert body["sources"] == ["role-visa"]
    assert body["refused"] is False
    assert body["meta"]["retriever"] == "embedding"


def test_ask_surfaces_a_gated_refusal_as_a_normal_200() -> None:
    """A refusal is an answer, not an error. The widget renders it the same way."""
    response = client(score=0.01).post("/ask", json={"question": "Capital of Peru?"})
    assert response.status_code == 200
    body = response.json()
    assert body["refused"] is True
    assert body["sources"] == []


def test_a_gated_question_never_reaches_the_api() -> None:
    deps = Deps(retriever=StubRetriever(0.01), client=StubClient())
    TestClient(create_app(deps)).post("/ask", json={"question": "Capital of Peru?"})
    assert deps.client.messages.calls == 0


def test_ask_rejects_a_blank_question_with_422() -> None:
    """Whitespace is stripped before the length check, so "   " is empty."""
    assert client().post("/ask", json={"question": "  "}).status_code == 422


def test_ask_rejects_an_over_long_question_with_422() -> None:
    assert client().post("/ask", json={"question": "x" * 501}).status_code == 422


def test_ask_rejects_a_missing_question_with_422() -> None:
    assert client().post("/ask", json={}).status_code == 422


def test_interactive_docs_are_disabled() -> None:
    """One endpoint, one frontend. A docs page is a free invitation to poke."""
    assert client().get("/docs").status_code == 404


def test_cors_allows_the_site_and_not_an_arbitrary_origin() -> None:
    site = client().options(
        "/ask",
        headers={
            "Origin": "https://benbest.uk",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert site.headers.get("access-control-allow-origin") == "https://benbest.uk"

    other = client().options(
        "/ask",
        headers={
            "Origin": "https://not-bens-site.example",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in other.headers


def test_importing_the_service_needs_no_api_key() -> None:
    """Dependencies are built on first request, not at import.

    If this module needed a key to import, CI and `vercel build` would too.
    """
    import importlib

    import ask_ben.service as service

    importlib.reload(service)
    assert service.app is not None
