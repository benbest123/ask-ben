"""Vercel serverless entrypoint.

Vercel's Python runtime looks for a module-level ASGI app in a file under
`api/`. All the logic lives in `ask_ben.service`; this file exists only to
expose it and to make the src-layout package importable.

The `sys.path` insert is doing real work rather than being cargo cult: the
package lives in `src/ask_ben`, and Vercel installs `requirements.txt` without
installing this repo as a package, so `ask_ben` is not on the path by default.
The alternative is flattening the package to the repository root, which would
mean giving up the src layout everywhere else to satisfy one deployment target.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ask_ben.service import app  # noqa: E402

__all__ = ["app"]
