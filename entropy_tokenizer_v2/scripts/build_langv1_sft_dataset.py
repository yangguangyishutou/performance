"""Build a synthetic prompt/completion SFT dataset for the LangV1 pilot."""

from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS  # noqa: E402
from eval.humaneval_utils import (  # noqa: E402
    build_codebook_entries,
    render_codebook_text,
    temporary_stage3ab_env,
)
from eval.langv1_dataset_utils import build_sft_prompt, split_prefix_completion  # noqa: E402
from eval.v2_eval import apply_v2_compression  # noqa: E402
from marker_count import encode as mc_encode  # noqa: E402
from repo_miner import _load_tokenizer, mine_from_sources  # noqa: E402


def _load_corpus(jsonl_path: Path, limit: int | None) -> list[str]:
    rows: list[str] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            text = str(obj.get("text", "")).strip()
            if not text:
                continue
            rows.append(text)
            if limit is not None and len(rows) >= limit:
                break
    return rows


def _parse_modes(raw: str) -> list[str]:
    allowed = {"compressed_to_compressed", "raw_to_compressed"}
    modes = [part.strip().lower() for part in str(raw or "").split(",") if part.strip()]
    if not modes:
        raise ValueError("empty prompt modes")
    invalid = [mode for mode in modes if mode not in allowed]
    if invalid:
        raise ValueError(f"unsupported prompt modes: {', '.join(invalid)}")
    return modes


@contextmanager
def _temporary_global_dict_env(path: str | None, *, enabled: bool, charge_vocab: bool) -> None:
    saved_enable = os.environ.get("ET_STAGE3_AB_GLOBAL_DICT_ENABLE")
    saved_path = os.environ.get("ET_STAGE3_AB_GLOBAL_DICT_PATH")
    saved_charge = os.environ.get("ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB")
    try:
        os.environ["ET_STAGE3_AB_GLOBAL_DICT_ENABLE"] = "1" if enabled else "0"
        if path:
            os.environ["ET_STAGE3_AB_GLOBAL_DICT_PATH"] = str(path)
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


