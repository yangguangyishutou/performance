"""Paths, tokenizer presets, and hyperparameters for Stages 1–3."""

import copy
from pathlib import Path
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# huggingface_hub / transformers read HF_ENDPOINT; default mirror when unset (override in .env or shell).
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR     = Path(os.getenv("ET_DATA_DIR", PROJECT_ROOT / "data"))
RESULTS_DIR  = Path(os.getenv("ET_RESULTS_DIR", PROJECT_ROOT / "results"))
CACHE_DIR    = Path(os.getenv("ET_CACHE_DIR", PROJECT_ROOT / "cache"))

# Stage3 backend: legacy replacement_map vs Plan A literal codec vs hybrid AB routing.
STAGE3_BACKEND = os.getenv("ET_STAGE3_BACKEND", "legacy").strip().lower()
if STAGE3_BACKEND not in {"legacy", "plan_a", "hybrid_ab"}:
    STAGE3_BACKEND = "legacy"

STAGE3_CODEBOOK_VERSION = os.getenv("ET_STAGE3_CODEBOOK_VERSION", "v1")
STAGE3_ESCAPE_PREFIX = os.getenv("ET_STAGE3_ESCAPE_PREFIX", "__L__")
STAGE3_PLAN_A_ENABLED_CATEGORIES = tuple(
    x.strip()
    for x in os.getenv(
        "ET_STAGE3_PLAN_A_ENABLED_CATEGORIES", "variable,attribute,string"
    ).split(",")
    if x.strip()
)
def _parse_plan_a_max_assignments() -> dict[str, int]:
    raw = os.getenv(
        "ET_STAGE3_PLAN_A_MAX_ASSIGNMENTS_PER_FIELD",
        "variable:256,attribute:128,string:128",
    )
    out: dict[str, int] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part or ":" not in part:
            continue
        k, v = part.split(":", 1)
        out[k.strip()] = int(v.strip())
    return out


STAGE3_PLAN_A_MIN_GAIN = float(os.getenv("ET_STAGE3_PLAN_A_MIN_GAIN", "0.001"))
STAGE3_PLAN_A_MAX_ASSIGNMENTS_PER_FIELD = _parse_plan_a_max_assignments()
STAGE3_PLAN_A_USE_TIKTOKEN = os.getenv("ET_STAGE3_PLAN_A_USE_TIKTOKEN", "0").lower() in (
    "1",
    "true",
    "yes",
)
STAGE3_PLAN_A_VOCAB_SCOPE = os.getenv("ET_STAGE3_PLAN_A_VOCAB_SCOPE", "used_only")
STAGE3_PLAN_A_COST_MODEL = os.getenv("ET_STAGE3_PLAN_A_COST_MODEL", "real_surface_form")
STAGE3_ARTIFACT_DIR = Path(
    os.getenv("ET_STAGE3_ARTIFACT_DIR", str(RESULTS_DIR / "stage3_plan_a"))
)

# Plan A tokenizer-aware profiles (see docs/stage3_plan_a_integration.md).
# Override with ET_STAGE3_PLAN_A_PROFILE=default|gpt4_conservative|gpt4_va_only
STAGE3_PLAN_A_POST_PRUNE = os.getenv("ET_STAGE3_PLAN_A_POST_PRUNE", "1").lower() in (
    "1",
    "true",
    "yes",
)

