"""
Primary truth source: raw tokenizer length.

Delegates to ``adapters.legacy_tokenizer_adapter`` so the rewrite tree does not
duplicate tokenizer construction. Future: swap adapter for a unified eval service.

TODO: Optional second entrypoint ``measure_augmented_token_len`` for parity with
``marker_count.count_augmented`` when economics need placeholder-aware costs.
"""

from __future__ import annotations


def measure_true_token_len(text: str, tokenizer_key: str) -> int:
    """
    Return len(tokenizer.encode(text)) using the same loader as the main repo.

    This is the **single canonical** length for A/B decisions in the rewrite framework.
    """
    from rewrite_stage3ab.adapters.legacy_tokenizer_adapter import encode_text_true_len

    return encode_text_true_len(text, tokenizer_key)
