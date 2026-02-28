#!/usr/bin/env python3
"""
Environment Setup and Validation Script

This script validates that all required dependencies are installed and
configured for the multi-language syntax constraint extraction system.

Usage:
    python scripts/0_setup_env.py
"""

import os
import sys
import subprocess
import json
from pathlib import Path

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")

def check_python_version():
    """Check Python version (requires 3.8+)"""
    print("\n=== Checking Python Version ===")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}")
        return False

def check_package(package_name, import_name=None):
    """Check if a Python package is installed"""
    if import_name is None:
        import_name = package_name

    try:
        __import__(import_name)
        print_success(f"{package_name} is installed")
        return True
    except ImportError:
        print_error(f"{package_name} is NOT installed")
        return False

def check_tree_sitter_languages():
    """Check if Tree-sitter language parsers are installed"""
    print("\n=== Checking Tree-sitter Language Parsers ===")

    languages = {
        'python': 'tree_sitter_python',
        'javascript': 'tree_sitter_javascript',
        'java': 'tree_sitter_java',
        'c': 'tree_sitter_c'
    }

    all_installed = True
    for lang, package in languages.items():
        try:
            mod = __import__(package)
            print_success(f"tree-sitter-{lang} ({package})")
        except ImportError:
            print_error(f"tree-sitter-{lang} ({package}) NOT installed")
            all_installed = False

    return all_installed

def check_api_keys():
    """Check if LLM API keys are configured"""
    print("\n=== Checking API Keys ===")

    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if openai_key:
        print_success("LLM API key found (OPENAI_API_KEY or ANTHROPIC_API_KEY)")
        return True
    else:
        print_warning("No LLM API key found in environment")
        print_warning("Set OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable")
        return False

def verify_tree_sitter_parsers():
    """Test Tree-sitter parsers for all languages"""
    print("\n=== Testing Tree-sitter Parsers ===")

    try:
        from tree_sitter import Language, Parser
        import tree_sitter_python
        import tree_sitter_javascript
        import tree_sitter_java
        import tree_sitter_c

        languages = {
            'python': tree_sitter_python.language(),
            'javascript': tree_sitter_javascript.language(),
            'java': tree_sitter_java.language(),
            'c': tree_sitter_c.language()
        }

        for lang, lang_obj in languages.items():
            try:
                parser = Parser(Language(lang_obj))
                print_success(f"Created parser for {lang}")
            except Exception as e:
                print_error(f"Failed to create parser for {lang}: {e}")
                return False

        return True
    except ImportError as e:
        print_error(f"Tree-sitter import failed: {e}")
        return False

def create_directories():
    """Create required directories"""
    print("\n=== Creating Directories ===")

    directories = [
        "scripts/utils",
        "prompts",
        "data/raw",
        "data/extracted",
        "data/validated",
        "data/final",
        "logs"
    ]

    for directory in directories:
        path = Path(directory)
        if path.exists():
            print_success(f"Directory exists: {directory}/")
        else:
            try:
                path.mkdir(parents=True, exist_ok=True)
                print_success(f"Created directory: {directory}/")
            except Exception as e:
                print_error(f"Failed to create {directory}/: {e}")
                return False

    return True

def install_dependencies():
    """Show command to install dependencies"""
    print("\n=== Installation Instructions ===")
    print("\nTo install missing dependencies, run:")
    print("\n" + YELLOW + "pip install tree-sitter" + RESET)
    print(YELLOW + "pip install tree-sitter-python tree-sitter-javascript tree-sitter-java tree-sitter-c" + RESET)
    print(YELLOW + "pip install openai anthropic beautifulsoup4 lxml requests jinja2" + RESET)

    print("\nOr install all at once:")
    print(YELLOW + "pip install tree-sitter tree-sitter-python tree-sitter-javascript " +
          "tree-sitter-java tree-sitter-c openai anthropic beautifulsoup4 lxml requests jinja2" + RESET)

def generate_setup_report(results):
    """Generate setup report"""
    print("\n=== Setup Report ===")

    report = {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "checks": results,
        "overall_status": "PASS" if all(results.values()) else "FAIL"
    }

    # Save report
    report_path = Path("logs/setup_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\nReport saved to: {report_path}")

    if report["overall_status"] == "PASS":
        print_success("All checks passed! Environment is ready.")
        return True
    else:
        print_error("Some checks failed. Please install missing dependencies.")
        return False

def main():
    """Main setup workflow"""
    print("="*60)
    print(" Multi-Language Syntax Constraint Extraction")
    print(" Environment Setup and Validation")
    print("="*60)

    results = {}

    # Check Python version
    results["python_version"] = check_python_version()

    # Check required packages
    print("\n=== Checking Python Packages ===")
    packages = [
        ("tree-sitter", "tree_sitter"),
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("beautifulsoup4", "bs4"),
        ("lxml", "lxml"),
        ("requests", "requests"),
        ("jinja2", "jinja2")
    ]

    packages_ok = True
    for package, import_name in packages:
        if not check_package(package, import_name):
            packages_ok = False

    results["packages"] = packages_ok

    # Check Tree-sitter language parsers
    results["tree_sitter_languages"] = check_tree_sitter_languages()

    # Verify Tree-sitter parsers work
    if results["tree_sitter_languages"]:
        results["parser_verification"] = verify_tree_sitter_parsers()
    else:
        results["parser_verification"] = False

    # Check API keys (optional but recommended)
    results["api_keys"] = check_api_keys()

    # Create directories
    results["directories"] = create_directories()

    # Generate report
    success = generate_setup_report(results)

    # Show installation instructions if needed
    if not success:
        install_dependencies()
        sys.exit(1)
    else:
        print("\n" + "="*60)
        print(" Setup complete! You can now run the next script.")
        print("="*60)
        sys.exit(0)

if __name__ == "__main__":
    main()
