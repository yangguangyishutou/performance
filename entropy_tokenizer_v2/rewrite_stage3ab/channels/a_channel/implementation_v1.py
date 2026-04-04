"""
Tokenizer-aware A channel: alias mining, true-token economics, AST scope safety.
"""

from __future__ import annotations

import ast
import keyword
import re
from collections import Counter
from typing import Any

from rewrite_stage3ab.channels.a_channel.alias_pool import pick_best_alias
from rewrite_stage3ab.channels.a_channel.economics import net_gain_for_alias
from rewrite_stage3ab.metrics.tokenizer_metric import measure_true_token_len

_NAME_MIN_CHARS = 10


def _collect_defined_and_imported_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
            for a in node.args.args:
                names.add(a.arg)
            if node.args.vararg:
                names.add(node.args.vararg.arg)
            if node.args.kwarg:
                names.add(node.args.kwarg.arg)
        if isinstance(node, ast.ClassDef):
            names.add(node.name)
        if isinstance(node, ast.Import):
            for n in node.names:
                names.add(n.asname or n.name.split(".")[0])
        if isinstance(node, ast.ImportFrom):
            for n in node.names:
                if n.name != "*":
                    names.add(n.asname or n.name)
        if isinstance(node, ast.arg):
            names.add(node.arg)
    return names


def _count_load_names(text: str) -> tuple[Counter[str], ast.AST | None]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return Counter(), None
    ctr: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            ctr[node.id] += 1
    return ctr, tree


def _count_attribute_suffixes(text: str) -> tuple[Counter[str], ast.AST | None]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return Counter(), None
    ctr: Counter[str] = Counter()
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            if isinstance(node.attr, str) and node.attr.isidentifier():
                ctr[node.attr] += 1
    return ctr, tree


class AChannelV1:
    """
    Exact identifier aliasing driven by **net true-token gain**; ``min_occ_aux`` is soft.
    """

    def __init__(
        self,
        tokenizer_key: str,
        *,
        min_occ_aux: int = 1,
        min_identifier_chars: int = _NAME_MIN_CHARS,
        enable_attributes: bool = True,
    ) -> None:
        self.tokenizer_key = tokenizer_key
        self.min_occ_aux = min_occ_aux
        self.min_identifier_chars = min_identifier_chars
        self.enable_attributes = enable_attributes

    def collect_candidates(self, text: str, ctx: dict[str, Any]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        name_ctr, tree = _count_load_names(text)
        if tree is None:
            return out
        fb = ctx.get("forbidden_base")
        if fb is None:
            fb = _collect_defined_and_imported_names(tree)
            ctx["forbidden_base"] = fb
        for field, ctr in (("variable", name_ctr),):
            for raw, occ in ctr.items():
                if not raw.isidentifier() or keyword.iskeyword(raw):
                    continue
                if len(raw) < self.min_identifier_chars:
                    tl = measure_true_token_len(raw, self.tokenizer_key)
                    if tl < 2:
                        continue
                out.append({"field": field, "literal": raw, "occ": occ})
        if self.enable_attributes:
            attr_ctr, tree2 = _count_attribute_suffixes(text)
            if tree2 is not None:
                for raw, occ in attr_ctr.items():
                    if keyword.iskeyword(raw) or len(raw) < self.min_identifier_chars:
                        continue
                    out.append({"field": "attribute", "literal": raw, "occ": occ})
        exact_path = ctx.get("string_exact_path")
        if isinstance(exact_path, str) and exact_path in text:
            out.append({"field": "string_exact_path", "literal": exact_path, "occ": text.count(exact_path)})
        return out

    def rank_candidates(self, candidates: list[dict[str, Any]], ctx: dict[str, Any]) -> list[dict[str, Any]]:
        scored: list[tuple[float, dict[str, Any]]] = []
        base = set(ctx.get("forbidden_base", set()))
        reserved = set(ctx.get("reserved_aliases", set()))
        for c in candidates:
            occ = int(c.get("occ", 0))
            raw = str(c.get("literal", ""))
            fb = base | reserved
            best = pick_best_alias(self.tokenizer_key, forbidden=fb | {raw})
            if best is None:
                scored.append((-1e9, c))
                continue
            _, _, net = net_gain_for_alias(raw, best.alias, occ, self.tokenizer_key)
            scored.append((float(net), c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored]

    def evaluate_candidate(self, candidate: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
        raw = str(candidate.get("literal", ""))
        occ = int(candidate.get("occ", 0))
        fb = set(ctx.get("forbidden_base", set())) | set(ctx.get("reserved_aliases", set()))
        best = pick_best_alias(self.tokenizer_key, forbidden=fb | {raw})
        if best is None:
            return {"ok": False, "candidate": candidate, "reason": "no_legal_alias"}
        gross, intro, net = net_gain_for_alias(raw, best.alias, occ, self.tokenizer_key)
        # Primary gate: net true tokens
        if net <= 0:
            return {
                "ok": False,
                "candidate": candidate,
                "reason": "no_net_true_gain",
                "gross_gain_true": gross,
                "intro_tokens_true": intro,
                "net_true": net,
                "alias": best.alias,
            }
        return {
            "ok": True,
            "candidate": candidate,
            "alias": best.alias,
            "gross_gain_true": gross,
            "intro_tokens_true": intro,
            "net_true": net,
            "token_len_alias": best.token_len_true,
        }

    def apply_assignments(self, text: str, ctx: dict[str, Any]) -> str:
        assignments: list[dict[str, Any]] = ctx.get("a_assignments", [])
        out = text
        for row in assignments:
            old = row.get("literal")
            new = row.get("alias")
            if not isinstance(old, str) or not isinstance(new, str):
                continue
            if row.get("field") == "attribute":
                pattern = re.compile(rf"(\.){re.escape(old)}\b")
                out = pattern.sub(rf"\1{new}", out)
            elif row.get("field") == "string_exact_path":
                out = out.replace(old, new)
            else:
                out = re.sub(rf"\b{re.escape(old)}\b", new, out)
        return out
