"""
Deprecated module name: clustering backends are registered in ``clustering_v1``.

Import this module to ensure default backends are registered in legacy call sites.
"""

from __future__ import annotations

from rewrite_stage3ab.channels.b_channel.clustering_v1 import (  # noqa: F401
    get_cluster_backend,
    hdbscan_available,
    list_registered_backends,
    register_cluster_backend,
)

__all__ = [
    "get_cluster_backend",
    "hdbscan_available",
    "list_registered_backends",
    "register_cluster_backend",
]
