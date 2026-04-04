"""Smoke runner and orchestrator imports."""

from __future__ import annotations

from rewrite_stage3ab.orchestrator.pipeline import run_scaffold_on_units
from rewrite_stage3ab.validation.smoke_runner import run_smoke


def test_run_smoke_gpt4():
    result, ledger = run_smoke("gpt4")
    assert result.summary is not None
    assert result.input_snapshot.token_count_true >= 0
    assert len(result.telemetry_events) >= 1
    assert len(ledger) >= 2


def test_pipeline_two_units():
    from rewrite_stage3ab.contracts.data_models import SourceUnit

    units = [
        SourceUnit("u0", "a = 1\n", "gpt4"),
        SourceUnit("u1", "b = 2\n", "gpt4"),
    ]
    out = run_scaffold_on_units(units)
    assert len(out) == 2
    assert all(r.final_snapshot.text == r.input_snapshot.text for r in out)
