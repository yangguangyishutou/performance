"""Validation entrypoints and helpers (lazy to avoid runpy double-import warnings)."""

from __future__ import annotations

from typing import Any, Tuple

__all__ = ["run_smoke"]


def run_smoke(tokenizer_key: str = "gpt4") -> Tuple[Any, Any]:
    from rewrite_stage3ab.validation.smoke_runner import run_smoke as _impl

    return _impl(tokenizer_key)
