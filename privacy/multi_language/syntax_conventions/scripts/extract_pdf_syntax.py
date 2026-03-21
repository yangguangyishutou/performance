#!/usr/bin/env python3
"""
PDF 语法附录章节分割脚本

将编程语言官方文档的语法附录 PDF 按章节分割为 txt 文件。
依赖：pdftotext（poppler-utils）

用法：
    python scripts/extract_pdf_syntax.py --language c
    python scripts/extract_pdf_syntax.py --language java
"""

import re
import sys
import json
import argparse
import subprocess
from pathlib import Path

# 各语言保留的章节
KEEP_SECTIONS = {
    "c": ["A.3.1", "A.3.2", "A.3.3", "A.4"],
    "java": ["§4", "§6", "§7", "§8", "§9", "§10", "§14", "§15"]
}

# PDF 文件名
PDF_FILES = {
    "c": "BS_ISO_IEC_9899_2024_Annex_A.pdf",
    "java": "The Java® Language Specification, Java SE 24 - Syntax.pdf"
}


def extract_pdf_text(pdf_path: Path) -> str:
    """使用 pdftotext 提取 PDF 文本"""
    result = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"pdftotext 失败: {result.stderr}")
    return result.stdout


def split_c_sections(text: str) -> dict:
    """按 A.X.X 标题分割 C 语法章节"""
    sections = {}
    # 匹配 A.3.1, A.3.2, A.4 等标题
    pattern = re.compile(r'^(A\.\d+(?:\.\d+)?)\s+(.+)$', re.MULTILINE)
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        section_id = match.group(1)
        section_name = match.group(2).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        if any(section_id.startswith(k) for k in KEEP_SECTIONS["c"]):
            key = f"{section_id}_{section_name.replace(' ', '_').replace('/', '_')}"
            sections[key] = {"id": section_id, "name": section_name, "content": content}

    return sections


def split_java_sections(text: str) -> dict:
    """按 'Productions from §X' 标题分割 Java 语法章节"""
    sections = {}
    pattern = re.compile(r'Productions from (§\d+)', re.MULTILINE)
    matches = list(pattern.finditer(text))

    for i, match in enumerate(matches):
        section_id = match.group(1)
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        if section_id in KEEP_SECTIONS["java"]:
            # 从内容第一行提取章节名
            first_line = content.split('\n')[0].strip()
            name = first_line.replace(f"Productions from {section_id}", "").strip()
            if not name:
                name = section_id
            key = f"{section_id.replace('§', 'S')}_{name.replace(' ', '_').replace(',', '')}"
            sections[key] = {"id": section_id, "name": name, "content": content}

    return sections


def main():
    parser = argparse.ArgumentParser(description="将 PDF 语法附录按章节分割为 txt 文件")
    parser.add_argument("--language", choices=["c", "java"], required=True)
    args = parser.parse_args()

    lang = args.language
    docs_dir = Path(f"{lang}/docs")
    pdf_path = docs_dir / PDF_FILES[lang]

    if not pdf_path.exists():
        print(f"错误: 找不到 PDF 文件: {pdf_path}")
        return 1

    print(f"提取 PDF 文本: {pdf_path.name}")
    text = extract_pdf_text(pdf_path)

    print("分割章节...")
    if lang == "c":
        sections = split_c_sections(text)
    else:
        sections = split_java_sections(text)

    # 保存章节 txt
    saved = []
    for key, section in sections.items():
        out_file = docs_dir / f"{lang}_{key}.txt"
        out_file.write_text(section["content"], encoding="utf-8")
        saved.append({"id": section["id"], "name": section["name"], "file": out_file.name})
        print(f"  ✓ {out_file.name}")

    # 保存章节索引
    index_file = docs_dir / f"{lang}_sections_index.json"
    with open(index_file, 'w', encoding='utf-8') as f:
        json.dump({"language": lang, "sections": saved}, f, ensure_ascii=False, indent=2)

    print(f"\n✓ 共提取 {len(saved)} 个章节，索引保存到 {index_file}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
