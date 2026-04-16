"""Lightweight lexical clustering codec for Stage3 hybrid B channel."""

from __future__ import annotations

import ast
import io
import math
import re
import tokenize
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from config import VOCAB_COST_MODE
from placeholder_accounting import compute_vocab_intro_cost
from token_scorer import _line_start_offsets, _pos_to_offset

from .string_classifier import SemanticClassifierConfig, classify_semantic_free_text

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]+")
_HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
_UUID_RE = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
_NUM_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_BASE62_ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


@dataclass(slots=True)
class BCluster:
    code: str
    representative: str
    members: list[str]
    avg_similarity: float


@dataclass(slots=True)
class BCodecResult:
    encoded_text: str
    clusters: list[BCluster] = field(default_factory=list)
    candidates: int = 0
    cluster_count: int = 0
    used_clusters: int = 0
    intro_tokens: int = 0
    sequence_saved: int = 0
    effective_net_saving: int = 0
    fallback_count: int = 0
    risk_reject_count: int = 0
    avg_similarity: float = 0.0
    vocab_entries: list[dict[str, Any]] = field(default_factory=list)
    similarity_kind: str = "lexical_bow_cosine"
    mode: str = "lexical_free_text_baseline"
    reject_reason_counts: dict[str, int] = field(default_factory=dict)
    intro_not_worth_count: int = 0
    global_used_codes: int = 0
    global_used_literals: int = 0
    global_sequence_saved: int = 0
    global_vocab_entries: list[dict[str, Any]] = field(default_factory=list)


def _token_len(tokenizer: Any, tok_type: str, text: str) -> int:
    from marker_count import encode as _encode

    return len(_encode(tokenizer, tok_type, text))


def _vec(text: str) -> Counter[str]:
    return Counter(x.lower() for x in _WORD_RE.findall(text))


