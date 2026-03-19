# entropy_tokenizer_v2 — 动态 Per-Repo 压缩框架

> **目标**：在信息论框架下，通过集成三种互补的有损/无损压缩手段，对 Python 代码进行极致的 token 数量压缩，以降低 LLM 的 context 成本。  
> v2 与 v1 / SimPy 完全独立，不共享任何模块。

---

## 核心思想："动态" × "多层集成"

| 维度 | v1 / SimPy | v2（本框架） |
|------|-----------|------------|
| 规则来源 | 固定规则集（SimPy 104条）/ 跨数据集统一挖掘 | **按仓库动态挖掘**，每个项目专属一套规则 |
| 压缩粒度 | 句式结构（词汇层） | 句式 + 冗余符号 + 标识符/字面量（三层叠加） |
| 有损能力 | 无损为主 | **显式有损**（缩进、docstring 可删除） |
| 句式压缩策略 | 仅替换固定部分，保留关键字 | **整体替换**（含关键字全部压入算子 token） |

---

## 三阶段压缩流水线

```
原始 Python 代码
       │
       ▼  Stage 1 ── 句式压缩（syntax_compressor.py）
       │   AST 解析 → 提取句式骨架 → MDL 选出 K* 个最划算的句式
       │   每个选中句式的 header 被整体替换为 <SYN_N> + 槽值
       │
       ▼  Stage 2 ── 有损清除（lossy_cleaner.py）
       │   R01 删除行注释（无损）
       │   R02 删除空白行（无损）
       │   R03 删除行尾空格（无损）
       │   R05 删除 docstring（有损）
       │   R04 删除所有缩进（有损，代码不再可解析）
       │
       ▼  Stage 3 ── Token 重要性替换（token_scorer.py）
       │   统计语料词频 → 计算 Score(w) → 选出高分 token
       │   高分 token 按类别替换为占位符
       │
       ▼
  压缩后 token 序列（用于 LLM 预训练 / context 压缩）
```

---

## Stage 1 详解：数据驱动句式压缩

### 句式骨架（Skeleton）

用 Python AST 将语句的变量部分匿名化，提取出结构模板：

```python
# 原始代码
with open(filepath, 'r', encoding='utf-8') as file_handle:

# 对应骨架（pattern key）
"with {0}({1}, {2}, encoding={3}) as {4}:"
```

骨架中 `{N}` 是槽位（slot），对应原始代码中的可变表达式。

### 整体替换（v2 vs v1 的关键差异）

```
原始:    with open(filepath, 'r', encoding='utf-8') as file_handle:
v1结果:  <OP_K> open(filepath, 'r', encoding='utf-8') as file_handle:  ← 只压 "with...:" 固定部分
v2结果:  <SYN_0> open(filepath, 'r', encoding='utf-8') file_handle     ← 关键字 with / as / : 全部吸收进算子
```

v2 中 `with`、`as`、`:` 这些关键字 token 被完全吸收进 `<SYN_0>`，槽值直接跟在算子后面。

### MDL 选择（Minimum Description Length）

贪心前向选择，满足以下条件才接受一个骨架：

```
ΔL_k = N_new · log₂(V₀+k) − N_curr · log₂(V₀+k−1) + cb_k · log₂(V₀) < 0
```

- `N_curr` → 当前压缩后 token 总数
- `cb_k = MDL_CODEBOOK_OVERHEAD`（描述算子本身的成本）
- `V₀` → 基础词表大小（GPT-4: 100,277）

**每个算子的实际收益**（demo 实测）：

| 算子 | 骨架 | spi | freq | MDL净收益 |
|------|------|-----|------|---------|
| SYN_0 | `with {0}({1}, {2}, encoding={3}) as {4}:` | 8 | 2 | 14 |
| SYN_1 | `{0} = {1}.get({2}, {3})` | 5 | 2 | 8 |
| SYN_2 | `{0} = {1}.path.join({2}, f'...')` | 9 | 1 | 7 |
| SYN_3 | `for {0} in {1}.listdir({2}.input_dir):` | 9 | 1 | 7 |

> spi = savings per instance（每次出现节省的 token 数）

### 算子码本（Codebook）

**算子编号与骨架的对应关系存储在 `cache/repo_config_<tok>_<name>.json`**，字段 `selected_skeletons`，**索引 N 对应 `<SYN_N>`**。

```json
"selected_skeletons": [
  {"skeleton": "with {0}({1}, {2}, encoding={3}) as {4}:", ...},   ← SYN_0
  {"skeleton": "{0} = {1}.get({2}, {3})", ...},                    ← SYN_1
  ...
]
```

---

## Stage 3 详解：Token 重要性评分

### Score 公式

$$\text{Score}(w) = \frac{\Delta T(w)}{\Delta I(w) + \varepsilon}$$

| 符号 | 含义 | 计算方式 |
|------|------|---------|
| $\Delta T(w)$ | 将 $w$ 单 token 化后节省的 subtoken 数 × 出现频次 | $(spt(w)-1) \times freq(w)$ |
| $\Delta I(w)$ | 自信息（越罕见越大，表示信息量越高） | $-\log_2 p(w)$ |
| $\varepsilon$ | 平滑常数，防止除零 | 0.01 |

