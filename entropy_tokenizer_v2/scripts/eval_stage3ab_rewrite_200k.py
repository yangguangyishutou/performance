#!/usr/bin/env python3
"""
Frozen 200k corpus: old hybrid_ab vs fast_try-style hybrid_ab vs rewrite Stage3 AB.

Reads ``results/stage3ab_starcoder_200k/frozen_corpus_manifest.json`` and
``frozen_corpus_sources.jsonl`` (no resampling). Writes under ``results_rewrite_200k/``.
"""

from __future__ import annotations

import csv
import dataclasses
import json
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from eval import bootstrap_v2  # noqa: E402

bootstrap_v2.ensure()

from config import EVAL_TOKENIZERS  # noqa: E402
from marker_count import encode as mc_encode  # noqa: E402
from pipeline import apply_stage1_with_stats, build_stage2_config, resolve_stage2_for_pipeline  # noqa: E402
from repo_miner import _load_tokenizer, mine_from_sources  # noqa: E402
from rewrite_stage3ab.contracts.data_models import SourceUnit  # noqa: E402
from rewrite_stage3ab.contracts.enums import TelemetryEventKind  # noqa: E402
from rewrite_stage3ab.diagnostics.a_probe import (  # noqa: E402
    aggregate_attr_occ_by_depth_caps,
    diagnose_a_evaluations,
    iter_short_name_filtered_records,
    scan_string_path_literal_stats,
)
from rewrite_stage3ab.diagnostics.route_probe import merge_route_breakdown, route_breakdown_for_text  # noqa: E402
from rewrite_stage3ab.orchestrator.pipeline import run_scaffold_on_units  # noqa: E402
from rewrite_stage3ab.telemetry.aggregate import RewriteCorpusRollup  # noqa: E402
from rewrite_stage3ab.telemetry.ledger import JsonlTelemetryLedger  # noqa: E402
from stage2.cleaning import stage2_clean_skip_syn_and_stats  # noqa: E402
from stage3.backends.hybrid_ab_backend import (  # noqa: E402
    HybridABConfig,
    _apply_hybrid_ab_file_guardrail,
    encode_stage3_hybrid_ab,
    hybrid_ab_config_from_summary,
)

TOKENIZER_KEY = "gpt4"
DEFAULT_FROZEN = ROOT / "results" / "stage3ab_starcoder_200k"
OUT_DIR = ROOT / "results_rewrite_200k"


def _true_len(text: str, tokenizer, tok_type: str) -> int:
    return len(mc_encode(tokenizer, tok_type, text))


def _load_frozen_sources(frozen_dir: Path) -> tuple[dict, list[str]]:
    man_path = frozen_dir / "frozen_corpus_manifest.json"
    jsonl_path = frozen_dir / "frozen_corpus_sources.jsonl"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    rows: list[dict] = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    rows.sort(key=lambda r: int(r["i"]))
    return manifest, [str(r["content"]) for r in rows]


def _fast_try_hybrid_config(base: HybridABConfig) -> HybridABConfig:
    """Mirror ``eval_stage3ab_starcoder_200k_fast_try_safe`` knob intent (explicit cfg)."""
    return dataclasses.replace(
        base,
        mode="hybrid",
        a_min_occ=2,
        min_raw_token_len=2,
        max_alias_token_len=3,
        a_alias_rank_pool_cap=64,
        a_enable_local_combo_greedy=True,
        a_combo_max_additions=48,
        b_similarity_kind="mixed",
        b_lexical_weight=0.6,
        b_char_weight=0.4,
        b_similarity_threshold=0.78,
        b_risk_threshold=0.68,
        b_min_cluster_size=1,
        b_channel_priority="normal",
    )


def _hybrid_pipeline_file(
    after_s2: str,
    conf: HybridABConfig,
    tokenizer,
    tok_type: str,
) -> tuple[str, int, int]:
    before = _true_len(after_s2, tokenizer, tok_type)
    raw = encode_stage3_hybrid_ab(after_s2, tokenizer=tokenizer, tok_type=tok_type, cfg=conf)
    final, _ = _apply_hybrid_ab_file_guardrail(after_s2, raw, conf=conf, tokenizer=tokenizer, tok_type=tok_type)
    out_txt = final.encoded_text
    after = _true_len(out_txt, tokenizer, tok_type)
    return out_txt, before, after


def _pct(num: int, den: int) -> float:
    return (100.0 * num / den) if den else 0.0


def _merge_top_lists(dst: list[dict[str, Any]], src: list[dict[str, Any]], *, key, limit: int = 50) -> None:
    dst.extend(src)
    dst.sort(key=key, reverse=True)
    del dst[limit:]


def _sz_bucket(n: int) -> str:
    if n <= 2:
        return "2"
    if n == 3:
        return "3"
    if n == 4:
        return "4"
    return "5+"


