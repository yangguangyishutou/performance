"""
Clustering backend registry (identifiers only — no algorithms).

TODO: Register factory callables that build real clusterers from config.
"""

from __future__ import annotations

from typing import Any, Callable

from rewrite_stage3ab.contracts.enums import ClusterBackendId

BackendFactory = Callable[[], Any]

_REGISTRY: dict[ClusterBackendId, BackendFactory] = {}


def register_cluster_backend(bid: ClusterBackendId, factory: BackendFactory) -> None:
    _REGISTRY[bid] = factory


def get_cluster_backend(bid: ClusterBackendId) -> Any:
    """Return backend instance; raises if not registered."""
    if bid not in _REGISTRY:
        raise KeyError(f"no clustering backend registered for {bid!r} (scaffold round)")
    return _REGISTRY[bid]()


def list_registered_backends() -> list[ClusterBackendId]:
    return list(_REGISTRY.keys())
