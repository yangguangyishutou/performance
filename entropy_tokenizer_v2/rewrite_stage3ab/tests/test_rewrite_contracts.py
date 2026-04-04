"""Dataclasses and enums are constructible."""

from __future__ import annotations

from rewrite_stage3ab.contracts.data_models import (
    AChannelResult,
    BChannelResult,
    SourceUnit,
    Stage3ABRunResult,
    Stage3ABRunSummary,
    StageSnapshot,
    TelemetryEvent,
)
from rewrite_stage3ab.contracts.enums import ClusterBackendId, RouteAction, StageName, TelemetryEventKind


def test_source_unit():
    u = SourceUnit(source_id="a", raw_text="x", tokenizer_key="gpt4")
    assert u.metadata == {}


def test_stage_snapshot():
    s = StageSnapshot("s", "hi", 2, token_count_augmented=3)
    assert s.token_count_true == 2
    assert s.token_count_augmented == 3


def test_channel_results():
    assert AChannelResult().net_saved_true == 0
    assert BChannelResult().clusters_selected == 0


def test_telemetry_event():
    e = TelemetryEvent("t", "st", 1, 1, 0, {})
    assert e.delta_true == 0


def test_run_result_minimal():
    z = StageSnapshot("i", "", 0)
    r = Stage3ABRunResult(
        source_id="x",
        input_snapshot=z,
        after_a_snapshot=z,
        after_b_snapshot=z,
        final_snapshot=z,
        a_result=AChannelResult(),
        b_result=BChannelResult(),
        summary=Stage3ABRunSummary(),
    )
    assert r.source_id == "x"


def test_enums():
    assert StageName.RAW.value == "raw"
    assert RouteAction.RETAIN_FOR_B.value == "retain_for_b"
    assert TelemetryEventKind.STAGE_BOUNDARY.value == "stage_boundary"
    assert ClusterBackendId.HDBSCAN_FUTURE.value == "hdbscan_future"
