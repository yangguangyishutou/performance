"""Result schema completeness for scaffold runs."""

from __future__ import annotations

import dataclasses

from rewrite_stage3ab.contracts.data_models import Stage3ABRunResult, StageSnapshot
from rewrite_stage3ab.validation.smoke_runner import run_smoke


def _field_names(cls) -> set[str]:
    return {f.name for f in dataclasses.fields(cls)}


def test_stage3ab_run_result_schema():
    results, _ = run_smoke("gpt4")
    result = results[0]
    assert _field_names(Stage3ABRunResult) == {
        "source_id",
        "input_snapshot",
        "after_a_snapshot",
        "after_b_snapshot",
        "final_snapshot",
        "a_result",
        "b_result",
        "telemetry_events",
        "summary",
    }
    assert isinstance(result.input_snapshot, StageSnapshot)
    assert result.summary is not None
    assert "total_input_tokens_true" in _field_names(type(result.summary))
