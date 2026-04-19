"""Generate multi-view instruction data for compression pre-adaptation."""

from __future__ import annotations

import argparse
import json
import logging
import random
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SYSTEM_PROMPT = (
    "You are an expert programming assistant. You may receive compressed code "
    "contexts containing base62 aliases (e.g., @A, @B) defined in a codebook. "
    "Expand them accurately if requested, or reason directly over them."
)

VIEW_RAW2RAW = "raw2raw"
VIEW_COMP2RAW = "compressed2raw"
VIEW_COMP2RAW_REJ = "compressed2raw_rejection"
VIEW_COMP2COMP = "compressed2compressed"
RAW_OUTPUT_REQ = "\n[Output Requirement: Expand all codebook aliases and output completely raw code.]"
COMPRESSED_OUTPUT_REQ = "\n[Output Requirement: Use the provided codebook aliases strictly to compress your response.]"
RAW_OUTPUT_REQ_PREFIX = "[Output Requirement: Expand all codebook aliases and output completely raw code.]"
COMPRESSED_OUTPUT_REQ_PREFIX = "[Output Requirement: Use the provided codebook aliases strictly to compress your response.]"


def _simple_token_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[^\w\s]", text))


class MockCompressionEngine:
    """A lightweight mock engine for A-channel alias compression."""

    _STOPWORDS = {
        "def",
        "return",
        "for",
        "while",
        "if",
        "else",
        "elif",
        "in",
        "and",
        "or",
        "not",
        "class",
        "from",
        "import",
        "with",
        "as",
        "try",
        "except",
        "finally",
        "lambda",
        "True",
        "False",
        "None",
    }

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)

    def compress_a_channel_only(self, text: str) -> dict[str, Any]:
        """Mock compression with alias replacement and synthetic metadata."""
        words = re.findall(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b", text)
        counter = Counter(
            w for w in words if w not in self._STOPWORDS and not w.startswith("_")
        )
        ranked = sorted(counter.items(), key=lambda x: (-x[1], -len(x[0]), x[0]))

        picked = ranked[: min(6, len(ranked))]
        aliases = [f"@{chr(ord('A') + i)}" for i in range(len(picked))]
        codebook: dict[str, str] = {alias: word for alias, (word, _freq) in zip(aliases, picked)}

        compressed = text
        for alias, word in codebook.items():
            compressed = re.sub(rf"\b{re.escape(word)}\b", alias, compressed)

        raw_tokens = _simple_token_count(text)
        compressed_tokens = _simple_token_count(compressed)
        jitter = self._rng.randint(-2, 2)
        delta_tokens = int(compressed_tokens - raw_tokens + jitter)
        delta_tokens = max(-20, min(20, delta_tokens))

        hits = sum(counter.get(word, 0) for word in codebook.values())
        ratio = (len(compressed) / len(text)) if text else 1.0
        metadata = {
            "is_valid_sample": True,
            "delta_tokens": delta_tokens,
            "compression_ratio": round(ratio, 4),
            "a_hits": int(hits),
        }
        return {
            "compressed_prompt": compressed,
            "codebook": codebook,
            "metadata": metadata,
        }

    def apply_existing_codebook(self, text: str, codebook: dict[str, str]) -> str:
        """Apply a known alias codebook to another text span."""
        out = text
        for alias, word in codebook.items():
            out = re.sub(rf"\b{re.escape(word)}\b", alias, out)
        return out


@dataclass
class TaskRecord:
    task_id: str
    prompt: str
    target: str


class MultiViewDataGenerator:
    """Generate raw/compressed multi-view instruction-tuning samples."""

    def __init__(
        self,
        compression_engine: MockCompressionEngine,
        *,
        task_family: str = "HumanEval",
        seed: int = 42,
        hard_constraint_prefix: bool = True,
    ) -> None:
        self.engine = compression_engine
        self.task_family = task_family
        self._rng = random.Random(seed)
        self.hard_constraint_prefix = bool(hard_constraint_prefix)

    def load_tasks(self, input_file: Path, max_samples: int | None = None) -> list[TaskRecord]:
        tasks: list[TaskRecord] = []
        with input_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                task_id = str(obj.get("task_id", "")).strip()
                prompt = str(obj.get("prompt", ""))
                target = str(obj.get("target", ""))
                if not task_id or not prompt or not target:
                    continue
                tasks.append(TaskRecord(task_id=task_id, prompt=prompt, target=target))
                if max_samples is not None and len(tasks) >= max_samples:
                    break
        return tasks

    def _format_codebook_prompt(self, compressed_prompt: str, codebook: dict[str, str]) -> str:
        body = "\n".join(f"{alias}={literal}" for alias, literal in codebook.items())
        return f"<CODEBOOK>\n{body}\n</CODEBOOK>\n<CONTEXT>\n{compressed_prompt}\n</CONTEXT>"

    def _build_sample(
        self,
        *,
        task: TaskRecord,
        view_type: str,
        user_content: str,
        assistant_content: str,
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        suffix_map = {
            VIEW_RAW2RAW: "raw2raw",
            VIEW_COMP2RAW: "comp2raw",
            VIEW_COMP2RAW_REJ: "comp2raw_rej",
            VIEW_COMP2COMP: "comp2comp",
        }
        sample = {
            "task_id": f"{task.task_id}_{suffix_map[view_type]}",
            "task_family": self.task_family,
            "view_type": view_type,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
                {"role": "assistant", "content": assistant_content},
            ],
            "metadata": metadata,
        }
        return sample

    def generate_multi_view_samples(self, task: TaskRecord) -> dict[str, dict[str, Any]]:
        """Generate candidate views for a single task."""
        return self._build_per_task_views(task)

    def _build_per_task_views(self, task: TaskRecord) -> dict[str, dict[str, Any]]:
        out: dict[str, dict[str, Any]] = {}
        raw_metadata = {
            "is_valid_sample": True,
            "delta_tokens": 0,
            "compression_ratio": 1.0,
            "a_hits": 0,
        }
        out[VIEW_RAW2RAW] = self._build_sample(
            task=task,
            view_type=VIEW_RAW2RAW,
            user_content=task.prompt,
            assistant_content=task.target,
            metadata=raw_metadata,
        )

        comp = self.engine.compress_a_channel_only(task.prompt)
        comp_prompt = str(comp["compressed_prompt"])
        codebook = dict(comp["codebook"])
        metadata = dict(comp["metadata"])
        user_comp = self._format_codebook_prompt(comp_prompt, codebook)

        if int(metadata.get("delta_tokens", 0)) > 8:
            return out

        comp_target = self.engine.apply_existing_codebook(task.target, codebook)
        user_comp_raw = user_comp + RAW_OUTPUT_REQ
        user_comp_comp = user_comp + COMPRESSED_OUTPUT_REQ
        if self.hard_constraint_prefix:
            user_comp_raw = RAW_OUTPUT_REQ_PREFIX + "\n" + user_comp_raw
            user_comp_comp = COMPRESSED_OUTPUT_REQ_PREFIX + "\n" + user_comp_comp
        out[VIEW_COMP2RAW] = self._build_sample(
            task=task,
            view_type=VIEW_COMP2RAW,
            user_content=user_comp_raw,
            assistant_content=task.target,
            metadata=dict(metadata),
        )
        # 自我纠错视图：先声明不能直接输出别名，再给出 raw 目标代码。
        if codebook:
            alias, word = self._rng.choice(list(codebook.items()))
        else:
            alias, word = "@A", "value"
        rejection_prefix = (
            f"[Constraint Check] I must not output '{alias}' directly. "
            f"It must be translated to '{word}'. Filtering all aliases...\n\n"
        )
        out[VIEW_COMP2RAW_REJ] = self._build_sample(
            task=task,
            view_type=VIEW_COMP2RAW_REJ,
            user_content=user_comp_raw,
            assistant_content=rejection_prefix + task.target,
            metadata=dict(metadata),
        )
        out[VIEW_COMP2COMP] = self._build_sample(
            task=task,
            view_type=VIEW_COMP2COMP,
            user_content=user_comp_comp,
            assistant_content=comp_target,
            metadata=dict(metadata),
        )
        return out

    def generate(self, tasks: list[TaskRecord]) -> list[dict[str, Any]]:
        # 目标配比：10/50/20/20 = 1:5:2:2
        target_ratio = {
            VIEW_RAW2RAW: 0.10,
            VIEW_COMP2RAW: 0.50,
            VIEW_COMP2RAW_REJ: 0.20,
            VIEW_COMP2COMP: 0.20,
        }
        pools: dict[str, list[dict[str, Any]]] = {
            VIEW_RAW2RAW: [],
            VIEW_COMP2RAW: [],
            VIEW_COMP2RAW_REJ: [],
            VIEW_COMP2COMP: [],
        }

        for idx, task in enumerate(tasks, start=1):
            per_task = self.generate_multi_view_samples(task)
            for view_name in pools:
                if view_name in per_task:
                    pools[view_name].append(per_task[view_name])
            if idx % 100 == 0 or idx == len(tasks):
                logging.info(
                    "Processed %d/%d tasks | raw=%d c2r=%d c2r_rej=%d c2c=%d",
                    idx,
                    len(tasks),
                    len(pools[VIEW_RAW2RAW]),
                    len(pools[VIEW_COMP2RAW]),
                    len(pools[VIEW_COMP2RAW_REJ]),
                    len(pools[VIEW_COMP2COMP]),
                )

        if not pools[VIEW_RAW2RAW]:
            return []

        # 根据各池可用样本量计算“可实现的最大总样本量”。
        feasible_total = min(
            int(len(pools[VIEW_RAW2RAW]) / target_ratio[VIEW_RAW2RAW]) if pools[VIEW_RAW2RAW] else 0,
            int(len(pools[VIEW_COMP2RAW]) / target_ratio[VIEW_COMP2RAW]) if pools[VIEW_COMP2RAW] else 0,
            int(len(pools[VIEW_COMP2RAW_REJ]) / target_ratio[VIEW_COMP2RAW_REJ]) if pools[VIEW_COMP2RAW_REJ] else 0,
            int(len(pools[VIEW_COMP2COMP]) / target_ratio[VIEW_COMP2COMP]) if pools[VIEW_COMP2COMP] else 0,
        )
        if feasible_total <= 0:
            logging.warning(
                "Insufficient compressed samples for 10/50/20/20. "
                "Falling back to raw2raw-only output."
            )
            return pools[VIEW_RAW2RAW]

        # 目标数按比例拆分，余数按最大比例优先补齐。
        desired_counts = {k: int(feasible_total * v) for k, v in target_ratio.items()}
        remainder = feasible_total - sum(desired_counts.values())
        fill_order = [VIEW_COMP2RAW, VIEW_COMP2RAW_REJ, VIEW_COMP2COMP, VIEW_RAW2RAW]
        while remainder > 0:
            for key in fill_order:
                desired_counts[key] += 1
                remainder -= 1
                if remainder <= 0:
                    break

        # 打乱池顺序后，用 while 循环按“剩余缺口概率”抽样接纳，直到达到目标总量。
        queue = {k: list(v) for k, v in pools.items()}
        for key in queue:
            self._rng.shuffle(queue[key])
        selected: list[dict[str, Any]] = []
        accepted_counts = {k: 0 for k in target_ratio}

        max_iter = max(1, feasible_total * 20)
        iters = 0
        while sum(accepted_counts.values()) < feasible_total and iters < max_iter:
            iters += 1
            deficits = {
                k: max(0, desired_counts[k] - accepted_counts[k])
                for k in target_ratio
            }
            total_deficit = sum(deficits.values())
            if total_deficit <= 0:
                break

            # 通过随机门控近似“概率拦截”：缺口越大，被选中的概率越高。
            pick = self._rng.uniform(0.0, float(total_deficit))
            cur = 0.0
            chosen = VIEW_COMP2RAW
            for key in (VIEW_RAW2RAW, VIEW_COMP2RAW, VIEW_COMP2RAW_REJ, VIEW_COMP2COMP):
                cur += float(deficits[key])
                if pick <= cur:
                    chosen = key
                    break
            if not queue[chosen]:
                continue
            row = queue[chosen].pop()
            selected.append(row)
            accepted_counts[chosen] += 1

        # 兜底：若随机门控没有正好填满，则按剩余缺口顺序补齐。
        for key in (VIEW_COMP2RAW, VIEW_COMP2RAW_REJ, VIEW_COMP2COMP, VIEW_RAW2RAW):
            need = max(0, desired_counts[key] - accepted_counts[key])
            if need <= 0:
                continue
            take = min(need, len(queue[key]))
            if take > 0:
                selected.extend(queue[key][:take])
                accepted_counts[key] += take
                queue[key] = queue[key][take:]

        self._rng.shuffle(selected)
        return selected


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def maybe_generate_mock_input(path: Path, n: int = 30) -> None:
    if path.exists():
        return
    logging.info("Input file not found. Creating mock input at %s", path)
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for i in range(n):
        rows.append(
            {
                "task_id": f"he_{i:03d}",
                "prompt": (
                    "def standard_deviation(val_list):\n"
                    "    total_count = len(val_list)\n"
                    "    if total_count == 0:\n"
                    "        return 0.0\n"
                ),
                "target": (
                    "    mean = sum(val_list) / len(val_list)\n"
                    "    variance = sum((x - mean) ** 2 for x in val_list) / len(val_list)\n"
                    "    return variance ** 0.5\n"
                ),
            }
        )
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input-file",
        type=Path,
        default=Path("raw_tasks.jsonl"),
        help="Raw task jsonl path.",
    )
    parser.add_argument(
        "--output-file",
        type=Path,
        default=Path("training_data.jsonl"),
        help="Output training jsonl path.",
    )
    parser.add_argument(
        "--max-samples",
        type=int,
        default=0,
        help="Max number of raw tasks to read. 0 means no limit.",
    )
    parser.add_argument(
        "--task-family",
        type=str,
        default="HumanEval",
        help="Task family label written to each row.",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument(
        "--hard-constraint-prefix",
        dest="hard_constraint_prefix",
        action="store_true",
        help="Inject output requirement at the beginning for compressed views.",
    )
    parser.add_argument(
        "--no-hard-constraint-prefix",
        dest="hard_constraint_prefix",
        action="store_false",
        help="Disable beginning-of-user hard output requirement injection.",
    )
    parser.set_defaults(hard_constraint_prefix=True)
    parser.add_argument(
        "--mock-size",
        type=int,
        default=30,
        help="Mock raw task size when input file is missing.",
    )
    return parser.parse_args()


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    args = parse_args()
    maybe_generate_mock_input(args.input_file, n=max(1, int(args.mock_size)))

    engine = MockCompressionEngine(seed=args.seed)
    generator = MultiViewDataGenerator(
        compression_engine=engine,
        task_family=args.task_family,
        seed=args.seed,
        hard_constraint_prefix=bool(args.hard_constraint_prefix),
    )

    max_samples = args.max_samples if args.max_samples > 0 else None
    tasks = generator.load_tasks(args.input_file, max_samples=max_samples)
    logging.info("Loaded %d tasks from %s", len(tasks), args.input_file)
    if not tasks:
        logging.error("No valid tasks found. Nothing generated.")
        return 1

    rows = generator.generate(tasks)
    write_jsonl(args.output_file, rows)

    cnt = Counter(str(x.get("view_type", "")) for x in rows)
    total = len(rows)
    logging.info("Wrote %d rows to %s", total, args.output_file)
    for view in (VIEW_RAW2RAW, VIEW_COMP2RAW, VIEW_COMP2RAW_REJ, VIEW_COMP2COMP):
        n = int(cnt.get(view, 0))
        pct = (n / total * 100.0) if total else 0.0
        logging.info("view=%s count=%d ratio=%.2f%%", view, n, pct)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
