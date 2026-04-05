# rewrite_200k 与旧主线评测口径差异（定点说明）

## 已对齐（本脚本内）

- **Tokenizer**：与仓库 `EVAL_TOKENIZERS` / `marker_count.encode` 一致，true token 以 `mc_encode` 长度计量。
- **Stage1**：`apply_stage1_with_stats` 与 `mine_from_sources` 摘要一致。
- **Stage2**：`stage2_clean_skip_syn_and_stats` + `build_stage2_config` / `resolve_stage2_for_pipeline`，rewrite 与 hybrid 分支共用同一 `after_s2` 文本。
- **Stage3 输入口径**：old / fast_try 的 hybrid_ab 与 rewrite 的对比均以 **after_s2 的 true token 数为 before**，Stage3 后再计 after。

## 未与旧主线完全同构

- **v2_eval / marker accounting**：本脚本未走完整 `v2_eval` 流水线；未做与生产一致的 marker 级账本对齐。
- **hybrid_ab guardrail**：old / fast_try 路径调用了 `_apply_hybrid_ab_file_guardrail`；rewrite Stage3 为独立 orchestrator，**未**接入同一 guardrail 实现。
- **A/B 经济学**：rewrite 使用 `AChannelV1` / `BChannelV1` 的 net_true 门控与单候选接受规则；与 hybrid_ab 的 combo / 风险阈值等 **算法不同**，仅可比「同一 after_s2 上的启发式压缩量」，不可视为同一后端重复实验。

## Apples-to-apples（可信对比）

- **同一输入**：三条线均使用 **同一 `after_s2` 文本** 作为 Stage3 输入计量点。
- **同一 tokenizer**：`mc_encode` / true token 长度定义一致。
- **可比指标**：每个文件的 `before_true`（after_s2）与 Stage3 后的 `after_true` 差分，在脚本内汇总为语料级 delta。

## 非生产等价（诊断向对比）

- rewrite 未跑 **hybrid_ab guardrail**；old / fast_try 跑了。
- 未接入 **v2_eval / marker** 完整账本。
- **后端算法不同**：rewrite 为 AChannelV1/BChannelV1；hybrid_ab 为另一套 A/B 逻辑。

## 结论用法

- rewrite_200k 结果适合诊断 **rewrite 架构自身**（路由留存、A/B 门、span 命中率）。
- 与 old baseline 的「谁赢 token」在 **同一 after_s2 口径下**可比较趋势，但 **不宜称为生产链路等价 A/B**。
