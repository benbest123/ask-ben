from ask_ben import config


def test_embedding_model_is_voyage_4_lite() -> None:
    assert config.EMBED_MODEL == "voyage-4-lite"
    assert config.EMBED_DIM == 1024


def test_serving_and_judging_models_are_split() -> None:
    """Serving is the cost that scales with traffic; judging is the evidence.

    They are deliberately different tiers -- see the spec, "Model choice".
    """
    assert config.ANSWER_MODEL == "claude-haiku-4-5-20251001"
    assert config.JUDGE_MODEL == "claude-opus-5"


def test_corpus_dir_is_at_repo_root() -> None:
    assert config.CORPUS_DIR == config.REPO_ROOT / "corpus"


def test_full_context_retriever_never_gates() -> None:
    """The control arm returns every chunk, so a relevance gate on it is meaningless."""
    assert config.GATE_THRESHOLDS["full"] == float("-inf")


def test_gate_thresholds_cover_every_retriever() -> None:
    assert set(config.GATE_THRESHOLDS) == {"bm25", "embedding", "full"}


def test_config_imports_without_environment_or_network() -> None:
    """config.py must stay importable with no API keys set -- CI has none."""
    assert config.MAX_QUESTION_CHARS > 0
    assert config.MAX_ANSWER_TOKENS > 0
