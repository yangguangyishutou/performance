"""Request-local exact aliasing for Stage3 hybrid A channel."""

from __future__ import annotations

import ast
import builtins
import io
import json
import keyword
import re
import tokenize
from collections import Counter
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Optional

from config import CACHE_DIR, VOCAB_COST_MODE
from placeholder_accounting import compute_vocab_intro_cost
from token_scorer import _line_start_offsets, _pos_to_offset, sum_context_aware_literal_delta

from ..literal_codec.alias_pool import build_legal_alias_alphabet
from ..routing.router import ABRoutingConfig, classify_string_with_reason

_PROTECTED = set(keyword.kwlist) | set(dir(builtins)) | {"self", "cls", "True", "False", "None"}


@dataclass(slots=True)
class AEntry:
    field: str
    literal: str
    alias: str
    count: int
    raw_cost: int
    alias_cost: int
    intro_cost: int
    gain: int
    is_global: bool = False
    vocab_kind: str = "stage3_ab_a_alias"


@dataclass(slots=True)
class ACodecResult:
    encoded_text: str
    entries: list[AEntry] = field(default_factory=list)
    candidates: int = 0
    selected: int = 0
    used_entries: int = 0
    intro_tokens: int = 0
    sequence_saved: int = 0
    effective_net_saving: int = 0
    vocab_entries: list[dict[str, Any]] = field(default_factory=list)
    reject_reason_counts: dict[str, int] = field(default_factory=dict)
    protected_name_count: int = 0
    min_occ_reject_count: int = 0
    net_gain_reject_count: int = 0
    global_used_entries: int = 0
    global_used_entries_variable: int = 0
    global_used_entries_attribute: int = 0
    global_used_entries_string: int = 0
    global_vocab_entries: list[dict[str, Any]] = field(default_factory=list)
    # Span index for incremental guardrail rollback (hybrid_ab file-level check).
    occ: dict[tuple[str, str], list[tuple[int, int]]] = field(default_factory=dict)


@dataclass(slots=True)
class _CompoundSpan:
    field: str
    literal: str
    start: int
    end: int


def _token_len(tokenizer: Any, tok_type: str, text: str) -> int:
    from marker_count import encode as _encode

    return len(_encode(tokenizer, tok_type, text))


def _alias_cache_id(tokenizer: Any, tok_type: str) -> str:
    model_name = getattr(tokenizer, "name_or_path", "") or getattr(tokenizer, "model", "")
    if not isinstance(model_name, str):
        model_name = str(model_name)
    cls_name = f"{tokenizer.__class__.__module__}.{tokenizer.__class__.__name__}"
    raw = f"{tok_type}_{model_name or cls_name}".strip()
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", raw).strip("_.-")
    return safe or f"{tok_type}_tokenizer"


def _load_alias_alphabet_cache(tokenizer: Any, tok_type: str) -> dict[str, Any]:
    cache_id = _alias_cache_id(tokenizer, tok_type)
    fp = CACHE_DIR / "alias_alphabets" / f"alias_alphabet_{cache_id}.json"
    if not fp.exists():
        return {}
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_alias_alphabet_cache(tokenizer: Any, tok_type: str, payload: dict[str, Any]) -> None:
    cache_id = _alias_cache_id(tokenizer, tok_type)
    fp = CACHE_DIR / "alias_alphabets" / f"alias_alphabet_{cache_id}.json"
    try:
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        return


