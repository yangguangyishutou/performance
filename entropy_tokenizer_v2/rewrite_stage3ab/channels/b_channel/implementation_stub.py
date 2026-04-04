"""Pass-through B backend implementing ``BChannelProtocol``."""

from __future__ import annotations

from typing import Any

from rewrite_stage3ab.channels.b_channel.protocol import BChannelProtocol


class BChannelStub:
    def collect_free_text_candidates(self, text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        del text, ctx
        return []

    def cluster_candidates(self, candidates: list[dict[str, Any]], ctx: dict[str, Any]) -> list[dict[str, Any]]:
        del ctx
        return []

    def evaluate_cluster(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        del ctx
        return {"ok": False, "cluster": cluster, "reason": "stub"}

    def emit_reference_or_template(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        del cluster, ctx
        return {}

    def apply_cluster_rewrites(self, text: str, ctx: dict[str, Any]) -> str:
        del ctx
        return text
