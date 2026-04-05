"""
Three-tier alias pool: strict single-token (true len == 1), low-cost multi-token, legal fallback.

Ranking: tier ascending, then ``token_len_true``, then lexicographic alias.
"""

from __future__ import annotations

import builtins
import keyword
import re
from dataclasses import dataclass
from typing import Any, Iterable

from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\Z")

# Tier 1: tokenizer reports exactly one token for the alias surface.
ALIAS_TIER_STRICT_SINGLE = 1
# Tier 2: multi-token but short (lowest cost band).
ALIAS_TIER_LOW_COST = 2
# Tier 3: remaining legal identifiers from the generator.
ALIAS_TIER_LEGAL_FALLBACK = 3

# Multi-token surfaces with token_len_true in [2, LOW_COST_MAX] land in tier 2.
LOW_COST_TOKEN_LEN_MAX = 6


@dataclass
class AliasCandidate:
    """One alias option with tier / tokenizer metadata."""

    alias: str
    token_len_true: int
    tier: int
    legal: bool
    conflict: bool
    scope_safe: bool
    is_strict_single_token: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "token_len_true": self.token_len_true,
            "tier": self.tier,
            "legal": self.legal,
            "conflict": self.conflict,
            "scope_safe": self.scope_safe,
            "is_strict_single_token": self.is_strict_single_token,
        }


def _builtin_names() -> set[str]:
    return {n for n in dir(builtins) if n.isidentifier()}


_BUILTINS = _builtin_names()


def is_legal_alias_surface(name: str) -> bool:
    if not _IDENT_RE.match(name):
        return False
    if keyword.iskeyword(name):
        return False
    if name in _BUILTINS:
        return False
    return True


def _classify_tier(token_len_true: int) -> tuple[int, bool]:
    """Return (tier, is_strict_single_token)."""
    if token_len_true == 1:
        return ALIAS_TIER_STRICT_SINGLE, True
    if 2 <= token_len_true <= LOW_COST_TOKEN_LEN_MAX:
        return ALIAS_TIER_LOW_COST, False
    return ALIAS_TIER_LEGAL_FALLBACK, False


def iter_legal_identifier_pool(*, max_n: int = 256) -> list[str]:
    """Deterministic short identifiers for pool enumeration."""
    out: list[str] = []
    for c in "abcdefghijklmnopqrstuvwxyz":
        out.append(c)
        if len(out) >= max_n:
            return out[:max_n]
    for c in "abcdefghijklmnopqrstuvwxyz":
        for d in "abcdefghijklmnopqrstuvwxyz0123456789":
            out.append(f"{c}{d}")
            if len(out) >= max_n:
                return out[:max_n]
    i = 0
    while len(out) < max_n:
        out.append(f"x{i}")
        i += 1
    return out[:max_n]


def build_ranked_alias_candidates(
    tokenizer_key: str,
    *,
    forbidden: set[str],
    pool_cap: int = 256,
) -> list[AliasCandidate]:
    """
    Full ranked pool (legal surfaces only), ordered for ``pick_best_alias``.

    Sort key: ``(tier, token_len_true, alias)``.
    """
    pool = iter_legal_identifier_pool(max_n=pool_cap)
    ranked: list[AliasCandidate] = []
    for name in pool:
        legal = is_legal_alias_surface(name)
        conflict = name in forbidden
        scope_safe = legal and not conflict
        tl = measure_true_token_len(name, tokenizer_key) if legal else 10**9
        tier, is_single = _classify_tier(tl) if legal else (ALIAS_TIER_LEGAL_FALLBACK, False)
        ranked.append(
            AliasCandidate(
                alias=name,
                token_len_true=tl,
                tier=tier,
                legal=legal,
                conflict=conflict,
                scope_safe=scope_safe,
                is_strict_single_token=is_single,
            )
        )
    ranked.sort(key=lambda c: (c.tier, c.token_len_true, c.alias))
    return ranked


def alias_pool_stats(ranked: list[AliasCandidate]) -> dict[str, Any]:
    """Telemetry-friendly counts over a ranked pool."""
    legal = [c for c in ranked if c.legal]
    return {
        "alias_pool_total": len(ranked),
        "alias_pool_legal_total": len(legal),
        "alias_pool_single_token_count": sum(1 for c in legal if c.is_strict_single_token),
        "alias_pool_low_cost_count": sum(1 for c in legal if c.tier == ALIAS_TIER_LOW_COST),
        "alias_pool_fallback_tier_count": sum(1 for c in legal if c.tier == ALIAS_TIER_LEGAL_FALLBACK),
    }


def pick_best_alias(
    tokenizer_key: str,
    *,
    forbidden: set[str],
    pool_cap: int = 256,
) -> tuple[AliasCandidate | None, dict[str, Any]]:
    """
    First scope-safe candidate in tier / token / lex order.

    Returns ``(candidate | None, selection_meta)`` where meta includes pool stats
    and, when selected, ``alias_selected_token_len_true`` and ``alias_selection_tier``.
    """
    ranked = build_ranked_alias_candidates(tokenizer_key, forbidden=forbidden, pool_cap=pool_cap)
    meta = alias_pool_stats(ranked)
    meta["alias_selection_tier"] = None
    meta["alias_selected_token_len_true"] = None
    meta["alias_selected"] = None
    for c in ranked:
        if c.scope_safe:
            meta["alias_selection_tier"] = c.tier
            meta["alias_selected_token_len_true"] = c.token_len_true
            meta["alias_selected"] = c.alias
            return c, meta
    return None, meta


def rank_aliases_by_tokenizer(
    names: Iterable[str],
    tokenizer_key: str,
    *,
    forbidden: set[str],
) -> list[AliasCandidate]:
    """Ad-hoc ranking of explicit *names* (used by diagnostics)."""
    ranked: list[AliasCandidate] = []
    for name in names:
        legal = is_legal_alias_surface(name)
        conflict = name in forbidden
        scope_safe = legal and not conflict
        tl = measure_true_token_len(name, tokenizer_key) if legal else 10**9
        tier, is_single = _classify_tier(tl) if legal else (ALIAS_TIER_LEGAL_FALLBACK, False)
        ranked.append(
            AliasCandidate(
                alias=name,
                token_len_true=tl,
                tier=tier,
                legal=legal,
                conflict=conflict,
                scope_safe=scope_safe,
                is_strict_single_token=is_single,
            )
        )
    ranked.sort(key=lambda c: (c.tier, c.token_len_true, c.alias))
    return ranked


def build_alias_candidate_table(
    tokenizer_key: str,
    *,
    forbidden: set[str],
    pool_cap: int = 128,
) -> list[dict[str, Any]]:
    ranked = build_ranked_alias_candidates(tokenizer_key, forbidden=forbidden, pool_cap=pool_cap)
    return [c.to_dict() for c in ranked if c.legal][:48]
