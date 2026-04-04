"""
Legal identifier pool, tokenizer-aware ranking, and scope conflict metadata.

All ranking uses **true tokenizer length** (never raw character count alone).
"""

from __future__ import annotations

import builtins
import keyword
import re
from dataclasses import dataclass
from typing import Any, Iterable

from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\Z")


@dataclass
class AliasCandidate:
    """One alias option with economics / legality metadata."""

    alias: str
    token_len_true: int
    legal: bool
    conflict: bool
    scope_safe: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "alias": self.alias,
            "token_len_true": self.token_len_true,
            "legal": self.legal,
            "conflict": self.conflict,
            "scope_safe": self.scope_safe,
            "single_token_preferred": self.token_len_true <= 8,
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


def iter_legal_identifier_pool(*, max_n: int = 256) -> list[str]:
    """
    Deterministic short identifiers: ``a``..``z``, ``_a``.., then ``x0``..``x99``, etc.
    """
    out: list[str] = []
    # single letters
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


def rank_aliases_by_tokenizer(
    names: Iterable[str],
    tokenizer_key: str,
    *,
    forbidden: set[str],
) -> list[AliasCandidate]:
    """Sort by ``token_len_true`` ascending, then lexicographic for stability."""
    ranked: list[AliasCandidate] = []
    for name in names:
        legal = is_legal_alias_surface(name)
        conflict = name in forbidden
        scope_safe = legal and not conflict
        tl = measure_true_token_len(name, tokenizer_key) if legal else 999999
        ranked.append(
            AliasCandidate(
                alias=name,
                token_len_true=tl,
                legal=legal,
                conflict=conflict,
                scope_safe=scope_safe,
            )
        )
    ranked.sort(key=lambda c: (c.token_len_true, c.alias))
    return ranked


def pick_best_alias(
    tokenizer_key: str,
    *,
    forbidden: set[str],
    pool_cap: int = 128,
) -> AliasCandidate | None:
    pool = iter_legal_identifier_pool(max_n=pool_cap)
    ranked = rank_aliases_by_tokenizer(pool, tokenizer_key, forbidden=forbidden)
    for c in ranked:
        if c.scope_safe:
            return c
    return None


def build_alias_candidate_table(
    tokenizer_key: str,
    *,
    forbidden: set[str],
    pool_cap: int = 128,
) -> list[dict[str, Any]]:
    """Serialized rows for telemetry."""
    pool = iter_legal_identifier_pool(max_n=pool_cap)
    ranked = rank_aliases_by_tokenizer(pool, tokenizer_key, forbidden=forbidden)
    return [c.to_dict() for c in ranked if c.legal][:32]
