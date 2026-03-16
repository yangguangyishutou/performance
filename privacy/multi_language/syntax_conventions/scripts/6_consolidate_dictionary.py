#!/usr/bin/env python3
"""
合并语法约束字典脚本

将所有构造文件合并为最终字典格式供模型使用。

输出格式：
{
  "language": "javascript",
  "version": "1.0",
  "metadata": {...},
  "dictionary": {
    "if": {
      "trigger_tokens": ["if"],
      "constraints": [...]
    },
    ...
  }
}

输入：{language}/data/cleaned/*.json（或 validated/）
输出：{language}/data/final/{language}_constraints.json
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
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


def extract_syntax_node(construct_data: Dict[str, Any]) -> str:
    """
    从构造数据中提取 syntax_node

    作为字典的键和 trigger_tokens
    """
    syntax_node = construct_data.get("syntax_node", "")

    # 如果没有 syntax_node，尝试从 construct 名称推断
    if not syntax_node:
        construct = construct_data.get("construct", "")
        # 简单的启发式规则
        if " " in construct:
            # 取第一个单词
            syntax_node = construct.split()[0]
        else:
            syntax_node = construct

    return syntax_node


def consolidate_constraints(
    input_dir: str,
    output_file: str
) -> Dict[str, Any]:
    """
    合并所有构造约束为最终字典
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

    print(f"{'='*70}")
    print(" 合并语法约束字典")
    print(f"{'='*70}")
    print(f"输入目录: {input_dir}")
    print(f"输出文件: {output_file}")
    print(f"构造数量: {len(json_files)}\n")

    # 按syntax_node分组
    dictionary = {}
    total_constraints = 0

    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print_error(f"无法读取文件 {json_file.name}: {e}")
            continue

        construct = data.get("construct", "Unknown")
        constraints = data.get("constraints", [])
        total_constraints += len(constraints)

        # 提取 syntax_node
        syntax_node = extract_syntax_node(data)

        # 收集所有触发该构造的 token
        # 从所有 conditional 中提取第一个 token
        trigger_tokens = set()
        for c in constraints:
            conditional = c.get("conditional", "").strip()
            if conditional:
                # 提取第一个 token（简单处理：取第一个单词或符号）
                # 例如：从 "if (" 提取 "if"
                # 从 "async (" 提取 "async"
                # 从 "[IDENT]" 提取 "[IDENT]"
                first_token = conditional.split()[0] if conditional.split() else conditional
                trigger_tokens.add(first_token)

        # 构建 dictionary 条目
        dictionary[syntax_node] = {
            "construct": construct,
            "trigger_tokens": sorted(list(trigger_tokens)),
            "constraints": constraints
        }

        print_success(f"✓ {construct}: {len(constraints)} 条规则, syntax_node='{syntax_node}'")

    # 构建最终输出
    language = input_dir.split('/')[0]

    output_data = {
        "language": language,
        "version": "1.0",
        "generated_at": datetime.now().isoformat(),
        "metadata": {
            "total_constructs": len(dictionary),
            "total_constraints": total_constraints,
            "source": "MDN Web Docs",
            "extraction_method": "LLM (Zhipu AI) + Post-processing",
            "processing_steps": [
                "1. LLM extraction (batch mode)",
                "2. Deduplication",
                "3. Cleaning",
                "4. Validation",
                "5. Consolidation"
            ]
        },
        "dictionary": dictionary
    }

    # 确保输出目录存在
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # 保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*70}")
    print(" 合并汇总")
    print(f"{'='*70}")
    print(f"总构造数: {len(dictionary)}")
    print(f"总约束数: {total_constraints}")
    print(f"平均约束数: {total_constraints / len(dictionary):.1f}")

    # 统计信息
    constraint_counts = [len(v["constraints"]) for v in dictionary.values()]
    print(f"\n约束数分布:")
    print(f"  最少: {min(constraint_counts)}")
    print(f"  最多: {max(constraint_counts)}")
    print(f"  中位数: {sorted(constraint_counts)[len(constraint_counts)//2]}")

    print_success(f"\n字典已保存: {output_file}")

    return output_data


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="合并语法约束字典"
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
        "--output-file",
        type=str,
        default=None,
        help="输出文件（默认：{language}/data/final/{language}_constraints.json）"
    )

    args = parser.parse_args()

    # 确定目录
    if args.input_dir:
        input_dir = args.input_dir
    else:
        input_dir = f"{args.language}/data/cleaned"

    if args.output_file:
        output_file = args.output_file
    else:
        output_file = f"{args.language}/data/final/{args.language}_constraints.json"

    # 运行合并
    try:
        output_data = consolidate_constraints(input_dir, output_file)

        print(f"\n{GREEN}{'='*70}")
        print(" 合并完成！")
        print(f"{'='*70}{RESET}")

        return 0

    except KeyboardInterrupt:
        print_warning("\n\n用户中断")
        return 1

    except Exception as e:
        print_error(f"合并失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
