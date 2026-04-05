"""
Read-only probes for A-channel gates (length, attribute depth, string_exact_path).
"""

from __future__ import annotations

import ast
import keyword
import re
from collections import Counter
from typing import Any, Iterator

from rewrite_stage3ab.channels.a_channel.implementation_v1 import (
    _collect_defined_and_imported_names,
    _count_load_names,
)
from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len

_SAFE_PATH_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]{7,}\Z")


def _attr_base_depth(node: ast.AST) -> int:
    if isinstance(node, ast.Name):
        return 1
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return 2
    if isinstance(node, ast.Attribute):
        return 1 + _attr_base_depth(node.value)
    return 99


def enumerate_attribute_suffixes_by_depth(text: str) -> list[tuple[str, int, int]]:
    """
    Return list of (attr_name, base_depth, occ) aggregated by name (max depth seen per name for reporting).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    by_name_depth: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if isinstance(node.attr, str) and node.attr.isidentifier():
                d = _attr_base_depth(node.value)
                n = node.attr
                by_name_depth[n] = max(by_name_depth.get(n, 0), d)
    ctr: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if isinstance(node.attr, str) and node.attr.isidentifier():
                ctr[node.attr] += 1
    out: list[tuple[str, int, int]] = []
    for name, depth in by_name_depth.items():
        out.append((name, depth, ctr[name]))
    return sorted(out, key=lambda x: (-x[2], x[0]))


def collect_attributes_for_max_depth(text: str, *, max_depth: int, min_len: int) -> list[str]:
    rows = enumerate_attribute_suffixes_by_depth(text)
    return sorted({n for n, d, occ in rows if d <= max_depth and len(n) >= min_len and not keyword.iskeyword(n)})


def count_variable_candidates(text: str, *, min_len: int, tokenizer_key: str) -> tuple[int, int]:
    """Returns (admitted_count, filtered_short_count)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return 0, 0
    ctr: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            ctr[node.id] += 1
    admitted = 0
    filtered_short = 0
    for raw, _occ in ctr.items():
        if not raw.isidentifier() or keyword.iskeyword(raw):
            continue
        if len(raw) < min_len:
            tl = measure_true_token_len(raw, tokenizer_key)
            if tl < 2:
                filtered_short += 1
            else:
                admitted += 1
        else:
            admitted += 1
    return admitted, filtered_short


def count_a_pre_collection_filters(
    text: str,
    tokenizer_key: str,
    *,
    min_identifier_chars: int,
    max_attr_depth: int,
    enable_attributes: bool = True,
    string_path_ctx: dict[str, Any] | None = None,
) -> dict[str, int]:
    """
    Occurrence-weighted drops before ``collect_candidates`` emits a row.
    """
    out = {
        "a_candidates_filtered_short_name": 0,
        "a_candidates_filtered_attr_depth": 0,
        "a_candidates_filtered_string_exact_path": 0,
    }
    name_ctr, tree = _count_load_names(text)
    if tree is None:
        return out
    for raw, occ in name_ctr.items():
        if not raw.isidentifier() or keyword.iskeyword(raw):
            continue
        if len(raw) < min_identifier_chars:
            tl = measure_true_token_len(raw, tokenizer_key)
            if tl < 2:
                out["a_candidates_filtered_short_name"] += occ

    if enable_attributes:
        for node in ast.walk(tree):
            if not isinstance(node, ast.Attribute) or not isinstance(node.ctx, ast.Load):
                continue
            if not isinstance(node.attr, str) or not node.attr.isidentifier() or keyword.iskeyword(node.attr):
                continue
            d = _attr_base_depth(node.value)
            if d > max_attr_depth and len(node.attr) >= min_identifier_chars:
                out["a_candidates_filtered_attr_depth"] += 1
            elif d <= max_attr_depth and len(node.attr) < min_identifier_chars:
                out["a_candidates_filtered_short_name"] += 1

    ctx_sp = string_path_ctx or {}
    exact_path = ctx_sp.get("string_exact_path")
    if isinstance(exact_path, str) and exact_path in text:
        allow = bool(ctx_sp.get("allow_string_exact_path"))
        reg_ok = bool(_SAFE_PATH_RE.match(exact_path))
        occ = text.count(exact_path)
        exp = ctx_sp.get("string_exact_path_expected_occ", occ)
        occ_ok = occ == exp and occ > 0
        if not (allow and reg_ok and occ_ok):
            out["a_candidates_filtered_string_exact_path"] += 1
    return out


