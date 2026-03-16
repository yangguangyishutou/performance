# 多语言语法约束提取系统

基于大语言模型的自动化语法约束提取系统，支持从编程语言文档中提取严格语法约束，并通过 Tree-sitter AST 解析进行验证。

## 项目状态

✅ **已完成：**
- 项目目录结构创建
- 环境配置脚本（`scripts/0_setup_env.py`）
- 文档收集脚本（`scripts/1_collect_docs.py`）
- JavaScript MDN 文档索引（150 个构造，138 个包含语法信息）
- Prompt 模板（基础模板 + JavaScript 策略）
- Python 少样本示例（从参考表格提取）

🚧 **进行中：**
- LLM 客户端实现（智谱 AI）
- 约束提取测试

📋 **待完成：**
- Java 和 C 语言文档收集
- 完整提取流程
- Tree-sitter 验证
- LaTeX 表格生成

## 快速开始

### 1. 环境配置

```bash
# 运行环境验证脚本
python3 scripts/0_setup_env.py

# 安装缺失的依赖（如需要）
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-java tree-sitter-c
pip install anthropic beautifulsoup4 lxml requests jinja2
```

### 2. 文档索引

```bash
# 索引 JavaScript 文档（已完成）
python3 scripts/1_collect_docs.py --language javascript

# 收集 Java 和 C 文档（需要手动下载或爬虫）
python3 scripts/1_collect_docs.py --language java
python3 scripts/1_collect_docs.py --language c
```

### 3. 提取语法约束（下一步）

```bash
# 提取指定语言的约束
python3 scripts/2_extract_constraints.py --language javascript
```

## 目录结构

```
syntax_conventions/
├── scripts/                    # 处理脚本
│   ├── 0_setup_env.py         # ✅ 环境验证
│   ├── 1_collect_docs.py      # ✅ 文档收集与索引
│   ├── 2_extract_constraints.py # 🚧 LLM 约束提取
│   ├── 3_classify_constraints.py # ⏳ 基于内容的客观分类
│   ├── 4_validate_constraints.py # ⏳ Tree-sitter 验证
│   ├── 5_generate_outputs.py  # ⏳ JSON/LaTeX 生成
│   └── utils/                  # 工具模块
│       ├── llm_client.py       # 🚧 智谱 AI 客户端
│       ├── tree_sitter_validator.py # ⏳ AST 验证
│       ├── prompt_templates.py # ⏳ Prompt 管理
│       └── output_formatters.py # ⏳ JSON/LaTeX 转换
├── prompts/                    # Prompt 模板（中文）
│   ├── base_prompt.txt         # ✅ 基础提取模板
│   ├── javascript_strategy.txt # ✅ JavaScript 特定指南
│   ├── python_few_shot_examples.json # ✅ Python 示例
│   ├── python_prompt.txt       # ⏳ Python 特定模板
│   ├── java_prompt.txt         # ⏳ Java 特定模板
│   └── c_prompt.txt            # ⏳ C 特定模板
├── data/                       # 数据文件
│   ├── raw/                    # 原始文档
│   │   └── javascript_index.json # ✅ JavaScript 索引
│   ├── extracted/              # LLM 提取的约束（无预设分类）
│   ├── classified/             # 客观分类后的约束
│   ├── validated/              # 验证后的约束
│   └── final/                  # 最终输出
├── js/                         # JavaScript MDN 文档
│   └── reference/              # 150 个 markdown 文件
├── logs/                       # 处理日志
│   └── setup_report.json       # ✅ 环境报告
└── README.md                   # 本文件
```

## 当前状态报告

### JavaScript 文档索引（✅ 已完成）

- **总构造数**：150
- **包含语法**：138
- **文档组织分类**（用于文档管理，非最终分类）：
  - 表达式（Expressions）：100 个构造
  - 单语句（Single Statements）：11 个构造
  - 复合语句（Compound Statements）：27 个构造

**重要说明**：此处的分类是"文档组织分类"，仅用于方便文档管理和检索。最终的"语法约束分类"将在提取约束后，基于约束的**实际内容特征**进行客观分析，详见下文"研究方法"部分。

