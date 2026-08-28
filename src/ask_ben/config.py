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
DEFAULT_RETRIEVER = "bm25"
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

# Provisional. Tuned against evals/golden.yaml in Task 11 and updated there.
# BM25 scores are unbounded; cosine similarity is bounded to [-1, 1]. The two
# are therefore not comparable, which is why thresholds are keyed by retriever
# name rather than shared. The full-context arm returns every chunk by
# definition, so gating it would be meaningless.
GATE_THRESHOLDS: dict[str, float] = {
    "bm25": 4.0,
    "embedding": 0.45,
    "full": float("-inf"),
}

REFUSAL_TEXT = (
    "I don't have anything on that in Ben's notes. I can answer questions about his "
    "work at Visa, his projects, the technical decisions behind them, and what he's "
    "looking for next."
)
