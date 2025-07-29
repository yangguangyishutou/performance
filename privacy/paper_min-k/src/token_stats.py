import json
import os
import argparse
import tokenize
from io import BytesIO

"""Re-implementation: use Conditional-Consequent pattern matching to avoid
duplicate token counting.  Each syntax convention from Appendix is defined as
a pair (or set) of tokens; we detect an occurrence **only when the consequent
token closes a previously seen unmatched conditional token**.  This guarantees
that a token只会被计入一次，对应它所属的唯一类别。特别处理 `if`：若
`if` 与 `else` 出现在同一行，则视为三元表达式 (Expressions)；若 `:` 与换行
组合，则判定为语句级 (Compound Statements)。
"""

# ---------------------------------------------------------------------------
# Pattern Definitions
# ---------------------------------------------------------------------------

from enum import Enum
from typing import Union, List, Dict


class Category(str, Enum):
    DATA_MODEL = "Data Model"
    EXPRESSIONS = "Expressions"
    SINGLE = "Single Statements"
    COMPOUND = "Compound Statements"


class Pattern:
    """Represent a syntax convention pattern with one/many conditional / consequent tokens."""

    def __init__(self, name: str, category: Union[Category, str],
                 cond_tokens, cons_tokens, extra=None):
        self.name = name
        self.category = category.value if isinstance(category, Enum) else category
        # accept str or set/list
        self.cond_tokens = set(cond_tokens) if not isinstance(cond_tokens, set) else cond_tokens
        self.cons_tokens = set(cons_tokens) if not isinstance(cons_tokens, set) else cons_tokens
        self.extra = extra  # auxiliary information for context-based decision


# Build patterns to match Appendix table (34 conventions)
PATTERNS: List[Pattern] = []

# Data Model
PATTERNS += [
    Pattern("list_bracket", Category.DATA_MODEL, "[", "]"),
    Pattern("dict_set_brace", Category.DATA_MODEL, "{", "}"),
    Pattern("tuple_paren", Category.DATA_MODEL, "(", ")", extra="tuple"),
    Pattern("string_single", Category.DATA_MODEL, "'", "'"),
    Pattern("string_double", Category.DATA_MODEL, '"', '"'),
]

# Expressions
PATTERNS += [
    Pattern("call_paren", Category.EXPRESSIONS, "(", ")", extra="call"),
    Pattern("lambda_expr", Category.EXPRESSIONS, "lambda", ":"),
    Pattern("cond_expr", Category.EXPRESSIONS, "if_expr", "else"),
    Pattern("comprehension", Category.EXPRESSIONS, {"for"}, {"in", "]", "}", ")"}),
    # chained comparison uses special handling, see scan_code
]

# Single Statements
PATTERNS += [
    Pattern("import_as", Category.SINGLE, "import", "as"),
    Pattern("from_import", Category.SINGLE, "from", "import"),
    Pattern("assert_msg", Category.SINGLE, "assert", ","),
]

# Compound Statements
PATTERNS += [
    Pattern("if_stmt", Category.COMPOUND, "if_stmt", ":"),
    Pattern("elif_stmt", Category.COMPOUND, "elif", ":"),
    Pattern("else_stmt", Category.COMPOUND, "else", ":"),
    Pattern("for_stmt", Category.COMPOUND, "for", ":"),
    Pattern("while_stmt", Category.COMPOUND, "while", ":"),
    Pattern("try_stmt", Category.COMPOUND, "try", ":"),
    Pattern("except_stmt", Category.COMPOUND, {"except", "except*"}, ":"),
    Pattern("finally_stmt", Category.COMPOUND, "finally", ":"),
    Pattern("with_stmt", Category.COMPOUND, "with", ":"),
    Pattern("class_stmt", Category.COMPOUND, "class", ":"),
    Pattern("def_stmt", Category.COMPOUND, "def", ":"),
    Pattern("async_def", Category.COMPOUND, {"async"}, {"def"}),  # async def ...
    Pattern("async_for", Category.COMPOUND, {"async"}, {"for"}),
    Pattern("async_with", Category.COMPOUND, {"async"}, {"with"}),
    Pattern("match_stmt", Category.COMPOUND, "match", {"case", ":"}),
]

