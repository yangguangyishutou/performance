from __future__ import annotations

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class GlobalDictionary:
    version: str = ""
    source: str = ""
    a_alias_map: dict[tuple[str, str], str] = field(default_factory=dict)
    b_norm_map: dict[str, str] = field(default_factory=dict)
    b_definition_by_code: dict[str, str] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


_CACHE: dict[str, tuple[float, int, GlobalDictionary]] = {}


def empty_global_dictionary() -> GlobalDictionary:
    return GlobalDictionary()


def _parse_code_inner(raw: Any) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if len(s) >= 2 and s[0] in {"'", '"'} and s[-1] == s[0]:
        try:
            inner = ast.literal_eval(s)
        except (SyntaxError, ValueError, MemoryError):
            return None
        if isinstance(inner, str) and inner:
            return inner
        return None
    return s


def _as_str(x: Any) -> str:
    return "" if x is None else str(x)


def load_global_dictionary(path: str | os.PathLike[str] | None) -> GlobalDictionary:
    if not path:
        return empty_global_dictionary()
    fp = Path(path)
    if not fp.exists() or not fp.is_file():
        return empty_global_dictionary()

    key = str(fp.resolve())
    try:
        st = fp.stat()
        mtime = float(st.st_mtime)
        size = int(st.st_size)
    except OSError:
        return empty_global_dictionary()

    cached = _CACHE.get(key)
    if cached is not None and cached[0] == mtime and cached[1] == size:
        return cached[2]

    try:
        import json

        raw = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        gd = empty_global_dictionary()
        _CACHE[key] = (mtime, size, gd)
        return gd

    a_alias_map: dict[tuple[str, str], str] = {}
    b_norm_map: dict[str, str] = {}
    b_definition_by_code: dict[str, str] = {}

    for row in (raw.get("a_entries", []) or raw.get("a", []) or []):
        if not isinstance(row, dict):
            continue
        field = _as_str(row.get("field")).strip().lower()
        literal = _as_str(row.get("literal"))
        alias = _as_str(row.get("alias")).strip()
        if field not in {"variable", "attribute", "string"}:
            continue
        if not literal or not alias:
            continue
        a_alias_map[(field, literal)] = alias

    for row in (raw.get("b_entries", []) or raw.get("b", []) or []):
        if not isinstance(row, dict):
            continue
        norm_key = _as_str(row.get("norm_key")).strip()
        code_inner = _parse_code_inner(row.get("code"))
        if not norm_key or not code_inner:
            continue
        b_norm_map[norm_key] = code_inner
        definition = _as_str(row.get("definition")).strip()
        if definition:
            b_definition_by_code[code_inner] = definition

    gd = GlobalDictionary(
        version=_as_str(raw.get("version")).strip(),
        source=_as_str(raw.get("source")).strip(),
        a_alias_map=a_alias_map,
        b_norm_map=b_norm_map,
        b_definition_by_code=b_definition_by_code,
        meta=dict(raw.get("summary", {}) or {}),
    )
    _CACHE[key] = (mtime, size, gd)
    return gd

