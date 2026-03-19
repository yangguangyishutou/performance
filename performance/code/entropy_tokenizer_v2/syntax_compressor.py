"""
Stage 1 — Data-Driven Syntax Compression (v2, independent framework)

Key difference from SimPy / v1:
  • v1 / SimPy: replace only the *fixed* text of a skeleton with one new token,
    keeping keyword tokens in place.
  • v2 (here): replace the ENTIRE statement header (keyword + structure + slot
    labels) with a single operator token <SYN_N>, keeping only the *slot
    values* (variable expressions).  This is a more aggressive "整体替换".

Example:
    Original:   for item in my_list:
    v1 result:  <OP_3> item in my_list :       (only "for ... in ...:" compressed)
    v2 result:  <SYN_3> item my_list            (keyword "for", "in", ":" gone)

Skeleton format (used as canonical pattern key):
    "for {0} in {1}:"     ← anonymised by _compute_skeleton()

MDL selection:
    Greedy forward selection minimising:
        L_total = N_compressed · log₂(V₀ + |S|) + Σ_k cb_k · log₂(V₀)

    A skeleton is accepted iff adding it *reduces* total description length.
    Each accepted skeleton consumes:
        savings = original_header_tokens − (1 + num_slots)
        cost    = MDL_CODEBOOK_OVERHEAD tokens
"""

import ast
import copy
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional

from config_v2 import AST_MIN_FREQ, MDL_CODEBOOK_OVERHEAD

# ─────────────────────────────────────────────────────────────────────────────
# Skeleton computation  (independent reimplementation, no v1 imports)
# ─────────────────────────────────────────────────────────────────────────────

_SKIP_NODE_TYPES = (ast.Pass, ast.Break, ast.Continue)
_TRY_TYPES = tuple(
    getattr(ast, n) for n in ("Try", "TryStar") if hasattr(ast, n)
)


def _compute_skeleton(node: ast.AST) -> Optional[str]:
    """
    Generate a canonical skeleton string for any statement-level AST node.

    Algorithm:
      1. Deep-copy the node.
      2. Strip block bodies (body / orelse / handlers / finally) so only the
         statement *header* remains.
      3. Anonymise all Name identifiers and non-trivial Constants with _PHn_.
      4. ast.unparse → take first line → substitute placeholder markers.

    Returns None for trivially short or unsupported nodes.
    """
    if not isinstance(node, (ast.stmt, ast.ExceptHandler)):
        return None
    if isinstance(node, _SKIP_NODE_TYPES + _TRY_TYPES):
        return None

    nc   = copy.deepcopy(node)
    ctr  = [0]

    def _ph() -> str:
        idx = ctr[0]; ctr[0] += 1
        return f"_PH{idx}_"

    # Strip body / orelse / finalbody to isolate header
    for attr in ("body", "orelse", "finalbody"):
        if getattr(nc, attr, None):
            setattr(nc, attr, [ast.Pass()])
    if getattr(nc, "handlers", None):
        nc.handlers = []
    if hasattr(nc, "decorator_list"):
        nc.decorator_list = []

    # Anonymise string-attribute names
    if isinstance(nc, (ast.FunctionDef, ast.AsyncFunctionDef)):
        nc.name = _ph()
        for arg_list in (nc.args.args, nc.args.posonlyargs, nc.args.kwonlyargs):
            for arg in arg_list:
                arg.arg = _ph()
        if nc.args.vararg:  nc.args.vararg.arg = _ph()
        if nc.args.kwarg:   nc.args.kwarg.arg  = _ph()
    elif isinstance(nc, ast.ClassDef):
        nc.name = _ph()
    elif isinstance(nc, ast.ExceptHandler) and nc.name:
        nc.name = _ph()
    elif isinstance(nc, ast.Global):
        nc.names = [_ph() for _ in nc.names]
    elif isinstance(nc, ast.Nonlocal):
        nc.names = [_ph() for _ in nc.names]
    elif isinstance(nc, ast.ImportFrom):
        if nc.module: nc.module = _ph()
        for a in nc.names:
            a.name = _ph()
            if a.asname: a.asname = _ph()
    elif isinstance(nc, ast.Import):
        for a in nc.names:
            a.name = _ph()
            if a.asname: a.asname = _ph()

    # Anonymise all Name / non-trivial Constant leaves
    class _Anon(ast.NodeTransformer):
        def visit_Name(self, n):
            n.id = _ph(); return n
        def visit_Constant(self, n):
            if n.value in (None, True, False): return n
            try:    n.value = _ph()
            except: pass
            return n

    try:
        nc = _Anon().visit(nc)
        ast.fix_missing_locations(nc)
        text = ast.unparse(nc)
    except Exception:
        return None

    skeleton = text.split("\n")[0]
    for i in range(ctr[0]):
        skeleton = skeleton.replace(f"'_PH{i}_'", f"{{{i}}}")
        skeleton = skeleton.replace(f'"_PH{i}_"', f"{{{i}}}")
        skeleton = skeleton.replace(f"_PH{i}_",   f"{{{i}}}")

    stripped = skeleton.strip()
    if not stripped or len(stripped) < 4:
        return None
    return skeleton


