"""
Telemetry event helpers.

Canonical event shape: ``contracts.data_models.TelemetryEvent``.

TODO: Add AST-scoped events (node type, lineno) without breaking JSON serialization.
"""

from __future__ import annotations

from rewrite_stage3ab.contracts.data_models import TelemetryEvent


def boundary_event(
    stage: str,
    input_true: int,
    output_true: int,
    payload: dict | None = None,
) -> TelemetryEvent:
    return TelemetryEvent(
        event_type="stage_boundary",
        stage=stage,
        input_tokens_true=input_true,
        output_tokens_true=output_true,
        delta_true=input_true - output_true,
        payload=payload or {},
    )
