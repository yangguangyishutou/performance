"""Compatibility shim — real implementation lives in ``implementation_v1``."""

from __future__ import annotations

from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1

AChannelStub = AChannelV1

__all__ = ["AChannelStub", "AChannelV1"]
