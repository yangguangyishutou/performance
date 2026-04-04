"""
B-channel Protocol: free-text → clusters → reference/template rewrites.

Backends: lexical, mixed, HDBSCAN path with explicit fallback (see ``clustering_v1``).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BChannelProtocol(Protocol):
    def collect_free_text_candidates(self, text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def cluster_candidates(self, candidates: list[dict[str, Any]], ctx: dict[str, Any]) -> list[dict[str, Any]]:
        ...

    def evaluate_cluster(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        ...

    def emit_reference_or_template(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        ...

    def apply_cluster_rewrites(self, text: str, ctx: dict[str, Any]) -> str:
        ...
