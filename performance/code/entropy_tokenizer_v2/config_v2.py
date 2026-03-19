"""
v2 Global Configuration — Dynamic Per-Repo Compression Framework

Pipeline:
    Stage 1: Syntax Compression  (AST skeleton → <SYN_N> + slots, MDL-driven)
    Stage 2: Lossy Cleaning       (remove noise: comments / blank lines / indent)
    Stage 3: Token Replacement    (high-score identifiers/literals → placeholders)

All three stages are lossy-friendly; the goal is maximal token reduction.
"""

from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent
RESULTS_DIR  = PROJECT_ROOT / "results"
CACHE_DIR    = PROJECT_ROOT / "cache"
DATA_DIR     = PROJECT_ROOT.parent.parent / "data"   # shared HF dataset cache

# ── HuggingFace ───────────────────────────────────────────────────────────────
HF_TOKEN            = "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"
EVAL_DATASET        = "zhensuuu/starcoderdata_100star_py"
EVAL_NUM_SAMPLES    = 1000

# ── Tokenizers (same targets as v1 for direct comparison) ────────────────────
EVAL_TOKENIZERS = {
    "gpt4": {
        "type": "tiktoken",
        "tiktoken_model": "gpt-4",
    },
    "codegen-350M-mono": {
        "type": "hf",
        "name": "Salesforce/codegen-350M-mono",
    },
    "santacoder": {
        "type": "hf",
        "name": "bigcode/santacoder",
    },
}

# SimPy baseline (from paper) for comparison
SIMPY_REPORTED = {
    "gpt4":              {"reduction_pct": 10.4},
    "codegen-350M-mono": {"reduction_pct": 13.5},
    "santacoder":        {"reduction_pct": 8.8},
}

# ── Stage 1: Syntax compression ───────────────────────────────────────────────
AST_MIN_FREQ          = 20     # skeleton must appear ≥ N times to be a candidate
MDL_CODEBOOK_OVERHEAD = 2      # tokens needed to encode one operator in codebook

# ── Stage 2: Lossy cleaning rules ─────────────────────────────────────────────
# Each rule is (enabled, is_lossy, description)
CLEANING_RULES = {
    "remove_comments":            (True,  False, "R01 Remove # inline comments"),
    "remove_blank_lines":         (True,  False, "R02 Remove empty lines"),
    "remove_trailing_whitespace": (True,  False, "R03 Remove trailing spaces/tabs"),
    "remove_docstrings":          (True,  True,  "R05 Remove triple-quoted docstrings [LOSSY]"),
    "remove_indentation":         (True,  True,  "R04 Remove all indentation [LOSSY]"),
}

# ── Stage 3: Token importance scoring ────────────────────────────────────────
SCORE_EPSILON             = 0.01   # ε in Score(w) denominator
SCORE_THRESHOLD_PERCENTILE = 0.70  # replace top (1-0.70)=30% by score

# Category placeholders — each maps to a single new token
PLACEHOLDERS = {
    "variable":  "<VAR>",
    "attribute": "<ATTR>",
    "string":    "<STR>",
    "fstring":   "<FSTR>",
    "number":    "<NUM>",
}
