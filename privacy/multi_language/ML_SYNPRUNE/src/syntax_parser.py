"""
Tree-sitter based syntax parser for multi-language membership inference attack.

This module implements a two-layer classification process:
1. Layer 1: Structure Check - Use Tree-sitter's is_named attribute
2. Layer 2: Lexical Feature Check - Classify using Unicode categories and operator sets
"""

import unicodedata
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

# Universal operator set based on C/Java/JS specifications
UNIVERSAL_OPERATORS = {
    # Arithmetic
    '+', '-', '*', '/', '%', '++', '--',
    # Assignment
    '=', '+=', '-=', '*=', '/=', '%=', '&=', '|=', '^=', '<<=', '>>=',
    # Comparison
    '==', '!=', '>', '<', '>=', '<=',
    # Logical / Bitwise
    '&&', '||', '!', '&', '|', '^', '~',
    # Ternary
    '?', ':',
    # Access / Scope
    '.', '->', '::',
    # Shift
    '>>', '<<', '>>>', '<<<',
}


@dataclass
class NodeClassification:
    """Classification result for a syntax node."""
    text: str
    is_named: bool
    layer: int  # 1 or 2
    category: str  # 'named', 'keyword', 'operator', 'delimiter'
    decision: str  # 'KEEP' or 'PRUNE'
    byte_range: Tuple[int, int]
    reasoning: str