# ---------------------------------------------------------------------------
# Helper structures for quick lookup
# ---------------------------------------------------------------------------

COND_MAP: Dict[str, List[int]] = {}
CONS_MAP: Dict[str, List[int]] = {}
for idx, pat in enumerate(PATTERNS):
    for tok in pat.cond_tokens:
        COND_MAP.setdefault(tok, []).append(idx)
    for tok in pat.cons_tokens:
        CONS_MAP.setdefault(tok, []).append(idx)
# ---------------------------------------------------------------------------
# Token scanning with stacks
# ---------------------------------------------------------------------------


def decide_paren_pattern(prev_tok):
    """Return pattern id for '(' depending on context (call vs tuple)."""
    if prev_tok and prev_tok.type == tokenize.NAME:
        # likely function call
        for idx, p in enumerate(PATTERNS):
            if p.name == "call_paren":
                return idx
    # default tuple/grouping
    for idx, p in enumerate(PATTERNS):
        if p.name == "tuple_paren":
            return idx


def decide_if_pattern(prev_significant_tok, current_tok):
    """Differentiate between if-expression and if-statement."""
    if prev_significant_tok and prev_significant_tok.start[0] == current_tok.start[0]:
        # same line -> expression
        for idx, p in enumerate(PATTERNS):
            if p.name == "cond_expr":
                return idx
    else:
        for idx, p in enumerate(PATTERNS):
            if p.name == "if_stmt":
                return idx


def scan_code(code: str):
    """Return total tokens and category counts using improved pattern matching."""
    total_tokens = 0
    cat_counts = {p.category: 0 for p in PATTERNS}

    stack: List[int] = []  # pattern indices
    prev_tok = None
    prev_significant = None

    # helper for chained comparison detection
    comp_pending = False  # whether a comp_op seen but not closed
    comp_line_no = -1

    COMP_OPS = {"<", "<=", ">", ">=", "==", "!=", "in", "is"}

    # --- Pre-computation for performance ---
    # Get pattern indices for specific pattern names to avoid searching list every time
    comprehension_pids = {
        idx for idx, p in enumerate(PATTERNS) if p.name == "comprehension"
    }
    for_stmt_pids = {
        idx for idx, p in enumerate(PATTERNS) if p.name == "for_stmt"
    }
    loop_related_pids = comprehension_pids.union(for_stmt_pids)
    # ---


    g = tokenize.tokenize(BytesIO(code.encode("utf-8")).readline)
    try:
        for tok in g:
            if tok.type in (tokenize.ENCODING, tokenize.ENDMARKER):
                continue

            tok_str = tok.string
            total_tokens += 1

            # --- Unary & Special Patterns ---
            # STRING literal: count as one syntax token (represents paired quotes)
            if tok.type == tokenize.STRING:
                cat_counts[Category.DATA_MODEL.value] += 1
            
            # Handle object access: '.' following a NAME
            elif tok_str == "." and prev_significant and prev_significant.type == tokenize.NAME:
                cat_counts[Category.DATA_MODEL.value] += 1  # count only the dot, avoid double-counting identifier

            # Scope Declaration
            elif tok_str in {"global", "nonlocal"}:
                 cat_counts[Category.SINGLE.value] += 1

            # Comparison Operators, with context check for 'in'
            elif tok_str in COMP_OPS:
                is_part_of_for_loop = False
                if tok_str == 'in':
                    # Check if 'for' is on the stack, indicating a comprehension or loop context
                    for pid_on_stack in reversed(stack):
                        if pid_on_stack in loop_related_pids:
                            is_part_of_for_loop = True
                            break
                if not is_part_of_for_loop:
                    cat_counts[Category.EXPRESSIONS.value] += 1
            
            # --- Paired Patterns ---
            # Consequent handling (pop)
            for pid in CONS_MAP.get(tok_str, []):
                for j in range(len(stack) - 1, -1, -1):
                    if stack[j] == pid:
                        # match found — pop and count as 1 event
                        stack.pop(j)
                        cat_counts[PATTERNS[pid].category] += 1
                        break
                else:
                    continue
                break

            # Conditional push handling
            push_handled = False
            if tok_str == "(":
                pid = decide_paren_pattern(prev_significant)
                stack.append(pid)
                push_handled = True
            elif tok_str == "if":
                pid = decide_if_pattern(prev_significant, tok)
                stack.append(pid)
                push_handled = True

            if not push_handled and tok_str in COND_MAP:
                for pid in COND_MAP[tok_str]:
                    # async special: ensure next token matches expected consequent in extra? skip for simplicity
                    stack.append(pid)

            # update previous trackers
            if tok.type not in (tokenize.NEWLINE, tokenize.NL, tokenize.INDENT, tokenize.DEDENT):
                prev_significant = tok
            prev_tok = tok
            if tok.type == tokenize.NEWLINE:
                comp_pending = False  # reset at line end
    except tokenize.TokenError:
        pass

    return total_tokens, cat_counts


