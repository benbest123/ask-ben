from ask_ben.normalise import normalise_question


def test_possessive_your_becomes_the_possessive_name() -> None:
    assert normalise_question("what's your AWS experience?") == "what's Ben's AWS experience?"


def test_subject_you_becomes_the_name() -> None:
    assert normalise_question("where did you work?") == "where did Ben work?"


def test_contraction_you_are() -> None:
    assert normalise_question("what are you're strengths") == "what are Ben is strengths"


def test_contraction_you_have() -> None:
    assert normalise_question("what have you've built") == "what have Ben has built"


def test_yours_becomes_possessive() -> None:
    assert normalise_question("is that project yours?") == "is that project Ben's?"


def test_yourself() -> None:
    assert normalise_question("tell me about yourself") == "tell me about Ben"


def test_capitalisation_at_the_start_of_a_sentence() -> None:
    """Every replacement starts with a proper noun, so casing needs no special handling."""
    assert normalise_question("Your degree?") == "Ben's degree?"
    assert normalise_question("You worked where?") == "Ben worked where?"


def test_word_boundaries_protect_unrelated_words() -> None:
    """`yourself` should rewrite; `youthful` and `young` must not."""
    assert normalise_question("a youthful and young thing") == "a youthful and young thing"
    assert normalise_question("yourselves") == "Ben"


def test_a_question_with_no_second_person_is_returned_unchanged() -> None:
    original = "Which cloud provider has Ben used most?"
    assert normalise_question(original) == original


def test_normalisation_is_idempotent() -> None:
    """The output contains no second-person pronouns, so re-applying is a no-op."""
    once = normalise_question("what's your view on you're own work, yourself?")
    assert normalise_question(once) == once
