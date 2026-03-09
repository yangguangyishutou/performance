# DC-PDD 简化版实现说明

## 概述

这是 DC-PDD (Detection via Confidence and PPL Drop) 的简化版实现，专门适配 AutoDL 环境和多语言代码数据集。

## 与原始 DC-PDD 的区别

| 方面 | 原始 DC-PDD | 简化版（本实现） |
|------|-------------|------------------|
| **参考模型** | 需要（如 pythia-70M） | ❌ 不需要 |
| **参考数据集** | 需要（C4，15GB+ 英文语料） | ✅ 其他语言代码（推荐） |
| **数据格式** | 特定 JSONL 格式 | ✅ 适配我们的格式 |
| **频率分布** | 外部数据集统计 | ✅ 从其他语言代码统计 |
| **三步流程** | com_pro_dis → com_fre_dis → com_det_sco | ✅ 一步完成 |
| **运行时间** | 数小时（含频率计算） | ✅ 数十分钟 |

### ⚠️ 重要：参考数据集选择

**原始 DC-PDD** 使用 C4 英文语料统计词频，但 C4 不适合代码数据：
- C4 是英文网页文本，token 分布与代码完全不同
- 代码有特定的语法关键字、函数名等

**本实现** 默认使用**其他语言代码**作为参考数据集：
- 评估 Java 代码时，用 C + JavaScript 代码统计词频
- 避免**数据泄露**（不使用评估数据本身统计词频）
- 更符合代码数据的特性

**如果不使用参考数据集**：
- 在评估数据本身上统计词频（原有行为）
- ⚠️ 会导致性能虚高（数据泄露）
- ⚠️ 不建议用于论文实验

## 核心算法

DC-PDD 的核心思想：**第一次出现的 token 携带更多信息**

```python
# 1. 只考虑第一次出现的 token（去重）
indexes = [i for i, id in enumerate(input_ids) if id not in current_ids]

# 2. 获取这些 token 的模型概率和频率
x_pro = probs[indexes]      # 模型对这些 token 的预测概率
x_fre = freq[indexes]      # 这些 token 在数据集中的频率

# 3. 计算频率感知交叉熵
ce = x_pro * log(1 / x_fre)

# 4. 截断极端值
ce[ce > a] = a  # a = 0.01

# 5. 最终分数（负号使得成员样本分数更低）
score = -mean(ce)
```

## 评估指标

本实现只计算核心 **DC-PDD** 方法：

| 指标 | 说明 | 与 MIA 关系 |
|------|------|-------------|
| `dcpdd` | DC-PDD 核心方法 | 首次出现 token 的频率感知交叉熵 |

**核心思想**：第一次出现的 token 携带更多信息，结合模型预测概率和数据集频率来检测成员样本。

> 注：其他 baseline 方法（loss/zlib/mink_0.2）由 `multi_language_run.py` 计算，DC-PDD 脚本专注于核心算法。

## 使用方法

### 方式 1: 单独运行 DC-PDD

**推荐：使用其他语言代码作为参考数据集**
```bash
python evaluation/run_dcpdd_autodl.py \
    --positive benchmark/data/positive/java_positive.jsonl \
    --negative benchmark/data/negative/java_negative.jsonl \
    --sample_size 20 \
    --model EleutherAI/pythia-2.8b \
    --half \
    --use_other_languages \
    --language java \
    --output results/dcpdd_java.csv
```

**不推荐：在评估数据上统计词频（性能虚高）**
```bash
python evaluation/run_dcpdd_autodl.py \
    --positive benchmark/data/positive/java_positive.jsonl \
    --negative benchmark/data/negative/java_negative.jsonl \
    --sample_size 20 \
    --model EleutherAI/pythia-2.8b \
    --half \
    --language java \
    --output results/dcpdd_java.csv
# ⚠️ 未提供参考数据集，将在评估数据上统计词频
```

**自定义参考数据集**
```bash
python evaluation/run_dcpdd_autodl.py \
    --positive benchmark/data/positive/java_positive.jsonl \
    --negative benchmark/data/negative/java_negative.jsonl \
    --sample_size 20 \
    --reference_data benchmark/data/reference/code_corpus.jsonl \
    --model EleutherAI/pythia-2.8b \
    --half \
    --language java
```

