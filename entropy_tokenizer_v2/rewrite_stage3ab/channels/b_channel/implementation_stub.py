"""Compatibility shim — real implementation lives in ``implementation_v1``."""

from __future__ import annotations

from rewrite_stage3ab.channels.b_channel.implementation_v1 import BChannelV1

BChannelStub = BChannelV1

__all__ = ["BChannelStub", "BChannelV1"]
