"""
Reference-style compression for small / similar clusters (SemDeDup-flavored).

Uses **true-token** intro / raw / net accounting from ``metrics``.
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
    """Pick lowest true-token surface as representative; emit assignment + replace literals."""

    def select_representative(self, members: list[str], ctx: dict[str, Any]) -> str:
        tok = ctx.get("tokenizer_key", "gpt4")
        best = members[0] if members else ""
        best_n = measure_true_token_len(best, tok)
        for m in members[1:]:
            n = measure_true_token_len(m, tok)
            if n < best_n:
                best, best_n = m, n
        return best

    def emit(self, representative: str, symbol: str, ctx: dict[str, Any]) -> ReferenceEmission:
        tok = ctx.get("tokenizer_key", "gpt4")
        members = list(ctx.get("cluster_members", []))
        if not members:
            members = [representative]
        rhs = _python_value_repr_from_literal_segment(representative)
        preamble = f"{symbol} = {rhs}\n"
        intro = measure_true_token_len(preamble, tok)
        raw_total = sum(measure_true_token_len(m, tok) for m in members)
        per_sym = measure_true_token_len(symbol, tok)
        ref_total = intro + per_sym * len(members)
        net = raw_total - ref_total
        return ReferenceEmission(
            symbol=symbol,
            representative=representative,
            member_texts=list(members),
            member_spans=list(ctx.get("member_spans", [])),
            intro_tokens_true=intro,
            raw_total_true=raw_total,
            ref_total_true=ref_total,
            net_true=net,
            meta={"preamble": preamble},
        )

    def rewrite_text(self, text: str, emission: ReferenceEmission, ctx: dict[str, Any]) -> str:
        del ctx
        preamble = emission.meta.get("preamble", "")
        out = text
        for m in sorted(set(emission.member_texts), key=len, reverse=True):
            if m:
                out = out.replace(m, emission.symbol)
        return f"{preamble}{out}"


class StubReferenceCodec(ReferenceCodecV1):
    """Back-compat name."""

    pass
