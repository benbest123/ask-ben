"""Static configuration.

No logic lives here. This module must stay importable with no environment
variables set and no network access -- CI runs with no API keys, and a config
module that reads secrets at import time makes every test that touches it
require them.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = REPO_ROOT / "corpus"
INDEX_DIR = REPO_ROOT / "index"
PROMPTS_DIR = REPO_ROOT / "prompts"
EVALS_DIR = REPO_ROOT / "evals"
CORPUS_JSON = INDEX_DIR / "corpus.json"
EMBEDDINGS_NPY = INDEX_DIR / "embeddings.npy"

# Voyage: confirmed against live docs 2026-08-25. An earlier draft said
# voyage-3.5-lite, which no longer exists. Anthropic sells no embeddings
# endpoint, so generation and retrieval are separate vendor decisions.
EMBED_MODEL = "voyage-4-lite"
EMBED_DIM = 1024

# Serving: the cheapest tier that clears the eval bar. Once retrieval has done
# its job, generation is grounded summarisation of a few short passages -- and
# this is the cost that scales with visitor traffic.
ANSWER_MODEL = "claude-haiku-4-5-20251001"
# Judging: its verdicts are the evidence behind every quality claim in the
# README, and it runs ~30 times per evaluation on manual dispatch. A cheap judge
# grading a cheap generator is a closed loop with no external check on it.
JUDGE_MODEL = "claude-opus-5"

# The corpus is written in the third person and never contains the word "you".
# `normalise.py` rewrites second-person pronouns to this before retrieval.
SUBJECT_NAME = "Ben"

DEFAULT_PROMPT_VERSION = "v2"
# Switched from bm25 to embedding on 2026-08-28, on the retrieval-only sweep
# (evals/results/retrieval-*.json). Dense wins on every retrieval measure:
# recall@4 0.989 vs 0.900, MRR 0.983 vs 0.789. The MRR gap is the telling one --
# BM25 frequently finds the right chunk but buries it, so k=4 was carrying it.
DEFAULT_RETRIEVER = "embedding"
DEFAULT_K = 4

MAX_QUESTION_CHARS = 500

# Output is billed at 5x input, so this is the cheapest lever on abuse cost.
# Measured 2026-08-28 with count_tokens against the real corpus: a retrieval
# request is ~1,414 input tokens and a good answer is ~150 output tokens. At
# Haiku 4.5 rates that is ~$0.0022 a question, but at the old 1024-token cap the
# worst case was ~$0.0065 -- three times the cost for output nobody wants, since
# the prompt asks for two to four sentences. 300 leaves headroom over a typical
# answer while capping the tail.
MAX_ANSWER_TOKENS = 300

# Tuned 2026-08-28 against the golden set. Run:
#   python -m ask_ben.eval.run --retrieval-only --retriever <arm>
#
# BM25 scores are unbounded; cosine similarity is bounded to [-1, 1]. The two are
# not comparable, which is why these are keyed by retriever rather than shared.
#
# THE TUNING RATIONALE, because the two errors are not equally bad:
#   - A false refusal (gating a real question) is a visitor being told "I don't
#     know" about something the corpus covers. It is the worst outcome here.
#   - A missed refusal (an off-topic question reaching the model) costs $0.0021
#     and is then caught by the prompt-side decline, which the eval shows works.
# So the gate is tuned to eliminate false refusals and the prompt is the backstop
# -- the same two-path design ama-rag uses, arrived at from the numbers.
GATE_THRESHOLDS: dict[str, float] = {
    # Set just below the lowest-scoring legitimate question (0.275,
    # "Why did he not just filter by partner in the query?"). Off-topic questions
    # in the 0.275-0.427 band still get through; the prompt declines them.
    "embedding": 0.27,
    # Disabled deliberately, not left unset. BM25's distributions do not merely
    # overlap, they invert: the highest-scoring question that should be refused
    # scored 16.200 ("Who were his managers at Visa and can I have their contact
    # details?") while the lowest legitimate one scored 2.891 ("What did he
    # study?"). BM25 rewards length and vocabulary overlap, both of which a
    # hostile visitor controls -- so a long question stuffed with corpus words
    # outscores a short honest one, and no threshold can separate them. A gate
    # that an attacker can raise their own score against is worse than none,
    # because it looks like a control.
    "bm25": float("-inf"),
    # The control arm returns every chunk by definition; there is nothing to gate.
    "full": float("-inf"),
}

REFUSAL_TEXT = (
    "I don't have anything on that in Ben's notes. I can answer questions about his "
    "work at Visa, his projects, the technical decisions behind them, and what he's "
    "looking for next."
)