# Stage3 Hybrid AB knobs (A=exact aliasing, B=lexical free-text clustering baseline).
STAGE3_AB_FREE_TEXT_MIN_CHARS = int(os.getenv("ET_STAGE3_AB_FREE_TEXT_MIN_CHARS", "24"))
STAGE3_AB_FREE_TEXT_MIN_WORDS = int(os.getenv("ET_STAGE3_AB_FREE_TEXT_MIN_WORDS", "4"))
STAGE3_AB_ENABLE_MID_FREE_TEXT = os.getenv("ET_STAGE3_AB_ENABLE_MID_FREE_TEXT", "1").lower() in (
    "1",
    "true",
    "yes",
)
STAGE3_AB_FREE_TEXT_MID_MIN_CHARS = int(os.getenv("ET_STAGE3_AB_FREE_TEXT_MID_MIN_CHARS", "14"))
STAGE3_AB_FREE_TEXT_MID_MIN_WORDS = int(os.getenv("ET_STAGE3_AB_FREE_TEXT_MID_MIN_WORDS", "3"))
STAGE3_AB_ALLOW_MULTILINE_WHITELIST = os.getenv(
    "ET_STAGE3_AB_ALLOW_MULTILINE_WHITELIST",
    "0",
).lower() in ("1", "true", "yes")
STAGE3_AB_MULTILINE_MAX_LINES = int(os.getenv("ET_STAGE3_AB_MULTILINE_MAX_LINES", "3"))
STAGE3_AB_MULTILINE_MAX_CHARS = int(os.getenv("ET_STAGE3_AB_MULTILINE_MAX_CHARS", "220"))
STAGE3_AB_B_SIMILARITY_THRESHOLD = float(
    os.getenv("ET_STAGE3_AB_B_SIMILARITY_THRESHOLD", "0.82")
)
STAGE3_AB_B_RISK_THRESHOLD = float(os.getenv("ET_STAGE3_AB_B_RISK_THRESHOLD", "0.72"))
STAGE3_AB_B_MIN_CLUSTER_SIZE = int(os.getenv("ET_STAGE3_AB_B_MIN_CLUSTER_SIZE", "2"))
STAGE3_AB_B_SIMILARITY_KIND = os.getenv(
    "ET_STAGE3_AB_B_SIMILARITY_KIND",
    "lexical_bow_cosine",
).strip().lower()
if STAGE3_AB_B_SIMILARITY_KIND not in {"lexical_bow_cosine", "hybrid_lexical_char", "mixed"}:
    STAGE3_AB_B_SIMILARITY_KIND = "lexical_bow_cosine"
STAGE3_AB_B_LEXICAL_WEIGHT = float(os.getenv("ET_STAGE3_AB_B_LEXICAL_WEIGHT", "0.7"))
STAGE3_AB_B_CHAR_WEIGHT = float(os.getenv("ET_STAGE3_AB_B_CHAR_WEIGHT", "0.3"))
STAGE3_AB_B_CHAR_NGRAM_N = int(os.getenv("ET_STAGE3_AB_B_CHAR_NGRAM_N", "3"))
STAGE3_AB_B_SIMILARITY_NORM = os.getenv(
    "ET_STAGE3_AB_B_SIMILARITY_NORM",
    "none",
).strip().lower()
if STAGE3_AB_B_SIMILARITY_NORM not in {"none", "raw", "light", "numeric"}:
    STAGE3_AB_B_SIMILARITY_NORM = "none"
STAGE3_AB_B_DEFINITION_MODE = os.getenv(
    "ET_STAGE3_AB_B_DEFINITION_MODE",
    "shared_terms",
).strip().lower()
if STAGE3_AB_B_DEFINITION_MODE not in {"shared_terms", "representative", "rep"}:
    STAGE3_AB_B_DEFINITION_MODE = "shared_terms"
STAGE3_AB_B_DEFINITION_MIN_DF_RATIO = float(
    os.getenv("ET_STAGE3_AB_B_DEFINITION_MIN_DF_RATIO", "0.6")
)
STAGE3_AB_B_DEFINITION_MAX_TERMS = int(
    os.getenv("ET_STAGE3_AB_B_DEFINITION_MAX_TERMS", "10")
)
STAGE3_AB_B_MEMBER_SELECT_MODE = os.getenv(
    "ET_STAGE3_AB_B_MEMBER_SELECT_MODE",
    "all",
).strip().lower()
if STAGE3_AB_B_MEMBER_SELECT_MODE not in {"all", "drop_negative", "net_greedy"}:
    STAGE3_AB_B_MEMBER_SELECT_MODE = "all"
STAGE3_AB_B_CODE_STYLE = os.getenv(
    "ET_STAGE3_AB_B_CODE_STYLE",
    "prefix_index",
).strip().lower()
if STAGE3_AB_B_CODE_STYLE not in {"prefix_index", "base62", "compact"}:
    STAGE3_AB_B_CODE_STYLE = "prefix_index"
