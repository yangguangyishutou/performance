# HumanEval with Stage3AB

This repo now includes a small HumanEval harness for `stage3ab` compression.

## What it measures

The intended comparison unit is:

- raw arm: `task prompt + raw support context`
- compressed arm: `task prompt + codebook + compressed support context`

The codebook is treated as real model input. Its cost is not ignored.

## Important scope

- Keep the HumanEval task `prompt` unchanged.
- Compress only the retrieved support context.
- Do **not** use `canonical_solution` or `test` when building support or codebooks.

## Files

- `eval/humaneval_prepare.py`: retrieve support, run `stage3ab`, build codebook, write prepared JSONL
- `eval/humaneval_generate.py`: call `OpenAI API` or `vLLM` and write `samples.jsonl`
- `eval/humaneval_score.py`: wrapper around the official HumanEval scorer
- `eval/humaneval_report.py`: merge prompt metadata and generation details into CSV

## Backend notes

- `openai`: works in the current Windows Python environment once `OPENAI_API_KEY` is set
- `vllm`: code path is included, but real execution requires Linux / WSL with `vllm` installed

## Minimal configuration

OpenAI API:

```powershell
$env:OPENAI_API_KEY="..."
```

Optional:

```powershell
$env:OPENAI_BASE_URL="https://your-proxy-or-compatible-endpoint/v1"
```

## Prepare prompts

Example with the repo's existing StarCoder-style support dataset:

```powershell
python eval/humaneval_prepare.py `
  --limit 20 `
  --support-dataset zhensuuu/starcoderdata_100star_py `
  --support-top-k 4 `
  --compression-tokenizer gpt4 `
  --stage3-ab-mode exact_only `
  --tag smoke
```

Example with a local repo as support corpus:

```powershell
python eval/humaneval_prepare.py `
  --limit 20 `
  --support-repo E:\path\to\python_repo `
  --support-top-k 4 `
  --compression-tokenizer gpt4 `
  --stage3-ab-mode exact_only `
  --tag localrepo
```

## Generate completions with OpenAI API

```powershell
python eval/humaneval_generate.py `
  --input results/humaneval/prepared_stage3ab_smoke.jsonl `
  --backend openai `
  --model gpt-4o-mini `
  --arm compressed `
  --n 1 `
  --temperature 0 `
  --max-new-tokens 256 `
  --tag smoke
```

Raw baseline:

```powershell
python eval/humaneval_generate.py `
  --input results/humaneval/prepared_stage3ab_smoke.jsonl `
  --backend openai `
  --model gpt-4o-mini `
  --arm raw `
  --n 1 `
  --temperature 0 `
  --max-new-tokens 256 `
  --tag smoke
```

## Generate completions with vLLM

Run this from Linux / WSL where `vllm` is installed:

```bash
python eval/humaneval_generate.py \
  --input results/humaneval/prepared_stage3ab_smoke.jsonl \
  --backend vllm \
  --model Qwen/Qwen2.5-Coder-1.5B-Instruct \
  --arm compressed \
  --n 1 \
  --temperature 0 \
  --max-new-tokens 256 \
  --tag smoke
```

## Score with official HumanEval

Install the scorer first:

```powershell
pip install git+https://github.com/openai/human-eval.git
```

Then run:

```powershell
python eval/humaneval_score.py `
  --samples results/humaneval/samples_compressed_openai_smoke.jsonl `
  --k 1,10,100
```

## Build a compact report

```powershell
python eval/humaneval_report.py `
  --prepared results/humaneval/prepared_stage3ab_smoke.jsonl `
  --details results/humaneval/generation_compressed_openai_smoke.jsonl `
  --output results/humaneval/report_compressed_openai_smoke.csv
```

## Recommended experiment order

1. `exact_only`, 10-20 tasks, `n=1`
2. `exact_only`, full HumanEval, `pass@1`
3. `hybrid`, full HumanEval, `pass@1`
4. Formal `pass@k` with multiple samples per task

## What to compare

- `raw` vs `compressed`
- `exact_only` vs `hybrid`
- `raw_context_tokens` vs `compressed_context_effective_tokens`
- `stage3_ab_a_sequence_saved` vs `stage3_ab_b_sequence_saved`
- failure cases where raw passes and compressed fails

