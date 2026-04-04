"""
Primary truth source: raw tokenizer length.

Delegates to ``adapters.legacy_tokenizer_adapter`` so the rewrite tree does not
duplicate tokenizer construction.

Optional auxiliary placeholder-aware counts must stay in adapters and be named
``*_augmented`` / ``*_legacy_like`` at call sites — never mixed into primary
saved / intro / net decisions.
"""

from __future__ import annotations

from typing import Iterable, List


def measure_true_token_len(text: str, tokenizer_key: str) -> int:
    """
    Return len(tokenizer.encode(text)) using the same loader as the main repo.

    This is the **single canonical** length for A/B decisions in the rewrite framework.
    """
    from rewrite_stage3ab.adapters.legacy_tokenizer_adapter import encode_text_true_len

    return encode_text_true_len(text, tokenizer_key)


def measure_true_token_len_many(texts: Iterable[str], tokenizer_key: str) -> List[int]:
    from rewrite_stage3ab.adapters.legacy_tokenizer_adapter import encode_many_true_lens

    return encode_many_true_lens(texts, tokenizer_key)


def compute_intro_cost_true(intro_text: str, tokenizer_key: str) -> int:
    """True-token cost of emitting *intro_text* (preamble / table row / comment block)."""
    return measure_true_token_len(intro_text, tokenizer_key)


def compute_saved_true(before_text: str, after_text: str, tokenizer_key: str) -> int:
    """Non-negative gross tokens removed from the sequence (before − after)."""
    from rewrite_stage3ab.metrics.accounting import gross_saved_true

    b = measure_true_token_len(before_text, tokenizer_key)
    a = measure_true_token_len(after_text, tokenizer_key)
    return gross_saved_true(b, a)


def compute_net_saving_true(
    before_text: str,
    after_text: str,
    intro_tokens: int,
    tokenizer_key: str,
) -> int:
    """Net true-token delta including explicit intro token budget (already in true-token space)."""
    from rewrite_stage3ab.metrics.accounting import net_saved_true

    gross = compute_saved_true(before_text, after_text, tokenizer_key)
    return net_saved_true(gross, intro_tokens)
