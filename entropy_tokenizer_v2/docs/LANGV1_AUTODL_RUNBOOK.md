# LangV1 AutoDL Runbook

This is the validated runbook for the low-cost `LangV1` pilot on the AutoDL
server we used for the `Qwen/Qwen2.5-Coder-1.5B` experiments.

Use this document before restarting work on the remote box. It records:

- the known-good environment shape
- the mistakes that wasted time
- the exact command sequence that worked
- the latest measured results
- what to check before shutting the server down

## What Must Be Preserved

The important assets from the latest run live on the remote server under:

```text
/root/workspaces/entropy_tokenizer_v2
```

Remote prerequisites that must still exist before rerunning:

- `cache/stage1_starcoder_1m_corpus.jsonl`
- `cache/humaneval/HumanEval_ascii_subset_164.jsonl`

Key artifacts:

- `cache/langv1_pilot/stage3_global_dictionary_qwen_small.json`
- `results/langv1_pilot/langv1_cpt_dataset_qwen_small_structured.jsonl`
- `results/langv1_pilot/langv1_sft_dataset_qwen_small_structured.jsonl`
- `results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt`
- `results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt_sft`
- `results/humaneval/prepared_stage3ab_langv1_qwen15b_qwen_small_structured.jsonl`
- `results/humaneval/samples_raw_transformers_qwen15b_qsmall_structured_lora_raw.jsonl`
- `results/humaneval/samples_compressed_transformers_qwen15b_qsmall_structured_lora_compressed.jsonl`

Useful local mirrored logs already checked into this workspace:

- `results_fast_try/remote_qwen_qsmall_summary.log`
- `results_fast_try/remote_structured_final_summary.log`
- `results_fast_try/remote_negative_compression_breakdown.log`

If the AutoDL instance will only be powered off, these should remain on its
persistent disk. If the instance will be destroyed, copy them out first.

## Known-Good Remote Environment

Validated remote assumptions:

- Linux GPU server on AutoDL
- GPU detected as `RTX 4080 SUPER 32GB`
- repo root: `/root/workspaces/entropy_tokenizer_v2`
- Python env: `/root/.venv-langv1`
- `torch 2.5.1+cu124` already working with CUDA on the server

Safe environment variables used for long runs:

```bash
HF_ENDPOINT=https://hf-mirror.com
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
PYTHONUNBUFFERED=1
```

## Do Not Repeat These Mistakes

These were the main time sinks from the first attempts:

1. Do not install Miniforge interactively over SSH.
   - The `.sh` installer expects interaction unless called with `-b`.
   - Rebuilding the whole Python stack was unnecessary anyway.

2. Do not download GPU `torch` from `https://download.pytorch.org` on AutoDL.
   - The large wheel download was slow and unreliable from the server.
   - Reuse the server's working CUDA `torch` build whenever possible.

3. Do not block on `stdout.read()` when running long SSH commands.
   - It hides progress and looks like a dead hang.
   - Use a streaming SSH channel and poll `recv_ready()`.

4. Do not blindly retry Hugging Face downloads after an interrupted run.
   - Stale `*.lock` files can leave the next process sleeping forever.
   - Clear the stale locks first.

5. Do not wipe the remote workspace casually.
   - `remote_bootstrap_lang_v1.py` now preserves the remote workspace by
     default.
   - Use `--clean-remote` only for disposable runs.

6. Do not change the tokenizer/model pair mid-experiment.
   - If the model is `Qwen/Qwen2.5-Coder-1.5B`, token accounting and global
     dictionary selection must also use the Qwen tokenizer preset.

7. Do not keep natural-language runtime primers in the learned-language eval.
   - Static rules belong in training.
   - Runtime prompt should only keep structured dynamic dictionary blocks.

## Recovery Checklist Before A New Run

Run these checks first:

```bash
cd /root/workspaces/entropy_tokenizer_v2
source /root/.venv-langv1/bin/activate
```

Check GPU and Python:

```bash
nvidia-smi
python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

Check for stale Hugging Face lock files:

```bash
find ~/.cache/huggingface/hub -name "*.lock" -type f
```

If stale locks exist after an interrupted run:

```bash
find ~/.cache/huggingface/hub -name "*.lock" -type f -delete
```

Check for orphan training processes before starting a new one:

```bash
ps -ef | grep train_langv1_lora.py
```

Smoke test the prepared assets before a long run:

```bash
python - <<'PY'
from pathlib import Path
for path in [
    "cache/langv1_pilot/stage3_global_dictionary_qwen_small.json",
    "results/langv1_pilot/langv1_cpt_dataset_qwen_small_structured.jsonl",
]:
    p = Path(path)
    print(path, p.exists(), p.stat().st_size if p.exists() else None)
