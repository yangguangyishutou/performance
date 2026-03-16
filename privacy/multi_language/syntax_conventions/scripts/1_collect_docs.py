#!/usr/bin/env python3
"""
Documentation Collection and Indexing Script

This script collects and indexes documentation for multiple programming languages:
- JavaScript: Index existing MDN documentation
- Java: Download Java Language Specification (JLS)
- C: Scrape cppreference.com

Usage:
    python scripts/1_collect_docs.py --language javascript
    python scripts/1_collect_docs.py --language all
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Try to import optional dependencies
try:
    from bs4 import BeautifulSoup
    import requests
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    print("Warning: beautifulsoup4 and requests not installed. Web scraping will be disabled.")


def should_ignore_construct(construct_name: str, file_path: str = "") -> bool:
    """
    检查构造是否应该被忽略（高熵运算符）

    Args:
        construct_name: 构造名称
        file_path: 文件路径（用于额外检查）

    Returns:
        True if should ignore, False otherwise
    """
    # 加载过滤配置
    filter_file = Path(__file__).parent / "operator_filter.json"
    if not filter_file.exists():
        return False

    with open(filter_file, 'r', encoding='utf-8') as f:
        filter_config = json.load(f)

    ignore_list = filter_config.get("ignore_list", [])

    # 检查构造名是否在忽略列表中
    construct_lower = construct_name.lower().replace(" ", "_")
    if construct_lower in ignore_list:
        return True

    # 检查文件路径是否包含忽略的运算符
    if file_path:
        for ignored in ignore_list:
            if f"/{ignored}/" in file_path.lower() or file_path.lower().startswith(f"{ignored}/"):
                return True

    return False


# ANSI color codes
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

# =============================================================================
# JavaScript Documentation Indexing
# =============================================================================

def extract_syntax_from_md(md_content: str) -> str:
    """
    Extract the syntax section from MDN markdown content.

    Args:
        md_content: Raw markdown content

    Returns:
        Extracted syntax section as string
    """
    # Find the Syntax section
    lines = md_content.split('\n')
    syntax_lines = []
    in_syntax_section = False
    in_code_block = False

    for i, line in enumerate(lines):
        # Check if we're entering the Syntax section
        if line.strip().startswith('## Syntax'):
            in_syntax_section = True
            continue

        # Check if we're leaving the Syntax section
        if in_syntax_section and line.strip().startswith('## '):
            if not line.strip().startswith('## Syntax'):
                break

        # Extract content within syntax section
        if in_syntax_section:
            # Track code blocks
            if line.strip().startswith('```'):
                in_code_block = not in_code_block

            syntax_lines.append(line)

    # Clean up the extracted syntax
    syntax_text = '\n'.join(syntax_lines).strip()

    # Remove empty lines at the start/end
    syntax_text = syntax_text.strip()

    return syntax_text

def infer_category_from_path(file_path: str) -> str:
    """
    Infer the 4-category classification from file path.

    Args:
        file_path: Path to markdown file

    Returns:
        One of: data_model, expressions, single_statements, compound_statements
    """
    path_lower = file_path.lower()

    # Expressions: operators, functions, template literals
    if any(x in path_lower for x in ['operators', 'template_literals', 'iteration_protocols']):
        return 'expressions'

    # Data Model: classes, regular expressions (as patterns)
    if 'classes' in path_lower:
        return 'compound_statements'  # Classes are compound in nature

    if 'regular_expressions' in path_lower:
        return 'expressions'  # Regex are expressions

    # Statements: split into single vs compound
    if 'statements' in path_lower:
        # Compound statements (control flow, blocks)
        compound_keywords = [
            'if', 'else', 'for', 'while', 'do', 'try', 'catch', 'finally',
            'switch', 'case', 'break', 'class', 'function', 'with'
        ]

        # Single statements (declarations, simple statements)
        single_keywords = [
            'var', 'let', 'const', 'return', 'throw', 'import', 'export',
            'debugger', 'empty', 'label', 'continue'
        ]

        for keyword in compound_keywords:
            if keyword in path_lower:
                return 'compound_statements'

        for keyword in single_keywords:
            if keyword in path_lower:
                return 'single_statements'

        # Default to compound for statements
        return 'compound_statements'

    # Default: expressions (most operators and built-ins)
    return 'expressions'

def extract_construct_name(md_content: str, file_path: str) -> str:
    """
    Extract the construct name from markdown content or filename.

    Args:
        md_content: Raw markdown content
        file_path: Path to file

    Returns:
        Construct name (e.g., "if...else", "while loop")
    """
    # Try to extract from frontmatter title
    title_match = re.search(r'^title:\s*(.+)$', md_content, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()

    # Fallback: extract from filename
    filename = Path(file_path).parent.name
    return filename.replace('_', ' ')

def index_javascript_docs(base_path: str = "js/reference") -> Dict[str, Any]:
    """
    Index existing JavaScript MDN documentation.

    Args:
        base_path: Base path to JS documentation

    Returns:
        Dictionary with indexed documentation
    """
    print_info(f"Indexing JavaScript documentation from {base_path}/")

    base_path = Path(base_path)
    if not base_path.exists():
        print_error(f"Path not found: {base_path}")
        return {}

    # Find all markdown files
    md_files = list(base_path.glob("**/*.md"))
    print_info(f"Found {len(md_files)} markdown files")

    # Index each file
    indexed_docs = {}
    categorized_docs = {
        "data_model": [],
        "expressions": [],
        "single_statements": [],
        "compound_statements": []
    }

    for md_file in md_files:
        try:
            # Read markdown content
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract metadata
            construct_name = extract_construct_name(content, str(md_file))

            # 检查是否应该忽略这个构造（高熵运算符）
            if should_ignore_construct(construct_name, str(md_file.relative_to(base_path))):
                print(f"  ⊗ Ignoring: {construct_name} (high-entropy operator)")
                continue

            # Extract syntax section
            syntax = extract_syntax_from_md(content)

            # Infer category
            category = infer_category_from_path(str(md_file))

            # Relative path from base
            rel_path = md_file.relative_to(base_path)

            # Store indexed data
            doc_data = {
                "file": str(rel_path),
                "full_path": str(md_file),
                "construct": construct_name,
                "category": category,
                "syntax": syntax,
                "has_syntax": len(syntax) > 0
            }

            indexed_docs[construct_name] = doc_data

            # Add to categorized list
            if doc_data["has_syntax"]:
                categorized_docs[category].append(doc_data)

        except Exception as e:
            print_warning(f"Failed to index {md_file}: {e}")
            continue

    # Print statistics
    print("\n=== JavaScript Documentation Statistics ===")
    total_with_syntax = sum(len(docs) for docs in categorized_docs.values())
    print_success(f"Total constructs indexed: {len(indexed_docs)}")
    print_success(f"Constructs with syntax: {total_with_syntax}")
    print("\nBy category:")
    for category, docs in categorized_docs.items():
        print(f"  - {category}: {len(docs)} constructs")

    return {
        "language": "javascript",
        "total_constructs": len(indexed_docs),
        "constructs_with_syntax": total_with_syntax,
        "index": indexed_docs,
        "by_category": categorized_docs
    }

# =============================================================================
# Java Documentation Collection
# =============================================================================

def collect_java_docs():
    """
    Collect Java Language Specification documentation.

    Note: This requires beautifulsoup4 and requests.
    For now, this is a placeholder that provides instructions.
    """
    if not BS4_AVAILABLE:
        print_warning("Web scraping not available. Please install beautifulsoup4 and requests.")

        print("\n=== Manual Java Documentation Collection ===")
        print("To collect Java Language Specification (JLS) documentation:")
        print("\n1. Download JLS chapters:")
        print("   - Chapter 4: https://docs.oracle.com/javase/specs/jls/se21/html/jls-4.html")
        print("   - Chapter 14: https://docs.oracle.com/javase/specs/jls/se21/html/jls-14.html")
        print("   - Chapter 15: https://docs.oracle.com/javase/specs/jls/se21/html/jls-15.html")
        print("\n2. Save HTML files to: data/raw/java/")
        print("\n3. Run the indexing step to parse HTML")

        return {
            "language": "java",
            "status": "manual_collection_required",
            "instructions": "Download JLS chapters manually from docs.oracle.com"
        }

    # TODO: Implement automated downloading and parsing
    print_info("Java documentation collection: To be implemented")
    return {}

# =============================================================================
# C Documentation Collection
# =============================================================================

def collect_c_docs():
    """
    Collect C language documentation from cppreference.com.

    Note: This requires beautifulsoup4 and requests.
    For now, this is a placeholder that provides instructions.
    """
    if not BS4_AVAILABLE:
        print_warning("Web scraping not available. Please install beautifulsoup4 and requests.")

        print("\n=== Manual C Documentation Collection ===")
        print("To collect C language reference documentation:")
        print("\n1. Visit: https://en.cppreference.com/w/c")
        print("\n2. Download key sections:")
        print("   - /language/basic_concepts")
        print("   - /language/expressions")
        print("   - /language/statements")
        print("   - /language/operators")
        print("\n3. Save HTML files to: data/raw/c/")

        return {
            "language": "c",
            "status": "manual_collection_required",
            "instructions": "Download C reference manually from cppreference.com"
        }

    # TODO: Implement automated scraping
    print_info("C documentation collection: To be implemented")
    return {}

# =============================================================================
# Python Reference Import
# =============================================================================

def import_python_reference():
    """
    Import existing Python constraint table.

    This is a placeholder for importing the user's Python table.
    """
    print_info("Python reference import: To be implemented")
    print_info("Please provide the Python constraint table (LaTeX or JSON format)")
    return {}

# =============================================================================
# Main Workflow
# =============================================================================

def save_index(data: Dict[str, Any], language: str):
    """Save indexed documentation to JSON file"""
    output_dir = Path("data/raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{language}_index.json"

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

    print_success(f"Saved index to: {output_file}")

    return output_file

def main():
    """Main documentation collection workflow"""
    parser = argparse.ArgumentParser(
        description="Collect and index programming language documentation"
    )
    parser.add_argument(
        "--language",
        choices=["javascript", "java", "c", "python", "all"],
        default="javascript",
        help="Language to collect documentation for"
    )
    parser.add_argument(
        "--js-path",
        default="js/reference",
        help="Path to JavaScript MDN documentation"
    )

    args = parser.parse_args()

    print("="*60)
    print(" Documentation Collection and Indexing")
    print("="*60)

    languages = args.language
    if languages == "all":
        languages = ["javascript", "java", "c", "python"]
    else:
        languages = [languages]

    for lang in languages:
        print(f"\n{'='*60}")
        print(f" Processing: {lang.upper()}")
        print(f"{'='*60}\n")

        if lang == "javascript":
            data = index_javascript_docs(args.js_path)
            if data:
                save_index(data, lang)

        elif lang == "java":
            data = collect_java_docs()
            if data:
                save_index(data, lang)

        elif lang == "c":
            data = collect_c_docs()
            if data:
                save_index(data, lang)

        elif lang == "python":
            data = import_python_reference()
            if data:
                save_index(data, lang)

    print("\n" + "="*60)
    print(" Documentation collection complete!")
    print("="*60)

if __name__ == "__main__":
    main()
