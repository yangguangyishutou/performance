"""Cross-platform HumanEval scoring helpers for this repo."""

from __future__ import annotations

import contextlib
import itertools
import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import StringIO
from pathlib import Path
from typing import Any

import numpy as np


def _load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    fp = Path(path)
    rows: list[dict[str, Any]] = []
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _write_jsonl(path: str | Path, rows: list[dict[str, Any]]) -> None:
    fp = Path(path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    with fp.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def read_problems_local(problem_file: str | Path) -> dict[str, dict[str, Any]]:
    return {row["task_id"]: row for row in _load_jsonl(problem_file)}


def estimate_pass_at_k(
    num_samples: int | list[int] | np.ndarray,
    num_correct: list[int] | np.ndarray,
    k: int,
) -> np.ndarray:
    def estimator(n: int, c: int, kk: int) -> float:
        if n - c < kk:
            return 1.0
        return 1.0 - np.prod(1.0 - kk / np.arange(n - c + 1, n + 1))

    if isinstance(num_samples, int):
        num_samples_it = itertools.repeat(num_samples, len(num_correct))
    else:
        assert len(num_samples) == len(num_correct)
        num_samples_it = iter(num_samples)

    return np.array([estimator(int(n), int(c), k) for n, c in zip(num_samples_it, num_correct)])


@contextlib.contextmanager
def create_tempdir() -> Any:
    old_cwd = os.getcwd()
    with tempfile.TemporaryDirectory(prefix="humaneval_") as tmpdir:
        os.chdir(tmpdir)
        try:
            yield tmpdir
        finally:
            os.chdir(old_cwd)


@contextlib.contextmanager
def swallow_io() -> Any:
    devnull = open(os.devnull, "w", encoding="utf-8")
    old_stdin = sys.stdin
    sys.stdin = StringIO("")
    try:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            yield
    finally:
        sys.stdin = old_stdin
        devnull.close()


def reliability_guard() -> None:
    """Best-effort local sandbox for generated code."""

    blocked_msg = "disabled by humaneval_scoring.reliability_guard"

    def _blocked(*_args: Any, **_kwargs: Any) -> Any:
        raise RuntimeError(blocked_msg)

    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["NUMEXPR_NUM_THREADS"] = "1"

    try:
        import resource  # type: ignore

        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (min(256, soft), min(256, hard)))
    except Exception:
        pass

    for attr in ("system", "popen", "spawnl", "spawnlp", "spawnv", "spawnvp", "startfile", "kill", "killpg"):
        if hasattr(os, attr):
            setattr(os, attr, _blocked)
    for attr in ("remove", "removedirs", "rename", "renames", "replace", "unlink", "chmod", "chown", "lchmod", "lchown"):
        if hasattr(os, attr):
            setattr(os, attr, _blocked)

    shutil.rmtree = _blocked  # type: ignore[assignment]
    shutil.move = _blocked  # type: ignore[assignment]
    subprocess.Popen = _blocked  # type: ignore[assignment]
    subprocess.call = _blocked  # type: ignore[assignment]
    subprocess.run = _blocked  # type: ignore[assignment]


def _unsafe_execute_cross_platform(problem: dict[str, Any], completion: str, result_list: Any) -> None:
    with create_tempdir():
        rmtree = shutil.rmtree
        rmdir = os.rmdir
        chdir = os.chdir

        reliability_guard()
        check_program = (
            problem["prompt"]
            + completion
            + "\n"
            + problem["test"]
            + "\n"
            + f"check({problem['entry_point']})"
        )

        try:
            exec_globals: dict[str, Any] = {}
            with swallow_io():
                exec(check_program, exec_globals)
            result_list.append("passed")
        except BaseException as exc:  # noqa: BLE001
            result_list.append(f"failed: {exc}")
        finally:
            shutil.rmtree = rmtree
            os.rmdir = rmdir
            os.chdir = chdir


def check_correctness_cross_platform(
    problem: dict[str, Any],
    completion: str,
    timeout: float,
    completion_id: int | None = None,
) -> dict[str, Any]:
    ctx = mp.get_context("spawn")
    manager = ctx.Manager()
    result_list = manager.list()
    proc = ctx.Process(
        target=_unsafe_execute_cross_platform,
        args=(problem, completion, result_list),
    )
    proc.start()
    proc.join(timeout=timeout + 1.0)
    if proc.is_alive():
        proc.kill()
        proc.join(timeout=1.0)
    if result_list:
        result = result_list[0]
    else:
        result = f"timed out (exitcode={proc.exitcode})"
    return {
        "task_id": problem["task_id"],
        "passed": result == "passed",
        "result": result,
        "completion_id": completion_id,
    }


def evaluate_functional_correctness_cross_platform(
    sample_file: str | Path,
    *,
    k: list[int],
    n_workers: int,
    timeout: float,
    problem_file: str | Path,
) -> dict[str, float]:
    problems = read_problems_local(problem_file)
    samples = _load_jsonl(sample_file)

    with ThreadPoolExecutor(max_workers=max(1, int(n_workers))) as executor:
        futures = []
        completion_id = Counter()
        results: dict[str, list[tuple[int, dict[str, Any]]]] = defaultdict(list)

        for sample in samples:
            task_id = str(sample["task_id"])
            completion = str(sample["completion"])
            if task_id not in problems:
                raise KeyError(f"task_id {task_id} not found in problem_file")
            fut = executor.submit(
                check_correctness_cross_platform,
                problems[task_id],
                completion,
                float(timeout),
                completion_id[task_id],
            )
            futures.append(fut)
            completion_id[task_id] += 1

        for fut in as_completed(futures):
            result = fut.result()
            results[result["task_id"]].append((result["completion_id"], result))

    total: list[int] = []
    correct: list[int] = []
    for result in results.values():
        result.sort(key=lambda x: x[0])
        passed = [r[1]["passed"] for r in result]
        total.append(len(passed))
        correct.append(sum(passed))
    total_np = np.array(total)
    correct_np = np.array(correct)
    pass_at_k = {
        f"pass@{kk}": estimate_pass_at_k(total_np, correct_np, kk).mean()
        for kk in k
        if len(total_np) > 0 and (total_np >= kk).all()
    }

    combined: list[dict[str, Any]] = []
    by_task_queues: dict[str, list[dict[str, Any]]] = {}
    for task_id, result in results.items():
        by_task_queues[task_id] = [x[1] for x in sorted(result, key=lambda x: x[0])]
    for sample in samples:
        task_id = str(sample["task_id"])
        row = dict(sample)
        result = by_task_queues[task_id].pop(0)
        row["result"] = result["result"]
        row["passed"] = result["passed"]
        combined.append(row)
    _write_jsonl(f"{sample_file}_results.jsonl", combined)
    return pass_at_k