STAGE3_AB_B_CODE_PREFIX = os.getenv("ET_STAGE3_AB_B_CODE_PREFIX", "__abB")
STAGE3_AB_ENABLE_B = os.getenv("ET_STAGE3_AB_ENABLE_B", "1").lower() in ("1", "true", "yes")
STAGE3_AB_GLOBAL_DICT_ENABLE = os.getenv(
    "ET_STAGE3_AB_GLOBAL_DICT_ENABLE",
    "0",
).lower() in ("1", "true", "yes")
STAGE3_AB_GLOBAL_DICT_PATH = os.getenv(
    "ET_STAGE3_AB_GLOBAL_DICT_PATH",
    str(CACHE_DIR / "stage3_global_dictionary.json"),
)
STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB = os.getenv(
    "ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB",
    "0",
).lower() in ("1", "true", "yes")
STAGE3_AB_MODE = os.getenv("ET_STAGE3_AB_MODE", "").strip().lower()
STAGE3_AB_A_MIN_OCC = int(os.getenv("ET_STAGE3_AB_A_MIN_OCC", "2"))
STAGE3_AB_A_MIN_NET_GAIN = int(os.getenv("ET_STAGE3_AB_A_MIN_NET_GAIN", "1"))
STAGE3_AB_A_ALIAS_STYLE = os.getenv("ET_STAGE3_AB_A_ALIAS_STYLE", "short").strip().lower()
if STAGE3_AB_A_ALIAS_STYLE not in {"short", "mnemonic"}:
    STAGE3_AB_A_ALIAS_STYLE = "short"
STAGE3_AB_SHORT_STRING_POLICY = os.getenv(
    "ET_STAGE3_AB_SHORT_STRING_POLICY",
    "exact_candidate",
).strip().lower()
if STAGE3_AB_SHORT_STRING_POLICY not in {"fallback", "exact_candidate"}:
    STAGE3_AB_SHORT_STRING_POLICY = "exact_candidate"
STAGE3_AB_A_ALIAS_CANDIDATE_STYLE = os.getenv(
    "ET_STAGE3_AB_A_ALIAS_CANDIDATE_STYLE",
    "token_cost_sorted",
).strip().lower()
STAGE3_AB_A_ALIAS_CACHE_DIR = str(CACHE_DIR / "alias_alphabets")
STAGE3_AB_ENABLE_COMPOUND_SPANS = os.getenv(
    "ET_STAGE3_AB_ENABLE_COMPOUND_SPANS",
    "1",
).lower() in ("1", "true", "yes")
STAGE3_AB_COMPOUND_MIN_RAW_TOKEN_LEN = int(
    os.getenv("ET_STAGE3_AB_COMPOUND_MIN_RAW_TOKEN_LEN", "4")
)
STAGE3_AB_KEY_LIKE_PATTERNS = tuple(
    x.strip()
    for x in os.getenv(
        "ET_STAGE3_AB_KEY_LIKE_PATTERNS",
        r"(?:^|[_\-.])(key|id|name|type|path|url|config|option|field)(?:$|[_\-.])",
    ).split("||")
    if x.strip()
)

# hybrid_ab only: GPT-4 / cl100k_base gets selective A + guardrails; GPT-2 keeps legacy path.
HYBRID_AB_GPT4_PROFILE_STAGE3: dict = {
    "a_processing_mode": "selective",
    "a_cost_mode": "context_aware",
    "enable_global_guardrail": True,
    "enable_incremental_rollback": True,
    "min_raw_token_len": 3,
    "max_alias_token_len": 2,
    # Use normal B priority on GPT-4: stronger B contributes net gains on 1M eval.
    "b_channel_priority": "normal",
    "context_window_chars": 80,
}
HYBRID_AB_GPT2_PROFILE_STAGE3: dict = {
    "a_processing_mode": "full",
    "a_cost_mode": "local",
    "enable_global_guardrail": False,
    "enable_incremental_rollback": False,
    "min_raw_token_len": 1,
    "max_alias_token_len": 32,
    "b_channel_priority": "normal",
    "context_window_chars": 80,
}


