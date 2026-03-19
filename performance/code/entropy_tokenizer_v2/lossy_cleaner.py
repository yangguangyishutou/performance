"""
Stage 2 — Lossy / Lossless Code Cleaner

Rules applied in order:
  Lossless (structure preserved, code stays valid Python):
    R01  Remove # inline comments         (uses tokenize for accuracy)
    R02  Remove blank lines
    R03  Remove trailing whitespace

  Lossy (structural information destroyed, code becomes invalid Python):
    R05  Remove docstrings                (triple-quoted string statements)
    R04  Remove indentation               (flattens all block structure)

NOTE: R04/R05 are intentionally lossy — the compressed form cannot be
      re-parsed as Python.  This is acceptable for representation/retrieval
      tasks; do NOT use for code generation benchmarks.
"""

import ast
import io
import re
import tokenize
from dataclasses import dataclass, field
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Configuration & Stats
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CleaningConfig:
    remove_comments:            bool = True
    remove_blank_lines:         bool = True
    remove_trailing_whitespace: bool = True
    remove_docstrings:          bool = True   # LOSSY
    remove_indentation:         bool = True   # LOSSY


@dataclass
class CleaningStats:
    original_chars:             int = 0
    cleaned_chars:              int = 0
    removed_blank_lines:        int = 0
    removed_docstring_chars:    int = 0
    removed_indent_chars:       int = 0

    @property
    def char_reduction_pct(self) -> float:
        if self.original_chars == 0:
            return 0.0
        return (1.0 - self.cleaned_chars / self.original_chars) * 100.0

    def __add__(self, other: "CleaningStats") -> "CleaningStats":
        return CleaningStats(
            original_chars          = self.original_chars          + other.original_chars,
            cleaned_chars           = self.cleaned_chars           + other.cleaned_chars,
            removed_blank_lines     = self.removed_blank_lines     + other.removed_blank_lines,
            removed_docstring_chars = self.removed_docstring_chars + other.removed_docstring_chars,
            removed_indent_chars    = self.removed_indent_chars    + other.removed_indent_chars,
        )


# ─────────────────────────────────────────────────────────────────────────────
# R05 — Docstring removal
# ─────────────────────────────────────────────────────────────────────────────

def _remove_docstrings(source: str) -> tuple[str, int]:
    """
    Remove standalone docstring expressions from functions, classes, and modules.
    Uses AST to precisely locate docstring nodes; falls back to regex.
    Returns (cleaned_source, chars_removed).
    """
    removed_chars = 0
    try:
        tree = ast.parse(source)
    except SyntaxError:
        before = len(source)
        source = re.sub(r'"""[\s\S]*?"""', '', source)
        source = re.sub(r"'''[\s\S]*?'''", '', source)
        return source, before - len(source)

    docstring_line_ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef, ast.Module)):
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                ds = node.body[0]
                docstring_line_ranges.append((ds.lineno, ds.end_lineno))

    if not docstring_line_ranges:
        return source, 0

    excluded: set[int] = set()
    for start, end in docstring_line_ranges:
        for ln in range(start, end + 1):
            excluded.add(ln)

    lines = source.splitlines(keepends=True)
    kept, removed = [], []
    for i, line in enumerate(lines, start=1):
        if i in excluded:
            removed.append(line)
        else:
            kept.append(line)

    removed_chars = sum(len(l) for l in removed)
    return "".join(kept), removed_chars


# ─────────────────────────────────────────────────────────────────────────────
# R01 — Inline comment removal (tokenize-based)
# ─────────────────────────────────────────────────────────────────────────────

def _remove_comments(source: str) -> str:
    """
    Strip # comments using Python's tokenize module so comments inside
    string literals are never accidentally touched.
    Falls back to regex on tokenize error.
    """
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return re.sub(r'(?m)#[^\n]*', '', source)

    comment_cols: dict[int, int] = {}
    for tok in toks:
        if tok.type == tokenize.COMMENT:
            comment_cols[tok.start[0]] = tok.start[1]

    if not comment_cols:
        return source

    result = []
    for i, line in enumerate(source.splitlines(keepends=True), start=1):
        if i in comment_cols:
            col = comment_cols[i]
            stripped = line[:col].rstrip()
            result.append(stripped + "\n" if stripped else "\n")
        else:
            result.append(line)
    return "".join(result)


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def clean_code(
    source: str,
    config: Optional[CleaningConfig] = None,
) -> tuple[str, CleaningStats]:
    """
    Apply the full cleaning pipeline to one code string.
    Returns (cleaned_source, stats).

    Pipeline order:
        R05 docstrings  →  R01 comments  →  R03 trailing ws
        →  R02 blank lines  →  R04 indentation
    """
    if config is None:
        config = CleaningConfig()

    stats = CleaningStats(original_chars=len(source))

    # R05 — docstrings (needs valid AST, do first)
    if config.remove_docstrings:
        source, removed = _remove_docstrings(source)
        stats.removed_docstring_chars = removed

    # R01 — inline comments
    if config.remove_comments:
        source = _remove_comments(source)

    lines = source.splitlines()

    # R03 — trailing whitespace
    if config.remove_trailing_whitespace:
        lines = [ln.rstrip() for ln in lines]

    # R02 — blank lines
    if config.remove_blank_lines:
        original_count = len(lines)
        lines = [ln for ln in lines if ln.strip()]
        stats.removed_blank_lines = original_count - len(lines)

    # R04 — indentation (LOSSY)
    if config.remove_indentation:
        indent_chars = sum(len(ln) - len(ln.lstrip()) for ln in lines)
        stats.removed_indent_chars = indent_chars
        lines = [ln.lstrip() for ln in lines]

    source = "\n".join(lines)
    stats.cleaned_chars = len(source)
    return source, stats


def clean_corpus(
    sources: list[str],
    config: Optional[CleaningConfig] = None,
) -> tuple[list[str], CleaningStats]:
    """Clean a list of code strings and return aggregate stats."""
    if config is None:
        config = CleaningConfig()

    cleaned_list: list[str] = []
    total = CleaningStats()
    for src in sources:
        cleaned, s = clean_code(src, config)
        cleaned_list.append(cleaned)
        total = total + s
    return cleaned_list, total


# ─────────────────────────────────────────────────────────────────────────────
# Partial cleaning helpers (used by the pipeline at specific stages)
# ─────────────────────────────────────────────────────────────────────────────

def lossless_clean(source: str) -> tuple[str, CleaningStats]:
    """Only apply lossless rules (R01-R03). Code remains valid Python."""
    cfg = CleaningConfig(
        remove_comments=True,
        remove_blank_lines=True,
        remove_trailing_whitespace=True,
        remove_docstrings=False,
        remove_indentation=False,
    )
    return clean_code(source, cfg)


def lossy_clean(source: str) -> tuple[str, CleaningStats]:
    """Apply all rules including lossy ones (R04+R05)."""
    return clean_code(source, CleaningConfig())
