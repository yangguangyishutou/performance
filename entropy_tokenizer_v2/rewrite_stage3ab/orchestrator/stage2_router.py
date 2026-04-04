"""
Stage2 → Stage3 resource routing (protocol + stub).

Replaces ad-hoc env toggles over time with explicit ``RouteDecision`` objects.

TODO: Wire starvation probe v2 and comment/docstring retention policies here.
TODO: Consume ``legacy_stage2_adapter`` normalized metrics when building decisions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rewrite_stage3ab.contracts.enums import RouteAction


@dataclass
class FreeTextAsset:
    """A span Stage2 might delete, retain for B, or classify as comment/docstring."""

    asset_id: str
    text: str
    source_id: str
    char_start: int | None = None
    char_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage2AssetDecision:
    """Per-asset routing outcome."""

    asset: FreeTextAsset
    action: RouteAction
    reason: str = ""
    priority_score: float = 0.0


@dataclass
class RouteDecision:
    """Batch routing for one source file."""

    source_id: str
    decisions: list[Stage2AssetDecision] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


class StubStage2Router:
    """
    Default no-op router: marks everything PASS_THROUGH.

    Swap for a policy engine that reads Stage2 telemetry and B visibility budgets.
    """

    def route(self, source_id: str, assets: list[FreeTextAsset]) -> RouteDecision:
        return RouteDecision(
            source_id=source_id,
            decisions=[
                Stage2AssetDecision(asset=a, action=RouteAction.PASS_THROUGH, reason="stub")
                for a in assets
            ],
        )
