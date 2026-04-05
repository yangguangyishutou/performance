"""Scaffold orchestration: routing, runtime, thin pipeline entry."""

from typing import Any

__all__ = ["Stage3ScaffoldRuntime", "run_scaffold_on_units"]


def __getattr__(name: str) -> Any:
    if name == "run_scaffold_on_units":
        from rewrite_stage3ab.orchestrator.pipeline import run_scaffold_on_units

        return run_scaffold_on_units
    if name == "Stage3ScaffoldRuntime":
        from rewrite_stage3ab.orchestrator.stage3_runtime import Stage3ScaffoldRuntime

        return Stage3ScaffoldRuntime
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
