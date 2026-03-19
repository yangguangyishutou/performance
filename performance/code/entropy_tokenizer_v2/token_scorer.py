"""
Stage 3 — Token Importance Scoring & Category-Based Placeholder Replacement

For each identifier / literal token w in a repo corpus, compute:

    Score(w) = ΔT(w) / (ΔI(w) + ε)

where:
    ΔT(w) = (spt(w) − 1) × freq(w)          token savings if w → one placeholder
    ΔI(w) = −log₂ p(w)                        self-information  (rare ⟹ large)
    p(w)  = freq(w) / Σ_u freq(u)             corpus frequency probability
    ε     = SCORE_EPSILON                      smoothing constant

High Score → frequent + low self-info  → safe to replace (big gain, little loss)
Low Score  → rare    + high self-info  → keep as-is    (small gain, big loss)

Replacement categories (one placeholder per semantic class):
    <VAR>   identifier used as a variable / parameter name
    <ATTR>  identifier appearing as an attribute  (right of '.')
    <STR>   regular string literal
    <FSTR>  f-string literal
    <NUM>   numeric literal

spt(w) estimation:
    If a target tokenizer is provided  → exact subtoken count via encode()
    Otherwise                          → heuristic: len(w) / 3.5
"""

import builtins
import io
import keyword
import math
import re
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from config_v2 import SCORE_EPSILON, SCORE_THRESHOLD_PERCENTILE, PLACEHOLDERS

# ─────────────────────────────────────────────────────────────────────────────
# Protected tokens — never replaced regardless of score
# ─────────────────────────────────────────────────────────────────────────────

_KEYWORDS  = set(keyword.kwlist)
_BUILTINS  = set(dir(builtins))
_PROTECTED = _KEYWORDS | _BUILTINS | {
    "self", "cls", "__init__", "__name__", "__main__",
    "True", "False", "None", "args", "kwargs",
}


# ─────────────────────────────────────────────────────────────────────────────
# Vocabulary extraction (from valid Python source using tokenize)
# ─────────────────────────────────────────────────────────────────────────────

def _safe_tokenize(source: str) -> list:
    try:
        return list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError:
        return []


def _extract_vocab_from_source(source: str) -> dict[str, Counter]:
    """
    Scan one source file and return per-category frequency Counters:
        {
          "identifiers": Counter,
          "attributes":  Counter,   # subset of identifiers appearing after '.'
          "strings":     Counter,
          "fstrings":    Counter,
          "numbers":     Counter,
        }
    """
    toks = _safe_tokenize(source)

    ids:    Counter = Counter()
    attrs:  Counter = Counter()
    strs:   Counter = Counter()
    fstrs:  Counter = Counter()
    nums:   Counter = Counter()

    prev_is_dot = False

    for tok in toks:
        ttype, tstr = tok.type, tok.string

        if ttype == tokenize.NAME:
            if tstr not in _PROTECTED:
                ids[tstr] += 1
                if prev_is_dot:
                    attrs[tstr] += 1
            prev_is_dot = False

        elif ttype == tokenize.STRING:
            if tstr.startswith(("f'", 'f"', "f'''", 'f"""',
                                 "F'", 'F"', "F'''", 'F"""',
                                 "rf'", 'rf"', "fr'", 'fr"')):
                fstrs[tstr] += 1
            else:
                strs[tstr] += 1
            prev_is_dot = False

        elif ttype == tokenize.NUMBER:
            nums[tstr] += 1
            prev_is_dot = False

        elif ttype == tokenize.OP:
            prev_is_dot = (tstr == ".")

        else:
            prev_is_dot = False

    return {
        "identifiers": ids,
        "attributes":  attrs,
        "strings":     strs,
        "fstrings":    fstrs,
        "numbers":     nums,
    }


def build_vocabulary(sources: list[str]) -> dict[str, Counter]:
    """
    Aggregate per-category vocabularies over a list of source files.
    Returns the same structure as _extract_vocab_from_source but corpus-wide.
    """
    total: dict[str, Counter] = {
        "identifiers": Counter(),
        "attributes":  Counter(),
        "strings":     Counter(),
        "fstrings":    Counter(),
        "numbers":     Counter(),
    }
    for src in sources:
        for cat, counter in _extract_vocab_from_source(src).items():
            total[cat].update(counter)
    return total


# ─────────────────────────────────────────────────────────────────────────────
# Score computation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TokenInfo:
    word:      str
    category:  str
    freq:      int
    spt:       float    # subtoken count under target tokenizer
    self_info: float    # I(w) = -log2 p(w)
    delta_T:   float    # (spt - 1) * freq
    score:     float    # delta_T / (self_info + ε)


def _spt_estimate(word: str, tokenizer=None, tok_type: str = "tiktoken") -> float:
    if tokenizer is None:
        return max(1.0, len(word) / 3.5)
    try:
        if tok_type == "tiktoken":
            return float(len(tokenizer.encode(word, allowed_special="all")))
        return float(len(tokenizer.encode(word, add_special_tokens=False)))
    except Exception:
        return max(1.0, len(word) / 3.5)