def resolve_hybrid_ab_settings(tokenizer_key: str) -> dict:
    """
    Resolve hybrid_ab runtime settings with tokenizer-aware defaults.

    Default mode is conservative exact_only for all tokenizers.
    """
    tok = (tokenizer_key or "").strip().lower()
    sim_default = 0.84 if tok == "gpt4" else STAGE3_AB_B_SIMILARITY_THRESHOLD
    risk_default = 0.74 if tok == "gpt4" else STAGE3_AB_B_RISK_THRESHOLD
    norm_default = "light" if tok == "gpt4" else STAGE3_AB_B_SIMILARITY_NORM
    code_style_default = "base62" if tok == "gpt4" else STAGE3_AB_B_CODE_STYLE
    code_prefix_default = "b" if tok == "gpt4" else STAGE3_AB_B_CODE_PREFIX
    mode_default = "exact_only"
    # Read mode from the environment on each call so subprocess-free tests and
    # validate smoke can switch exact_only vs hybrid without reloading config.
    mode_env = os.getenv("ET_STAGE3_AB_MODE", "").strip().lower()
    if not mode_env:
        mode_env = (STAGE3_AB_MODE or "").strip().lower()
    mode = mode_env if mode_env in {"exact_only", "hybrid"} else mode_default
    enable_b = os.getenv("ET_STAGE3_AB_ENABLE_B", "1" if STAGE3_AB_ENABLE_B else "0")
    enable_b = enable_b.lower() in ("1", "true", "yes")
    if mode != "hybrid":
        enable_b = False

    raw_a_min = os.getenv("ET_STAGE3_AB_A_MIN_OCC", "").strip()
    if raw_a_min:
        a_min_occ = int(raw_a_min)
    elif tok == "gpt4":
        a_min_occ = max(STAGE3_AB_A_MIN_OCC, 3)
    else:
        a_min_occ = STAGE3_AB_A_MIN_OCC

    ab_prof = HYBRID_AB_GPT4_PROFILE_STAGE3 if tok == "gpt4" else HYBRID_AB_GPT2_PROFILE_STAGE3
    cand_style_default = (
        "legal_identifier_pool" if tok == "gpt4" else STAGE3_AB_A_ALIAS_CANDIDATE_STYLE
    )

    def _truthy_ab(v: str) -> bool:
        return v.lower() in ("1", "true", "yes", "on")

    out = {
        "mode": mode,
        "free_text_min_chars": STAGE3_AB_FREE_TEXT_MIN_CHARS,
        "free_text_min_words": STAGE3_AB_FREE_TEXT_MIN_WORDS,
        "enable_mid_free_text": os.getenv(
            "ET_STAGE3_AB_ENABLE_MID_FREE_TEXT",
            "1" if STAGE3_AB_ENABLE_MID_FREE_TEXT else "0",
        ).lower() in ("1", "true", "yes"),
        "free_text_mid_min_chars": int(
            os.getenv(
                "ET_STAGE3_AB_FREE_TEXT_MID_MIN_CHARS",
                str(STAGE3_AB_FREE_TEXT_MID_MIN_CHARS),
            )
        ),
        "free_text_mid_min_words": int(
            os.getenv(
                "ET_STAGE3_AB_FREE_TEXT_MID_MIN_WORDS",
                str(STAGE3_AB_FREE_TEXT_MID_MIN_WORDS),
            )
        ),
        "allow_multiline_whitelist": os.getenv(
            "ET_STAGE3_AB_ALLOW_MULTILINE_WHITELIST",
            "1" if STAGE3_AB_ALLOW_MULTILINE_WHITELIST else "0",
        ).lower() in ("1", "true", "yes"),
        "multiline_max_lines": int(
            os.getenv("ET_STAGE3_AB_MULTILINE_MAX_LINES", str(STAGE3_AB_MULTILINE_MAX_LINES))
        ),
        "multiline_max_chars": int(
            os.getenv("ET_STAGE3_AB_MULTILINE_MAX_CHARS", str(STAGE3_AB_MULTILINE_MAX_CHARS))
        ),
        "b_similarity_threshold": float(
            os.getenv("ET_STAGE3_AB_B_SIMILARITY_THRESHOLD", str(sim_default))
        ),
        "b_risk_threshold": float(os.getenv("ET_STAGE3_AB_B_RISK_THRESHOLD", str(risk_default))),
        "b_min_cluster_size": int(
            os.getenv("ET_STAGE3_AB_B_MIN_CLUSTER_SIZE", str(STAGE3_AB_B_MIN_CLUSTER_SIZE))
        ),
        "b_similarity_kind": os.getenv(
            "ET_STAGE3_AB_B_SIMILARITY_KIND",
            STAGE3_AB_B_SIMILARITY_KIND,
        ).strip().lower(),
        "b_lexical_weight": float(
            os.getenv("ET_STAGE3_AB_B_LEXICAL_WEIGHT", str(STAGE3_AB_B_LEXICAL_WEIGHT))
        ),
        "b_char_weight": float(os.getenv("ET_STAGE3_AB_B_CHAR_WEIGHT", str(STAGE3_AB_B_CHAR_WEIGHT))),
        "b_char_ngram_n": int(os.getenv("ET_STAGE3_AB_B_CHAR_NGRAM_N", str(STAGE3_AB_B_CHAR_NGRAM_N))),
        "b_similarity_norm": os.getenv(
            "ET_STAGE3_AB_B_SIMILARITY_NORM",
            norm_default,
        ).strip().lower(),
        "b_definition_mode": os.getenv(
            "ET_STAGE3_AB_B_DEFINITION_MODE",
            STAGE3_AB_B_DEFINITION_MODE,
        ).strip().lower(),
        "b_definition_min_df_ratio": float(
            os.getenv(
                "ET_STAGE3_AB_B_DEFINITION_MIN_DF_RATIO",
                str(STAGE3_AB_B_DEFINITION_MIN_DF_RATIO),
            )
        ),
        "b_definition_max_terms": int(
            os.getenv(
                "ET_STAGE3_AB_B_DEFINITION_MAX_TERMS",
                str(STAGE3_AB_B_DEFINITION_MAX_TERMS),
            )
        ),
        "b_member_select_mode": os.getenv(
            "ET_STAGE3_AB_B_MEMBER_SELECT_MODE",
            STAGE3_AB_B_MEMBER_SELECT_MODE,
        ).strip().lower(),
        "b_code_style": os.getenv(
            "ET_STAGE3_AB_B_CODE_STYLE",
            code_style_default,
        ).strip().lower(),
        "b_code_prefix": os.getenv(
            "ET_STAGE3_AB_B_CODE_PREFIX",
            code_prefix_default,
        ),
        "enable_b": enable_b,
        "global_dict_enabled": os.getenv(
            "ET_STAGE3_AB_GLOBAL_DICT_ENABLE",
            "1" if STAGE3_AB_GLOBAL_DICT_ENABLE else "0",
        ).lower() in ("1", "true", "yes"),
        "global_dict_path": os.getenv(
            "ET_STAGE3_AB_GLOBAL_DICT_PATH",
            STAGE3_AB_GLOBAL_DICT_PATH,
        ),
        "global_dict_charge_vocab": os.getenv(
            "ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB",
            "1" if STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB else "0",
        ).lower() in ("1", "true", "yes"),
        "a_min_occ": a_min_occ,
        "a_min_net_gain": int(
            os.getenv("ET_STAGE3_AB_A_MIN_NET_GAIN", str(STAGE3_AB_A_MIN_NET_GAIN))
        ),
        "a_alias_style": os.getenv("ET_STAGE3_AB_A_ALIAS_STYLE", STAGE3_AB_A_ALIAS_STYLE),
        "short_string_policy": os.getenv(
            "ET_STAGE3_AB_SHORT_STRING_POLICY",
            STAGE3_AB_SHORT_STRING_POLICY,
        ).strip().lower(),
        "a_alias_candidate_style": os.getenv(
            "ET_STAGE3_AB_A_ALIAS_CANDIDATE_STYLE",
            cand_style_default,
        ).strip().lower(),
        "enable_compound_spans": os.getenv(
            "ET_STAGE3_AB_ENABLE_COMPOUND_SPANS",
            "1" if STAGE3_AB_ENABLE_COMPOUND_SPANS else "0",
        ).lower() in ("1", "true", "yes"),
        "compound_min_raw_token_len": int(
            os.getenv(
                "ET_STAGE3_AB_COMPOUND_MIN_RAW_TOKEN_LEN",
                str(STAGE3_AB_COMPOUND_MIN_RAW_TOKEN_LEN),
            )
        ),
        "a_alias_cache_dir": os.getenv(
            "ET_STAGE3_AB_A_ALIAS_CACHE_DIR",
            STAGE3_AB_A_ALIAS_CACHE_DIR,
        ),
        "key_like_patterns": list(STAGE3_AB_KEY_LIKE_PATTERNS),
        "stage3_ab_mode": mode,
        "stage3_ab_similarity_kind": os.getenv(
            "ET_STAGE3_AB_B_SIMILARITY_KIND",
            STAGE3_AB_B_SIMILARITY_KIND,
        ).strip().lower(),
        "stage3_ab_b_mode": (
            "lexical_free_text_mixed"
            if mode == "hybrid"
            and enable_b
            and os.getenv(
                "ET_STAGE3_AB_B_SIMILARITY_KIND",
                STAGE3_AB_B_SIMILARITY_KIND,
            ).strip().lower()
            in {"hybrid_lexical_char", "mixed"}
            else "lexical_free_text_baseline"
            if mode == "hybrid" and enable_b
            else "disabled"
        ),
    }
    out.update(ab_prof)
    if str(out.get("b_similarity_norm", "")).strip().lower() not in {"none", "raw", "light", "numeric"}:
        out["b_similarity_norm"] = "none"
    if str(out.get("b_definition_mode", "")).strip().lower() not in {"shared_terms", "representative", "rep"}:
        out["b_definition_mode"] = "shared_terms"
    try:
        out["b_definition_min_df_ratio"] = float(out.get("b_definition_min_df_ratio", 0.6))
    except Exception:
        out["b_definition_min_df_ratio"] = 0.6
    out["b_definition_min_df_ratio"] = max(0.0, min(1.0, float(out["b_definition_min_df_ratio"])))
    try:
        out["b_definition_max_terms"] = int(out.get("b_definition_max_terms", 10))
    except Exception:
        out["b_definition_max_terms"] = 10
    out["b_definition_max_terms"] = max(1, int(out["b_definition_max_terms"]))
    if str(out.get("b_member_select_mode", "")).strip().lower() not in {"all", "drop_negative", "net_greedy"}:
        out["b_member_select_mode"] = "all"
    if str(out.get("b_code_style", "")).strip().lower() not in {"prefix_index", "base62", "compact"}:
        out["b_code_style"] = "prefix_index"
    if not str(out.get("b_code_prefix", "")).strip():
        out["b_code_prefix"] = "__abB"
    eg = os.getenv("ET_STAGE3_AB_ENABLE_GLOBAL_GUARDRAIL", "").strip()
    if eg:
        out["enable_global_guardrail"] = _truthy_ab(eg)
    er = os.getenv("ET_STAGE3_AB_ENABLE_INCREMENTAL_ROLLBACK", "").strip()
    if er:
        out["enable_incremental_rollback"] = _truthy_ab(er)
    cm = os.getenv("ET_STAGE3_AB_A_COST_MODE", "").strip().lower()
    if cm in {"local", "context_aware"}:
        out["a_cost_mode"] = cm
    mrl = os.getenv("ET_STAGE3_AB_MIN_RAW_TOKEN_LEN", "").strip()
    if mrl:
        out["min_raw_token_len"] = int(mrl)
    mal = os.getenv("ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN", "").strip()
    if mal:
        out["max_alias_token_len"] = int(mal)
    cw = os.getenv("ET_STAGE3_AB_CONTEXT_WINDOW_CHARS", "").strip()
    if cw:
        out["context_window_chars"] = int(cw)
    apm = os.getenv("ET_STAGE3_AB_A_PROCESSING_MODE", "").strip().lower()
    if apm in {"full", "selective"}:
        out["a_processing_mode"] = apm
    bcp = os.getenv("ET_STAGE3_AB_B_CHANNEL_PRIORITY", "").strip().lower()
    if bcp in {"low", "normal", "high"}:
        out["b_channel_priority"] = bcp
    if (
        tok == "gpt4"
        and str(out.get("b_channel_priority", "normal")).strip().lower() == "low"
    ):
        out["b_similarity_threshold"] = min(
            0.94, float(out["b_similarity_threshold"]) + 0.06
        )
    return out