def count_tokens(code: str):
    return scan_code(code)


def process_file(jsonl_path):
    total_tokens = 0
    cat_totals = {p.category: 0 for p in PATTERNS}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                code = obj.get("function", "")
                t_total, t_cat = count_tokens(code)
                total_tokens += t_total
                for cat in cat_totals:
                    cat_totals[cat] += t_cat.get(cat, 0)
            except json.JSONDecodeError:
                continue
    return total_tokens, cat_totals


def main():
    parser = argparse.ArgumentParser(
        description="Compute syntax token statistics for benchmark dataset")
    parser.add_argument("--dataset_dir", default="python_dataset",
                        help="Path to dataset directory containing positive and negative subdirs")
    args = parser.parse_args()

    pos_path = os.path.join(args.dataset_dir, "positive", "positive.jsonl")
    neg_path = os.path.join(args.dataset_dir, "negative", "negative.jsonl")

    grand_total = 0
    categories = sorted({p.category for p in PATTERNS})
    grand_cat = {cat: 0 for cat in categories}

    for p in [pos_path, neg_path]:
        if os.path.exists(p):
            total, cat = process_file(p)
            grand_total += total
            for cat_name in categories:
                grand_cat[cat_name] += cat[cat_name]
        else:
            print(f"Warning: {p} not found, skipping.")

    syntax_total = sum(grand_cat.values())
    ratio = syntax_total / grand_total if grand_total else 0

    print("\n===== Syntax Token Statistics =====")
    for cat in grand_cat:
        print(f"{cat}: {grand_cat[cat]}")
    print(f"Total Syntax Tokens: {syntax_total}")
    print(f"Total Tokens: {grand_total}")
    print(f"Syntax Tokens Ratio: {ratio:.4f}")

    # Output LaTeX lines for easy copy-paste
    print("\nLaTeX Table Lines:")
    for cat in grand_cat:
        print(f"{cat} & {grand_cat[cat]} \\")
    print("\\midrule")
    print(f"\\multicolumn{{2}}{{l}}{{\\textbf{{Total Syntax Tokens:}} {syntax_total}}} \\")
    print(f"\\multicolumn{{2}}{{l}}{{\\textbf{{Total Tokens:}} {grand_total}}} \\")
    print(f"\\multicolumn{{2}}{{l}}{{\\textbf{{Syntax Tokens Ratio:}} {ratio:.4f}}} \\")


if __name__ == "__main__":
    main() 