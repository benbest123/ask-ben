"""Rewrite second-person questions into the third person before retrieval.

Visitors ask "what's *your* AWS experience?" but the corpus is written in the
third person and never contains the word "you". Both retrievers score the
question against corpus text, so the pronoun is dead weight at best: for BM25 it
contributes a token that appears in no chunk, and for embeddings it shifts the
query vector away from every document.

Borrowed, with attribution, from `njranum/ama-rag` (`query/normalise.py`), which
measured the un-rewritten form scoring 0.10-0.23 lower in cosine similarity and
false-refusing at the relevance gate. This project measures its own version --
see the golden set, which carries both phrasings of several questions so the fix
is evidenced rather than assumed.

Deliberately a regex rather than a model call. It runs on every query, it must
not fail, and it must not cost anything.
"""

from __future__ import annotations

import re

from ask_ben.config import SUBJECT_NAME

# Ordered longest-first only for readability -- \b handles the prefix overlaps,
# so `\byour\b` cannot match inside "yours" or "yourself", and `\byou\b` cannot
# match inside "youthful" or "young".
_SUBSTITUTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\byou\s?'\s?re\b", re.IGNORECASE), f"{SUBJECT_NAME} is"),
    (re.compile(r"\byou\s?'\s?ve\b", re.IGNORECASE), f"{SUBJECT_NAME} has"),
    (re.compile(r"\byourselves\b", re.IGNORECASE), SUBJECT_NAME),
    (re.compile(r"\byourself\b", re.IGNORECASE), SUBJECT_NAME),
    (re.compile(r"\byours\b", re.IGNORECASE), f"{SUBJECT_NAME}'s"),
    (re.compile(r"\byour\b", re.IGNORECASE), f"{SUBJECT_NAME}'s"),
    (re.compile(r"\byou\b", re.IGNORECASE), SUBJECT_NAME),
)


def normalise_question(text: str) -> str:
    """Map second-person pronouns to the subject's name.

    Idempotent: the output contains no second-person pronouns, so re-applying it
    is a no-op. A question that never had any is returned byte-identical.

    Capitalisation needs no special handling -- every replacement begins with a
    proper noun, so "Your AWS experience?" and "what's your AWS experience?" both
    come out correctly cased.
    """
    for pattern, replacement in _SUBSTITUTIONS:
        text = pattern.sub(replacement, text)
    return text
