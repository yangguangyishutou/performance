"""
Corpus-level rollups for rewrite Stage3 AB (200k / large eval).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rewrite_stage3ab.contracts.data_models import Stage3ABRunResult


def _sum_route(dst: dict[str, int], src: dict[str, Any]) -> None:
    for k, v in src.items():
        if isinstance(v, int):
            dst[k] = dst.get(k, 0) + v


@dataclass
class RewriteCorpusRollup:
    n_sources: int = 0
    total_input_tokens_true: int = 0
    total_after_b_tokens_true: int = 0
    total_after_clean_tokens_true: int = 0
    total_after_a_tokens_true: int = 0
    total_final_tokens_true: int = 0
    total_a_saved_true: int = 0
    total_b_saved_true: int = 0
    total_a_intro_true: int = 0
    total_b_intro_true: int = 0
    total_net_true: int = 0
    total_a_candidates: int = 0
    total_a_selected: int = 0
    total_b_assets: int = 0
    total_b_clusters: int = 0
    total_b_clusters_selected: int = 0
    route_initial: dict[str, int] = field(default_factory=dict)
    route_post_b: dict[str, int] = field(default_factory=dict)
    alias_strict_single_selections: int = 0
    alias_tier_counts: dict[str, int] = field(default_factory=dict)

    def add_run(self, r: Stage3ABRunResult) -> None:
        self.n_sources += 1
        ex = r.run_extras or {}
        self.total_input_tokens_true += r.input_snapshot.token_count_true
        self.total_after_b_tokens_true += int(ex.get("after_b_token_true", r.after_b_snapshot.token_count_true))
        self.total_after_clean_tokens_true += int(ex.get("after_clean_token_true", 0))
        self.total_after_a_tokens_true += int(ex.get("after_a_token_true", r.after_a_snapshot.token_count_true))
        self.total_final_tokens_true += r.final_snapshot.token_count_true
        self.total_a_saved_true += int(r.a_result.saved_tokens_true)
        self.total_b_saved_true += int(r.b_result.saved_tokens_true)
        self.total_a_intro_true += int(r.a_result.intro_tokens_true)
        self.total_b_intro_true += int(r.b_result.intro_tokens_true)
        self.total_net_true += int(r.a_result.net_saved_true) + int(r.b_result.net_saved_true)
        self.total_a_candidates += int(ex.get("total_a_candidates_collected", 0))
        self.total_a_selected += int(ex.get("total_a_selected", 0))
        self.total_b_assets += int(r.b_result.visible_candidates)
        self.total_b_clusters += int(ex.get("total_b_clusters_evaluated", r.b_result.clusters_formed))
        self.total_b_clusters_selected += int(ex.get("total_b_clusters_selected", r.b_result.clusters_selected))
        rs0 = ex.get("route_summary_initial") or {}
        rs1 = ex.get("route_summary_post_b") or {}
        if isinstance(rs0, dict):
            _sum_route(self.route_initial, rs0)
        if isinstance(rs1, dict):
            _sum_route(self.route_post_b, rs1)
        apt = ex.get("alias_pool_telemetry") or {}
        if isinstance(apt, dict):
            for t, c in (apt.get("alias_selections_by_tier") or {}).items():
                self.alias_tier_counts[t] = self.alias_tier_counts.get(t, 0) + int(c)
            for row in r.a_result.alias_assignments:
                if row.get("alias_is_strict_single_token"):
                    self.alias_strict_single_selections += 1

    def to_summary_row(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "n_sources": self.n_sources,
            "total_input_tokens_true": self.total_input_tokens_true,
            "total_after_b_tokens_true": self.total_after_b_tokens_true,
            "total_after_clean_tokens_true": self.total_after_clean_tokens_true,
            "total_after_a_tokens_true": self.total_after_a_tokens_true,
            "total_final_tokens_true": self.total_final_tokens_true,
            "total_a_saved_true": self.total_a_saved_true,
            "total_b_saved_true": self.total_b_saved_true,
            "total_a_intro_true": self.total_a_intro_true,
            "total_b_intro_true": self.total_b_intro_true,
            "total_net_true": self.total_net_true,
            "total_a_candidates": self.total_a_candidates,
            "total_a_selected": self.total_a_selected,
            "total_b_assets": self.total_b_assets,
            "total_b_clusters": self.total_b_clusters,
            "total_b_clusters_selected": self.total_b_clusters_selected,
            "alias_strict_single_selections": self.alias_strict_single_selections,
            "alias_tier_counts_json": dict(self.alias_tier_counts),
        }
        for k, v in self.route_initial.items():
            out[f"route_initial__{k}"] = v
        for k, v in self.route_post_b.items():
            out[f"route_post_b__{k}"] = v
        return out


def merge_route_into(dst: dict[str, int], key: str, r: Stage3ABRunResult) -> None:
    ex = r.run_extras or {}
    rs = ex.get(key) or {}
    if isinstance(rs, dict):
        _sum_route(dst, rs)
