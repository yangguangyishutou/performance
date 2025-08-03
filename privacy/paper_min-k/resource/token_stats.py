import json
import os
import argparse
import tokenize
from io import BytesIO
from typing import Union, List, Dict
from enum import Enum

class Category(str, Enum):
    DATA_MODEL = "Data Model"
    EXPRESSIONS = "Expressions"
    SINGLE = "Single Statements"
    COMPOUND = "Compound Statements"

class Pattern:
    def __init__(self, name: str, category: Union[Category, str],
                 cond_tokens, cons_tokens, extra=None):
        self.name = name
        self.category = category.value if isinstance(category, Enum) else category
        self.cond_tokens = set(cond_tokens) if not isinstance(cond_tokens, set) else cond_tokens
        self.cons_tokens = set(cons_tokens) if not isinstance(cons_tokens, set) else cons_tokens

PATTERNS: List[Pattern] = [
    Pattern("list", Category.DATA_MODEL, "[", "]"),
    Pattern("dict_set", Category.DATA_MODEL, "{", "}"),
    Pattern("tuple", Category.DATA_MODEL, "(", ")"),
    Pattern("call", Category.EXPRESSIONS, "(", ")"),
    Pattern("lambda", Category.EXPRESSIONS, "lambda", ":"),
    Pattern("conditional_expr", Category.EXPRESSIONS, "if", "else"),
    Pattern("comprehension_for_in", Category.EXPRESSIONS, "for", "in"),
    Pattern("comprehension_close", Category.EXPRESSIONS, "in", {"]", "}", ")"}),
    Pattern("import_as", Category.SINGLE, "import", "as"),
    Pattern("from_import", Category.SINGLE, "from", "import"),
    Pattern("assert_msg", Category.SINGLE, "assert", ","),
    Pattern("if_colon", Category.COMPOUND, "if", ":"),
    Pattern("if_body", Category.COMPOUND, ":", {"INDENT", "elif", "else"}),
    Pattern("elif_colon", Category.COMPOUND, "elif", ":"),
    Pattern("else_colon", Category.COMPOUND, "else", ":"),
    Pattern("for_in", Category.COMPOUND, "for", "in"),
    Pattern("for_colon", Category.COMPOUND, "in", ":"),
    Pattern("for_body", Category.COMPOUND, ":", "INDENT"),
    Pattern("try_colon", Category.COMPOUND, "try", ":"),
    Pattern("try_body", Category.COMPOUND, ":", {"INDENT", "except", "except*"}),
    Pattern("try_finally_else", Category.COMPOUND, "INDENT", {"finally", "else"}),
    Pattern("except_as", Category.COMPOUND, {"except", "except*"}, "as"),
    Pattern("except_colon", Category.COMPOUND, "as", ":"),
    Pattern("except_body", Category.COMPOUND, ":", "INDENT"),
    Pattern("with_as", Category.COMPOUND, "with", "as"),
    Pattern("with_colon_as", Category.COMPOUND, "as", ":"),
    Pattern("with_colon_no_as", Category.COMPOUND, "with", ":"),
    Pattern("with_body", Category.COMPOUND, ":", "INDENT"),
    Pattern("class_paren", Category.COMPOUND, "class", "("),
    Pattern("class_colon", Category.COMPOUND, ")", ":"),
    Pattern("class_body", Category.COMPOUND, ":", "INDENT"),
    Pattern("def_paren", Category.COMPOUND, "def", "("),
    Pattern("def_returns", Category.COMPOUND, ")", "->"),
    Pattern("def_colon", Category.COMPOUND, {"->", ")"}, ":"),
    Pattern("def_body", Category.COMPOUND, ":", "INDENT"),
    Pattern("while_colon", Category.COMPOUND, "while", ":"),
    Pattern("while_body", Category.COMPOUND, ":", {"INDENT", "else"}),
    Pattern("match_colon", Category.COMPOUND, "match", ":"),
    Pattern("match_body", Category.COMPOUND, ":", {"INDENT", "case"}),
]

COND_MAP: Dict[str, List[int]] = {}
for idx, pat in enumerate(PATTERNS):
    for tok in pat.cond_tokens:
        COND_MAP.setdefault(tok, []).append(idx)

