# 脚本使用说明

## 快速导航

### 🌟 推荐使用（总控脚本）

**[evaluation/evaluate_baseline_optimized.py](../evaluation/evaluate_baseline_optimized.py)**
- 所有方法（loss, zlib, mink_0.2, synprune, dcpdd）
- 模型只加载一次
- DC-PDD 使用方案 C（混合所有负样本）
- 支持多语言、多模型批量评估

```bash
# 单模型 + baseline + DC-PDD
python evaluation/evaluate_baseline_optimized.py \
    --languages java \
    --sample_size 1000 \
    --models pythia-2.8b \
    --half \
    --include_dcpdd

# 多模型 + 所有语言
python evaluation/evaluate_baseline_optimized.py \
    --languages c,java,javascript \
    --sample_size 1000 \
    --models pythia-2.8b,gpt-neo-2.7b,stablelm-3b \
    --half \
    --include_dcpdd
```

---

### 单独运行脚本

#### Baseline 方法

**[src/run_baseline.py](src/run_baseline.py)**
- 方法：loss, zlib, mink_0.2, synprune
- 单语言评估

```bash
python src/run_baseline.py \
    --language java \
    --sample_size 1000 \
    --model EleutherAI/pythia-2.8b \
    --half \
    --output results
```

#### DC-PDD 方法

**[src/run_dcpdd.py](src/run_dcpdd.py)**
- 方法：dcpdd
- 使用方案 C（混合所有负样本作为通用代码语料）

```bash
# 默认：混合所有语言负样本
python src/run_dcpdd.py \
    --language java \
    --sample_size 1000 \
    --model EleutherAI/pythia-2.8b \
    --half \
    --output results

# 只用当前语言负样本
python src/run_dcpdd.py \
    --language java \
    --sample_size 1000 \
    --only_current_lang \
    --half

# 自定义参考数据集
python src/run_dcpdd.py \
    --language java \
    --sample_size 1000 \
    --reference_data data/reference_corpus.jsonl \
    --half
```

---

## 方法对比

| 脚本 | 适用场景 | 模型加载次数 | DC-PDD 方案 |
|------|---------|-------------|------------|
| **evaluate_baseline_optimized.py** | 完整实验（推荐） | 1次/模型 | 方案 C |
| **src/run_baseline.py** | 单独运行 baseline | 1次 | - |
| **src/run_dcpdd.py** | 单独运行 DC-PDD | 1次 | 方案 C |

---

## DC-PDD 方案 C 说明

**方案 C：混合所有负样本作为通用代码语料**

```python
# 词频统计
all_negative = C_neg + Java_neg + JS_neg  # 3000 样本
freq_dist = compute_frequency(all_negative)

# 评估
evaluate(Java_pos + Java_neg, freq_dist)  # Java_neg 在词频中
evaluate(C_pos + C_neg, freq_dist)        # C_neg 在词频中
```

**优势**：
- ✅ 避免数据泄露（不使用正样本统计词频）
- ✅ 包含所有语言的 tokens
- ✅ 词频更稳定（3000 vs 1000 样本）
- ✅ 符合 MIA 假设（非成员代表分布）

**预期性能**：
- DC-PDD AUROC：55-60%
- SYNPRUNE AUROC：63%

---

## 常见用法

### 快速测试（20 样本）

```bash
# Baseline
python src/run_baseline.py --language java --sample_size 20 --half

# DC-PDD
python src/run_dcpdd.py --language java --sample_size 20 --half
```

### 完整实验（1000 样本）

```bash
# 使用总控脚本（推荐）
python evaluation/evaluate_baseline_optimized.py \
    --languages c,java,javascript \
    --sample_size 1000 \
    --models pythia-2.8b \
    --half \
    --include_dcpdd
```

### 多模型对比

```bash
python evaluation/evaluate_baseline_optimized.py \
    --languages java \
    --sample_size 1000 \
    --models pythia-2.8b,gpt-neo-2.7b,stablelm-3b,gpt-j-6b \
    --half \
    --include_dcpdd
```

---

## 参数说明

### 通用参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--language` | 语言名称 (c/java/javascript) | 必需 |
| `--sample_size` | 每类样本数量 | 20 |
| `--model` | 模型名称 | EleutherAI/pythia-2.8b |
| `--half` | 使用 bfloat16 | 关闭 |
| `--output` | 输出目录 | results |

### evaluate_baseline_optimized.py 额外参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--languages` | 逗号分隔的语言列表 | c,java,javascript |
| `--models` | 逗号分隔的模型列表 | pythia-2.8b,gpt-neo-2.7b,stablelm-3b,gpt-j-6b |
| `--include_dcpdd` | 包含 DC-PDD 方法 | 关闭 |

### run_dcpdd.py 额外参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--reference_data` | 自定义参考数据集路径 | - |
| `--only_current_lang` | 只用当前语言负样本 | 关闭 |
| `--a` | DC-PDD 截断参数 | 0.01 |

---

## 输出格式

所有脚本输出相同格式的 CSV 文件：

```csv
language,method,auroc,fpr95,tpr05
java,loss,38.4%,97.2%,3.2%
java,zlib,33.2%,98.6%,1.6%
java,mink_0.2,38.8%,97.7%,2.5%
java,synprune,63.0%,88.3%,19.0%
java,dcpdd,57.5%,85.0%,15.0%
```

---

## 故障排除

### GPU 内存不足

```bash
# 添加 --half 参数
python src/run_baseline.py --language java --sample_size 1000 --half

# 或减少样本数
python src/run_baseline.py --language java --sample_size 100 --half
```

### 磁盘空间不足（GPT-J 6B）

GPT-J 6B 需要 24GB 空间，代码会自动尝试以下缓存位置：
1. `/root/autodl-tmp/huggingface_cache`
2. `/root/autodl-fs/huggingface_cache`
3. `/tmp/huggingface_cache`

如果都失败，请清理磁盘空间。

### Tree-sitter 解析器错误

确保已安装 tree-sitter 和语言语法包：
```bash
pip install tree-sitter
pip install tree-sitter-c tree-sitter-java tree-sitter-javascript
```

---

## 文件结构

```
ML_SYNPRUNE/
├── evaluation/
│   ├── evaluate_baseline_optimized.py  # ⭐ 总控脚本
│   ├── ablate.py                      # Python 消融实验
│   ├── visualization.py               # 结果可视化
│   └── visualize_syntax_parsing.py    # HTML 可视化
│
├── src/
│   ├── run_baseline.py                # 单独运行 baseline
│   ├── run_dcpdd.py                   # 单独运行 DC-PDD（方案 C）
│   ├── multi_language_run.py          # baseline 评估模块
│   ├── dcpdd_evaluator.py             # DC-PDD 评估模块
│   └── syntax_parser.py               # 语法解析器
│
└── docs/
    └── SCRIPT_REFERENCE.md            # 本文档
```
