"""
Bridge for formatting before/after snippets compatible with existing eval markdown style.

TODO: Call into ``eval`` / scripts helpers when deduplicating example ledgers.
"""

from __future__ import annotations


def clip_snippet(text: str, limit: int = 400) -> str:
    """Same spirit as ``eval_stage3ab_starcoder_200k._clip`` — keep local to avoid import cycles."""
    text = text.replace("\r\n", "\n")
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