def compute_scores(
    vocab: dict[str, Counter],
    tokenizer=None,
    tok_type: str = "tiktoken",
    epsilon: float = SCORE_EPSILON,
) -> dict[str, TokenInfo]:
    """
    Compute Score(w) for every token in the vocabulary.

    The total corpus frequency (denominator of p(w)) is computed across
    identifiers + strings + fstrings + numbers combined, so probabilities
    are comparable across categories.
    """
    ids   = vocab["identifiers"]
    attrs = vocab["attributes"]
    strs  = vocab["strings"]
    fstrs = vocab["fstrings"]
    nums  = vocab["numbers"]

    total_freq = (sum(ids.values()) + sum(strs.values())
                  + sum(fstrs.values()) + sum(nums.values()))
    if total_freq == 0:
        return {}

    results: dict[str, TokenInfo] = {}

    def _add(word: str, freq: int, cat: str):
        if freq == 0:
            return
        p_w       = freq / total_freq
        self_info = -math.log2(p_w)
        spt       = _spt_estimate(word, tokenizer, tok_type)
        delta_T   = max(0.0, spt - 1.0) * freq
        score     = delta_T / (self_info + epsilon)
        results[word] = TokenInfo(
            word=word, category=cat, freq=freq,
            spt=spt, self_info=self_info,
            delta_T=delta_T, score=score,
        )

    for word, freq in ids.items():
        cat = "attribute" if word in attrs else "variable"
        _add(word, freq, cat)

    for word, freq in strs.items():
        _add(word, freq, "string")

    for word, freq in fstrs.items():
        _add(word, freq, "fstring")

    for word, freq in nums.items():
        _add(word, freq, "number")

    return results


# ─────────────────────────────────────────────────────────────────────────────
# Selection: which tokens to replace
# ─────────────────────────────────────────────────────────────────────────────

def select_replacement_set(
    scores: dict[str, TokenInfo],
    threshold_percentile: float = SCORE_THRESHOLD_PERCENTILE,
) -> set[str]:
    """
    Return the set of tokens whose Score is at or above the
    (1 − threshold_percentile) quantile.

    Only tokens with spt > 1 are eligible (replacing a single-subtoken
    word saves 0 subtokens and is not worth the semantic cost).
    """
    eligible = [info for info in scores.values() if info.spt > 1.0]
    if not eligible:
        return set()

    eligible.sort(key=lambda x: x.score)
    cutoff_idx = int(len(eligible) * threshold_percentile)
    cutoff_score = eligible[cutoff_idx].score if cutoff_idx < len(eligible) else float("inf")

    return {info.word for info in eligible if info.score >= cutoff_score}


def build_replacement_map(
    scores: dict[str, TokenInfo],
    replacement_set: set[str],
) -> dict[str, str]:
    """
    Build {original_token: placeholder} for all tokens in replacement_set.
    """
    rmap: dict[str, str] = {}
    for word in replacement_set:
        if word in scores:
            placeholder = PLACEHOLDERS.get(scores[word].category, "<UNK>")
            rmap[word] = placeholder
    return rmap


# ─────────────────────────────────────────────────────────────────────────────
# Application: replace tokens in source text
# ─────────────────────────────────────────────────────────────────────────────

# Precompile once — matches Python identifiers, quoted strings, numbers
_IDENT_RE  = re.compile(r'\b([A-Za-z_]\w*)\b')
_STRING_RE = re.compile(
    r'(?:f|F|r|R|b|B|u|U)?(?:\'\'\'[\s\S]*?\'\'\'|"""[\s\S]*?"""|'
    r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\")"
)
_NUMBER_RE = re.compile(r'\b(\d+(?:\.\d*)?(?:[eE][+-]?\d+)?[jJ]?|\d+)\b')


def apply_token_replacement(text: str, rmap: dict[str, str]) -> str:
    """
    Replace tokens in *text* according to rmap using regex (works on
    non-valid Python, i.e. after syntax compression has added <SYN_N> markers).

    Processing order:
        1. String literals (protect their content from identifier replacement)
        2. Number literals
        3. Identifiers (word-boundary aware, skips already-replaced placeholders)
    """
    if not rmap:
        return text

    # Separate rmap by category
    str_words = {w: p for w, p in rmap.items()
                 if p in (PLACEHOLDERS["string"], PLACEHOLDERS["fstring"])}
    num_words  = {w: p for w, p in rmap.items() if p == PLACEHOLDERS["number"]}
    id_words   = {w: p for w, p in rmap.items()
                  if p in (PLACEHOLDERS["variable"], PLACEHOLDERS["attribute"])}

    # Step 1 — strings (replace entire literals)
    if str_words:
        def _replace_str(m):
            s = m.group(0)
            return str_words.get(s, s)
        text = _STRING_RE.sub(_replace_str, text)

    # Step 2 — numbers
    if num_words:
        def _replace_num(m):
            n = m.group(0)
            return num_words.get(n, n)
        text = _NUMBER_RE.sub(_replace_num, text)

    # Step 3 — identifiers (word-boundary match, avoid hitting placeholders)
    if id_words:
        def _replace_id(m):
            word = m.group(1)
            return id_words.get(word, word)
        text = _IDENT_RE.sub(_replace_id, text)

    return text


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: one-call score summary
# ─────────────────────────────────────────────────────────────────────────────

def score_summary(scores: dict[str, TokenInfo], top_n: int = 20) -> list[dict]:
    """Return top-N tokens by score as a list of dicts (for reporting)."""
    top = sorted(scores.values(), key=lambda x: x.score, reverse=True)[:top_n]
    return [
        {
            "word":      t.word,
            "category":  t.category,
            "score":     round(t.score, 4),
            "delta_T":   round(t.delta_T, 1),
            "self_info": round(t.self_info, 4),
            "freq":      t.freq,
            "spt":       round(t.spt, 2),
        }
        for t in top
    ]
