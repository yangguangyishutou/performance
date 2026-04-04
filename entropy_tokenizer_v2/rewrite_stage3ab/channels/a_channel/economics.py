"""
Token economics for A: true-token intro vs gross replacement gain.

``min_occ`` is optional soft filtering only; acceptance is **net_true > 0**.
"""

from __future__ import annotations

from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len


def estimate_alias_intro_cost(alias_surface: str, tokenizer_key: str, *, ledger_line_template: str | None = None) -> int:
    """
    Tokens to introduce one alias binding in a side ledger (comment line).

    Default template mimics a one-line audit comment plus the alias token itself.
    """
    if ledger_line_template is None:
        ledger_line_template = f"# AMAP old -> {alias_surface}\n"
    return measure_true_token_len(ledger_line_template, tokenizer_key)


def estimate_alias_replacement_gain(
    raw_span: str,
    replaced_with: str,
    tokenizer_key: str,
) -> int:
    """Per-occurrence gross token reduction (non-negative)."""
    a = measure_true_token_len(raw_span, tokenizer_key)
    b = measure_true_token_len(replaced_with, tokenizer_key)
    return max(0, a - b)


def net_gain_for_alias(
    raw_span: str,
    alias: str,
    occ: int,
    tokenizer_key: str,
) -> tuple[int, int, int]:
    """
    Returns ``(gross_gain_total, intro_tokens, net_true)`` in true-token space.
    """
    per = estimate_alias_replacement_gain(raw_span, alias, tokenizer_key)
    gross = per * occ
    intro = estimate_alias_intro_cost(alias, tokenizer_key)
    net = gross - intro
    return gross, intro, net


def compute_token_economics_score(
    gross_gain: int,
    intro_cost: int,
    risk_penalty: float = 0.0,
) -> float:
    """Scalar score for ranking; higher is better."""
    return float(gross_gain - intro_cost - risk_penalty)


def soft_min_occ_filter(occ: int, min_occ: int) -> bool:
    """Auxiliary filter only — economics may still accept occ < min_occ when net > 0 elsewhere."""
    return occ >= min_occ
