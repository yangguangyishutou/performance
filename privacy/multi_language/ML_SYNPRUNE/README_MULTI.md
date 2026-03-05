# 多语言成员推断攻击 (Multi-Language Membership Inference Attack)

## 项目概述

本项目在原有的 Python-only SYNPRUNE 基础上，扩展支持多种编程语言（C、Java、JavaScript），使用 **Tree-sitter** 实现语言无关的语法解析，通过**两层分类**过滤掉语法约束的 Token，提高成员推断攻击的准确性。

## 核心创新

### 两层分类法 (Two-Layer Classification)

**第 1 层 - 结构检查**（使用 Tree-sitter）：
- `is_named == True` → **保留**（标识符、字面量、业务逻辑）
- `is_named == False` → 进入第 2 层判断

**第 2 层 - 词法特征检查**（使用 Unicode 分类）：
- 字母/数字（关键字、标识符）→ **保留**
- 操作符（+, -, ==, →, ::）→ **保留**
- 定界符（(, ), {, }, ;, ,）→ **剪枝**

这样可以过滤掉约 38.4% 的语法约束 Token，这些 Token 会稀释归属信号。

## 项目结构

```
ML_SYNPRUNE/
├── src/
│   ├── run.py                        # 原有 Python 实现（保留作为参考）
│   ├── syntax_parser.py              # 新增：Tree-sitter 两层分类解析器
│   └── multi_language_run.py         # 新增：多语言评估脚本
├── evaluation/
│   ├── ablate.py                     # 保留：Python 消融实验
│   ├── evaluate_baseline.py          # 新增：Baseline 复现脚本
│   └── visualize_syntax_parsing.py   # 新增：HTML 可视化生成器
├── benchmark/
│   └── data/
│       ├── positive/                 # 成员样本（来自 ThePile）
│       └── negative/                 # 非成员样本（来自 GitHub 2024+）
├── autodl_run.sh                     # AutoDL 运行脚本
├── README_AUTODL.md                  # AutoDL 部署指南
├── requirements_multi.txt            # 多语言依赖
└── README_MULTI.md                   # 本文件
```

## 快速开始

### 1. 环境配置

**本地开发环境**（无需 GPU）：
```bash
# 安装依赖
pip install -r requirements_multi.txt

# 安装 Tree-sitter 和语言语法
pip install tree-sitter
pip install tree-sitter-c tree-sitter-java tree-sitter-javascript
```

**AutoDL GPU 服务器**（运行模型实验）：
```bash
# 参见 README_AUTODL.md 获取详细说明
bash autodl_run.sh
```

### 2. 本地测试语法解析器

```bash
# 测试 C 语言解析器
python src/syntax_parser.py c benchmark/data/positive/c_positive.jsonl

# 生成 HTML 可视化（推荐）
python evaluation/visualize_syntax_parsing.py \
    --language c \
    --input benchmark/data/positive/c_positive.jsonl \
    --num_samples 5 \
    --output syntax_visualization_c.html
```

在浏览器中打开生成的 HTML 文件，查看两层分类的可视化结果。

### 3. 运行 Baseline 实验

**本地小规模测试**（需要 GPU）：
```bash
# C 语言（10 样本）
python src/multi_language_run.py \
    --dataset c \
    --sample_size 10 \
    --half \
    --output results/c_test.csv

# 所有语言
python evaluation/evaluate_baseline.py \
    --languages c,java,javascript \
    --sample_size 20 \
    --half
```

**AutoDL 完整实验**：
```bash
# 登录 AutoDL 后
bash autodl_run.sh
```

### 4. 运行 DC-PDD 对比实验（可选）

为了更全面的对比，我们还支持 DC-PDD 方法的三种指标。

**一键运行完整流程**：
```bash
# 准备数据 + 运行我们的 4 种方法
bash run_dcpdd_pipeline.sh

# 然后按照提示手动运行 DC-PDD（见 DC_PDD_GUIDE.md）
```

**详细步骤**参见：[DC_PDD_GUIDE.md](DC_PDD_GUIDE.md)

DC-PDD 提供额外的 3 种指标：
- `program_discrepancy` - 程序差异度
- `frequency_discrepancy` - 频率差异度
- `detection_score` - 检测分数

最终对比 **7 种方法**：
| 类别 | 方法 |
|------|------|
| 我们的方法 | loss, zlib, mink_0.2, **synprune** |
| DC-PDD | program_discrepancy, frequency_discrepancy, detection_score |

## 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `src/syntax_parser.py` | Tree-sitter 两层分类解析器。核心算法实现。 |
| `src/multi_language_run.py` | 多语言评估脚本。替代原有的 `run.py`。 |
| `evaluation/visualize_syntax_parsing.py` | HTML 可视化生成器。展示分类过程。 |
| `evaluation/evaluate_baseline.py` | Baseline 复现脚本。批量运行实验。 |

### 部署文件

| 文件 | 说明 |
|------|------|
| `autodl_run.sh` | AutoDL 一键运行脚本 |
| `README_AUTODL.md` | AutoDL 详细部署指南 |

### 数据集

| 路径 | 说明 |
|------|------|
| `benchmark/data/positive/{lang}_positive.jsonl` | 成员样本（1000 个/语言） |
| `benchmark/data/negative/{lang}_negative.jsonl` | 非成员样本（1100 个/语言） |

## 实验流程

### 阶段 1：本地验证（无需 GPU）

1. 测试语法解析器
2. 生成 HTML 可视化
3. 验证两层分类逻辑正确性

### 阶段 2：小规模实验（需要 GPU）

在 AutoDL 上运行 20 样本/语言的快速测试，验证：
- 模型能正常运行
- synprune 优于 baseline 方法
- 跨语言性能一致

### 阶段 3：完整实验

在 AutoDL 上运行 1000 样本/语言的完整实验，生成论文级别的结果。

## 预期结果

在 Pythia-2.8B 模型上，预期看到：

```
        method  auroc  fpr95  tpr05
0      loss  38-40%  ~97%    ~3%
1      zlib  33-35%  ~98%    ~1%
2  mink_0.2  38-40%  ~97%    ~2%
3  synprune  60-65%  ~88%   ~19%
```

synprune 应该显著优于其他三种 baseline 方法（AUROC 提升 20-30%）。

## 与原 Python 版本的对比

| 方面 | 原版本 | 新版本 |
|------|--------|--------|
| 语言 | Python only | C, Java, JavaScript |
| 语法解析 | Python AST | Tree-sitter |
| 约束字典 | 手动维护 | 自动解析 |
| 扩展性 | 需手动编码 | 统一 API |

## 下一步工作

1. 完成小规模验证（20 样本）
2. 在 AutoDL 上运行完整实验
3. 分析跨语言性能差异
4. 扩展到更多语言（Rust, Go 等）

## 参考资料

- 原论文：[Uncovering Pretraining Code in LLMs: A Syntax-Aware Attribution Approach](https://arxiv.org/pdf/2511.07033)
- Tree-sitter：[GitHub](https://github.com/tree-sitter/tree-sitter)
- AutoDL：[官网](https://www.autodl.com/)

## 问题反馈

如果遇到问题，请检查：
1. Tree-sitter 和语言语法包是否正确安装
2. 数据集路径是否正确
3. GPU 内存是否足够（降低 `--max_length` 或 `--sample_size`）

对于 AutoDL 相关问题，请参考 `README_AUTODL.md`。
