#!/usr/bin/env python3
"""
生成 Review 格式脚本

为人工审核生成人类可读的 Markdown 文件。

输入：{language}/data/cleaned/*.json
输出：{language}/data/review/*.md
"""

import os
import sys
import json
import argparse
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


def generate_review_markdown(data: Dict[str, Any], validation_warnings: List[Dict] = None) -> str:
    """
    为单个构造生成 Review 格式的 Markdown

    Args:
        data: 构造数据
        validation_warnings: 验证警告（如果有）

    Returns:
        Markdown 字符串
    """
    construct = data.get("construct", "Unknown")
    syntax_node = data.get("syntax_node", "")
    constraints = data.get("constraints", [])
    cleaning_stats = data.get("cleaning_stats", {})

    # 头部
    md = f"# {construct}\n\n"
    md += f"**语法节点**: `{syntax_node}`\n\n"
    md += f"**约束数**: {len(constraints)} 条\n\n"

    # 清洗信息
    if cleaning_stats:
        changes = cleaning_stats.get("changes", {})
        if any(changes.values()):
            md += f"**清洗状态**: ✅ 已清洗\n"
            change_msgs = []
            if changes.get("placeholders_normalized", 0) > 0:
                change_msgs.append(f"{changes['placeholders_normalized']} 处占位符标准化")
            if changes.get("consequents_split", 0) > 0:
                change_msgs.append(f"{changes['consequents_split']} 处拆分")
            if changes.get("notes_cleaned", 0) > 0:
                change_msgs.append(f"{changes['notes_cleaned']} 处 notes 清洗")
            md += f"- {', '.join(change_msgs)}\n\n"
        else:
            md += f"**清洗状态**: ✓ 无需清洗\n\n"

    # 验证警告
    if validation_warnings:
        md += f"**验证状态**: ⚠️ {len(validation_warnings)} 个警告\n\n"
        for warning in validation_warnings:
            md += f"### 警告 #{warning['constraint_index']}\n"
            md += f"- 规则: `{warning['conditional']} → {warning['consequent']}`\n"
            for w in warning['warnings']:
                md += f"- ⚠️ {w}\n"
            md += "\n"
    else:
        md += f"**验证状态**: ✅ 通过验证\n\n"

    # 约束列表
    md += "## 约束规则\n\n"
    md += "| # | Conditional | Consequent | Skip | Required | Note |\n"
    md += "|---|------------|------------|------|----------|------|\n"

    for i, c in enumerate(constraints, 1):
        conditional = c.get("conditional", "").replace("|", "\\|")
        consequent = c.get("consequent", "").replace("|", "\\|")
        skip = c.get("skip", "") or "-"
        required = "✅" if c.get("required", True) else "⭕"
        note = c.get("note", "").replace("|", "\\|").replace("\n", " ")

        # 检查是否有验证警告
        warning_marker = ""
        if validation_warnings:
            for w in validation_warnings:
                if w['constraint_index'] == i:
                    warning_marker = " ⚠️"
                    break

        md += f"| {i}{warning_marker} | `{conditional}` | `{consequent}` | `{skip}` | {required} | {note} |\n"

    # Review 问题
    md += "\n## Review 问题\n\n"
    md += "- [ ] 约束是否完整？有没有遗漏的语法路径？\n"
    md += "- [ ] 约束是否正确？有没有错误的规则？\n"
    md += "- [ ] Note 描述是否清晰？\n"
    md += "- [ ] 占位符使用是否恰当？\n"

    # 修改记录
    md += "\n## 修改记录\n\n"
    md += "| 日期 | 修改内容 | Reviewer |\n"
    md += "|------|---------|----------|\n"
    md += f"| {datetime.now().strftime('%Y-%m-%d')} | 初始提取（LLM + 后处理） | System |\n"

    return md