def build_alias_alphabet(
    tokenizer: Any,
    tok_type: str,
    *,
    style: str,
    prefix: Optional[str] = None,
    max_n: int = 256,
    candidate_style: str = "token_cost_sorted",
) -> list[str]:
    style = (style or "").strip().lower()
    style = style if style in {"short", "mnemonic"} else "short"
    cache = _load_alias_alphabet_cache(tokenizer, tok_type)

    if style == "short":
        cached = cache.get("short", {})
        if (
            isinstance(cached, dict)
            and cached.get("max_n") == max_n
            and str(cached.get("candidate_style", "token_cost_sorted")) == candidate_style
        ):
            cands = cached.get("candidates")
            if isinstance(cands, list) and all(isinstance(x, str) for x in cands):
                return cands
        items: list[tuple[int, int, str]] = []
        families: list[str]
        if candidate_style == "compact_mixed":
            families = ["x", "v", "_x", "__ab"]
        elif candidate_style == "underscore_heavy":
            families = ["__ab", "__x", "_x", "x"]
        else:
            families = ["__ab", "_x", "x", "z"]
        per_family = max(8, max_n // max(1, len(families)))
        generated: list[str] = []
        for fam in families:
            for n in range(per_family):
                generated.append(f"{fam}{n}")
        # Ensure stable budget and uniqueness.
        seen_alias: set[str] = set()
        candidates = []
        for a in generated:
            if a in seen_alias:
                continue
            seen_alias.add(a)
            candidates.append(a)
            if len(candidates) >= max_n:
                break
        for alias in candidates:
            items.append((_token_len(tokenizer, tok_type, alias), len(alias), alias))
        items.sort(key=lambda t: (t[0], t[1], t[2]))
        out = [a for _c, _l, a in items]
        cache["short"] = {
            "max_n": max_n,
            "candidate_style": candidate_style,
            "candidates": out,
        }
        _save_alias_alphabet_cache(tokenizer, tok_type, cache)
        return out

    if not prefix:
        prefix = "x"
    cached_mn = cache.get("mnemonic_prefixes", {})
    if isinstance(cached_mn, dict):
        entry = cached_mn.get(prefix, {})
        if isinstance(entry, dict) and entry.get("max_n") == max_n:
            cands = entry.get("candidates")
            if isinstance(cands, list) and all(isinstance(x, str) for x in cands):
                return cands
    items = []
    for n in range(max_n):
        alias = f"_{prefix}{n}"
        items.append((_token_len(tokenizer, tok_type, alias), len(alias), alias))
    items.sort(key=lambda t: (t[0], t[1], t[2]))
    out = [a for _c, _l, a in items]
    cache.setdefault("mnemonic_prefixes", {})[prefix] = {"max_n": max_n, "candidates": out}
    _save_alias_alphabet_cache(tokenizer, tok_type, cache)
    return out


def _apply_spans(text: str, spans: list[tuple[int, int, str]]) -> str:
    out = text
    for st, ed, rep in sorted(spans, key=lambda x: x[0], reverse=True):
        out = out[:st] + rep + out[ed:]
    return out


def _sanitize_prefix(name: str) -> str:
    s = "".join(ch for ch in name if ch.isalnum() or ch == "_")
    return (s[:2] if s else "x").lower()


def _collect_ast_protected_names(text: str) -> set[str]:
    out: set[str] = set()
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, MemoryError):
        return out
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = node.name
            if re.match(r"^__.*__$", name):
                out.add(name)
                continue
            if name.startswith("_"):
                continue
            out.add(name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        for elt in node.value.elts:
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                out.add(elt.value)
    return out


def _collect_scope_name_conflicts(text: str) -> set[str]:
    """Names / attributes / imports that must not be reused as A-channel aliases."""
    names: set[str] = set()
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, MemoryError):
        return names
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Import):
            for a in node.names:
                base = (a.name or "").split(".")[0]
                names.add(a.asname or base)
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name == "*":
                    continue
                names.add(a.asname or a.name)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.NamedExpr):
            names.add(node.target.id)
    return names


def _node_offsets(
    line_starts: list[int],
    node: ast.AST,
) -> tuple[int, int] | None:
    if not all(
        hasattr(node, attr)
        for attr in ("lineno", "col_offset", "end_lineno", "end_col_offset")
    ):
        return None
    try:
        st = _pos_to_offset(line_starts, (int(node.lineno), int(node.col_offset)))
        ed = _pos_to_offset(line_starts, (int(node.end_lineno), int(node.end_col_offset)))
    except Exception:
        return None
    if ed <= st:
        return None
    return st, ed


def _push_compound_span(
    out: list[_CompoundSpan],
    *,
    field: str,
    literal: str,
    start: int,
    end: int,
    tokenizer: Any,
    tok_type: str,
    min_raw_token_len: int,
) -> None:
    if end <= start:
        return
    if not literal or literal.isspace():
        return
    if not re.search(r"[A-Za-z_]", literal):
        return
    if _token_len(tokenizer, tok_type, literal) < int(min_raw_token_len):
        return
    out.append(_CompoundSpan(field=field, literal=literal, start=start, end=end))


