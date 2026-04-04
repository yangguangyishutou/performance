"""
Multi-unit entrypoint over ``Stage3ScaffoldRuntime`` with optional JSONL telemetry.
"""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.contracts.data_models import SourceUnit, Stage3ABRunResult, TelemetryEvent
from rewrite_stage3ab.orchestrator.stage3_runtime import Stage3ScaffoldRuntime
from rewrite_stage3ab.telemetry.ledger import JsonlTelemetryLedger


def run_scaffold_on_units(
    units: list[SourceUnit],
    *,
    jsonl_ledger_path: Path | str | None = None,
) -> list[Stage3ABRunResult]:
    rt = Stage3ScaffoldRuntime()
    out: list[Stage3ABRunResult] = []
    jlog: JsonlTelemetryLedger | None = None
    if jsonl_ledger_path is not None:
        jlog = JsonlTelemetryLedger(jsonl_ledger_path)
    for u in units:
        r = rt.run_unit(u)
        out.append(r)
        if jlog is not None:
            jlog.extend(r.telemetry_events)
    return out


def flatten_events(results: list[Stage3ABRunResult]) -> list[TelemetryEvent]:
    ev: list[TelemetryEvent] = []
    for r in results:
        ev.extend(r.telemetry_events)
    return ev
