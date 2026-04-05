"""
Rewrite Stage3 AB runtime: route → B → re-route → parse-safe A input → A → re-route / destructive, with telemetry.
"""

from __future__ import annotations

import ast as ast_module
from dataclasses import replace
from typing import Any

from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1
from rewrite_stage3ab.channels.b_channel.implementation_v1 import BChannelV1
from rewrite_stage3ab.contracts.data_models import (
    AChannelResult,
    BChannelResult,
    SourceUnit,
    Stage3ABRunResult,
    Stage3ABRunSummary,
    TelemetryEvent,
)
from rewrite_stage3ab.contracts.enums import RouteAction, StageName, TelemetryEventKind
from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len
from rewrite_stage3ab.orchestrator.stage2_router import (
    RoutePolicy,
    Stage2RouterEngine,
    apply_char_span_removals,
    assets_for_b,
    collect_spans_for_action,
    extract_python_free_text_assets,
    mask_char_spans_preserve_layout,
)
from rewrite_stage3ab.telemetry import events as tev
from rewrite_stage3ab.telemetry.summaries import summarize_run
from rewrite_stage3ab.validation.example_snapshot import snapshot_from_text


class Stage3ScaffoldRuntime:
    """
    Production rewrite path (name kept for import stability).

    Order: **B** on routed NL assets → **re-route** → **parse-safe view for A** (mask spans if needed) → **A** →
    **re-route + destructive clean** → final text.
    """

    def __init__(self, default_route_policy: RoutePolicy | None = None) -> None:
        self._default_route_policy = default_route_policy or RoutePolicy()
        self._router = Stage2RouterEngine(self._default_route_policy)
        self._b = BChannelV1()

    def run_unit(self, unit: SourceUnit) -> Stage3ABRunResult:
        tok = unit.tokenizer_key
        sid = unit.source_id
        text0 = unit.raw_text
        events: list[TelemetryEvent] = []
        pol = unit.metadata.get("route_policy")
        router = Stage2RouterEngine(pol) if isinstance(pol, RoutePolicy) else self._router

        assets0 = extract_python_free_text_assets(sid, text0)
        rd0 = router.route(sid, assets0)
        route_sum0 = dict(rd0.extras.get("route_summary", {}))
        for d in rd0.decisions:
            a = d.asset
            ak = a.metadata.get("asset_kind", "")
            if ak == "docstring":
                events.append(
                    tev.event_docstring_detected(
                        sid,
                        StageName.STAGE2_CLEAN.value,
                        measure_true_token_len(a.text, tok),
                        {"asset_id": a.asset_id, "route": d.action.value, "reason": d.reason},
                    )
                )
            elif ak == "comment":
                events.append(
                    tev.event_comment_detected(
                        sid,
                        StageName.STAGE2_CLEAN.value,
                        measure_true_token_len(a.text, tok),
                        {"asset_id": a.asset_id, "route": d.action.value, "reason": d.reason},
                    )
                )
            events.append(
                tev.event_route_decision_made(
                    sid,
                    StageName.STAGE2_CLEAN.value,
                    {
                        "asset_id": a.asset_id,
                        "route_action": d.action.value,
                        "asset_kind": ak,
                        "reason": d.reason,
                    },
                )
            )

        span_pre_b = collect_spans_for_action(
            rd0, {RouteAction.DELETE_NOW, RouteAction.CLEAN_AFTER_B}
        )
        text_for_b = mask_char_spans_preserve_layout(text0, span_pre_b)
        b_routed = []
        for a in assets_for_b(rd0):
            cs, ce = a.char_start, a.char_end
            if cs is not None and ce is not None:
                b_routed.append(replace(a, text=text_for_b[cs:ce]))
            else:
                b_routed.append(a)
        ctx_b: dict = {
            "source_id": sid,
            "tokenizer_key": tok,
            "b_routed_assets": b_routed,
        }
        for x in ctx_b["b_routed_assets"]:
            events.append(
                tev.event_b_asset_collected(
                    sid,
                    StageName.STAGE3_PRE_AB.value,
                    measure_true_token_len(x.text, tok),
                    {"asset_id": x.asset_id, "kind": x.metadata.get("asset_kind")},
                )
            )

        text_after_b = self._b.apply_cluster_rewrites(text_for_b, ctx_b)
        b_rewrite_diag = dict(ctx_b.get("b_rewrite_diagnostics") or {})

        for cl in ctx_b.get("b_cluster_evaluations", []):
            clus = cl.get("cluster", {}) or {}
            cid = str(clus.get("cluster_id", ""))
            texts = list(clus.get("texts") or [])
            n_mem = len(texts)
            events.append(tev.event_b_cluster_formed(sid, StageName.STAGE3_PRE_AB.value, {"cluster_id": cid}))
            if cl.get("ok"):
                em = cl.get("emission")
                net = getattr(em, "net_true", 0)
                events.append(
                    tev.event_b_cluster_accepted(
                        sid,
                        StageName.STAGE3_PRE_AB.value,
                        int(net),
                        {
                            "cluster_id": cid,
                            "fallback_exact": clus.get("fallback_exact", False),
                            "n_members": n_mem,
                            "cluster_path": str(clus.get("cluster_path", "")),
                        },
                    )
                )
                events.append(
                    tev.event_b_reference_emitted(
                        sid,
                        StageName.STAGE3_PRE_AB.value,
                        int(getattr(em, "intro_tokens_true", 0)),
                        int(net),
                        {
                            "symbol": getattr(em, "symbol", ""),
                            "cluster_id": cid,
                            "n_members": n_mem,
                            "raw_total_true": int(getattr(em, "raw_total_true", 0)),
                            "ref_total_true": int(getattr(em, "ref_total_true", 0)),
                            "intro_tokens_true": int(getattr(em, "intro_tokens_true", 0)),
                            "net_true": int(net),
                            "cluster_path": str(clus.get("cluster_path", "")),
                        },
                    )
                )
            else:
                reason = str(cl.get("reason", ""))
                rej_pl: dict[str, Any] = {
                    "cluster_id": cid,
                    "n_members": n_mem,
                    "cluster_path": str(clus.get("cluster_path", "")),
                    "fallback_exact": bool(clus.get("fallback_exact")),
                    "fallback_near_dup": bool(clus.get("fallback_near_dup")),
                    "total_text_chars": sum(len(t) for t in texts),
                }
                if reason == "rejected_for_no_net_gain" and cl.get("emission") is not None:
                    em0 = cl["emission"]
                    rej_pl["raw_total_true"] = int(getattr(em0, "raw_total_true", 0))
                    rej_pl["intro_tokens_true"] = int(getattr(em0, "intro_tokens_true", 0))
                    rej_pl["ref_total_true"] = int(getattr(em0, "ref_total_true", 0))
                    rej_pl["cluster_net_true"] = int(getattr(em0, "net_true", 0))
                events.append(
                    tev.event_b_cluster_rejected(
                        sid,
                        StageName.STAGE3_PRE_AB.value,
                        reason,
                        rej_pl,
                    )
                )

        assets1 = extract_python_free_text_assets(sid, text_after_b)
        rd1 = router.route(sid, assets1)
        route_sum1 = dict(rd1.extras.get("route_summary", {}))
        del_spans = collect_spans_for_action(rd1, {RouteAction.DELETE_NOW})
        clean_spans = collect_spans_for_action(rd1, {RouteAction.CLEAN_AFTER_B})
        mask_spans = list(del_spans) + list(clean_spans)

        text_for_a = text_after_b
        a_input_origin = "after_b_direct"
        a_parse_safe_fallback_used = False
        a_parse_safe_fallback_masked_chars = 0
        a_parse_safe_parse_ok = False
        try:
            ast_module.parse(text_for_a)
            a_parse_safe_parse_ok = True
        except SyntaxError:
            before_mask = text_for_a
            text_for_a = mask_char_spans_preserve_layout(text_after_b, mask_spans)
            a_parse_safe_fallback_used = True
            a_parse_safe_fallback_masked_chars = sum(1 for i, (a, b) in enumerate(zip(before_mask, text_for_a)) if a != b)
            a_input_origin = "after_b_masked_preserve_layout"
            try:
                ast_module.parse(text_for_a)
                a_parse_safe_parse_ok = True
            except SyntaxError:
                a_input_origin = "after_b_parse_failed_mask_failed"

        b_syms: set[str] = {str(getattr(em, "symbol", "")) for em in ctx_b.get("b_emissions", []) if getattr(em, "symbol", "")}

        a_impl = AChannelV1(tok, min_occ_aux=1)
        ctx_a: dict = {
            "source_id": sid,
            "tokenizer_key": tok,
            "reserved_aliases": set(),
            "b_generated_symbols": b_syms,
        }
        alias_pool_agg = {
            "alias_pool_total": 0,
            "alias_pool_single_token_count": 0,
            "alias_pool_low_cost_count": 0,
            "alias_pool_fallback_tier_count": 0,
            "alias_selections_by_tier": {},  # type: ignore[var-annotated]
        }
        cands = a_impl.collect_candidates(text_for_a, ctx_a)
        for c in cands:
            lit = str(c.get("literal", ""))
            events.append(
                tev.event_a_candidate_collected(
                    sid,
                    StageName.STAGE3_PRE_AB.value,
                    measure_true_token_len(lit, tok) * int(c.get("occ", 1)),
                    dict(c),
                )
            )
        ranked = a_impl.rank_candidates(cands, ctx_a)
        assignments: list[dict] = []
        intro_a = 0
        gross_a = 0
        net_a = 0
        for c in ranked:
            ev = a_impl.evaluate_candidate(c, ctx_a)
            if ev.get("ok"):
                events.append(
                    tev.event_a_candidate_accepted(
                        sid,
                        StageName.STAGE3_AFTER_A.value,
                        int(ev.get("net_true", 0)),
                        {"literal": c.get("literal"), "alias": ev.get("alias")},
                    )
                )
                apm = ev.get("alias_pool_meta") or {}
                for k in ("alias_pool_total", "alias_pool_single_token_count", "alias_pool_low_cost_count"):
                    if k in apm:
                        alias_pool_agg[k] = max(alias_pool_agg[k], int(apm[k]))
                fb = int(apm.get("alias_pool_fallback_tier_count", 0))
                alias_pool_agg["alias_pool_fallback_tier_count"] = max(alias_pool_agg["alias_pool_fallback_tier_count"], fb)
                tier = ev.get("alias_selection_tier")
                if tier is not None:
                    alias_pool_agg["alias_selections_by_tier"][str(tier)] = (
                        alias_pool_agg["alias_selections_by_tier"].get(str(tier), 0) + 1
                    )
                assignments.append(
                    {
                        "field": c.get("field"),
                        "literal": c.get("literal"),
                        "alias": ev.get("alias"),
                        "alias_selected_token_len_true": ev.get("token_len_alias"),
                        "alias_selection_tier": ev.get("alias_selection_tier"),
                        "alias_is_strict_single_token": ev.get("alias_is_strict_single_token"),
                    }
                )
                intro_a += int(ev.get("intro_tokens_true", 0))
                gross_a += int(ev.get("gross_gain_true", 0))
                net_a += int(ev.get("net_true", 0))
                ctx_a["reserved_aliases"].add(str(ev.get("alias", "")))
            else:
                events.append(
                    tev.event_a_candidate_rejected(
                        sid,
                        StageName.STAGE3_AFTER_A.value,
                        measure_true_token_len(str(c.get("literal", "")), tok),
                        measure_true_token_len(str(c.get("literal", "")), tok),
                        str(ev.get("reason", "")),
                        {"literal": c.get("literal"), "detail": ev},
                    )
                )
        ctx_a["a_assignments"] = assignments
        text_after_a = a_impl.apply_assignments(text_for_a, ctx_a)

        assets2 = extract_python_free_text_assets(sid, text_after_a)
        rd2 = router.route(sid, assets2)
        route_sum2 = dict(rd2.extras.get("route_summary", {}))
        del_spans2 = collect_spans_for_action(rd2, {RouteAction.DELETE_NOW})
        clean_spans2 = collect_spans_for_action(rd2, {RouteAction.CLEAN_AFTER_B})
        text_final = apply_char_span_removals(text_after_a, del_spans2)
        text_final = apply_char_span_removals(text_final, clean_spans2)
        for row in assignments:
            events.append(
                tev.event_a_alias_applied(
                    sid,
                    StageName.STAGE3_AFTER_A.value,
                    measure_true_token_len(str(row.get("literal", "")), tok)
                    - measure_true_token_len(str(row.get("alias", "")), tok),
                    row,
                )
            )

        input_snap = snapshot_from_text(StageName.STAGE3_PRE_AB.value, text0, tok, notes="rewrite input")
        after_b_snap = snapshot_from_text(StageName.STAGE3_AFTER_B.value, text_after_b, tok, notes="after B")
        after_clean_snap = snapshot_from_text("after_stage2_route_clean", text_final, tok, notes="after destructive clean (post-A route)")
        after_a_snap = snapshot_from_text(StageName.STAGE3_AFTER_A.value, text_after_a, tok, notes="after A")
        final_snap = snapshot_from_text(StageName.STAGE3_FINAL.value, text_final, tok, notes="final")

        em_list = list(ctx_b.get("b_emissions", []))
        b_intro = sum(int(getattr(em, "intro_tokens_true", 0)) for em in em_list)
        b_net = sum(int(getattr(em, "net_true", 0)) for em in em_list)
        b_body_saved = 0
        for em in em_list:
            r = int(getattr(em, "raw_total_true", 0))
            ref = int(getattr(em, "ref_total_true", 0))
            intro_e = int(getattr(em, "intro_tokens_true", 0))
            b_body_saved += max(0, r - max(0, ref - intro_e))

        a_res = AChannelResult(
            intro_tokens_true=intro_a,
            saved_tokens_true=max(0, gross_a - intro_a),
            net_saved_true=net_a,
            alias_assignments=assignments,
            rejected_candidates_by_reason=_count_a_reasons(events),
            selected_candidates=[dict(x) for x in assignments],
        )
        b_res = BChannelResult(
            visible_candidates=int(ctx_b.get("b_collect_dedupe", 0)),
            clusters_formed=len(ctx_b.get("b_cluster_evaluations", [])),
            clusters_selected=len(em_list),
            rejected_clusters_by_reason=_count_b_reasons(ctx_b.get("b_cluster_evaluations", [])),
            intro_tokens_true=b_intro,
            saved_tokens_true=max(0, b_body_saved),
            net_saved_true=b_net,
            references_or_templates=[
                {
                    "symbol": getattr(em, "symbol", ""),
                    "representative": getattr(em, "representative", ""),
                    "net_true": getattr(em, "net_true", 0),
                    "intro_tokens_true": getattr(em, "intro_tokens_true", 0),
                    "raw_total_true": getattr(em, "raw_total_true", 0),
                    "ref_total_true": getattr(em, "ref_total_true", 0),
                    "representative_token_len_true": (getattr(em, "representative_meta", {}) or {}).get(
                        "representative_token_len_true"
                    ),
                    "cluster_path": (getattr(em, "meta", {}) or {}).get("cluster_path", ""),
                    "fallback_reason": (getattr(em, "meta", {}) or {}).get("fallback_reason", ""),
                }
                for em in ctx_b.get("b_emissions", [])
            ],
        )

        events.append(
            tev.event_final_stage_delta(
                sid,
                StageName.STAGE3_FINAL.value,
                input_snap.token_count_true,
                final_snap.token_count_true,
                {
                    "a_net_saved_true": net_a,
                    "b_net_saved_true": b_net,
                    "clustering_note": ctx_b.get("b_clustering_backend_note"),
                    "hdbscan_available": ctx_b.get("b_hdbscan_runtime_available"),
                },
            )
        )
        events.append(
            tev.boundary_event(
                StageName.STAGE3_FINAL.value,
                input_snap.token_count_true,
                final_snap.token_count_true,
                {"source_id": sid, "rewrite": True},
                source_id=sid,
            )
        )

        run_extras: dict[str, Any] = {
            "text_for_a_parse_safe": text_for_a,
            "a_input_origin": a_input_origin,
            "a_parse_safe_token_true": measure_true_token_len(text_for_a, tok),
            "a_parse_safe_fallback_used": a_parse_safe_fallback_used,
            "a_parse_safe_fallback_masked_chars": a_parse_safe_fallback_masked_chars,
            "a_parse_safe_parse_ok": a_parse_safe_parse_ok,
            "text_after_destructive_clean_for_a": text_final,
            "b_rewrite_diagnostics": b_rewrite_diag,
            "after_b_token_true": after_b_snap.token_count_true,
            "after_clean_token_true": after_clean_snap.token_count_true,
            "after_a_token_true": after_a_snap.token_count_true,
            "final_token_true": final_snap.token_count_true,
            "route_summary_initial": route_sum0,
            "route_summary_post_b": route_sum1,
            "route_summary_post_a": route_sum2,
            "alias_pool_telemetry": alias_pool_agg,
            "b_clustering_backend_note": ctx_b.get("b_clustering_backend_note"),
            "b_hdbscan_runtime_available": ctx_b.get("b_hdbscan_runtime_available"),
            "b_hdbscan_actually_used": ctx_b.get("b_hdbscan_actually_used"),
            "b_hdbscan_noise_points": int(ctx_b.get("b_hdbscan_noise_points", 0)),
            "b_hdbscan_noise_singleton_residual": int(ctx_b.get("b_hdbscan_noise_singleton_residual", 0)),
            "total_a_candidates_collected": len(cands),
            "total_a_selected": len(assignments),
            "total_b_clusters_evaluated": len(ctx_b.get("b_cluster_evaluations", [])),
            "total_b_clusters_selected": len(em_list),
        }

        result = Stage3ABRunResult(
            source_id=sid,
            input_snapshot=input_snap,
            after_a_snapshot=after_a_snap,
            after_b_snapshot=after_b_snap,
            final_snapshot=final_snap,
            a_result=a_res,
            b_result=b_res,
            telemetry_events=events,
            summary=None,
            run_extras=run_extras,
            after_route_clean_snapshot=after_clean_snap,
        )
        result.summary = summarize_run(result)
        if result.summary is not None:
            result.summary.extras.update(
                {
                    "after_clean_token_true": after_clean_snap.token_count_true,
                    "route_summary_initial": route_sum0,
                    "route_summary_post_b": route_sum1,
                    "route_summary_post_a": route_sum2,
                    "alias_pool_telemetry": alias_pool_agg,
                }
            )
        return result


def _count_a_reasons(events: list[TelemetryEvent]) -> dict[str, int]:
    out: dict[str, int] = {}
    want = TelemetryEventKind.A_CANDIDATE_REJECTED.value
    for e in events:
        if e.event_type != want:
            continue
        out[e.action] = out.get(e.action, 0) + 1
    return out


def _count_b_reasons(rows: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for cl in rows:
        if cl.get("ok"):
            continue
        r = str(cl.get("reason", ""))
        out[r] = out.get(r, 0) + 1
    return out


# Back-compat alias
Stage3ABRewriteRuntime = Stage3ScaffoldRuntime