def plan_a_profile_name_for_tokenizer(tokenizer_key: str) -> str:
    """Default profile: gpt4 -> conservative; others -> default (gpt2-friendly)."""
    explicit = os.getenv("ET_STAGE3_PLAN_A_PROFILE", "").strip()
    if explicit:
        return explicit
    if tokenizer_key.strip().lower() == "gpt4":
        return os.getenv("ET_STAGE3_PLAN_A_PROFILE_GPT4_DEFAULT", "gpt4_conservative")
    return "default"


def resolve_plan_a_settings(tokenizer_key: str) -> dict:
    """
    Resolved Plan A knobs for this tokenizer (and env overrides).

    Returns dict with:
    profile_name, enabled_categories, min_gain, max_assignments_by_field,
    string_filter (dict or None), post_prune_enabled
    """
    profile = plan_a_profile_name_for_tokenizer(tokenizer_key)
    # Env overrides (highest priority for categories / gain / caps)
    cat_env = os.getenv("ET_STAGE3_PLAN_A_ENABLED_CATEGORIES", "").strip()
    mg_env = os.getenv("ET_STAGE3_PLAN_A_MIN_GAIN", "").strip()
    max_env = os.getenv("ET_STAGE3_PLAN_A_MAX_ASSIGNMENTS_PER_FIELD", "").strip()

    profiles: dict[str, dict] = {
        "default": {
            "enabled_categories": ("variable", "attribute", "string"),
            "min_gain": 0.001,
            "max_assignments": {"variable": 256, "attribute": 128, "string": 128},
            "string_filter": {"min_count": 1, "min_raw_token_cost": 0, "strict_heuristics": False},
            "post_prune": STAGE3_PLAN_A_POST_PRUNE,
        },
        "gpt4_conservative": {
            "enabled_categories": ("variable", "attribute", "string"),
            "min_gain": 0.003,
            "max_assignments": {"variable": 64, "attribute": 32, "string": 16},
            "string_filter": {"min_count": 2, "min_raw_token_cost": 8, "strict_heuristics": True},
            "post_prune": True,
        },
        "gpt4_va_only": {
            "enabled_categories": ("variable", "attribute"),
            "min_gain": 0.003,
            "max_assignments": {"variable": 64, "attribute": 32},
            "string_filter": None,
            "post_prune": True,
        },
    }
    base = copy.deepcopy(profiles.get(profile, profiles["default"]))
    if cat_env:
        base["enabled_categories"] = tuple(
            x.strip() for x in cat_env.split(",") if x.strip()
        )
    if mg_env:
        base["min_gain"] = float(mg_env)
    if max_env:
        out_max: dict[str, int] = {}
        for part in max_env.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            k, v = part.split(":", 1)
            out_max[k.strip()] = int(v.strip())
        base["max_assignments"] = out_max
    base["profile_name"] = profile
    pp_env = os.getenv("ET_STAGE3_PLAN_A_POST_PRUNE", "").strip()
    if pp_env:
        base["post_prune"] = pp_env.lower() in ("1", "true", "yes")
    return base

