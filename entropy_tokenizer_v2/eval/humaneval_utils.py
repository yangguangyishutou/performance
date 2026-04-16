"""Shared helpers for stage3ab HumanEval experiments."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence

from datasets import load_dataset

from config import CACHE_DIR, EVAL_TOKENIZERS, RESULTS_DIR, VOCAB_COST_MODE
from eval.langv1_dataset_utils import build_humaneval_structured_prompt
from eval.v2_eval import apply_v2_compression, load_eval_samples
from markers import RE_SYN_ONLY
from placeholder_accounting import (
    compute_vocab_intro_cost,
    count_base_tokens,
    count_sequence_tokens,
    dedupe_vocab_entries,
    serialize_vocab_entry,
)
from repo_miner import _load_tokenizer, collect_py_sources, mine_from_sources
from syntax_compressor import build_stage1_vocab_entry

DEFAULT_HUMANEVAL_DATASET = os.getenv("ET_HUMANEVAL_DATASET", "openai/openai_humaneval")
DEFAULT_HUMANEVAL_SPLIT = os.getenv("ET_HUMANEVAL_SPLIT", "test")
DEFAULT_SUPPORT_DATASET = os.getenv(
    "ET_HUMANEVAL_SUPPORT_DATASET",
    "",
).strip()
DEFAULT_SUPPORT_DATASET_SPLIT = os.getenv(
    "ET_HUMANEVAL_SUPPORT_DATASET_SPLIT",
    "train",
).strip()
DEFAULT_SUPPORT_TEXT_FIELD = os.getenv(
    "ET_HUMANEVAL_SUPPORT_TEXT_FIELD",
    "content",
).strip()
DEFAULT_SUPPORT_LIMIT = int(os.getenv("ET_HUMANEVAL_SUPPORT_LIMIT", "1200"))
DEFAULT_SUPPORT_TOP_K = int(os.getenv("ET_HUMANEVAL_SUPPORT_TOP_K", "4"))
DEFAULT_SNIPPET_MAX_CHARS = int(os.getenv("ET_HUMANEVAL_SNIPPET_MAX_CHARS", "1200"))
DEFAULT_STAGE2_PROFILE = os.getenv("ET_HUMANEVAL_STAGE2_PROFILE", "").strip() or None
DEFAULT_STAGE2_MODE = os.getenv("ET_HUMANEVAL_STAGE2_MODE", "").strip() or None
DEFAULT_COMPRESSION_TOKENIZER = os.getenv("ET_HUMANEVAL_COMPRESSION_TOKENIZER", "gpt4")
HUMANEVAL_RESULTS_DIR = Path(
    os.getenv("ET_HUMANEVAL_RESULTS_DIR", str(RESULTS_DIR / "humaneval"))
)

_WORD_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]+")
_COMMON_STOPWORDS = {
    "a",
    "an",
    "and",
    "args",
    "as",
    "be",
    "by",
    "class",
    "code",
    "def",
    "false",
    "for",
    "from",
    "function",
    "if",
    "in",
    "input",
    "is",
    "it",
    "list",
    "none",
    "not",
    "of",
    "or",
    "python",
    "return",
    "returns",
    "self",
    "string",
    "test",
    "that",
    "the",
    "to",
    "true",
    "value",
    "with",
}

PROMPT_PREAMBLE = (
    "You are solving a Python HumanEval function-completion task.\n"
    "Return only the Python continuation that should be appended immediately after the task prompt.\n"
    "Do not repeat the task prompt.\n"
    "Do not add markdown fences.\n"
    "Do not explain your answer."
)


@dataclass(slots=True)
class HumanEvalTask:
    task_id: str
    prompt: str
    entry_point: str
    canonical_solution: str = ""
    test: str = ""


@dataclass(slots=True)
class SupportSnippet:
    snippet_id: str
    source_id: str
    rank_hint: int
    text: str
    score: float = 0.0


@dataclass(slots=True)
class PreparedTaskRecord:
    task_id: str
    entry_point: str
    task_prompt: str
    compression_tokenizer_key: str
    stage3_backend: str
    stage3_ab_mode: str
    prompt_style: str
    stage2_profile: str | None
    stage2_mode: str | None
    support_ids: list[str]
    raw_support_text: str
    compressed_support_text: str
    codebook_entries: list[dict[str, Any]]
    codebook_text: str
    prompt_raw: str
    prompt_compressed: str
    raw_context_tokens: int
    compressed_context_sequence_tokens: int
    compressed_codebook_tokens: int
    compressed_context_effective_tokens: int
    metrics: dict[str, Any]


def _tokenize_words(text: str) -> list[str]:
    return [
        w.lower()
        for w in _WORD_RE.findall(text or "")
        if len(w) >= 2 and w.lower() not in _COMMON_STOPWORDS
    ]


def _query_weights(task: HumanEvalTask) -> dict[str, int]:
    out: dict[str, int] = {}
    for token in _tokenize_words(task.prompt):
        out[token] = out.get(token, 0) + 1
    for token in _tokenize_words(task.entry_point.replace("_", " ")):
        out[token] = out.get(token, 0) + 3
    return out


def _snippet_score(task: HumanEvalTask, text: str) -> float:
    q = _query_weights(task)
    if not q:
        return 0.0
    words = _tokenize_words(text)
    if not words:
        return 0.0
    counts: dict[str, int] = {}
    for w in words:
        counts[w] = counts.get(w, 0) + 1
    overlap = sum(min(weight, counts.get(term, 0)) for term, weight in q.items())
    direct_entry_match = 5.0 if task.entry_point and task.entry_point in text else 0.0
    return (overlap + direct_entry_match) / math.sqrt(len(counts) + 8.0)


def split_source_into_snippets(
    source: str,
    *,
    source_id: str,
    max_chars: int = DEFAULT_SNIPPET_MAX_CHARS,
) -> list[SupportSnippet]:
    lines = source.splitlines()
    if not lines:
        return []
    snippets: list[SupportSnippet] = []
    buf: list[str] = []
    buf_len = 0
    chunk_idx = 0
    for line in lines:
        extra = len(line) + 1
        if buf and buf_len + extra > max_chars:
            text = "\n".join(buf).strip()
            if text:
                snippets.append(
                    SupportSnippet(
                        snippet_id=f"{source_id}::chunk{chunk_idx}",
                        source_id=source_id,
                        rank_hint=chunk_idx,
                        text=text,
                    )
                )
                chunk_idx += 1
            overlap = buf[-3:] if len(buf) > 3 else buf[:]
            buf = overlap + [line]
            buf_len = sum(len(x) + 1 for x in buf)
            continue
        buf.append(line)
        buf_len += extra
    text = "\n".join(buf).strip()
    if text:
        snippets.append(
            SupportSnippet(
                snippet_id=f"{source_id}::chunk{chunk_idx}",
                source_id=source_id,
                rank_hint=chunk_idx,
                text=text,
            )
        )
    return snippets


def load_humaneval_tasks(
    *,
    dataset_name: str = DEFAULT_HUMANEVAL_DATASET,
    split: str = DEFAULT_HUMANEVAL_SPLIT,
    jsonl_path: str | Path | None = None,
    limit: int | None = None,
    task_ids: Sequence[str] | None = None,
) -> list[HumanEvalTask]:
    wanted = {x.strip() for x in task_ids or [] if x and x.strip()}
    if jsonl_path:
        fp = Path(jsonl_path)
        tasks: list[HumanEvalTask] = []
        with fp.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                row = json.loads(line)
                task = HumanEvalTask(
                    task_id=str(row["task_id"]),
                    prompt=str(row["prompt"]),
                    entry_point=str(row["entry_point"]),
                    canonical_solution=str(row.get("canonical_solution", "")),
                    test=str(row.get("test", "")),
                )
                if wanted and task.task_id not in wanted:
                    continue
                tasks.append(task)
                if limit is not None and len(tasks) >= limit:
                    break
        return tasks

    ds = load_dataset(dataset_name, split=split)
    tasks: list[HumanEvalTask] = []
    for row in ds:
        task = HumanEvalTask(
            task_id=str(row["task_id"]),
            prompt=str(row["prompt"]),
            entry_point=str(row["entry_point"]),
            canonical_solution=str(row.get("canonical_solution", "")),
            test=str(row.get("test", "")),
        )
        if wanted and task.task_id not in wanted:
            continue
        tasks.append(task)
        if limit is not None and len(tasks) >= limit:
            break
    return tasks


def load_support_snippets(
    *,
    repo_path: str | None = None,
    jsonl_path: str | None = None,
    dataset_name: str | None = None,
    dataset_split: str = DEFAULT_SUPPORT_DATASET_SPLIT,
    text_field: str = DEFAULT_SUPPORT_TEXT_FIELD,
    limit: int = DEFAULT_SUPPORT_LIMIT,
    snippet_max_chars: int = DEFAULT_SNIPPET_MAX_CHARS,
) -> list[SupportSnippet]:
    snippets: list[SupportSnippet] = []
    if repo_path:
        for idx, source in enumerate(collect_py_sources(repo_path)[:limit]):
            snippets.extend(
                split_source_into_snippets(
                    source,
                    source_id=f"repo:{idx}",
                    max_chars=snippet_max_chars,
                )
            )
        return snippets

    if jsonl_path:
        fp = Path(jsonl_path)
        with fp.open("r", encoding="utf-8") as f:
            for idx, line in enumerate(f):
                if idx >= limit:
                    break
                row = json.loads(line)
                text = str(row.get(text_field) or row.get("content") or row.get("text") or "")
                if not text:
                    continue
                snippets.extend(
                    split_source_into_snippets(
                        text,
                        source_id=f"jsonl:{idx}",
                        max_chars=snippet_max_chars,
                    )
                )
        return snippets

    ds_name = dataset_name or DEFAULT_SUPPORT_DATASET
    if ds_name:
        ds = load_dataset(ds_name, split=dataset_split)
        for idx, row in enumerate(ds):
            if idx >= limit:
                break
            text = str(row.get(text_field) or row.get("content") or row.get("text") or "")
            if not text:
                continue
            snippets.extend(
                split_source_into_snippets(
                    text,
                    source_id=f"hf:{idx}",
                    max_chars=snippet_max_chars,
                )
            )
        return snippets

    for idx, source in enumerate(load_eval_samples(limit)):
        snippets.extend(
            split_source_into_snippets(
                source,
                source_id=f"fallback:{idx}",
                max_chars=snippet_max_chars,
            )
        )
    return snippets


def retrieve_support_snippets(
    task: HumanEvalTask,
    corpus: Sequence[SupportSnippet],
    *,
    top_k: int = DEFAULT_SUPPORT_TOP_K,
) -> list[SupportSnippet]:
    scored: list[SupportSnippet] = []
    for item in corpus:
        scored.append(
            SupportSnippet(
                snippet_id=item.snippet_id,
                source_id=item.source_id,
                rank_hint=item.rank_hint,
                text=item.text,
                score=_snippet_score(task, item.text),
            )
        )
    scored.sort(key=lambda x: (-x.score, x.source_id, x.rank_hint))
    return scored[:top_k]


def _render_support_blocks(snippets: Sequence[str], *, compressed: bool) -> str:
    blocks: list[str] = []
    label = "Compressed Support" if compressed else "Support"
    for idx, text in enumerate(snippets, start=1):
        blocks.append(f"# [{label} {idx}]\n{text.rstrip()}")
    return "\n\n".join(blocks).strip()


def _extract_used_stage1_entries(
    compressed_texts: Sequence[str],
    repo_config: Any,
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    cands = list(repo_config.skeleton_candidates())
    for text in compressed_texts:
        for match in RE_SYN_ONLY.finditer(text):
            marker = match.group(0)
            try:
                idx = int(marker[len("<SYN_") : -1])
            except ValueError:
                continue
            if idx < 0 or idx >= len(cands):
                continue
            key = (marker, cands[idx].skeleton)
            if key in seen:
                continue
            seen.add(key)
            entries.append(build_stage1_vocab_entry(marker, cands[idx].skeleton))
    return entries


def _extract_stage3_entries(breakdowns: Sequence[Any]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for bd in breakdowns:
        metrics = dict(getattr(bd, "stage3_metrics", {}) or {})
        rows = metrics.get("stage3_ab_vocab_entries", []) or metrics.get("stage3_vocab_entries", []) or []
        for row in rows:
            if isinstance(row, dict):
                entries.append(dict(row))
    return entries


def build_codebook_entries(
    compressed_texts: Sequence[str],
    breakdowns: Sequence[Any],
    repo_config: Any,
    *,
    include_stage1: bool = True,
    include_stage3: bool = True,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if include_stage1:
        rows.extend(_extract_used_stage1_entries(compressed_texts, repo_config))
    if include_stage3:
        rows.extend(_extract_stage3_entries(breakdowns))
    return dedupe_vocab_entries(rows)


def render_codebook_text(entries: Sequence[dict[str, Any]]) -> str:
    if not entries:
        return ""
    return "\n".join(serialize_vocab_entry(e) for e in entries)


def build_prompt_text(
    task: HumanEvalTask,
    *,
    support_text: str,
    compressed: bool,
    codebook_text: str = "",
    prompt_style: str = "legacy",
) -> str:
    if str(prompt_style).strip().lower() == "structured":
        return build_humaneval_structured_prompt(
            support_text=support_text,
            compressed=compressed,
            dynamic_dict_text=codebook_text,
            task_prompt=task.prompt,
        )
    parts = [PROMPT_PREAMBLE]
    if compressed:
        if codebook_text:
            parts.append(f"Compression dictionary:\n{codebook_text}")
        if support_text:
            parts.append(f"Compressed support context:\n{support_text}")
    else:
        if support_text:
            parts.append(f"Support context:\n{support_text}")
    parts.append(f"Task prompt:\n{task.prompt}")
    return "\n\n".join(x for x in parts if x).rstrip() + "\n"


def _sum_metric(breakdowns: Sequence[Any], key: str) -> int:
    total = 0
    for bd in breakdowns:
        metrics = dict(getattr(bd, "stage3_metrics", {}) or {})
        try:
            total += int(metrics.get(key, 0) or 0)
        except (TypeError, ValueError):
            continue
    return total


def _config_cache_name(task: HumanEvalTask, support_texts: Sequence[str], tokenizer_key: str) -> str:
    h = hashlib.sha1()
    h.update(task.task_id.encode("utf-8"))
    h.update(tokenizer_key.encode("utf-8"))
    for text in support_texts:
        h.update(text.encode("utf-8", errors="replace"))
        h.update(b"\n--\n")
    return f"humaneval_{task.task_id.replace('/', '_')}_{h.hexdigest()[:12]}"


@contextmanager
def temporary_stage3ab_env(*, mode: str, enable_b: bool) -> Iterable[None]:
    saved_mode = os.environ.get("ET_STAGE3_AB_MODE")
    saved_b = os.environ.get("ET_STAGE3_AB_ENABLE_B")
    try:
        os.environ["ET_STAGE3_AB_MODE"] = mode
        os.environ["ET_STAGE3_AB_ENABLE_B"] = "1" if enable_b else "0"
        yield
    finally:
        if saved_mode is None:
            os.environ.pop("ET_STAGE3_AB_MODE", None)
        else:
            os.environ["ET_STAGE3_AB_MODE"] = saved_mode
        if saved_b is None:
            os.environ.pop("ET_STAGE3_AB_ENABLE_B", None)
        else:
            os.environ["ET_STAGE3_AB_ENABLE_B"] = saved_b


def prepare_task_record(
    task: HumanEvalTask,
    support_hits: Sequence[SupportSnippet],
    *,
    compression_tokenizer_key: str = DEFAULT_COMPRESSION_TOKENIZER,
    stage3_backend: str = "hybrid_ab",
    stage3_ab_mode: str = "exact_only",
    enable_b: bool = False,
    prompt_style: str = "legacy",
    stage2_profile: str | None = DEFAULT_STAGE2_PROFILE,
    stage2_mode: str | None = DEFAULT_STAGE2_MODE,
    cache_repo_config: bool = True,
) -> PreparedTaskRecord:
    cfg = EVAL_TOKENIZERS[compression_tokenizer_key]
    tokenizer, tok_type = _load_tokenizer(compression_tokenizer_key, cfg)
    raw_texts = [x.text for x in support_hits]
    cache_name = _config_cache_name(task, raw_texts, compression_tokenizer_key)

    with temporary_stage3ab_env(mode=stage3_ab_mode, enable_b=enable_b):
        repo_config = mine_from_sources(
            raw_texts,
            tokenizer_key=compression_tokenizer_key,
            tokenizer_cfg=cfg,
            cache=cache_repo_config,
            cache_name=cache_name,
            verbose=False,
            min_freq=1,
            stage3_backend=stage3_backend,
        )
        compressed_texts: list[str] = []
        breakdowns: list[Any] = []
        for text in raw_texts:
            comp, bd = apply_v2_compression(
                text,
                repo_config,
                tokenizer,
                tok_type,
                stage2_profile=stage2_profile,
                stage2_mode=stage2_mode,
            )
            compressed_texts.append(comp)
            breakdowns.append(bd)

    include_stage1_entries = str(prompt_style).strip().lower() != "structured"
    codebook_entries = build_codebook_entries(
        compressed_texts,
        breakdowns,
        repo_config,
        include_stage1=include_stage1_entries,
        include_stage3=True,
    )
    codebook_text = render_codebook_text(codebook_entries)
    raw_support_text = _render_support_blocks(raw_texts, compressed=False)
    compressed_support_text = _render_support_blocks(compressed_texts, compressed=True)
    prompt_raw = build_prompt_text(
        task,
        support_text=raw_support_text,
        compressed=False,
        prompt_style=prompt_style,
    )
    prompt_compressed = build_prompt_text(
        task,
        support_text=compressed_support_text,
        compressed=True,
        codebook_text=codebook_text,
        prompt_style=prompt_style,
    )

    raw_context_tokens = count_base_tokens(
        raw_support_text,
        tokenizer=tokenizer,
        tok_type=tok_type,
    )
    compressed_context_sequence_tokens = count_sequence_tokens(
        compressed_support_text,
        tokenizer=tokenizer,
        tok_type=tok_type,
    )
    compressed_codebook_tokens = compute_vocab_intro_cost(
        codebook_entries,
        mode=VOCAB_COST_MODE,
        tokenizer=tokenizer,
        tok_type=tok_type,
    )
    metrics = {
        "n_support_snippets": len(support_hits),
        "stage3_ab_mode": stage3_ab_mode,
        "raw_context_tokens": raw_context_tokens,
        "compressed_context_sequence_tokens": compressed_context_sequence_tokens,
        "compressed_codebook_tokens": compressed_codebook_tokens,
        "compressed_context_effective_tokens": compressed_context_sequence_tokens + compressed_codebook_tokens,
        "stage3_ab_a_sequence_saved": _sum_metric(breakdowns, "stage3_ab_a_sequence_saved"),
        "stage3_ab_b_sequence_saved": _sum_metric(breakdowns, "stage3_ab_b_sequence_saved"),
        "stage3_ab_a_intro_tokens": _sum_metric(breakdowns, "stage3_ab_a_intro_tokens"),
        "stage3_ab_b_intro_tokens": _sum_metric(breakdowns, "stage3_ab_b_intro_tokens"),
        "stage3_ab_fallback_count": _sum_metric(breakdowns, "stage3_ab_fallback_count"),
        "stage3_ab_b_route_reject_count": _sum_metric(breakdowns, "stage3_ab_b_route_reject_count"),
        "stage3_ab_telemetry_guardrail_triggered_nfiles": _sum_metric(
            breakdowns,
            "stage3_guardrail_triggered",
        ),
    }
    return PreparedTaskRecord(
        task_id=task.task_id,
        entry_point=task.entry_point,
        task_prompt=task.prompt,
        compression_tokenizer_key=compression_tokenizer_key,
        stage3_backend=stage3_backend,
        stage3_ab_mode=stage3_ab_mode,
        prompt_style=prompt_style,
        stage2_profile=stage2_profile,
        stage2_mode=stage2_mode,
        support_ids=[x.snippet_id for x in support_hits],
        raw_support_text=raw_support_text,
        compressed_support_text=compressed_support_text,
        codebook_entries=codebook_entries,
        codebook_text=codebook_text,
        prompt_raw=prompt_raw,
        prompt_compressed=prompt_compressed,
        raw_context_tokens=raw_context_tokens,
        compressed_context_sequence_tokens=compressed_context_sequence_tokens,
        compressed_codebook_tokens=compressed_codebook_tokens,
        compressed_context_effective_tokens=compressed_context_sequence_tokens + compressed_codebook_tokens,
        metrics=metrics,
    )


def record_to_dict(record: PreparedTaskRecord) -> dict[str, Any]:
    return asdict(record)


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    fp = Path(path)
    rows: list[dict[str, Any]] = []
    with fp.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def default_prepare_output_path(tag: str = "") -> Path:
    HUMANEVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{tag}" if tag else ""
    return HUMANEVAL_RESULTS_DIR / f"prepared_stage3ab{suffix}.jsonl"


def default_samples_output_path(*, arm: str, backend: str, tag: str = "") -> Path:
    HUMANEVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{tag}" if tag else ""
    return HUMANEVAL_RESULTS_DIR / f"samples_{arm}_{backend}{suffix}.jsonl"


def default_details_output_path(*, arm: str, backend: str, tag: str = "") -> Path:
    HUMANEVAL_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{tag}" if tag else ""
    return HUMANEVAL_RESULTS_DIR / f"generation_{arm}_{backend}{suffix}.jsonl"
