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
