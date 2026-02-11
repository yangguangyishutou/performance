# 批量语法约束提取指南

## 概述

`scripts/2_extract_constraints.py` 脚本用于批量提取语法约束，支持所有文档索引中的构造。

## 功能特性

- ✅ 批量提取所有构造
- ✅ 断点续传（中断后可继续）
- ✅ 进度保存
- ✅ 错误处理和重试
- ✅ 详细日志和统计

## 快速开始

### 1. 测试提取（5 个构造）

```bash
cd /Users/chenzhuoyang/repo/GithubSITP/privacy/multi_language/syntax_conventions

# 激活虚拟环境
source venv/bin/activate

# 设置 API 密钥
export ZHIPU_API_KEY="72957a5577ad485c8f2f68d51ac180d2.Co4xjEtBtWBDXuzA"

# 测试提取前 5 个构造
python scripts/2_extract_constraints.py --language javascript --limit 5
```

### 2. 批量提取所有构造（138 个）

```bash
# 提取所有 JavaScript 构造
python scripts/2_extract_constraints.py --language javascript
```

### 3. 断点续传

```bash
# 如果中途中断，可以从断点继续
python scripts/2_extract_constraints.py \
    --language javascript \
    --checkpoint data/extracted/checkpoint.json
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--language` | 目标语言 (javascript, java, c, python) | `javascript` |
| `--limit` | 限制提取数量（用于测试） | 全部 |
| `--checkpoint` | 检查点文件路径 | 自动生成 |
| `--prompt` | Prompt 模板文件路径 | `prompts/base_prompt_cn_v4.0.txt` |

## 输出文件

### 单个构造输出

每个构造的约束保存到单独的 JSON 文件：

```
../js/data/
├── if...else.json          # if 语句的约束
├── for...of.json           # for...of 的约束
├── while.json              # while 的约束
├── try...catch.json        # try...catch 的约束
...
```

### 汇总输出

```
../js/data/
├── checkpoint.json                      # 断点文件
└── javascript_extraction_summary.json   # 汇总统计
```

## 验证提取质量

### 检查单个结果

```bash
# 查看提取的约束
cat data/extracted/if...else.json | python -m json.tool
```

### 检查汇总统计

```bash
# 查看提取统计
cat data/extracted/javascript_extraction_summary.json | python -m json.tool
```

## 常见问题

### Q: 提取失败怎么办？

检查 API 密钥和网络连接：
```bash
# 测试 API 连接
python scripts/utils/llm_client.py --test-connection
```

### Q: 如何只提取特定构造？

使用 `--limit` 参数：
```bash
python scripts/2_extract_constraints.py --language javascript --limit 10
```

### Q: 如何提取 Java 或 C？

首先收集文档：
```bash
python scripts/1_collect_docs.py --language java
python scripts/2_extract_constraints.py --language java
```

## 下一步

提取完成后：
1. **验证提取质量**：运行 `scripts/3_validate_constraints.py`
2. **客观分类**：运行 `scripts/3_classify_constraints.py`
3. **生成最终输出**：运行 `scripts/5_generate_outputs.py`
