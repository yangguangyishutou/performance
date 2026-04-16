"""Prepare stage3ab HumanEval prompts with raw and compressed support context."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.humaneval_utils import (
    DEFAULT_COMPRESSION_TOKENIZER,
    DEFAULT_HUMANEVAL_DATASET,
    DEFAULT_HUMANEVAL_SPLIT,
    DEFAULT_SNIPPET_MAX_CHARS,
    DEFAULT_STAGE2_MODE,
    DEFAULT_STAGE2_PROFILE,
    DEFAULT_SUPPORT_DATASET,
    DEFAULT_SUPPORT_DATASET_SPLIT,
    DEFAULT_SUPPORT_LIMIT,
    DEFAULT_SUPPORT_TEXT_FIELD,
    DEFAULT_SUPPORT_TOP_K,
    default_prepare_output_path,
    load_humaneval_tasks,
    load_support_snippets,
    prepare_task_record,
    record_to_dict,
    retrieve_support_snippets,
    write_jsonl,
)


def _bool_from_ab_mode(mode: str) -> bool:
    return (mode or "").strip().lower() == "hybrid"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare HumanEval prompts for stage3ab experiments.")
    parser.add_argument("--dataset", default=DEFAULT_HUMANEVAL_DATASET)
    parser.add_argument("--split", default=DEFAULT_HUMANEVAL_SPLIT)
    parser.add_argument("--dataset-jsonl", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--task-id", action="append", default=None)
    parser.add_argument("--support-repo", default=None)
    parser.add_argument("--support-jsonl", default=None)
    parser.add_argument("--support-dataset", default=DEFAULT_SUPPORT_DATASET or None)
    parser.add_argument("--support-dataset-split", default=DEFAULT_SUPPORT_DATASET_SPLIT)
    parser.add_argument("--support-text-field", default=DEFAULT_SUPPORT_TEXT_FIELD)
    parser.add_argument("--support-limit", type=int, default=DEFAULT_SUPPORT_LIMIT)
    parser.add_argument("--support-top-k", type=int, default=DEFAULT_SUPPORT_TOP_K)
    parser.add_argument("--snippet-max-chars", type=int, default=DEFAULT_SNIPPET_MAX_CHARS)
    parser.add_argument("--compression-tokenizer", default=DEFAULT_COMPRESSION_TOKENIZER)
    parser.add_argument("--stage3-backend", default="hybrid_ab", choices=("hybrid_ab",))
    parser.add_argument("--stage3-ab-mode", default="exact_only", choices=("exact_only", "hybrid"))
    parser.add_argument("--prompt-style", default="legacy", choices=("legacy", "structured"))
    parser.add_argument("--stage2-profile", default=DEFAULT_STAGE2_PROFILE)
    parser.add_argument("--stage2-mode", default=DEFAULT_STAGE2_MODE, choices=("linewise", "blockwise", None))
    parser.add_argument("--no-cache", action="store_true")
    parser.add_argument("--tag", default="")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    tasks = load_humaneval_tasks(
        dataset_name=args.dataset,
        split=args.split,
        jsonl_path=args.dataset_jsonl,
        limit=args.limit,
        task_ids=args.task_id,
    )
    support = load_support_snippets(
        repo_path=args.support_repo,
        jsonl_path=args.support_jsonl,
        dataset_name=args.support_dataset,
        dataset_split=args.support_dataset_split,
        text_field=args.support_text_field,
        limit=args.support_limit,
        snippet_max_chars=args.snippet_max_chars,
    )
    if not support:
        raise SystemExit("No support snippets found. Provide --support-repo, --support-jsonl, or --support-dataset.")

    rows: list[dict] = []
    enable_b = _bool_from_ab_mode(args.stage3_ab_mode)
    for idx, task in enumerate(tasks, start=1):
        hits = retrieve_support_snippets(task, support, top_k=args.support_top_k)
        record = prepare_task_record(
            task,
            hits,
            compression_tokenizer_key=args.compression_tokenizer,
            stage3_backend=args.stage3_backend,
            stage3_ab_mode=args.stage3_ab_mode,
            enable_b=enable_b,
            prompt_style=args.prompt_style,
            stage2_profile=args.stage2_profile,
            stage2_mode=args.stage2_mode,
            cache_repo_config=not args.no_cache,
        )
        rows.append(record_to_dict(record))
        print(
            f"[prepare] {idx}/{len(tasks)} {task.task_id} "
            f"raw_ctx={record.raw_context_tokens} "
            f"comp_ctx={record.compressed_context_effective_tokens}"
        )

    out = args.output or default_prepare_output_path(args.tag)
    write_jsonl(out, rows)
    meta = {
        "dataset": args.dataset,
        "split": args.split,
        "dataset_jsonl": args.dataset_jsonl,
        "n_tasks": len(rows),
        "support_repo": args.support_repo,
        "support_jsonl": args.support_jsonl,
        "support_dataset": args.support_dataset,
        "support_dataset_split": args.support_dataset_split,
        "support_text_field": args.support_text_field,
        "support_limit": args.support_limit,
        "support_top_k": args.support_top_k,
        "snippet_max_chars": args.snippet_max_chars,
        "compression_tokenizer": args.compression_tokenizer,
        "stage3_backend": args.stage3_backend,
        "stage3_ab_mode": args.stage3_ab_mode,
        "prompt_style": args.prompt_style,
        "stage2_profile": args.stage2_profile,
        "stage2_mode": args.stage2_mode,
        "output": str(out),
    }
    meta_path = out.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(out)
    print(meta_path)


if __name__ == "__main__":
    main()
