#!/bin/bash
# 半自动化语法约束提取 - 一键运行脚本
#
# 用法：
#   ./run.sh javascript
#   ./run.sh c
#   ./run.sh java
#   ./run.sh all
#
# 前置条件：
#   1. pip install -r requirements.txt
#   2. 在 config.yaml 中配置 active 服务
#   3. 设置对应的 API Key 环境变量

set -e

LANGUAGE=${1:-all}

run_language() {
    local lang=$1
    echo ""
    echo "========================================"
    echo " 处理语言: $lang"
    echo "========================================"

    # Step 0: 预处理
    if [ "$lang" = "javascript" ]; then
        echo "[Step 0] 抓取 MDN 文档..."
        python scripts/1_collect_docs.py --language javascript
    else
        echo "[Step 0] 分割 PDF 章节..."
        python scripts/extract_pdf_syntax.py --language $lang
        echo "[Step 0] 解析构造索引..."
        python scripts/0_preprocess_pdf.py --language $lang
    fi

    # Step 1: LLM 批量提取
    echo "[Step 1] LLM 批量提取..."
    python scripts/2_extract_constraints.py \
        --language $lang \
        --batch-size 10 \
        --prompt prompts/base_prompt_cn_v4.0.txt

    # Step 2: 过滤合并
    echo "[Step 2] 过滤合并..."
    python scripts/3_consolidate.py --language $lang

    echo ""
    echo "✓ $lang 完成 → ${lang}/constraints.json"
}

if [ "$LANGUAGE" = "all" ]; then
    run_language javascript
    run_language c
    run_language java
    echo ""
    echo "========================================"
    echo " 全部完成"
    echo "========================================"
    echo "输出文件："
    echo "  javascript/constraints.json"
    echo "  c/constraints.json"
    echo "  java/constraints.json"
else
    run_language $LANGUAGE
fi
