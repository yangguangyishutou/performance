"""
Reuse existing tokenizer construction and tiktoken/HF encode path.

This is an **adapter** only: no new tokenization semantics here.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any, Tuple

from marker_count import encode as mc_encode


@lru_cache(maxsize=8)
def get_tokenizer_for_key(tokenizer_key: str) -> Tuple[Any, str]:
    """Return ``(tokenizer, tok_type)`` using ``config.EVAL_TOKENIZERS`` + ``repo_miner._load_tokenizer``."""
    from config import EVAL_TOKENIZERS
    from repo_miner import _load_tokenizer

    cfg = EVAL_TOKENIZERS[tokenizer_key]
    return _load_tokenizer(tokenizer_key, cfg)


def encode_text_true_len(text: str, tokenizer_key: str) -> int:
    """Raw id length (primary truth); not placeholder-augmented."""
    tokenizer, tok_type = get_tokenizer_for_key(tokenizer_key)
    return len(mc_encode(tokenizer, tok_type, text))
