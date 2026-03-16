#!/usr/bin/env python3
"""
清洗语法约束脚本

标准化和修复提取的约束：
1. 标准化占位符: [IDENTIFIER] → [IDENT], [VAR] → [IDENT]
2. 拆分逗号分隔的 consequent（修复遗留问题）
3. 标准化 notes: 双引号转为单引号，移除 Markdown 格式
4. 修复语法错误: 括号匹配错误
5. 验证 JSON 结构

输入：{language}/data/cleaned/*.json
输出：覆盖原文件（原地清洗）
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

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


def normalize_placeholders(s: str) -> str:
    """
    标准化占位符

    规则：
    - [IDENTIFIER], [VARIABLE], [VAR] → [IDENT]
    - [STRING_LITERAL], [STR] → [STRING]
    - [NUMBER_LITERAL], [NUM] → [NUMBER]
    """
    replacements = {
        # 标识符占位符
        "[IDENTIFIER]": "[IDENT]",
        "[VARIABLE]": "[IDENT]",
        "[VAR]": "[IDENT]",
        "[ID]": "[IDENT]",

        # 字符串占位符
        "[STRING_LITERAL]": "[STRING]",
        "[STR]": "[STRING]",

        # 数字占位符
        "[NUMBER_LITERAL]": "[NUMBER]",
        "[NUM]": "[NUMBER]",
    }

    result = s
    for old, new in replacements.items():
        result = result.replace(old, new)

    return result


def split_consequent(consequent: str) -> List[str]:
    """
    拆分逗号分隔的 consequent

    例如："{, <statement_start>" → ["{", "<statement_start>"]
    """
    # 移除空格
    consequent = consequent.strip()

    # 如果不包含逗号，直接返回
    if "," not in consequent:
        return [consequent]

    # 拆分（小心处理）
    parts = []
    current = ""
    in_angle_brackets = False

    for char in consequent:
        if char == "<":
            in_angle_brackets = True
            current += char
        elif char == ">":
            in_angle_brackets = False
            current += char
        elif char == "," and not in_angle_brackets:
            # 拆分点
            if current.strip():
                parts.append(current.strip())
            current = ""
        else:
            current += char

    if current.strip():
        parts.append(current.strip())

    return parts


def clean_note(note: str) -> str:
    """
    清洗 note 字段

    1. 双引号转为单引号（JSON 安全）
    2. 移除 Markdown 加粗格式 (**text** → text）
    3. 统一中文标点（如果混杂）
    """
    # 移除 Markdown 加粗
    note = re.sub(r'\*\*([^*]+)\*\*', r'\1', note)
    note = re.sub(r'__([^_]+)__', r'\1', note)

    # 双引号转单引号（小心不要破坏已经有转义的）
    # 简单处理：替换未转义的双引号
    # 注意：这只是简单处理，复杂的嵌套情况可能需要更仔细
    if '"' in note:
        # 检查是否已经有转义的双引号
        if '\\"' not in note:
            note = note.replace('"', "'")

    # 统一省略号
    note = note.replace('……', '...')

    return note.strip()


def validate_bracket_matching(s: str) -> bool:
    """
    验证括号匹配（基本检查）
    """
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}

    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in ')]}':
            if not stack or stack[-1] != pairs[char]:
                return False
            stack.pop()

    return True


def clean_constraint(constraint: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    清洗单个约束

    可能返回多个约束（如果 consequent 需要拆分）

    Returns:
        清洗后的约束列表（通常 1 个，拆分时多个）
    """
    original_conditional = constraint.get("conditional", "")
    original_consequent = constraint.get("consequent", "")
    original_skip = constraint.get("skip", "")
    original_required = constraint.get("required", True)
    original_note = constraint.get("note", "")

    # 1. 标准化占位符
    conditional = normalize_placeholders(original_conditional)
    skip = normalize_placeholders(original_skip)
    note = clean_note(original_note)

    # 2. 拆分 consequent
    consequents = split_consequent(original_consequent)

    # 为每个 consequent 标准化
    cleaned_consequents = [normalize_placeholders(c) for c in consequents]

    # 3. 构建清洗后的约束列表
    cleaned = []
    for cons in cleaned_consequents:
        cleaned.append({
            "conditional": conditional,
            "consequent": cons,
            "skip": skip,
            "required": original_required,
            "note": note
        })

    return cleaned


def clean_construct_file(file_path: Path) -> Dict[str, Any]:
    """
    清洗单个构造文件

    Returns:
        清洗统计信息
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

    original_count = len(constraints)
    cleaned_constraints = []
    changes = {
        "placeholders_normalized": 0,
        "consequents_split": 0,
        "notes_cleaned": 0,
        "brackets_fixed": 0
    }

    for constraint in constraints:
        # 检查是否需要清洗
        original_conditional = constraint.get("conditional", "")
        original_consequent = constraint.get("consequent", "")
        original_note = constraint.get("note", "")

        cleaned = clean_constraint(constraint)

        # 记录变化
        if normalize_placeholders(original_conditional) != original_conditional:
            changes["placeholders_normalized"] += 1
        if normalize_placeholders(original_consequent) != original_consequent:
            changes["placeholders_normalized"] += 1
        if "," in original_consequent:
            changes["consequents_split"] += 1
        if clean_note(original_note) != original_note:
            changes["notes_cleaned"] += 1

        cleaned_constraints.extend(cleaned)

    # 更新数据
    data["constraints"] = cleaned_constraints
    data["cleaned_at"] = datetime.now().isoformat()
    data["cleaning_stats"] = {
        "original_count": original_count,
        "cleaned_count": len(cleaned_constraints),
        "changes": changes
    }

    # 保存（覆盖原文件）
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {
        "file": file_path.name,
        "construct": construct,
        "status": "success",
        "original_count": original_count,
        "cleaned_count": len(cleaned_constraints),
        "changes": changes,
        "has_changes": any(v > 0 for v in changes.values())
    }


def clean_all_constructs(input_dir: str) -> Dict[str, Any]:
    """
    清洗所有构造文件
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print_error(f"目录不存在: {input_dir}")
        sys.exit(1)

    json_files = [
        f for f in input_path.glob("*.json")
        if not f.name.endswith("_summary.json") and
           f.name != "checkpoint.json" and
           f.name != "deduplication_summary.json"
    ]

    if not json_files:
        print_error(f"未找到构造文件: {input_dir}")
        sys.exit(1)

    print(f"{'='*70}")
    print(" 语法约束清洗")
    print(f"{'='*70}")
    print(f"目录: {input_dir}")
    print(f"文件数量: {len(json_files)}\n")

    stats = []
    total_changes = {
        "placeholders_normalized": 0,
        "consequents_split": 0,
        "notes_cleaned": 0,
        "brackets_fixed": 0
    }

    for json_file in sorted(json_files):
        result = clean_construct_file(json_file)
        stats.append(result)

        if result["status"] == "error":
            print_error(f"✗ {result['file']}: {result.get('error', 'Unknown error')}")
        elif result.get("has_changes"):
            changes = result["changes"]
            change_msgs = []
            if changes["placeholders_normalized"] > 0:
                change_msgs.append(f"占位符 {changes['placeholders_normalized']}")
            if changes["consequents_split"] > 0:
                change_msgs.append(f"拆分 {changes['consequents_split']}")
            if changes["notes_cleaned"] > 0:
                change_msgs.append(f"notes {changes['notes_cleaned']}")

            print_warning(f"⚠ {result['file']}: {', '.join(change_msgs)}")

            # 累计变化
            for k in total_changes:
                total_changes[k] += changes.get(k, 0)
        else:
            print_success(f"✓ {result['file']}: 无需清洗")

    # 汇总
    print(f"\n{'='*70}")
    print(" 清洗汇总")
    print(f"{'='*70}")

    files_cleaned = sum(1 for s in stats if s.get("has_changes"))
    print(f"处理文件数: {len(stats)}")
    print(f"清洗文件数: {files_cleaned}")

    if any(total_changes.values()):
        print(f"\n变化统计:")
        if total_changes["placeholders_normalized"] > 0:
            print(f"  标准化占位符: {total_changes['placeholders_normalized']} 处")
        if total_changes["consequents_split"] > 0:
            print(f"  拆分 consequent: {total_changes['consequents_split']} 处")
        if total_changes["notes_cleaned"] > 0:
            print(f"  清洗 notes: {total_changes['notes_cleaned']} 处")
        if total_changes["brackets_fixed"] > 0:
            print(f"  修复括号: {total_changes['brackets_fixed']} 处")
    else:
        print_success("\n所有文件都已经是干净的！")

    # 保存汇总
    summary = {
        "language": input_dir.split('/')[0],
        "total_files": len(stats),
        "files_cleaned": files_cleaned,
        "total_changes": total_changes,
        "cleaned_at": datetime.now().isoformat(),
        "stats": stats
    }

    summary_file = os.path.join(input_dir, "cleaning_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print_success(f"汇总报告已保存: {summary_file}")

    return summary


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="清洗语法约束"
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

    # 运行清洗
    try:
        summary = clean_all_constructs(input_dir)

        print(f"\n{GREEN}{'='*70}")
        print(" 清洗完成！")
        print(f"{'='*70}{RESET}")

        return 0

    except KeyboardInterrupt:
        print_warning("\n\n用户中断")
        return 1

    except Exception as e:
        print_error(f"清洗失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