def _write_accounting_gap_md(path: Path) -> None:
    body = """# rewrite_200k 与旧主线评测口径差异（定点说明）

## 已对齐（本脚本内）

- **Tokenizer**：与仓库 `EVAL_TOKENIZERS` / `marker_count.encode` 一致，true token 以 `mc_encode` 长度计量。
- **Stage1**：`apply_stage1_with_stats` 与 `mine_from_sources` 摘要一致。
- **Stage2**：`stage2_clean_skip_syn_and_stats` + `build_stage2_config` / `resolve_stage2_for_pipeline`，rewrite 与 hybrid 分支共用同一 `after_s2` 文本。
- **Stage3 输入口径**：old / fast_try 的 hybrid_ab 与 rewrite 的对比均以 **after_s2 的 true token 数为 before**，Stage3 后再计 after。

## 未与旧主线完全同构

- **v2_eval / marker accounting**：本脚本未走完整 `v2_eval` 流水线；未做与生产一致的 marker 级账本对齐。
- **hybrid_ab guardrail**：old / fast_try 路径调用了 `_apply_hybrid_ab_file_guardrail`；rewrite Stage3 为独立 orchestrator，**未**接入同一 guardrail 实现。
- **A/B 经济学**：rewrite 使用 `AChannelV1` / `BChannelV1` 的 net_true 门控与单候选接受规则；与 hybrid_ab 的 combo / 风险阈值等 **算法不同**，仅可比「同一 after_s2 上的启发式压缩量」，不可视为同一后端重复实验。

## Apples-to-apples（可信对比）

- **同一输入**：三条线均使用 **同一 `after_s2` 文本** 作为 Stage3 输入计量点。
- **同一 tokenizer**：`mc_encode` / true token 长度定义一致。
- **可比指标**：每个文件的 `before_true`（after_s2）与 Stage3 后的 `after_true` 差分，在脚本内汇总为语料级 delta。

## 非生产等价（诊断向对比）

- rewrite 未跑 **hybrid_ab guardrail**；old / fast_try 跑了。
- 未接入 **v2_eval / marker** 完整账本。
- **后端算法不同**：rewrite 为 AChannelV1/BChannelV1；hybrid_ab 为另一套 A/B 逻辑。

## 结论用法

- rewrite_200k 结果适合诊断 **rewrite 架构自身**（路由留存、A/B 门、span 命中率）。
- 与 old baseline 的「谁赢 token」在 **同一 after_s2 口径下**可比较趋势，但 **不宜称为生产链路等价 A/B**。
"""
    path.write_text(body, encoding="utf-8")


