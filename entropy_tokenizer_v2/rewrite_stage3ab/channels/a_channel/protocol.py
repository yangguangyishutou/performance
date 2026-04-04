"""
A-channel Protocol: exact aliasing + future token economics.

Implementations must use ``measure_true_token_len`` (or injected ``TrueTokenMeasurer``)
for any gain/cost comparison.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class AChannelProtocol(Protocol):
    def collect_candidates(self, text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        """Gather alias / literal candidates (stub returns empty)."""
        ...

    def rank_candidates(self, candidates: list[dict[str, Any]], ctx: dict[str, Any]) -> list[dict[str, Any]]:
        """Order by expected net true-token gain."""
        ...

    def evaluate_candidate(self, candidate: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        """Score single candidate; include reject reason if any."""
        ...

    def apply_assignments(self, text: str, ctx: dict[str, Any]) -> str:
        """Return rewritten text after applying chosen aliases."""
        ...