**Score 高** → 高频 + 低自信息 → 值得替换（省得多，损失少）  
**Score 低** → 低频 + 高自信息 → 保留（该 token 语义独特）

### 类别占位符

| 占位符 | 替换对象 | 示例 |
|--------|---------|------|
| `<VAR>` | 普通变量名（高分） | `DEFAULT_OUTPUT_DIR` → `<VAR>` |
| `<ATTR>` | 属性名（出现在 `.` 右侧） | `output_dir` → `<ATTR>` |
| `<STR>` | 字符串字面量 | `"utf-8"` → `<STR>` |
| `<FSTR>` | f-string 字面量 | `f"hello {name}"` → `<FSTR>` |
| `<NUM>` | 数值字面量 | `3.14` → `<NUM>` |

**受保护（永不替换）**：Python 关键字、内置函数（`len`/`print` 等）、`self`/`cls`/`args`/`kwargs`

### demo 实测替换表

```
'DEFAULT_OUTPUT_DIR'  → <VAR>
'load_json_file'      → <VAR>
'"utf-8"'             → <STR>
'output_dir'          → <ATTR>
'input_dir'           → <ATTR>
'output_path'         → <ATTR>
...（共 10 个词）
```

---

## Token 计数修正（增广词表模拟）

`<SYN_N>` / `<VAR>` / `<ATTR>` 等占位符是**新增词表项**，在基础 tokenizer 中会被拆成多个 subtoken（如 `<SYN_0>` → `<` / `SYN` / `_` / `0` / `>`）。

v2 评估时用 `_count_with_ops()` 修正此误差：

```python
total_tokens = tokenize(text_without_markers) + count(markers)
# 每个 marker 模拟为 1 个新词表 token
```

---

## Demo 实测结果（玩具代码，GPT-4 tokenizer）

```
原始代码：2166 chars，469 tokens（含 docstring / 注释 / 缩进）

  Stage 1（句式压缩）：469 → 410    省 59 tokens   (12.6%)
  Stage 2（有损清除）：410 → 327    省 83 tokens   (17.7%)
  Stage 3（token替换）：327 → 314   省 13 tokens   ( 2.8%)
  ─────────────────────────────────────────────────────
  总压缩             ：469 → 314    省 155 tokens  (33.0%)
```

**参数**：MDL K\* = 26 个句式算子，10 个 token 替换，V₀ = 100,277

> SimPy（v1 对比）：GPT-4 tokenizer 上报告压缩率 **10.4%**（无损，仅句式层）

---

## 动态性（Per-Repo）

每个仓库单独走一遍挖掘流程，产出**专属的** `RepoConfig`：

```
repo_miner.mine_from_repo_path("/path/to/my_project", tok_key, cfg)
         ↓
cache/repo_config_gpt4_my_project.json
         ↓
apply_v2_compression(source, repo_config, tokenizer)
```

同一代码在不同仓库下得到不同的算子集合，压缩规则贴合该项目的真实语料分布。

---

## 文件结构

```
entropy_tokenizer_v2/
├── config_v2.py          # 全局配置（路径 / 参数 / tokenizer 列表）
├── lossy_cleaner.py      # Stage 2：有损/无损清除（R01-R05）
├── token_scorer.py       # Stage 3：Score(w) 计算 + 类别占位替换
├── syntax_compressor.py  # Stage 1：AST 骨架提取 + MDL 选择 + 整体替换
├── repo_miner.py         # 按仓库动态挖掘，串联三个 Stage
├── v2_eval.py            # 评估流水线：分阶段指标 + CSV/JSON 输出
├── run_v2.py             # CLI 入口
├── cache/                # 挖掘结果缓存（RepoConfig JSON）
└── results/              # 评估报告（CSV + JSON）
```

---

## 使用方法

```bash
# 玩具代码 demo（快速验证）
python run_v2.py demo --tokenizer gpt4

# 指定本地文件
python run_v2.py demo --file path/to/script.py --tokenizer gpt4

# 评估一个本地仓库
python run_v2.py eval --repo /path/to/project --tokenizer gpt4

# 评估 HF 数据集（需网络 + HF token）
python run_v2.py eval --samples 200 --tokenizers gpt4 santacoder
```

---

## 设计取舍说明

| 点 | 当前选择 | 备注 |
|----|---------|------|
| 有损/无损 | 显式有损（缩进 / docstring 删除） | 仅适合表示/检索任务，不适合代码生成 |
| 槽值边界 | 空格分隔，无显式边界标记 | 若需精确解压缩可加 `<SEP>` token |
| 高分 token 替换范围 | 包括槽值位置 | 若要保护槽值语义，可在 mining 阶段排除 slot_token_set |
| 动态粒度 | 按仓库 | 不做在线更新，挖掘一次缓存复用 |
| 信息量度量 | 自信息 $I(w) = -\log_2 p(w)$（词频统计） | 后续可用掩码实验校正 |
