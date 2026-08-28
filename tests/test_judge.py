from __future__ import annotations

from pathlib import Path
from typing import Any

from ask_ben.eval.judge import Verdict, judge_agreement, judge_answer, load_human_labels


class StubParsed:
    def __init__(self, verdict: Verdict) -> None:
        self.parsed_output = verdict


class StubMessages:
    def __init__(self, verdict: Verdict) -> None:
        self._verdict = verdict
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> StubParsed:
        self.calls.append(kwargs)
        return StubParsed(self._verdict)


class StubClient:
    def __init__(self, verdict: Verdict) -> None:
        self.messages = StubMessages(verdict)


def test_judge_returns_a_validated_verdict() -> None:
    expected = Verdict(
        declined=False, grounded=True, quality=4, reasoning="Every claim is supported."
    )
    verdict = judge_answer(
        StubClient(expected),
        question="What did Ben do at Visa?",
        context="[source: role-visa] He was an Associate Data Engineer.",
        answer="He was an Associate Data Engineer [source: role-visa].",
        reference="Associate Data Engineer at Visa.",
    )
    assert verdict == expected


def test_judge_uses_structured_output_so_the_verdict_cannot_be_prose() -> None:
    client = StubClient(Verdict(declined=False, grounded=True, quality=5, reasoning="ok"))
    judge_answer(client, question="q", context="c", answer="a", reference="r")
    assert client.messages.calls[0]["output_format"] is Verdict


def test_judge_runs_on_a_stronger_model_than_the_system_it_grades() -> None:
    """A cheap judge grading a cheap generator is a closed loop with no external check."""
    from ask_ben.config import ANSWER_MODEL, JUDGE_MODEL

    client = StubClient(Verdict(declined=False, grounded=True, quality=5, reasoning="ok"))
    judge_answer(client, question="q", context="c", answer="a", reference="r")
    assert client.messages.calls[0]["model"] == JUDGE_MODEL
    assert JUDGE_MODEL != ANSWER_MODEL


def test_judge_prompt_contains_the_context_and_the_answer() -> None:
    client = StubClient(Verdict(declined=False, grounded=False, quality=1, reasoning="unsupported"))
    judge_answer(client, question="q", context="THE-CONTEXT", answer="THE-ANSWER", reference="r")
    sent = str(client.messages.calls[0]["messages"])
    assert "THE-CONTEXT" in sent
    assert "THE-ANSWER" in sent


def test_judge_is_told_when_a_refusal_was_the_correct_outcome() -> None:
    """Otherwise a correct decline gets graded as an unhelpful answer."""
    client = StubClient(
        Verdict(declined=False, grounded=True, quality=5, reasoning="correct decline")
    )
    judge_answer(client, question="q", context="c", answer="a", reference=None)
    sent = str(client.messages.calls[0]["messages"])
    assert "should be refused" in sent


def test_the_judge_never_learns_which_arm_produced_the_answer() -> None:
    """Retriever and prompt version are what is being compared, so the judge must not see them."""
    client = StubClient(Verdict(declined=False, grounded=True, quality=5, reasoning="ok"))
    judge_answer(client, question="q", context="c", answer="a", reference="r")
    call = client.messages.calls[0]
    blob = (str(call["messages"]) + str(call["system"])).lower()
    for leak in ("bm25", "embedding retriever", "full-context", "prompt v1", "prompt v2"):
        assert leak not in blob


def test_agreement_is_one_when_judge_and_human_match() -> None:
    fraction, disagreements = judge_agreement({"a": True, "b": False}, {"a": True, "b": False})
    assert fraction == 1.0
    assert disagreements == []


def test_agreement_reports_which_items_disagree() -> None:
    fraction, disagreements = judge_agreement({"a": True, "b": True}, {"a": True, "b": False})
    assert fraction == 0.5
    assert disagreements == ["b"]


def test_agreement_only_scores_items_the_human_actually_labelled() -> None:
    """Ben labels ~20 of 30. Unlabelled items are not evidence either way."""
    fraction, disagreements = judge_agreement({"a": True, "b": False}, {"a": True})
    assert fraction == 1.0
    assert disagreements == []


def test_agreement_is_zero_when_nothing_is_labelled() -> None:
    """No labels is not perfect agreement. It is no evidence, and must not read as a pass."""
    fraction, disagreements = judge_agreement({"a": True}, {})
    assert fraction == 0.0
    assert disagreements == []


def test_load_human_labels_returns_empty_when_the_file_is_absent(tmp_path: Path) -> None:
    """Labels arrive after the first run, so earlier runs must still work."""
    assert load_human_labels(tmp_path / "nope.yaml") == {}


def test_load_human_labels_skips_unanswered_entries(tmp_path: Path) -> None:
    """A left-blank label means "unsure", which must not become False."""
    path = tmp_path / "labels.yaml"
    path.write_text("factual-degree: true\nfactual-aws: false\nreasoning-csp:\n", encoding="utf-8")
    assert load_human_labels(path) == {"factual-degree": True, "factual-aws": False}
