"""
Savings accounting in **true-token** space.

Definitions:
- **gross_saved_true**: tokens removed from the sequence before intro (``before - after``).
- **intro_cost_true**: tokens paid for vocabulary / alias / reference intros.
- **net_saved_true**: ``gross_saved_true - intro_cost_true``.

This module does not mutate telemetry; callers attach results to ``AChannelResult`` / events.
"""

from __future__ import annotations


def gross_saved_true(before_tokens: int, after_tokens: int) -> int:
    return max(0, before_tokens - after_tokens)


def intro_cost_true(n_intro_tokens: int) -> int:
    return max(0, n_intro_tokens)


def net_saved_true(gross_saved: int, intro_tokens: int) -> int:
    return gross_saved - intro_cost_true(intro_tokens)


def compute_net_saving_true(
    before_text: str,
    after_text: str,
    intro_tokens: int,
    tokenizer_key: str,
) -> int:
    """
    End-to-end net saving using ``measure_true_token_len`` for before/after spans.

    TODO: Split intro into per-assignment rows when ledger granularity is required.
    """
    from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len

    b = measure_true_token_len(before_text, tokenizer_key)
    a = measure_true_token_len(after_text, tokenizer_key)
    gross = gross_saved_true(b, a)
    return net_saved_true(gross, intro_tokens)