class TreeSitterSyntaxParser:
    """
    Tree-sitter based syntax parser implementing two-layer classification.

    Layer 1: Structure Check
    - is_named == True → KEEP (identifiers, literals, business logic)
    - is_named == False → Proceed to Layer 2

    Layer 2: Lexical Feature Check
    - Alphanumeric (keywords, identifiers) → KEEP
    - Operators (+, *, ==, &&, →, ::) → KEEP
    - Delimiters/Separators ((), {}, ;, ,) → PRUNE
    """

    def __init__(self, language: str):
        """
        Initialize parser for specific language.

        Args:
            language: One of 'c', 'java', 'javascript'
        """
        self.language = language.lower()
        self.parser = None
        self.tree_language = None
        self._load_language()

    def _load_language(self):
        """Load Tree-sitter language grammar."""
        try:
            from tree_sitter import Language, Parser

            # Map language names to their tree-sitter identifiers
            # Support both individual packages and tree-sitter-languages
            lang_map_for_individual = {
                'c': 'tree_sitter_c',
                'java': 'tree_sitter_java',
                'javascript': 'tree_sitter_javascript',
                'js': 'tree_sitter_javascript',
            }
            lang_map_for_bundle = {
                'c': 'c',
                'java': 'java',
                'javascript': 'javascript',
                'js': 'javascript',
            }

            if self.language not in lang_map_for_individual:
                raise ValueError(f"Unsupported language: {self.language}")

            lang_obj = None

            # Method 1: Try tree-sitter-languages bundle (AutoDL compatible)
            try:
                from tree_sitter_languages import get_language
                bundle_lang_name = lang_map_for_bundle[self.language]
                lang_obj = get_language(bundle_lang_name)
            except ImportError:
                pass

            # Method 2: Try individual language packages
            if lang_obj is None:
                lang_module_name = lang_map_for_individual[self.language]
                try:
                    lang_module = __import__(lang_module_name)
                    if hasattr(lang_module, 'language'):
                        lang_obj = lang_module.language()
                    elif hasattr(lang_module, f'{self.language.upper()}Language'):
                        # Alternative naming convention
                        lang_obj = getattr(lang_module, f'{self.language.upper()}Language')()
                except ImportError:
                    pass

            if lang_obj is None:
                raise ImportError(
                    f"Tree-sitter grammar for {self.language} not found.\n"
                    f"Install one of:\n"
                    f"  pip install tree-sitter-languages  # 推荐：包含所有语言\n"
                    f"  或单独安装: pip install tree-sitter-c tree-sitter-java tree-sitter-javascript"
                )

            # Handle different return types from language packages
            # - tree-sitter-languages.get_language() returns a Language object directly
            # - Individual packages (tree-sitter-java) return a PyCapsule pointer
            if isinstance(lang_obj, Language):
                # Already a Language object, use directly
                self.tree_language = lang_obj
            else:
                # PyCapsule pointer, need to wrap in Language
                # For newer tree-sitter: Language(ptr, name)
                # For older: Language(ptr) or Language(path)
                try:
                    self.tree_language = Language(lang_obj, name=self.language)
                except TypeError:
                    # Fallback for older tree-sitter versions
                    self.tree_language = Language(lang_obj)

            self.parser = Parser()
            # In newer tree-sitter versions, set_language is a method
            if hasattr(self.parser, 'set_language'):
                self.parser.set_language(self.tree_language)
            else:
                # For older tree-sitter versions (<0.20.0), use the old API
                raise RuntimeError(
                    "Your tree-sitter version is too old. Please upgrade:\n"
                    "  pip install --upgrade tree-sitter"
                )

        except ImportError as e:
            raise ImportError(
                f"Failed to import tree_sitter: {e}\n"
                "Install with: pip install tree-sitter"
            )

    def parse_code(self, code: str) -> Any:
        """
        Parse code and return CST using Tree-sitter.

        Args:
            code: Source code string

        Returns:
            Tree-sitter Tree object
        """
        if self.parser is None:
            raise RuntimeError("Parser not initialized")

        # Parse code as bytes
        tree = self.parser.parse(bytes(code, "utf8"))
        return tree

    def _get_unicode_category(self, char: str) -> str:
        """
        Get Unicode General Category for a character.

        Categories (ISO/IEC 10646):
        - Lu, Ll, Lt, Lm, Lo: Letters (keywords, identifiers)
        - Nd, Nl, No: Numbers (literals)
        - Sm, So: Symbols/Math symbols (operators)
        - Ps, Pe, Pi, Pf: Punctuation (open/close brackets)
        - Po: Other punctuation (separators like ;, ,)
        - Cn: Unassigned

        Args:
            char: Single character

        Returns:
            Unicode category string (e.g., 'Lu' for uppercase letter)
        """
        if not char:
            return 'Cn'
        return unicodedata.category(char[0])

    def _is_operator(self, text: str) -> bool:
        """
        Check if text is a known operator.

        Args:
            text: Token text

        Returns:
            True if text is in UNIVERSAL_OPERATORS
        """
        # Check exact match
        if text in UNIVERSAL_OPERATORS:
            return True

        # Check for multi-character operators (handle tokenization issues)
        for op in UNIVERSAL_OPERATORS:
            if len(op) > 1 and op in text:
                return True

        return False

    def _classify_lexical(self, text: str) -> str:
        """
        Layer 2: Classify anonymous node text by lexical features.

        Classification logic:
        - Alphanumeric (Unicode L/N categories) → 'keyword' (KEEP)
        - Operator (in UNIVERSAL_OPERATORS) → 'operator' (KEEP)
        - Delimiter/Separator (Unicode P categories) → 'delimiter' (PRUNE)

        Args:
            text: Node text content

        Returns:
            One of: 'keyword', 'operator', 'delimiter', 'unknown'
        """
        if not text:
            return 'unknown'

        # Remove whitespace for checking
        text_stripped = text.strip()
        if not text_stripped:
            return 'unknown'

        # Check if it's an operator (including multi-char operators)
        if self._is_operator(text_stripped):
            return 'operator'

        # Check first character's Unicode category
        first_char = text_stripped[0]
        category = self._get_unicode_category(first_char)

        # Letters and Numbers → keyword/identifier (KEEP)
        if category.startswith('L') or category.startswith('N'):
            return 'keyword'

        # Symbols → could be operators (KEEP)
        if category in ('Sm', 'So'):
            # Additional check for operators
            if self._is_operator(text_stripped):
                return 'operator'
            return 'operator'  # Default symbols to operators (keep)

        # Punctuation → delimiters/separators (PRUNE)
        if category.startswith('P'):
            return 'delimiter'

        return 'unknown'

    def get_syntax_constrained_byte_ranges(self, code: str) -> List[Tuple[int, int]]:
        """
        Two-layer classification to identify syntax-constrained tokens.

        **Key Enhancement**: Detects byte gaps between Tree-sitter nodes to capture
        whitespace (spaces, newlines, tabs, indentation) that Tree-sitter skips.

        Returns byte ranges for tokens that should be PRUNED (syntax-constrained).

        Args:
            code: Source code string

        Returns:
            List of (start_byte, end_byte) tuples for PRUNE ranges
        """
        tree = self.parse_code(code)
        code_bytes = code.encode('utf-8')
        prune_ranges = []

        # Step 1: Collect all leaf nodes and classify them
        # Also track their byte positions for gap detection
        leaf_spans = []  # List of (start_byte, end_byte, should_prune)

        def traverse_and_collect(node):
            """Traverse and collect leaf node spans."""
            # Only process leaf nodes (actual tokens)
            if len(node.children) == 0:
                start_byte = node.start_byte
                end_byte = node.end_byte
                node_text = code[start_byte:end_byte] if start_byte < len(code) else ''

                # Skip empty nodes
                if start_byte >= end_byte:
                    return

                if node.is_named:
                    # Layer 1: Named leaf nodes → KEEP
                    leaf_spans.append((start_byte, end_byte, False))
                else:
                    # Layer 1: Anonymous leaf nodes → Proceed to Layer 2
                    category = self._classify_lexical(node_text)

                    # Layer 2: Check if should prune
                    if category == 'delimiter':
                        leaf_spans.append((start_byte, end_byte, True))
                    else:
                        # Keywords and operators → KEEP
                        leaf_spans.append((start_byte, end_byte, False))
            else:
                # Recurse into children
                for child in node.children:
                    traverse_and_collect(child)

        traverse_and_collect(tree.root_node)

        # Step 2: Sort leaf spans by start position
        leaf_spans.sort(key=lambda x: x[0])

        # Step 3: Detect and add byte gaps (whitespace) between leaf nodes
        # Any gap between leaf nodes is whitespace/indentation → PRUNE
        last_end = 0
        final_prune_ranges = []

        for start, end, should_prune in leaf_spans:
            # Check for gap before current leaf node
            if start > last_end:
                # Gap found! This is whitespace (spaces, newlines, tabs, indentation)
                # Example: "    ", "\n", "\n        "
                final_prune_ranges.append((last_end, start))

            # Add delimiters to prune ranges
            if should_prune:
                final_prune_ranges.append((start, end))

            last_end = max(last_end, end)

        # Step 4: Check for trailing whitespace after last leaf node
        if last_end < len(code_bytes):
            final_prune_ranges.append((last_end, len(code_bytes)))

        # Step 5: Merge overlapping or adjacent ranges
        final_prune_ranges.sort()
        merged_ranges = []
        for start, end in final_prune_ranges:
            if merged_ranges and start <= merged_ranges[-1][1]:
                # Overlap or adjacent: merge with previous
                merged_ranges[-1] = (merged_ranges[-1][0], max(merged_ranges[-1][1], end))
            else:
                merged_ranges.append((start, end))

        return merged_ranges

    def classify_all_nodes(self, code: str) -> List[NodeClassification]:
        """
        Classify only LEAF nodes in the CST for visualization/analysis.

        **Key Enhancement**: Also detects and classifies byte gaps as WHITESPACE nodes.
        This ensures that spaces, newlines, tabs, and indentation are visible in visualization.

        Key Fix: We only care about actual tokens (leaf nodes), not container nodes.
        Container nodes like 'if_statement' are named but they don't represent tokens.

        Args:
            code: Source code string

        Returns:
            List of NodeClassification objects for leaf nodes only (including whitespace gaps)
        """
        tree = self.parse_code(code)
        classifications = []
        code_bytes = code.encode('utf-8')

        # First pass: collect all leaf node spans
        leaf_spans = []  # List of (start_byte, end_byte, node_obj)

        def collect_leaf_spans(node):
            """Collect all leaf node spans for gap detection."""
            if len(node.children) == 0:
                start_byte = node.start_byte
                end_byte = node.end_byte
                # Skip empty nodes
                if start_byte < end_byte:
                    leaf_spans.append((start_byte, end_byte, node))
            else:
                for child in node.children:
                    collect_leaf_spans(child)

        collect_leaf_spans(tree.root_node)

        # Sort leaf spans by start position
        leaf_spans.sort(key=lambda x: x[0])

        # Second pass: traverse with gap detection
        last_end = 0

        for start_byte, end_byte, node in leaf_spans:
            # Detect gap before current node
            if start_byte > last_end:
                # Gap found! This is whitespace (spaces, newlines, tabs, indentation)
                gap_text = code[last_end:start_byte]
                gap_display = repr(gap_text)  # Show \n, \t, etc. explicitly

                classification = NodeClassification(
                    text=gap_display,  # Show as '\n    ' instead of actual whitespace
                    is_named=False,
                    layer=2,
                    category='whitespace',
                    decision='PRUNE',
                    byte_range=(last_end, start_byte),
                    reasoning=f'Whitespace gap (formatting: spaces/newlines/tabs)'
                )
                classifications.append(classification)

            # Classify the current leaf node
            node_text = code[start_byte:end_byte] if start_byte < len(code) else ''

            # Skip if empty (shouldn't happen, but safety check)
            if not node_text:
                last_end = max(last_end, end_byte)
                continue

            if node.is_named:
                # Layer 1: Named leaf nodes → KEEP (identifiers, literals)
                classification = NodeClassification(
                    text=node_text,
                    is_named=True,
                    layer=1,
                    category='named',
                    decision='KEEP',
                    byte_range=(start_byte, end_byte),
                    reasoning=f'Named leaf (identifier/literal: {node.type})'
                )
                classifications.append(classification)
            else:
                # Layer 1: Anonymous leaf nodes → Proceed to Layer 2
                category = self._classify_lexical(node_text)

                # Layer 2: Make decision
                if category == 'delimiter':
                    decision = 'PRUNE'
                    reasoning = f'Delimiter/Separator (syntax-constrained)'
                elif category == 'operator':
                    decision = 'KEEP'
                    reasoning = f'Operator (computational logic)'
                elif category == 'keyword':
                    decision = 'KEEP'
                    reasoning = f'Keyword (algorithmic choice)'
                else:
                    decision = 'KEEP'  # Default to keep for unknown
                    reasoning = f'Unknown category, defaulting to KEEP'

                classification = NodeClassification(
                    text=node_text,
                    is_named=False,
                    layer=2,
                    category=category,
                    decision=decision,
                    byte_range=(start_byte, end_byte),
                    reasoning=reasoning
                )
                classifications.append(classification)

            last_end = max(last_end, end_byte)

        # Check for trailing whitespace after last leaf node
        if last_end < len(code_bytes):
            gap_text = code[last_end:]
            gap_display = repr(gap_text)

            classification = NodeClassification(
                text=gap_display,
                is_named=False,
                layer=2,
                category='whitespace',
                decision='PRUNE',
                byte_range=(last_end, len(code_bytes)),
                reasoning=f'Trailing whitespace (formatting)'
            )
            classifications.append(classification)

        return classifications

    def get_statistics(self, code: str) -> Dict[str, Any]:
        """
        Get statistics about the classification.

        Args:
            code: Source code string

        Returns:
            Dictionary with classification statistics
        """
        classifications = self.classify_all_nodes(code)

        total_nodes = len(classifications)
        keep_nodes = sum(1 for c in classifications if c.decision == 'KEEP')
        prune_nodes = sum(1 for c in classifications if c.decision == 'PRUNE')

        # Count by category
        category_counts = {}
        for c in classifications:
            category_counts[c.category] = category_counts.get(c.category, 0) + 1

        return {
            'total_nodes': total_nodes,
            'keep_nodes': keep_nodes,
            'prune_nodes': prune_nodes,
            'keep_ratio': keep_nodes / total_nodes if total_nodes > 0 else 0,
            'prune_ratio': prune_nodes / total_nodes if total_nodes > 0 else 0,
            'category_counts': category_counts,
        }