def _write_failure_artifacts(
    *,
    out_dir: Path,
    n_sources: int,
    a_diag_rows: list[dict[str, Any]],
    parse_ok_true: int,
    parse_ok_false: int,
    short_name_counter: Counter[tuple[str, str]],
    attr_depth_corpus: dict[str, int],
    string_path_corpus: dict[str, int],
    b_singleton_n: int,
    b_singleton_chars: int,
    b_lq_n: int,
    b_lq_mem_sum: int,
    b_lq_char_sum: int,
    b_no_net_n: int,
    intro_by_bucket: dict[str, dict[str, int]],
    b_span_corpus: dict[str, int],
    route_flat: dict[str, int],
    sum_row: dict[str, Any],
    totals_rw_in: int,
    totals_rw_out: int,
    totals_old_before: int,
    totals_old_after: int,
    totals_fast_before: int,
    totals_fast_after: int,
    a_corpus_totals: dict[str, int],
) -> None:
    top_short = sorted(short_name_counter.items(), key=lambda x: -x[1])[:50]
    with (out_dir / "rewrite_200k_short_name_filtered_top50.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["literal", "field", "occ_sum_corpus"])
        w.writeheader()
        for (lit, fld), occ in top_short:
            w.writerow({"literal": lit, "field": fld, "occ_sum_corpus": occ})

    with (out_dir / "rewrite_200k_a_attr_depth_hist.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"])
        w.writeheader()
        for k in sorted(attr_depth_corpus.keys()):
            w.writerow({"metric": k, "value": attr_depth_corpus[k]})

    with (out_dir / "rewrite_200k_a_string_exact_path_stats.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "value"])
        w.writeheader()
        for k, v in string_path_corpus.items():
            w.writerow({"metric": k, "value": v})
        w.writerow({"metric": "eval_context_allow_string_exact_path_true_files", "value": 0})
        w.writerow({"metric": "note", "value": "rewrite_200k 未注入 string_exact_path metadata；AST 扫描仅统计类 path 字符串常量"})

    with (out_dir / "rewrite_200k_b_singleton_stats.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "n_cluster_reject_insufficient_members",
                "sum_total_text_chars_in_those_clusters",
                "n_sources",
                "avg_chars_per_singleton_reject",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "n_cluster_reject_insufficient_members": b_singleton_n,
                "sum_total_text_chars_in_those_clusters": b_singleton_chars,
                "n_sources": n_sources,
                "avg_chars_per_singleton_reject": f"{(b_singleton_chars / b_singleton_n):.2f}" if b_singleton_n else "0",
            }
        )

    with (out_dir / "rewrite_200k_b_low_quality_stats.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "n_rejected_for_low_quality",
                "avg_n_members",
                "avg_total_text_chars",
            ],
        )
        w.writeheader()
        w.writerow(
            {
                "n_rejected_for_low_quality": b_lq_n,
                "avg_n_members": f"{(b_lq_mem_sum / b_lq_n):.4f}" if b_lq_n else "0",
                "avg_total_text_chars": f"{(b_lq_char_sum / b_lq_n):.2f}" if b_lq_n else "0",
            }
        )

    with (out_dir / "rewrite_200k_b_intro_breakdown.csv").open("w", newline="", encoding="utf-8") as f:
        cols = [
            "cluster_size_bucket",
            "n_accepted_reference_emitted",
            "n_rejected_no_net_gain",
            "sum_raw_total_true_accepted",
            "sum_intro_true_accepted",
            "sum_net_true_accepted",
            "sum_raw_total_true_rejected_no_net",
            "sum_intro_true_rejected_no_net",
            "sum_cluster_net_true_rejected_no_net",
        ]
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for bkt in ["2", "3", "4", "5+"]:
            row = intro_by_bucket.get(bkt, {})
            w.writerow(
                {
                    "cluster_size_bucket": bkt,
                    "n_accepted_reference_emitted": int(row.get("n_acc", 0)),
                    "n_rejected_no_net_gain": int(row.get("n_rej_nn", 0)),
                    "sum_raw_total_true_accepted": int(row.get("raw_acc", 0)),
                    "sum_intro_true_accepted": int(row.get("intro_acc", 0)),
                    "sum_net_true_accepted": int(row.get("net_acc", 0)),
                    "sum_raw_total_true_rejected_no_net": int(row.get("raw_rej", 0)),
                    "sum_intro_true_rejected_no_net": int(row.get("intro_rej", 0)),
                    "sum_cluster_net_true_rejected_no_net": int(row.get("net_rej", 0)),
                }
            )

    hits = int(b_span_corpus.get("b_span_safe_rewrite_hits", 0))
    mb = int(b_span_corpus.get("b_span_safe_rewrite_misses_bounds", 0))
    mm = int(b_span_corpus.get("b_span_safe_rewrite_misses_slice_mismatch", 0))
    gf = int(b_span_corpus.get("b_global_replace_fallback_hits", 0))
    span_try = hits + mb + mm
    ratio_hit = (hits / span_try) if span_try else 0.0
    ratio_mismatch = (mm / span_try) if span_try else 0.0
    span_md = f"""# B span-safe rewrite 语料汇总

## 原始计数（全文件求和）

- `span_hits`: {hits}
- `span_misses_bounds`: {mb}
- `span_misses_slice_mismatch`: {mm}
- `global_replace_fallback_clusters`: {gf}

## 比率（在「有 spans 时尝试 span 路径」的语义下）

- **span hit ratio** ≈ hits / (hits + bounds_miss + slice_mismatch) = **{ratio_hit:.4f}**（分母 {span_try}）
- **slice mismatch ratio** ≈ slice_mismatch / 同上分母 = **{ratio_mismatch:.4f}**
- **global fallback**：按簇计数；本语料 gf={gf}（无 span 时整簇走 replace）

## 解读要点

- slice_mismatch 相对 hit 偏高时，优先排查 **B 改写后偏移** 或 **member_spans 与改写后文本不对齐**。
"""
    (out_dir / "rewrite_200k_b_span_stats.md").write_text(span_md, encoding="utf-8")

    kind_actions: dict[str, Counter[str]] = defaultdict(Counter)
    for key, cnt in route_flat.items():
        if "__" not in key:
            continue
        kind, act = key.split("__", 1)
        kind_actions[kind][act] += cnt
    rows_rt: list[dict[str, Any]] = []
    for kind, acts in sorted(kind_actions.items()):
        tot = sum(acts.values())
        for act, c in sorted(acts.items(), key=lambda x: -x[1]):
            rows_rt.append(
                {
                    "asset_kind": kind,
                    "route_action": act,
                    "count": c,
                    "pct_within_kind": f"{(100.0 * c / tot):.4f}" if tot else "0",
                }
            )
    with (out_dir / "rewrite_200k_route_asset_breakdown.csv").open("w", newline="", encoding="utf-8") as f:
        keys = ["asset_kind", "route_action", "count", "pct_within_kind"]
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows_rt)

    cov = (100.0 * parse_ok_true / n_sources) if n_sources else 0.0
    n_nonempty = sum(1 for r in a_diag_rows if r.get("a_text_nonempty") in (True, "True"))
    n_ast_fail = sum(1 for r in a_diag_rows if r.get("ast_parse_failed") in (True, "True"))
    old_d = totals_old_before - totals_old_after
    fast_d = totals_fast_before - totals_fast_after
    rw_d = totals_rw_in - totals_rw_out
    root_md = f"""# rewrite_200k 失败根因报告（自动生成）

基于本次 `eval_stage3ab_rewrite_200k.py` 全量重跑结果。

## 1. A diagnostics 覆盖率

- **sources**: {n_sources}
- **A 输入非空** (`a_text_nonempty`): {n_nonempty}
- **parse_ok=True**（整文件 probe 跑通）: {parse_ok_true}
- **parse_ok=False**: {parse_ok_false}
- **其中 AST 解析失败** (`ast_parse_failed`): {n_ast_fail}
- **parse_ok 占全文件比例**: {cov:.2f}%

**说明**：rewrite 在 B 与 destructive route 之后，**A 输入常常不再是合法 Python 源码**（缩进/类体被破坏），`ast.parse` 失败与 **A 通道 collect 同样无法走 AST** 一致。此类 `parse_ok=False` **不是 eval 与 `after_route_clean_snapshot` 接线错误**，而是 **管线形态导致 A 诊断 probe 无法在语法层分析**。

## 2. A 通道（语料计数来自 a_diagnostics 行求和）

| 指标 | 值 |
|------|-----|
| a_candidates_total | {a_corpus_totals.get("a_candidates_total", 0)} |
| a_candidates_variable | {a_corpus_totals.get("a_candidates_variable", 0)} |
| a_candidates_attribute | {a_corpus_totals.get("a_candidates_attribute", 0)} |
| a_candidates_string_exact_path | {a_corpus_totals.get("a_candidates_string_exact_path", 0)} |
| filtered_short_name | {a_corpus_totals.get("a_candidates_filtered_short_name", 0)} |
| filtered_attr_depth | {a_corpus_totals.get("a_candidates_filtered_attr_depth", 0)} |
| no_legal_alias | {a_corpus_totals.get("a_candidates_no_legal_alias", 0)} |
| no_net_true_gain | {a_corpus_totals.get("a_candidates_no_net_true_gain", 0)} |
| gross_pos_net_neg | {a_corpus_totals.get("a_candidates_positive_gross_but_negative_net", 0)} |
| accepted | {a_corpus_totals.get("a_candidates_accepted", 0)} |

**属性后缀 occ（仅 len≥min 默认10）按深度上限**：见 `rewrite_200k_a_attr_depth_hist.csv`。  
**short_name 被挡 Top50**：`rewrite_200k_short_name_filtered_top50.csv`。

## 3. B 通道

- **insufficient_members（簇级 telemetry）**: {b_singleton_n}（见 `rewrite_200k_b_singleton_stats.csv`）
- **说明**：若此项为 0，通常 **不代表「没有单条长文本」**——多数单条字符串在聚类阶段为 **HDBSCAN 噪声**，**根本不会形成簇**，因此不会调用 `evaluate_cluster`，也就不会出现 `insufficient_members` 事件。单测里的 singleton 是 **显式单簇** 路径，与真语料不同。
- **rejected_for_low_quality**: {b_lq_n}（见 `rewrite_200k_b_low_quality_stats.csv`）
- **rejected_for_no_net_gain**: {b_no_net_n}
- **intro / 簇规模**: `rewrite_200k_b_intro_breakdown.csv`
- **span**: `rewrite_200k_b_span_stats.md`

## 4. Route

- 分桶 CSV: `rewrite_200k_route_asset_breakdown.csv`
- 与 summary 中 `route_initial__*` 一致可对读

## 5. 与 old / fast_try 语料级 delta（true token 求和）

| 路径 | delta |
|------|-------|
| old | {old_d} |
| fast_try | {fast_d} |
| rewrite | {rw_d} |

## 6. 根因 Top 3（结合本次数字）

1. **A 语法层失效**：{n_ast_fail}/{n_sources} 个文件 A 输入 `ast.parse` 失败；与 **长度门/深度门** 无关，是 **B + destructive route 后源码不可解析**，导致 A collect 与 AST probe 同时瘫痪。
2. **A 经济与规模（在可解析子集上）**：语料行求和 `a_candidates_total`={a_corpus_totals.get("a_candidates_total", 0)}，且 `no_net_true_gain`={a_corpus_totals.get("a_candidates_no_net_true_gain", 0)}；**几乎全部候选被 net 门杀掉**。
3. **语料级未赢**：rewrite Δ={rw_d} vs old Δ={old_d}；B 通道局部正收益不足以抵消全文与 intro 口径差异，见 summary 与 `rewrite_200k_b_span_stats.md`。

## 7. 评测口径

见 `rewrite_200k_accounting_gap.md`（同脚本生成）。

---
*提交/分支请以当前仓库为准；本文件仅描述本地一次 eval 结果。*
"""
    (out_dir / "rewrite_200k_failure_root_causes.md").write_text(root_md, encoding="utf-8")


