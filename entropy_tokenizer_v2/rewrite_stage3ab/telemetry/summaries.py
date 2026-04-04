"""Aggregate ``Stage3ABRunResult`` into a compact summary."""

from __future__ import annotations

from rewrite_stage3ab.contracts.data_models import Stage3ABRunResult, Stage3ABRunSummary


def summarize_run(result: Stage3ABRunResult) -> Stage3ABRunSummary:
    inp = result.input_snapshot.token_count_true
    out = result.final_snapshot.token_count_true
    return Stage3ABRunSummary(
        total_input_tokens_true=inp,
        total_output_tokens_true=out,
        a_net_saved_true=result.a_result.net_saved_true,
        b_net_saved_true=result.b_result.net_saved_true,
        n_events=len(result.telemetry_events),
        extras={
            "source_id": result.source_id,
            "a_saved": result.a_result.saved_tokens_true,
            "b_saved": result.b_result.saved_tokens_true,
            "a_intro_true": result.a_result.intro_tokens_true,
            "b_intro_true": result.b_result.intro_tokens_true,
            "delta_input_to_final_true": inp - out,
            "primary_metric": "tokenizer_true",
        },
    )
