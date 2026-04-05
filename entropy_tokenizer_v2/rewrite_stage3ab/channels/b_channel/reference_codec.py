"""
Reference-style compression (SemDeDup-flavored): true-token accounting + span-safe rewrite.
"""

from __future__ import annotations

import ast as ast_module
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len


def _python_value_repr_from_literal_segment(seg: str) -> str:
    try:
        v = ast_module.literal_eval(seg)
        return repr(v)
    except Exception:
        return seg


def _source_span_matches_cluster_literal(slice_: str, members: set[str]) -> bool:
    """True if *slice_* equals some member, or ``ast.literal_eval`` matches (e.g. ``'a'`` vs ``\"a\"``)."""
    if slice_ in members:
        return True
    try:
        v_slice = ast_module.literal_eval(slice_)
    except Exception:
        return False
    for m in members:
        try:
            if ast_module.literal_eval(m) == v_slice:
                return True
        except Exception:
            continue
    return False


@dataclass
class ReferenceEmission:
    symbol: str
    representative: str
    member_texts: list[str]
    member_spans: list[tuple[int, int]]
    intro_tokens_true: int = 0
    raw_total_true: int = 0
    ref_total_true: int = 0
    net_true: int = 0
    representative_meta: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class ReferenceCodec(Protocol):
    def select_representative(self, members: list[str], ctx: dict[str, Any]) -> str:
        ...

    def emit(self, representative: str, symbol: str, ctx: dict[str, Any]) -> ReferenceEmission:
        ...

    def rewrite_text(self, text: str, emission: ReferenceEmission, ctx: dict[str, Any]) -> str:
        ...


class ReferenceCodecV1:
    """
    Representative: min true-token length, then char length, then lexicographic, then index.
    Rewrite: prefer recorded ``member_spans`` (half-open); never global blind replace when spans exist.
    """

    def __init__(self) -> None:
        self._last_rep_meta: dict[str, Any] = {}

    def select_representative(self, members: list[str], ctx: dict[str, Any]) -> str:
        tok = ctx.get("tokenizer_key", "gpt4")
        if not members:
            self._last_rep_meta = {}
            return ""
        scored: list[tuple[int, int, str, int]] = []
        for i, m in enumerate(members):
            tl = measure_true_token_len(m, tok)
            scored.append((tl, len(m), m, i))
        scored.sort(key=lambda x: (x[0], x[1], x[2]))
        best = scored[0]
        self._last_rep_meta = {
            "representative_token_len_true": best[0],
            "representative_char_len": best[1],
            "representative_index": best[3],
            "tiebreak_rule": "token_len_true_then_char_len_then_lex_then_index",
        }
        return best[2]

    def emit(self, representative: str, symbol: str, ctx: dict[str, Any]) -> ReferenceEmission:
        tok = ctx.get("tokenizer_key", "gpt4")
        members = list(ctx.get("cluster_members", []))
        if not members:
            members = [representative]
        spans = [tuple(x) for x in ctx.get("member_spans", [])]
        rhs = _python_value_repr_from_literal_segment(representative)
        preamble = f"{symbol} = {rhs}\n"
        intro = measure_true_token_len(preamble, tok)
        raw_total = sum(measure_true_token_len(m, tok) for m in members)
        per_sym = measure_true_token_len(symbol, tok)
        ref_total = intro + per_sym * len(members)
        net = raw_total - ref_total
        rep_meta = dict(self._last_rep_meta)
        return ReferenceEmission(
            symbol=symbol,
            representative=representative,
            member_texts=list(members),
            member_spans=spans,
            intro_tokens_true=intro,
            raw_total_true=raw_total,
            ref_total_true=ref_total,
            net_true=net,
            representative_meta=rep_meta,
            meta={
                "preamble": preamble,
                "cluster_path": ctx.get("cluster_path", ""),
                "fallback_reason": ctx.get("fallback_reason", ""),
            },
        )

    def rewrite_text(self, text: str, emission: ReferenceEmission, ctx: dict[str, Any]) -> str:
        diag = ctx.setdefault(
            "b_rewrite_diagnostics",
            {
                "span_hits": 0,
                "span_hits_literal_equiv": 0,
                "span_misses_bounds": 0,
                "span_misses_slice_mismatch": 0,
                "global_replace_fallback_clusters": 0,
            },
        )
        preamble = emission.meta.get("preamble", "")
        spans = sorted(emission.member_spans, key=lambda t: t[0], reverse=True)
        members_set = set(emission.member_texts)
        if spans:
            out = text
            for start, end in spans:
                if not (0 <= start < end <= len(out)):
                    diag["span_misses_bounds"] += 1
                    continue
                slice_ = out[start:end]
                if slice_ in members_set:
                    diag["span_hits"] += 1
                elif _source_span_matches_cluster_literal(slice_, members_set):
                    diag["span_hits"] += 1
                    diag["span_hits_literal_equiv"] += 1
                else:
                    diag["span_misses_slice_mismatch"] += 1
                    continue
                out = out[:start] + emission.symbol + out[end:]
            return preamble + out
        diag["global_replace_fallback_clusters"] += 1
        out = text
        for m in sorted(set(emission.member_texts), key=len, reverse=True):
            if m:
                out = out.replace(m, emission.symbol)
        return preamble + out


class StubReferenceCodec(ReferenceCodecV1):
    """Back-compat name."""

    pass
