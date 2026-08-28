"""HTTP surface. One endpoint plus a health check.

Dependencies are injected rather than reached for, so the tests drive a real
app with stub retrieval and a stub client and never need a key. Building them
is deferred until the first request: importing this module must not require an
API key, or `vercel build` and every import-time check would need secrets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, StringConstraints

from ask_ben.answer import answer_question
from ask_ben.config import MAX_QUESTION_CHARS

ALLOWED_ORIGINS = [
    "https://benbest.uk",
    "https://www.benbest.uk",
    "http://localhost:5173",
]

# strip_whitespace before the length checks, so "   " is rejected as empty
# rather than accepted as three characters.
QuestionText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_CHARS),
]


class AskRequest(BaseModel):
    question: QuestionText


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    refused: bool
    meta: dict[str, Any]


@dataclass
class Deps:
    retriever: Any
    client: Any


def create_app(dependencies: Deps | None = None) -> FastAPI:
    # docs_url and redoc_url are off: this serves one endpoint to one frontend,
    # and an interactive docs page is a free invitation to poke at it.
    app = FastAPI(title="ask-ben", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_methods=["POST", "GET"],
        allow_headers=["content-type"],
    )

    def resolve() -> Deps:
        """Build the real dependencies on first use.

        CORS restricts which *browsers* will use the response; it stops nothing
        server-side. The real cost controls are the console spend limit, the
        answer-token cap and the edge rate limit -- see the spec's "Cost and
        abuse" section.
        """
        nonlocal dependencies
        if dependencies is None:
            import anthropic

            from ask_ben.config import DEFAULT_RETRIEVER
            from ask_ben.retrieve import build_retriever

            dependencies = Deps(
                retriever=build_retriever(DEFAULT_RETRIEVER),
                client=anthropic.Anthropic(),
            )
        return dependencies

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(request: AskRequest) -> AskResponse:
        deps = resolve()
        result = answer_question(request.question, retriever=deps.retriever, client=deps.client)
        return AskResponse(
            answer=result.text,
            sources=result.sources,
            refused=result.refused,
            meta=result.meta,
        )

    return app


app = create_app()
