"""Structural checks on the real corpus.

These do not judge the writing -- that is Ben's review gate. They enforce the
properties the design depends on: that the chunk ids the golden set references
exist, that chunks stay small enough for the no-chunking decision to hold, and
that nothing lands in a public, world-readable corpus that should not be there.
"""

from ask_ben.chunks import load_corpus

EXPECTED_IDS = {
    # Facts (12) -- what Ben did
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
    # Projects (5)
    "project-snip",
    "project-epl-tracker",
    "project-rym-hide-ratings",
    "project-personal-site",
    "project-ask-ben",
    # Decisions (9) -- why he did it that way, each with its rejected alternative
    "visa-isolation-in-iam-not-code",
    "visa-polling-to-timestamp",
    "visa-csp-not-widened",
    "visa-reconciling-a-black-box",
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


def test_thelook_is_not_a_corpus_topic() -> None:
    """theLook was a dbt tutorial, not a project, and the corpus said otherwise.

    It had six chunks including five decision chunks, which claimed more for it
    than it earns. It survives only as a line in skills-languages-data. This
    test exists so the material does not drift back in.
    """
    for chunk in load_corpus():
        if chunk.id == "skills-languages-data":
            continue
        assert "thelook" not in chunk.text.lower(), f"{chunk.id} mentions theLook"


def test_no_chunk_overstates_the_right_to_work() -> None:
    """Ben is on a Youth Mobility Visa until June 2029, not open-ended leave.

    The first corpus draft said "full right to work in the UK" in three places.
    That is the kind of error a grounded system will repeat confidently and
    without hedging, because it is faithfully reporting what it was given -- so
    it has to be caught in the corpus rather than in the prompt.
    """
    for chunk in load_corpus():
        assert "full right to work" not in chunk.text.lower(), f"{chunk.id} overstates work rights"
