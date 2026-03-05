#!/usr/bin/env python3
"""
去重语法约束脚本

从提取的约束中移除重复的 conditional-consequent 对：
- 构造内去重：同一构造内的重复规则
- 跨构造去重：可选，报告但保留（不同构造可能有相同规则）

输入：{language}/data/extracted/*.json
输出：{language}/data/cleaned/*.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Set
from datetime import datetime
from collections import defaultdict

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")


def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")


def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")


def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")


def normalize_constraint(constraint: Dict[str, Any]) -> Tuple[str, str]:
    """
    标准化约束用于去重比较

    标准化处理：
    - 空格标准化：去除多余空格
    - 大小写标准化：统一为小写（仅 conditional）
    - 占位符标准化：[IDENTIFIER] → [IDENT]

    Returns:
        (conditional, consequent) 标准化后的键
    """
    conditional = constraint.get("conditional", "")
    consequent = constraint.get("consequent", "")

    # 标准化占位符
    conditional = conditional.replace("[IDENTIFIER]", "[IDENT]")
    conditional = conditional.replace("[VARIABLE]", "[IDENT]")
    conditional = conditional.replace("[VAR]", "[IDENT]")

    consequent = consequent.replace("[IDENTIFIER]", "[IDENT]")
    consequent = consequent.replace("[VARIABLE]", "[IDENT]")
    consequent = consequent.replace("[VAR]", "[IDENT]")

    # 空格标准化
    conditional = " ".join(conditional.split())
    consequent = " ".join(consequent.split())

    return conditional, consequent


def deduplicate_construct(constraints: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    对单个构造的约束进行去重

    Args:
        constraints: 约束列表

    Returns:
        (去重后的约束列表, 去重统计信息)
    """
    seen = {}  # (conditional, consequent) -> constraint
    duplicates = []  # 记录重复项

    for constraint in constraints:
        key = normalize_constraint(constraint)

        if key in seen:
            # 记录重复
            duplicates.append({
                "key": key,
                "original": seen[key],
                "duplicate": constraint
            })
        else:
            seen[key] = constraint

    # 返回去重后的列表（保持原始顺序）
    deduplicated = list(seen.values())

    stats = {
        "original_count": len(constraints),
        "deduplicated_count": len(deduplicated),
        "removed_count": len(constraints) - len(deduplicated),
        "duplicates": duplicates
    }

    return deduplicated, stats


def deduplicate_all_constructs(
    input_dir: str,
    output_dir: str,
    cross_construct_check: bool = True
) -> Dict[str, Any]:
    """
    去重所有构造的约束

    Args:
        input_dir: 输入目录
        output_dir: 输出目录
        cross_construct_check: 是否检查跨构造重复

    Returns:
        汇总统计信息
    """
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有 JSON 文件
    input_path = Path(input_dir)
    json_files = [
        f for f in input_path.glob("*.json")
        if not f.name.endswith("_summary.json") and f.name != "checkpoint.json"
    ]

    if not json_files:
        print_error(f"未找到提取结果文件: {input_dir}")
        sys.exit(1)

    print(f"{'='*70}")
    print(" 语法约束去重")
    print(f"{'='*70}")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_dir}")
    print(f"文件数量: {len(json_files)}\n")

    # 统计信息
    total_original = 0
    total_deduplicated = 0
    total_removed = 0
    construct_stats = []

    # 跨构造重复检查
    cross_construct_duplicates = defaultdict(list) if cross_construct_check else {}

    # 处理每个文件
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print_error(f"无法读取文件 {json_file.name}: {e}")
            continue

        construct_name = data.get("construct", "Unknown")
        constraints = data.get("constraints", [])

        original_count = len(constraints)

        # 去重
        deduplicated, stats = deduplicate_construct(constraints)

        # 更新数据
        data["constraints"] = deduplicated
        data["deduplicated_at"] = datetime.now().isoformat()
        data["deduplication_stats"] = {
            "original_count": stats["original_count"],
            "removed_count": stats["removed_count"]
        }

        # 保存去重后的文件
        output_file = os.path.join(output_dir, json_file.name)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 统计
        total_original += original_count
        total_deduplicated += len(deduplicated)
        total_removed += stats["removed_count"]

        status_msg = f"{json_file.name}: {original_count} → {len(deduplicated)}"
        if stats["removed_count"] > 0:
            print_warning(f"⚠ {status_msg} (移除 {stats['removed_count']} 条)")
        else:
            print_success(f"✓ {status_msg}")

        # 记录统计
        construct_stats.append({
            "construct": construct_name,
            "file": json_file.name,
            "original_count": original_count,
            "deduplicated_count": len(deduplicated),
            "removed_count": stats["removed_count"]
        })

        # 跨构造重复检查
        if cross_construct_check:
            for constraint in deduplicated:
                key = normalize_constraint(constraint)
                cross_construct_duplicates[key].append(construct_name)

    # 汇总
    print(f"\n{'='*70}")
    print(" 去重汇总")
    print(f"{'='*70}")
    print(f"总约束数（去重前）: {total_original}")
    print(f"总约束数（去重后）: {total_deduplicated}")
    print_success(f"移除重复: {total_removed} ({total_removed/total_original*100:.1f}%)")

    # 跨构造重复报告
    if cross_construct_check:
        print(f"\n{'='*70}")
        print(" 跨构造重复检查")
        print(f"{'='*70}")

        cross_duplicates = {
            k: v for k, v in cross_construct_duplicates.items()
            if len(v) > 1
        }

        if cross_duplicates:
            print_warning(f"发现 {len(cross_duplicates)} 组跨构造重复的约束\n")

            # 显示前 10 组
            for i, (key, constructs) in enumerate(list(cross_duplicates.items())[:10], 1):
                print(f"{i}. {key[0]} → {key[1]}")
                print(f"   出现在: {', '.join(constructs)}")

            if len(cross_duplicates) > 10:
                print(f"\n... (还有 {len(cross_duplicates) - 10} 组)")
        else:
            print_success("✓ 未发现跨构造重复")

    # 保存汇总报告
    summary = {
        "language": input_dir.split('/')[0],
        "total_constructs": len(json_files),
        "total_original_constraints": total_original,
        "total_deduplicated_constraints": total_deduplicated,
        "total_removed": total_removed,
        "removal_rate": f"{total_removed/total_original*100:.1f}%",
        "deduplicated_at": datetime.now().isoformat(),
        "construct_stats": construct_stats,
        "cross_construct_duplicates_count": len(cross_duplicates) if cross_construct_check else 0
    }

    summary_file = os.path.join(output_dir, "..", "deduplication_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print_success(f"汇总报告已保存: {summary_file}")

    return summary


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="去重语法约束"
    )

    parser.add_argument(
        "--language",
        choices=["javascript", "java", "c"],
        default="javascript",
        help="目标语言"
    )

    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="输入目录（默认：{language}/data/extracted）"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认：{language}/data/cleaned）"
    )

    parser.add_argument(
        "--no-cross-check",
        action="store_true",
        help="禁用跨构造重复检查"
    )

    args = parser.parse_args()

    # 确定目录
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = f"{args.language}/data/extracted"

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = f"{args.language}/data/cleaned"

    # 运行去重
    try:
        summary = deduplicate_all_constructs(
            input_dir=input_dir,
            output_dir=output_dir,
            cross_construct_check=not args.no_cross_check
        )

        print(f"\n{GREEN}{'='*70}")
        print(" 去重完成！")
        print(f"{'='*70}{RESET}")

        return 0

    except KeyboardInterrupt:
        print_warning("\n\n用户中断")
        return 1

    except Exception as e:
        print_error(f"去重失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
