"""
Token economics helpers for A (signatures only this round).

TODO: Replace static ``min_occ`` style gates with **marginal true-token delta** per alias.
TODO: Plug tokenizer-aware alias length and collision penalties.
TODO: Add local combo / greedy rescoring hooks (see ``implementation_stub``).
"""

from __future__ import annotations

from typing import Any


def estimate_alias_intro_cost(alias_surface: str, tokenizer_key: str) -> int:
    """
    True-token cost to introduce *alias_surface* into the side channel / preamble.

    TODO: Multiplex per-occurrence amortization once codebook accounting lands.
    """
    del alias_surface, tokenizer_key
    return 0


def estimate_alias_replacement_gain(
    raw_span: str,
    replaced_with: str,
    tokenizer_key: str,
) -> int:
    """
    Expected gross true-token reduction for one replacement (before intro amortization).

    TODO: Use ``measure_true_token_len`` on span vs replacement + context penalties.
    """
    del raw_span, replaced_with, tokenizer_key
    return 0


def compute_token_economics_score(
    gross_gain: int,
    intro_cost: int,
    risk_penalty: float = 0.0,
) -> float:
    """Scalar score for ranking; higher is better."""
    del risk_penalty
    return float(gross_gain - intro_cost)
