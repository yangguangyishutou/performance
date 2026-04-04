"""Pass-through A backend implementing ``AChannelProtocol``."""

from __future__ import annotations

from typing import Any

from rewrite_stage3ab.channels.a_channel.protocol import AChannelProtocol


class AChannelStub:
    """No-op A channel — preserves text; empty candidate lists."""

    def collect_candidates(self, text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        del text, ctx
        return []

    def rank_candidates(self, candidates: list[dict[str, Any]], ctx: dict[str, Any]) -> list[dict[str, Any]]:
        del ctx
        return list(candidates)

    def evaluate_candidate(self, candidate: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        del ctx
        return {"ok": True, "candidate": candidate}

    def apply_assignments(self, text: str, ctx: dict[str, Any]) -> str:
        del ctx
        return text
