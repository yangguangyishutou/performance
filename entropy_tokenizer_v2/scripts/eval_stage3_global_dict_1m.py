"""Evaluate Stage3 hybrid_ab with and without a global shared dictionary (1M corpus)."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS, resolve_hybrid_ab_settings  # noqa: E402
from eval.v2_eval import evaluate  # noqa: E402
from repo_miner import mine_from_sources  # noqa: E402


def _load_sources(jsonl_path: Path) -> list[str]:
    out: list[str] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = obj.get("text", "")
            if isinstance(text, str) and text:
                out.append(text)
    return out


def _row(name: str, res) -> dict:
    return {
        "name": name,
        "effective_total_reduction_pct": float(res.effective_total_reduction_pct),
        "sequence_reduction_pct": float(res.sequence_reduction_pct),
        "replacement_pct": float(res.replacement_pct),
        "stage3_vocab_intro_tokens": int(res.stage3_vocab_intro_tokens),
        "stage3_ab_a_effective_net_saving": int(res.stage3_ab_a_effective_net_saving),
        "stage3_ab_b_effective_net_saving": int(res.stage3_ab_b_effective_net_saving),
        "stage3_ab_global_dict_enabled": bool(res.stage3_ab_global_dict_enabled),
        "stage3_ab_global_dict_size_a": int(res.stage3_ab_global_dict_size_a),
        "stage3_ab_global_dict_size_b": int(res.stage3_ab_global_dict_size_b),
        "stage3_ab_a_global_used_entries": int(res.stage3_ab_a_global_used_entries),
        "stage3_ab_b_global_used_codes": int(res.stage3_ab_b_global_used_codes),
        "stage3_ab_global_sequence_saved": int(res.stage3_ab_global_sequence_saved),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=str,
        default=str(ROOT / "cache" / "stage1_starcoder_1m_corpus.jsonl"),
    )
    parser.add_argument(
        "--global-dict",
        type=str,
        default=str(ROOT / "cache" / "stage3_global_dictionary.json"),
    )
    parser.add_argument("--tokenizer", type=str, default="gpt4")
    parser.add_argument(
        "--out-json",
        type=str,
        default=str(ROOT / "results" / "stage3_global_dict_1m_eval.json"),
    )
    parser.add_argument(
        "--out-csv",
        type=str,
        default=str(ROOT / "results" / "stage3_global_dict_1m_eval.csv"),
    )
    args = parser.parse_args()

    tok_key = str(args.tokenizer).strip()
    tok_cfg = EVAL_TOKENIZERS.get(tok_key)
    if tok_cfg is None:
        raise SystemExit(f"unknown tokenizer: {tok_key}")

    corpus = Path(args.corpus)
    if not corpus.exists():
        raise SystemExit(f"missing corpus: {corpus}")
    sources = _load_sources(corpus)
    if not sources:
        raise SystemExit("empty sources")

    base_repo = mine_from_sources(
        sources=sources,
        tokenizer_key=tok_key,
        tokenizer_cfg=tok_cfg,
        cache_name=f"stage3_global_dict_eval_mine_once_{tok_key}",
        cache=True,
        verbose=True,
        stage3_backend="hybrid_ab",
    )

    rows: list[dict] = []
    detail: dict[str, dict] = {}
    for name, use_global in (
        ("hybrid_local_only", False),
        ("hybrid_global_dict", True),
    ):
        rc = copy.deepcopy(base_repo)
        rc.stage3_backend = "hybrid_ab"
        ab = resolve_hybrid_ab_settings(tok_key)
        ab["mode"] = "hybrid"
        ab["enable_b"] = True
        ab["stage3_ab_mode"] = "hybrid"
        ab["stage3_ab_b_mode"] = "lexical_free_text_baseline"
        ab["global_dict_enabled"] = bool(use_global)
        ab["global_dict_path"] = str(args.global_dict)
        ab["global_dict_charge_vocab"] = False
        rc.stage3_ab_summary = ab
        res = evaluate(sources, rc, tok_key, tok_cfg, stage2_profile=None, stage2_mode=None)
        row = _row(name, res)
        rows.append(row)
        detail[name] = {"metrics": row, "stage3_ab_summary": ab}
        print(
            f"[{name}] eff={row['effective_total_reduction_pct']:.6f} "
            f"seq={row['sequence_reduction_pct']:.6f} "
            f"global_saved={row['stage3_ab_global_sequence_saved']}"
        )

    local = next(r for r in rows if r["name"] == "hybrid_local_only")
    gbl = next(r for r in rows if r["name"] == "hybrid_global_dict")
    payload = {
        "corpus": str(corpus),
        "tokenizer_key": tok_key,
        "global_dict_path": str(args.global_dict),
        "rows": rows,
        "delta_global_vs_local": {
            "effective_total_reduction_pct": gbl["effective_total_reduction_pct"]
            - local["effective_total_reduction_pct"],
            "sequence_reduction_pct": gbl["sequence_reduction_pct"]
            - local["sequence_reduction_pct"],
            "replacement_pct": gbl["replacement_pct"] - local["replacement_pct"],
            "stage3_ab_global_sequence_saved": gbl["stage3_ab_global_sequence_saved"]
            - local["stage3_ab_global_sequence_saved"],
        },
        "details": detail,
    }

    out_json = Path(args.out_json)
    out_csv = Path(args.out_csv)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with out_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"[done] wrote {out_json}")
    print(f"[done] wrote {out_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
