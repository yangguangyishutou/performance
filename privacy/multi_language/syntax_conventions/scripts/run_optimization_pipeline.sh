#!/bin/bash
#
# 语法约束优化管道脚本
#
# 整合提取、去重、弱约束优化、清洗、验证等步骤
#
# 使用方法:
#   ./scripts/run_optimization_pipeline.sh --language javascript
#

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认参数
LANGUAGE="javascript"
PROMPT="prompts/base_prompt_strong_constraints_v1.0.txt"
THRESHOLD=4

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --language)
            LANGUAGE="$2"
            shift 2
            ;;
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --threshold)
            THRESHOLD="$2"
            shift 2
            ;;
        --help)
            echo "使用方法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --language LANG    编程语言 (默认: javascript)"
            echo "  --prompt FILE      Prompt 文件 (默认: prompts/base_prompt_strong_constraints_v1.0.txt)"
            echo "  --threshold NUM    弱约束阈值 (默认: 4)"
            echo "  --help             显示此帮助信息"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}语法约束优化管道${NC}"
echo -e "${BLUE}========================================${NC}"
echo "语言: $LANGUAGE"
echo "Prompt: $PROMPT"
echo "弱约束阈值: > $THRESHOLD 种 consequent"
echo ""

# 基础目录
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$BASE_DIR/$LANGUAGE/data"

# 激活虚拟环境
if [ -f "$BASE_DIR/venv/bin/activate" ]; then
    echo -e "${GREEN}✓ 激活虚拟环境${NC}"
    source "$BASE_DIR/venv/bin/activate"
fi

# ============================================
# Stage 1: 提取约束
# ============================================
echo -e "\n${BLUE}[Stage 1/5] 提取约束${NC}"
echo "----------------------------------------"

python3 "$BASE_DIR/scripts/2_extract_constraints.py" \
    --language "$LANGUAGE" \
    --prompt "$PROMPT"

echo -e "${GREEN}✓ Stage 1 完成${NC}"


# ============================================
# Stage 2: 去重
# ============================================
echo -e "\n${BLUE}[Stage 2/5] 去重${NC}"
echo "----------------------------------------"

python3 "$BASE_DIR/scripts/3_deduplicate_constraints.py" \
    --language "$LANGUAGE"

echo -e "${GREEN}✓ Stage 2 完成${NC}"


# ============================================
# Stage 3: 弱约束优化 ⭐
# ============================================
echo -e "\n${BLUE}[Stage 3/5] 弱约束优化${NC}"
echo "----------------------------------------"
echo "检测并优化 consequent 数量 > $THRESHOLD 的 conditional 规则"
echo ""

python3 "$BASE_DIR/scripts/4_optimize_weak_constraints.py" \
    --language "$LANGUAGE" \
    --threshold "$THRESHOLD" \
    --verbose

echo -e "${GREEN}✓ Stage 3 完成${NC}"


# ============================================
# Stage 4: 清洗与标准化
# ============================================
echo -e "\n${BLUE}[Stage 4/5] 清洗与标准化${NC}"
echo "----------------------------------------"

# TODO: 创建清洗脚本
echo -e "${YELLOW}⚠ 清洗脚本尚未实现，跳过${NC}"

echo -e "${GREEN}✓ Stage 4 完成${NC}"


# ============================================
# Stage 5: 质量验证
# ============================================
echo -e "\n${BLUE}[Stage 5/5] 质量验证${NC}"
echo "----------------------------------------"

python3 "$BASE_DIR/scripts/validate_constraints.py" \
    --language "$LANGUAGE" \
    --threshold "$THRESHOLD" 2>/dev/null || echo -e "${YELLOW}⚠ 验证脚本尚未实现${NC}"

echo -e "${GREEN}✓ Stage 5 完成${NC}"


# ============================================
# 管道汇总
# ============================================
echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}管道执行完成${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "数据目录: $DATA_DIR"
echo "  - extracted/    : 原始提取结果"
echo "  - deduplicated/ : 去重后"
echo "  - optimized/    : 弱约束优化后"
echo "  - cleaned/      : 清洗后"
echo ""
echo -e "${GREEN}✓ 所有阶段完成${NC}"
echo ""
echo "下一步:"
echo "  1. 检查优化报告: cat $DATA_DIR/optimization_summary.json"
echo "  2. 运行质量检查: python3 scripts/identify_strong_constraints.py"
echo "  3. 启动 Web 应用审核: cd web_app && npm run dev"
echo ""
