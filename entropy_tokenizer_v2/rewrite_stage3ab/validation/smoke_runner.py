#!/usr/bin/env python3
"""
Rewrite Stage3 AB smoke: three hand-written units → results + example ledger.

Run from ``entropy_tokenizer_v2`` root::

    python -m rewrite_stage3ab.validation.smoke_runner
"""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.contracts.data_models import SourceUnit
from rewrite_stage3ab.orchestrator.stage3_runtime import Stage3ScaffoldRuntime
from rewrite_stage3ab.telemetry.ledger import ExampleLedger, JsonlTelemetryLedger
from rewrite_stage3ab.validation.example_snapshot import write_example_markdown

# A: long identifier, two uses → tokenizer-aware alias should win on net_true
CASE_A = """def f():
    very_long_identifier_for_tokenizer_alias_demo_case = 1
    return very_long_identifier_for_tokenizer_alias_demo_case + very_long_identifier_for_tokenizer_alias_demo_case
"""

# B: identical long literals ×3 → reference / cluster path
CASE_B = '''
msg_a = "this_is_a_shared_literal_token_sink_abc"
msg_b = "this_is_a_shared_literal_token_sink_abc"
msg_c = "this_is_a_shared_literal_token_sink_abc"
'''

# Routing: ultra-short comment → DELETE_NOW after B pass; docstring retained for B
CASE_ROUTE = '''# x
def g():
    """routing_case_docstring_asset"""
    return 1
'''


def run_smoke(tokenizer_key: str = "gpt4") -> tuple[list[object], ExampleLedger]:
    rt = Stage3ScaffoldRuntime()
    units = [
        SourceUnit("smoke:a_success", CASE_A, tokenizer_key, metadata={"case": "A"}),
        SourceUnit("smoke:b_cluster", CASE_B, tokenizer_key, metadata={"case": "B"}),
        SourceUnit("smoke:route", CASE_ROUTE, tokenizer_key, metadata={"case": "route"}),
    ]
    results = [rt.run_unit(u) for u in units]
    ledger = ExampleLedger()

    ra, rb, rr = results
    # A success / reject samples
    if ra.a_result.alias_assignments:
        a0 = ra.a_result.alias_assignments[0]
        ledger.append_a_rewrite(
            ra.source_id,
            CASE_A.strip()[:120],
            ra.final_snapshot.text[:200],
            payload={"assignments": ra.a_result.alias_assignments, "net": ra.a_result.net_saved_true},
        )
    else:
        ledger.append_reject(ra.source_id, "a_no_assignment_in_smoke", payload={"a": ra.a_result.selected_candidates})

    # B success / reject
    if rb.b_result.references_or_templates:
        ledger.append_b_cluster(
            rb.source_id,
            CASE_B.strip()[:160],
            rb.after_b_snapshot.text[:220],
            payload={"refs": rb.b_result.references_or_templates, "net": rb.b_result.net_saved_true},
        )
    else:
        ledger.append_reject(rb.source_id, "b_no_reference_in_smoke", payload={"b_eval": rb.summary.extras if rb.summary else {}})

    ledger.append_routing(
        rr.source_id,
        CASE_ROUTE,
        rr.final_snapshot.text,
        reason="short_comment_delete_plus_docstring_retained",
        payload={"events": len(rr.telemetry_events)},
    )

    return results, ledger


def main() -> None:
    results, ledger = run_smoke()
    for r in results:
        assert r.summary is not None
    root = Path(__file__).resolve().parents[2] / "results_rewrite_full"
    root.mkdir(parents=True, exist_ok=True)
    jlog = JsonlTelemetryLedger(root / "smoke_ledger.jsonl")
    for r in results:
        jlog.extend(r.telemetry_events)
    write_example_markdown(ledger.entries(), root / "smoke_examples.md")
    print("ok", "units=", len(results), "ledger=", len(ledger), "events=", sum(len(r.telemetry_events) for r in results))


if __name__ == "__main__":
    main()
