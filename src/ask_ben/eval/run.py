"""The evaluation harness.

    python -m ask_ben.eval.run --retriever bm25 --prompt v2
    python -m ask_ben.eval.run --check-judge evals/results/<run>.json

Each run writes a JSON file (every row, for labelling and for diffing between
runs) and a markdown report (the summary and the failures).
"""

from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ask_ben.answer import answer_question
from ask_ben.chunks import load_corpus
from ask_ben.config import (
    ANSWER_MODEL,
    DEFAULT_K,
    DEFAULT_PROMPT_VERSION,
    EVALS_DIR,
    JUDGE_MODEL,
)
from ask_ben.eval.judge import judge_agreement, judge_answer, load_human_labels
from ask_ben.eval.metrics import (
    GoldenQuestion,
    citation_validity,
    fabricated_urls,
    load_golden,
    recall_at_k,
    reciprocal_rank,
    refusal_correct,
    retrieval_metrics_apply,
)
from ask_ben.retrieve import Hit, Retriever

RESULTS_DIR = EVALS_DIR / "results"

# USD per million tokens, (input, output). Kept here rather than fetched: a run
# that silently reprices itself is not reproducible.
PRICES: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001": (1.00, 5.00),
    "claude-haiku-4-5": (1.00, 5.00),
    "claude-sonnet-5": (2.00, 10.00),
    "claude-opus-5": (5.00, 25.00),
}


@dataclass(frozen=True)
class RunResult:
    config: dict[str, Any]
    rows: list[dict[str, Any]]
    summary: dict[str, Any]


