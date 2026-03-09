#!/usr/bin/env python3
"""
验证语法约束脚本

综合验证约束的正确性和完整性：

1. 语法规则验证：
   - 非法语法组合检测
   - 括号匹配验证
   - 必需字段检查

2. 跨构造验证：
   - 检测冲突规则（同一 conditional 有不同的 consequent）
   - 查找孤立的 conditionals

3. 覆盖率分析：
   - 计算每个构造的约束密度
   - 识别可能有遗漏的构造

输入：{language}/data/cleaned/*.json
输出：{language}/data/validation_report.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
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


def validate_bracket_matching(s: str) -> Tuple[bool, str]:
    """
    验证括号匹配（仅检测错误的右括号）
    """
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}

    for i, char in enumerate(s):
        if char in '([{':
            stack.append((char, i))
        elif char in ')]}':
            if not stack or stack[-1][0] != pairs[char]:
                return False, f"位置 {i}: '{char}' 没有对应的左括号"
            stack.pop()

    return True, ""


def validate_constraint(
    constraint: Dict[str, Any],
    construct_name: str
) -> List[str]:
    """
    验证单个约束

    Returns:
        警告列表
    """
    warnings = []

    conditional = constraint.get("conditional", "")
    consequent = constraint.get("consequent", "")
    required = constraint.get("required", True)
    note = constraint.get("note", "")

    # 检查 1: 必需字段
    if not conditional:
        warnings.append("缺少 conditional 字段")
    if not consequent:
        warnings.append("缺少 consequent 字段")
    if note == "":
        warnings.append("缺少 note 字段")

    # 检查 2: 括号匹配
    is_valid, error_msg = validate_bracket_matching(conditional)
    if not is_valid:
        warnings.append(f"conditional 括号错误: {error_msg}")

    # 检查 3: 空的 consequent（除非有 skip）
    skip = constraint.get("skip", "")
    if not consequent and not skip:
        warnings.append("consequent 和 skip 都为空")

    # 检查 4: 特定构造的规则
    if "Rest parameter" in construct_name:
        if "..." in conditional and "," in consequent:
            warnings.append("Rest 参数后不能跟逗号")

    # 检查 5: conditional 和 consequent 不能相同（无意义的规则）
    if conditional == consequent:
        warnings.append(f"conditional 和 consequent 相同: '{conditional}'")

    return warnings


def validate_construct_file(file_path: Path) -> Dict[str, Any]:
    """
    验证单个构造文件

    Returns:
        验证结果
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {
            "file": file_path.name,
            "status": "error",
            "error": str(e)
        }

    construct = data.get("construct", "Unknown")
    constraints = data.get("constraints", [])

    all_warnings = []
    constraint_density = {
        "total": len(constraints),
        "with_skip": sum(1 for c in constraints if c.get("skip")),
        "required": sum(1 for c in constraints if c.get("required", True)),
        "optional": sum(1 for c in constraints if not c.get("required", True))
    }

    for i, constraint in enumerate(constraints, 1):
        warnings = validate_constraint(constraint, construct)

        if warnings:
            all_warnings.append({
                "constraint_index": i,
                "conditional": constraint.get("conditional", ""),
                "consequent": constraint.get("consequent", ""),
                "warnings": warnings
            })

    # 约束密度分析
    density_score = len(constraints)
    if density_score < 3:
        density_status = "low"
    elif density_score < 10:
        density_status = "medium"
    else:
        density_status = "high"

    return {
        "file": file_path.name,
        "construct": construct,
        "status": "passed" if not all_warnings else "warning",
        "total_constraints": len(constraints),
        "constraint_density": constraint_density,
        "density_status": density_status,
        "warning_count": len(all_warnings),
        "warnings": all_warnings
    }


