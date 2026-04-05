"""
Route decision breakdown by coarse asset kind (for corpus CSV).
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from rewrite_stage3ab.orchestrator.stage2_router import (
    FreeTextAsset,
    Stage2RouterEngine,
    extract_python_free_text_assets,
)


def _bucket_kind(asset: FreeTextAsset) -> str:
    k = asset.metadata.get("asset_kind", "")
    if k == "docstring":
        return "docstring"
    if k == "comment":
        return "comment"
    if k == "string_literal":
        if asset.metadata.get("multiline"):
            return "multiline_string"
        if len(asset.text) >= 24:
            return "long_literal"
        return "short_literal"
    if k == "ordinary_code_text":
        return "ordinary_code"
    return k or "unknown"


def route_breakdown_for_text(source_id: str, text: str, router: Stage2RouterEngine | None = None) -> dict[str, Any]:
    router = router or Stage2RouterEngine()
    assets = extract_python_free_text_assets(source_id, text)
    rd = router.route(source_id, assets)
    pair_counts: dict[tuple[str, str], int] = defaultdict(int)
    for d in rd.decisions:
        b = _bucket_kind(d.asset)
        pair_counts[(b, d.action.value)] += 1
    flat = {f"{kind}__{act}": c for (kind, act), c in pair_counts.items()}
    summary = rd.extras.get("route_summary", {})
    return {"pair_counts": dict(pair_counts), "flat": flat, "route_summary": dict(summary)}


def merge_route_breakdown(dst: dict[str, int], breakdown: dict[str, Any]) -> None:
    for k, v in breakdown.get("flat", {}).items():
        dst[k] = dst.get(k, 0) + int(v)