HF_TOKEN         = os.getenv("HF_TOKEN", "")
EVAL_DATASET     = os.getenv("ET_EVAL_DATASET", "zhensuuu/starcoderdata_100star_py")
EVAL_NUM_SAMPLES = int(os.getenv("ET_EVAL_NUM_SAMPLES", "1000"))

LOCAL_SAMPLE_FILE = Path(
    os.getenv("ET_LOCAL_SAMPLE_FILE", DATA_DIR / "starcoder_1m_tokens.txt")
)
HF_DISK_DATASET_FALLBACK = Path(
    os.getenv("ET_HF_DISK_DATASET_FALLBACK", DATA_DIR / "test")
)
SIMPY_DIR = Path(
    os.getenv("ET_SIMPY_DIR", PROJECT_ROOT / "third_party" / "Simpy-master")
)

EVAL_TOKENIZERS = {
    "gpt4": {
        "type": "tiktoken",
        "tiktoken_model": "gpt-4",
    },
    "qwen25-coder-15b": {
        "type": "hf",
        "name": os.getenv("ET_QWEN25_CODER_15B_MODEL", "Qwen/Qwen2.5-Coder-1.5B").strip()
        or "Qwen/Qwen2.5-Coder-1.5B",
    },
    "deepseek-v31": {
        "type": "hf",
        "name": "deepseek-ai/DeepSeek-V3.1",
    },
    "gpt2": {
        "type": "hf",
        "name": "gpt2",
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

AST_MIN_FREQ           = 20
MDL_CODEBOOK_OVERHEAD  = 2
STAGE1_MIN_OCCURRENCES = 2
STAGE1_MIN_TOTAL_NET_SAVING = 1
STAGE1_MIN_AVG_NET_SAVING = 0

# Stage1 knobs used only when stage3_backend == hybrid_ab (see repo_miner.mine_repo).
STAGE1_HYBRID_AB_AST_MIN_FREQ = int(os.getenv("ET_STAGE1_HYBRID_AB_AST_MIN_FREQ", "12"))
STAGE1_HYBRID_AB_SCORE_THRESHOLD_PERCENTILE = float(
    os.getenv("ET_STAGE1_HYBRID_AB_SCORE_THRESHOLD_PERCENTILE", "0.60")
)
STAGE1_HYBRID_AB_MIN_TOTAL_NET_SAVING = int(
    os.getenv("ET_STAGE1_HYBRID_AB_MIN_TOTAL_NET_SAVING", "0")
)

# Placeholder regex fragments (consumed by ``placeholder_accounting.PLACEHOLDER_RE``).
PLACEHOLDER_PATTERNS = [
    r"<SYN_\d+>",
    r"<VAR>",
    r"<ATTR>",
    r"<STR>",
    r"<FSTR>",
    r"<NUM>",
    r"<NL[0-8]>",
]

# Vocab introduction cost for effective-total accounting.
VOCAB_COST_MODE = os.getenv("ET_VOCAB_COST_MODE", "serialized_definition")
VOCAB_COST_SCOPE = os.getenv("ET_VOCAB_COST_SCOPE", "corpus_once")
FIXED_VOCAB_TOKEN_COST = int(os.getenv("ET_FIXED_VOCAB_TOKEN_COST", "4"))

CLEANING_RULES = {
    "remove_comments":            (False, False, "R01 Remove # inline comments [default off]"),
    "remove_blank_lines":         (True,  False, "R02 Remove empty lines"),
    "remove_trailing_whitespace": (True,  False, "R03 Remove trailing spaces/tabs"),
    "remove_docstrings":          (False, True,  "R05 Remove docstrings [LOSSY, default off]"),
    "remove_indentation":         (True,  True,  "R04 Remove all indentation [LOSSY]"),
}

STAGE2_DEFAULT_PROFILE = os.getenv("ET_STAGE2_DEFAULT_PROFILE", "stage2_aggressive")
STAGE2_DEFAULT_MODE = os.getenv("ET_STAGE2_DEFAULT_MODE", "linewise")
STAGE2_PROFILE_FLAGS = {
    "stage2_parseable": {
        "remove_comments": False,
        "remove_blank_lines": True,
        "remove_trailing_whitespace": True,
        "remove_docstrings": False,
        "remove_indentation": False,
    },
    "stage2_aggressive": {
        "remove_comments": False,
        "remove_blank_lines": True,
        "remove_trailing_whitespace": True,
        "remove_docstrings": False,
        "remove_indentation": True,
    },
    # Stage1+Stage2 eval profiles (blockwise + docstrings; see scripts/eval_stage1_stage2_only.py).
    "stage2_safe": {
        "remove_comments": False,
        "remove_blank_lines": True,
        "remove_trailing_whitespace": True,
        "remove_docstrings": True,
        "remove_indentation": False,
    },
    "stage2_aggressive_upper_bound": {
        "remove_comments": True,
        "remove_blank_lines": True,
        "remove_trailing_whitespace": True,
        "remove_docstrings": True,
        "remove_indentation": True,
    },
    # hybrid_ab-only default Stage2 (blockwise + docstrings); same flags as aggressive_upper_bound.
    "stage2_hybrid_ab_aggressive": {
        "remove_comments": True,
        "remove_blank_lines": True,
        "remove_trailing_whitespace": True,
        "remove_docstrings": True,
        "remove_indentation": True,
    },
}

# Stage2 defaults when stage3_backend == hybrid_ab and eval does not pass explicit Stage2 (see pipeline).
STAGE2_HYBRID_AB_PROFILE = os.getenv(
    "ET_STAGE2_HYBRID_AB_PROFILE", "stage2_hybrid_ab_aggressive"
).strip()
STAGE2_HYBRID_AB_MODE = os.getenv("ET_STAGE2_HYBRID_AB_MODE", "blockwise").strip()
if STAGE2_HYBRID_AB_MODE not in ("linewise", "blockwise"):
    STAGE2_HYBRID_AB_MODE = "blockwise"

SCORE_EPSILON              = 0.01
SCORE_THRESHOLD_PERCENTILE = 0.70

PLACEHOLDERS = {
    "variable":  "<VAR>",
    "attribute": "<ATTR>",
    "string":    "<STR>",
    "fstring":   "<FSTR>",
    "number":    "<NUM>",
}
