"""
Per-Repository Dynamic Mining (v2)

"Dynamic" means: every repository gets its own compression rule set,
derived exclusively from that repository's own code.

Pipeline (run once per repo before evaluation):
  [1] Collect all .py files from the repository.
  [2] Lossless clean (remove comments / blank lines) so AST parsing stays valid.
  [3] Mine syntax skeletons -> MDL selection -> SkeletonCandidate list.
  [4] Build token vocabulary -> compute scores -> select replacement set.
  [5] Persist the RepoConfig to cache (JSON) for reuse.

The resulting RepoConfig is a self-contained compression specification:
  apply_v2_compression(source, repo_config, tokenizer) -> compressed_str
"""

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

from tqdm.auto import tqdm

from config import (
    AST_MIN_FREQ, CACHE_DIR, MDL_CODEBOOK_OVERHEAD,
    SCORE_THRESHOLD_PERCENTILE, SCORE_EPSILON,
)
from lossy_cleaner import lossless_clean
from syntax_compressor import (
    SkeletonCandidate, build_candidate_pool,
    greedy_mdl_select, mine_skeletons,
)
from marker_count import encode as _encode
from token_scorer import (
    build_replacement_map, build_vocabulary,
    compute_scores, select_replacement_set,
)


# ─────────────────────────────────────────────────────────────────────────────
# RepoConfig — the output of mining, the input to compression / evaluation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RepoConfig:
    """
    All compression rules derived from one repository.

    selected_skeletons : MDL-accepted syntax patterns (in acceptance order).
    replacement_map    : {original_token: placeholder} for Stage-3 replacement.
    scores_summary     : top-50 token scores for reporting.
    n_sources          : number of files mined.
    N_baseline_tokens  : total tokens in the corpus under the target tokenizer.
    V0                 : base vocabulary size of the target tokenizer.
    tokenizer_key      : label of the tokenizer used during mining.
    """
    selected_skeletons:  list[dict] = field(default_factory=list)
    replacement_map:     dict[str, str] = field(default_factory=dict)
    scores_summary:      list[dict] = field(default_factory=list)
    n_sources:           int = 0
    N_baseline_tokens:   int = 0
    V0:                  int = 0
    tokenizer_key:       str = ""

    # ── convenience accessors ──────────────────────────────────────────────

    def skeleton_candidates(self) -> list[SkeletonCandidate]:
        return [SkeletonCandidate(**d) for d in self.selected_skeletons]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

    @classmethod
    def from_json(cls, s: str) -> "RepoConfig":
        d = json.loads(s)
        return cls(**d)


# ─────────────────────────────────────────────────────────────────────────────
# Tokenizer helpers (duplicated locally so repo_miner is self-contained)
# ─────────────────────────────────────────────────────────────────────────────

def _load_tokenizer(tok_key: str, cfg: dict):
    if cfg["type"] == "tiktoken":
        import tiktoken
        return tiktoken.encoding_for_model(cfg["tiktoken_model"]), "tiktoken"
    import transformers
    from config import HF_TOKEN
    tok = transformers.AutoTokenizer.from_pretrained(
        cfg["name"], trust_remote_code=True, token=HF_TOKEN,
    )
    return tok, "hf"


def _vocab_size(tokenizer, tok_type: str) -> int:
    if tok_type == "tiktoken":
        return tokenizer.n_vocab
    vs = getattr(tokenizer, "vocab_size", None)
    if vs is not None:
        return int(vs)
    return len(tokenizer)


# ─────────────────────────────────────────────────────────────────────────────
# Source collection
# ─────────────────────────────────────────────────────────────────────────────

def collect_py_sources(repo_path: str | Path) -> list[str]:
    """
    Recursively collect the text content of all .py files under repo_path.
    Silently skips unreadable files.
    """
    sources: list[str] = []
    for root, _dirs, files in os.walk(str(repo_path)):
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                    sources.append(f.read())
            except OSError:
                continue
    return sources


# ─────────────────────────────────────────────────────────────────────────────
# Core mining function
# ─────────────────────────────────────────────────────────────────────────────

