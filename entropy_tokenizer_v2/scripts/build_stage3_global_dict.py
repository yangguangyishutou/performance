"""Build a cross-file static global dictionary for Stage3 hybrid_ab."""

from __future__ import annotations

import argparse
import ast
import builtins
import io
import json
import keyword
import os
import sys
import tokenize
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from config import EVAL_TOKENIZERS, resolve_hybrid_ab_settings  # noqa: E402
from marker_count import encode as mc_encode  # noqa: E402
from repo_miner import _load_tokenizer  # noqa: E402
from stage3.literal_codec.alias_pool import build_legal_alias_alphabet  # noqa: E402
from stage3.lexical.semantic_codec import _normalize_for_similarity  # noqa: E402
from stage3.routing.router import ABRoutingConfig, classify_string_with_reason  # noqa: E402

_PROTECTED = set(keyword.kwlist) | set(dir(builtins)) | {"self", "cls", "True", "False", "None"}
_BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_PRESETS: dict[str, dict[str, object]] = {
    "default": {},
    "qwen_small": {
        "tokenizer": "qwen25-coder-15b",
        "a_min_occ": 8,
        "b_min_occ": 10**9,
        "a_max_entries": 128,
        "b_max_entries": 0,
        "a_prefix": "q",
        "b_prefix": "qb",
    },
    "qwen_medium": {
        "tokenizer": "qwen25-coder-15b",
        "a_min_occ": 6,
        "b_min_occ": 10**9,
        "a_max_entries": 256,
        "b_max_entries": 0,
        "a_prefix": "q",
        "b_prefix": "qb",
    },
}


def _base62(num: int) -> str:
    n = int(num)
    if n <= 0:
        return "0"
    out: list[str] = []
    base = len(_BASE62_ALPHABET)
    while n > 0:
        n, rem = divmod(n, base)
        out.append(_BASE62_ALPHABET[rem])
    out.reverse()
    return "".join(out)


def _apply_preset(args: argparse.Namespace) -> argparse.Namespace:
    preset = str(getattr(args, "preset", "default") or "default").strip().lower()
    payload = dict(_PRESETS.get(preset, {}))
    if not payload:
        return args
    for key, value in payload.items():
        setattr(args, key, value)
    args.preset = preset
    return args


def _token_len(tokenizer, tok_type: str, text: str) -> int:
    return len(mc_encode(tokenizer, tok_type, text))


def _load_sources(jsonl_path: Path) -> list[str]:
    out: list[str] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            text = obj.get("text", "")
            if isinstance(text, str) and text:
                out.append(text)
    return out


