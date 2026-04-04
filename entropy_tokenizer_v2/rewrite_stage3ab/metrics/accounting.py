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