示例索引的构造：
- **复合语句**（Compound Statements）：if...else, for...of, while, do...while, try...catch, class, switch
- **单语句**（Single Statements）：var, let, const, return, throw, import, export
- **表达式**（Expressions）：箭头函数、模板字符串、操作符、解构

## 研究方法与学术严谨性

### 两阶段分类方法论

为确保学术严谨性，本项目采用**两阶段分类**方法：

#### 阶段 1：文档组织分类（当前阶段）

**目的**：文档管理和定位，**不是**最终分类

**流程**：
1. 根据文档结构（如 MDN 的 operators/, statements/）进行初步组织
2. 便于快速定位和处理特定构造的文档

**示例**：
```json
{
  "construct": "if...else",
  "doc_category": "statements",  // 来自文档路径，用于组织
  "syntax": "..."
}
```

**标注**：此分类仅用于文档组织，不代表语法约束的最终分类

#### 阶段 2：约束客观分类（核心研究阶段）

**目的**：基于实际约束内容进行科学分类

**流程**：
1. **无预设提取**：LLM 提取约束时不带任何分类预设
2. **内容分析**：基于约束的结构特征进行客观分析
3. **自动分类**：根据预定义的客观标准自动分类
4. **人工验证**：抽样验证分类的准确性

**客观分类标准**：
- **数据模型（Data Model）**：
  - 字面量、类型定义、变量声明
  - 特征：定义数据结构和类型

- **表达式（Expressions）**：
  - 操作符、函数调用、计算式
  - 特征：产生值，可嵌套

- **单语句（Single Statements）**：
  - return, break, continue, import, throw
  - 特征：单一控制流转移，不包含嵌套块

- **复合语句（Compound Statements）**：
  - if, for, while, class, function, try...catch
  - 特征：包含嵌套块结构或控制流

**输出示例**：
```json
{
  "construct": "if...else",
  "extracted_constraints": [
    {"step": 1, "conditional_token": "if", "consequence_token": "(", ...},
    {"step": 2, "conditional_token": "if (", "consequence_token": ")", ...}
  ],
  "constraint_category": "Compound Statements",  // 基于内容分析
  "category_reasoning": "包含控制流和条件分支，需要块结构",
  "confidence": 0.95
}
```

### 学术论文中的表述

在论文中，我们将这样描述方法：

> **方法**：我们采用两阶段方法以确保分类的客观性。首先，从官方文档中提取所有语法约束，**不预设任何分类**。然后，基于约束的**结构特征**（如是否包含控制流、是否需要块结构、是否产生值等）进行**客观分类**。此分类方法避免了预设偏见，确保结果的可重现性和可验证性。

这种完全符合学术规范的方法论！

## Prompt 工程

### 基础 Prompt 结构

基础 Prompt（`prompts/base_prompt.txt`）包含：

1. **角色**：编程语言理论和 AST 分析专家
2. **任务**：提取严格语法约束（不预设分类）
3. **方法**：原子化顺序分解
4. **输出格式**：结构化 JSON
5. **客观标准**：基于内容的分类依据

### JavaScript 特定策略

JavaScript 策略（`prompts/javascript_strategy.txt`）强调：

- **括号**：`if`, `while`, `for` 中必须（不同于 Python）
- **大括号**：多语句块必需
- **分号**：ASI 使其可选但推荐
- **箭头函数**：独特的 `=>` 语法
- **模板字符串**：反引号定界符
- **解构**：对象 `{}` 和数组 `[]` 模式

### 少样本学习（Few-Shot）

Python 示例（`prompts/python_few_shot_examples.json`）提供：
- 5 个不同构造：while, if, for, list, function
- 顺序约束分解
- 有效和无效示例
- 链式规则表示

## 下一步工作

### 立即进行（需要 API 密钥）

1. **配置智谱 AI API 密钥**：
   ```bash
   export ZHIPU_API_KEY="72957a5577ad485c8f2f68d51ac180d2.Co4xjEtBtWBDXuzA"
   ```