def _cos(a: Counter[str], b: Counter[str]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(v * b.get(k, 0) for k, v in a.items())
    na = math.sqrt(sum(v * v for v in a.values()))
    nb = math.sqrt(sum(v * v for v in b.values()))
    if na <= 0 or nb <= 0:
        return 0.0
    return dot / (na * nb)


def _char_ngrams(text: str, n: int = 3) -> set[str]:
    s = re.sub(r"\s+", " ", text.lower()).strip()
    if not s:
        return set()
    if len(s) < n:
        return {s}
    return {s[i : i + n] for i in range(len(s) - n + 1)}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    uni = len(a | b)
    if uni <= 0:
        return 0.0
    return inter / uni


def _light_stem(word: str) -> str:
    """Tiny, dependency-free normalizer for cluster-keyword extraction."""
    w = (word or "").lower()
    for suf in ("ing", "ed", "es", "s"):
        if len(w) > len(suf) + 2 and w.endswith(suf):
            return w[: -len(suf)]
    return w


def _base62(num: int) -> str:
    n = int(num)
    if n <= 0:
        return "0"
    out: list[str] = []
    base = len(_BASE62_ALPHABET)
    while n > 0:
        n, rem = divmod(n, base)
        out.append(_BASE62_ALPHABET[rem])
    out.reverse()
    return "".join(out)


def _normalize_for_similarity(text: str, mode: str) -> str:
    m = (mode or "").strip().lower()
    if m in {"", "none", "raw"}:
        return text
    s = text or ""
    s = _UUID_RE.sub(" <uuid> ", s)
    s = _HEX_RE.sub(" <hex> ", s)
    s = _NUM_RE.sub(" <num> ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _cluster_definition(
    member_texts: list[str],
    representative: str,
    *,
    definition_mode: str,
    min_df_ratio: float,
    max_terms: int,
) -> str:
    mode = (definition_mode or "").strip().lower()
    if mode in {"representative", "rep"}:
        return representative
    return _cluster_definition_signature(
        member_texts,
        representative,
        min_df_ratio=min_df_ratio,
        max_terms=max_terms,
    )


def _build_code_inner(idx: int, *, code_prefix: str, code_style: str) -> str:
    style = (code_style or "").strip().lower()
    if style in {"base62", "compact"}:
        return f"{code_prefix}{_base62(idx)}"
    return f"{code_prefix}{idx}"


def _pick_representative(
    members: list[str],
    *,
    tokenizer: Any,
    tok_type: str,
    inners: dict[str, str],
    sim_fn: Any,
) -> str:
    return min(
        members,
        key=lambda cand: (
            _token_len(tokenizer, tok_type, cand),
            -(
                sum(sim_fn(cand, other) for other in members if other != cand)
                / max(1, len(members) - 1)
            ),
            len(inners[cand]),
        ),
    )


def _cluster_definition_signature(
    member_texts: list[str],
    representative: str,
    *,
    min_df_ratio: float = 0.6,
    max_terms: int = 10,
) -> str:
    """
    Build a short semantic signature for a cluster definition.

    Using concise shared keywords reduces B-channel intro cost materially while
    still exposing the cluster topic.
    """
    if not member_texts:
        return representative

    docs: list[list[str]] = []
    for t in member_texts:
        words = [_light_stem(w) for w in _WORD_RE.findall((t or "").lower())]
        seen: set[str] = set()
        uniq = [w for w in words if w and not (w in seen or seen.add(w))]
        docs.append(uniq)

    df: Counter[str] = Counter()
    for d in docs:
        for w in d:
            df[w] += 1

    rep_words = [_light_stem(w) for w in _WORD_RE.findall((representative or "").lower())]
    rep_pos: dict[str, int] = {}
    for i, w in enumerate(rep_words):
        if w and w not in rep_pos:
            rep_pos[w] = i

    min_df = max(2, int(math.ceil(len(member_texts) * float(min_df_ratio))))
    cands = [w for w, c in df.items() if c >= min_df and len(w) >= 3]
    cands.sort(key=lambda w: (-df[w], rep_pos.get(w, 10**6), w))
    picked = cands[: max_terms]

    if not picked:
        raw = [w.lower() for w in _WORD_RE.findall((representative or ""))]
        picked = raw[: max_terms]
    if not picked:
        return representative
    return " ".join(picked)


def _apply_spans(text: str, spans: list[tuple[int, int, str]]) -> str:
    out = text
    for st, ed, rep in sorted(spans, key=lambda x: x[0], reverse=True):
        out = out[:st] + rep + out[ed:]
    return out


def encode_semantic_strings(
    text: str,
    *,
    tokenizer: Any,
    tok_type: str,
    similarity_threshold: float = 0.82,
    risk_threshold: float = 0.72,
    min_cluster_size: int = 2,
    classifier_cfg: SemanticClassifierConfig | None = None,
    code_prefix: str = "__abB",
    code_style: str = "prefix_index",
    similarity_kind: str = "lexical_bow_cosine",
    lexical_weight: float = 0.7,
    char_weight: float = 0.3,
    ngram_n: int = 3,
    similarity_norm: str = "none",
    definition_mode: str = "shared_terms",
    definition_min_df_ratio: float = 0.6,
    definition_max_terms: int = 10,
    member_select_mode: str = "all",
    global_norm_codebook: dict[str, str] | None = None,
    global_code_definition: dict[str, str] | None = None,
    global_codes_are_predefined: bool = True,
) -> BCodecResult:
    cfg = classifier_cfg or SemanticClassifierConfig()
    try:
        toks = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return BCodecResult(encoded_text=text)

    line_starts = _line_start_offsets(text)
    occurrences: dict[str, list[tuple[int, int]]] = {}
    inners: dict[str, str] = {}
    global_occurrences: dict[str, list[tuple[int, int]]] = {}
    global_code_surface_by_literal: dict[str, str] = {}
    global_code_inner_by_literal: dict[str, str] = {}
    global_definition_by_code = dict(global_code_definition or {})
    route_rejects: Counter[str] = Counter()
    g_map = dict(global_norm_codebook or {})
    for tok in toks:
        if tok.type != tokenize.STRING:
            continue
        sp = tok.string
        route, reason = classify_semantic_free_text(sp, cfg)
        if route != "B":
            route_rejects[f"route_{reason}"] += 1
            continue
        try:
            inner = ast.literal_eval(sp)
        except (SyntaxError, ValueError, MemoryError):
            continue
        if not isinstance(inner, str):
            continue
        st = _pos_to_offset(line_starts, tok.start)
        ed = _pos_to_offset(line_starts, tok.end)
        norm_key = _normalize_for_similarity(inner, similarity_norm)
        g_code_inner = g_map.get(norm_key)
        if g_code_inner:
            code_inner = str(g_code_inner)
            global_occurrences.setdefault(sp, []).append((st, ed))
            global_code_surface_by_literal[sp] = repr(code_inner)
            global_code_inner_by_literal[sp] = code_inner
            if code_inner not in global_definition_by_code:
                global_definition_by_code[code_inner] = inner
            continue
        occurrences.setdefault(sp, []).append((st, ed))
        inners[sp] = inner

    cands = len(occurrences) + len(global_occurrences)
    if cands == 0:
        return BCodecResult(encoded_text=text)

    normed = {
        sp: _normalize_for_similarity(inner, similarity_norm) for sp, inner in inners.items()
    }
    vecs = {sp: _vec(val) for sp, val in normed.items()}
    grams = {sp: _char_ngrams(val, n=max(2, int(ngram_n))) for sp, val in normed.items()}
    use_mixed = (similarity_kind or "").strip().lower() in {"hybrid_lexical_char", "mixed"}
    lw = max(0.0, float(lexical_weight))
    cw = max(0.0, float(char_weight))
    wsum = max(1e-9, lw + cw)

    def _sim(lhs: str, rhs: str) -> float:
        lexical = _cos(vecs[lhs], vecs[rhs])
        if not use_mixed:
            return lexical
        char = _jaccard(grams[lhs], grams[rhs])
        return (lw * lexical + cw * char) / wsum

    literals = list(occurrences.keys())
    clusters: list[list[str]] = []
    for sp in literals:
        placed = False
        for cl in clusters:
            sims = [_sim(sp, other) for other in cl]
            if sims and sum(sims) / len(sims) >= similarity_threshold:
                cl.append(sp)
                placed = True
                break
        if not placed:
            clusters.append([sp])

    usable: list[BCluster] = []
    replacements: dict[str, str] = {}
    vocab_entries: list[dict[str, Any]] = []
    global_vocab_entries: list[dict[str, Any]] = []
    risk_reject_count = 0
    fallback_count = 0
    intro_not_worth_count = 0
    seq_saved = 0
    intro = 0
    global_used_codes: set[str] = set()
    global_used_literals = 0
    global_seq_saved = 0
    sim_values: list[float] = []

    sel_mode = (member_select_mode or "").strip().lower()
    if sel_mode not in {"all", "drop_negative", "net_greedy"}:
        sel_mode = "all"

    for lit, spans_lit in global_occurrences.items():
        rep = global_code_surface_by_literal.get(lit)
        code_inner = global_code_inner_by_literal.get(lit)
        if not rep or not code_inner:
            fallback_count += len(spans_lit)
            continue
        cnt = len(spans_lit)
        gain = cnt * (_token_len(tokenizer, tok_type, lit) - _token_len(tokenizer, tok_type, rep))
        if gain <= 0:
            fallback_count += cnt
            continue
        replacements[lit] = rep
        global_used_literals += cnt
        global_used_codes.add(code_inner)
        global_seq_saved += gain
        seq_saved += gain

    for idx, members in enumerate(clusters):
        if len(members) < min_cluster_size:
            fallback_count += len(members)
            continue
        code_inner = _build_code_inner(idx, code_prefix=code_prefix, code_style=code_style)
        code_surface = repr(code_inner)

        gains: dict[str, int] = {}
        for m in members:
            cnt = len(occurrences[m])
            gains[m] = cnt * (
                _token_len(tokenizer, tok_type, m)
                - _token_len(tokenizer, tok_type, code_surface)
            )

        candidate_subsets: list[list[str]]
        if sel_mode == "all":
            candidate_subsets = [list(members)]
        else:
            positive_members = [m for m in members if gains.get(m, 0) > 0]
            if len(positive_members) < min_cluster_size:
                fallback_count += len(members)
                continue
            if sel_mode == "drop_negative":
                candidate_subsets = [list(positive_members)]
            else:
                ordered = sorted(
                    positive_members,
                    key=lambda m: (-gains[m], -len(occurrences.get(m, [])), m),
                )
                candidate_subsets = [
                    ordered[:k] for k in range(min_cluster_size, len(ordered) + 1)
                ]

        best_choice: tuple[list[str], str, float, dict[str, Any], int, int] | None = None
        saw_risk_reject = False
        for subset in candidate_subsets:
            if len(subset) < min_cluster_size:
                continue
            rep = _pick_representative(
                subset,
                tokenizer=tokenizer,
                tok_type=tok_type,
                inners=inners,
                sim_fn=_sim,
            )
            sims = [_sim(m, rep) for m in subset if m != rep]
            avg_sim = sum(sims) / len(sims) if sims else 1.0
            if avg_sim < risk_threshold:
                saw_risk_reject = True
                continue
            definition_sig = _cluster_definition(
                [inners[m] for m in subset],
                inners[rep],
                definition_mode=definition_mode,
                min_df_ratio=float(definition_min_df_ratio),
                max_terms=int(definition_max_terms),
            )
            intro_entry = {
                "token": code_surface,
                "kind": "stage3_ab_b_cluster",
                "definition": definition_sig,
                "cluster_size": len(subset),
            }
            intro_cost = compute_vocab_intro_cost(
                [intro_entry],
                mode=VOCAB_COST_MODE,
                tokenizer=tokenizer,
                tok_type=tok_type,
            )
            seq_gain = sum(gains[m] for m in subset)
            if seq_gain <= intro_cost:
                continue
            if best_choice is None or (seq_gain - intro_cost) > (best_choice[4] - best_choice[5]):
                best_choice = (subset, rep, avg_sim, intro_entry, seq_gain, intro_cost)

        if best_choice is None:
            if saw_risk_reject:
                risk_reject_count += len(members)
            else:
                intro_not_worth_count += 1
            fallback_count += len(members)
            continue

        subset, rep, avg_sim, intro_entry, seq_gain, intro_cost = best_choice
        for m in subset:
            replacements[m] = code_surface
        usable.append(
            BCluster(
                code=code_inner,
                representative=inners[rep],
                members=list(subset),
                avg_similarity=avg_sim,
            )
        )
        vocab_entries.append(intro_entry)
        seq_saved += seq_gain
        intro += intro_cost
        sim_values.append(avg_sim)

    if global_used_codes:
        for code_inner in sorted(global_used_codes):
            intro_entry = {
                "token": repr(code_inner),
                "kind": "stage3_ab_b_global_cluster",
                "definition": str(global_definition_by_code.get(code_inner, code_inner)),
            }
            global_vocab_entries.append(intro_entry)
        if not global_codes_are_predefined:
            intro_global = compute_vocab_intro_cost(
                global_vocab_entries,
                mode=VOCAB_COST_MODE,
                tokenizer=tokenizer,
                tok_type=tok_type,
            )
            intro += int(intro_global)

    spans: list[tuple[int, int, str]] = []
    for lit, rep in replacements.items():
        for st, ed in occurrences.get(lit, []):
            spans.append((st, ed, rep))
    encoded = _apply_spans(text, spans) if spans else text

    return BCodecResult(
        encoded_text=encoded,
        clusters=usable,
        candidates=cands,
        cluster_count=len(clusters),
        used_clusters=len(usable),
        intro_tokens=intro,
        sequence_saved=seq_saved,
        effective_net_saving=seq_saved - intro,
        fallback_count=fallback_count,
        risk_reject_count=risk_reject_count,
        avg_similarity=(sum(sim_values) / len(sim_values)) if sim_values else 0.0,
        vocab_entries=vocab_entries,
        similarity_kind="hybrid_lexical_char" if use_mixed else "lexical_bow_cosine",
        mode=(
            "lexical_free_text_mixed"
            if use_mixed
            else "lexical_free_text_baseline"
        ),
        reject_reason_counts=dict(route_rejects),
        intro_not_worth_count=intro_not_worth_count,
        global_used_codes=len(global_used_codes),
        global_used_literals=global_used_literals,
        global_sequence_saved=global_seq_saved,
        global_vocab_entries=global_vocab_entries,
    )

