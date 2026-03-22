#!/usr/bin/env python3
"""
将 C/Java 的 PDF 章节文本解析成统一的 index.json 格式

输入：{language}/syntax_sections/*.txt
输出：{language}/{language}_index.json

将章节拆分成单个语法规则（构造级），与 JS 对齐
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path

def parse_c_rules(content: str) -> dict:
    """
    解析 C 语言 BNF 规则，拆分成单个构造

    格式：(6.8.1) statement:
              labeled-statement
              unlabeled-statement
    """
    constructs = {}

    # 匹配规则：(章节号) 规则名: ... 直到下一个规则或文件结束
    pattern = r'\([\d.]+\)\s+([a-zA-Z_][\w-]*)\s*:\s*(.*?)(?=\n\s*\([\d.]+\)|$)'

    matches = re.finditer(pattern, content, re.DOTALL)

    for match in matches:
        rule_name = match.group(1).strip()
        rule_body = match.group(2).strip()

        # 跳过空规则
        if not rule_body:
            continue

        # 跳过 "one of" 纯枚举规则（lexical）
        if "one of" in rule_body and not any(kw in rule_body for kw in ["(", ")", "{", "}", "[", "]", "if", "for", "while", "switch"]):
            continue

        constructs[rule_name] = {
            "syntax": f"({rule_name}):\n{rule_body}",
            "has_syntax": True
        }

    return constructs

def parse_java_rules(content: str) -> dict:
    """
    解析 Java 语言 BNF 规则，拆分成单个构造

    格式：
       RuleName:
         Production1
         Production2
    """
    constructs = {}

    # 按空行分割，每个块可能是一个规则
    blocks = re.split(r'\n\s*\n', content)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        # 匹配规则名（首字母大写，后跟冒号）
        match = re.match(r'^([A-Z][a-zA-Z0-9]*)\s*:\s*(.*)$', block, re.DOTALL)
        if not match:
            continue

        rule_name = match.group(1).strip()
        rule_body = match.group(2).strip()

        if not rule_body:
            continue

        # 跳过纯 lexical 规则（只有 "one of" 列表，没有结构符号）
        if "one of" in rule_body and not any(kw in rule_body for kw in ["(", ")", "{", "}", "[", "]", "class", "interface", "if", "for", "while"]):
            continue

        constructs[rule_name] = {
            "syntax": f"{rule_name}:\n{rule_body}",
            "has_syntax": True
        }

    return constructs

def parse_c_sections(sections_dir: Path) -> dict:
    """解析 C 语言所有章节，提取所有构造"""
    all_constructs = {}

    for section_file in sorted(sections_dir.glob("c_*.txt")):
        if section_file.name == "c_sections_index.json":
            continue

        with open(section_file, 'r', encoding='utf-8') as f:
            content = f.read()

        section_constructs = parse_c_rules(content)

        # 添加章节前缀避免重名
        section_name = section_file.stem.replace("c_", "")
        for rule_name, rule_data in section_constructs.items():
            # 使用原始规则名，不加前缀（C的规则名全局唯一）
            all_constructs[rule_name] = rule_data

    return all_constructs

def parse_java_sections(sections_dir: Path) -> dict:
    """解析 Java 语言所有章节，提取所有构造"""
    all_constructs = {}

    for section_file in sorted(sections_dir.glob("java_*.txt")):
        if section_file.name == "java_sections_index.json":
            continue

        with open(section_file, 'r', encoding='utf-8') as f:
            content = f.read()

        section_constructs = parse_java_rules(content)

        for rule_name, rule_data in section_constructs.items():
            all_constructs[rule_name] = rule_data

    return all_constructs

def main():
    parser = argparse.ArgumentParser(description="将 PDF 章节解析成 index.json")
    parser.add_argument("--language", choices=["c", "java"], required=True)
    args = parser.parse_args()

    sections_dir = Path(f"{args.language}/docs")
    if not sections_dir.exists():
        print(f"错误: {sections_dir} 不存在")
        print(f"请先运行: python scripts/extract_pdf_syntax.py --language {args.language}")
        return 1

    # 解析章节
    if args.language == "c":
        constructs = parse_c_sections(sections_dir)
    else:
        constructs = parse_java_sections(sections_dir)

    # 生成 index
    index = {
        "language": args.language,
        "total_constructs": len(constructs),
        "constructs_with_syntax": len(constructs),
        "index": constructs
    }

    # 保存
    output_file = Path(f"{args.language}/{args.language}_index.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    print(f"✓ 生成 {output_file}")
    print(f"  总构造数: {len(constructs)}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
