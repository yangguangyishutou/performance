# rewrite_200k report

## Corpus (frozen)

- **manifest**: `E:\cursor\SITP1\performance-work2\entropy_tokenizer_v2\results\stage3ab_starcoder_200k\frozen_corpus_manifest.json`
- **sources**: 132 files, tokenizer `gpt4`

## Aggregate token deltas (sum of per-file true-token counts at Stage2→Stage3 input)

| Variant | Sum before | Sum after | Delta | Reduction % |
|---------|------------|-----------|-------|-------------|
| old hybrid_ab | 178255 | 174530 | 3725 | 2.0897% |
| fast_try-style hybrid_ab | 178255 | 174790 | 3465 | 1.9438% |
| rewrite Stage3 AB | 178255 | 178300 | -45 | -0.0252% |

**Largest corpus-level delta (this run): `old_baseline`** (Δ=3725 tokens).

## Rewrite channel totals

- **total_a_saved_true** (sum of per-file body savings): 0
- **total_b_saved_true**: 227
- **total_a_intro_true**: 0
- **total_b_intro_true**: 127
- **total_net_true** (A net + B net): 100
- **strict single-token alias picks** (assignments): 0
- **alias tier histogram** (JSON): `{}`

## Route (initial pass, summed over files)

- **delete_now**: 2
- **retain_for_b**: 35
- **retain_as_reference_candidate**: 44
- **docstrings_detected**: 1
- **comments_detected**: 36

## Answers (this frozen run)

1. **Strict single-token pool**: aliases with `measure_true_token_len==1` are tier-1 and ordered before multi-token candidates (`rewrite_stage3ab/channels/a_channel/alias_pool.py`).
2. **A vs previous**: tier metadata + `alias_strict_single_selections` / `alias_tier_counts_json` in summary quantify single-token usage.
3. **B near-duplicate**: noise indices are grouped by exact / norm-WS / word-Jaccard / char-Jaccard before reference evaluation; span-safe rewrite uses `char_start`/`char_end` slices.
4. **Span safety**: `ReferenceCodecV1.rewrite_text` replaces only verified `[start:end)` slices matching cluster literals when spans exist.
5. **Route retention**: see route columns in `rewrite_200k_summary.csv` / table above.
6. **Gap to default pipeline**: rewrite still bypasses full `v2_eval` / marker accounting; integrate behind same entrypoint and align guardrails with `hybrid_ab` for production default.

Artifacts: `rewrite_200k_summary.csv`, `rewrite_200k_detail.csv`, `rewrite_200k_examples.md`, `rewrite_200k_ledger.jsonl`.
