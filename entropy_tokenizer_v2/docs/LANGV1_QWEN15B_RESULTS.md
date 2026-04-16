# LangV1 Qwen 1.5B Pilot Results

This note captures the main local results for the `Qwen/Qwen2.5-Coder-1.5B` pilot on a 20-task HumanEval slice.

## 1. Early run: poor baseline

Primary files:

- `results_fast_try/remote_eval_summary.log`
- `results_fast_try/remote_failure_summary.log`
- `results_fast_try/remote_negative_compression_breakdown.log`
- `results_fast_try/remote_score_qwen15b_base_raw.log`
- `results_fast_try/remote_score_qwen15b_base_compressed.log`
- `results_fast_try/remote_score_qwen15b_lora_compressed.log`

Headline numbers:

- raw: `2/20 = 0.10`
- base compressed: `1/20 = 0.05`
- LoRA compressed: `4/20 = 0.20`

Main takeaways:

- Compression hurt the base model relative to raw prompting.
- The compressed prompt was not actually shorter on average once wrappers and codebook cost were counted.
- Many failures were syntax-level generation failures rather than clean semantic misses.

Negative compression breakdown:

- average prompt delta: `+7.05`
- average context body delta: `+3.25`
- average codebook delta: `+0.8`
- average wrapper delta: `+3`

Interpretation:

- On this setup, the compression scheme did not buy real context savings for Qwen 1.5B.
- Wrapper overhead and dynamic dictionary overhead were enough to erase the small Stage3 gains.

## 2. Qwen small preset rerun

Primary file:

- `results_fast_try/remote_qwen_qsmall_summary.log`

Headline numbers:

- raw: `2/20 = 0.10`
- base compressed: `1/20 = 0.05`
- LoRA compressed: `8/20 = 0.40`

Prepared-context stats:

- average raw context tokens: `1027.55`
- average compressed effective tokens: `1031.6`
- average context delta: `+4.05`

Interpretation:

- The LoRA adapter helped materially.
- The compression format still failed to reduce effective prompt length on average.
- This run is useful as a training sanity check, not as evidence that the current compressed prompt format is better.

## 3. Structured prompt rerun

Primary files:

- `results_fast_try/remote_structured_final_summary.log`
- `results_fast_try/remote_score_qwen_qsmall_lora_raw.log`
- `results_fast_try/remote_score_qwen_qsmall_lora_comp.log`
- `results/humaneval/prepared_stage3ab_langv1_qwen15b_qwen_small_structured_local.meta.json`

Headline numbers:

- raw: `10/20 = 0.50`
- compressed: `10/20 = 0.50`

Prepared-context stats:

- average raw context tokens: `1027.55`
- average compressed effective tokens: `1031.6`
- average codebook tokens: `0.8`

Interpretation:

- The structured prompt fixed a large part of the earlier formatting / parsing failure mode.
- Compression still did not beat raw prompting on this 20-task slice.
- The best reading is "compression became non-destructive," not "compression became beneficial."

## 4. Global dictionary side result

Primary files:

- `results/langv1_pilot/stage3_global_dict_deepseek200.csv`
- `results/langv1_pilot/stage3_global_dict_deepseek200.json`

Headline numbers on the 200-sample pilot corpus:

- local only effective-total reduction: `14.9109569%`
- global dict effective-total reduction: `16.3713159%`
- delta: `+1.4603590 pp`

Interpretation:

- The shared dictionary materially improved compression metrics on the pilot corpus.
- That gain did not automatically translate into better Qwen HumanEval accuracy under the current prompt packaging.

## 5. Current conclusion

What looks true from these logs:

- The early Qwen 1.5B result was poor.
- The main issue was not only model quality; prompt packaging overhead and formatting instability also mattered.
- Structured prompts removed a large chunk of the damage.
- Shared dictionary improves compression metrics, but the end-to-end generation benefit is still unproven.
