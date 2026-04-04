"""
Thin multi-unit entrypoint over ``Stage3ScaffoldRuntime``.

TODO: Insert Stage1/Stage2 adapters and ``Stage2Router`` between raw units and Stage3.
"""

from __future__ import annotations

from rewrite_stage3ab.contracts.data_models import SourceUnit, Stage3ABRunResult
from rewrite_stage3ab.orchestrator.stage3_runtime import Stage3ScaffoldRuntime


def run_scaffold_on_units(units: list[SourceUnit]) -> list[Stage3ABRunResult]:
    rt = Stage3ScaffoldRuntime()
    return [rt.run_unit(u) for u in units]
