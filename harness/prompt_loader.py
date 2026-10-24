"""Load prompt files at runtime.

The Prompt Fixer contract lives in prompts/prompt-fixer.md. Call
load_prompt("prompt-fixer"). Do not copy that file's text into code.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS = ROOT / "prompts"

_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def load_prompt(name: str) -> str:
    """Return the UTF-8 text of prompts/<name>.md.

    Raises ValueError for names that are not a single path segment.
    Raises FileNotFoundError when that file is not in prompts/.
    """
    if not isinstance(name, str) or _NAME.fullmatch(name) is None:
        raise ValueError(f"invalid prompt name: {name!r}")
    path = (PROMPTS / f"{name}.md").resolve()
    if path.parent != PROMPTS.resolve():
        raise ValueError(f"invalid prompt name: {name!r}")
    if not path.is_file():
        raise FileNotFoundError(f"prompt not found: {name}")
    return path.read_text(encoding="utf-8")
