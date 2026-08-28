"""Structural checks on the real corpus.

These do not judge the writing -- that is Ben's review gate. They enforce the
properties the design depends on: that the chunk ids the golden set references
exist, that chunks stay small enough for the no-chunking decision to hold, and
that nothing lands in a public, world-readable corpus that should not be there.
"""

from ask_ben.chunks import load_corpus

EXPECTED_IDS = {
    # Facts (12)
    "profile-summary",
    "role-visa",
    "role-visa-billing-pipeline",
    "role-visa-legacy-billing",
    "role-visa-qlik",
    "role-visa-solo-cover",
    "role-russell-mcveagh",
    "role-tin",
    "education",
    "certifications",
    "skills-languages-data",
    "skills-cloud-bi",
    # Projects (6)
    "project-snip",
    "project-thelook",
    "project-epl-tracker",
    "project-rym-hide-ratings",
    "project-personal-site",
    "project-ask-ben",
    # Decisions (10)
    "thelook-bigquery-over-snowflake",
    "thelook-star-schema",
    "thelook-degenerate-dimension",
    "thelook-margin-approximation",
    "thelook-tests-at-staging",
    "snip-no-orm",
    "personal-site-window-manager",
    "askben-no-vector-db",
    "askben-no-chunking",
    "askben-eval-approach",
    # Meta (3)
    "what-im-looking-for",
    "availability-and-contact",
    "how-i-work",
}


def test_every_expected_chunk_exists() -> None:
    """Chunk ids are an interface -- evals/golden.yaml cites them by name."""
    assert {c.id for c in load_corpus()} == EXPECTED_IDS


def test_chunks_are_sized_for_atomic_retrieval() -> None:
    """The no-chunking decision only holds if chunks are authored at the right size.

    A 600-word chunk is a chunking problem wearing a disguise: retrieval would
    return it whole, most of it irrelevant, and the prompt would pay for all of it.
    """
    for chunk in load_corpus():
        words = len(chunk.body.split())
        assert 60 <= words <= 320, f"{chunk.id} has {words} words"


def test_every_chunk_is_tagged() -> None:
    for chunk in load_corpus():
        assert chunk.tags, f"{chunk.id} has no tags"


def test_titles_are_unique() -> None:
    """Titles are shown to the visitor as source labels, so duplicates are confusing."""
    titles = [c.title for c in load_corpus()]
    assert len(titles) == len(set(titles))


def test_corpus_holds_no_contact_details_worth_scraping() -> None:
    """The corpus is public and is the bot's entire universe.

    A question-answering endpoint that will emit an email address or a number on
    request is a scraping target. Contact routes stay on the site itself, behind
    a human visit. See corpus/availability-and-contact.md.
    """
    banned = ("salary", "@gmail", "phone", "+44", "£")
    for chunk in load_corpus():
        lowered = chunk.text.lower()
        for term in banned:
            assert term not in lowered, f"{chunk.id} mentions '{term}'"
