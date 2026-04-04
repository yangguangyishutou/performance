"""
Rewrite Stage3 AB runtime: route → B → re-route / destructive → A, with telemetry.
"""

from __future__ import annotations

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
    Stage2RouterEngine,
    apply_char_span_removals,
    assets_for_b,
    collect_spans_for_action,
    extract_python_free_text_assets,
)
from rewrite_stage3ab.telemetry import events as tev
from rewrite_stage3ab.telemetry.summaries import summarize_run
from rewrite_stage3ab.validation.example_snapshot import snapshot_from_text


class Stage3ScaffoldRuntime:
    """
    Production rewrite path (name kept for import stability).

    Order: **B** on routed NL assets → **re-sniff + destructive + clean** → **A** economics.
    """

    def __init__(self) -> None:
        self._router = Stage2RouterEngine()
        self._b = BChannelV1()

    def run_unit(self, unit: SourceUnit) -> Stage3ABRunResult:
        tok = unit.tokenizer_key
        sid = unit.source_id
        text0 = unit.raw_text
        events: list[TelemetryEvent] = []

        assets0 = extract_python_free_text_assets(sid, text0)
        rd0 = self._router.route(sid, assets0)
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

        ctx_b: dict = {
            "source_id": sid,
            "tokenizer_key": tok,
            "b_routed_assets": assets_for_b(rd0),
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

        text_after_b = self._b.apply_cluster_rewrites(text0, ctx_b)

        for cl in ctx_b.get("b_cluster_evaluations", []):
            clus = cl.get("cluster", {})
            cid = str(clus.get("cluster_id", ""))
            events.append(tev.event_b_cluster_formed(sid, StageName.STAGE3_PRE_AB.value, {"cluster_id": cid}))
            if cl.get("ok"):
                em = cl.get("emission")
                net = getattr(em, "net_true", 0)
                events.append(
                    tev.event_b_cluster_accepted(
                        sid,
                        StageName.STAGE3_PRE_AB.value,
                        int(net),
                        {"cluster_id": cid, "fallback_exact": clus.get("fallback_exact", False)},
                    )
                )
                events.append(
                    tev.event_b_reference_emitted(
                        sid,
                        StageName.STAGE3_PRE_AB.value,
                        int(getattr(em, "intro_tokens_true", 0)),
                        int(net),
                        {"symbol": getattr(em, "symbol", ""), "cluster_id": cid},
                    )
                )
            else:
                events.append(
                    tev.event_b_cluster_rejected(
                        sid,
                        StageName.STAGE3_PRE_AB.value,
                        str(cl.get("reason", "")),
                        {"cluster_id": cid},
                    )
                )

        assets1 = extract_python_free_text_assets(sid, text_after_b)
        rd1 = self._router.route(sid, assets1)
        del_spans = collect_spans_for_action(rd1, {RouteAction.DELETE_NOW})
        clean_spans = collect_spans_for_action(rd1, {RouteAction.CLEAN_AFTER_B})
        text_s2 = apply_char_span_removals(text_after_b, del_spans)
        text_s2 = apply_char_span_removals(text_s2, clean_spans)

        a_impl = AChannelV1(tok, min_occ_aux=1)
        ctx_a: dict = {"source_id": sid, "tokenizer_key": tok, "reserved_aliases": set()}
        cands = a_impl.collect_candidates(text_s2, ctx_a)
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
                assignments.append(
                    {
                        "field": c.get("field"),
                        "literal": c.get("literal"),
                        "alias": ev.get("alias"),
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
        text_after_a = a_impl.apply_assignments(text_s2, ctx_a)
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
        after_a_snap = snapshot_from_text(StageName.STAGE3_AFTER_A.value, text_after_a, tok, notes="after A")
        final_snap = snapshot_from_text(StageName.STAGE3_FINAL.value, text_after_a, tok, notes="final")

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
        )
        result.summary = summarize_run(result)
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
