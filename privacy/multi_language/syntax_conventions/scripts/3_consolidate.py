#!/usr/bin/env python3
"""
统一的约束合并验证脚本

读取 {language}/extracted/*.json
自动过滤、验证、合并
输出 {language}/constraints.json
"""

import os
import sys
import json
import argparse
from pathlib import Path


def validate_bracket_matching(s: str) -> tuple:
    """验证 conditional 中的括号类型匹配（允许未闭合左括号和单独右括号）"""
    stack = []
    bracket_pairs = {')': '(', ']': '[', '}': '{'}
    for i, char in enumerate(s):
        if char in '([{':
            stack.append((char, i))
        elif char in ')]}':
            if stack:
                if stack[-1][0] != bracket_pairs[char]:
                    return False, f"位置 {i}: '{char}' 与 '{stack[-1][0]}' 类型不匹配"
                stack.pop()
    return True, ""


def check_constraint_pair(constraint: dict, language: str) -> list:
    """检查单个约束对，返回问题列表"""
    issues = []
    conditional = constraint.get("conditional", "")
    consequent = constraint.get("consequent", "")

    # 检查括号类型不匹配
    is_valid, msg = validate_bracket_matching(conditional)
    if not is_valid:
        issues.append(f"conditional 括号类型不匹配: {msg}")

    # 检查 conditional 包含抽象占位符
    for placeholder in ["statement", "expression", "block"]:
        if placeholder in conditional.lower():
            special = f"<{placeholder}_start>"
            if special not in conditional.lower():
                issues.append(f"conditional 包含抽象占位符 '{placeholder}'")

    # JS 特定：getter/setter 后不能用圆括号
    if language == "javascript" and conditional in ["get", "set"]:
        parts = [p.strip() for p in consequent.split(",")]
        if any(p == "(" or (p.endswith("(") and not p.startswith("<")) for p in parts):
            issues.append("getter/setter 计算属性名必须使用方括号 [")

    # JS 特定：Rest 参数后不能跟逗号
    if language == "javascript" and "Rest parameter" in constraint.get("construct", ""):
        if "..." in conditional and "," in consequent:
            issues.append("Rest 参数后不能跟逗号")

    return issues


def load_extracted(language: str) -> list:
    extracted_dir = Path(f"{language}/extracted")
    if not extracted_dir.exists():
        print(f"错误: {extracted_dir} 不存在")
        return []
    result = []
    for file in extracted_dir.glob("*.json"):
        with open(file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "constraints" in data and isinstance(data["constraints"], list):
                result.append(data)
    return result


def main():
    parser = argparse.ArgumentParser(description="合并验证约束")
    parser.add_argument("--language", required=True, choices=["javascript", "c", "java"])
    args = parser.parse_args()

    print(f"处理 {args.language}...")

    all_data = load_extracted(args.language)
    print(f"✓ 加载 {len(all_data)} 个构造")

    # 过滤空约束
    filtered = [c for c in all_data if c.get("constraints")]
    print(f"✓ 过滤空约束: 移除 {len(all_data) - len(filtered)} 个，剩余 {len(filtered)} 个构造")

    # 验证
    result = []
    total_before = total_after = 0
    for construct in filtered:
        total_before += len(construct.get("constraints", []))
        valid = [c for c in construct["constraints"]
                 if not check_constraint_pair({**c, "construct": construct["construct"]}, args.language)]
        total_after += len(valid)
        if valid:
            result.append({
                "construct": construct["construct"],
                "language": construct["language"],
                "syntax_node": construct.get("syntax_node", ""),
                "constraints": valid
            })

    print(f"✓ 验证后: {total_after}/{total_before} 个约束对，{len(result)} 个构造")

    output_file = Path(f"{args.language}/constraints.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "language": args.language,
            "total_constructs": len(result),
            "total_constraints": total_after,
            "constructs": result
        }, f, ensure_ascii=False, indent=2)

    print(f"✓ 保存到 {output_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
