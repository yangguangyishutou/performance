# Stage3 AB rewrite scaffold (`rewrite_stage3ab`)

**Branch:** develop this tree on `exp/stage3ab-architecture-scaffold` (cut from `feat/stage1-stage2-adapt` @ `4e8b3c1e`). Keep `feat/stage1-stage2-adapt` for baseline / fast_try / 200k without mixing in large refactors.

## Why a separate tree?

Production Stage3 hybrid AB lives in `stage3/backends/`, `pipeline.py`, and eval scripts. Rewriting it in place would risk breaking the working baseline (`eval_stage3ab_starcoder_200k.py`), fast-try wrappers, and cached mining configs.

This package is a **parallel architecture**: contracts first, adapters to the old stack, stub backends until real algorithms land.

## What this package **does** carry

- **Contracts**: `SourceUnit`, `StageSnapshot`, `Stage3ABRunResult`, channel results, `TelemetryEvent`.
- **Metrics**: `measure_true_token_len` (single truth source) and `compute_net_saving_true` accounting.
- **Orchestrator skeleton**: `Stage3ScaffoldRuntime`, `run_scaffold_on_units`, `Stage2Router` types (stub).
- **Channel protocols**: A (economics + alias pool hooks), B (clustering registry + reference codec skeleton).
- **Telemetry**: event helpers, `summarize_run`, `ExampleLedger`.
- **Adapters**: thin bridges to `repo_miner._load_tokenizer`, `marker_count.encode`, Stage2 meta (stub).
- **Validation**: `smoke_runner` + pytest under `rewrite_stage3ab/tests/`.

## What it **does not** carry (yet)

- HDBSCAN, embeddings, SemDeDup, DAG schedulers.
- Replacement of `encode_stage3_hybrid_ab` or `mine_from_sources`.
- Large result artifacts or 200k runs.

## Evolution roadmap (suggested)

1. Implement **TrueTokenMeasurer** injection tests; keep `measure_true_token_len` as default.
2. Swap **AChannelStub** for a thin wrapper around current exact-aliasing, then iterate toward economics-driven ranking.
3. Register real B clusterers in `clustering_stub`; add **HDBSCAN** backend behind `ClusterBackendId.HDBSCAN_FUTURE`.
4. Replace **StubStage2Router** with policy driven by Stage2 funnel + B starvation budgets.
5. Stream **ExampleLedger** rows into markdown/JSON for eval parity with `stage3ab_starcoder_200k_examples.md`.

## Smoke

From `entropy_tokenizer_v2/`:

```bash
python -m rewrite_stage3ab.validation
pytest rewrite_stage3ab/tests -q
```

## Imports

All imports assume `entropy_tokenizer_v2` is the working directory (or on `PYTHONPATH`).
