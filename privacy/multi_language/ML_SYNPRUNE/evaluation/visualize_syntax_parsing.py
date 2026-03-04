"""
HTML visualization generator for two-layer syntax classification.

This script generates interactive HTML visualizations showing how the two-layer
classification process works on code samples.
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.syntax_parser import TreeSitterSyntaxParser, NodeClassification
except ImportError:
    print("Error: Cannot import syntax_parser. Make sure tree-sitter is installed.")
    sys.exit(1)


def generate_html_header(title: str) -> str:
    """Generate HTML header with CSS styles."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + title + """</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f7fa;
            padding: 20px;
        }

        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            padding: 30px;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
        }

        .header h1 {
            font-size: 2.2em;
            color: #2c3e50;
            margin-bottom: 10px;
        }

        .header .meta {
            color: #7f8c8d;
            font-size: 1em;
        }

        .sample-info {
            background: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 4px;
        }

        .section {
            margin-bottom: 35px;
        }

        .section-title {
            font-size: 1.4em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
            display: flex;
            align-items: center;
        }

        .section-title .step-number {
            background: #3498db;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            margin-right: 12px;
            font-weight: bold;
        }

        .section-title .step-number.step-1 { background: #3498db; }
        .section-title .step-number.step-2 { background: #e67e22; }
        .section-title .step-number.step-3 { background: #e74c3c; }

        .section-description {
            color: #7f8c8d;
            margin-bottom: 15px;
            font-size: 0.95em;
            line-height: 1.5;
        }

        .tree-extract {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            max-height: 300px;
            overflow-y: auto;
        }

        .tree-node {
            padding: 4px 0;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 13px;
            border-left: 2px solid #dee2e6;
            padding-left: 15px;
            margin-left: 10px;
        }

        .tree-node.named {
            border-left-color: #27ae60;
            background: rgba(39, 174, 96, 0.05);
        }

        .tree-node.anonymous {
            border-left-color: #f39c12;
            background: rgba(243, 156, 18, 0.05);
        }

        .tree-node .node-type {
            color: #8e44ad;
            font-weight: 600;
        }

        .tree-node .node-text {
            color: #2c3e50;
        }

        .filter-stage {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }

        .filter-box {
            background: #fff;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
        }

        .filter-box h4 {
            color: #2c3e50;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid #ecf0f1;
        }

        .filter-item {
            display: flex;
            align-items: center;
            padding: 6px 0;
            font-size: 13px;
        }

        .filter-item .category-badge {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-right: 10px;
            min-width: 80px;
            text-align: center;
        }

        .category-named { background: #d4edda; color: #155724; }
        .category-anonymous { background: #fff3cd; color: #856404; }
        .category-keyword { background: #d1ecf1; color: #0c5460; }
        .category-operator { background: #e2e3e5; color: #383d41; }
        .category-delimiter { background: #f8d7da; color: #721c24; }
        .category-whitespace { background: #e2e6ea; color: #6c757d; font-style: italic; }

        .filter-item .node-text {
            font-family: 'Consolas', monospace;
            color: #2c3e50;
            flex: 1;
        }

        .result-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
            font-size: 13px;
        }

        .result-table th {
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: 600;
        }

        .result-table td {
            padding: 8px 10px;
            border-bottom: 1px solid #ecf0f1;
        }

        .result-table tr:hover {
            background: #f8f9fa;
        }

        .result-table .byte-range {
            font-family: 'Consolas', monospace;
            color: #7f8c8d;
        }

        .result-table .token-text {
            font-family: 'Consolas', monospace;
            color: #2c3e50;
        }

        .badge {
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
        }

        .badge-keep {
            background: #d4edda;
            color: #155724;
        }

        .badge-prune {
            background: #f8d7da;
            color: #721c24;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }

        .stat-card.keep { background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%); }
        .stat-card.prune { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); }

        .stat-card h3 {
            font-size: 1.8em;
            margin-bottom: 5px;
        }

        .stat-card p {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .code-preview {
            background: #282c34;
            color: #abb2bf;
            padding: 20px;
            border-radius: 8px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.5;
            overflow-x: auto;
            white-space: pre;
            margin-bottom: 20px;
        }

        .code-container {
            background: #282c34;
            border-radius: 8px;
            padding: 20px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 12px;
            line-height: 1.5;
            overflow-x: auto;
            overflow-y: auto;
            color: #abb2bf;
            white-space: pre-wrap;
            tab-size: 4;
            max-height: 500px;
            width: 100%;
            box-sizing: border-box;
        }

        .code-line {
            display: block;
            line-height: 1.6;
            min-height: 1.6em;
            width: 100%;
            box-sizing: border-box;
        }

        .code-line:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .code-line .token {
            white-space: pre-wrap;
            word-break: break-word;
        }

        .token {
            display: inline;
            padding: 2px 4px;
            border-radius: 3px;
            transition: all 0.2s;
            cursor: pointer;
        }

        .token.active-highlight {
            background: rgba(255, 235, 59, 0.5) !important;
            border: 2px solid #ffeb3b !important;
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(255, 235, 59, 0.5);
            z-index: 10;
            position: relative;
        }

        tr.table-row-highlight {
            background: rgba(255, 235, 59, 0.2) !important;
        }

        .token:hover {
            transform: scale(1.05);
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }

        .token-keep {
            background: rgba(40, 167, 69, 0.3);
            border: 1px solid #28a745;
        }

        .token-prune {
            background: rgba(220, 53, 69, 0.3);
            border: 1px solid #dc3545;
        }

        .token-unknown {
            background: rgba(255, 193, 7, 0.3);
            border: 1px solid #ffc107;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }

        .stat-card h3 {
            font-size: 2em;
            margin-bottom: 5px;
        }

        .stat-card p {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .classification-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .classification-table th {
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }

        .classification-table td {
            padding: 10px 12px;
            border-bottom: 1px solid #e0e0e0;
        }

        .classification-table tr:hover {
            background: #f5f5f5;
        }

        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge-keep {
            background: #d4edda;
            color: #155724;
        }

        .badge-prune {
            background: #f8d7da;
            color: #721c24;
        }

        .legend {
            display: flex;
            gap: 20px;
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .legend-color {
            width: 30px;
            height: 20px;
            border-radius: 4px;
            border: 2px solid;
        }

        .legend-color.keep {
            background: rgba(40, 167, 69, 0.5);
            border-color: #28a745;
        }

        .legend-color.prune {
            background: rgba(220, 53, 69, 0.5);
            border-color: #dc3545;
        }

        .sample-info {
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin-bottom: 20px;
            border-radius: 4px;
        }

        .tooltip {
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 14px;
            pointer-events: none;
            z-index: 1000;
            max-width: 300px;
            display: none;
        }

        @media (max-width: 1024px) {
            .content {
                grid-template-columns: 1fr;
            }

            .panel-left {
                border-right: none;
                border-bottom: 2px solid #e0e0e0;
            }
        }
    </style>
</head>
<body>
"""


def generate_html_footer() -> str:
    """Generate HTML footer."""
    return """
</body>
</html>"""


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#039;'))


def highlight_code_with_classification(code: str, classifications: List[NodeClassification]) -> str:
    """
    Highlight code with classification colors, formatted by lines.

    Args:
        code: Original source code
        classifications: List of NodeClassification objects

    Returns:
        HTML string with highlighted tokens
    """
    # Sort classifications by byte offset
    sorted_classifications = sorted(classifications, key=lambda x: x.byte_range[0])

    # Split code into lines
    lines = code.split('\n')
    result = []

    # Track current position in the original code
    current_pos = 0
    token_id = 0

    for line_num, line in enumerate(lines):
        # Get classifications for this line
        line_start = current_pos
        line_end = current_pos + len(line)

        # Find tokens that overlap with this line
        line_tokens = []
        for cls in sorted_classifications:
            token_start, token_end = cls.byte_range
            # Check if token overlaps with this line
            if token_start < line_end and token_end > line_start:
                line_tokens.append(cls)

        # Build line HTML
        line_html = []
        pos_in_line = 0

        for cls in line_tokens:
            token_start, token_end = cls.byte_range

            # Adjust to line-relative position
            rel_start = max(0, token_start - line_start)
            rel_end = min(len(line), token_end - line_start)

            # Add any text before this token
            if rel_start > pos_in_line:
                line_html.append(escape_html(line[pos_in_line:rel_start]))

            # Add highlighted token
            token_text = line[rel_start:rel_end]
            css_class = 'token-keep' if cls.decision == 'KEEP' else 'token-prune'

            # Create tooltip data with token ID for linkage
            tooltip_data = {
                'text': escape_html(cls.text[:30]),
                'layer': cls.layer,
                'category': cls.category,
                'decision': cls.decision,
                'reasoning': escape_html(cls.reasoning),
                'tokenId': token_id
            }

            line_html.append(f'<span class="token {css_class}" data-info=\'{json.dumps(tooltip_data)}\' data-token-id="{token_id}">')
            line_html.append(escape_html(token_text))
            line_html.append('</span>')

            pos_in_line = rel_end
            token_id += 1

        # Add remaining text in line
        if pos_in_line < len(line):
            line_html.append(escape_html(line[pos_in_line:]))

        # Wrap line in div
        result.append(f'<div class="code-line">{"".join(line_html)}</div>')

        # Update current position (plus 1 for newline)
        current_pos = line_end + 1

    return ''.join(result)


def generate_classification_table(classifications: List[NodeClassification]) -> str:
    """Generate HTML table showing classification details with token linkage."""
    # Filter to show only interesting nodes (not too small)
    filtered = [c for c in classifications if len(c.text.strip()) > 0]

    rows = []
    token_id = 0
    for cls in filtered[:50]:  # Limit to first 50
        badge_class = 'badge-keep' if cls.decision == 'KEEP' else 'badge-prune'
        rows.append(f'''
        <tr data-table-token-id="{token_id}" class="table-row">
            <td>{token_id+1}</td>
            <td><code>{escape_html(cls.text[:30])}</code></td>
            <td>{cls.layer}</td>
            <td>{cls.category}</td>
            <td><span class="badge {badge_class}">{cls.decision}</span></td>
            <td>{escape_html(cls.reasoning[:50])}</td>
        </tr>
        ''')
        token_id += 1

    return f"""
    <table class="classification-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Text</th>
                <th>Layer</th>
                <th>Category</th>
                <th>Decision</th>
                <th>Reasoning</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def generate_html_visualization(code: str, language: str, classifications: List[NodeClassification],
                                 stats: Dict[str, Any], sample_info: Dict[str, Any]) -> str:
    """
    Generate complete HTML visualization with three-stage process display.

    Args:
        code: Source code
        language: Programming language
        classifications: List of NodeClassification objects
        stats: Statistics dictionary
        sample_info: Sample metadata

    Returns:
        Complete HTML string
    """
    html_parts = []

    # Header
    title = f"Two-Layer Syntax Classification - {language.upper()}"
    html_parts.append(generate_html_header(title))

    # Body start
    html_parts.append('<div class="container">')

    # Header section
    html_parts.append(f'''
    <div class="header">
        <h1>🔍 Two-Layer Syntax Classification Process</h1>
        <div class="meta">
            Language: <strong>{language.upper()}</strong> |
            Sample: <strong>{sample_info.get('name', 'Unknown')}</strong> |
            Lines: <strong>{len(code.splitlines())}</strong> |
            Characters: <strong>{len(code)}</strong>
        </div>
    </div>
    ''')

    # Sample info
    html_parts.append(f'''
    <div class="sample-info">
        <strong>📂 Source:</strong> {sample_info.get('source', 'N/A')}<br>
        <strong>📊 Statistics:</strong>
        Total Nodes: {stats['total_nodes']} |
        KEEP (High Entropy): {stats['keep_nodes']} ({stats['keep_ratio']:.1%}) |
        PRUNE (Syntax-Constrained): {stats['prune_nodes']} ({stats['prune_ratio']:.1%})
    </div>
    ''')

    # Stage 1: Code Preview
    html_parts.append('''
    <div class="section">
        <div class="section-title">
            <span class="step-number">0</span>
            Original Code Sample
        </div>
        <div class="code-preview">
    ''')
    html_parts.append(escape_html(code[:500]) + ('...' if len(code) > 500 else ''))
    html_parts.append('''
        </div>
    </div>
    ''')

    # Separate classifications by type
    named_nodes = [c for c in classifications if c.is_named]
    anonymous_nodes = [c for c in classifications if not c.is_named]

    # Stage 1: Tree-sitter Extraction
    html_parts.append('''
    <div class="section">
        <div class="section-title">
            <span class="step-number step-1">1</span>
            Tree-sitter CST Extraction
        </div>
        <div class="section-description">
            Tree-sitter parses the code and generates a Concrete Syntax Tree (CST), preserving all characters.
            Nodes are classified as <strong>Named</strong> (business logic) or <strong>Anonymous</strong> (syntax tokens).
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <h3>''' + str(len(named_nodes)) + '''</h3>
                <p>Named Nodes</p>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);">
                <h3>''' + str(len(anonymous_nodes)) + '''</h3>
                <p>Anonymous Nodes</p>
            </div>
        </div>

        <div class="filter-stage">
            <div class="filter-box">
                <h4>✅ Named Nodes (Layer 1: KEEP)</h4>
                <div style="max-height: 250px; overflow-y: auto;">
    ''')

    for i, node in enumerate(named_nodes[:20]):
        html_parts.append(f'''
                    <div class="tree-node named">
                        <span class="node-type">{node.category}</span>
                        <span class="node-text">{escape_html(node.text[:40])}</span>
                    </div>
        ''')

    if len(named_nodes) > 20:
        html_parts.append(f'<p style="text-align: center; color: #7f8c8d;">... and {len(named_nodes) - 20} more named nodes</p>')

    html_parts.append('''
                </div>
            </div>
            <div class="filter-box">
                <h4>❓ Anonymous Nodes (→ Layer 2)</h4>
                <div style="max-height: 250px; overflow-y: auto;">
    ''')

    for i, node in enumerate(anonymous_nodes[:20]):
        html_parts.append(f'''
                    <div class="tree-node anonymous">
                        <span class="node-type">{node.category}</span>
                        <span class="node-text">{escape_html(node.text[:40])}</span>
                    </div>
        ''')

    if len(anonymous_nodes) > 20:
        html_parts.append(f'<p style="text-align: center; color: #7f8c8d;">... and {len(anonymous_nodes) - 20} more anonymous nodes</p>')

    html_parts.append('''
                </div>
            </div>
        </div>
    </div>
    ''')

    # Stage 2: Lexical Feature Classification
    html_parts.append('''
    <div class="section">
        <div class="section-title">
            <span class="step-number step-2">2</span>
            Anonymous Node Classification (Layer 2)
        </div>
        <div class="section-description">
            Anonymous nodes undergo lexical feature analysis using Unicode categories and operator sets.
            Classification: <strong>Keywords/Operators → KEEP</strong> | <strong>Delimiters → PRUNE</strong>
        </div>

        <div class="filter-stage">
    ''')

    # Group anonymous nodes by category (including whitespace)
    by_category = {}
    for node in anonymous_nodes:
        cat = node.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(node)

    # Order: named, keyword, operator, delimiter, whitespace
    categories_order = ['named', 'keyword', 'operator', 'delimiter', 'whitespace']
    for cat in categories_order:
        if cat in by_category:
            # Determine decision based on category
            if cat in ['named', 'keyword', 'operator']:
                decision_display = 'KEEP'
            elif cat == 'whitespace':
                decision_display = 'PRUNE - Gap'
            else:  # delimiter
                decision_display = 'PRUNE'

            html_parts.append(f'''
            <div class="filter-box">
                <h4>{cat.upper()} ({decision_display})</h4>
                <div style="max-height: 200px; overflow-y: auto;">
            ''')

            for node in by_category[cat][:15]:
                html_parts.append(f'''
                    <div class="filter-item">
                        <span class="category-badge category-{cat}">{node.decision}</span>
                        <span class="node-text">{escape_html(node.text[:30])}</span>
                    </div>
                ''')

            if len(by_category[cat]) > 15:
                html_parts.append(f'<p style="text-align: center; color: #7f8c8d;">... and {len(by_category[cat]) - 15} more</p>')

            html_parts.append('''
                </div>
            </div>
            ''')

    html_parts.append('''
        </div>
    </div>
    ''')

    # Stage 3: Final Result
    html_parts.append('''
    <div class="section">
        <div class="section-title">
            <span class="step-number step-3">3</span>
            Final Syntax-Constrained Tokens (PRUNE)
        </div>
        <div class="section-description">
            These tokens will be masked out during membership inference attack because they have
            <strong>zero/low conditional entropy</strong> (determined by syntax, not author intent).
        </div>

        <table class="result-table">
            <thead>
                <tr>
                    <th>#</th>
                    <th>Token</th>
                    <th>Byte Range</th>
                    <th>Category</th>
                    <th>Reasoning</th>
                </tr>
            </thead>
            <tbody>
    ''')

    prune_nodes = [c for c in classifications if c.decision == 'PRUNE']
    for i, node in enumerate(prune_nodes[:30]):
        start, end = node.byte_range
        html_parts.append(f'''
                <tr>
                    <td>{i+1}</td>
                    <td class="token-text">{escape_html(node.text)}</td>
                    <td class="byte-range">[{start}, {end})</td>
                    <td>{node.category}</td>
                    <td>{escape_html(node.reasoning)}</td>
                </tr>
        ''')

    if len(prune_nodes) > 30:
        html_parts.append(f'''
                <tr>
                    <td colspan="5" style="text-align: center; color: #7f8c8d;">
                        ... and {len(prune_nodes) - 30} more syntax-constrained tokens
                    </td>
                </tr>
        ''')

    html_parts.append('''
            </tbody>
        </table>
    </div>
    ''')

    # Close container
    html_parts.append('</div>')

    # Footer
    html_parts.append(generate_html_footer())

    return ''.join(html_parts)


def load_jsonl_samples(path: str, num_samples: int = None) -> list:
    """Load samples from JSONL file."""
    samples = []
    with open(path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if num_samples and i >= num_samples:
                break
            samples.append(json.loads(line))
    return samples


def main():
    parser = argparse.ArgumentParser(description='Generate HTML visualization of two-layer syntax classification')
    parser.add_argument("--language", required=True, help="Programming language (c/java/javascript)")
    parser.add_argument("--input", required=True, help="Input JSONL file or directory")
    parser.add_argument("--num_samples", type=int, default=5, help="Number of samples to visualize")
    parser.add_argument("--output", default="syntax_visualization.html", help="Output HTML file")

    args = parser.parse_args()

    language = args.language.lower()
    if language == 'js':
        language = 'javascript'

    print(f"Generating HTML visualization for {language}...")

    # Initialize parser
    try:
        syntax_parser = TreeSitterSyntaxParser(language)
        print(f"  Tree-sitter parser initialized for {language}")
    except Exception as e:
        print(f"Error initializing parser: {e}")
        sys.exit(1)

    # Load samples
    input_path = Path(args.input)

    if input_path.is_file():
        samples = load_jsonl_samples(str(input_path), args.num_samples)
    elif input_path.is_dir():
        # Try to find the appropriate file
        pattern = f"{language}_positive.jsonl"
        file_path = input_path / pattern
        if file_path.exists():
            samples = load_jsonl_samples(str(file_path), args.num_samples)
        else:
            print(f"Error: Cannot find {pattern} in {input_path}")
            sys.exit(1)
    else:
        print(f"Error: {args.input} is not a valid file or directory")
        sys.exit(1)

    print(f"  Loaded {len(samples)} samples")

    # Generate visualizations
    output_path = Path(args.output)

    # Create visualization subdirectory for this language
    viz_dir = Path("visualization") / language
    viz_dir.mkdir(parents=True, exist_ok=True)

    # Generate separate HTML for each sample
    for i, sample in enumerate(samples):
        # Get code
        if 'code' in sample:
            code = sample['code']
        elif 'function' in sample:
            code = sample['function']
        else:
            print(f"  Warning: Sample {i} has no code field, skipping")
            continue

        # Get sample name
        sample_name = sample.get('name', f'sample_{i}')
        sample_source = sample.get('repo', sample.get('origin', 'unknown'))

        # Classify
        classifications = syntax_parser.classify_all_nodes(code)
        stats = syntax_parser.get_statistics(code)

        # Sample info
        sample_info = {
            'name': sample_name,
            'source': sample_source
        }

        # Generate HTML
        html = generate_html_visualization(code, language, classifications, stats, sample_info)

        # Save individual sample
        sample_output = viz_dir / f"{output_path.stem}_{i}{output_path.suffix}"
        with open(sample_output, 'w', encoding='utf-8') as f:
            f.write(html)

        print(f"  Generated visualization {i+1}/{len(samples)}: {sample_output}")

    print(f"\n✅ All visualizations generated in {viz_dir}/!")
    print(f"   Open in browser: file://{sample_output.resolve()}")


if __name__ == "__main__":
    main()
