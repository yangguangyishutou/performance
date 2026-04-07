"""Evaluate Stage3-B rule combinations on cached StarCoder 1M corpus (gpt4 tokenizer)."""

from __future__ import annotations

import copy
import csv
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS, resolve_hybrid_ab_settings  # noqa: E402
from eval.v2_eval import evaluate  # noqa: E402
from repo_miner import mine_from_sources  # noqa: E402

CORPUS_JSONL = ROOT / "cache" / "stage1_starcoder_1m_corpus.jsonl"
OUT_JSON = ROOT / "results" / "stage3_hybrid_ab_1m_b_rule_combo_eval.json"
OUT_CSV = ROOT / "results" / "stage3_hybrid_ab_1m_b_rule_combo_eval.csv"


@contextmanager
def _temp_env(env: dict[str, str]) -> Iterator[None]:
    old: dict[str, str | None] = {}
    try:
        for k, v in env.items():
            old[k] = os.environ.get(k)
            os.environ[k] = str(v)
        yield
    finally:
        for k, prev in old.items():
            if prev is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = prev


def _load_sources() -> list[str]:
    if not CORPUS_JSONL.exists():
        raise FileNotFoundError(f"missing corpus: {CORPUS_JSONL}")
    out: list[str] = []
    with CORPUS_JSONL.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            text = obj.get("text", "")
            if isinstance(text, str) and text:
                out.append(text)
    if not out:
        raise RuntimeError("empty corpus sources")
    return out


def _mk_ab_summary(overrides: dict[str, str]) -> dict:
    base = {
        "ET_STAGE3_AB_MODE": "hybrid",
        "ET_STAGE3_AB_ENABLE_B": "1",
        "ET_STAGE3_AB_A_MIN_OCC": "2",
        "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
        "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
    }
    base.update(overrides)
    with _temp_env(base):
        summary = resolve_hybrid_ab_settings("gpt4")
    summary["stage3_ab_mode"] = summary.get("mode", "exact_only")
    summary["stage3_ab_similarity_kind"] = summary.get("b_similarity_kind", "lexical_bow_cosine")
    summary["stage3_ab_b_mode"] = (
        "lexical_free_text_mixed"
        if summary.get("mode") == "hybrid"
        and str(summary.get("b_similarity_kind", "")).strip().lower() in {"hybrid_lexical_char", "mixed"}
        else "lexical_free_text_baseline"
        if summary.get("mode") == "hybrid"
        else "disabled"
    )
    return summary


def _mk_exact_summary() -> dict:
    return _mk_ab_summary({"ET_STAGE3_AB_MODE": "exact_only", "ET_STAGE3_AB_ENABLE_B": "0"})


def _row(name: str, res) -> dict:
    return {
        "name": name,
        "stage3_ab_mode": res.stage3_ab_mode,
        "sequence_reduction_pct": float(res.sequence_reduction_pct),
        "effective_total_reduction_pct": float(res.effective_total_reduction_pct),
        "replacement_pct": float(res.replacement_pct),
        "stage3_vocab_intro_tokens": int(res.stage3_vocab_intro_tokens),
        "stage3_ab_a_effective_net_saving": int(res.stage3_ab_a_effective_net_saving),
        "stage3_ab_b_candidates": int(res.stage3_ab_b_candidates),
        "stage3_ab_b_used_clusters": int(res.stage3_ab_b_used_clusters),
        "stage3_ab_b_sequence_saved": int(res.stage3_ab_b_sequence_saved),
        "stage3_ab_b_intro_tokens": int(res.stage3_ab_b_intro_tokens),
        "stage3_ab_b_effective_net_saving": int(res.stage3_ab_b_effective_net_saving),
        "stage3_ab_b_intro_not_worth_count": int(res.stage3_ab_b_intro_not_worth_count),
        "stage3_ab_b_avg_similarity": float(res.stage3_ab_b_avg_similarity),
        "n_files": int(res.n_files),
        "baseline_tokens": int(res.baseline_tokens),
    }