def diagnose_a_evaluations(
    text: str,
    tokenizer_key: str,
    *,
    min_identifier_chars: int = 10,
    max_attr_depth: int = 3,
    string_path_ctx: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Simulate collect + per-candidate evaluate (single-candidate economics, no combo).
    """
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        return {
            "parse_ok": False,
            "ast_parse_failed": True,
            "syntax_error_lineno": int(e.lineno or 0),
            "syntax_error_msg": str(e.msg or ""),
            "a_candidates_variable": 0,
            "a_candidates_attribute": 0,
            "a_candidates_string_exact_path": 0,
        }
    fb = _collect_defined_and_imported_names(tree)
    ctx: dict[str, Any] = {"forbidden_base": fb, "reserved_aliases": set()}
    if string_path_ctx:
        ctx.update(string_path_ctx)
    from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1

    gate = count_a_pre_collection_filters(
        text,
        tokenizer_key,
        min_identifier_chars=min_identifier_chars,
        max_attr_depth=max_attr_depth,
        string_path_ctx=string_path_ctx,
    )
    a = AChannelV1(tokenizer_key, min_identifier_chars=min_identifier_chars, max_attr_depth=max_attr_depth)
    cands = a.collect_candidates(text, ctx)
    by_field: Counter[str] = Counter(str(c.get("field")) for c in cands)
    stats = {
        "parse_ok": True,
        "ast_parse_failed": False,
        "syntax_error_lineno": 0,
        "syntax_error_msg": "",
        **gate,
        "a_candidates_total": len(cands),
        "a_candidates_variable": int(by_field.get("variable", 0)),
        "a_candidates_attribute": int(by_field.get("attribute", 0)),
        "a_candidates_string_exact_path": int(by_field.get("string_exact_path", 0)),
        "a_candidates_no_legal_alias": 0,
        "a_candidates_no_net_true_gain": 0,
        "a_candidates_positive_gross_but_negative_net": 0,
        "a_candidates_accepted": 0,
    }
    gross_neg_net: list[dict[str, Any]] = []
    long_ids: list[dict[str, Any]] = []
    high_occ: list[dict[str, Any]] = []
    for c in cands:
        raw = str(c.get("literal", ""))
        occ = int(c.get("occ", 0))
        ev = a.evaluate_candidate(c, ctx)
        if ev.get("ok"):
            stats["a_candidates_accepted"] += 1
            ctx["reserved_aliases"].add(str(ev.get("alias", "")))
            continue
        reason = str(ev.get("reason", ""))
        if reason == "no_legal_alias":
            stats["a_candidates_no_legal_alias"] += 1
        elif reason == "no_net_true_gain":
            stats["a_candidates_no_net_true_gain"] += 1
            g = int(ev.get("gross_gain_true", 0))
            n = int(ev.get("net_true", 0))
            if g > 0 and n < 0:
                stats["a_candidates_positive_gross_but_negative_net"] += 1
                gross_neg_net.append(
                    {"literal": raw, "occ": occ, "field": c.get("field"), "gross": g, "net": n, "intro": ev.get("intro_tokens_true")}
                )
        if len(raw) >= 16:
            long_ids.append({"literal": raw, "occ": occ, "field": c.get("field"), "tok": measure_true_token_len(raw, tokenizer_key)})
        if occ >= 4:
            high_occ.append({"literal": raw, "occ": occ, "field": c.get("field")})
    gross_neg_net.sort(key=lambda x: -x["gross"])
    long_ids.sort(key=lambda x: (-x["tok"], -x["occ"]))
    high_occ.sort(key=lambda x: (-x["occ"], -len(x["literal"])))
    return {
        **stats,
        "top_gross_pos_net_neg": gross_neg_net[:50],
        "top_long_identifiers": long_ids[:50],
        "top_high_occurrence": high_occ[:50],
    }


def iter_short_name_filtered_records(
    text: str,
    tokenizer_key: str,
    *,
    min_identifier_chars: int = 10,
    max_attr_depth: int = 3,
) -> Iterator[dict[str, Any]]:
    """
    Identifiers that fail the short-name gate (variable: len<min and true_tok<2;
    attribute: shallow chain and len(attr)<min), with occurrence counts in this file.
    """
    name_ctr, tree = _count_load_names(text)
    if tree is None:
        return
    for raw, occ in name_ctr.items():
        if not raw.isidentifier() or keyword.iskeyword(raw):
            continue
        if len(raw) < min_identifier_chars:
            tl = measure_true_token_len(raw, tokenizer_key)
            if tl < 2:
                yield {
                    "literal": raw,
                    "field": "variable",
                    "occ": occ,
                    "char_len": len(raw),
                    "tok_true": tl,
                }
    short_attr: Counter[str] = Counter()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Attribute) or not isinstance(node.ctx, ast.Load):
            continue
        if not isinstance(node.attr, str) or not node.attr.isidentifier() or keyword.iskeyword(node.attr):
            continue
        d = _attr_base_depth(node.value)
        if d <= max_attr_depth and len(node.attr) < min_identifier_chars:
            short_attr[node.attr] += 1
    for raw, occ in short_attr.items():
        yield {
            "literal": raw,
            "field": "attribute",
            "occ": occ,
            "char_len": len(raw),
            "tok_true": measure_true_token_len(raw, tokenizer_key),
        }


def aggregate_attr_occ_by_depth_caps(
    text: str,
    *,
    min_identifier_chars: int = 10,
) -> dict[str, int]:
    """
    Per-name max-depth rows from ``enumerate_attribute_suffixes_by_depth``;
    sum ``occ`` where name length passes ``min_identifier_chars``.
    """
    rows = enumerate_attribute_suffixes_by_depth(text)
    eligible = [(n, d, occ) for n, d, occ in rows if len(n) >= min_identifier_chars and not keyword.iskeyword(n)]
    le3 = sum(occ for _n, d, occ in eligible if d <= 3)
    le4 = sum(occ for _n, d, occ in eligible if d <= 4)
    le5 = sum(occ for _n, d, occ in eligible if d <= 5)
    gt5 = sum(occ for _n, d, occ in eligible if d > 5)
    return {
        "attr_suffix_occ_minlen_ok_depth_le_3": le3,
        "attr_suffix_occ_minlen_ok_depth_le_4": le4,
        "attr_suffix_occ_minlen_ok_depth_le_5": le5,
        "attr_suffix_occ_minlen_ok_depth_gt_5": gt5,
        "attr_occ_gain_relax_3_to_4": le4 - le3,
        "attr_occ_gain_relax_4_to_5": le5 - le4,
    }


def scan_string_path_literal_stats(text: str) -> dict[str, Any]:
    """Count AST string constants whose full value matches ``_SAFE_PATH_RE`` (proxy for string_exact_path)."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {"parse_ok": False, "n_distinct_path_like": 0, "total_occurrences_in_file": 0}
    distinct: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            v = node.value
            if _SAFE_PATH_RE.match(v):
                distinct.add(v)
    total_occ = sum(text.count(v) for v in distinct)
    return {
        "parse_ok": True,
        "n_distinct_path_like": len(distinct),
        "total_occurrences_in_file": total_occ,
    }


def count_string_exact_path_eligibility(
    text: str,
    *,
    exact_path: str,
    allow: bool,
    expected_occ: int | None,
) -> dict[str, Any]:
    occ = text.count(exact_path) if exact_path in text else 0
    reg_ok = bool(_SAFE_PATH_RE.match(exact_path)) if exact_path else False
    exp = expected_occ if expected_occ is not None else occ
    occ_ok = occ == exp and occ > 0
    would_add = allow and reg_ok and exact_path in text and occ_ok
    return {
        "allow_string_exact_path": allow,
        "regex_ok": reg_ok,
        "occurrences_in_text": occ,
        "expected_occ": exp,
        "occ_matches_expected": occ_ok,
        "would_enter_candidates": would_add,
    }
