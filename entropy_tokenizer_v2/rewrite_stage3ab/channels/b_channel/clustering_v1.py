"""
Clustering backends: HDBSCAN when available, else explicit lexical fallback (no silent skip).
"""

from __future__ import annotations

import math
from typing import Any, Callable, List, Sequence, Tuple

from rewrite_stage3ab.contracts.enums import ClusterBackendId

BackendFactory = Callable[[], Any]

_REGISTRY: dict[ClusterBackendId, BackendFactory] = {}

_HAS_HDBSCAN = False
_HAS_NUMPY = False
try:
    import numpy as np  # type: ignore

    _HAS_NUMPY = True
except ImportError:
    np = None  # type: ignore

try:
    import hdbscan  # type: ignore

    _HAS_HDBSCAN = bool(_HAS_NUMPY)
except ImportError:
    hdbscan = None  # type: ignore


def register_cluster_backend(bid: ClusterBackendId, factory: BackendFactory) -> None:
    _REGISTRY[bid] = factory


def get_cluster_backend(bid: ClusterBackendId) -> Any:
    if bid not in _REGISTRY:
        raise KeyError(f"no clustering backend registered for {bid!r}")
    return _REGISTRY[bid]()


def list_registered_backends() -> list[ClusterBackendId]:
    return list(_REGISTRY.keys())


def hdbscan_available() -> bool:
    return _HAS_HDBSCAN


def _string_features(s: str) -> List[float]:
    """Mixed lexical–character baseline (fixed dim) without sklearn."""
    L = max(1, len(s))
    uniq = len(set(s)) / L
    digits = sum(c.isdigit() for c in s) / L
    alpha = sum(c.isalpha() for c in s) / L
    ws = sum(c.isspace() for c in s) / L
    up = sum(c.isupper() for c in s) / L
    h = [0.0] * 16
    for c in s:
        h[ord(c) % 16] += 1.0
    h = [v / L for v in h]
    return [math.log1p(L), uniq, digits, alpha, ws, up, *h]


def cluster_labels_hdbscan_or_fallback(strings: Sequence[str], *, min_cluster_size: int = 2) -> Tuple[List[int], str]:
    """
    Returns ``(label_per_index, backend_note)``.

    ``-1`` means noise / singleton (caller may still apply reference fallback pairwise).
    """
    if len(strings) == 0:
        return [], "empty"
    if _HAS_HDBSCAN and np is not None and hdbscan is not None:
        X = np.array([_string_features(s) for s in strings], dtype=np.float64)
        clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, metric="euclidean")
        labels = clusterer.fit_predict(X)
        return [int(x) for x in labels], "hdbscan_euclidean"

    # Explicit fallback: single-linkage by Jaccard on character sets (deterministic)
    n = len(strings)
    sets = [set(s) for s in strings]
    parent = list(range(n))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i: int, j: int) -> None:
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri

    def jaccard(a: set[str], b: set[str]) -> float:
        if not a and not b:
            return 1.0
        u = len(a | b)
        if u == 0:
            return 0.0
        return len(a & b) / u

    thr = 0.45
    for i in range(n):
        for j in range(i + 1, n):
            if jaccard(sets[i], sets[j]) >= thr:
                union(i, j)
    clusters: dict[int, list[int]] = {}
    for i in range(n):
        r = find(i)
        clusters.setdefault(r, []).append(i)
    labels = [-1] * n
    next_id = 0
    for _root, members in clusters.items():
        if len(members) >= min_cluster_size:
            for idx in members:
                labels[idx] = next_id
            next_id += 1
        else:
            for idx in members:
                labels[idx] = -1
    return labels, "lexical_jaccard_fallback_explicit"


class MixedLexicalCharBackend:
    """Callable facade used by B channel."""

    def __call__(self, strings: Sequence[str], *, min_cluster_size: int = 2) -> Tuple[List[int], str]:
        return cluster_labels_hdbscan_or_fallback(strings, min_cluster_size=min_cluster_size)


def _register_defaults() -> None:
    b = MixedLexicalCharBackend()
    register_cluster_backend(ClusterBackendId.MIXED_LEXICAL_CHAR, lambda: b)
    register_cluster_backend(ClusterBackendId.LEXICAL_BASELINE, lambda: b)
    register_cluster_backend(ClusterBackendId.HDBSCAN, lambda: b)
    register_cluster_backend(ClusterBackendId.HDBSCAN_FUTURE, lambda: b)


_register_defaults()