def scan_code(code: str):
    total_tokens, syntax_token_count = 0, 0
    cat_counts = {p.category: 0 for p in PATTERNS}
    statement_toks, statement_syntax_indices = [], set()
    COMP_OPS = {"<", "<=", ">", ">=", "==", "!=", "in", "is"}

    try:
        g = tokenize.tokenize(BytesIO(code.encode("utf-8")).readline)
        for tok in g:
            tok_type, tok_str = tok.type, tok.string
            if tok_type in (tokenize.ENCODING, tokenize.ENDMARKER, tokenize.COMMENT, tokenize.NL):
                continue
            
            total_tokens += 1
            
            if tok_type in (tokenize.INDENT, tokenize.DEDENT, tokenize.NEWLINE):
                current_tok_id = tokenize.tok_name[tok_type]
            else:
                current_tok_id = tok_str
            
            current_tok_idx = len(statement_toks)

            # Paired patterns
            for i, prev_tok in reversed(list(enumerate(statement_toks))):
                if prev_tok in COND_MAP:
                    for pid in COND_MAP[prev_tok]:
                        if current_tok_id in PATTERNS[pid].cons_tokens:
                            cat_counts[PATTERNS[pid].category] += 1
                            statement_syntax_indices.update([i, current_tok_idx])
            
            # Unary patterns
            if tok_type == tokenize.STRING:
                cat_counts[Category.DATA_MODEL.value] += 1
                statement_syntax_indices.add(current_tok_idx)
            elif current_tok_id == "." and statement_toks and statement_toks[-1].isalpha():
                cat_counts[Category.DATA_MODEL.value] += 1
                statement_syntax_indices.update([current_tok_idx - 1, current_tok_idx])
            elif current_tok_id in {"global", "nonlocal"}:
                cat_counts[Category.SINGLE.value] += 1
                statement_syntax_indices.add(current_tok_idx)
            elif current_tok_id in COMP_OPS and not ("for" in statement_toks and current_tok_id == "in"):
                cat_counts[Category.EXPRESSIONS.value] += 1
                statement_syntax_indices.add(current_tok_idx)

            statement_toks.append(current_tok_id)

            if tok_type == tokenize.NEWLINE:
                syntax_token_count += len(statement_syntax_indices)
                statement_toks, statement_syntax_indices = [], set()

    except (tokenize.TokenError, IndentationError): pass

    syntax_token_count += len(statement_syntax_indices)
    return total_tokens, cat_counts, syntax_token_count

def process_file(jsonl_path):
    total_tok, total_syn, cat_totals = 0, 0, {p.category: 0 for p in PATTERNS}
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                code = json.loads(line).get("function", "")
                t, c, s = scan_code(code)
                total_tok += t
                total_syn += s
                for cat, count in c.items():
                    cat_totals[cat] += count
            except json.JSONDecodeError: continue
    return total_tok, cat_totals, total_syn

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset_dir", default="python_dataset")
    args = parser.parse_args()

    pos_path, neg_path = (os.path.join(args.dataset_dir, d, f"{d.split('/')[-1]}.jsonl") for d in ["positive", "negative"])
    
    grand_total_tok, grand_total_syn = 0, 0
    grand_cat_counts = {p.category: 0 for p in PATTERNS}
    
    for p in [pos_path, neg_path]:
        if os.path.exists(p):
            total, cats, syn = process_file(p)
            grand_total_tok += total
            grand_total_syn += syn
            for cat, count in cats.items():
                grand_cat_counts[cat] += count
    
    ratio = grand_total_syn / grand_total_tok if grand_total_tok else 0
    
    print("\n===== Syntax Token Statistics =====")
    for cat in sorted(grand_cat_counts.keys()):
        print(f"  {cat}: {grand_cat_counts.get(cat, 0)}")
    print(f"\n  Total Syntax Tokens: {grand_total_syn}")
    print(f"  Total Tokens: {grand_total_tok}")
    print(f"  Syntax Tokens Ratio: {ratio:.4f}")
    
    print("\nLaTeX Table Lines:")
    for cat in sorted(grand_cat_counts.keys()):
        print(f"{cat} & {grand_cat_counts.get(cat, 0)} \\\\")
    print("\\midrule")
    print(f"\\multicolumn{{2}}{{l}}{{\\textbf{{Total Syntax Tokens:}} {grand_total_syn}}} \\\\")
    print(f"\\multicolumn{{2}}{{l}}{{\\textbf{{Total Tokens:}} {grand_total_tok}}} \\\\")
    print(f"\\multicolumn{{2}}{{l}}{{\\textbf{{Syntax Tokens Ratio:}} {ratio:.4f}}} \\\\")

if __name__ == "__main__":
    main()
