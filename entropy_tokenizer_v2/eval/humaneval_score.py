"""Stable HumanEval scoring wrapper for this repo."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from eval.humaneval_scoring import evaluate_functional_correctness_cross_platform
from eval.humaneval_utils import DEFAULT_HUMANEVAL_DATASET, DEFAULT_HUMANEVAL_SPLIT


def ensure_problem_file(
    *,
    dataset_name: str = DEFAULT_HUMANEVAL_DATASET,
    split: str = DEFAULT_HUMANEVAL_SPLIT,
    output: str | Path | None = None,
    task_ids: set[str] | None = None,
) -> Path:
    """Export HumanEval problems to an ASCII JSONL file local to this workspace."""
    from datasets import load_dataset

    out = Path(output) if output is not None else (REPO_ROOT / "cache" / "humaneval" / "HumanEval_ascii.jsonl")
    out.parent.mkdir(parents=True, exist_ok=True)
    if task_ids is None and out.exists() and out.stat().st_size > 0:
        return out
    ds = load_dataset(dataset_name, split=split)
    with out.open("w", encoding="utf-8") as f:
        for row in ds:
            if task_ids is not None and str(row["task_id"]) not in task_ids:
                continue
            f.write(
                json.dumps(
                    {
                        "task_id": row["task_id"],
                        "prompt": row["prompt"],
                        "canonical_solution": row["canonical_solution"],
                        "test": row["test"],
                        "entry_point": row["entry_point"],
                    },
                    ensure_ascii=True,
                )
                + "\n"
            )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Score samples.jsonl with the official HumanEval evaluator.")
    parser.add_argument("--samples", type=Path, required=True)
    parser.add_argument("--problem-file", type=Path, default=None)
    parser.add_argument("--dataset", default=DEFAULT_HUMANEVAL_DATASET)
    parser.add_argument("--split", default=DEFAULT_HUMANEVAL_SPLIT)
    parser.add_argument("--k", default="1,10,100")
    parser.add_argument("--n-workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument(
        "--match-samples",
        action="store_true",
        help="Export a problem file that contains only task_ids present in --samples.",
    )
    args = parser.parse_args()

    task_ids = None
    if args.match_samples:
        task_ids = set()
        with args.samples.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                task_ids.add(str(row["task_id"]))
    problem_file = args.problem_file or ensure_problem_file(
        dataset_name=args.dataset,
        split=args.split,
        output=(
            REPO_ROOT
            / "cache"
            / "humaneval"
            / (
                f"HumanEval_ascii_subset_{len(task_ids)}.jsonl"
                if task_ids is not None
                else "HumanEval_ascii.jsonl"
            )
        )
        if task_ids is not None
        else None,
        task_ids=task_ids,
    )
    ks = [int(x.strip()) for x in str(args.k).split(",") if x.strip()]

    res = evaluate_functional_correctness_cross_platform(
        str(args.samples),
        k=ks,
        n_workers=int(args.n_workers),
        timeout=float(args.timeout),
        problem_file=str(problem_file),
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
