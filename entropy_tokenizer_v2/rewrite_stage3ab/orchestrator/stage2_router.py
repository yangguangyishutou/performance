"""
Stage2 → Stage3 resource routing: AST / tokenize sniff, asset extraction, DAG decisions.

Pipeline order (rewrite): **B on retained NL assets first**, then **DELETE_NOW** destructive
pass, then **A** on code identifiers. ``CLEAN_AFTER_B`` removes spans after B (scaffolding).
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass, field
from typing import Any, Iterable

from rewrite_stage3ab.contracts.enums import RouteAction


def _line_col_to_offset(text: str, line: int, col: int) -> int:
    """1-based line, 0-based col (tokenize convention)."""
    lines = text.splitlines(keepends=True)
    off = 0
    for i in range(line - 1):
        if i < len(lines):
            off += len(lines[i])
    return off + col


def _is_docstring_statement(
    parent: ast.AST | None,
    stmt: ast.stmt | None,
) -> bool:
    if parent is None or stmt is None:
        return False
    if not isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    if not parent.body or parent.body[0] is not stmt:
        return False
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and isinstance(stmt.value.value, str):
        return True
    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Str):  # py<3.8 compat unused in 3.11
        return True
    return False


@dataclass
class FreeTextAsset:
    """A span Stage2 might delete, retain for B, or classify as comment/docstring."""

    asset_id: str
    text: str
    source_id: str
    char_start: int | None = None
    char_end: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Stage2AssetDecision:
    """Per-asset routing outcome."""

    asset: FreeTextAsset
    action: RouteAction
    reason: str = ""
    priority_score: float = 0.0


@dataclass
class RouteDecision:
    """Batch routing for one source file."""

    source_id: str
    decisions: list[Stage2AssetDecision] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)


def extract_python_free_text_assets(source_id: str, text: str) -> list[FreeTextAsset]:
    """
    Collect comment, docstring, string literal, and coarse code-region assets using
    ``tokenize`` + ``ast`` (no regex for docstrings / strings).
    """
    assets: list[FreeTextAsset] = []
    aid = 0

    # --- Comments (tokenize)
    readline = io.StringIO(text).readline
    try:
        for tok in tokenize.generate_tokens(readline):
            if tok.type != tokenize.COMMENT:
                continue
            raw = tok.string
            inner = raw.lstrip("#").strip()
            s = _line_col_to_offset(text, tok.start[0], tok.start[1])
            e = _line_col_to_offset(text, tok.end[0], tok.end[1])
            assets.append(
                FreeTextAsset(
                    asset_id=f"{source_id}:c:{aid}",
                    text=raw,
                    source_id=source_id,
                    char_start=s,
                    char_end=e,
                    metadata={
                        "asset_kind": "comment",
                        "lineno": tok.start[0],
                    },
                )
            )
            aid += 1
    except (tokenize.TokenError, IndentationError, SyntaxError):
        pass
    except Exception:
        # Malformed or pathological sources in large corpora: skip comment mining only.
        pass

    # --- AST: docstrings + string literals
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return assets

    parents: dict[ast.AST, ast.AST | None] = {tree: None}
    for p in ast.walk(tree):
        for ch in ast.iter_child_nodes(p):
            parents[ch] = p

    seen_spans: set[tuple[int, int]] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            seg = ast.get_source_segment(text, node)
            if seg is None:
                continue
            p = parents.get(node)
            stmt_for_doc = None
            if isinstance(p, ast.Expr):
                stmt_for_doc = p
                gp = parents.get(p)
            else:
                gp = p
            is_doc = _is_docstring_holder(stmt_for_doc, gp)
            try:
                s = node.lineno  # type: ignore[attr-defined]
                col = node.col_offset  # type: ignore[attr-defined]
                end_ln = getattr(node, "end_lineno", node.lineno)
                end_col = getattr(node, "end_col_offset", col + len(seg))
                cs = _line_col_to_offset(text, s, col)
                ce = _line_col_to_offset(text, end_ln, end_col)
            except Exception:
                cs, ce = None, None
            if cs is not None and ce is not None:
                key = (cs, ce)
                if key in seen_spans:
                    continue
                seen_spans.add(key)
            kind = "docstring" if is_doc else "string_literal"
            if is_doc:
                scope = "module"
                if isinstance(gp, ast.ClassDef):
                    scope = "class"
                elif isinstance(gp, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    scope = "function"
                meta = {"asset_kind": kind, "scope": scope, "name": getattr(gp, "name", None)}
            else:
                meta = {
                    "asset_kind": kind,
                    "multiline": "\n" in seg,
                    "char_len": len(seg),
                }
            assets.append(
                FreeTextAsset(
                    asset_id=f"{source_id}:s:{aid}",
                    text=seg,
                    source_id=source_id,
                    char_start=cs,
                    char_end=ce,
                    metadata=meta,
                )
            )
            aid += 1

    # --- Ordinary code (single coarse asset for telemetry / pass-through)
    assets.append(
        FreeTextAsset(
            asset_id=f"{source_id}:code:0",
            text=text,
            source_id=source_id,
            char_start=0,
            char_end=len(text),
            metadata={"asset_kind": "ordinary_code_text"},
        )
    )
    return assets


def _is_docstring_holder(stmt: ast.stmt | None, parent: ast.AST | None) -> bool:
    return _is_docstring_statement(parent, stmt)


@dataclass
class RoutePolicy:
    """Tunable Stage2 → B routing (AST/tokenize assets only)."""

    short_comment_max_inner: int = 8
    retain_docstring: bool = True
    b_string_min_chars: int = 16
    retain_comment_threshold: int = 9
    long_literal_reference_threshold: int = 16
    multiline_string_policy: str = "retain_b"  # retain_b | pass_through


def summarize_route_decision(rd: RouteDecision) -> dict[str, Any]:
    """Aggregate counts for corpus rollups (excludes coarse ``ordinary_code_text`` spam)."""
    from collections import Counter

    act = Counter()
    docstrings = 0
    comments = 0
    for d in rd.decisions:
        a = d.asset
        kind = a.metadata.get("asset_kind", "")
        if kind == "ordinary_code_text":
            continue
        act[d.action.value] += 1
        if kind == "docstring":
            docstrings += 1
        elif kind == "comment":
            comments += 1
    return {
        "total_route_delete_now": int(act.get(RouteAction.DELETE_NOW.value, 0)),
        "total_route_retain_for_b": int(act.get(RouteAction.RETAIN_FOR_B.value, 0)),
        "total_route_retain_as_reference_candidate": int(act.get(RouteAction.RETAIN_AS_REFERENCE_CANDIDATE.value, 0)),
        "total_route_pass_through": int(act.get(RouteAction.PASS_THROUGH.value, 0)),
        "total_route_clean_after_b": int(act.get(RouteAction.CLEAN_AFTER_B.value, 0)),
        "total_docstrings_detected": docstrings,
        "total_comments_detected": comments,
    }


class Stage2RouterEngine:
    """
    Parameterized policy: long NL → B; noise comments → delete; reference-like literals flagged.
    """

    def __init__(self, policy: RoutePolicy | None = None) -> None:
        self.policy = policy or RoutePolicy()

    def route(self, source_id: str, assets: list[FreeTextAsset]) -> RouteDecision:
        decisions: list[Stage2AssetDecision] = []
        for a in assets:
            kind = a.metadata.get("asset_kind", "")
            action, reason, score = self._decide_one(a, kind)
            decisions.append(Stage2AssetDecision(asset=a, action=action, reason=reason, priority_score=score))
        summary = summarize_route_decision(
            RouteDecision(source_id=source_id, decisions=decisions, extras={})
        )
        return RouteDecision(
            source_id=source_id,
            decisions=decisions,
            extras={"engine": "Stage2RouterEngine", "route_summary": summary, "policy": self.policy},
        )

    def _decide_one(self, a: FreeTextAsset, kind: str) -> tuple[RouteAction, str, float]:
        p = self.policy
        if kind == "ordinary_code_text":
            return RouteAction.PASS_THROUGH, "code_body_default", 0.0
        if kind == "comment":
            inner = a.text.lstrip("#").strip()
            if len(inner) <= p.short_comment_max_inner:
                return RouteAction.DELETE_NOW, "short_comment_noise", 1.0
            if len(inner) >= p.retain_comment_threshold:
                return RouteAction.RETAIN_FOR_B, "comment_nl_candidate", 0.6
            return RouteAction.PASS_THROUGH, "comment_mid_neutral", 0.2
        if kind == "docstring":
            if p.retain_docstring:
                return RouteAction.RETAIN_FOR_B, "docstring_compressible", 0.9
            return RouteAction.PASS_THROUGH, "docstring_policy_off", 0.1
        if kind == "string_literal":
            L = len(a.text)
            if a.metadata.get("multiline"):
                if p.multiline_string_policy == "retain_b":
                    return RouteAction.RETAIN_FOR_B, "multiline_string_asset", 0.75
                return RouteAction.PASS_THROUGH, "multiline_policy_pass", 0.15
            if L >= p.long_literal_reference_threshold:
                return RouteAction.RETAIN_AS_REFERENCE_CANDIDATE, "long_literal_reference_pool", 0.55
            if L >= p.b_string_min_chars:
                return RouteAction.RETAIN_FOR_B, "long_string_nl", 0.5
            return RouteAction.PASS_THROUGH, "short_literal_keep", 0.1
        return RouteAction.PASS_THROUGH, "unknown_kind", 0.0


class StubStage2Router:
    """Back-compat: pass-through everything."""

    def route(self, source_id: str, assets: list[FreeTextAsset]) -> RouteDecision:
        return RouteDecision(
            source_id=source_id,
            decisions=[Stage2AssetDecision(asset=x, action=RouteAction.PASS_THROUGH, reason="stub") for x in assets],
        )


def _merge_spans(spans: list[tuple[int, int]]) -> list[tuple[int, int]]:
    if not spans:
        return []
    spans = sorted(spans)
    out = [spans[0]]
    for s, e in spans[1:]:
        ps, pe = out[-1]
        if s <= pe:
            out[-1] = (ps, max(pe, e))
        else:
            out.append((s, e))
    return out


def apply_char_span_removals(text: str, spans: Iterable[tuple[int, int]]) -> str:
    """Remove half-open [start, end) spans from *text* (right to left)."""
    merged = _merge_spans(list(spans))
    out = text
    for s, e in reversed(merged):
        s = max(0, min(s, len(out)))
        e = max(s, min(e, len(out)))
        out = out[:s] + out[e:]
    return out


def collect_spans_for_action(rd: RouteDecision, actions: set[RouteAction]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for d in rd.decisions:
        if d.action not in actions:
            continue
        a = d.asset
        if a.char_start is None or a.char_end is None:
            continue
        spans.append((a.char_start, a.char_end))
    return spans


def assets_for_b(rd: RouteDecision) -> list[FreeTextAsset]:
    """Assets routed to B-style compression."""
    out: list[FreeTextAsset] = []
    for d in rd.decisions:
        if d.action in (RouteAction.RETAIN_FOR_B, RouteAction.RETAIN_AS_REFERENCE_CANDIDATE):
            if d.asset.metadata.get("asset_kind") != "ordinary_code_text":
                out.append(d.asset)
    return out
