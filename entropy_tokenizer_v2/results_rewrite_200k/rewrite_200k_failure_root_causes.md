# rewrite_200k 失败根因报告（自动生成）

基于本次 `eval_stage3ab_rewrite_200k.py` 全量重跑结果。

## 1. A diagnostics 覆盖率

- **sources**: 132
- **A 输入非空** (`a_text_nonempty`): 132
- **parse_ok=True**（整文件 probe 跑通）: 4
- **parse_ok=False**: 128
- **其中 AST 解析失败** (`ast_parse_failed`): 128
- **parse_ok 占全文件比例**: 3.03%

**说明**：A 诊断优先使用 `run_extras["text_for_a_parse_safe"]`（与运行时 A 通道输入一致：B 后 re-route，必要时对待删 span 做空格 mask）。若仍 `parse_ok=False`，多为 mask 后仍不合法或残余语法问题，而非 eval 与 `after_route_clean_snapshot` 的简单接线错误。

## 2. A 通道（语料计数来自 a_diagnostics 行求和）

| 指标 | 值 |
|------|-----|
| a_candidates_total | 1 |
| a_candidates_variable | 0 |
| a_candidates_attribute | 1 |
| a_candidates_string_exact_path | 0 |
| filtered_short_name | 18 |
| filtered_attr_depth | 0 |
| no_legal_alias | 0 |
| no_net_true_gain | 1 |
| gross_pos_net_neg | 1 |
| accepted | 0 |

**属性后缀 occ（仅 len≥min 默认10）按深度上限**：见 `rewrite_200k_a_attr_depth_hist.csv`。  
**short_name 被挡 Top50**：`rewrite_200k_short_name_filtered_top50.csv`。

## 3. B 通道

- **insufficient_members（簇级 telemetry）**: 0（见 `rewrite_200k_b_singleton_stats.csv`）
- **说明**：若此项为 0，通常 **不代表「没有单条长文本」**——多数单条字符串在聚类阶段为 **HDBSCAN 噪声**，**根本不会形成簇**，因此不会调用 `evaluate_cluster`，也就不会出现 `insufficient_members` 事件。单测里的 singleton 是 **显式单簇** 路径，与真语料不同。
- **rejected_for_low_quality**: 2（见 `rewrite_200k_b_low_quality_stats.csv`）
- **rejected_for_no_net_gain**: 3
- **intro / 簇规模**: `rewrite_200k_b_intro_breakdown.csv`
- **span**: `rewrite_200k_b_span_stats.md`

## 4. Route

- 分桶 CSV: `rewrite_200k_route_asset_breakdown.csv`
- 与 summary 中 `route_initial__*` 一致可对读

## 5. 与 old / fast_try 语料级 delta（true token 求和）

| 路径 | delta |
|------|-------|
| old | 3725 |
| fast_try | 3465 |
| rewrite | -45 |

## 6. 根因 Top 3（结合本次数字）

1. **A 语法层**：优先诊断 `text_for_a_parse_safe`（B 后、destructive 前；必要时 mask）。若 `ast.parse` 仍失败，多为 mask 后仍不合法或残余语法问题。
2. **A 经济与规模（在可解析子集上）**：语料行求和 `a_candidates_total`=1，且 `no_net_true_gain`=1。
3. **语料级 delta**：rewrite Δ=-45 vs old Δ=3725；路由使用 `RoutePolicy.rewrite_recovery_v2()`（更多 NL 进 B）；B span 统计见 `rewrite_200k_b_diagnostics.csv`（含 `span_hits_literal_equiv`）。

## 7. 评测口径

见 `rewrite_200k_accounting_gap.md`（同脚本生成）。

---
*提交/分支请以当前仓库为准；本文件仅描述本地一次 eval 结果。*