def _iter_annotation_nodes(tree: ast.AST) -> list[ast.AST]:
    nodes: list[ast.AST] = []
    for item in ast.walk(tree):
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for arg in (
                list(item.args.posonlyargs)
                + list(item.args.args)
                + list(item.args.kwonlyargs)
            ):
                if arg.annotation is not None:
                    nodes.append(arg.annotation)
            if item.args.vararg and item.args.vararg.annotation is not None:
                nodes.append(item.args.vararg.annotation)
            if item.args.kwarg and item.args.kwarg.annotation is not None:
                nodes.append(item.args.kwarg.annotation)
            if item.returns is not None:
                nodes.append(item.returns)
        elif isinstance(item, ast.AnnAssign) and item.annotation is not None:
            nodes.append(item.annotation)
    return nodes


def _collect_compound_spans(
    text: str,
    *,
    tokenizer: Any,
    tok_type: str,
    line_starts: list[int],
    min_raw_token_len: int,
) -> list[_CompoundSpan]:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError, MemoryError):
        return []

    raw: list[_CompoundSpan] = []
    for ann in _iter_annotation_nodes(tree):
        offsets = _node_offsets(line_starts, ann)
        if offsets is None:
            continue
        st, ed = offsets
        _push_compound_span(
            raw,
            field="annotation",
            literal=text[st:ed],
            start=st,
            end=ed,
            tokenizer=tokenizer,
            tok_type=tok_type,
            min_raw_token_len=min_raw_token_len,
        )

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            offsets = _node_offsets(line_starts, node)
            if offsets is None:
                continue
            module_text = "." * int(getattr(node, "level", 0) or 0) + str(node.module or "")
            if not module_text:
                continue
            st_node, ed_node = offsets
            segment = text[st_node:ed_node]
            rel = segment.find(module_text)
            if rel < 0:
                continue
            _push_compound_span(
                raw,
                field="import_module",
                literal=module_text,
                start=st_node + rel,
                end=st_node + rel + len(module_text),
                tokenizer=tokenizer,
                tok_type=tok_type,
                min_raw_token_len=min_raw_token_len,
            )
        elif isinstance(node, ast.Import):
            offsets = _node_offsets(line_starts, node)
            if offsets is None:
                continue
            st_node, ed_node = offsets
            segment = text[st_node:ed_node]
            cursor = 0
            for alias in node.names:
                target = str(alias.name or "")
                if not target:
                    continue
                rel = segment.find(target, cursor)
                if rel < 0:
                    rel = segment.find(target)
                    if rel < 0:
                        continue
                _push_compound_span(
                    raw,
                    field="import_module",
                    literal=target,
                    start=st_node + rel,
                    end=st_node + rel + len(target),
                    tokenizer=tokenizer,
                    tok_type=tok_type,
                    min_raw_token_len=min_raw_token_len,
                )
                cursor = rel + len(target)

    raw.sort(key=lambda sp: (sp.start, -(sp.end - sp.start), sp.field))
    filtered: list[_CompoundSpan] = []
    for span in raw:
        if any(not (span.end <= cur.start or span.start >= cur.end) for cur in filtered):
            continue
        filtered.append(span)
    return filtered


def _inside_compound_span(start: int, end: int, spans: list[_CompoundSpan]) -> bool:
    return any(start >= sp.start and end <= sp.end for sp in spans)


def apply_a_entries(
    text: str,
    occ: dict[tuple[str, str], list[tuple[int, int]]],
    entries: list[AEntry],
) -> str:
    """Re-apply a subset of A entries onto Stage2 text (used by file-level guardrail)."""
    if not entries:
        return text
    spans_all: list[tuple[int, int, str]] = []
    for e in entries:
        key = (e.field, e.literal)
        for st, ed in occ.get(key, ()):
            spans_all.append((st, ed, e.alias))
    return _apply_spans(text, spans_all) if spans_all else text