2. **实现 LLM 客户端**（`scripts/utils/llm_client.py`）：
   - 智谱 AI API 集成
   - Prompt 模板组装
   - JSON 响应解析

3. **实现约束提取脚本**（`scripts/2_extract_constraints.py`）：
   - **不带预设分类**提取所有约束
   - 保存为中间格式

4. **实现客观分类脚本**（`scripts/3_classify_constraints.py`）：
   - 基于约束内容进行客观分析
   - 应用分类标准
   - 计算分类置信度

5. **子集测试**：
   - 提取 5 个 JavaScript 构造的约束
   - 验证输出质量
   - 根据结果调整 Prompt

### 短期目标

6. **批量提取**：提取所有 138 个 JavaScript 构造的约束
7. **客观分类**：对所有提取的约束进行基于内容的分类
8. **Java/C 文档**：收集并索引 Java 和 C 文档
9. **验证实现**：实现 Tree-sitter 验证
10. **测试**：验证提取和分类的准确性

### 长期目标

11. **人工审查**：抽查 10% 的约束和分类
12. **输出生成**：生成最终 JSON 和 LaTeX 表格
13. **跨语言对比**：对比不同语言间的构造差异
14. **论文撰写**：使用生成的表格和统计数据

## 核心设计决策

### 四大分类体系

与 Python 参考表格保持一致：
1. **数据模型（Data Model）**：类型、字面量、对象
2. **表达式（Expressions）**：操作符、函数调用
3. **单语句（Single Statements）**：声明、简单语句
4. **复合语句（Compound Statements）**：控制流、定义

### 原子化顺序分解

每个构造分解为顺序步骤：
- 示例：`while` 循环 → 关键字 → 条件 → 冒号 → 换行 → 缩进

捕捉**链式规则**，每步依赖前一步。

### 两阶段分类

1. **文档组织**：基于文档结构（方便管理）
2. **约束分类**：基于约束内容（科学研究）

### 双重验证

1. **自动**：Tree-sitter AST 解析
2. **人工**：抽样检查（10% 随机 + 复杂构造）

### 双重输出

1. **JSON**：机器可读的结构化数据
2. **LaTeX**：符合 Python 格式的发表级表格

## 依赖项

### 必需

- Python 3.8+
- tree-sitter
- tree-sitter-python
- tree-sitter-javascript
- tree-sitter-java
- tree-sitter-c
- anthropic（智谱 AI 兼容）
- beautifulsoup4
- lxml
- requests
- jinja2

### 安装

```bash
# 一次性安装所有依赖
pip install tree-sitter tree-sitter-python tree-sitter-javascript \
            tree-sitter-java tree-sitter-c anthropic \
            beautifulsoup4 lxml requests jinja2
```

## 环境变量

```bash
# 智谱 AI API 密钥
export ZHIPU_API_KEY="72957a5577ad485c8f2f68d51ac180d2.Co4xjEtBtWBDXuzA"
```

## 故障排除

### 环境配置脚本失败

如果 `scripts/0_setup_env.py` 失败：
1. 检查 Python 版本 >= 3.8
2. 安装缺失的依赖
3. 验证 Tree-sitter 解析器已安装

### 文档索引失败

如果 `scripts/1_collect_docs.py` 失败：
1. 验证 `js/reference/` 目录存在
2. 检查 markdown 文件是否存在
3. 确保使用 UTF-8 编码

### API 错误

如果 LLM API 调用失败：
1. 验证 API 密钥已设置
2. 检查 API 配额/额度
3. 手动测试 API 密钥

## 贡献

这是一个研究项目。如有问题或建议：
1. 查看本 README
2. 查看计划文件：`~/.claude/plans/precious-watching-leaf.md`
3. 查阅 `logs/` 目录中的日志

## 参考资料

- Python 约束表：用户提供的 LaTeX 表格
- JavaScript 文档：MDN Web Docs
- Java 规范：JLS (Oracle)
- C 参考：cppreference.com
- Tree-sitter：https://tree-sitter.github.io/tree-sitter/

## 许可证

研究项目 - 联系维护者获取使用许可。
