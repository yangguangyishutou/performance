"""Synthetic markers count as exactly one token each (augmented-vocabulary accounting)."""
from __future__ import annotations

import re
from re import Pattern

# Full pipeline: Stage-1 + Stage-3 placeholders
RE_ALL_MARKERS: Pattern[str] = re.compile(
    r"<SYN_\d+>|<VAR>|<ATTR>|<STR>|<FSTR>|<NUM>"
)
# Stage-1 output only (for isolated syntax eval)
RE_SYN_ONLY: Pattern[str] = re.compile(r"<SYN_\d+>")


def encode(tokenizer, tok_type: str, text: str) -> list[int]:
    if tok_type == "tiktoken":
        return tokenizer.encode(text, allowed_special="all")
    return tokenizer.encode(text, add_special_tokens=False)


def count_augmented(
    text: str,
    tokenizer,
    tok_type: str,
    *,
    pattern: Pattern[str] = RE_ALL_MARKERS,
) -> int:
    hits = pattern.findall(text)
    if not hits:
        return len(encode(tokenizer, tok_type, text))
    stripped = pattern.sub("", text)
    return len(encode(tokenizer, tok_type, stripped)) + len(hits)