def encode_exact_aliases(
    text: str,
    *,
    tokenizer: Any,
    tok_type: str,
    route_cfg: ABRoutingConfig,
    min_occ: int = 2,
    min_net_gain: int = 1,
    alias_style: str = "short",
    alias_candidate_style: str = "token_cost_sorted",
    enable_compound_spans: bool = True,
    compound_min_raw_token_len: int = 4,
    cost_mode: str = "local",
    min_raw_token_len: int = 1,
    max_alias_token_len: int = 32,
    context_window_chars: int = 80,
    global_aliases: Optional[dict[tuple[str, str], str]] = None,
    global_aliases_are_predefined: bool = True,
) -> ACodecResult:
    cost_mode = (cost_mode or "local").strip().lower()
    if cost_mode not in {"local", "context_aware"}:
        cost_mode = "local"
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return ACodecResult(encoded_text=text)
    line_starts = _line_start_offsets(text)
    ast_protected = _collect_ast_protected_names(text)
    scope_conflicts = _collect_scope_name_conflicts(text)
    compound_spans = (
        _collect_compound_spans(
            text,
            tokenizer=tokenizer,
            tok_type=tok_type,
            line_starts=line_starts,
            min_raw_token_len=max(int(min_raw_token_len), int(compound_min_raw_token_len)),
        )
        if enable_compound_spans
        else []
    )
    occ: dict[tuple[str, str], list[tuple[int, int]]] = defaultdict(list)
    reject_reasons: Counter[str] = Counter()
    protected_name_count = 0
    prev_is_dot = False
    for tok in toks:
        ttype, tstr = tok.type, tok.string
        if ttype == tokenize.NAME:
            if tstr in _PROTECTED or tstr in ast_protected:
                protected_name_count += 1
                prev_is_dot = False
                continue
            field = "attribute" if prev_is_dot else "variable"
            st = _pos_to_offset(line_starts, tok.start)
            ed = _pos_to_offset(line_starts, tok.end)
            if _inside_compound_span(st, ed, compound_spans):
                prev_is_dot = False
                continue
            occ[(field, tstr)].append((st, ed))
            prev_is_dot = False
        elif ttype == tokenize.STRING:
            route, reason = classify_string_with_reason(tstr, route_cfg)
            if route == "A":
                st = _pos_to_offset(line_starts, tok.start)
                ed = _pos_to_offset(line_starts, tok.end)
                if _inside_compound_span(st, ed, compound_spans):
                    prev_is_dot = False
                    continue
                occ[("string", tstr)].append((st, ed))
            else:
                reject_reasons[f"route_{reason}"] += 1
            prev_is_dot = False
        elif ttype == tokenize.OP:
            prev_is_dot = tstr == "."
        else:
            prev_is_dot = False

    for span in compound_spans:
        occ[(span.field, span.literal)].append((span.start, span.end))

    candidates = len(occ)
    alias_style = (alias_style or "").strip().lower()
    if alias_style not in {"short", "mnemonic"}:
        alias_style = "short"
    alias_candidate_style = (alias_candidate_style or "token_cost_sorted").strip().lower()
    alias_iter_idx = 0
    short_alias_alphabet: list[str] = []
    legal_alias_idx = 0
    mnemonic_alias_alphabet_by_prefix: dict[str, list[str]] = {}
    mnemonic_cursor_by_prefix: defaultdict[str, int] = defaultdict(int)
    taken_alias_bases: set[str] = set()
    static_reserved = set(_PROTECTED) | ast_protected | scope_conflicts

    if alias_style == "short":
        if alias_candidate_style == "legal_identifier_pool":
            short_alias_alphabet = build_legal_alias_alphabet(
                tokenizer,
                tok_type,
                reserved=static_reserved,
                max_n=256,
                max_alias_token_len=int(max_alias_token_len),
            )
        else:
            short_alias_alphabet = build_alias_alphabet(
                tokenizer,
                tok_type,
                style="short",
                max_n=256,
                candidate_style=alias_candidate_style,
            )

    selected: dict[tuple[str, str], str] = {}
    entries: list[AEntry] = []
    global_vocab_entries: list[dict[str, Any]] = []
    global_used_v = 0
    global_used_a = 0
    global_used_s = 0
    min_occ_reject_count = 0
    net_gain_reject_count = 0

    def _try_global_alias(field: str, literal: str) -> tuple[str, str] | None:
        if not global_aliases:
            return None
        raw = global_aliases.get((field, literal))
        if raw is None:
            return None
        ab = str(raw).strip()
        if not ab:
            return None
        if field != "string":
            if not ab.isidentifier() or keyword.iskeyword(ab):
                return None
            surf = ab
        else:
            # For string field, value can be either plain alias text (gs0)
            # or a quoted literal ("'gs0'").
            if len(ab) >= 2 and ab[0] in {"'", '"'} and ab[-1] == ab[0]:
                try:
                    inner = ast.literal_eval(ab)
                except (SyntaxError, ValueError, MemoryError):
                    return None
                if not isinstance(inner, str) or not inner:
                    return None
                ab = inner
            surf = repr(ab)
        if ab in taken_alias_bases:
            return None
        if field != "string" and ab in static_reserved:
            return None
        if _token_len(tokenizer, tok_type, surf) > int(max_alias_token_len):
            return None
        return ab, surf

    for key, spans in sorted(occ.items(), key=lambda kv: len(kv[1]), reverse=True):
        field, literal = key
        count = len(spans)
        raw_cost = _token_len(tokenizer, tok_type, literal)
        if raw_cost < int(min_raw_token_len):
            net_gain_reject_count += 1
            continue

        def _evaluate_current_alias(
            cur_alias_surface: str,
            *,
            is_global_alias: bool,
        ) -> tuple[int, int, dict[str, Any], str, int]:
            cur_alias_cost = _token_len(tokenizer, tok_type, cur_alias_surface)
            cur_vocab_kind = (
                "stage3_ab_a_global_alias" if is_global_alias else "stage3_ab_a_alias"
            )
            cur_intro_entry = {
                "token": cur_alias_surface,
                "kind": cur_vocab_kind,
                "field": field,
                "definition": literal,
            }
            cur_intro_cost = 0
            if not (is_global_alias and global_aliases_are_predefined):
                cur_intro_cost = compute_vocab_intro_cost(
                    [cur_intro_entry], mode=VOCAB_COST_MODE, tokenizer=tokenizer, tok_type=tok_type
                )
            if cost_mode == "context_aware":
                seq_delta = sum_context_aware_literal_delta(
                    text,
                    spans,
                    literal,
                    cur_alias_surface,
                    tokenizer,
                    tok_type,
                    window_chars=int(context_window_chars),
                )
                cur_gain = int(seq_delta) - int(cur_intro_cost)
            else:
                cur_gain = count * (raw_cost - cur_alias_cost) - cur_intro_cost
            return cur_alias_cost, cur_intro_cost, cur_intro_entry, cur_vocab_kind, int(cur_gain)

        g_pick = _try_global_alias(field, literal)
        global_alias_base: str | None = None
        global_alias_surface: str | None = None
        global_eval: tuple[int, int, dict[str, Any], str, int] | None = None
        if g_pick is not None:
            global_alias_base, global_alias_surface = g_pick
            global_eval = _evaluate_current_alias(global_alias_surface, is_global_alias=True)

        if count < int(min_occ):
            if global_eval is not None and int(global_eval[4]) >= int(min_net_gain):
                assert global_alias_base is not None and global_alias_surface is not None
                taken_alias_bases.add(global_alias_base)
                alias_cost, intro_cost, intro_entry, vocab_kind, gain = global_eval
                selected[key] = global_alias_surface
                entries.append(
                    AEntry(
                        field=field,
                        literal=literal,
                        alias=global_alias_surface,
                        count=count,
                        raw_cost=raw_cost,
                        alias_cost=alias_cost,
                        intro_cost=intro_cost,
                        gain=gain,
                        is_global=True,
                        vocab_kind=vocab_kind,
                    )
                )
                global_vocab_entries.append(intro_entry)
                if field == "variable":
                    global_used_v += 1
                elif field == "attribute":
                    global_used_a += 1
                elif field == "string":
                    global_used_s += 1
                continue
            min_occ_reject_count += 1
            continue

        local_alias_base: str | None = None
        local_alias_surface: str | None = None
        if alias_style == "mnemonic":
            prefix = _sanitize_prefix(literal)
            if prefix not in mnemonic_alias_alphabet_by_prefix:
                mnemonic_alias_alphabet_by_prefix[prefix] = build_alias_alphabet(
                    tokenizer, tok_type, style="mnemonic", prefix=prefix, max_n=256
                )
            picked = False
            attempts = 0
            while attempts < 512:
                cursor = mnemonic_cursor_by_prefix[prefix]
                if cursor < len(mnemonic_alias_alphabet_by_prefix[prefix]):
                    ab = mnemonic_alias_alphabet_by_prefix[prefix][cursor]
                else:
                    ab = f"_{prefix}{cursor}"
                mnemonic_cursor_by_prefix[prefix] = cursor + 1
                attempts += 1
                surf = ab if field != "string" else repr(ab)
                if ab in taken_alias_bases or ab in static_reserved:
                    continue
                if _token_len(tokenizer, tok_type, surf) > int(max_alias_token_len):
                    continue
                local_alias_base, local_alias_surface = ab, surf
                picked = True
                break
            if not picked:
                if global_eval is not None and int(global_eval[4]) >= int(min_net_gain):
                    assert global_alias_base is not None and global_alias_surface is not None
                    taken_alias_bases.add(global_alias_base)
                    alias_cost, intro_cost, intro_entry, vocab_kind, gain = global_eval
                    selected[key] = global_alias_surface
                    entries.append(
                        AEntry(
                            field=field,
                            literal=literal,
                            alias=global_alias_surface,
                            count=count,
                            raw_cost=raw_cost,
                            alias_cost=alias_cost,
                            intro_cost=intro_cost,
                            gain=gain,
                            is_global=True,
                            vocab_kind=vocab_kind,
                        )
                    )
                    global_vocab_entries.append(intro_entry)
                    if field == "variable":
                        global_used_v += 1
                    elif field == "attribute":
                        global_used_a += 1
                    elif field == "string":
                        global_used_s += 1
                    continue
                net_gain_reject_count += 1
                continue
        elif alias_candidate_style == "legal_identifier_pool":
            picked = False
            while legal_alias_idx < len(short_alias_alphabet):
                ab = short_alias_alphabet[legal_alias_idx]
                legal_alias_idx += 1
                if ab in taken_alias_bases:
                    continue
                surf = ab if field != "string" else repr(ab)
                if _token_len(tokenizer, tok_type, surf) > int(max_alias_token_len):
                    continue
                local_alias_base, local_alias_surface = ab, surf
                picked = True
                break
            if not picked:
                if global_eval is not None and int(global_eval[4]) >= int(min_net_gain):
                    assert global_alias_base is not None and global_alias_surface is not None
                    taken_alias_bases.add(global_alias_base)
                    alias_cost, intro_cost, intro_entry, vocab_kind, gain = global_eval
                    selected[key] = global_alias_surface
                    entries.append(
                        AEntry(
                            field=field,
                            literal=literal,
                            alias=global_alias_surface,
                            count=count,
                            raw_cost=raw_cost,
                            alias_cost=alias_cost,
                            intro_cost=intro_cost,
                            gain=gain,
                            is_global=True,
                            vocab_kind=vocab_kind,
                        )
                    )
                    global_vocab_entries.append(intro_entry)
                    if field == "variable":
                        global_used_v += 1
                    elif field == "attribute":
                        global_used_a += 1
                    elif field == "string":
                        global_used_s += 1
                    continue
                net_gain_reject_count += 1
                continue
        else:
            for _attempt in range(512):
                cursor = alias_iter_idx + _attempt
                if cursor < len(short_alias_alphabet):
                    ab = short_alias_alphabet[cursor]
                else:
                    ab = f"x{cursor}"
                surf = ab if field != "string" else repr(ab)
                if ab in taken_alias_bases:
                    continue
                if _token_len(tokenizer, tok_type, surf) > int(max_alias_token_len):
                    continue
                local_alias_base, local_alias_surface = ab, surf
                alias_iter_idx = cursor + 1
                break
            if local_alias_base is None:
                if global_eval is not None and int(global_eval[4]) >= int(min_net_gain):
                    assert global_alias_base is not None and global_alias_surface is not None
                    taken_alias_bases.add(global_alias_base)
                    alias_cost, intro_cost, intro_entry, vocab_kind, gain = global_eval
                    selected[key] = global_alias_surface
                    entries.append(
                        AEntry(
                            field=field,
                            literal=literal,
                            alias=global_alias_surface,
                            count=count,
                            raw_cost=raw_cost,
                            alias_cost=alias_cost,
                            intro_cost=intro_cost,
                            gain=gain,
                            is_global=True,
                            vocab_kind=vocab_kind,
                        )
                    )
                    global_vocab_entries.append(intro_entry)
                    if field == "variable":
                        global_used_v += 1
                    elif field == "attribute":
                        global_used_a += 1
                    elif field == "string":
                        global_used_s += 1
                    continue
                net_gain_reject_count += 1
                continue

        assert local_alias_base is not None and local_alias_surface is not None
        local_eval = _evaluate_current_alias(local_alias_surface, is_global_alias=False)
        local_alias_cost, local_intro_cost, local_intro_entry, local_vocab_kind, local_gain = local_eval

        pick_is_global = False
        best_alias_base = local_alias_base
        best_alias_surface = local_alias_surface
        best_alias_cost = local_alias_cost
        best_intro_cost = local_intro_cost
        best_intro_entry = local_intro_entry
        best_vocab_kind = local_vocab_kind
        best_gain = int(local_gain)

        if global_eval is not None and int(global_eval[4]) > int(best_gain):
            assert global_alias_base is not None and global_alias_surface is not None
            (
                best_alias_cost,
                best_intro_cost,
                best_intro_entry,
                best_vocab_kind,
                best_gain,
            ) = global_eval
            best_alias_base = global_alias_base
            best_alias_surface = global_alias_surface
            pick_is_global = True

        if int(best_gain) < int(min_net_gain):
            net_gain_reject_count += 1
            continue

        taken_alias_bases.add(best_alias_base)
        selected[key] = best_alias_surface
        entries.append(
            AEntry(
                field=field,
                literal=literal,
                alias=best_alias_surface,
                count=count,
                raw_cost=raw_cost,
                alias_cost=best_alias_cost,
                intro_cost=best_intro_cost,
                gain=best_gain,
                is_global=pick_is_global,
                vocab_kind=best_vocab_kind,
            )
        )
        if pick_is_global:
            global_vocab_entries.append(best_intro_entry)
            if field == "variable":
                global_used_v += 1
            elif field == "attribute":
                global_used_a += 1
            elif field == "string":
                global_used_s += 1

    spans_all: list[tuple[int, int, str]] = []
    for key, alias in selected.items():
        for st, ed in occ[key]:
            spans_all.append((st, ed, alias))
    encoded = _apply_spans(text, spans_all) if spans_all else text

    vocab_entries = [
        {"token": e.alias, "kind": e.vocab_kind, "field": e.field, "definition": e.literal}
        for e in entries
        if int(e.intro_cost) > 0
    ]
    seq_saved = sum(e.count * max(0, e.raw_cost - e.alias_cost) for e in entries)
    intro = sum(e.intro_cost for e in entries)
    occ_snapshot = {k: list(v) for k, v in occ.items()}
    return ACodecResult(
        encoded_text=encoded,
        entries=entries,
        candidates=candidates,
        selected=len(entries),
        used_entries=len(entries),
        intro_tokens=intro,
        sequence_saved=seq_saved,
        effective_net_saving=seq_saved - intro,
        vocab_entries=vocab_entries,
        reject_reason_counts=dict(reject_reasons),
        protected_name_count=protected_name_count,
        min_occ_reject_count=min_occ_reject_count,
        net_gain_reject_count=net_gain_reject_count,
        global_used_entries=global_used_v + global_used_a + global_used_s,
        global_used_entries_variable=global_used_v,
        global_used_entries_attribute=global_used_a,
        global_used_entries_string=global_used_s,
        global_vocab_entries=global_vocab_entries,
        occ=occ_snapshot,
    )


def decode_exact_aliases(text: str, entries: list[AEntry]) -> str:
    if not entries:
        return text
    name_map: dict[str, str] = {}
    string_map: dict[str, str] = {}
    for e in entries:
        if e.field == "string":
            string_map[e.alias] = e.literal
        else:
            name_map[e.alias] = e.literal
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return text
    line_starts = _line_start_offsets(text)
    spans: list[tuple[int, int, str]] = []
    for tok in toks:
        rep = None
        if tok.type == tokenize.NAME:
            rep = name_map.get(tok.string)
        elif tok.type == tokenize.STRING:
            rep = string_map.get(tok.string)
        if rep is not None:
            st = _pos_to_offset(line_starts, tok.start)
            ed = _pos_to_offset(line_starts, tok.end)
            spans.append((st, ed, rep))
    return _apply_spans(text, spans)

