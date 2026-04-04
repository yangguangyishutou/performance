"""Bridges to the production ``entropy_tokenizer_v2`` package (minimal surface)."""

from rewrite_stage3ab.adapters.legacy_tokenizer_adapter import (
    encode_text_true_len,
    get_tokenizer_for_key,
)

__all__ = ["encode_text_true_len", "get_tokenizer_for_key"]
