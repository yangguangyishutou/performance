"""Merge prepared prompt metadata and generation details into a compact CSV/JSONL summary."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from eval.humaneval_utils import load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a task-level report for HumanEval experiments.")
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--details", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    prepared = {row["task_id"]: row for row in load_jsonl(args.prepared)}
    details = load_jsonl(args.details)
    rows: list[dict[str, object]] = []
    for det in details:
        prep = prepared.get(det["task_id"], {})
        metrics = dict(prep.get("metrics", {}) or {})
        rows.append(
            {
                "task_id": det["task_id"],
                "arm": det.get("arm", ""),
                "backend": det.get("backend", ""),
                "model": det.get("model", ""),
                "prompt_tokens": det.get("prompt_tokens", ""),
                "raw_context_tokens": prep.get("raw_context_tokens", ""),
                "compressed_context_effective_tokens": prep.get(
                    "compressed_context_effective_tokens",
                    "",
                ),
                "codebook_entries": len(prep.get("codebook_entries", []) or []),
                "stage3_ab_mode": prep.get("stage3_ab_mode", ""),
                "stage3_ab_a_sequence_saved": metrics.get("stage3_ab_a_sequence_saved", 0),
                "stage3_ab_b_sequence_saved": metrics.get("stage3_ab_b_sequence_saved", 0),
                "stage3_ab_fallback_count": metrics.get("stage3_ab_fallback_count", 0),
                "stage3_ab_b_route_reject_count": metrics.get(
                    "stage3_ab_b_route_reject_count",
                    0,
                ),
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["task_id"])
        writer.writeheader()
        writer.writerows(rows)
    meta = args.output.with_suffix(".json")
    meta.write_text(json.dumps({"n_rows": len(rows)}, indent=2), encoding="utf-8")
    print(args.output)
    print(meta)


if __name__ == "__main__":
    main()

