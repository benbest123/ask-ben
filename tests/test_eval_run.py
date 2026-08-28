from __future__ import annotations

from typing import Any

from ask_ben.chunks import Chunk, load_corpus
from ask_ben.eval.judge import Verdict
from ask_ben.eval.metrics import GoldenQuestion
from ask_ben.eval.run import evaluate, render_report
from ask_ben.retrieve import Hit

# A real corpus id, because evaluate() rebuilds the judged context from the
# corpus rather than searching a second time.
REAL_ID = "role-visa"
CHUNK = Chunk(id=REAL_ID, title="Visa", tags=(), body="Associate Data Engineer.")

QUESTIONS = [
    GoldenQuestion(
        id="factual-visa",
        question="What did Ben do at Visa?",
        category="factual",
        expected="answer",
        must_cite=(REAL_ID,),
        reference="Associate Data Engineer.",
    ),
    GoldenQuestion(
        id="out-of-scope-compensation",
        question="What are his compensation expectations?",
        category="out-of-scope",
        expected="refuse",
        must_cite=(),
        reference=None,
    ),
]


class StubRetriever:
    name = "bm25"

    def search(self, query: str, k: int) -> list[Hit]:
        return [Hit(chunk=CHUNK, score=9.0 if "Visa" in query else 0.0)]


class StubBlock:
    type = "text"
    text = "He was an Associate Data Engineer [source: role-visa]."


class StubUsage:
    input_tokens = 100
    output_tokens = 25
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


class StubParsed:
    parsed_output = Verdict(declined=False, grounded=True, quality=4, reasoning="fine")


class StubJudgeMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> StubParsed:
        self.calls.append(kwargs)
        return StubParsed()


class StubJudgeClient:
    def __init__(self) -> None:
        self.messages = StubJudgeMessages()


def run(judge: StubJudgeClient | None = None) -> Any:
    return evaluate(
        QUESTIONS,
        retriever=StubRetriever(),
        client=StubClient(),
        judge_client=judge or StubJudgeClient(),
        prompt_version="v2",
        model="claude-haiku-4-5-20251001",
        k=4,
    )


def test_every_question_produces_a_row() -> None:
    assert len(run().rows) == 2


def test_the_gated_question_is_recorded_as_refused() -> None:
    row = next(r for r in run().rows if r["id"] == "out-of-scope-compensation")
    assert row["refused"] is True
    assert row["gated"] is True
    assert row["refusal_correct"] is True


def test_the_judge_is_not_called_for_a_gated_refusal() -> None:
    """Grading a scripted refusal spends money to evaluate a constant string."""
    judge = StubJudgeClient()
    run(judge)
    assert len(judge.messages.calls) == 1


def test_an_answered_question_carries_retrieval_and_judged_metrics() -> None:
    row = next(r for r in run().rows if r["id"] == "factual-visa")
    assert row["recall_at_k"] == 1.0
    assert row["reciprocal_rank"] == 1.0
    assert row["citation_valid"] is True
    assert row["grounded"] is True
    assert row["quality"] == 4


def test_rows_store_the_context_so_a_human_can_label_without_rerunning() -> None:
    """Ben labels grounding, which is unanswerable without the passages shown."""
    row = next(r for r in run().rows if r["id"] == "factual-visa")
    assert "[source: role-visa]" in row["context"]
    assert row["reference"] == "Associate Data Engineer."


def test_the_judge_grades_against_the_same_context_the_answer_saw() -> None:
    """Rebuilt from the retrieved ids, not from a second search.

    A second search would be another embedding call per question on the dense
    arm, and could grade the answer against different passages than produced it.
    """
    judge = StubJudgeClient()
    result = run(judge)
    row = next(r for r in result.rows if r["id"] == "factual-visa")
    sent = judge.messages.calls[0]["messages"][0]["content"]
    assert row["context"] in sent


def test_the_judge_runs_on_the_judge_model_not_the_answer_model() -> None:
    """The plan wired the answer model through to the judge; that collapses the check."""
    judge = StubJudgeClient()
    run(judge)
    assert judge.messages.calls[0]["model"] == "claude-opus-5"


def test_summary_reports_the_headline_numbers() -> None:
    summary = run().summary
    assert summary["n"] == 2
    assert summary["refusal_accuracy"] == 1.0
    assert summary["mean_recall_at_k"] == 1.0
    assert summary["citation_validity"] == 1.0
    assert summary["gated"] == 1


def test_summary_records_token_cost_including_cache_activity() -> None:
    summary = run().summary
    assert summary["input_tokens"] == 100
    assert summary["output_tokens"] == 25
    assert summary["cache_read_input_tokens"] == 0
    assert summary["cache_creation_input_tokens"] == 0


def test_a_gated_question_contributes_no_tokens() -> None:
    """The gate's whole point is that a declined question is free."""
    row = next(r for r in run().rows if r["id"] == "out-of-scope-compensation")
    assert row["input_tokens"] == 0
    assert row["output_tokens"] == 0


def test_fabricated_urls_are_scored_per_row() -> None:
    row = next(r for r in run().rows if r["id"] == "factual-visa")
    assert row["fabricated_urls"] == []
    assert run().summary["answers_with_fabricated_urls"] == 0


def test_the_report_is_markdown_naming_the_configuration() -> None:
    report = render_report(run())
    assert "bm25" in report
    assert "v2" in report
    assert "claude-haiku-4-5-20251001" in report
    assert "claude-opus-5" in report
    assert "| " in report


def test_the_report_lists_failures_with_a_reason() -> None:
    result = run()
    result.rows[0]["grounded"] = False
    result.rows[0]["fabricated_urls"] = ["https://example.com"]
    report = render_report(result)
    assert "not grounded" in report
    assert "fabricated URL" in report


def test_evaluate_uses_real_corpus_ids() -> None:
    """Guards the fixture against the corpus drifting out from under it."""
    assert REAL_ID in {c.id for c in load_corpus()}