def main() -> int:
    frozen_dir = Path(os.environ.get("ET_FROZEN_CORPUS_DIR", str(DEFAULT_FROZEN))).resolve()
    if not (frozen_dir / "frozen_corpus_sources.jsonl").is_file():
        print("[rewrite_200k] missing frozen corpus under", frozen_dir, file=sys.stderr)
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest, sources = _load_frozen_sources(frozen_dir)
    tok_cfg = EVAL_TOKENIZERS[TOKENIZER_KEY]
    tokenizer, tok_type = _load_tokenizer(TOKENIZER_KEY, tok_cfg)

    cache_name = f"starcoder_baseline{manifest.get('token_budget', 200000)}_hybrid_v1"
    print("[rewrite_200k] mine_from_sources cache=", cache_name, "n=", len(sources), flush=True)
    rc = mine_from_sources(
        sources=sources,
        tokenizer_key=TOKENIZER_KEY,
        tokenizer_cfg=tok_cfg,
        cache_name=cache_name,
        cache=True,
        verbose=False,
        stage3_backend="hybrid_ab",
    )

    conf_old = hybrid_ab_config_from_summary(dict(getattr(rc, "stage3_ab_summary", {}) or {}))
    if conf_old is None:
        conf_old = HybridABConfig(mode="hybrid", a_min_occ=2, b_min_cluster_size=2)
    if conf_old.mode != "hybrid":
        conf_old = dataclasses.replace(conf_old, mode="hybrid")
    conf_fast = _fast_try_hybrid_config(conf_old)

    s2_prof, s2_mode, _ = resolve_stage2_for_pipeline(rc, None, None)
    s2_cfg = build_stage2_config(profile=s2_prof, mode=s2_mode)

    rollup = RewriteCorpusRollup()
    ledger = JsonlTelemetryLedger(OUT_DIR / "rewrite_200k_ledger.jsonl")
    detail_rows: list[dict[str, Any]] = []
    a_diag_rows: list[dict[str, Any]] = []
    b_diag_rows: list[dict[str, Any]] = []
    route_flat_corpus: dict[str, int] = {}
    route_per_file_rows: list[dict[str, Any]] = []
    top_gross_neg: list[dict[str, Any]] = []
    top_long_ids: list[dict[str, Any]] = []
    top_high_occ: list[dict[str, Any]] = []
    short_name_global: Counter[tuple[str, str]] = Counter()
    attr_depth_corpus: defaultdict[str, int] = defaultdict(int)
    string_path_corpus: dict[str, int] = {
        "n_files_text_nonempty": 0,
        "n_files_ast_scan_ok_for_path_literals": 0,
        "sum_distinct_path_like_literals": 0,
        "sum_occurrences_path_like_literals": 0,
        "n_files_with_any_path_like_literal": 0,
    }
    b_singleton_n = 0
    b_singleton_chars = 0
    b_lq_n = 0
    b_lq_mem_sum = 0
    b_lq_char_sum = 0
    b_no_net_n = 0
    intro_by_bucket: defaultdict[str, defaultdict[str, int]] = defaultdict(lambda: defaultdict(int))

    totals_old_after = 0
    totals_old_before = 0
    totals_fast_after = 0
    totals_fast_before = 0
    totals_rw_in = 0
    totals_rw_out = 0

    ex: dict[str, Any | None] = {
        "a_ok": None,
        "a_rej": None,
        "b_ok": None,
        "b_rej": None,
        "route": None,
    }

    for i, raw in enumerate(sources):
        sid = f"frozen:{i}"
        s1, _ = apply_stage1_with_stats(raw, rc, tokenizer, tok_type)
        after_s2, _ = stage2_clean_skip_syn_and_stats(
            s1,
            s2_cfg.cleaning,
            mode=s2_cfg.mode,
            drop_empty_cleaned_lines=False,
        )
        b0 = _true_len(after_s2, tokenizer, tok_type)

        _, t_old_b, t_old_a = _hybrid_pipeline_file(after_s2, conf_old, tokenizer, tok_type)
        _, t_fast_b, t_fast_a = _hybrid_pipeline_file(after_s2, conf_fast, tokenizer, tok_type)

        unit = SourceUnit(sid, after_s2, TOKENIZER_KEY, metadata={"eval": "rewrite_200k", "frozen_index": i})
        rw = run_scaffold_on_units([unit], jsonl_ledger_path=None)[0]
        ledger.extend(rw.telemetry_events)
        rollup.add_run(rw)
        ex0 = rw.run_extras or {}
        rs0 = ex0.get("route_summary_initial") or {}

        t_rw_out = rw.final_snapshot.token_count_true
        totals_old_before += t_old_b
        totals_old_after += t_old_a
        totals_fast_before += t_fast_b
        totals_fast_after += t_fast_a
        totals_rw_in += b0
        totals_rw_out += t_rw_out

        detail_rows.append(
            {
                "source_id": sid,
                "frozen_index": i,
                "after_s2_before_true": b0,
                "old_after_true": t_old_a,
                "old_delta_true": t_old_b - t_old_a,
                "old_effective_total_reduction_pct": f"{_pct(t_old_b - t_old_a, t_old_b):.6f}",
                "fast_after_true": t_fast_a,
                "fast_delta_true": t_fast_b - t_fast_a,
                "fast_effective_total_reduction_pct": f"{_pct(t_fast_b - t_fast_a, t_fast_b):.6f}",
                "rewrite_after_true": t_rw_out,
                "rewrite_delta_true": b0 - t_rw_out,
                "rewrite_effective_total_reduction_pct": f"{_pct(b0 - t_rw_out, b0):.6f}",
                "rewrite_a_saved_true": rw.a_result.saved_tokens_true,
                "rewrite_b_saved_true": rw.b_result.saved_tokens_true,
                "rewrite_a_intro_true": rw.a_result.intro_tokens_true,
                "rewrite_b_intro_true": rw.b_result.intro_tokens_true,
                "rewrite_a_net_true": rw.a_result.net_saved_true,
                "rewrite_b_net_true": rw.b_result.net_saved_true,
                "rewrite_net_true": rw.a_result.net_saved_true + rw.b_result.net_saved_true,
                "route_initial_delete_now": rs0.get("total_route_delete_now", 0),
                "route_initial_retain_for_b": rs0.get("total_route_retain_for_b", 0),
                "route_initial_reference": rs0.get("total_route_retain_as_reference_candidate", 0),
                "route_initial_docstrings": rs0.get("total_docstrings_detected", 0),
                "route_initial_comments": rs0.get("total_comments_detected", 0),
                "clustering_backend_note": ex0.get("b_clustering_backend_note", ""),
                "hdbscan_runtime_available": ex0.get("b_hdbscan_runtime_available", False),
                "hdbscan_actually_used": ex0.get("b_hdbscan_actually_used", False),
            }
        )

        ars = rw.after_route_clean_snapshot
        text_for_a = (ars.text if ars is not None else "") or str(ex0.get("text_after_destructive_clean_for_a") or "")
        ad = (
            diagnose_a_evaluations(text_for_a, TOKENIZER_KEY)
            if text_for_a
            else {
                "parse_ok": False,
                "ast_parse_failed": False,
                "syntax_error_lineno": 0,
                "syntax_error_msg": "",
                "a_candidates_variable": 0,
                "a_candidates_attribute": 0,
                "a_candidates_string_exact_path": 0,
            }
        )
        if ad.get("parse_ok"):
            _merge_top_lists(top_gross_neg, list(ad.get("top_gross_pos_net_neg") or []), key=lambda x: x.get("gross", 0))
            _merge_top_lists(top_long_ids, list(ad.get("top_long_identifiers") or []), key=lambda x: (x.get("tok", 0), x.get("occ", 0)))
            _merge_top_lists(top_high_occ, list(ad.get("top_high_occurrence") or []), key=lambda x: (x.get("occ", 0), len(str(x.get("literal", "")))))
        if text_for_a:
            string_path_corpus["n_files_text_nonempty"] += 1
            for rec in iter_short_name_filtered_records(text_for_a, TOKENIZER_KEY):
                short_name_global[(rec["literal"], rec["field"])] += rec["occ"]
            if ad.get("parse_ok"):
                sp = scan_string_path_literal_stats(text_for_a)
                if sp.get("parse_ok"):
                    string_path_corpus["n_files_ast_scan_ok_for_path_literals"] += 1
                    string_path_corpus["sum_distinct_path_like_literals"] += int(sp.get("n_distinct_path_like", 0))
                    string_path_corpus["sum_occurrences_path_like_literals"] += int(sp.get("total_occurrences_in_file", 0))
                    if int(sp.get("n_distinct_path_like", 0)) > 0:
                        string_path_corpus["n_files_with_any_path_like_literal"] += 1
                agg_d = aggregate_attr_occ_by_depth_caps(text_for_a)
                for kk, vv in agg_d.items():
                    attr_depth_corpus[kk] += int(vv)
        a_diag_rows.append(
            {
                "source_id": sid,
                "frozen_index": i,
                "a_text_nonempty": bool(text_for_a),
                "parse_ok": ad.get("parse_ok", False),
                "ast_parse_failed": ad.get("ast_parse_failed", False),
                "syntax_error_lineno": ad.get("syntax_error_lineno", 0),
                "syntax_error_msg": (str(ad.get("syntax_error_msg", ""))[:200]),
                "a_candidates_total": ad.get("a_candidates_total", 0),
                "a_candidates_variable": ad.get("a_candidates_variable", 0),
                "a_candidates_attribute": ad.get("a_candidates_attribute", 0),
                "a_candidates_string_exact_path": ad.get("a_candidates_string_exact_path", 0),
                "a_candidates_filtered_short_name": ad.get("a_candidates_filtered_short_name", 0),
                "a_candidates_filtered_attr_depth": ad.get("a_candidates_filtered_attr_depth", 0),
                "a_candidates_filtered_string_exact_path": ad.get("a_candidates_filtered_string_exact_path", 0),
                "a_candidates_no_legal_alias": ad.get("a_candidates_no_legal_alias", 0),
                "a_candidates_no_net_true_gain": ad.get("a_candidates_no_net_true_gain", 0),
                "a_candidates_positive_gross_but_negative_net": ad.get("a_candidates_positive_gross_but_negative_net", 0),
                "a_candidates_accepted": ad.get("a_candidates_accepted", 0),
            }
        )
        bd = ex0.get("b_rewrite_diagnostics") or {}
        b_diag_rows.append(
            {
                "source_id": sid,
                "frozen_index": i,
                "b_span_safe_rewrite_hits": int(bd.get("span_hits", 0)),
                "b_span_safe_rewrite_misses_bounds": int(bd.get("span_misses_bounds", 0)),
                "b_span_safe_rewrite_misses_slice_mismatch": int(bd.get("span_misses_slice_mismatch", 0)),
                "b_global_replace_fallback_hits": int(bd.get("global_replace_fallback_clusters", 0)),
            }
        )
        rb = route_breakdown_for_text(sid, after_s2)
        merge_route_breakdown(route_flat_corpus, rb)
        route_per_file_rows.append({"source_id": sid, "frozen_index": i, **dict(rb.get("flat") or {})})

        for ev in rw.telemetry_events:
            pl = ev.payload or {}
            et = ev.event_type
            if et == TelemetryEventKind.B_CLUSTER_REJECTED.value:
                reason = ev.action
                nm = int(pl.get("n_members", 0))
                ch = int(pl.get("total_text_chars", 0))
                bkt = _sz_bucket(nm)
                ib = intro_by_bucket[bkt]
                if reason == "insufficient_members":
                    b_singleton_n += 1
                    b_singleton_chars += ch
                elif reason == "rejected_for_low_quality":
                    b_lq_n += 1
                    b_lq_mem_sum += nm
                    b_lq_char_sum += ch
                elif reason == "rejected_for_no_net_gain":
                    b_no_net_n += 1
                    ib["n_rej_nn"] += 1
                    ib["raw_rej"] += int(pl.get("raw_total_true", 0))
                    ib["intro_rej"] += int(pl.get("intro_tokens_true", 0))
                    ib["net_rej"] += int(pl.get("cluster_net_true", 0))
            elif et == TelemetryEventKind.B_REFERENCE_EMITTED.value:
                nm = int(pl.get("n_members", 0))
                bkt = _sz_bucket(nm)
                ib = intro_by_bucket[bkt]
                ib["n_acc"] += 1
                ib["raw_acc"] += int(pl.get("raw_total_true", 0))
                ib["intro_acc"] += int(pl.get("intro_tokens_true", 0))
                ib["net_acc"] += int(pl.get("net_true", 0))

        if ex["a_ok"] is None and rw.a_result.net_saved_true > 0 and rw.a_result.alias_assignments:
            ex["a_ok"] = {
                "source_id": sid,
                "before": after_s2[:500],
                "after": rw.final_snapshot.text[:500],
                "assignments": rw.a_result.alias_assignments[:5],
                "net": rw.a_result.net_saved_true,
            }
        if ex["a_rej"] is None and rw.a_result.rejected_candidates_by_reason:
            ex["a_rej"] = {
                "source_id": sid,
                "reasons": dict(rw.a_result.rejected_candidates_by_reason),
                "snippet": after_s2[:400],
            }
        if ex["b_ok"] is None and rw.b_result.net_saved_true > 0 and rw.b_result.references_or_templates:
            ex["b_ok"] = {
                "source_id": sid,
                "before_b": rw.after_b_snapshot.text[:500],
                "refs": rw.b_result.references_or_templates[:5],
                "b_net": rw.b_result.net_saved_true,
            }
        if ex["b_rej"] is None and rw.b_result.rejected_clusters_by_reason:
            ex["b_rej"] = {"source_id": sid, "reasons": dict(rw.b_result.rejected_clusters_by_reason)}
        if ex["route"] is None and int(rs0.get("total_route_delete_now", 0) or 0) + int(
            rs0.get("total_route_retain_for_b", 0) or 0
        ) > 0:
            ex["route"] = {"source_id": sid, "route_summary_initial": rs0, "snippet": after_s2[:400]}

        if (i + 1) % 20 == 0:
            print(f"[rewrite_200k] processed {i + 1}/{len(sources)}", flush=True)

    sum_row = rollup.to_summary_row()
    sum_row.update(
        {
            "corpus_old_sum_before_true": totals_old_before,
            "corpus_old_sum_after_true": totals_old_after,
            "corpus_old_sum_delta_true": totals_old_before - totals_old_after,
            "corpus_old_reduction_pct": f"{_pct(totals_old_before - totals_old_after, totals_old_before):.6f}",
            "corpus_fast_sum_before_true": totals_fast_before,
            "corpus_fast_sum_after_true": totals_fast_after,
            "corpus_fast_sum_delta_true": totals_fast_before - totals_fast_after,
            "corpus_fast_reduction_pct": f"{_pct(totals_fast_before - totals_fast_after, totals_fast_before):.6f}",
            "corpus_rewrite_sum_before_true": totals_rw_in,
            "corpus_rewrite_sum_after_true": totals_rw_out,
            "corpus_rewrite_sum_delta_true": totals_rw_in - totals_rw_out,
            "corpus_rewrite_reduction_pct": f"{_pct(totals_rw_in - totals_rw_out, totals_rw_in):.6f}",
            "frozen_manifest_path": str(frozen_dir / "frozen_corpus_manifest.json"),
        }
    )

    with (OUT_DIR / "rewrite_200k_summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(sum_row.keys()))
        w.writeheader()
        w.writerow(sum_row)

    if detail_rows:
        keys = sorted({k for row in detail_rows for k in row})
        with (OUT_DIR / "rewrite_200k_detail.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(detail_rows)

    if a_diag_rows:
        keys_a = sorted({k for row in a_diag_rows for k in row})
        with (OUT_DIR / "rewrite_200k_a_diagnostics.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys_a)
            w.writeheader()
            w.writerows(a_diag_rows)

    if b_diag_rows:
        keys_b = sorted({k for row in b_diag_rows for k in row})
        b_corpus = {
            "source_id": "__corpus__",
            "frozen_index": -1,
            "b_span_safe_rewrite_hits": sum(int(r.get("b_span_safe_rewrite_hits", 0)) for r in b_diag_rows),
            "b_span_safe_rewrite_misses_bounds": sum(int(r.get("b_span_safe_rewrite_misses_bounds", 0)) for r in b_diag_rows),
            "b_span_safe_rewrite_misses_slice_mismatch": sum(
                int(r.get("b_span_safe_rewrite_misses_slice_mismatch", 0)) for r in b_diag_rows
            ),
            "b_global_replace_fallback_hits": sum(int(r.get("b_global_replace_fallback_hits", 0)) for r in b_diag_rows),
        }
        with (OUT_DIR / "rewrite_200k_b_diagnostics.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys_b)
            w.writeheader()
            w.writerows(b_diag_rows + [b_corpus])

    if route_per_file_rows:
        keys_rt = sorted({k for row in route_per_file_rows for k in row} | set(route_flat_corpus.keys()))
        corp_rt: dict[str, Any] = {"source_id": "__corpus__", "frozen_index": -1}
        for k in keys_rt:
            if k in ("source_id", "frozen_index"):
                continue
            corp_rt[k] = route_flat_corpus.get(k, 0)
        for row in route_per_file_rows:
            for k in keys_rt:
                if k not in row and k not in ("source_id", "frozen_index"):
                    row.setdefault(k, 0)
        with (OUT_DIR / "rewrite_200k_route_diagnostics.csv").open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys_rt)
            w.writeheader()
            w.writerows(route_per_file_rows + [corp_rt])

    a_rej_md = ["# A 通道拒绝样例（corpus 级 Top，来自 diagnose_a_evaluations）\n\n## gross>0 且 net<0（Top 50）\n```json\n"]
    a_rej_md.append(json.dumps(top_gross_neg[:50], ensure_ascii=False, indent=2))
    a_rej_md.append("\n```\n\n## 长 identifier 候选（Top 50）\n```json\n")
    a_rej_md.append(json.dumps(top_long_ids[:50], ensure_ascii=False, indent=2))
    a_rej_md.append("\n```\n\n## 高频 identifier 候选（Top 50）\n```json\n")
    a_rej_md.append(json.dumps(top_high_occ[:50], ensure_ascii=False, indent=2))
    a_rej_md.append("\n```\n")
    (OUT_DIR / "rewrite_200k_a_reject_examples.md").write_text("".join(a_rej_md), encoding="utf-8")

    b_sum = {
        "b_span_safe_rewrite_hits": sum(int(r.get("b_span_safe_rewrite_hits", 0)) for r in b_diag_rows),
        "b_span_safe_rewrite_misses_bounds": sum(int(r.get("b_span_safe_rewrite_misses_bounds", 0)) for r in b_diag_rows),
        "b_span_safe_rewrite_misses_slice_mismatch": sum(
            int(r.get("b_span_safe_rewrite_misses_slice_mismatch", 0)) for r in b_diag_rows
        ),
        "b_global_replace_fallback_hits": sum(int(r.get("b_global_replace_fallback_hits", 0)) for r in b_diag_rows),
    } if b_diag_rows else {
        "b_span_safe_rewrite_hits": 0,
        "b_span_safe_rewrite_misses_bounds": 0,
        "b_span_safe_rewrite_misses_slice_mismatch": 0,
        "b_global_replace_fallback_hits": 0,
    }
    b_ex_md = (
        "# B span / fallback 诊断汇总\n\n"
        f"```json\n{json.dumps(b_sum, ensure_ascii=False, indent=2)}\n```\n\n"
        "详见 `rewrite_200k_b_diagnostics.csv` 末行 `__corpus__`。\n"
    )
    (OUT_DIR / "rewrite_200k_b_examples.md").write_text(b_ex_md, encoding="utf-8")

    top_retain = sorted(
        detail_rows,
        key=lambda r: int(r.get("route_initial_retain_for_b", 0) or 0),
        reverse=True,
    )[:12]
    rt_md = ["# Route 高留存样例（按 route_initial_retain_for_b 排序）\n"]
    for r in top_retain:
        rt_md.append(f"## {r.get('source_id')} (retain_for_b={r.get('route_initial_retain_for_b')})\n")
        rt_md.append(f"- delete_now: {r.get('route_initial_delete_now')}, reference: {r.get('route_initial_reference')}\n")
        rt_md.append(f"- docstrings: {r.get('route_initial_docstrings')}, comments: {r.get('route_initial_comments')}\n\n")
    (OUT_DIR / "rewrite_200k_route_examples.md").write_text("".join(rt_md), encoding="utf-8")

    _write_accounting_gap_md(OUT_DIR / "rewrite_200k_accounting_gap.md")

    parse_ok_true = sum(1 for r in a_diag_rows if r.get("parse_ok") in (True, "True"))
    parse_ok_false = len(a_diag_rows) - parse_ok_true if a_diag_rows else 0
    a_sum_keys = (
        "a_candidates_total",
        "a_candidates_variable",
        "a_candidates_attribute",
        "a_candidates_string_exact_path",
        "a_candidates_filtered_short_name",
        "a_candidates_filtered_attr_depth",
        "a_candidates_filtered_string_exact_path",
        "a_candidates_no_legal_alias",
        "a_candidates_no_net_true_gain",
        "a_candidates_positive_gross_but_negative_net",
        "a_candidates_accepted",
    )
    a_corpus_totals_d: dict[str, int] = {k: sum(int(r.get(k) or 0) for r in a_diag_rows) for k in a_sum_keys}
    b_span_corpus_dict = {
        "b_span_safe_rewrite_hits": sum(int(r.get("b_span_safe_rewrite_hits", 0)) for r in b_diag_rows),
        "b_span_safe_rewrite_misses_bounds": sum(int(r.get("b_span_safe_rewrite_misses_bounds", 0)) for r in b_diag_rows),
        "b_span_safe_rewrite_misses_slice_mismatch": sum(
            int(r.get("b_span_safe_rewrite_misses_slice_mismatch", 0)) for r in b_diag_rows
        ),
        "b_global_replace_fallback_hits": sum(int(r.get("b_global_replace_fallback_hits", 0)) for r in b_diag_rows),
    } if b_diag_rows else {
        "b_span_safe_rewrite_hits": 0,
        "b_span_safe_rewrite_misses_bounds": 0,
        "b_span_safe_rewrite_misses_slice_mismatch": 0,
        "b_global_replace_fallback_hits": 0,
    }
    keys_ib = ("n_acc", "n_rej_nn", "raw_acc", "intro_acc", "net_acc", "raw_rej", "intro_rej", "net_rej")
    intro_final: dict[str, dict[str, int]] = {}
    for b in ["2", "3", "4", "5+"]:
        d = intro_by_bucket[b]
        intro_final[b] = {k: int(d[k]) for k in keys_ib}

    _write_failure_artifacts(
        out_dir=OUT_DIR,
        n_sources=len(sources),
        a_diag_rows=a_diag_rows,
        parse_ok_true=parse_ok_true,
        parse_ok_false=parse_ok_false,
        short_name_counter=short_name_global,
        attr_depth_corpus=dict(attr_depth_corpus),
        string_path_corpus=string_path_corpus,
        b_singleton_n=b_singleton_n,
        b_singleton_chars=b_singleton_chars,
        b_lq_n=b_lq_n,
        b_lq_mem_sum=b_lq_mem_sum,
        b_lq_char_sum=b_lq_char_sum,
        b_no_net_n=b_no_net_n,
        intro_by_bucket=intro_final,
        b_span_corpus=b_span_corpus_dict,
        route_flat=dict(route_flat_corpus),
        sum_row=sum_row,
        totals_rw_in=totals_rw_in,
        totals_rw_out=totals_rw_out,
        totals_old_before=totals_old_before,
        totals_old_after=totals_old_after,
        totals_fast_before=totals_fast_before,
        totals_fast_after=totals_fast_after,
        a_corpus_totals=a_corpus_totals_d,
    )

    examples_md = ["# rewrite_200k examples (ledger-backed snapshots)\n"]
    for title, key in [
        ("A success", "a_ok"),
        ("A reject", "a_rej"),
        ("B success", "b_ok"),
        ("B reject", "b_rej"),
        ("Route", "route"),
    ]:
        examples_md.append(f"## {title}\n")
        examples_md.append("```json\n")
        examples_md.append(json.dumps(ex.get(key), ensure_ascii=False, indent=2) or "null")
        examples_md.append("\n```\n")
    (OUT_DIR / "rewrite_200k_examples.md").write_text("".join(examples_md), encoding="utf-8")

    old_d = totals_old_before - totals_old_after
    fast_d = totals_fast_before - totals_fast_after
    rw_d = totals_rw_in - totals_rw_out
    best = max(
        [("old_baseline", old_d), ("fast_try", fast_d), ("rewrite", rw_d)],
        key=lambda x: x[1],
    )
    report = f"""# rewrite_200k report

## Corpus (frozen)

- **manifest**: `{frozen_dir / "frozen_corpus_manifest.json"}`
- **sources**: {len(sources)} files, tokenizer `{TOKENIZER_KEY}`

## Aggregate token deltas (sum of per-file true-token counts at Stage2→Stage3 input)

| Variant | Sum before | Sum after | Delta | Reduction % |
|---------|------------|-----------|-------|-------------|
| old hybrid_ab | {totals_old_before} | {totals_old_after} | {old_d} | {_pct(old_d, totals_old_before):.4f}% |
| fast_try-style hybrid_ab | {totals_fast_before} | {totals_fast_after} | {fast_d} | {_pct(fast_d, totals_fast_before):.4f}% |
| rewrite Stage3 AB | {totals_rw_in} | {totals_rw_out} | {rw_d} | {_pct(rw_d, totals_rw_in):.4f}% |

**Largest corpus-level delta (this run): `{best[0]}`** (Δ={best[1]} tokens).

## Rewrite channel totals

- **total_a_saved_true** (sum of per-file body savings): {sum_row.get("total_a_saved_true")}
- **total_b_saved_true**: {sum_row.get("total_b_saved_true")}
- **total_a_intro_true**: {sum_row.get("total_a_intro_true")}
- **total_b_intro_true**: {sum_row.get("total_b_intro_true")}
- **total_net_true** (A net + B net): {sum_row.get("total_net_true")}
- **strict single-token alias picks** (assignments): {sum_row.get("alias_strict_single_selections")}
- **alias tier histogram** (JSON): `{sum_row.get("alias_tier_counts_json")}`

## Route (initial pass, summed over files)

- **delete_now**: {sum_row.get("route_initial__total_route_delete_now", 0)}
- **retain_for_b**: {sum_row.get("route_initial__total_route_retain_for_b", 0)}
- **retain_as_reference_candidate**: {sum_row.get("route_initial__total_route_retain_as_reference_candidate", 0)}
- **docstrings_detected**: {sum_row.get("route_initial__total_docstrings_detected", 0)}
- **comments_detected**: {sum_row.get("route_initial__total_comments_detected", 0)}

## Answers (this frozen run)

1. **Strict single-token pool**: aliases with `measure_true_token_len==1` are tier-1 and ordered before multi-token candidates (`rewrite_stage3ab/channels/a_channel/alias_pool.py`).
2. **A vs previous**: tier metadata + `alias_strict_single_selections` / `alias_tier_counts_json` in summary quantify single-token usage.
3. **B near-duplicate**: noise indices are grouped by exact / norm-WS / word-Jaccard / char-Jaccard before reference evaluation; span-safe rewrite uses `char_start`/`char_end` slices.
4. **Span safety**: `ReferenceCodecV1.rewrite_text` replaces only verified `[start:end)` slices matching cluster literals when spans exist.
5. **Route retention**: see route columns in `rewrite_200k_summary.csv` / table above.
6. **Gap to default pipeline**: rewrite still bypasses full `v2_eval` / marker accounting; integrate behind same entrypoint and align guardrails with `hybrid_ab` for production default.

Artifacts: `rewrite_200k_summary.csv`, `rewrite_200k_detail.csv`, `rewrite_200k_examples.md`, `rewrite_200k_ledger.jsonl`.
"""
    (OUT_DIR / "rewrite_200k_report.md").write_text(report, encoding="utf-8")
    print("[rewrite_200k] wrote", OUT_DIR, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