def main():
    """Test the syntax parser."""
    import sys

    if len(sys.argv) < 3:
        print("Usage: python syntax_parser.py <language> <code_file>")
        print("Example: python syntax_parser.py c test_code.c")
        sys.exit(1)

    language = sys.argv[1]
    code_file = sys.argv[2]

    with open(code_file, 'r') as f:
        code = f.read()

    parser = TreeSitterSyntaxParser(language)

    print(f"Parsing {language} code from {code_file}")
    print("=" * 60)

    # Get statistics
    stats = parser.get_statistics(code)
    print(f"\nStatistics:")
    print(f"  Total nodes: {stats['total_nodes']}")
    print(f"  KEEP: {stats['keep_nodes']} ({stats['keep_ratio']:.1%})")
    print(f"  PRUNE: {stats['prune_nodes']} ({stats['prune_ratio']:.1%})")
    print(f"\nCategory counts:")
    for cat, count in stats['category_counts'].items():
        print(f"  {cat}: {count}")

    # Show prune ranges
    print(f"\nSyntax-constrained byte ranges (first 10):")
    prune_ranges = parser.get_syntax_constrained_byte_ranges(code)
    for i, (start, end) in enumerate(prune_ranges[:10]):
        text = code[start:end]
        print(f"  [{i}] bytes {start:4d}-{end:4d}: '{text}'")

    if len(prune_ranges) > 10:
        print(f"  ... and {len(prune_ranges) - 10} more")


if __name__ == "__main__":
    main()
