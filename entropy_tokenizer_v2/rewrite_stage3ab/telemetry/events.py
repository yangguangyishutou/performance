"""
Telemetry event constructors (canonical shape: ``TelemetryEvent``).
"""

from __future__ import annotations

from typing import Any

from rewrite_stage3ab.contracts.data_models import TelemetryEvent
from rewrite_stage3ab.contracts.enums import TelemetryEventKind


def _ev(
    kind: TelemetryEventKind,
    stage: str,
    input_true: int,
    output_true: int,
    *,
    source_id: str = "",
    action: str = "",
    payload: dict[str, Any] | None = None,
) -> TelemetryEvent:
    return TelemetryEvent(
        event_type=kind.value,
        stage=stage,
        input_tokens_true=input_true,
        output_tokens_true=output_true,
        delta_true=input_true - output_true,
        payload=payload or {},
        source_id=source_id,
        action=action,
    )


def event_a_candidate_collected(source_id: str, stage: str, tokens: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.A_CANDIDATE_COLLECTED,
        stage,
        tokens,
        tokens,
        source_id=source_id,
        action="collect",
        payload=payload,
    )


def event_a_candidate_rejected(
    source_id: str, stage: str, before_t: int, after_t: int, reason: str, payload: dict[str, Any]
) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.A_CANDIDATE_REJECTED,
        stage,
        before_t,
        after_t,
        source_id=source_id,
        action=reason,
        payload=payload,
    )


def event_a_candidate_accepted(source_id: str, stage: str, net_true: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.A_CANDIDATE_ACCEPTED,
        stage,
        max(net_true, 0),
        0,
        source_id=source_id,
        action="accept",
        payload=payload,
    )


def event_a_alias_applied(source_id: str, stage: str, delta_true: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.A_ALIAS_APPLIED,
        stage,
        abs(delta_true),
        0,
        source_id=source_id,
        action="apply",
        payload=payload,
    )


def event_b_asset_collected(source_id: str, stage: str, tok: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.B_ASSET_COLLECTED,
        stage,
        tok,
        tok,
        source_id=source_id,
        action="collect",
        payload=payload,
    )


def event_b_cluster_formed(source_id: str, stage: str, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.B_CLUSTER_FORMED,
        stage,
        0,
        0,
        source_id=source_id,
        action="form",
        payload=payload,
    )


def event_b_cluster_rejected(source_id: str, stage: str, reason: str, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.B_CLUSTER_REJECTED,
        stage,
        0,
        0,
        source_id=source_id,
        action=reason,
        payload=payload,
    )


def event_b_cluster_accepted(source_id: str, stage: str, net_true: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.B_CLUSTER_ACCEPTED,
        stage,
        max(net_true, 0),
        0,
        source_id=source_id,
        action="accept",
        payload=payload,
    )


def event_b_reference_emitted(source_id: str, stage: str, intro: int, net: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.B_REFERENCE_EMITTED,
        stage,
        intro + max(net, 0),
        intro,
        source_id=source_id,
        action="emit",
        payload=payload,
    )


def event_route_decision_made(source_id: str, stage: str, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.ROUTE_DECISION_MADE,
        stage,
        0,
        0,
        source_id=source_id,
        action=str(payload.get("route_action", "")),
        payload=payload,
    )


def event_docstring_detected(source_id: str, stage: str, tok: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.DOCSTRING_DETECTED,
        stage,
        tok,
        tok,
        source_id=source_id,
        action="docstring",
        payload=payload,
    )


def event_comment_detected(source_id: str, stage: str, tok: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.COMMENT_DETECTED,
        stage,
        tok,
        tok,
        source_id=source_id,
        action="comment",
        payload=payload,
    )


def event_final_stage_delta(source_id: str, stage: str, inp: int, out: int, payload: dict[str, Any]) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.FINAL_STAGE_DELTA,
        stage,
        inp,
        out,
        source_id=source_id,
        action="final",
        payload=payload,
    )


def boundary_event(
    stage: str,
    input_true: int,
    output_true: int,
    payload: dict[str, Any] | None = None,
    *,
    source_id: str = "",
) -> TelemetryEvent:
    return _ev(
        TelemetryEventKind.STAGE_BOUNDARY,
        stage,
        input_true,
        output_true,
        source_id=source_id,
        action="boundary",
        payload=payload or {},
    )
