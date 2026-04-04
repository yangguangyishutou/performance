# Validation plan (rewrite Stage3 AB)

This document describes how to validate each future pillar **without** mixing concerns in one giant eval script.

## 1. Tokenizer-aware primary metric

- **Invariant**: Every savings claim in the rewrite tree must be reproducible from `measure_true_token_len` (or an injected `TrueTokenMeasurer` used in tests).
- **Checks**:
  - Golden strings: fixed snippets × tokenizer keys (`gpt4`, `gpt2`) — compare against legacy `marker_count.encode` length.
  - Property: `measure_true_token_len("", k) == 0`.
- **Non-goals this round**: Replacing `count_augmented` in the main eval CSV (adapter may expose both).

## 2. A-channel token economics

- **Unit tests**: `estimate_alias_replacement_gain` / `compute_token_economics_score` with mocked lengths.
- **Integration**: Single-file corpus where one alias is obviously net-positive; expect ledger + telemetry to record positive `net_saved_true`.
- **Regression**: When wiring production A, diff against current `stage3_ab_a_*` telemetry totals on a frozen micro-corpus.

## 3. B-channel small-cluster reference mode

- **Unit tests**: `ReferenceCodec.rewrite_text` round-trip on synthetic clusters.
- **Integration**: Force `min_cluster_size=1` policy in router + reference codec; verify `BChannelResult.references_or_templates` non-empty.
- **Safety**: Reject paths must populate `rejected_clusters_by_reason` without throwing.

## 4. HDBSCAN (future backend)

- **Gate**: Register `ClusterBackendId.HDBSCAN_FUTURE` only when dependency and baseline numerics are pinned.
- **Smoke**: Small 2D toy feature space → cluster count sanity (no production code yet).

## 5. Stage2 / B routing

- **Unit tests**: `RouteDecision` respects starvation budget (once defined).
- **Integration**: Adapter ingests real `stage2_retained_for_b_*` sums from legacy eval meta; router output matches expectations on frozen JSON.

## 6. Examples ledger

- **Schema**: Ledger entries serialize to JSONL (one row per A/B/reject event).
- **Manual review**: Sample 20 rows from 200k run; ensure before/after clips are non-empty for applied edits.

## Running scaffold checks today

```bash
cd entropy_tokenizer_v2
pytest rewrite_stage3ab/tests -q
python -m rewrite_stage3ab.validation
```

No large downloads or result directories are required for the above.