def generate_review_for_all(
    input_dir: str,
    validation_report: str = None,
    output_dir: str = None
) -> Dict[str, Any]:
    """
    为所有构造生成 Review 格式
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
           f.name != "deduplication_summary.json" and
           f.name != "validation_report.json"
    ]

    if not json_files:
        print_error(f"未找到构造文件: {input_dir}")
        sys.exit(1)

    # 加载验证报告（如果有）
    validation_data = {}
    if validation_report and Path(validation_report).exists():
        with open(validation_report, 'r') as f:
            report = json.load(f)
            for result in report.get("detailed_results", []):
                validation_data[result["file"]] = result.get("warnings", [])

    # 创建输出目录
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path(input_dir).parent / "review"

    output_path.mkdir(parents=True, exist_ok=True)

    print(f"{'='*70}")
    print(" 生成 Review 格式")
    print(f"{'='*70}")
    print(f"输入目录: {input_dir}")
    print(f"输出目录: {output_path}")
    print(f"构造数量: {len(json_files)}\n")

    generated = []
    skipped = []

    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print_error(f"✗ {json_file.name}: {e}")
            skipped.append(json_file.name)
            continue

        construct = data.get("construct", "Unknown")
        constraints = data.get("constraints", [])

        # 跳过空构造
        if len(constraints) == 0:
            print_warning(f"⊘ {json_file.name}: 无约束（跳过）")
            skipped.append(json_file.name)
            continue

        # 获取验证警告
        warnings = validation_data.get(json_file.name, [])

        # 生成 Markdown
        markdown = generate_review_markdown(data, warnings if warnings else None)

        # 保存
        output_file = output_path / f"{json_file.stem}.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown)

        status_marker = " ⚠️" if warnings else ""
        print_success(f"✓ {json_file.name}: {len(constraints)} 条规则{status_marker}")
        generated.append({
            "construct": construct,
            "file": json_file.name,
            "output_file": output_file.name,
            "constraint_count": len(constraints),
            "has_warnings": len(warnings) > 0,
            "warning_count": len(warnings)
        })

    # 生成索引文件
    index_path = output_path / "index.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(f"# 语法约束 Review 索引\n\n")
        f.write(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**语言**: {input_dir.split('/')[0]}\n\n")
        f.write(f"**总构造数**: {len(generated)}\n\n")
        f.write(f"**有警告的构造**: {sum(1 for g in generated if g['has_warnings'])}\n\n")

        f.write("## 所有构造\n\n")
        for g in sorted(generated, key=lambda x: x["construct"]):
            warning_marker = " ⚠️" if g["has_warnings"] else ""
            f.write(f"- [{g['construct']}]({g['output_file']}) - {g['constraint_count']} 条规则{warning_marker}\n")

        if skipped:
            f.write(f"\n## 跳过的构造（无约束）\n\n")
            for filename in skipped:
                f.write(f"- {filename}\n")

    print(f"\n{'='*70}")
    print(" 生成汇总")
    print(f"{'='*70}")
    print(f"生成文件数: {len(generated)}")
    print(f"跳过文件数: {len(skipped)}")
    print(f"有警告的构造: {sum(1 for g in generated if g['has_warnings'])}")

    print_success(f"Review 文件已保存: {output_path}")
    print_success(f"索引文件: {index_path}")

    return {
        "total_generated": len(generated),
        "total_skipped": len(skipped),
        "with_warnings": sum(1 for g in generated if g['has_warnings']),
        "generated": generated,
        "skipped": skipped
    }


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="生成 Review 格式"
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

    parser.add_argument(
        "--validation-report",
        type=str,
        default=None,
        help="验证报告路径（默认：{language}/data/cleaned/validation_report.json）"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认：{language}/data/review）"
    )

    args = parser.parse_args()

    # 确定目录
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = f"{args.language}/data/cleaned"

    if args.validation_report:
        validation_report = args.validation_report
    else:
        validation_report = f"{args.language}/data/cleaned/validation_report.json"

    if args.output_dir:
        output_dir = args.output_dir
    else:
        output_dir = f"{args.language}/data/review"

    # 运行生成
    try:
        result = generate_review_for_all(
            input_dir=input_dir,
            validation_report=validation_report,
            output_dir=output_dir
        )

        print(f"\n{GREEN}{'='*70}")
        print(" 生成完成！")
        print(f"{'='*70}{RESET}")

        return 0

    except KeyboardInterrupt:
        print_warning("\n\n用户中断")
        return 1

    except Exception as e:
        print_error(f"生成失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