def _count_tokens(tokenizer, tok_type: str, text: str) -> int:
    return len(mc_encode(tokenizer, tok_type, text))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=ROOT / "cache" / "stage1_starcoder_1m_corpus.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "results" / "langv1_pilot" / "langv1_sft_dataset.jsonl",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=ROOT / "results" / "langv1_pilot" / "langv1_sft_dataset.summary.json",
    )
    parser.add_argument("--limit", type=int, default=128)
    parser.add_argument("--compression-tokenizer", default="qwen25-coder-15b")
    parser.add_argument("--stage2-profile", default="stage2_parseable")
    parser.add_argument("--stage2-mode", default="blockwise")
    parser.add_argument("--stage3-backend", default="hybrid_ab")
    parser.add_argument("--stage3-ab-mode", default="exact_only", choices=("exact_only", "hybrid"))
    parser.add_argument("--enable-b", action="store_true")
    parser.add_argument("--global-dict", type=Path, default=None)
    parser.add_argument("--global-dict-charge-vocab", action="store_true")
    parser.add_argument("--prompt-modes", default="compressed_to_compressed")
    parser.add_argument("--prompt-ratio", type=float, default=0.6)
    parser.add_argument("--min-prompt-chars", type=int, default=192)
    parser.add_argument("--min-completion-chars", type=int, default=96)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    tok_cfg = EVAL_TOKENIZERS[args.compression_tokenizer]
    tokenizer, tok_type = _load_tokenizer(args.compression_tokenizer, tok_cfg)
    sources = _load_corpus(args.corpus, args.limit)
    modes = _parse_modes(args.prompt_modes)
    if not sources:
        raise SystemExit(f"empty corpus: {args.corpus}")
    if args.output.exists() and not args.overwrite:
        raise SystemExit(f"output exists: {args.output} (pass --overwrite to replace)")

    kept_sources = 0
    failures = 0
    n_examples = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with _temporary_global_dict_env(
        str(args.global_dict) if args.global_dict else None,
        enabled=bool(args.global_dict),
        charge_vocab=bool(args.global_dict_charge_vocab),
    ):
        with temporary_stage3ab_env(mode=args.stage3_ab_mode, enable_b=bool(args.enable_b)):
            with args.output.open("w", encoding="utf-8") as f:
                for idx, text in enumerate(sources, start=1):
                    try:
                        prefix_raw, completion_raw = split_prefix_completion(
                            text,
                            prompt_ratio=float(args.prompt_ratio),
                            min_prompt_chars=int(args.min_prompt_chars),
                            min_completion_chars=int(args.min_completion_chars),
                        )
                        repo_config = mine_from_sources(
                            [text],
                            tokenizer_key=args.compression_tokenizer,
                            tokenizer_cfg=tok_cfg,
                            cache=False,
                            cache_name=f"langv1_sft_{args.compression_tokenizer}_{idx}",
                            verbose=False,
                            min_freq=1,
                            stage3_backend=args.stage3_backend,
                        )
                        prefix_comp, bd_prefix = apply_v2_compression(
                            prefix_raw,
                            repo_config,
                            tokenizer,
                            tok_type,
                            stage2_profile=args.stage2_profile,
                            stage2_mode=args.stage2_mode,
                        )
                        completion_comp, bd_completion = apply_v2_compression(
                            completion_raw,
                            repo_config,
                            tokenizer,
                            tok_type,
                            stage2_profile=args.stage2_profile,
                            stage2_mode=args.stage2_mode,
                        )
                        entries = build_codebook_entries(
                            [prefix_comp, completion_comp],
                            [bd_prefix, bd_completion],
                            repo_config,
                            include_stage1=False,
                            include_stage3=True,
                        )
                        dynamic_dict_text = render_codebook_text(entries)
                        for mode in modes:
                            prefix_text = prefix_comp if mode == "compressed_to_compressed" else prefix_raw
                            row = {
                                "source_index": idx - 1,
                                "mode": mode,
                                "prompt": build_sft_prompt(
                                    prefix_text,
                                    prompt_mode=mode,
                                    dynamic_dict_text=dynamic_dict_text,
                                ),
                                "completion": completion_comp,
                                "raw_prefix_chars": len(prefix_raw),
                                "raw_completion_chars": len(completion_raw),
                                "compressed_prefix_chars": len(prefix_comp),
                                "compressed_completion_chars": len(completion_comp),
                                "raw_prefix_tokens": _count_tokens(tokenizer, tok_type, prefix_raw),
                                "compressed_prefix_tokens": _count_tokens(tokenizer, tok_type, prefix_comp),
                                "compressed_completion_tokens": _count_tokens(tokenizer, tok_type, completion_comp),
                                "codebook_entries": len(entries),
                            }
                            f.write(json.dumps(row, ensure_ascii=False) + "\n")
                            f.flush()
                            n_examples += 1
                        kept_sources += 1
                    except Exception as exc:
                        failures += 1
                        print(f"[skip] {idx}/{len(sources)} {type(exc).__name__}: {exc}")
                        continue
                    if idx % 25 == 0 or idx == len(sources):
                        print(
                            f"[build] {idx}/{len(sources)} "
                            f"sources={kept_sources} examples={n_examples} failed={failures}"
                        )

    summary = {
        "corpus": str(args.corpus),
        "output": str(args.output),
        "n_sources": kept_sources,
        "n_examples": n_examples,
        "failures": failures,
        "compression_tokenizer": args.compression_tokenizer,
        "stage2_profile": args.stage2_profile,
        "stage2_mode": args.stage2_mode,
        "stage3_backend": args.stage3_backend,
        "stage3_ab_mode": args.stage3_ab_mode,
        "enable_b": bool(args.enable_b),
        "global_dict": str(args.global_dict) if args.global_dict else "",
        "global_dict_charge_vocab": bool(args.global_dict_charge_vocab),
        "prompt_modes": modes,
        "prompt_ratio": float(args.prompt_ratio),
        "min_prompt_chars": int(args.min_prompt_chars),
        "min_completion_chars": int(args.min_completion_chars),
    }
    args.summary_output.parent.mkdir(parents=True, exist_ok=True)
    args.summary_output.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(args.output)
    print(args.summary_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
