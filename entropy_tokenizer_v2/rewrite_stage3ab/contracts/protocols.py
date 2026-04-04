"""
Cross-cutting Protocol definitions (typing-only; no runtime deps on heavy modules).

Channel-specific Protocols live under ``channels/*/protocol.py``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from rewrite_stage3ab.contracts.data_models import SourceUnit, Stage3ABRunResult, StageSnapshot


@runtime_checkable
class TrueTokenMeasurer(Protocol):
    """Pluggable primary token counter (defaults to legacy encode length)."""

    def measure(self, text: str, tokenizer_key: str) -> int:
        """Return raw tokenizer token count for *text*."""
        ...


@runtime_checkable
class RewriteOrchestrator(Protocol):
    """Runs Stage3 AB scaffold over one or more units."""

    def run_unit(self, unit: SourceUnit) -> Stage3ABRunResult:
        ...


@runtime_checkable
class SnapshotBuilder(Protocol):
    """Builds ``StageSnapshot`` with both true and optional augmented counts."""

    def build(self, stage_name: str, text: str, tokenizer_key: str, notes: str = "") -> StageSnapshot:
        ...