### 方式 2: 与 baseline 一起运行（自动使用其他语言）

```bash
python evaluation/evaluate_baseline.py \
    --languages java \
    --sample_size 20 \
    --half \
    --include_dcpdd
```

### 方式 3: 批量运行所有语言

```bash
# 使用脚本
bash run_dcpdd_all.sh

# 自定义参数
LANGUAGES=c,java,javascript SAMPLE_SIZE=100 MODEL=EleutherAI/pythia-2.8b bash run_dcpdd_all.sh
```

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--positive` | 正样本（成员）数据文件 | 必需 |
| `--negative` | 负样本（非成员）数据文件 | 必需 |
| `--sample_size` | 每类样本数量 | 20 |
| `--model` | 模型名称 | EleutherAI/pythia-2.8b |
| `--half` | 使用半精度（bfloat16） | 关闭 |
| `--max_length` | 最大文本长度 | 512 |
| `--field` | 数据集中的文本字段名 | function |
| `--a` | DC-PDD 截断参数 | 0.01 |
| `--output` | 输出文件路径 | results/dcpdd_results.csv |

## 输出格式

输出 CSV 文件包含 1 行（核心 DC-PDD 方法）：

| 列名 | 说明 |
|------|------|
| `method` | 固定值：dcpdd |
| `auroc` | ROC 曲线下面积 |
| `fpr95` | FPR@95（TPR=95% 时的 FPR） |
| `tpr05` | TPR@5（FPR=5% 时的 TPR） |

示例输出：
```csv
method,auroc,fpr95,tpr05
dcpdd,68.0%,80.0%,35.0%
```

## 性能预期

根据实验结果，DC-PDD 在代码数据集上的性能：

- **Java (20 样本)**: 68.0% AUROC
- **对比 SYNPRUNE**: DC-PDD 在某些数据集上可能优于 SYNPRUNE

## 工作流程

```
输入数据
   ↓
加载模型和分词器
   ↓
计算数据集上的 token 频率分布
   ↓
对每个样本：
   ├─ 计算模型概率分布
   ├─ 提取第一次出现的 token
   ├─ 计算 DC-PDD 分数
   └─ 计算其他 baseline 分数
   ↓
计算 AUROC 等指标
   ↓
保存结果
```

## 优势与限制

### 优势
- ✅ 不需要额外的参考模型
- ✅ 不需要外部参考数据集
- ✅ 运行速度快（数分钟 vs 数小时）
- ✅ 易于在 AutoDL 上部署

### 限制
- ⚠️ 从评估数据集计算频率，可能不如大规模语料准确
- ⚠️ 预期性能低于 SYNPRUNE

## 故障排除

### Q1: 频率分布计算慢
**解决**：减少 `--sample_size` 或 `--max_length`

### Q2: GPU 内存不足
**解决**：添加 `--half` 参数使用半精度

### Q3: DC-PDD 性能低于预期
**说明**：DC-PDD 在代码数据集上通常不如 SYNPRUNE，这是预期行为

## 参考文献

- [DC-PDD 论文](https://arxiv.org/abs/xxxx.xxxxx)
- [原始实现](https://github.com/zhang-wei-chao/DC-PDD)

# DC-PDD 优化说明

## 方案 C：混合所有负样本作为通用代码语料

### 核心改进

**问题**：之前 DC-PDD 在评估数据上统计词频，导致数据泄露和性能虚高。

**解决方案**：使用混合所有语言的负样本作为"通用代码语料"统计词频。

```python
# 收集所有负样本
all_negative = C_neg + Java_neg + JS_neg  # 3000 样本

# 计算全局词频
freq_dist = compute_frequency(all_negative)

# 评估每种语言
evaluate(C_pos + C_neg, freq_dist)
evaluate(Java_pos + Java_neg, freq_dist)
evaluate(JS_pos + JS_neg, freq_dist)
```

### 优势

1. **避免数据泄露**：统计时不使用正样本
2. **符合 MIA 假设**：非成员代表"从分布中采样"
3. **包含所有 tokens**：每种语言的 tokens 都有覆盖
4. **词频更稳定**：3000 样本 vs 1000 样本

### 预期性能

| 方法 | AUROC | 说明 |
|------|-------|------|
| SYNPRUNE | ~63% | 基准方法 |
| DC-PDD (旧) | ~68% | 数据泄露，虚高 |
| DC-PDD (新) | ~55-60% | 方案 C，更可靠 |

---

## 模型加载优化

### 问题

旧实现每个语言都会加载两次模型：
```python
for model in models:
    for lang in languages:
        load_model() → baseline  # 加载 1 次
        load_model() → dcpdd     # 又加载 1 次！