def build_global_dictionary(
    *,
    sources: list[str],
    tokenizer,
    tok_type: str,
    tokenizer_key: str,
    a_min_occ: int,
    b_min_occ: int,
    a_max_entries: int,
    b_max_entries: int,
    a_prefix: str,
    b_prefix: str,
) -> dict:
    ab = resolve_hybrid_ab_settings(tokenizer_key)
    route_cfg = ABRoutingConfig(
        free_text_min_chars=int(ab.get("free_text_min_chars", 24)),
        free_text_min_words=int(ab.get("free_text_min_words", 4)),
        fallback_unknown=True,
        key_like_patterns=tuple(ab.get("key_like_patterns", []) or ()),
        short_string_policy=str(ab.get("short_string_policy", "exact_candidate")),
        enable_mid_free_text=bool(ab.get("enable_mid_free_text", False)),
        free_text_mid_min_chars=int(ab.get("free_text_mid_min_chars", 14)),
        free_text_mid_min_words=int(ab.get("free_text_mid_min_words", 3)),
        allow_multiline_whitelist=bool(ab.get("allow_multiline_whitelist", False)),
        multiline_max_lines=int(ab.get("multiline_max_lines", 3)),
        multiline_max_chars=int(ab.get("multiline_max_chars", 220)),
    )
    similarity_norm = str(ab.get("b_similarity_norm", "light") or "light")

    a_counts: Counter[tuple[str, str]] = Counter()
    b_counts: Counter[str] = Counter()
    b_rep_spelling: dict[str, str] = {}
    b_rep_inner: dict[str, str] = {}

    for text in sources:
        try:
            toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
        except (tokenize.TokenError, IndentationError, SyntaxError):
            continue
        prev_is_dot = False
        for tok in toks:
            ttype, tstr = tok.type, tok.string
            if ttype == tokenize.NAME:
                if tstr in _PROTECTED:
                    prev_is_dot = False
                    continue
                field = "attribute" if prev_is_dot else "variable"
                a_counts[(field, tstr)] += 1
                prev_is_dot = False
                continue
            if ttype == tokenize.STRING:
                route, _reason = classify_string_with_reason(tstr, route_cfg)
                if route == "A":
                    a_counts[("string", tstr)] += 1
                elif route == "B":
                    try:
                        inner = ast.literal_eval(tstr)
                    except (SyntaxError, ValueError, MemoryError):
                        inner = None
                    if isinstance(inner, str) and inner:
                        norm = _normalize_for_similarity(inner, similarity_norm)
                        if norm:
                            b_counts[norm] += 1
                            prev_rep = b_rep_spelling.get(norm)
                            if (
                                prev_rep is None
                                or _token_len(tokenizer, tok_type, tstr)
                                < _token_len(tokenizer, tok_type, prev_rep)
                            ):
                                b_rep_spelling[norm] = tstr
                                b_rep_inner[norm] = inner
                prev_is_dot = False
                continue
            if ttype == tokenize.OP:
                prev_is_dot = tstr == "."
            else:
                prev_is_dot = False

    a_candidates: list[tuple[str, str, int, int]] = []
    for (field, literal), cnt in a_counts.items():
        if cnt < int(a_min_occ):
            continue
        raw_cost = _token_len(tokenizer, tok_type, literal)
        a_candidates.append((field, literal, cnt, raw_cost))
    a_candidates.sort(key=lambda x: (-(x[2] * x[3]), -x[2], -x[3], x[0], x[1]))

    a_entries: list[dict] = []
    alias_pool = build_legal_alias_alphabet(
        tokenizer,
        tok_type,
        reserved=_PROTECTED,
        max_n=max(int(a_max_entries) * 12, 2048),
        max_alias_token_len=2 if str(tokenizer_key).strip().lower() == "gpt4" else 32,
    )
    a_idx = 0
    for field, literal, cnt, raw_cost in a_candidates:
        if len(a_entries) >= int(a_max_entries):
            break
        if a_idx >= len(alias_pool):
            break
        alias = str(alias_pool[a_idx])
        a_idx += 1
        surface = alias if field != "string" else repr(alias)
        alias_cost = _token_len(tokenizer, tok_type, surface)
        potential_saved = cnt * (raw_cost - alias_cost)
        if potential_saved <= 0:
            continue
        a_entries.append(
            {
                "field": field,
                "literal": literal,
                "alias": alias,
                "count": int(cnt),
                "raw_cost": int(raw_cost),
                "alias_cost": int(alias_cost),
                "potential_saved": int(potential_saved),
            }
        )

    b_candidates: list[tuple[str, int, int]] = []
    for norm_key, cnt in b_counts.items():
        if cnt < int(b_min_occ):
            continue
        rep = b_rep_spelling.get(norm_key)
        if not rep:
            continue
        raw_cost = _token_len(tokenizer, tok_type, rep)
        b_candidates.append((norm_key, cnt, raw_cost))
    b_candidates.sort(key=lambda x: (-(x[1] * x[2]), -x[1], -x[2], x[0]))

    b_entries: list[dict] = []
    b_idx = 0
    for norm_key, cnt, raw_cost in b_candidates:
        if len(b_entries) >= int(b_max_entries):
            break
        code = f"{b_prefix}{_base62(b_idx)}"
        b_idx += 1
        code_cost = _token_len(tokenizer, tok_type, repr(code))
        potential_saved = cnt * (raw_cost - code_cost)
        if potential_saved <= 0:
            continue
        b_entries.append(
            {
                "norm_key": norm_key,
                "code": code,
                "definition": b_rep_inner.get(norm_key, norm_key),
                "count": int(cnt),
                "raw_cost": int(raw_cost),
                "code_cost": int(code_cost),
                "potential_saved": int(potential_saved),
            }
        )

    return {
        "version": "stage3_global_dict_v1",
        "source": "cross_file_mining",
        "tokenizer_key": tokenizer_key,
        "summary": {
            "n_sources": len(sources),
            "a_entries": len(a_entries),
            "b_entries": len(b_entries),
            "a_min_occ": int(a_min_occ),
            "b_min_occ": int(b_min_occ),
            "a_max_entries": int(a_max_entries),
            "b_max_entries": int(b_max_entries),
            "a_prefix": a_prefix,
            "b_prefix": b_prefix,
        },
        "a_entries": a_entries,
        "b_entries": b_entries,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        type=str,
        default=str(ROOT / "cache" / "stage1_starcoder_1m_corpus.jsonl"),
        help="JSONL corpus with {'text': ...} rows.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "cache" / "stage3_global_dictionary.json"),
        help="Output global dictionary JSON path.",
    )
    parser.add_argument(
        "--preset",
        type=str,
        default="default",
        choices=tuple(_PRESETS.keys()),
        help="Optional learned-language preset for tokenizer + vocabulary size.",
    )
    parser.add_argument("--tokenizer", type=str, default="gpt4")
    parser.add_argument("--a-min-occ", type=int, default=24)
    parser.add_argument("--b-min-occ", type=int, default=12)
    parser.add_argument("--a-max-entries", type=int, default=6000)
    parser.add_argument("--b-max-entries", type=int, default=2500)
    parser.add_argument("--a-prefix", type=str, default="g")
    parser.add_argument("--b-prefix", type=str, default="gb")
    args = parser.parse_args()
    args = _apply_preset(args)

    tok_key = str(args.tokenizer).strip()
    tok_cfg = EVAL_TOKENIZERS.get(tok_key)
    if tok_cfg is None:
        raise SystemExit(f"unknown tokenizer: {tok_key}")
    corpus = Path(args.corpus)
    if not corpus.exists():
        raise SystemExit(f"missing corpus: {corpus}")
    sources = _load_sources(corpus)
    if not sources:
        raise SystemExit("empty sources")

    tok, tt = _load_tokenizer(tok_key, tok_cfg)
    payload = build_global_dictionary(
        sources=sources,
        tokenizer=tok,
        tok_type=tt,
        tokenizer_key=tok_key,
        a_min_occ=int(args.a_min_occ),
        b_min_occ=int(args.b_min_occ),
        a_max_entries=int(args.a_max_entries),
        b_max_entries=int(args.b_max_entries),
        a_prefix=str(args.a_prefix),
        b_prefix=str(args.b_prefix),
    )
    payload["summary"]["preset"] = getattr(args, "preset", "default")
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[done] wrote {out}")
    print(
        "[done] summary "
        f"preset={getattr(args, 'preset', 'default')} "
        f"A={payload['summary']['a_entries']} "
        f"B={payload['summary']['b_entries']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
