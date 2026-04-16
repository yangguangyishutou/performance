"""Analyze token deltas across raw -> stage1 -> stage2 -> stage3 for prepared HumanEval prompts."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from statistics import mean
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS, VOCAB_COST_MODE  # noqa: E402
from eval.humaneval_utils import load_jsonl, temporary_stage3ab_env  # noqa: E402
from placeholder_accounting import compute_vocab_intro_cost, count_base_tokens  # noqa: E402
from pipeline import apply_stage1, apply_stage2, apply_stage3  # noqa: E402
from repo_miner import _load_tokenizer, mine_from_sources  # noqa: E402

_SUPPORT_BLOCK_RE = re.compile(
    r"(?ms)^# \[(?:Support|Compressed Support) \d+\]\n(.*?)(?=^# \[(?:Support|Compressed Support) \d+\]\n|\Z)"
)


def _extract_support_blocks(rendered: str) -> list[str]:
    return [m.group(1).strip() for m in _SUPPORT_BLOCK_RE.finditer(str(rendered or "")) if m.group(1).strip()]


def _join_support_bodies(texts: list[str]) -> str:
    return "\n\n".join(x.rstrip() for x in texts if str(x).strip()).rstrip()


@contextmanager
def _temporary_global_dict_env(path: str | None, *, enabled: bool, charge_vocab: bool):
    saved_enable = os.environ.get("ET_STAGE3_AB_GLOBAL_DICT_ENABLE")
    saved_path = os.environ.get("ET_STAGE3_AB_GLOBAL_DICT_PATH")
    saved_charge = os.environ.get("ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB")
    try:
        os.environ["ET_STAGE3_AB_GLOBAL_DICT_ENABLE"] = "1" if enabled else "0"
        if path:
            os.environ["ET_STAGE3_AB_GLOBAL_DICT_PATH"] = str(path)
        else:
            os.environ.pop("ET_STAGE3_AB_GLOBAL_DICT_PATH", None)
        os.environ["ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB"] = "1" if charge_vocab else "0"
        yield
    finally:
        if saved_enable is None:
            os.environ.pop("ET_STAGE3_AB_GLOBAL_DICT_ENABLE", None)
        else:
            os.environ["ET_STAGE3_AB_GLOBAL_DICT_ENABLE"] = saved_enable
        if saved_path is None:
            os.environ.pop("ET_STAGE3_AB_GLOBAL_DICT_PATH", None)
        else:
            os.environ["ET_STAGE3_AB_GLOBAL_DICT_PATH"] = saved_path
        if saved_charge is None:
            os.environ.pop("ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB", None)
        else:
            os.environ["ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB"] = saved_charge


def _count(text: str, tokenizer: Any, tok_type: str) -> int:
    return count_base_tokens(text, tokenizer=tokenizer, tok_type=tok_type)


def _safe_mean(values: list[float | int]) -> float:
    return float(mean(values)) if values else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--global-dict", type=Path, default=None)
    parser.add_argument("--global-dict-charge-vocab", action="store_true")
    parser.add_argument("--enable-b", action="store_true")
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional summary JSON path",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=None,
        help="Optional per-task CSV path",
    )
    args = parser.parse_args()

    rows = load_jsonl(args.prepared)
    if not rows:
        raise SystemExit(f"empty prepared file: {args.prepared}")

    tokenizer_key = str(rows[0]["compression_tokenizer_key"])
    tok_cfg = EVAL_TOKENIZERS[tokenizer_key]
    tokenizer, tok_type = _load_tokenizer(tokenizer_key, tok_cfg)

    task_rows: list[dict[str, Any]] = []
    with _temporary_global_dict_env(
        str(args.global_dict) if args.global_dict else None,
        enabled=bool(args.global_dict),
        charge_vocab=bool(args.global_dict_charge_vocab),
    ):
        for idx, row in enumerate(rows, start=1):
            raw_texts = _extract_support_blocks(row.get("raw_support_text", ""))
            if not raw_texts:
                continue

            with temporary_stage3ab_env(
                mode=str(row.get("stage3_ab_mode") or "exact_only"),
                enable_b=bool(args.enable_b),
            ):
                repo_config = mine_from_sources(
                    raw_texts,
                    tokenizer_key=tokenizer_key,
                    tokenizer_cfg=tok_cfg,
                    cache=False,
                    cache_name=f"humaneval_stage_stack_{idx}",
                    verbose=False,
                    min_freq=1,
                    stage3_backend=str(row.get("stage3_backend") or "hybrid_ab"),
                )
                stage1_texts: list[str] = []
                stage2_texts: list[str] = []
                stage3_texts: list[str] = []
                for text in raw_texts:
                    s1 = apply_stage1(text, repo_config)
                    s2 = apply_stage2(
                        s1,
                        profile=str(row.get("stage2_profile") or "stage2_parseable"),
                        mode=str(row.get("stage2_mode") or "blockwise"),
                    )
                    s3 = apply_stage3(
                        s2,
                        repo_config,
                        tokenizer=tokenizer,
                        tok_type=tok_type,
                    )
                    stage1_texts.append(s1)
                    stage2_texts.append(s2)
                    stage3_texts.append(s3)

            raw_body = _join_support_bodies(raw_texts)
            s1_body = _join_support_bodies(stage1_texts)
            s2_body = _join_support_bodies(stage2_texts)
            s3_body = _join_support_bodies(stage3_texts)

            raw_body_tokens = _count(raw_body, tokenizer, tok_type)
            stage1_body_tokens = _count(s1_body, tokenizer, tok_type)
            stage2_body_tokens = _count(s2_body, tokenizer, tok_type)
            stage3_body_tokens = _count(s3_body, tokenizer, tok_type)

            prompt_raw_tokens = _count(str(row.get("prompt_raw", "")), tokenizer, tok_type)
            prompt_compressed_tokens = _count(str(row.get("prompt_compressed", "")), tokenizer, tok_type)
            task_prompt_tokens = _count(str(row.get("task_prompt", "")), tokenizer, tok_type)
            dynamic_dict_tokens = compute_vocab_intro_cost(
                list(row.get("codebook_entries") or []),
                mode=VOCAB_COST_MODE,
                tokenizer=tokenizer,
                tok_type=tok_type,
            )

            raw_nonbody_tokens = prompt_raw_tokens - task_prompt_tokens - raw_body_tokens
            compressed_nonbody_tokens = (
                prompt_compressed_tokens - task_prompt_tokens - stage3_body_tokens - dynamic_dict_tokens
            )

            task_rows.append(
                {
                    "task_id": row["task_id"],
                    "raw_body_tokens": raw_body_tokens,
                    "stage1_body_tokens": stage1_body_tokens,
                    "stage2_body_tokens": stage2_body_tokens,
                    "stage3_body_tokens": stage3_body_tokens,
                    "stage1_delta_vs_raw": stage1_body_tokens - raw_body_tokens,
                    "stage2_delta_vs_stage1": stage2_body_tokens - stage1_body_tokens,
                    "stage3_delta_vs_stage2": stage3_body_tokens - stage2_body_tokens,
                    "stage3_delta_vs_raw": stage3_body_tokens - raw_body_tokens,
                    "dynamic_dict_tokens": dynamic_dict_tokens,
                    "raw_nonbody_tokens": raw_nonbody_tokens,
                    "compressed_nonbody_tokens": compressed_nonbody_tokens,
                    "wrapper_delta": compressed_nonbody_tokens - raw_nonbody_tokens,
                    "prompt_raw_tokens": prompt_raw_tokens,
                    "prompt_compressed_tokens": prompt_compressed_tokens,
                    "prompt_delta": prompt_compressed_tokens - prompt_raw_tokens,
                    "task_prompt_tokens": task_prompt_tokens,
                }
            )
            print(
                f"[analyze] {idx}/{len(rows)} {row['task_id']} "
                f"stage1={stage1_body_tokens - raw_body_tokens:+d} "
                f"stage2={stage2_body_tokens - stage1_body_tokens:+d} "
                f"stage3={stage3_body_tokens - stage2_body_tokens:+d} "
                f"dict={dynamic_dict_tokens:+d} "
                f"wrapper={compressed_nonbody_tokens - raw_nonbody_tokens:+d} "
                f"prompt={prompt_compressed_tokens - prompt_raw_tokens:+d}"
            )

    summary = {
        "prepared": str(args.prepared),
        "tokenizer_key": tokenizer_key,
        "n_tasks": len(task_rows),
        "averages": {
            "raw_body_tokens": _safe_mean([r["raw_body_tokens"] for r in task_rows]),
            "stage1_body_tokens": _safe_mean([r["stage1_body_tokens"] for r in task_rows]),
            "stage2_body_tokens": _safe_mean([r["stage2_body_tokens"] for r in task_rows]),
            "stage3_body_tokens": _safe_mean([r["stage3_body_tokens"] for r in task_rows]),
            "stage1_delta_vs_raw": _safe_mean([r["stage1_delta_vs_raw"] for r in task_rows]),
            "stage2_delta_vs_stage1": _safe_mean([r["stage2_delta_vs_stage1"] for r in task_rows]),
            "stage3_delta_vs_stage2": _safe_mean([r["stage3_delta_vs_stage2"] for r in task_rows]),
            "stage3_delta_vs_raw": _safe_mean([r["stage3_delta_vs_raw"] for r in task_rows]),
            "dynamic_dict_tokens": _safe_mean([r["dynamic_dict_tokens"] for r in task_rows]),
            "wrapper_delta": _safe_mean([r["wrapper_delta"] for r in task_rows]),
            "prompt_delta": _safe_mean([r["prompt_delta"] for r in task_rows]),
        },
        "tasks": task_rows,
    }

    print(json.dumps(summary["averages"], ensure_ascii=False, indent=2))

    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print(args.output_json)

    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(task_rows[0].keys()) if task_rows else [])
            if task_rows:
                writer.writeheader()
                writer.writerows(task_rows)
        print(args.output_csv)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
