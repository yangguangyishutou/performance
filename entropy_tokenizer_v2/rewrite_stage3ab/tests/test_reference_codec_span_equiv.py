"""Span rewrite accepts equivalent Python literals (quote style)."""

from __future__ import annotations

from rewrite_stage3ab.channels.b_channel.reference_codec import ReferenceCodecV1


def test_rewrite_span_quote_style_mismatch_still_hits() -> None:
    codec = ReferenceCodecV1()
    text = "x = 'hello world string literal'\n"
    lit_sq = "'hello world string literal'"
    assert text.index(lit_sq) == 4
    end = 4 + len(lit_sq)
    rep = '"hello world string literal"'
    sym = "_b0"
    ctx0: dict = {
        "tokenizer_key": "gpt4",
        "cluster_members": [rep, rep],
        "member_spans": [(4, end)],
        "cluster_path": "test",
        "fallback_reason": "",
    }
    em = codec.emit(rep, sym, ctx0)
    ctx: dict = {}
    out = codec.rewrite_text(text, em, ctx)
    diag = ctx.get("b_rewrite_diagnostics") or {}
    assert diag.get("span_hits", 0) == 1
    assert diag.get("span_hits_literal_equiv", 0) == 1
    assert sym in out


def test_route_policy_recovery_v2_factory() -> None:
    from rewrite_stage3ab.orchestrator.stage2_router import RoutePolicy

    p = RoutePolicy.rewrite_recovery_v2()
    assert p.b_string_min_chars == 10
    assert p.long_literal_reference_threshold == 10
