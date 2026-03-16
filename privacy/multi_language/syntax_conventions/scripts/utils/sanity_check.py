#!/usr/bin/env python3
"""
语法约束合理性检查

检测提取的约束中可能的错误，如：
- 使用了错误的括号类型（例如 set 后应该用 [ 而不是 (）
- 违反语法规则（例如 Rest 参数后跟逗号）
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple


# 已知的语法规则
SYNTAX_RULES = {
    # JavaScript 特定规则
    "javascript": {
        # setter/getter 必须使用 [ 而不是 ( 来开始计算属性名
        "setter_bracket": {
            "pattern": r"^(get|set)\s*\(",
            "error": "getter/setter 计算属性名必须使用方括号 [ 而不是圆括号 (",
            "correct": "应该使用 'get [' 或 'set ['"
        },
        # Rest 参数必须是最后一个参数
        "rest_params_last": {
            "pattern": r"\.\.\s*[A-Z]+\s*,",
            "error": "Rest 参数后不能跟逗号",
            "correct": "删除 '... [IDENT] ,' 后的规则"
        }
    }
}


def validate_bracket_matching(s: str) -> Tuple[bool, str]:
    """
    验证字符串中的括号是否正确配对（针对前缀模式）

    注意：conditional 是前缀模式，允许未闭合的左括号，
    但不允许错误的括号类型（如右括号没有对应的左括号）

    Args:
        s: 要验证的字符串

    Returns:
        (is_valid, error_message) - is_valid 为 True 表示合法
    """
    stack = []  # 存储左括号
    bracket_pairs = {')': '(', ']': '[', '}': '{'}

    for i, char in enumerate(s):
        if char in '([{':
            stack.append((char, i))
        elif char in ')]}':
            if not stack or stack[-1][0] != bracket_pairs[char]:
                # 错误：右括号没有对应的左括号或类型不匹配
                return False, f"位置 {i}: 右括号 '{char}' 没有对应的左括号"
            stack.pop()

    # 注意：我们不再检查 stack 是否为空
    # 因为 conditional 是前缀，允许有未闭合的括号（如 "async (" 是合法的）
    return True, ""


def check_constraint_pair(constraint: Dict[str, Any], language: str, construct_name: str = "") -> List[str]:
    """
    检查单个约束对的合理性

    Args:
        constraint: 约束字典
        language: 语言名称
        construct_name: 构造名称（用于特定规则检查）

    Returns:
        错误列表
    """
    errors = []

    conditional = constraint.get("conditional", "")
    consequent = constraint.get("consequent", "")
    note = constraint.get("note", "")

    # 检查 0: conditional 中的括号匹配（仅检测真正错误的括号类型）
    is_valid, error_msg = validate_bracket_matching(conditional)
    if not is_valid:
        errors.append(
            f"❌ 错误：conditional 中的括号不匹配\n"
            f"   conditional: '{conditional}'\n"
            f"   {error_msg}\n"
            f"   说明：conditional 作为前缀可以包含未闭合的左括号（如 'async (' 是合法的），\n"
            f"        但右括号必须有对应的左括号（如 'if () }}' 是非法的）"
        )

    # 检查 1: getter/setter 括号类型
    if conditional in ["get", "set"]:
        # 检查是否包含独立的 '(' (不是 'expression_start' 等标记的一部分)
        consequent_parts = [c.strip() for c in consequent.split(",")]
        # 如果有独立的 '(' 且不是表达式的一部分，则是错误的
        has_invalid_paren = False
        for part in consequent_parts:
            if part == "(":
                has_invalid_paren = True
                break
            # 如果包含 '(' 但不是单独的，比如 'expression_start('，这也可能是错的
            if part.endswith("(") and not part.startswith("<"):
                has_invalid_paren = True
                break

        if has_invalid_paren:
            errors.append(
                f"❌ 错误：'{conditional}' 后使用了圆括号 '(' 而不是方括号 '['\n"
                f"   当前 consequent: {consequent}\n"
                f"   正确 consequent: '[PROPERTY], [' （计算属性名必须用方括号）"
            )

    # 检查 2: Rest 参数后跟逗号（仅对 Rest parameters 构造生效）
    # 注意：Spread syntax (...).json 等其他使用 ... 的构造可以跟逗号
    if "Rest parameter" in construct_name and "..." in conditional and "," in consequent:
        errors.append(
            f"❌ 错误：Rest 参数后不能跟逗号\n"
            f"   conditional: {conditional}\n"
            f"   consequent: {consequent}\n"
            f"   JS 语法规则：Rest 参数必须是最后一个参数"
        )

    # 检查 3: conditional 包含抽象占位符
    # 排除我们定义的特殊标记（如 <expression_start>, <statement_start>）
    abstract_placeholders = ["statement", "expression", "block"]
    for placeholder in abstract_placeholders:
        # 检查是否包含占位符但不包含特殊标记
        if placeholder in conditional.lower():
            # 如果包含特殊标记，则跳过检查
            special_markers = ["<" + placeholder + "_start>", "<" + placeholder + "_start>"]
            has_special_marker = any(marker in conditional.lower() for marker in special_markers)

            if not has_special_marker:
                errors.append(
                    f"⚠️  警告：conditional 包含抽象占位符 '{placeholder}'\n"
                    f"   conditional: {conditional}\n"
                    f"   建议：使用 [IDENT], [STRING] 等具体占位符，或放在 skip 字段"
                )

    # 检查 4: note 中的双引号（可能导致 JSON 解析失败）
    if '"' in note and "'" not in note and '\\"' not in note:
        # 只有当 note 包含双引号但没有转义或单引号时才警告
        errors.append(
            f"⚠️  警告：note 中包含未转义的双引号（可能导致 JSON 解析失败）\n"
            f"   note: {note}\n"
            f"   建议：使用单引号 ' 代替双引号"
        )

    return errors


def check_construct_file(file_path: Path) -> Dict[str, Any]:
    """
    检查单个构造文件

    Args:
        file_path: JSON 文件路径

    Returns:
        检查结果字典
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        return {
            "file": file_path.name,
            "status": "error",
            "error": f"无法读取文件: {e}"
        }

    construct = data.get("construct", "Unknown")
    language = data.get("language", "unknown")
    constraints = data.get("constraints", [])

    all_errors = []

    for i, constraint in enumerate(constraints, 1):
        errors = check_constraint_pair(constraint, language, construct)
        if errors:
            all_errors.append({
                "constraint_index": i,
                "conditional": constraint.get("conditional", ""),
                "consequent": constraint.get("consequent", ""),
                "errors": errors
            })

    return {
        "file": file_path.name,
        "construct": construct,
        "language": language,
        "status": "passed" if not all_errors else "failed",
        "total_constraints": len(constraints),
        "error_count": len(all_errors),
        "errors": all_errors
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="检查提取的语法约束的合理性"
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="语言名称 (javascript, java, c)，将自动使用对应的目录"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="提取结果目录（如果指定 --language，则此项被忽略）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细错误信息"
    )

    args = parser.parse_args()

    # 确定检查目录
    if args.language:
        extract_dir = Path(f"{args.language}/data/extracted")
    elif args.dir:
        extract_dir = Path(args.dir)
    else:
        # 默认使用 JavaScript
        extract_dir = Path("javascript/data/extracted")

    if not extract_dir.exists():
        print(f"❌ 目录不存在: {extract_dir}")
        return 1

    # 获取所有 JSON 文件
    json_files = [
        f for f in extract_dir.glob("*.json")
        if not f.name.endswith("_summary.json") and f.name != "checkpoint.json"
    ]

    if not json_files:
        print(f"❌ 未找到提取结果文件")
        return 1

    print("="*70)
    print(" 语法约束合理性检查")
    print("="*70)
    print(f"检查目录: {extract_dir}")
    print(f"文件数量: {len(json_files)}\n")

    # 检查每个文件
    results = []
    passed = []
    failed = []

    for json_file in json_files:
        result = check_construct_file(json_file)
        results.append(result)

        if result["status"] == "passed":
            passed.append(result["file"])
            print(f"✅ {result['file']}")
        elif result["status"] == "failed":
            failed.append(result["file"])
            print(f"❌ {result['file']} ({result['error_count']} 个错误)")

            if args.verbose:
                for error in result["errors"]:
                    print(f"\n  约束 #{error['constraint_index']}:")
                    print(f"    conditional: {error['conditional']}")
                    print(f"    consequent: {error['consequent']}")
                    for err_msg in error["errors"]:
                        print(f"    {err_msg}")
        else:
            print(f"⚠️  {result['file']}: {result.get('error', 'Unknown error')}")

    # 汇总
    print(f"\n{'='*70}")
    print(" 检查汇总")
    print(f"{'='*70}")
    print(f"总文件数: {len(json_files)}")
    print(f"✅ 通过: {len(passed)}")
    print(f"❌ 失败: {len(failed)}")

    if failed:
        print(f"\n需要修正的文件:")
        for filename in failed:
            print(f"  - {filename}")

        # 生成修正建议
        print(f"\n{'='*70}")
        print(" 修正建议")
        print(f"{'='*70}")

        for result in results:
            if result["status"] == "failed":
                print(f"\n## {result['file']} ({result['construct']})")
                for error in result["errors"]:
                    print(f"\n约束 #{error['constraint_index']}:")
                    for err_msg in error["errors"]:
                        print(f"  {err_msg}")

        return 1
    else:
        print(f"\n🎉 所有文件检查通过！")
        return 0


if __name__ == "__main__":
    sys.exit(main())