def mine_repo(
    sources: list[str],
    tokenizer,
    tok_type: str,
    V0: int,
    tokenizer_key: str = "",
    min_freq: int = AST_MIN_FREQ,
    score_percentile: float = SCORE_THRESHOLD_PERCENTILE,
    verbose: bool = True,
) -> RepoConfig:
    """
    Run the full mining pipeline for a list of source strings.
    Returns a RepoConfig ready for compression.
    """
    n = len(sources)
    if verbose:
        print(f"[repo_miner] Mining {n} source files ...")

    # [1] Lossless clean (comments removed so token counts are meaningful,
    #     indentation kept so AST parsing still works)
    clean_sources = []
    for src in sources:
        c, _ = lossless_clean(src)
        clean_sources.append(c)

    # [2] Compute baseline token count
    if verbose:
        print("[repo_miner] Computing baseline token counts ...")
    N_baseline = 0
    for src in tqdm(clean_sources, desc="  baseline tokens", disable=not verbose):
        N_baseline += len(_encode(tokenizer, tok_type, src))

    # [3] Stage 1: syntax skeleton mining + MDL selection
    if verbose:
        print("[repo_miner] Stage 1 - mining AST skeletons ...")
    skeleton_counts = mine_skeletons(clean_sources, min_freq=min_freq)
    if verbose:
        print(f"  {len(skeleton_counts)} unique skeletons (freq >= {min_freq})")

    candidates = build_candidate_pool(
        skeleton_counts, tokenizer, tok_type, sources=clean_sources
    )
    selected_skeletons = greedy_mdl_select(candidates, N_baseline, V0)
    if verbose:
        print(f"  MDL K* = {len(selected_skeletons)} accepted skeletons")
        for c in selected_skeletons[:5]:
            print(f"    [{c.skeleton[:60]}]  spi={c.savings_per_instance} "
                  f"freq={c.frequency} net_benefit={c.mdl_net_benefit:.0f}")

    # [4] Stage 3: token importance scoring
    if verbose:
        print("[repo_miner] Stage 3 - computing token importance scores ...")
    vocab = build_vocabulary(clean_sources)
    scores = compute_scores(vocab, tokenizer, tok_type)
    replacement_set = select_replacement_set(scores, score_percentile)
    rmap = build_replacement_map(scores, replacement_set)

    if verbose:
        eligible = sum(1 for info in scores.values() if info.spt > 1.0)
        print(f"  {len(scores)} unique tokens scored, "
              f"{eligible} eligible (spt>1), "
              f"{len(replacement_set)} selected for replacement")

    # [5] Build scores summary (top 50)
    from token_scorer import score_summary
    summary = score_summary(scores, top_n=50)

    return RepoConfig(
        selected_skeletons=[
            {
                "skeleton":                  c.skeleton,
                "frequency":                 c.frequency,
                "fixed_tokens":              c.fixed_tokens,
                "num_slots":                 c.num_slots,
                "savings_per_instance":      c.savings_per_instance,
                "codebook_cost":             c.codebook_cost,
                "mdl_net_benefit":           c.mdl_net_benefit,
                "empirical_total_savings":   c.empirical_total_savings,
            }
            for c in selected_skeletons
        ],
        replacement_map=rmap,
        scores_summary=summary,
        n_sources=n,
        N_baseline_tokens=N_baseline,
        V0=V0,
        tokenizer_key=tokenizer_key,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: mine from a local repo path
# ─────────────────────────────────────────────────────────────────────────────

def mine_from_repo_path(
    repo_path: str | Path,
    tokenizer_key: str,
    tokenizer_cfg: dict,
    cache: bool = True,
    verbose: bool = True,
) -> RepoConfig:
    """
    Mine compression rules for a local repository and optionally cache.
    """
    cache_file = CACHE_DIR / f"repo_config_{tokenizer_key}_{Path(repo_path).name}.json"
    if cache and cache_file.exists():
        if verbose:
            print(f"[repo_miner] Loading cached config: {cache_file}")
        return RepoConfig.from_json(cache_file.read_text(encoding="utf-8"))

    tokenizer, tok_type = _load_tokenizer(tokenizer_key, tokenizer_cfg)
    V0 = _vocab_size(tokenizer, tok_type)

    sources = collect_py_sources(repo_path)
    if not sources:
        raise ValueError(f"No .py files found in {repo_path}")
    if verbose:
        print(f"[repo_miner] Found {len(sources)} .py files in {repo_path}")

    config = mine_repo(sources, tokenizer, tok_type, V0,
                       tokenizer_key=tokenizer_key, verbose=verbose)

    if cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(config.to_json(), encoding="utf-8")
        if verbose:
            print(f"[repo_miner] Config saved to {cache_file}")

    return config


# ─────────────────────────────────────────────────────────────────────────────
# Convenience: mine from an in-memory list of sources
# ─────────────────────────────────────────────────────────────────────────────

def mine_from_sources(
    sources: list[str],
    tokenizer_key: str,
    tokenizer_cfg: dict,
    cache_name: Optional[str] = None,
    cache: bool = True,
    verbose: bool = True,
    min_freq: int = AST_MIN_FREQ,
) -> RepoConfig:
    """Mine from a list of source strings (e.g., loaded from HF dataset)."""
    if cache and cache_name:
        cache_file = CACHE_DIR / f"repo_config_{tokenizer_key}_{cache_name}.json"
        if cache_file.exists():
            if verbose:
                print(f"[repo_miner] Loading cached config: {cache_file}")
            return RepoConfig.from_json(cache_file.read_text(encoding="utf-8"))

    tokenizer, tok_type = _load_tokenizer(tokenizer_key, tokenizer_cfg)
    V0 = _vocab_size(tokenizer, tok_type)

    config = mine_repo(sources, tokenizer, tok_type, V0,
                       tokenizer_key=tokenizer_key, verbose=verbose,
                       min_freq=min_freq)

    if cache and cache_name:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file = CACHE_DIR / f"repo_config_{tokenizer_key}_{cache_name}.json"
        cache_file.write_text(config.to_json(), encoding="utf-8")
        if verbose:
            print(f"[repo_miner] Config saved to {cache_file}")

    return config
