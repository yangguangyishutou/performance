"""
Clustering backends: HDBSCAN when available, else explicit lexical fallback (no silent skip).

Also provides **near-duplicate** grouping for noise points (exact / norm-ws / lexical / char overlap).
"""

from __future__ import annotations

import ast
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


def _inner_string_value(s: str) -> str:
    try:
        v = ast.literal_eval(s)
        if isinstance(v, str):
            return v
    except Exception:
        pass
    return s


def _norm_ws_literal(s: str) -> str:
    return " ".join(_inner_string_value(s).split())


def word_jaccard_literal(a: str, b: str) -> float:
    wa = set(_inner_string_value(a).lower().split())
    wb = set(_inner_string_value(b).lower().split())
    if not wa and not wb:
        return 1.0
    return len(wa & wb) / len(wa | wb)


def char_jaccard_literal(a: str, b: str) -> float:
    ca = set(_inner_string_value(a))
    cb = set(_inner_string_value(b))
    if not ca and not cb:
        return 1.0
    return len(ca & cb) / len(ca | cb)


def near_duplicate_noise_groups(
    strings: Sequence[str],
    noise_indices: Sequence[int],
    *,
    word_thr: float = 0.72,
    char_thr: float = 0.55,
) -> list[list[int]]:
    """
    Union-find on *noise* indices only: exact, normalized-whitespace, lexical, char-overlap edges.
    Returns disjoint member lists of size >= 2.
    """
    idxs = list(noise_indices)
    if len(idxs) < 2:
        return []
    parent = {i: i for i in idxs}

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for ii in range(len(idxs)):
        for jj in range(ii + 1, len(idxs)):
            i, j = idxs[ii], idxs[jj]
            si, sj = strings[i], strings[j]
            if si == sj:
                union(i, j)
                continue
            if _norm_ws_literal(si) == _norm_ws_literal(sj) and len(_norm_ws_literal(si)) > 0:
                union(i, j)
                continue
            if word_jaccard_literal(si, sj) >= word_thr:
                union(i, j)
                continue
            if char_jaccard_literal(si, sj) >= char_thr:
                union(i, j)
    buckets: dict[int, list[int]] = {}
    for i in idxs:
        r = find(i)
        buckets.setdefault(r, []).append(i)
    return [sorted(v) for v in buckets.values() if len(v) >= 2]


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