# ─────────────────────────────────────────────────────────────────────────────
# Slot extraction (the variable parts that survive compression)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_slots(node: ast.AST) -> list[str]:
    """
    Return the ordered list of slot-value strings for a given AST node.
    These are the variable expressions kept after the header is replaced.
    """
    slots: list[str] = []

    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        slots.append(node.name)
        for a in node.args.args + node.args.posonlyargs + node.args.kwonlyargs:
            slots.append(a.arg)
        if node.args.vararg: slots.append(node.args.vararg.arg)
        if node.args.kwarg:  slots.append(node.args.kwarg.arg)

    elif isinstance(node, ast.ClassDef):
        slots.append(node.name)
        for base in node.bases:
            slots.append(ast.unparse(base))

    elif isinstance(node, (ast.For, ast.AsyncFor)):
        slots.append(ast.unparse(node.target))
        slots.append(ast.unparse(node.iter))

    elif isinstance(node, ast.While):
        slots.append(ast.unparse(node.test))

    elif isinstance(node, ast.If):
        slots.append(ast.unparse(node.test))

    elif isinstance(node, ast.With):
        for item in node.items:
            slots.append(ast.unparse(item.context_expr))
            if item.optional_vars:
                slots.append(ast.unparse(item.optional_vars))

    elif isinstance(node, ast.Return):
        if node.value:
            slots.append(ast.unparse(node.value))

    elif isinstance(node, ast.Assign):
        for t in node.targets:
            slots.append(ast.unparse(t))
        slots.append(ast.unparse(node.value))

    elif isinstance(node, ast.AugAssign):
        slots.append(ast.unparse(node.target))
        slots.append(ast.unparse(node.value))

    elif isinstance(node, ast.AnnAssign):
        slots.append(ast.unparse(node.target))
        slots.append(ast.unparse(node.annotation))
        if node.value:
            slots.append(ast.unparse(node.value))

    elif isinstance(node, ast.Expr):
        slots.append(ast.unparse(node.value))

    elif isinstance(node, ast.Import):
        for alias in node.names:
            slots.append(alias.name)
            if alias.asname: slots.append(alias.asname)

    elif isinstance(node, ast.ImportFrom):
        if node.module: slots.append(node.module)
        for alias in node.names:
            slots.append(alias.name)
            if alias.asname: slots.append(alias.asname)

    elif isinstance(node, ast.Raise):
        if node.exc: slots.append(ast.unparse(node.exc))

    elif isinstance(node, ast.Assert):
        slots.append(ast.unparse(node.test))
        if node.msg: slots.append(ast.unparse(node.msg))

    elif isinstance(node, ast.Delete):
        for t in node.targets:
            slots.append(ast.unparse(t))

    elif isinstance(node, ast.ExceptHandler):
        if node.type: slots.append(ast.unparse(node.type))
        if node.name: slots.append(node.name)

    return slots


# ─────────────────────────────────────────────────────────────────────────────
# Mining: count skeleton frequencies across a corpus
# ─────────────────────────────────────────────────────────────────────────────

def mine_skeletons(sources: list[str], min_freq: int = AST_MIN_FREQ) -> Counter:
    """
    Count how many times each skeleton appears across all sources.
    Returns {skeleton_str: count} filtered by min_freq.
    """
    counter: Counter = Counter()
    for src in sources:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            sk = _compute_skeleton(node)
            if sk:
                counter[sk] += 1
    return Counter({k: v for k, v in counter.items() if v >= min_freq})


# ─────────────────────────────────────────────────────────────────────────────
# Header token counting helpers
# ─────────────────────────────────────────────────────────────────────────────

def _header_token_count(skeleton: str, tokenizer, tok_type: str) -> int:
    """
    Count how many tokens the *fixed* part of the skeleton takes.
    We use the skeleton string itself (with {N} placeholders removed) as proxy.
    """
    fixed = re.sub(r'\{\d+\}', '', skeleton)
    fixed = fixed.strip()
    if not fixed:
        return 1
    try:
        if tok_type == "tiktoken":
            return len(tokenizer.encode(fixed, allowed_special="all"))
        return len(tokenizer.encode(fixed, add_special_tokens=False))
    except Exception:
        return max(1, len(fixed.split()))


def _num_slots(skeleton: str) -> int:
    return len(re.findall(r'\{\d+\}', skeleton))


# ─────────────────────────────────────────────────────────────────────────────
# MDL-based skeleton selection
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class SkeletonCandidate:
    skeleton:    str
    frequency:   int
    fixed_tokens: int    # tokens in fixed part (to be replaced by <SYN_N>)
    num_slots:   int     # number of variable slot expressions
    savings_per_instance: int   # fixed_tokens - 1 (one new token replaces all fixed)
    codebook_cost: int          # MDL_CODEBOOK_OVERHEAD
    mdl_net_benefit: float      # spi * freq - codebook_cost


