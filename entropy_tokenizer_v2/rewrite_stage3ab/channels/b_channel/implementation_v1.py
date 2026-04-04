"""
B channel: HDBSCAN (or explicit fallback) clustering + reference-style literal compression.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from rewrite_stage3ab.channels.b_channel.clustering_v1 import (
    get_cluster_backend,
    hdbscan_available,
)
from rewrite_stage3ab.channels.b_channel.reference_codec import ReferenceCodecV1
from rewrite_stage3ab.contracts.enums import ClusterBackendId
from rewrite_stage3ab.orchestrator.stage2_router import FreeTextAsset, extract_python_free_text_assets


class BChannelV1:
    def __init__(self) -> None:
        self._codec = ReferenceCodecV1()
        self._next_sym = 0

    def _mint_symbol(self) -> str:
        s = f"_BREF{self._next_sym}"
        self._next_sym += 1
        return s

    def collect_free_text_candidates(self, text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        sid = str(ctx.get("source_id", "unknown"))
        out: list[dict[str, Any]] = []
        for a in extract_python_free_text_assets(sid, text):
            k = a.metadata.get("asset_kind")
            if k in ("string_literal", "docstring"):
                out.append(
                    {
                        "text": a.text,
                        "asset_id": a.asset_id,
                        "kind": k,
                        "char_start": a.char_start,
                        "char_end": a.char_end,
                    }
                )
        routed = ctx.get("b_routed_assets")
        if routed:
            for item in routed:
                if isinstance(item, FreeTextAsset):
                    out.append(
                        {
                            "text": item.text,
                            "asset_id": item.asset_id,
                            "kind": item.metadata.get("asset_kind", "routed"),
                            "char_start": item.char_start,
                            "char_end": item.char_end,
                        }
                    )
                elif isinstance(item, dict):
                    out.append(item)
        ctx["b_collect_dedupe"] = len(out)
        return out

    def cluster_candidates(self, candidates: list[dict[str, Any]], ctx: dict[str, Any]) -> list[dict[str, Any]]:
        if not candidates:
            return []
        strings = [str(c.get("text", "")) for c in candidates]
        backend = get_cluster_backend(ClusterBackendId.HDBSCAN)
        labels, note = backend(strings, min_cluster_size=2)
        ctx["b_clustering_backend_note"] = note
        ctx["b_hdbscan_runtime_available"] = hdbscan_available()
        clusters: dict[int, list[int]] = defaultdict(list)
        for i, lab in enumerate(labels):
            if lab >= 0:
                clusters[lab].append(i)
        formed: list[dict[str, Any]] = []
        for lab, idxs in clusters.items():
            formed.append(
                {
                    "cluster_id": f"c{lab}",
                    "member_indices": idxs,
                    "members": [candidates[i] for i in idxs],
                    "texts": [strings[i] for i in idxs],
                }
            )
        # Exact-duplicate fallback: only indices that HDBSCAN marked noise (-1)
        buckets: dict[str, list[int]] = defaultdict(list)
        for i, s in enumerate(strings):
            buckets[s].append(i)
        fid = 0
        for _s, idxs in buckets.items():
            if len(idxs) < 2:
                continue
            if not all(labels[i] < 0 for i in idxs):
                continue
            formed.append(
                {
                    "cluster_id": f"exact{fid}",
                    "member_indices": idxs,
                    "members": [candidates[i] for i in idxs],
                    "texts": [strings[i] for i in idxs],
                    "fallback_exact": True,
                }
            )
            fid += 1
        return formed

    def evaluate_cluster(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        texts: list[str] = list(cluster.get("texts", []))
        if len(texts) < 2:
            return {"ok": False, "cluster": cluster, "reason": "cluster_too_small"}
        uniq = list(dict.fromkeys(texts))
        rep = self._codec.select_representative(uniq, {**ctx, "tokenizer_key": ctx.get("tokenizer_key", "gpt4")})
        sym = self._mint_symbol()
        sub = {
            "tokenizer_key": ctx.get("tokenizer_key", "gpt4"),
            "cluster_members": texts,
            "member_spans": [],
        }
        emission = self._codec.emit(rep, sym, sub)
        if emission.net_true <= 0:
            return {
                "ok": False,
                "cluster": cluster,
                "reason": "no_net_gain",
                "emission": emission,
            }
        return {"ok": True, "cluster": cluster, "emission": emission, "reason": "accepted"}

    def emit_reference_or_template(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        ev = self.evaluate_cluster(cluster, ctx)
        if not ev.get("ok"):
            return {}
        em = ev["emission"]
        return {
            "symbol": em.symbol,
            "representative": em.representative,
            "intro_tokens_true": em.intro_tokens_true,
            "net_true": em.net_true,
            "member_texts": em.member_texts,
        }

    def apply_cluster_rewrites(self, text: str, ctx: dict[str, Any]) -> str:
        self._next_sym = 0
        cands = self.collect_free_text_candidates(text, ctx)
        clusters = self.cluster_candidates(cands, ctx)
        ctx.setdefault("b_cluster_evaluations", [])
        ctx.setdefault("b_emissions", [])
        out = text
        for cl in clusters:
            ev = self.evaluate_cluster(cl, ctx)
            ctx["b_cluster_evaluations"].append(ev)
            if not ev.get("ok"):
                continue
            em = ev["emission"]
            out = self._codec.rewrite_text(out, em, ctx)
            ctx["b_emissions"].append(em)
        return out
