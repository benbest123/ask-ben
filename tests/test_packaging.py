"""Keep the two dependency lists honest.

Vercel installs from `requirements.txt`; everything else installs from
`pyproject.toml`. Nothing makes them agree, so a dependency added in one place
works locally and in CI and then fails at runtime in production, which is the
worst place to find out.
"""

from __future__ import annotations

import tomllib

from ask_ben.config import REPO_ROOT


def _names(specs: list[str]) -> set[str]:
    """Package names only, normalised -- versions are allowed to differ."""
    out = set()
    for spec in specs:
        spec = spec.strip()
        if not spec or spec.startswith("#"):
            continue
        for separator in (">=", "==", "~=", ">", "<", "["):
            spec = spec.split(separator)[0]
        out.add(spec.strip().lower().replace("_", "-"))
    return out


def test_requirements_matches_pyproject_dependencies() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = _names(pyproject["project"]["dependencies"])
    deployed = _names((REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines())
    assert declared == deployed, (
        f"only in pyproject: {sorted(declared - deployed)}; "
        f"only in requirements.txt: {sorted(deployed - declared)}"
    )


def test_no_heavyweight_ml_dependency_reaches_the_bundle() -> None:
    """Vercel caps an unzipped function bundle at 250MB.

    That cap is why embeddings are a Voyage HTTP call rather than a local
    sentence-transformers model. If torch ever appears here, that decision has
    been quietly reversed and the deploy will fail.
    """
    deployed = _names((REPO_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines())
    assert not deployed & {"torch", "sentence-transformers", "transformers"}


def test_vercel_bundles_the_files_the_service_reads_at_runtime() -> None:
    """The function needs the package, the prompts and the committed index.

    None of those live under api/, and Vercel bundles only what it is told to.
    A missing index is a 500 on the first request, not a build failure.
    """
    import json

    config = json.loads((REPO_ROOT / "vercel.json").read_text(encoding="utf-8"))
    included = config["functions"]["api/ask.py"]["includeFiles"]
    for required in ("src", "prompts", "index"):
        assert required in included