PY
```

## Validated Command Sequence

### 1. Build the small global dictionary

```bash
python scripts/build_stage3_global_dict.py \
  --preset qwen_small \
  --corpus cache/stage1_starcoder_1m_corpus.jsonl \
  --output cache/langv1_pilot/stage3_global_dictionary_qwen_small.json
```

Expected shape:

- A entries: `128`
- B entries: `0`

### 2. Build the structured CPT dataset

```bash
ET_STAGE3_AB_GLOBAL_DICT_ENABLE=1 \
ET_STAGE3_AB_GLOBAL_DICT_PATH=cache/langv1_pilot/stage3_global_dictionary_qwen_small.json \
ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB=0 \
python scripts/build_langv1_cpt_dataset.py \
  --overwrite \
  --corpus cache/stage1_starcoder_1m_corpus.jsonl \
  --output results/langv1_pilot/langv1_cpt_dataset_qwen_small_structured.jsonl \
  --summary-output results/langv1_pilot/langv1_cpt_dataset_qwen_small_structured.summary.json \
  --limit 120 \
  --compression-tokenizer qwen25-coder-15b \
  --stage2-profile stage2_parseable \
  --stage2-mode blockwise \
  --stage3-ab-mode exact_only \
  --global-dict cache/langv1_pilot/stage3_global_dictionary_qwen_small.json
```

### 3. Build the structured SFT dataset

```bash
ET_STAGE3_AB_GLOBAL_DICT_ENABLE=1 \
ET_STAGE3_AB_GLOBAL_DICT_PATH=cache/langv1_pilot/stage3_global_dictionary_qwen_small.json \
ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB=0 \
python scripts/build_langv1_sft_dataset.py \
  --overwrite \
  --corpus cache/stage1_starcoder_1m_corpus.jsonl \
  --output results/langv1_pilot/langv1_sft_dataset_qwen_small_structured.jsonl \
  --summary-output results/langv1_pilot/langv1_sft_dataset_qwen_small_structured.summary.json \
  --limit 120 \
  --compression-tokenizer qwen25-coder-15b \
  --stage2-profile stage2_parseable \
  --stage2-mode blockwise \
  --stage3-ab-mode exact_only \
  --global-dict cache/langv1_pilot/stage3_global_dictionary_qwen_small.json
```

### 4. Train CPT

```bash
HF_ENDPOINT=https://hf-mirror.com \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
python -u scripts/train_langv1_lora.py \
  --train-jsonl results/langv1_pilot/langv1_cpt_dataset_qwen_small_structured.jsonl \
  --train-mode cpt \
  --base-model Qwen/Qwen2.5-Coder-1.5B \
  --output-dir results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt \
  --epochs 1 \
  --learning-rate 2e-4 \
  --batch-size 2 \
  --grad-accum 4 \
  --logging-steps 5
```

### 5. Continue with SFT

```bash
HF_ENDPOINT=https://hf-mirror.com \
PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
python -u scripts/train_langv1_lora.py \
  --train-jsonl results/langv1_pilot/langv1_sft_dataset_qwen_small_structured.jsonl \
  --train-mode sft \
  --base-model Qwen/Qwen2.5-Coder-1.5B \
  --adapter-init-path results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt \
  --output-dir results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt_sft \
  --epochs 1 \
  --learning-rate 1e-4 \
  --batch-size 2 \
  --grad-accum 4 \
  --logging-steps 5
```

### 6. Prepare HumanEval-20

```bash
ET_STAGE3_AB_GLOBAL_DICT_ENABLE=1 \
ET_STAGE3_AB_GLOBAL_DICT_PATH=cache/langv1_pilot/stage3_global_dictionary_qwen_small.json \
ET_STAGE3_AB_GLOBAL_DICT_CHARGE_VOCAB=0 \
python eval/humaneval_prepare.py \
  --dataset-jsonl cache/humaneval/HumanEval_ascii_subset_164.jsonl \
  --limit 20 \
  --support-jsonl cache/stage1_starcoder_1m_corpus.jsonl \
  --support-top-k 4 \
  --compression-tokenizer qwen25-coder-15b \
  --stage3-ab-mode exact_only \
  --stage2-profile stage2_parseable \
  --stage2-mode blockwise \
  --prompt-style structured \
  --tag langv1_qwen15b_qwen_small_structured