def evaluate(
    questions: list[GoldenQuestion],
    *,
    retriever: Retriever,
    client: Any,
    judge_client: Any,
    prompt_version: str = DEFAULT_PROMPT_VERSION,
    model: str = ANSWER_MODEL,
    judge_model: str = JUDGE_MODEL,
    k: int = DEFAULT_K,
) -> RunResult:
    by_id = {chunk.id: chunk for chunk in load_corpus()}
    corpus_text = "\n".join(chunk.text for chunk in by_id.values())
    rows: list[dict[str, Any]] = []

    for question in questions:
        result = answer_question(
            question.question,
            retriever=retriever,
            client=client,
            prompt_version=prompt_version,
            model=model,
            k=k,
        )
        retrieved = list(result.meta["retrieved_ids"])

        # Rebuild the context from the ids rather than searching again. A second
        # search would be a second embedding API call per question on the dense
        # arm, and would risk grading the answer against different passages from
        # the ones that produced it.
        from ask_ben.prompt import render_context

        context = render_context([Hit(chunk=by_id[i], score=0.0) for i in retrieved if i in by_id])

        ranked = retrieval_metrics_apply(retriever.name)
        row: dict[str, Any] = {
            "id": question.id,
            "category": question.category,
            "question": question.question,
            "answer": result.text,
            # Stored so a human can label grounding without re-running anything.
            "context": context,
            "reference": question.reference,
            "sources": result.sources,
            "retrieved_ids": retrieved,
            "must_cite": list(question.must_cite),
            "expected": question.expected,
            "refused": result.refused,
            "gated": result.meta["gated"],
            "top_score": result.meta["top_score"],
            # Filled below: a gate refusal is deterministic, a prose decline is
            # the judge's call. Neither is inferred from whether sources exist.
            "declined": result.refused,
            "refusal_correct": None,
            "recall_at_k": recall_at_k(retrieved, question.must_cite, k) if ranked else None,
            "reciprocal_rank": reciprocal_rank(retrieved, question.must_cite) if ranked else None,
            "citation_valid": citation_validity(result.sources, retrieved),
            "fabricated_urls": fabricated_urls(result.text, corpus_text),
            "grounded": None,
            "quality": None,
            "judge_reasoning": None,
            "judge_input_tokens": 0,
            "judge_output_tokens": 0,
            "input_tokens": result.meta["input_tokens"],
            "output_tokens": result.meta["output_tokens"],
            "cache_read_input_tokens": result.meta["cache_read_input_tokens"],
            "cache_creation_input_tokens": result.meta["cache_creation_input_tokens"],
        }

        # Judge only answers that were actually generated. Grading a scripted
        # refusal spends money to evaluate a constant string.
        if not result.refused:
            judgement = judge_answer(
                judge_client,
                question=question.question,
                context=context,
                answer=result.text,
                reference=question.reference,
                model=judge_model,
            )
            verdict = judgement.verdict
            row["declined"] = verdict.declined
            row["grounded"] = verdict.grounded
            row["quality"] = verdict.quality
            row["judge_reasoning"] = verdict.reasoning
            row["judge_input_tokens"] = judgement.input_tokens
            row["judge_output_tokens"] = judgement.output_tokens

        row["refusal_correct"] = refusal_correct(question.expected, declined=row["declined"])
        rows.append(row)

    judged = [r for r in rows if r["grounded"] is not None]
    ranked_rows = [r for r in rows if r["recall_at_k"] is not None]
    summary = {
        "n": len(rows),
        "refusal_accuracy": statistics.fmean(r["refusal_correct"] for r in rows),
        "mean_recall_at_k": (
            statistics.fmean(r["recall_at_k"] for r in ranked_rows) if ranked_rows else None
        ),
        "mean_reciprocal_rank": (
            statistics.fmean(r["reciprocal_rank"] for r in ranked_rows) if ranked_rows else None
        ),
        "citation_validity": statistics.fmean(r["citation_valid"] for r in rows),
        "answers_with_fabricated_urls": sum(1 for r in rows if r["fabricated_urls"]),
        "gated": sum(1 for r in rows if r["gated"]),
        "groundedness": statistics.fmean(r["grounded"] for r in judged) if judged else None,
        "mean_quality": statistics.fmean(r["quality"] for r in judged) if judged else None,
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "cache_read_input_tokens": sum(r["cache_read_input_tokens"] for r in rows),
        "cache_creation_input_tokens": sum(r["cache_creation_input_tokens"] for r in rows),
        "judge_input_tokens": sum(r["judge_input_tokens"] for r in rows),
        "judge_output_tokens": sum(r["judge_output_tokens"] for r in rows),
    }
    summary["answer_cost_usd"] = round(
        summary["input_tokens"] / 1e6 * PRICES[model][0]
        + summary["output_tokens"] / 1e6 * PRICES[model][1]
        + summary["cache_read_input_tokens"] / 1e6 * PRICES[model][0] * 0.1
        + summary["cache_creation_input_tokens"] / 1e6 * PRICES[model][0] * 1.25,
        4,
    )
    summary["judge_cost_usd"] = round(
        summary["judge_input_tokens"] / 1e6 * PRICES[judge_model][0]
        + summary["judge_output_tokens"] / 1e6 * PRICES[judge_model][1],
        4,
    )
    summary["total_cost_usd"] = round(summary["answer_cost_usd"] + summary["judge_cost_usd"], 4)

    config = {
        "retriever": retriever.name,
        "prompt": prompt_version,
        "model": model,
        "judge_model": judge_model,
        "k": k,
    }
    return RunResult(config=config, rows=rows, summary=summary)


def _fmt(value: Any) -> str:
    if value is None:
        return "--"
    if isinstance(value, float):
        return f"{value:.3f}"
    return str(value)


