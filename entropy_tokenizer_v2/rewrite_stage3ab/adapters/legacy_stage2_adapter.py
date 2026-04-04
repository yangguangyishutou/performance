"""
Read-only bridge for Stage2 funnel metrics (hybrid_ab / cleaning stats).

Normalizes arbitrary per-file meta dicts into rewrite routing hints.
"""

from __future__ import annotations

from typing import Any

from rewrite_stage3ab.orchestrator.stage2_router import FreeTextAsset, RouteAction, RouteDecision, Stage2AssetDecision


def read_stage2_meta_stub(meta: dict[str, Any] | None) -> dict[str, Any]:
    """
    Pass-through placeholder: return a shallow copy of known keys for experiments.

    Prefer ``normalize_stage2_meta`` for structured routing hints.
    """
    if not meta:
        return {}
    return {k: meta[k] for k in meta if k.startswith("stage2_")}


def normalize_stage2_meta(source_id: str, meta: dict[str, Any] | None) -> RouteDecision | None:
    """
    Map keys like ``stage2_retained_for_b`` into synthetic ``RouteDecision`` rows.

    Returns ``None`` when no recognized keys exist.
    """
    if not meta:
        return None
    hints = read_stage2_meta_stub(meta)
    if not hints:
        return None
    decisions: list[Stage2AssetDecision] = []
    for k, v in hints.items():
        if "retain" in k and "b" in k:
            action = RouteAction.RETAIN_FOR_B
        elif "delete" in k or "drop" in k:
            action = RouteAction.DELETE_NOW
        else:
            action = RouteAction.PASS_THROUGH
        decisions.append(
            Stage2AssetDecision(
                asset=FreeTextAsset(asset_id=f"{source_id}:meta:{k}", text=str(v), source_id=source_id, metadata={"key": k}),
                action=action,
                reason="legacy_stage2_meta",
            )
        )
    return RouteDecision(source_id=source_id, decisions=decisions, extras={"legacy_meta": hints})
