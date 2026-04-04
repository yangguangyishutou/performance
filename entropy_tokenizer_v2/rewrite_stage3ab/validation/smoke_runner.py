#!/usr/bin/env python3
"""
Minimal scaffold smoke: one ``SourceUnit`` → ``Stage3ABRunResult``.

Run from ``entropy_tokenizer_v2`` root::

    python -m rewrite_stage3ab.validation.smoke_runner
"""

from __future__ import annotations

from rewrite_stage3ab.contracts.data_models import SourceUnit
from rewrite_stage3ab.orchestrator.stage3_runtime import Stage3ScaffoldRuntime
from rewrite_stage3ab.telemetry.ledger import ExampleLedger


SNIPPET = '''def hello():
    """doc"""
    x = "literal"
    return x
'''


def run_smoke(tokenizer_key: str = "gpt4") -> tuple[object, ExampleLedger]:
    unit = SourceUnit(
        source_id="smoke:0",
        raw_text=SNIPPET,
        tokenizer_key=tokenizer_key,
        metadata={"runner": "rewrite_stage3ab.validation.smoke_runner"},
    )
    rt = Stage3ScaffoldRuntime()
    result = rt.run_unit(unit)
    ledger = ExampleLedger()
    ledger.append_reject(unit.source_id, "dummy_reject_for_schema", payload={"phase": "smoke"})
    ledger.append_a_rewrite(
        unit.source_id,
        SNIPPET[:20],
        SNIPPET[:20],
        payload={"note": "no-op stub"},
    )
    return result, ledger


def main() -> None:
    result, ledger = run_smoke()
    assert result.summary is not None
    print("ok", result.source_id, "events=", len(result.telemetry_events), "ledger=", len(ledger))


if __name__ == "__main__":
    main()
