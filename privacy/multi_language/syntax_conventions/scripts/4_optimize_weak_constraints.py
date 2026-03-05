#!/usr/bin/env python3
"""
弱约束优化脚本

检测并优化 consequent 数量 > 4 的 conditional 规则。
- 如果全部 optional：保持原样
- 如果可以抽象：使用抽象占位符
- 如果无法抽象：舍弃规则
"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_color(message: str, color: str):
    """打印带颜色的消息"""
    print(f"{color}{message}{RESET}")


def load_constraints(data_dir: Path) -> dict:
    """加载所有约束文件"""
    constraints_by_file = {}

    for file in sorted(data_dir.glob("*.json")):
        with open(file) as f:
            data = json.load(f)
            constraints_by_file[file.name] = data

    return constraints_by_file


def detect_weak_constraints(constraints: list, filename: str) -> list:
    """检测弱约束规则"""
    # 按 conditional 分组
    by_conditional = defaultdict(list)

    for c in constraints:
        # 跳过占位符 consequent（以 < 开头的抽象占位符）
        if not c["consequent"].startswith("["):
            by_conditional[c["conditional"]].append(c)

    # 检测弱约束
    weak_constraints = []

    for cond, rules in by_conditional.items():
        unique_consequents = set(r["consequent"] for r in rules)
        count = len(unique_consequents)

        # 判断标准：> 4 种 consequent
        if count > 4:
            # 检查是否都是 optional
            all_optional = all(r.get("required", True) == False for r in rules)

            weak_constraints.append({
                "conditional": cond,
                "consequent_count": count,
                "all_optional": all_optional,
                "consequents": sorted(list(unique_consequents)),
                "rules": rules,
                "optimizable": not all_optional and count > 4
            })

    return weak_constraints


def select_abstract_placeholder(conditional: str) -> str:
    """
    根据 conditional 选择合适的抽象占位符
    """
    # await/yield → expression
    if conditional in ["await", "yield"]:
        return "<expression_start>"

    # new/delete/typeof/void → expression
    if conditional in ["new", "delete", "typeof", "void"]:
        return "<expression_start>"

    # export/import → declaration or specifier
    if conditional in ["export", "import", "export default", "import("]:
        return "<declaration_or_expression>"

    # for/while/if → control structure
    if conditional.startswith("for") or conditional in ["while", "if"]:
        return "<loop_or_control>"

    # 默认：通用抽象
    return "<expression_start>"


def optimize_weak_constraint(weak_constraint: dict) -> list:
    """
    优化弱约束规则

    Returns:
        优化后的规则列表，或 None（如果不需要优化）
    """
    cond = weak_constraint["conditional"]
    all_optional = weak_constraint["all_optional"]

    # 如果都是 optional，不需要优化
    if all_optional:
        return None

    # 选择抽象占位符
    placeholder = select_abstract_placeholder(cond)

    # 生成优化后的规则
    optimized_rule = {
        "conditional": cond,
        "consequent": placeholder,
        "skip": "",
        "required": True,
        "note": f"{cond} 后必须跟 {placeholder}"
    }

    return [optimized_rule]


def optimize_file(input_file: Path, output_file: Path) -> dict:
    """优化单个文件"""
    with open(input_file) as f:
        data = json.load(f)

    construct = data.get("construct", input_file.stem)
    constraints = data.get("constraints", [])

    # 检测弱约束
    weak_constraints = detect_weak_constraints(constraints, input_file.name)

    if not weak_constraints:
        return {
            "file": input_file.name,
            "construct": construct,
            "status": "NO_WEAK_CONSTRAINTS"
        }

    # 优化弱约束
    optimized_count = 0
    accepted_count = 0
    discarded_count = 0
    new_constraints = []
    removed_conditionals = set()

    for wc in weak_constraints:
        if wc["all_optional"]:
            # 全部 optional，保持原样
            accepted_count += 1
        else:
            # 需要优化
            optimized_rules = optimize_weak_constraint(wc)

            if optimized_rules:
                # 移除旧规则，添加优化后的规则
                removed_conditionals.add(wc["conditional"])
                new_constraints.extend(optimized_rules)
                optimized_count += 1

                print_color(f"  ✓ 优化: '{wc['conditional']}' ({wc['consequent_count']}种 → 1种)", GREEN)
            else:
                # 无法优化，舍弃
                removed_conditionals.add(wc["conditional"])
                discarded_count += 1

                print_color(f"  ✗ 舍弃: '{wc['conditional']}' ({wc['consequent_count']}种)", RED)

    # 构建新的约束列表
    final_constraints = []

    # 添加未移除的原始规则
    for c in constraints:
        if c["conditional"] not in removed_conditionals:
            final_constraints.append(c)

    # 添加优化后的规则
    final_constraints.extend(new_constraints)

    # 更新数据
    data["constraints"] = final_constraints
    data["optimized_at"] = datetime.now().isoformat()
    data["optimization_stats"] = {
        "original_count": len(constraints),
        "optimized_count": len(final_constraints),
        "weak_constraints_found": len(weak_constraints),
        "weak_constraints_optimized": optimized_count,
        "weak_constraints_accepted": accepted_count,
        "weak_constraints_discarded": discarded_count
    }

    # 保存
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {
        "file": input_file.name,
        "construct": construct,
        "status": "OPTIMIZED",
        "weak_found": len(weak_constraints),
        "optimized": optimized_count,
        "accepted": accepted_count,
        "discarded": discarded_count
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="优化弱约束规则（consequent 数量 > 4）"
    )
    parser.add_argument(
        "--language",
        default="javascript",
        help="编程语言（默认：javascript）"
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="输入目录（默认：{language}/data/deduplicated）"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="输出目录（默认：{language}/data/optimized）"
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=4,
        help="弱约束阈值（默认：4）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细信息"
    )

    args = parser.parse_args()

    # 确定路径
    base_dir = Path.cwd()
    if args.input_dir:
        input_dir = Path(args.input_dir)
    else:
        input_dir = base_dir / f"{args.language}/data/deduplicated"

    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = base_dir / f"{args.language}/data/optimized"

    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)

    print_color("=" * 100, BLUE)
    print_color("弱约束优化脚本", BLUE)
    print_color("=" * 100, BLUE)
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"阈值: consequent 数量 > {args.threshold}")
    print()

    # 处理所有文件
    results = []
    total_optimized = 0
    total_accepted = 0
    total_discarded = 0

    for input_file in sorted(input_dir.glob("*.json")):
        output_file = output_dir / input_file.name

        if args.verbose:
            print_color(f"处理: {input_file.name}", YELLOW)

        result = optimize_file(input_file, output_file)
        results.append(result)

        if result.get("status") == "OPTIMIZED":
            if args.verbose:
                print_color(f"  构造: {result['construct']}", YELLOW)

            total_optimized += result.get("optimized", 0)
            total_accepted += result.get("accepted", 0)
            total_discarded += result.get("discarded", 0)

    # 汇总
    print()
    print_color("=" * 100, BLUE)
    print_color("优化汇总", BLUE)
    print_color("=" * 100, BLUE)
    print(f"处理文件数: {len(results)}")
    print(f"优化规则数: {total_optimized}")
    print(f"接受规则数: {total_accepted}")
    print(f"舍弃规则数: {total_discarded}")
    print()

    # 保存汇总报告
    summary_file = output_dir.parent / "optimization_summary.json"
    summary = {
        "language": args.language,
        "threshold": args.threshold,
        "processed_files": len(results),
        "total_optimized": total_optimized,
        "total_accepted": total_accepted,
        "total_discarded": total_discarded,
        "results": results,
        "timestamp": datetime.now().isoformat()
    }

    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print_color(f"✅ 汇总报告已保存到：{summary_file}", GREEN)


if __name__ == "__main__":
    main()
