# 半自动化语法约束提取工作流

## 概述

本工作流从编程语言官方文档（PDF）中提取**语法约束对**，用于 token 级别的语法合规性检测。

**语法约束对**定义为：给定一个 token 序列前缀（conditional），下一个合法 token 的集合（consequent）。例如：

```
if → (          # if 关键字后必须跟左括号
if ( → )        # 左括号后必须跟右括号（跳过条件表达式）
if () → {, <statement_start>
```

工作流支持 JavaScript、C、Java 三种语言，已提取结果：

| 语言 | 输入文档 | 语法构造数 | 有效约束对 |
|------|---------|-----------|-----------|
| JavaScript | MDN Web Docs | 71 | 628 |
| C | ISO/IEC 9899:2024 Annex A | 85 | 234 |
| Java | JLS Java SE 24 Syntax | 173 | 507 |

---

## 工作流架构

```
官方文档 (PDF)
      │
      ▼
┌─────────────────────────────┐
│  Step 0: 文档预处理          │  脚本：0_preprocess_pdf.py
│  PDF → BNF 规则索引          │        1_collect_docs.py (JS)
└─────────────────────────────┘
      │  {language}_index.json
      ▼
┌─────────────────────────────┐
│  Step 1: LLM 批量提取        │  脚本：2_extract_constraints.py
│  BNF 规则 → 约束对 (JSON)    │  模型：DeepSeek-V3 / Claude Sonnet
└─────────────────────────────┘
      │  extracted/*.json
      ▼
┌─────────────────────────────┐
│  Step 2: 过滤与合并          │  脚本：3_consolidate.py
│  过滤空约束 + 验证格式        │
└─────────────────────────────┘
      │
      ▼
  constraints.json
```

---

## 目录结构

```
{language}/
  ├── docs/                    # 原始文档（PDF + 章节 txt）
  ├── extracted/               # LLM 原始提取（中间产物）
  ├── {language}_index.json    # 构造索引
  └── constraints.json         # 最终输出
```

---

## 运行步骤

### Step 0: 文档预处理

**C / Java（从 PDF 提取 BNF 章节）：**

先用 `pdftotext` 将 PDF 转为章节 txt（已完成，存放在 `{language}/docs/`），再解析成构造索引：

```bash
python scripts/0_preprocess_pdf.py --language c
python scripts/0_preprocess_pdf.py --language java
```

输出：`{language}/{language}_index.json`

**JavaScript（从 MDN 抓取文档）：**

```bash
python scripts/1_collect_docs.py --language javascript
```

输出：`javascript/javascript_index.json`

---

### Step 1: LLM 批量提取

配置 LLM 服务（修改 `config.yaml` 中的 `active` 字段切换服务）：

```yaml
active: deepseek  # 或 anthropic
```

```bash
# 设置 API Key
export DEEPSEEK_API_KEY='your-key'       # DeepSeek
export ANTHROPIC_API_KEY='your-key'      # Claude

# 批量提取（batch-size=10 约节省 90% API 调用）
python scripts/2_extract_constraints.py --language javascript --batch-size 10
python scripts/2_extract_constraints.py --language c --batch-size 10
python scripts/2_extract_constraints.py --language java --batch-size 10
```

输出：`{language}/extracted/*.json`（每个构造一个文件）

支持断点续传：中断后重新运行同一命令自动从 checkpoint 继续。

---

### Step 2: 过滤与合并

```bash
python scripts/3_consolidate.py --language javascript
python scripts/3_consolidate.py --language c
python scripts/3_consolidate.py --language java
```

自动执行：
1. 过滤空约束（无条件-结果关系的构造）
2. 验证约束格式（括号匹配、抽象占位符检查）
3. 合并为单一输出文件

输出：`{language}/constraints.json`

---

## 输出格式

```json
{
  "language": "c",
  "total_constructs": 85,
  "total_constraints": 234,
  "constructs": [
    {
      "construct": "selection-statement",
      "language": "c",
      "syntax_node": "if",
      "constraints": [
        {
          "conditional": "if",
          "consequent": "(",
          "skip": "",
          "required": true,
          "note": "if 关键字后必须跟左括号"
        },
        {
          "conditional": "if (",
          "consequent": ")",
          "skip": "expression",
          "required": true,
          "note": "左括号后必须跟右括号（中间跳过条件表达式）"
        }
      ]
    }
  ]
}
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `conditional` | token 序列前缀（累积的已见 token） |
| `consequent` | 下一步合法的 token 集合（逗号分隔） |
| `skip` | 中间可跳过的抽象节点类型（如 `expression`） |
| `required` | 是否为强制约束 |
| `note` | 人类可读说明 |

### 特殊标记

| 标记 | 含义 |
|------|------|
| `[IDENT]` | 任意标识符 |
| `[STRING]` | 任意字符串字面量 |
| `[PROPERTY]` | 对象属性名占位符 |
| `<expression_start>` | 表达式起始 token 集合 |
| `<statement_start>` | 语句起始 token 集合 |

---

## Prompt 设计

提取使用 `prompts/base_prompt_cn_v4.0.txt`，核心方法为**原子分解**：

将语法结构分解为最小的、连续的匹配步骤，每个步骤的 conditional 是累积的 token 前缀。

跳过规则：
- 纯词法规则（identifier、digit 等枚举）
- 高熵二元运算符（`+`, `-`, `*`, `/` 等）
- 纯选择规则（无关键字约束的 alternatives）