def find_cross_construct_conflicts(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    查找跨构造冲突

    冲突定义：同一 conditional 在不同构造中有不同的 consequent 集合
    """
    # 收集所有 conditional -> (construct, consequent) 映射
    conditional_map = defaultdict(set)  # conditional -> set of (construct, consequent)

    for result in results:
        if result["status"] == "error":
            continue

        construct = result["construct"]
        # 读取原始文件获取 constraints
        file_path = Path(f"javascript/data/cleaned/{result['file']}")
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
                for c in data.get("constraints", []):
                    conditional = c.get("conditional", "")
                    consequent = c.get("consequent", "")
                    if conditional and consequent:
                        conditional_map[conditional].add((construct, consequent))
        except:
            continue

    # 查找冲突
    conflicts = []
    for conditional, constructs in conditional_map.items():
        # 获取所有不同的 consequent
        consequents = set(cons for _, cons in constructs)

        if len(consequents) > 1:
            # 这可能是一个冲突
            # 检查是否真的不同（例如 `{` 和 `<statement_start>` 是允许的）
            conflicts.append({
                "conditional": conditional,
                "constructs": list(set(cons for cons, _ in constructs)),
                "consequents": list(consequents),
                "is_real_conflict": len(consequents) > 1  # 可能需要人工判断
            })

    return conflicts


def analyze_coverage(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    分析覆盖率
    """
    total_constructs = len(results)
    total_constraints = sum(r["total_constraints"] for r in results)

    low_density = [r for r in results if r["density_status"] == "low"]
    warnings_count = sum(r["warning_count"] for r in results)

    return {
        "total_constructs": total_constructs,
        "total_constraints": total_constraints,
        "avg_constraints_per_construct": total_constraints / total_constructs if total_constructs > 0 else 0,
        "low_density_constructs": len(low_density),
        "low_density_construct_names": [r["construct"] for r in low_density],
        "total_warnings": warnings_count,
        "constructs_with_warnings": sum(1 for r in results if r["warning_count"] > 0)
    }


def validate_all_constructs(input_dir: str) -> Dict[str, Any]:
    """
    验证所有构造文件
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print_error(f"目录不存在: {input_dir}")
        sys.exit(1)

    json_files = [
        f for f in input_path.glob("*.json")
        if not f.name.endswith("_summary.json") and
           f.name != "checkpoint.json" and
           f.name != "cleaning_summary.json" and
           f.name != "deduplication_summary.json"
    ]

    if not json_files:
        print_error(f"未找到构造文件: {input_dir}")
        sys.exit(1)

    print(f"{'='*70}")
    print(" 语法约束验证")
    print(f"{'='*70}")
    print(f"目录: {input_dir}")
    print(f"文件数量: {len(json_files)}\n")

    results = []
    for json_file in sorted(json_files):
        result = validate_construct_file(json_file)
        results.append(result)

        if result["status"] == "error":
            print_error(f"✗ {result['file']}: {result.get('error', 'Unknown error')}")
        elif result["status"] == "warning":
            print_warning(f"⚠ {result['file']}: {result['warning_count']} 个警告")
        else:
            density_emoji = {
                "low": "🔴",
                "medium": "🟡",
                "high": "🟢"
            }.get(result["density_status"], "⚪")
            print_success(f"{density_emoji} {result['file']}: {result['total_constraints']} 条规则")

    # 跨构造冲突检测
    print(f"\n{'='*70}")
    print(" 跨构造冲突检测")
    print(f"{'='*70}")

    conflicts = find_cross_construct_conflicts(results)

    if conflicts:
        print_warning(f"发现 {len(conflicts)} 个潜在冲突\n")

        # 显示前 10 个
        for i, conflict in enumerate(conflicts[:10], 1):
            print(f"{i}. conditional: '{conflict['conditional']}'")
            print(f"   出现在: {', '.join(conflict['constructs'])}")
            print(f"   consequents: {conflict['consequents']}")

        if len(conflicts) > 10:
            print(f"\n... (还有 {len(conflicts) - 10} 个)")
    else:
        print_success("✓ 未发现跨构造冲突")

    # 覆盖率分析
    print(f"\n{'='*70}")
    print(" 覆盖率分析")
    print(f"{'='*70}")

    coverage = analyze_coverage(results)
    print(f"总构造数: {coverage['total_constructs']}")
    print(f"总约束数: {coverage['total_constraints']}")
    print(f"平均每构造约束数: {coverage['avg_constraints_per_construct']:.1f}")
    print(f"低密度构造数: {coverage['low_density_constructs']}")

    if coverage["low_density_constructs"] > 0:
        print(f"\n低密度构造（可能需要人工检查）:")
        for name in coverage["low_density_construct_names"]:
            print(f"  - {name}")

    print(f"\n有警告的构造: {coverage['constructs_with_warnings']}")
    print(f"总警告数: {coverage['total_warnings']}")

    # 汇总报告
    print(f"\n{'='*70}")
    print(" 验证汇总")
    print(f"{'='*70}")

    passed = sum(1 for r in results if r["status"] == "passed")
    warning = sum(1 for r in results if r["status"] == "warning")
    error = sum(1 for r in results if r["status"] == "error")

    print(f"✅ 通过: {passed}")
    if warning > 0:
        print_warning(f"⚠ 警告: {warning}")
    if error > 0:
        print_error(f"❌ 错误: {error}")

    # 保存报告
    report = {
        "language": input_dir.split('/')[0],
        "validated_at": datetime.now().isoformat(),
        "summary": {
            "total_constructs": coverage["total_constructs"],
            "total_constraints": coverage["total_constraints"],
            "passed": passed,
            "warning": warning,
            "error": error
        },
        "coverage": coverage,
        "cross_construct_conflicts": conflicts,
        "detailed_results": results
    }

    report_file = os.path.join(input_dir, "validation_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print_success(f"验证报告已保存: {report_file}")

    return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="验证语法约束"
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
        help="输入目录（默认：{language}/data/cleaned）"
    )

    args = parser.parse_args()

    # 确定目录
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = f"{args.language}/data/cleaned"

    # 运行验证
    try:
        report = validate_all_constructs(input_dir)

        print(f"\n{GREEN}{'='*70}")
        print(" 验证完成！")
        print(f"{'='*70}{RESET}")

        return 0

    except KeyboardInterrupt:
        print_warning("\n\n用户中断")
        return 1

    except Exception as e:
        print_error(f"验证失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
