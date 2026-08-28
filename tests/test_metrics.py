from __future__ import annotations

from ask_ben.eval.metrics import (
    citation_validity,
    declined,
    fabricated_urls,
    load_golden,
    recall_at_k,
    reciprocal_rank,
    refusal_correct,
)


def test_recall_is_one_when_every_required_chunk_is_retrieved() -> None:
    assert recall_at_k(["a", "b", "c"], ("a", "b"), k=3) == 1.0


def test_recall_is_a_fraction_when_some_are_missed() -> None:
    assert recall_at_k(["a", "x", "y"], ("a", "b"), k=3) == 0.5


def test_recall_only_counts_the_first_k() -> None:
    assert recall_at_k(["x", "y", "a"], ("a",), k=2) == 0.0


def test_recall_is_one_when_nothing_is_required() -> None:
    """Out-of-scope questions have no must_cite and must not drag recall down."""
    assert recall_at_k(["x"], (), k=4) == 1.0


def test_reciprocal_rank_rewards_an_earlier_first_hit() -> None:
    assert reciprocal_rank(["a", "b"], ("a",)) == 1.0
    assert reciprocal_rank(["x", "a"], ("a",)) == 0.5


def test_reciprocal_rank_is_zero_when_nothing_relevant_is_retrieved() -> None:
    assert reciprocal_rank(["x", "y"], ("a",)) == 0.0


def test_recall_and_mrr_disagree_when_k_is_carrying_a_weak_retriever() -> None:
    """The real case from PR #8: correct chunk retrieved, but ranked third."""
    retrieved = ["snip-no-orm", "role-visa-billing-pipeline", "visa-isolation-in-iam-not-code"]
    must = ("visa-isolation-in-iam-not-code",)
    assert recall_at_k(retrieved, must, k=4) == 1.0
    assert reciprocal_rank(retrieved, must) == 1 / 3


def test_citation_validity_requires_every_citation_to_have_been_retrieved() -> None:
    assert citation_validity(["a"], ["a", "b"]) is True
    assert citation_validity(["c"], ["a", "b"]) is False


def test_citing_nothing_is_valid() -> None:
    """A correct refusal cites nothing. That must not score as invalid."""
    assert citation_validity([], ["a", "b"]) is True


def test_declined_covers_both_routes() -> None:
    """The gate is one way to decline; the model declining in prose is the other."""
    assert declined(refused=True, sources=[]) is True
    assert declined(refused=False, sources=[]) is True
    assert declined(refused=False, sources=["role-visa"]) is False


def test_refusal_correct_compares_expectation_to_behaviour() -> None:
    assert refusal_correct("refuse", refused=True, sources=[]) is True
    assert refusal_correct("refuse", refused=False, sources=["a"]) is False
    assert refusal_correct("answer", refused=False, sources=["a"]) is True
    assert refusal_correct("answer", refused=True, sources=[]) is False


def test_a_prose_decline_counts_as_a_correct_refusal() -> None:
    """Gate missed it, model caught it. Still the right outcome for the visitor."""
    assert refusal_correct("refuse", refused=False, sources=[]) is True


def test_fabricated_urls_flags_a_url_absent_from_the_corpus() -> None:
    """The exact failure seen live in PR #9."""
    text = "like [Snip, which uses raw SQL with no ORM](https://example.com)"
    assert fabricated_urls(text, "corpus mentions github.com/benbest123") == ["https://example.com"]


def test_fabricated_urls_accepts_a_url_that_is_in_the_corpus() -> None:
    corpus = "The repository is github.com/benbest123/url-shortener."
    assert fabricated_urls("See https://github.com/benbest123/url-shortener", corpus) == []


def test_fabricated_urls_is_empty_for_ordinary_prose() -> None:
    assert fabricated_urls("He worked at Visa as a data engineer.", "anything") == []


def test_the_golden_set_loads_and_is_well_formed() -> None:
    questions = load_golden()
    assert len(questions) >= 30

    ids = [q.id for q in questions]
    assert len(ids) == len(set(ids)), "duplicate golden question ids"

    for question in questions:
        assert question.expected in {"answer", "refuse"}
        if question.expected == "answer":
            assert question.must_cite, f"{question.id} must name the chunks it needs"
            assert question.reference, f"{question.id} needs a reference answer"
        else:
            assert not question.must_cite
            assert question.reference is None


def test_the_golden_set_covers_all_four_categories_at_the_planned_sizes() -> None:
    counts: dict[str, int] = {}
    for question in load_golden():
        counts[question.category] = counts.get(question.category, 0) + 1
    assert counts == {"factual": 10, "reasoning": 8, "out-of-scope": 7, "adversarial": 5}


def test_every_must_cite_id_exists_in_the_corpus() -> None:
    """Guards the interface between the golden set and the corpus chunk ids."""
    from ask_ben.chunks import load_corpus

    corpus_ids = {c.id for c in load_corpus()}
    for question in load_golden():
        for chunk_id in question.must_cite:
            assert chunk_id in corpus_ids, f"{question.id} cites unknown chunk '{chunk_id}'"


def test_the_golden_set_pairs_second_person_phrasings_for_normalisation() -> None:
    """Normalisation is measured, not assumed -- so both phrasings must be present."""
    ids = {q.id for q in load_golden()}
    pairs = [i for i in ids if i.endswith("-2p")]
    assert pairs, "no second-person variants to measure normalisation against"
    for variant in pairs:
        assert variant.removesuffix("-2p") in ids, f"{variant} has no third-person counterpart"
