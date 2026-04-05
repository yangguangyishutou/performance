"""
B channel: HDBSCAN / fallback clustering, near-duplicate noise groups, span-safe reference codec.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from rewrite_stage3ab.channels.b_channel.clustering_v1 import (
    get_cluster_backend,
    hdbscan_available,
    near_duplicate_noise_groups,
    word_jaccard_literal,
)
from rewrite_stage3ab.channels.b_channel.reference_codec import ReferenceCodecV1
from rewrite_stage3ab.contracts.enums import ClusterBackendId
from rewrite_stage3ab.orchestrator.stage2_router import FreeTextAsset, extract_python_free_text_assets


def _member_spans_from_candidates(members: list[dict[str, Any]]) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for m in members:
        cs, ce = m.get("char_start"), m.get("char_end")
        if cs is not None and ce is not None:
            out.append((int(cs), int(ce)))
    return out


def _cluster_low_quality(texts: list[str], cluster: dict[str, Any]) -> bool:
    if cluster.get("fallback_exact") or cluster.get("fallback_near_dup"):
        return False
    uniq = list(dict.fromkeys(texts))
    if len(uniq) < 3:
        return False
    pairs: list[float] = []
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            pairs.append(word_jaccard_literal(uniq[i], uniq[j]))
    if not pairs:
        return False
    return sum(pairs) / len(pairs) < 0.18


class BChannelV1:
    def __init__(self) -> None:
        self._codec = ReferenceCodecV1()
        self._next_sym = 0

    def _next_symbol_name(self) -> str:
        return f"_b{self._next_sym}"

    def _commit_symbol(self) -> None:
        self._next_sym += 1

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
            ctx["b_hdbscan_noise_points"] = 0
            ctx["b_hdbscan_noise_singleton_residual"] = 0
            return []
        strings = [str(c.get("text", "")) for c in candidates]
        backend = get_cluster_backend(ClusterBackendId.HDBSCAN)
        labels, note = backend(strings, min_cluster_size=2)
        ctx["b_clustering_backend_note"] = note
        ctx["b_hdbscan_actually_used"] = str(note).lower().startswith("hdbscan")
        ctx["b_hdbscan_runtime_available"] = hdbscan_available()
        clusters_map: dict[int, list[int]] = defaultdict(list)
        for i, lab in enumerate(labels):
            if lab >= 0:
                clusters_map[lab].append(i)
        formed: list[dict[str, Any]] = []
        for lab, idxs in clusters_map.items():
            members = [candidates[i] for i in idxs]
            formed.append(
                {
                    "cluster_id": f"c{lab}",
                    "member_indices": idxs,
                    "members": members,
                    "texts": [strings[i] for i in idxs],
                    "member_spans": _member_spans_from_candidates(members),
                    "cluster_path": "standard_hdbscan_or_lexical",
                    "fallback_exact": False,
                    "fallback_near_dup": False,
                }
            )
        noise = [i for i, lab in enumerate(labels) if lab < 0]
        buckets: dict[str, list[int]] = defaultdict(list)
        for i, s in enumerate(strings):
            buckets[s].append(i)
        claimed_noise: set[int] = set()
        fid = 0
        for _s, idxs in buckets.items():
            if len(idxs) < 2:
                continue
            if not all(labels[i] < 0 for i in idxs):
                continue
            members = [candidates[i] for i in idxs]
            formed.append(
                {
                    "cluster_id": f"exact{fid}",
                    "member_indices": idxs,
                    "members": members,
                    "texts": [strings[i] for i in idxs],
                    "member_spans": _member_spans_from_candidates(members),
                    "cluster_path": "exact_repeat_fallback",
                    "fallback_exact": True,
                    "fallback_near_dup": False,
                }
            )
            claimed_noise.update(idxs)
            fid += 1
        nid = 0
        remaining_noise = [i for i in noise if i not in claimed_noise]
        near_grouped: set[int] = set()
        for grp in near_duplicate_noise_groups(strings, remaining_noise):
            members = [candidates[i] for i in grp]
            near_grouped.update(grp)
            formed.append(
                {
                    "cluster_id": f"nd{nid}",
                    "member_indices": grp,
                    "members": members,
                    "texts": [strings[i] for i in grp],
                    "member_spans": _member_spans_from_candidates(members),
                    "cluster_path": "near_duplicate_noise",
                    "fallback_exact": False,
                    "fallback_near_dup": True,
                }
            )
            nid += 1
        ctx["b_hdbscan_noise_points"] = len(noise)
        ctx["b_hdbscan_noise_singleton_residual"] = len([i for i in remaining_noise if i not in near_grouped])
        return formed

    def evaluate_cluster(self, cluster: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        texts: list[str] = list(cluster.get("texts", []))
        if len(texts) < 2:
            return {"ok": False, "cluster": cluster, "reason": "insufficient_members"}
        if _cluster_low_quality(texts, cluster):
            return {"ok": False, "cluster": cluster, "reason": "rejected_for_low_quality"}
        uniq = list(dict.fromkeys(texts))
        rep = self._codec.select_representative(uniq, {**ctx, "tokenizer_key": ctx.get("tokenizer_key", "gpt4")})
        sym = self._next_symbol_name()
        path = str(cluster.get("cluster_path", "unknown"))
        fr = ""
        if cluster.get("fallback_exact"):
            fr = "exact_repeat_fallback"
        elif cluster.get("fallback_near_dup"):
            fr = "near_duplicate_fallback"
        sub = {
            "tokenizer_key": ctx.get("tokenizer_key", "gpt4"),
            "cluster_members": texts,
            "member_spans": list(cluster.get("member_spans", [])),
            "cluster_path": path,
            "fallback_reason": fr,
        }
        emission = self._codec.emit(rep, sym, sub)
        ev: dict[str, Any] = {
            "ok": emission.net_true > 0,
            "cluster": cluster,
            "emission": emission,
            "cluster_path": path,
            "fallback_reason": fr,
            "cluster_backend_note": ctx.get("b_clustering_backend_note"),
            "hdbscan_runtime_available": ctx.get("b_hdbscan_runtime_available"),
            "hdbscan_actually_used": ctx.get("b_hdbscan_actually_used"),
            "representative_token_len_true": emission.representative_meta.get("representative_token_len_true"),
            "cluster_raw_total_true": emission.raw_total_true,
            "cluster_ref_total_true": emission.ref_total_true,
            "cluster_intro_true": emission.intro_tokens_true,
            "cluster_net_true": emission.net_true,
        }
        if emission.net_true <= 0:
            ev["reason"] = "rejected_for_no_net_gain"
            ev["ok"] = False
        else:
            ev["reason"] = "accepted"
            self._commit_symbol()
        return ev

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
