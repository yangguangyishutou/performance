"""Search Stage3 hybrid_ab settings for Qwen and validate on HumanEval prompt size."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from statistics import mean
from typing import Iterator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS, resolve_hybrid_ab_settings  # noqa: E402
from eval.humaneval_utils import (  # noqa: E402
    HumanEvalTask,
    load_humaneval_tasks,
    load_support_snippets,
    prepare_task_record,
    retrieve_support_snippets,
)
from eval.v2_eval import evaluate  # noqa: E402
from repo_miner import mine_from_sources, _load_tokenizer  # noqa: E402
from scripts.build_stage3_global_dict import build_global_dictionary  # noqa: E402

TOKENIZER_KEY = "qwen25-coder-15b"


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


def _load_sources(jsonl_path: Path) -> list[str]:
    out: list[str] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            text = obj.get("text", "")
            if isinstance(text, str) and text:
                out.append(text)
    if not out:
        raise RuntimeError(f"empty corpus: {jsonl_path}")
    return out


def _mk_ab_summary(overrides: dict[str, str]) -> dict:
    with _temp_env(overrides):
        summary = resolve_hybrid_ab_settings(TOKENIZER_KEY)
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


def _mk_global_dict(
    *,
    corpus_path: Path,
    preset_name: str,
    output_path: Path,
) -> Path:
    sources = _load_sources(corpus_path)
    tok_cfg = EVAL_TOKENIZERS[TOKENIZER_KEY]
    tok, tt = _load_tokenizer(TOKENIZER_KEY, tok_cfg)
    preset_payload = {
        "qwen_small": {
            "a_min_occ": 8,
            "b_min_occ": 10**9,
            "a_max_entries": 128,
            "b_max_entries": 0,
            "a_prefix": "q",
            "b_prefix": "qb",
        },
        "qwen_medium": {
            "a_min_occ": 6,
            "b_min_occ": 10**9,
            "a_max_entries": 256,
            "b_max_entries": 0,
            "a_prefix": "q",
            "b_prefix": "qb",
        },
    }[preset_name]
    payload = build_global_dictionary(
        sources=sources,
        tokenizer=tok,
        tok_type=tt,
        tokenizer_key=TOKENIZER_KEY,
        a_min_occ=int(preset_payload["a_min_occ"]),
        b_min_occ=int(preset_payload["b_min_occ"]),
        a_max_entries=int(preset_payload["a_max_entries"]),
        b_max_entries=int(preset_payload["b_max_entries"]),
        a_prefix=str(preset_payload["a_prefix"]),
        b_prefix=str(preset_payload["b_prefix"]),
    )
    payload["summary"]["preset"] = preset_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def _corpus_row(name: str, summary: dict, res) -> dict:
    return {
        "name": name,
        "mode": res.stage3_ab_mode,
        "effective_total_reduction_pct": float(res.effective_total_reduction_pct),
        "sequence_reduction_pct": float(res.sequence_reduction_pct),
        "replacement_pct": float(res.replacement_pct),
        "stage3_vocab_intro_tokens": int(res.stage3_vocab_intro_tokens),
        "stage3_ab_a_effective_net_saving": int(res.stage3_ab_a_effective_net_saving),
        "stage3_ab_b_effective_net_saving": int(res.stage3_ab_b_effective_net_saving),
        "stage3_ab_b_used_clusters": int(res.stage3_ab_b_used_clusters),
        "stage3_ab_global_dict_enabled": bool(res.stage3_ab_global_dict_enabled),
        "stage3_ab_global_dict_size_a": int(res.stage3_ab_global_dict_size_a),
        "stage3_ab_global_dict_size_b": int(res.stage3_ab_global_dict_size_b),
        "stage3_ab_a_global_used_entries": int(res.stage3_ab_a_global_used_entries),
        "stage3_ab_b_global_used_codes": int(res.stage3_ab_b_global_used_codes),
        "stage3_ab_global_sequence_saved": int(res.stage3_ab_global_sequence_saved),
        "a_min_occ": int(summary.get("a_min_occ", 0) or 0),
        "min_raw_token_len": int(summary.get("min_raw_token_len", 0) or 0),
        "max_alias_token_len": int(summary.get("max_alias_token_len", 0) or 0),
        "a_cost_mode": str(summary.get("a_cost_mode", "")),
        "b_similarity_norm": str(summary.get("b_similarity_norm", "")),
        "b_code_style": str(summary.get("b_code_style", "")),
        "b_definition_mode": str(summary.get("b_definition_mode", "")),
    }


def _prompt_eval_row(name: str, prompt_rows: list[dict]) -> dict:
    raw_vals = [float(r["raw_context_tokens"]) for r in prompt_rows]
    comp_vals = [float(r["compressed_effective_tokens"]) for r in prompt_rows]
    delta_vals = [float(r["delta_tokens"]) for r in prompt_rows]
    codebook_vals = [float(r["codebook_tokens"]) for r in prompt_rows]
    return {
        "name": name,
        "n_tasks": len(prompt_rows),
        "avg_raw_context_tokens": mean(raw_vals) if raw_vals else 0.0,
        "avg_compressed_effective_tokens": mean(comp_vals) if comp_vals else 0.0,
        "avg_delta_tokens": mean(delta_vals) if delta_vals else 0.0,
        "avg_codebook_tokens": mean(codebook_vals) if codebook_vals else 0.0,
        "n_tasks_improved": sum(1 for x in delta_vals if x < 0),
        "n_tasks_worse": sum(1 for x in delta_vals if x > 0),
        "n_tasks_equal": sum(1 for x in delta_vals if x == 0),
    }


def _prompt_eval(
    *,
    name: str,
    ab_summary: dict,
    tasks: list[HumanEvalTask],
    support,
    prompt_style: str,
    stage2_profile: str,
    stage2_mode: str,
) -> tuple[dict, list[dict]]:
    prompt_rows: list[dict] = []
    for task in tasks:
        hits = retrieve_support_snippets(task, support, top_k=4)
        with _temp_env(
            {
                "ET_STAGE3_AB_MODE": str(ab_summary.get("mode", "exact_only")),
                "ET_STAGE3_AB_ENABLE_B": "1" if ab_summary.get("enable_b") else "0",
                "ET_STAGE3_AB_A_MIN_OCC": str(ab_summary.get("a_min_occ", 2)),
                "ET_STAGE3_AB_A_MIN_NET_GAIN": str(ab_summary.get("a_min_net_gain", 1)),
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": str(ab_summary.get("min_raw_token_len", 1)),
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": str(ab_summary.get("max_alias_token_len", 32)),
                "ET_STAGE3_AB_A_COST_MODE": str(ab_summary.get("a_cost_mode", "local")),
                "ET_STAGE3_AB_B_SIMILARITY_NORM": str(ab_summary.get("b_similarity_norm", "none")),
                "ET_STAGE3_AB_B_CODE_STYLE": str(ab_summary.get("b_code_style", "prefix_index")),
                "ET_STAGE3_AB_B_CODE_PREFIX": str(ab_summary.get("b_code_prefix", "__abB")),
                "ET_STAGE3_AB_B_DEFINITION_MODE": str(ab_summary.get("b_definition_mode", "shared_terms")),
                "ET_STAGE3_AB_GLOBAL_DICT_ENABLE": "1" if ab_summary.get("global_dict_enabled") else "0",
                "ET_STAGE3_AB_GLOBAL_DICT_PATH": str(ab_summary.get("global_dict_path", "")),
                "ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB": "1"
                if ab_summary.get("global_dict_charge_vocab")
                else "0",
            }
        ):
            record = prepare_task_record(
                task,
                hits,
                compression_tokenizer_key=TOKENIZER_KEY,
                stage3_backend="hybrid_ab",
                stage3_ab_mode=str(ab_summary.get("mode", "exact_only")),
                enable_b=bool(ab_summary.get("enable_b", False)),
                prompt_style=prompt_style,
                stage2_profile=stage2_profile,
                stage2_mode=stage2_mode,
                cache_repo_config=False,
            )
        delta = int(record.compressed_context_effective_tokens) - int(record.raw_context_tokens)
        prompt_rows.append(
            {
                "name": name,
                "task_id": task.task_id,
                "raw_context_tokens": int(record.raw_context_tokens),
                "compressed_effective_tokens": int(record.compressed_context_effective_tokens),
                "compressed_sequence_tokens": int(record.compressed_context_sequence_tokens),
                "codebook_tokens": int(record.compressed_codebook_tokens),
                "delta_tokens": int(delta),
            }
        )
    return _prompt_eval_row(name, prompt_rows), prompt_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "cache" / "langv1_pilot_corpus_200.jsonl",
    )
    parser.add_argument(
        "--humaneval-jsonl",
        type=Path,
        default=ROOT / "cache" / "humaneval" / "HumanEval_ascii_subset_10.jsonl",
    )
    parser.add_argument("--humaneval-limit", type=int, default=10)
    parser.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "results" / "langv1_pilot" / "qwen_stage3_param_search.json",
    )
    parser.add_argument(
        "--out-csv",
        type=Path,
        default=ROOT / "results" / "langv1_pilot" / "qwen_stage3_param_search.csv",
    )
    args = parser.parse_args()

    corpus_path = args.corpus
    tok_cfg = EVAL_TOKENIZERS[TOKENIZER_KEY]
    sources = _load_sources(corpus_path)

    qsmall_dict = _mk_global_dict(
        corpus_path=corpus_path,
        preset_name="qwen_small",
        output_path=ROOT / "cache" / "stage3_global_dictionary_qwen_small_200.json",
    )
    qmedium_dict = _mk_global_dict(
        corpus_path=corpus_path,
        preset_name="qwen_medium",
        output_path=ROOT / "cache" / "stage3_global_dictionary_qwen_medium_200.json",
    )

    base_repo = mine_from_sources(
        sources=sources,
        tokenizer_key=TOKENIZER_KEY,
        tokenizer_cfg=tok_cfg,
        cache_name="qwen_stage3_param_search_200",
        cache=True,
        verbose=True,
        stage3_backend="hybrid_ab",
    )

    scenarios: list[tuple[str, dict[str, str]]] = [
        (
            "exact_default",
            {
                "ET_STAGE3_AB_MODE": "exact_only",
                "ET_STAGE3_AB_ENABLE_B": "0",
            },
        ),
        (
            "exact_occ4",
            {
                "ET_STAGE3_AB_MODE": "exact_only",
                "ET_STAGE3_AB_ENABLE_B": "0",
                "ET_STAGE3_AB_A_MIN_OCC": "4",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
            },
        ),
        (
            "exact_occ6",
            {
                "ET_STAGE3_AB_MODE": "exact_only",
                "ET_STAGE3_AB_ENABLE_B": "0",
                "ET_STAGE3_AB_A_MIN_OCC": "6",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
            },
        ),
        (
            "exact_occ8",
            {
                "ET_STAGE3_AB_MODE": "exact_only",
                "ET_STAGE3_AB_ENABLE_B": "0",
                "ET_STAGE3_AB_A_MIN_OCC": "8",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
            },
        ),
        (
            "hybrid_default",
            {
                "ET_STAGE3_AB_MODE": "hybrid",
                "ET_STAGE3_AB_ENABLE_B": "1",
            },
        ),
        (
            "hybrid_compact_norm",
            {
                "ET_STAGE3_AB_MODE": "hybrid",
                "ET_STAGE3_AB_ENABLE_B": "1",
                "ET_STAGE3_AB_A_MIN_OCC": "4",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
                "ET_STAGE3_AB_B_SIMILARITY_NORM": "light",
                "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                "ET_STAGE3_AB_B_CODE_PREFIX": "q",
            },
        ),
        (
            "hybrid_compact_norm_occ6",
            {
                "ET_STAGE3_AB_MODE": "hybrid",
                "ET_STAGE3_AB_ENABLE_B": "1",
                "ET_STAGE3_AB_A_MIN_OCC": "6",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
                "ET_STAGE3_AB_B_SIMILARITY_NORM": "light",
                "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                "ET_STAGE3_AB_B_CODE_PREFIX": "q",
            },
        ),
        (
            "exact_global_qsmall",
            {
                "ET_STAGE3_AB_MODE": "exact_only",
                "ET_STAGE3_AB_ENABLE_B": "0",
                "ET_STAGE3_AB_A_MIN_OCC": "8",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
                "ET_STAGE3_AB_GLOBAL_DICT_ENABLE": "1",
                "ET_STAGE3_AB_GLOBAL_DICT_PATH": str(qsmall_dict),
                "ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB": "0",
            },
        ),
        (
            "exact_global_qmedium",
            {
                "ET_STAGE3_AB_MODE": "exact_only",
                "ET_STAGE3_AB_ENABLE_B": "0",
                "ET_STAGE3_AB_A_MIN_OCC": "6",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
                "ET_STAGE3_AB_GLOBAL_DICT_ENABLE": "1",
                "ET_STAGE3_AB_GLOBAL_DICT_PATH": str(qmedium_dict),
                "ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB": "0",
            },
        ),
        (
            "hybrid_global_qmedium",
            {
                "ET_STAGE3_AB_MODE": "hybrid",
                "ET_STAGE3_AB_ENABLE_B": "1",
                "ET_STAGE3_AB_A_MIN_OCC": "6",
                "ET_STAGE3_AB_MIN_RAW_TOKEN_LEN": "2",
                "ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN": "2",
                "ET_STAGE3_AB_B_SIMILARITY_NORM": "light",
                "ET_STAGE3_AB_B_CODE_STYLE": "base62",
                "ET_STAGE3_AB_B_CODE_PREFIX": "q",
                "ET_STAGE3_AB_GLOBAL_DICT_ENABLE": "1",
                "ET_STAGE3_AB_GLOBAL_DICT_PATH": str(qmedium_dict),
                "ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB": "0",
            },
        ),
    ]

    corpus_rows: list[dict] = []
    scenario_details: dict[str, dict] = {}
    for name, env in scenarios:
        summary = _mk_ab_summary(env)
        cfg = copy.deepcopy(base_repo)
        cfg.stage3_backend = "hybrid_ab"
        cfg.stage3_ab_summary = dict(summary)
        res = evaluate(
            sources,
            cfg,
            TOKENIZER_KEY,
            tok_cfg,
            stage2_profile="stage2_parseable",
            stage2_mode="blockwise",
        )
        row = _corpus_row(name, summary, res)
        corpus_rows.append(row)
        scenario_details[name] = {"stage3_ab_summary": summary, "corpus_metrics": row}
        print(
            f"[corpus:{name}] eff={row['effective_total_reduction_pct']:.6f} "
            f"seq={row['sequence_reduction_pct']:.6f} "
            f"global={row['stage3_ab_global_dict_enabled']}"
        )

    ranked = sorted(
        corpus_rows,
        key=lambda r: (
            float(r["effective_total_reduction_pct"]),
            float(r["sequence_reduction_pct"]),
        ),
        reverse=True,
    )
    top_names = [r["name"] for r in ranked[:4]]

    tasks = load_humaneval_tasks(
        jsonl_path=args.humaneval_jsonl,
        limit=int(args.humaneval_limit),
    )
    support = load_support_snippets(
        jsonl_path=str(ROOT / "cache" / "stage1_starcoder_1m_corpus.jsonl"),
        text_field="text",
        limit=1200,
        snippet_max_chars=1200,
    )

    prompt_summary_rows: list[dict] = []
    prompt_detail_rows: list[dict] = []
    for name in top_names:
        summary = scenario_details[name]["stage3_ab_summary"]
        prompt_row, prompt_rows = _prompt_eval(
            name=name,
            ab_summary=summary,
            tasks=tasks,
            support=support,
            prompt_style="structured",
            stage2_profile="stage2_parseable",
            stage2_mode="blockwise",
        )
        prompt_summary_rows.append(prompt_row)
        prompt_detail_rows.extend(prompt_rows)
        scenario_details[name]["prompt_metrics"] = prompt_row
        print(
            f"[prompt:{name}] avg_delta={prompt_row['avg_delta_tokens']:.3f} "
            f"improved={prompt_row['n_tasks_improved']}/{prompt_row['n_tasks']}"
        )

    prompt_ranked = sorted(
        prompt_summary_rows,
        key=lambda r: (float(r["avg_delta_tokens"]), -int(r["n_tasks_improved"])),
    )
    best_prompt = prompt_ranked[0] if prompt_ranked else None

    payload = {
        "tokenizer_key": TOKENIZER_KEY,
        "corpus_path": str(corpus_path),
        "humaneval_jsonl": str(args.humaneval_jsonl),
        "humaneval_limit": int(args.humaneval_limit),
        "qwen_global_dicts": {
            "qwen_small": str(qsmall_dict),
            "qwen_medium": str(qmedium_dict),
        },
        "corpus_rows": corpus_rows,
        "top_scenarios_by_corpus": top_names,
        "prompt_summary_rows": prompt_summary_rows,
        "best_prompt_scenario": best_prompt,
        "prompt_detail_rows": prompt_detail_rows,
        "scenario_details": scenario_details,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with args.out_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(corpus_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(corpus_rows)

    prompt_csv = args.out_csv.with_name(args.out_csv.stem + "_prompt.csv")
    with prompt_csv.open("w", newline="", encoding="utf-8") as f:
        fieldnames = list(prompt_summary_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(prompt_summary_rows)

    print(f"[done] wrote {args.out_json}")
    print(f"[done] wrote {args.out_csv}")
    print(f"[done] wrote {prompt_csv}")
    if best_prompt is not None:
        print(
            f"[best] {best_prompt['name']} avg_delta={best_prompt['avg_delta_tokens']:.3f} "
            f"improved={best_prompt['n_tasks_improved']}/{best_prompt['n_tasks']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