def main() -> int:
    sources = _load_sources()
    tok_key = "gpt4"
    tok_cfg = EVAL_TOKENIZERS[tok_key]

    # Mine once; Stage3 AB behavior is runtime-driven by stage3_ab_summary.
    base_repo = mine_from_sources(
        sources=sources,
        tokenizer_key=tok_key,
        tokenizer_cfg=tok_cfg,
        cache_name="starcoder_1m_b_rule_combo_mine_once",
        cache=True,
        verbose=True,
        stage3_backend="hybrid_ab",
    )

    scenarios: list[tuple[str, dict]] = [
        ("exact_occ2_mrt2", _mk_exact_summary()),
        ("b_shared_terms_default", _mk_ab_summary({})),
        (
            "b_compact_code",
            _mk_ab_summary(
                {
                    "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                    "ET_STAGE3_AB_B_CODE_PREFIX": "b",
                }
            ),
        ),
        (
            "b_net_greedy",
            _mk_ab_summary({"ET_STAGE3_AB_B_MEMBER_SELECT_MODE": "net_greedy"}),
        ),
        (
            "b_compact_plus_greedy",
            _mk_ab_summary(
                {
                    "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                    "ET_STAGE3_AB_B_CODE_PREFIX": "b",
                    "ET_STAGE3_AB_B_MEMBER_SELECT_MODE": "net_greedy",
                }
            ),
        ),
        (
            "b_compact_plus_greedy_plus_norm",
            _mk_ab_summary(
                {
                    "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                    "ET_STAGE3_AB_B_CODE_PREFIX": "b",
                    "ET_STAGE3_AB_B_MEMBER_SELECT_MODE": "net_greedy",
                    "ET_STAGE3_AB_B_SIMILARITY_NORM": "light",
                }
            ),
        ),
        (
            "b_compact_plus_drop_negative",
            _mk_ab_summary(
                {
                    "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                    "ET_STAGE3_AB_B_CODE_PREFIX": "b",
                    "ET_STAGE3_AB_B_MEMBER_SELECT_MODE": "drop_negative",
                }
            ),
        ),
        (
            "b_repr_def_compact_greedy",
            _mk_ab_summary(
                {
                    "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                    "ET_STAGE3_AB_B_CODE_PREFIX": "b",
                    "ET_STAGE3_AB_B_MEMBER_SELECT_MODE": "net_greedy",
                    "ET_STAGE3_AB_B_DEFINITION_MODE": "representative",
                }
            ),
        ),
        (
            "b_mixed_sim_compact_greedy",
            _mk_ab_summary(
                {
                    "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                    "ET_STAGE3_AB_B_CODE_PREFIX": "b",
                    "ET_STAGE3_AB_B_MEMBER_SELECT_MODE": "net_greedy",
                    "ET_STAGE3_AB_B_SIMILARITY_KIND": "mixed",
                    "ET_STAGE3_AB_B_LEXICAL_WEIGHT": "0.65",
                    "ET_STAGE3_AB_B_CHAR_WEIGHT": "0.35",
                }
            ),
        ),
    ]

    rows: list[dict] = []
    summary_by_name: dict[str, dict] = {}
    for name, ab_summary in scenarios:
        cfg = copy.deepcopy(base_repo)
        cfg.stage3_backend = "hybrid_ab"
        cfg.stage3_ab_summary = dict(ab_summary)
        res = evaluate(sources, cfg, tok_key, tok_cfg, stage2_profile=None, stage2_mode=None)
        row = _row(name, res)
        rows.append(row)
        summary_by_name[name] = {
            "stage3_ab_summary": ab_summary,
            "metrics": row,
        }
        print(
            f"[{name}] eff={row['effective_total_reduction_pct']:.6f} "
            f"seq={row['sequence_reduction_pct']:.6f} "
            f"B_net={row['stage3_ab_b_effective_net_saving']}"
        )

    exact = next(r for r in rows if r["name"] == "exact_occ2_mrt2")
    hybrid_rows = [r for r in rows if r["name"] != "exact_occ2_mrt2"]
    best = max(hybrid_rows, key=lambda r: r["effective_total_reduction_pct"])
    deltas = {
        "effective_total_reduction_pct": best["effective_total_reduction_pct"] - exact["effective_total_reduction_pct"],
        "sequence_reduction_pct": best["sequence_reduction_pct"] - exact["sequence_reduction_pct"],
        "replacement_pct": best["replacement_pct"] - exact["replacement_pct"],
        "stage3_ab_b_effective_net_saving": best["stage3_ab_b_effective_net_saving"] - exact["stage3_ab_b_effective_net_saving"],
    }

    payload = {
        "corpus": str(CORPUS_JSONL),
        "tokenizer_key": tok_key,
        "rows": rows,
        "best_hybrid_by_effective_total": best,
        "exact_baseline": exact,
        "delta_best_hybrid_vs_exact": deltas,
        "scenario_details": summary_by_name,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"[done] wrote {OUT_JSON}")
    print(f"[done] wrote {OUT_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
