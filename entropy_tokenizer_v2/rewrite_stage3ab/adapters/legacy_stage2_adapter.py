"""
Read-only bridge for Stage2 funnel metrics (hybrid_ab / cleaning stats).

TODO: Map production per-file meta dicts into ``FreeTextAsset`` / ``RouteDecision``
      when orchestrator replaces env-driven routing.
"""

from __future__ import annotations

from typing import Any


def read_stage2_meta_stub(meta: dict[str, Any] | None) -> dict[str, Any]:
    """
    Pass-through placeholder: return a shallow copy of known keys for experiments.

    Real implementation will normalize keys like ``stage2_retained_for_b_probe_*``.
    """
    if not meta:
        return {}
    return {k: meta[k] for k in meta if k.startswith("stage2_")}