def build_candidate_pool(
    skeleton_counts: Counter,
    tokenizer,
    tok_type: str,
) -> list[SkeletonCandidate]:
    """
    Build the ranked candidate pool for MDL selection.
    Each candidate's savings_per_instance = (header_fixed_tokens - 1 - 0)
    because <SYN_N> is ONE new token replacing all fixed tokens.

    Note: slot values are kept, so we don't subtract them from savings here.
    The actual per-instance saving is fixed_tokens - 1 (we spend 1 new token
    instead of fixed_tokens).
    """
    candidates: list[SkeletonCandidate] = []
    for sk, freq in skeleton_counts.items():
        fixed_toks = _header_token_count(sk, tokenizer, tok_type)
        spi        = max(0, fixed_toks - 1)   # savings: fixed → 1 new token
        if spi <= 0:
            continue
        cb   = MDL_CODEBOOK_OVERHEAD
        cand = SkeletonCandidate(
            skeleton=sk,
            frequency=freq,
            fixed_tokens=fixed_toks,
            num_slots=_num_slots(sk),
            savings_per_instance=spi,
            codebook_cost=cb,
            mdl_net_benefit=spi * freq - cb,
        )
        candidates.append(cand)
    candidates.sort(key=lambda c: c.mdl_net_benefit, reverse=True)
    return candidates


def greedy_mdl_select(
    candidates: list[SkeletonCandidate],
    N_baseline: int,
    V0: int,
) -> list[SkeletonCandidate]:
    """
    Greedy forward selection: accept a skeleton iff adding it reduces L_total.

    ΔL_k = N_new · log₂(V₀+k) − N_curr · log₂(V₀+k−1) + cb_k · log₂(V₀)

    Returns the list of accepted skeletons (ordered by acceptance).
    """
    log2_V0   = math.log2(V0) if V0 > 1 else 1.0
    N_current = N_baseline
    S_size    = 0
    accepted: list[SkeletonCandidate] = []

    for cand in candidates:
        if N_current <= 0:
            break
        freq = cand.frequency
        if freq == 0:
            continue

        log2_V_curr = math.log2(V0 + S_size) if (V0 + S_size) > 1 else 1.0
        log2_V_new  = math.log2(V0 + S_size + 1)

        N_new  = N_current - cand.savings_per_instance * freq
        delta  = N_new * log2_V_new - N_current * log2_V_curr + cand.codebook_cost * log2_V0

        if delta >= 0:
            break    # further candidates have lower benefit — stop

        accepted.append(cand)
        N_current = N_new
        S_size   += 1

    return accepted


# ─────────────────────────────────────────────────────────────────────────────
# Source transformation: apply syntax compression to one file
# ─────────────────────────────────────────────────────────────────────────────

def _find_header_end_line(node: ast.AST, total_lines: int) -> int:
    """
    For block statements, return the line number of the last header line
    (i.e., the line containing the ':' before the body).
    For simple statements, that is just node.lineno.
    """
    body_first_line: Optional[int] = None
    for attr in ("body", "handlers", "orelse"):
        children = getattr(node, attr, None)
        if children:
            child_line = getattr(children[0], "lineno", None)
            if child_line is not None:
                if body_first_line is None or child_line < body_first_line:
                    body_first_line = child_line

    if body_first_line is not None and body_first_line > node.lineno:
        return body_first_line - 1
    return node.lineno


def compress_source_syntax(
    source: str,
    selected: list[SkeletonCandidate],
) -> str:
    """
    Apply syntax compression to a source string.

    For each selected skeleton:
      - Find all matching statement nodes in the AST.
      - Replace their header line(s) with:
            <SYN_N> slot_val_1 slot_val_2 ...
      - Leave body lines untouched (indentation removal happens in Stage 2).

    Returns the transformed source (no longer valid Python).
    """
    if not selected:
        return source

    # Build lookup: skeleton → operator token string
    skeleton_to_op: dict[str, str] = {
        cand.skeleton: f"<SYN_{i}>"
        for i, cand in enumerate(selected)
    }

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source

    lines = source.splitlines()

    # Collect replacements: {header_start_line: (header_end_line, replacement_str)}
    # line numbers are 1-based (as in AST)
    replacements: dict[int, tuple[int, str]] = {}

    for node in ast.walk(tree):
        sk = _compute_skeleton(node)
        if not sk or sk not in skeleton_to_op:
            continue
        op_tok  = skeleton_to_op[sk]
        slots   = _extract_slots(node)
        slot_str = " ".join(slots) if slots else ""
        compressed = f"{op_tok} {slot_str}".strip()

        start_line = node.lineno                               # 1-based
        end_line   = _find_header_end_line(node, len(lines))  # 1-based

        # Avoid double-replacing nested nodes that share the same start line
        if start_line not in replacements:
            replacements[start_line] = (end_line, compressed)

    if not replacements:
        return source

    # Apply replacements — build output line by line
    skip_until = -1
    result: list[str] = []
    for lineno, line in enumerate(lines, start=1):
        if lineno <= skip_until:
            continue
        if lineno in replacements:
            end_line, compressed = replacements[lineno]
            result.append(compressed)
            skip_until = end_line
        else:
            result.append(line)

    return "\n".join(result)
