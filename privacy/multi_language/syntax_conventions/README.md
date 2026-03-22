# 多语言语法约束提取

半自动化工作流，从编程语言官方文档中提取 token 级语法约束对，支持 JavaScript、C、Java。

## 语法约束对

`(conditional, consequent)` 表示：给定已见的 token 序列前缀，下一步合法的 token 集合。

```json
{"conditional": "if",    "consequent": "("}
{"conditional": "if (",  "consequent": ")", "skip": "expression"}
{"conditional": "if ()", "consequent": "{, <statement_start>"}
```

## 提取结果

| 语言 | 官方文档 | 有效构造 | 约束对 |
|------|---------|---------|--------|
| JavaScript | MDN Web Docs | 71 | 628 |
| C | ISO/IEC 9899:2024 Annex A | 85 | 234 |
| Java | JLS Java SE 24 | 173 | 507 |

## 工作流

```
官方文档 (PDF / HTML)
    │
    ▼  Step 0: 文档预处理
{language}_index.json   ← 构造索引（name + syntax rule）
    │
    ▼  Step 1: LLM 批量提取
extracted/*.json        ← 每个构造的原始约束对
    │
    ▼  Step 2: 过滤合并
constraints.json        ← 最终输出
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 LLM 服务（编辑 config.yaml，设置 active: deepseek 或 anthropic）
export DEEPSEEK_API_KEY='your-key'

# 运行（单语言或全部）
./run.sh java
./run.sh all
```

## 目录结构

```
{language}/
  ├── docs/                  # 原始文档（PDF + 章节 txt）
  ├── extracted/             # LLM 原始提取（中间产物）
  ├── {language}_index.json  # 构造索引
  └── constraints.json       # 最终输出

scripts/
  ├── extract_pdf_syntax.py  # Step 0a: PDF → 章节 txt
  ├── 0_preprocess_pdf.py    # Step 0b: 章节 txt → index.json (C/Java)
  ├── 1_collect_docs.py      # Step 0b: MDN → index.json (JS)
  ├── 2_extract_constraints.py  # Step 1: LLM 批量提取
  ├── 3_consolidate.py       # Step 2: 过滤合并
  └── utils/llm_client.py    # LLM 客户端（Anthropic / DeepSeek）

config.yaml                  # LLM 服务配置
prompts/base_prompt_cn_v4.0.txt  # 提取 prompt
```

## 输出格式

```json
{
  "language": "c",
  "total_constructs": 85,
  "total_constraints": 234,
  "constructs": [
    {
      "construct": "selection-statement",
      "syntax_node": "if",
      "constraints": [
        {"conditional": "if", "consequent": "(", "skip": "", "required": true},
        {"conditional": "if (", "consequent": ")", "skip": "expression", "required": true}
      ]
    }
  ]
}
```

| 字段 | 说明 |
|------|------|
| `conditional` | 累积的 token 序列前缀 |
| `consequent` | 下一步合法 token（逗号分隔） |
| `skip` | 中间可跳过的抽象节点（如 `expression`） |
| `required` | 是否为强制约束 |

特殊标记：`[IDENT]` `[STRING]` `[PROPERTY]` `<expression_start>` `<statement_start>`
