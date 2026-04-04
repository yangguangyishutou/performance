#!/usr/bin/env python3
"""
Small-scale rewrite Stage3 AB eval vs legacy ``hybrid_ab`` (true-token primary).

Writes under ``entropy_tokenizer_v2/results_rewrite_full/`` (does not touch main ``results/``).
"""

from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS  # noqa: E402
from rewrite_stage3ab.contracts.data_models import SourceUnit  # noqa: E402
from rewrite_stage3ab.orchestrator.pipeline import run_scaffold_on_units  # noqa: E402
from rewrite_stage3ab.validation.smoke_runner import CASE_A, CASE_B, CASE_ROUTE  # noqa: E402
from repo_miner import _load_tokenizer  # noqa: E402
from stage3.backends.hybrid_ab_backend import HybridABConfig, encode_stage3_hybrid_ab  # noqa: E402
from marker_count import encode as mc_encode  # noqa: E402


OUT_DIR = ROOT / "results_rewrite_full"
TOKENIZER_KEY = "gpt4"


def _true_len(text: str, tokenizer_key: str) -> int:
    cfg = EVAL_TOKENIZERS[tokenizer_key]
    tok, typ = _load_tokenizer(tokenizer_key, cfg)
    return len(mc_encode(tok, typ, text))


def _hybrid_ab_on_text(text: str, tokenizer_key: str) -> tuple[str, int, int, dict]:
    cfg = EVAL_TOKENIZERS[tokenizer_key]
    tok, typ = _load_tokenizer(tokenizer_key, cfg)
    conf = HybridABConfig(mode="hybrid", a_min_occ=2, b_min_cluster_size=2)
    before = _true_len(text, tokenizer_key)
    res = encode_stage3_hybrid_ab(text, tokenizer=tok, tok_type=typ, cfg=conf)
    after = _true_len(res.encoded_text, tokenizer_key)
    return res.encoded_text, before, after, dict(res.meta or {})


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snippets = [
        ("hand_a", CASE_A),
        ("hand_b", CASE_B),
        ("hand_route", CASE_ROUTE),
    ]
    rows_detail = []
    rows_summary = []

    for sid, src in snippets:
        enc, b_old, a_old, meta_old = _hybrid_ab_on_text(src, TOKENIZER_KEY)
        unit = SourceUnit(sid, src, TOKENIZER_KEY, metadata={"eval": "rewrite_full"})
        rw = run_scaffold_on_units([unit])[0]
        b_rw = rw.input_snapshot.token_count_true
        a_rw = rw.final_snapshot.token_count_true
        rows_detail.append(
            {
                "source_id": sid,
                "old_hybrid_before_true": b_old,
                "old_hybrid_after_true": a_old,
                "old_delta_true": b_old - a_old,
                "rewrite_before_true": b_rw,
                "rewrite_after_true": a_rw,
                "rewrite_delta_true": b_rw - a_rw,
                "rewrite_a_net": rw.a_result.net_saved_true,
                "rewrite_b_net": rw.b_result.net_saved_true,
                "hybrid_meta_keys": ",".join(sorted(meta_old.keys()))[:200],
            }
        )

    # Corpus slice: optional first N files from HF disk fallback (same pattern as starcoder eval)
    n_corpus = int(os.environ.get("ET_REWRITE_EVAL_CORPUS_N", "0"))
    if n_corpus > 0:
        try:
            from datasets import load_from_disk
            from config import HF_DISK_DATASET_FALLBACK

            ds = load_from_disk(str(HF_DISK_DATASET_FALLBACK))
            contents = ds["content"]
            for i in range(min(n_corpus, len(contents))):
                sid = f"corpus:{i}"
                src = contents[i]
                if not isinstance(src, str):
                    continue
                enc, b_old, a_old, meta_old = _hybrid_ab_on_text(src, TOKENIZER_KEY)
                unit = SourceUnit(sid, src[:8000], TOKENIZER_KEY, metadata={"eval": "rewrite_full_corpus"})
                rw = run_scaffold_on_units([unit])[0]
                rows_detail.append(
                    {
                        "source_id": sid,
                        "old_hybrid_before_true": b_old,
                        "old_hybrid_after_true": a_old,
                        "old_delta_true": b_old - a_old,
                        "rewrite_before_true": rw.input_snapshot.token_count_true,
                        "rewrite_after_true": rw.final_snapshot.token_count_true,
                        "rewrite_delta_true": rw.input_snapshot.token_count_true - rw.final_snapshot.token_count_true,
                        "rewrite_a_net": rw.a_result.net_saved_true,
                        "rewrite_b_net": rw.b_result.net_saved_true,
                        "hybrid_meta_keys": ",".join(sorted(meta_old.keys()))[:200],
                    }
                )
        except Exception as exc:
            rows_detail.append(
                {
                    "source_id": "corpus:error",
                    "error": str(exc),
                }
            )

    all_units = [SourceUnit(sid, src, TOKENIZER_KEY) for sid, src in snippets]
    results = run_scaffold_on_units(all_units, jsonl_ledger_path=OUT_DIR / "rewrite_full_ledger.jsonl")

    for r in results:
        rows_summary.append(
            {
                "source_id": r.source_id,
                "in_true": r.input_snapshot.token_count_true,
                "out_true": r.final_snapshot.token_count_true,
                "a_net": r.a_result.net_saved_true,
                "b_net": r.b_result.net_saved_true,
                "n_events": len(r.telemetry_events),
            }
        )

    sum_path = OUT_DIR / "rewrite_full_summary.csv"
    det_path = OUT_DIR / "rewrite_full_detail.csv"
    if rows_summary:
        with sum_path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows_summary[0].keys()))
            w.writeheader()
            w.writerows(rows_summary)
    if rows_detail:
        with det_path.open("w", newline="", encoding="utf-8") as f:
            keys = sorted({k for row in rows_detail for k in row})
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows_detail)

    examples = []
    for r in results:
        examples.append(
            {
                "source_id": r.source_id,
                "before": r.input_snapshot.text[:400],
                "after": r.final_snapshot.text[:400],
            }
        )
    (OUT_DIR / "rewrite_full_examples.md").write_text(
        "# Rewrite full eval snapshots\n\n" + "\n".join(json.dumps(x, ensure_ascii=False, indent=2) for x in examples),
        encoding="utf-8",
    )
    print("wrote", sum_path, det_path, OUT_DIR / "rewrite_full_ledger.jsonl")


if __name__ == "__main__":
    main()
