"""
Wires stub A/B channels and builds ``Stage3ABRunResult``.

No production ``encode_stage3_hybrid_ab`` calls here — keeps the scaffold independent
until backends are migrated.
"""

from __future__ import annotations

from rewrite_stage3ab.channels.a_channel.implementation_stub import AChannelStub
from rewrite_stage3ab.channels.b_channel.implementation_stub import BChannelStub
from rewrite_stage3ab.contracts.data_models import (
    AChannelResult,
    BChannelResult,
    SourceUnit,
    Stage3ABRunResult,
    Stage3ABRunSummary,
    StageSnapshot,
    TelemetryEvent,
)
from rewrite_stage3ab.contracts.enums import StageName, TelemetryEventKind
from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len
from rewrite_stage3ab.telemetry.summaries import summarize_run
from rewrite_stage3ab.validation.example_snapshot import snapshot_from_text


class Stage3ScaffoldRuntime:
    """
    Minimal runtime: input text → same text through A stub → same through B stub.

    Populates snapshots and zero-valued channel results; emits one boundary event.
    """

    def __init__(self) -> None:
        self._a = AChannelStub()
        self._b = BChannelStub()

    def run_unit(self, unit: SourceUnit) -> Stage3ABRunResult:
        tok = unit.tokenizer_key
        text_in = unit.raw_text
        input_snap = snapshot_from_text(StageName.STAGE3_PRE_AB.value, text_in, tok, notes="scaffold input")

        ctx = {"source_id": unit.source_id, "tokenizer_key": tok}
        after_a_text = self._a.apply_assignments(text_in, ctx)
        after_a_snap = snapshot_from_text(StageName.STAGE3_AFTER_A.value, after_a_text, tok, notes="after A stub")

        after_b_text = self._b.apply_cluster_rewrites(after_a_text, ctx)
        after_b_snap = snapshot_from_text(StageName.STAGE3_AFTER_B.value, after_b_text, tok, notes="after B stub")
        final_snap = snapshot_from_text(StageName.STAGE3_FINAL.value, after_b_text, tok, notes="final")

        a_res = AChannelResult()
        b_res = BChannelResult()
        # Dummy bookkeeping: true deltas from snapshots
        a_res.saved_tokens_true = max(0, input_snap.token_count_true - after_a_snap.token_count_true)
        b_res.saved_tokens_true = max(0, after_a_snap.token_count_true - after_b_snap.token_count_true)

        events: list[TelemetryEvent] = [
            TelemetryEvent(
                event_type=TelemetryEventKind.STAGE_BOUNDARY.value,
                stage=StageName.STAGE3_FINAL.value,
                input_tokens_true=input_snap.token_count_true,
                output_tokens_true=final_snap.token_count_true,
                delta_true=input_snap.token_count_true - final_snap.token_count_true,
                payload={"source_id": unit.source_id, "scaffold": True},
            )
        ]
        result = Stage3ABRunResult(
            source_id=unit.source_id,
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