```

### 解决方案

新实现每个模型只加载一次：
```python
for model in models:
    load_model()  # 只加载 1 次
    compute_global_freq()  # 计算全局词频

    for lang in languages:
        baseline(model)   # 使用已加载的模型
        dcpdd(model)      # 使用已加载的模型
```

### 性能提升

- **节省时间**：4 种语言 × 4 个模型 = 少加载 16 次模型
- **节省内存**：避免重复加载模型权重
- **更稳定**：模型加载是失败高发操作，减少加载次数提高稳定性

---

## 使用方法

### 新脚本：evaluate_baseline_optimized.py

**特点**：
- 模型只加载一次
- DC-PDD 使用方案 C（混合负样本）
- baseline 和 DC-PDD 共享模型实例

**用法**：
```bash
# 单模型 + baseline
python evaluation/evaluate_baseline_optimized.py \
    --languages java \
    --sample_size 20 \
    --models pythia-2.8b \
    --half

# 多模型 + baseline + DC-PDD
python evaluation/evaluate_baseline_optimized.py \
    --languages c,java,javascript \
    --sample_size 100 \
    --models pythia-2.8b,gpt-neo-2.7b,stablelm-3b \
    --half \
    --include_dcpdd
```

### 旧脚本：evaluate_baseline.py

**保留用于**：
- 快速单语言测试
- 不需要 DC-PDD 的场景

**仍然可用**，但效率较低（每个语言加载两次模型）。

---

## 文件说明

### 新增文件

1. **src/dcpdd_evaluator.py**
   - DC-PDD 评估模块
   - 提供 `compute_global_token_frequency()` 和 `evaluate_dcpdd_on_dataset()`
   - 可导入使用

2. **evaluation/evaluate_baseline_optimized.py**
   - 优化版评估脚本
   - 模型只加载一次
   - DC-PDD 使用方案 C

### 修改文件

- **DC-PDD_README.md**：更新说明方案 C

### 保留文件

- **evaluation/run_dcpdd_autodl.py**：独立 DC-PDD 脚本（仍可单独使用）
- **evaluation/evaluate_baseline.py**：旧版评估脚本（仍可用）

---

## 迁移指南

### 从旧脚本迁移

**旧方式**（每个语言加载 2 次模型）：
```bash
python evaluation/evaluate_baseline.py \
    --languages c,java,javascript \
    --sample_size 100 \
    --models pythia-2.8b \
    --half \
    --include_dcpdd
```

**新方式**（每个模型只加载 1 次）：
```bash
python evaluation/evaluate_baseline_optimized.py \
    --languages c,java,javascript \
    --sample_size 100 \
    --models pythia-2.8b \
    --half \
    --include_dcpdd
```

### 参数对照

| 旧脚本参数 | 新脚本参数 | 说明 |
|-----------|-----------|------|
| `--languages` | `--languages` | 相同 |
| `--sample_size` | `--sample_size` | 相同 |
| `--model` | `--model` | 相同 |
| `--models` | `--models` | 相同 |
| `--half` | `--half` | 相同 |
| `--include_dcpdd` | `--include_dcpdd` | 相同 |
| N/A | `--max_length` | 新增：最大序列长度 |

---

## 实验流程建议

### 快速验证（20 样本）
```bash
python evaluation/evaluate_baseline_optimized.py \
    --languages java \
    --sample_size 20 \
    --models pythia-2.8b \
    --half \
    --include_dcpdd
```

### 完整实验（1000 样本，4 个模型）
```bash
python evaluation/evaluate_baseline_optimized.py \
    --languages c,java,javascript \
    --sample_size 1000 \
    --models pythia-2.8b,gpt-neo-2.7b,stablelm-3b,gpt-j-6b \
    --half \
    --include_dcpdd
```

**预计时间**：
- 单模型 3 语言（1000 样本）：~3 小时
- 4 模型 3 语言（1000 样本）：~12 小时
- vGPU-32GB 成本：~6-12 元