def render_report(result: RunResult) -> str:
    c, s = result.config, result.summary
    lines = [
        f"# Eval -- {c['retriever']} / {c['prompt']} / {c['model']} (k={c['k']})",
        "",
        f"Judged by `{c['judge_model']}`.",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Questions | {s['n']} |",
        f"| Refusal accuracy | {_fmt(s['refusal_accuracy'])} |",
        f"| Gated (no API call) | {s['gated']} |",
        f"| Recall@k | {_fmt(s['mean_recall_at_k'])} |",
        f"| MRR | {_fmt(s['mean_reciprocal_rank'])} |",
        f"| Citation validity | {_fmt(s['citation_validity'])} |",
        f"| Answers with fabricated URLs | {s['answers_with_fabricated_urls']} |",
        f"| Groundedness (judged) | {_fmt(s['groundedness'])} |",
        f"| Mean quality (judged) | {_fmt(s['mean_quality'])} |",
        f"| Input tokens | {s['input_tokens']} |",
        f"| Output tokens | {s['output_tokens']} |",
        f"| Cache-read tokens | {s['cache_read_input_tokens']} |",
        f"| Cache-write tokens | {s['cache_creation_input_tokens']} |",
        f"| Judge tokens (in / out) | {s['judge_input_tokens']} / {s['judge_output_tokens']} |",
        f"| **Answer cost** | ${s['answer_cost_usd']:.4f} |",
        f"| **Judge cost** | ${s['judge_cost_usd']:.4f} |",
        f"| **Total cost** | ${s['total_cost_usd']:.4f} |",
        "",
        "## Failures",
        "",
    ]
    failures = [
        r
        for r in result.rows
        if not r["refusal_correct"]
        or r["grounded"] is False
        or not r["citation_valid"]
        or r["fabricated_urls"]
    ]
    if not failures:
        lines.append("None.")
    else:
        lines += ["| Question | Problem |", "| --- | --- |"]
        for row in failures:
            problems = []
            if not row["refusal_correct"]:
                expected = (
                    "should have declined" if row["expected"] == "refuse" else "wrongly declined"
                )
                problems.append(expected)
            if row["grounded"] is False:
                problems.append("not grounded")
            if not row["citation_valid"]:
                problems.append("invalid citation")
            if row["fabricated_urls"]:
                problems.append(f"fabricated URL ({', '.join(row['fabricated_urls'])})")
            lines.append(f"| `{row['id']}` | {'; '.join(problems)} |")
    return "\n".join(lines) + "\n"


def _check_judge(path: str) -> int:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    judge = {r["id"]: r["grounded"] for r in payload["rows"] if r["grounded"] is not None}
    human = load_human_labels()

    if not human:
        print("No human labels found in evals/human_labels.yaml.")
        print("The judge's scores are unvalidated until they exist, so they are not reported.")
        return 1

    fraction, disagreements = judge_agreement(judge, human)
    print(f"Judge/human agreement: {fraction:.1%} over {len(human)} labelled questions")
    if disagreements:
        print("\nDisagreements (judge vs Ben):")
        rows = {r["id"]: r for r in payload["rows"]}
        for qid in disagreements:
            row = rows.get(qid, {})
            print(f"  {qid}: judge={judge[qid]} ben={human[qid]}")
            if row.get("judge_reasoning"):
                print(f"      judge said: {row['judge_reasoning']}")
    else:
        print("No disagreements.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ask_ben.eval.run")
    parser.add_argument("--retriever", default="bm25", choices=["bm25", "embedding", "full"])
    parser.add_argument("--prompt", default=DEFAULT_PROMPT_VERSION)
    parser.add_argument("--model", default=ANSWER_MODEL)
    parser.add_argument("--judge-model", default=JUDGE_MODEL)
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    parser.add_argument("--check-judge", metavar="RESULT_JSON")
    args = parser.parse_args(argv)

    if args.check_judge:
        return _check_judge(args.check_judge)

    import anthropic

    from ask_ben.retrieve import build_retriever

    client = anthropic.Anthropic()
    result = evaluate(
        load_golden(),
        retriever=build_retriever(args.retriever),
        client=client,
        judge_client=client,
        prompt_version=args.prompt,
        model=args.model,
        judge_model=args.judge_model,
        k=args.k,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stem = f"{args.retriever}-{args.prompt}-{args.model}-k{args.k}"
    (RESULTS_DIR / f"{stem}.json").write_text(
        json.dumps(
            {"config": result.config, "rows": result.rows, "summary": result.summary}, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    report = render_report(result)
    (RESULTS_DIR / f"{stem}.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