```

### 7. Generate raw and compressed with the LoRA adapter

```bash
HF_ENDPOINT=https://hf-mirror.com \
python eval/humaneval_generate.py \
  --input results/humaneval/prepared_stage3ab_langv1_qwen15b_qwen_small_structured.jsonl \
  --backend transformers \
  --model Qwen/Qwen2.5-Coder-1.5B \
  --adapter-path results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt_sft \
  --arm raw \
  --n 1 \
  --temperature 0 \
  --max-new-tokens 256 \
  --device-map auto \
  --tag qwen15b_qsmall_structured_lora_raw
```

```bash
HF_ENDPOINT=https://hf-mirror.com \
python eval/humaneval_generate.py \
  --input results/humaneval/prepared_stage3ab_langv1_qwen15b_qwen_small_structured.jsonl \
  --backend transformers \
  --model Qwen/Qwen2.5-Coder-1.5B \
  --adapter-path results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt_sft \
  --arm compressed \
  --n 1 \
  --temperature 0 \
  --max-new-tokens 256 \
  --device-map auto \
  --tag qwen15b_qsmall_structured_lora_compressed
```

### 8. Score

```bash
python eval/humaneval_score.py \
  --samples results/humaneval/samples_raw_transformers_qwen15b_qsmall_structured_lora_raw.jsonl \
  --problem-file cache/humaneval/HumanEval_ascii_subset_164.jsonl \
  --match-samples \
  --k 1 \
  --n-workers 1 \
  --timeout 15
```

```bash
python eval/humaneval_score.py \
  --samples results/humaneval/samples_compressed_transformers_qwen15b_qsmall_structured_lora_compressed.jsonl \
  --problem-file cache/humaneval/HumanEval_ascii_subset_164.jsonl \
  --match-samples \
  --k 1 \
  --n-workers 1 \
  --timeout 15
```

## Latest Verified Results

This is the latest structured run after removing natural-language runtime
primers and keeping only the structured dynamic dictionary block.

### Accuracy

- `LoRA + raw`: `10/20 = 0.50`
- `LoRA + compressed`: `10/20 = 0.50`

The learned-language route is now preserving accuracy relative to the same
LoRA model on raw prompts.

### Token Accounting

Average prompt tokens:

- raw: `1155.2`
- compressed: `1162.25`
- delta: `+7.05`

Average support-context tokens:

- raw: `1027.55`
- compressed effective: `1031.6`
- delta: `+4.05`

Breakdown of the prompt delta:

- compressed support body: about `+3.25`
- dynamic dictionary: about `+0.8`
- wrapper tags / structure overhead: about `+3.0`

Current conclusion:

- removing runtime prose solved most of the old overhead
- the remaining negative compression now comes mostly from the compressed body
  itself not being shorter enough under the Qwen tokenizer

## Why The Negative Compression Still Exists

The current `LangV1` design still pays token overhead in three places:

1. wrapper tags such as `<LANGV1_HUMANEVAL>` and `<COMPRESSED_SUPPORT>`
2. dynamic dictionary entries that are still sent at runtime
3. aliases and placeholders whose tokenization under the Qwen tokenizer is not
   yet cheap enough to offset the replaced text

This means the next optimization target is not more primer removal. The next
target is the compression body itself.

## Fast Rules For The Next Iteration

1. Keep static rules in training only.
2. Keep runtime prompt structure minimal and machine-readable.
3. Only send dynamic dictionary entries when they have positive net savings.
4. Only keep aliases that are net-positive under the same tokenizer used by
   the downstream model.
5. Smoke test with `--limit 2` before launching a full `HumanEval-20` run.

## Shutdown Checklist

Before stopping the AutoDL box:

1. Confirm there is no active long-running process:

```bash
ps -ef | grep -E "train_langv1_lora|humaneval_generate|humaneval_prepare"
```

2. Confirm the latest checkpoint directories still exist:

```bash
ls results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt
ls results/langv1_pilot/checkpoints/qwen15b_langv1_qwen_small_structured_cpt_sft
```

3. Confirm the prepared/eval outputs still exist:

```bash
ls results/humaneval/prepared_stage3ab_langv1_qwen15b_qwen_small_structured.jsonl
ls results/humaneval/samples_*qwen15b_qsmall_structured*
```

4. Stop the instance from the AutoDL console after the checks pass.

Do not leave the machine running idle.
