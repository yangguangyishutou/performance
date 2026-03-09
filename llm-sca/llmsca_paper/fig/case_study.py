import os

import matplotlib.pyplot as plt
import numpy as np

FIG_DIR = os.path.dirname(__file__)


def savefig(name: str):
    """Save figure as PDF into the fig directory with tight layout."""
    path = os.path.join(FIG_DIR, name)
    plt.tight_layout()
    plt.savefig(path, format="pdf", bbox_inches='tight')
    print(f"Saved {path}")


def plot_error_case_study():
    """
    RQ4: Directed graph case study illustrating erroneous edges in the lineage graph.
    
    This function draws a directed graph showing:
    - Correct edges (black arrows): representing valid parent-child relationships
    - Erroneous edges (red arrows): representing incorrect relationships (e.g., sibling edges)
    """
    # Hard-coded graph structure - modify as needed for your case study
    # Format: node_name -> (x_position, y_position)
    # Positions are in normalized coordinates (0-1)
    node_positions = {
        "A": (0.5, 0.8),   # Top center
        "B": (0.2, 0.4),   # Bottom left
        "C": (0.8, 0.4),   # Bottom right
    }
    
    # Hard-coded edges - modify as needed
    # Format: (start_node, end_node, color, line_width, is_erroneous)
    # Correct edges (black)
    correct_edges = [
        ("A", "B", "black", 1.2, False),
        ("B", "C", "black", 1.2, False),
    ]
    
    # Erroneous edges (red, thicker line)
    erroneous_edges = [
        ("C", "B", "#C44E52", 1.6, True),  # Sibling edge (C -> B)
    ]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(3.4, 2.6))
    
    def draw_arrow(start, end, color, line_width=1.2, zorder=2):
        """Helper function to draw an arrow from start to end node."""
        x0, y0 = node_positions[start]
        x1, y1 = node_positions[end]
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle="-|>",
                color=color,
                lw=line_width,
                shrinkA=10,
                shrinkB=10,
            ),
            zorder=zorder,
        )
    
    # Draw correct edges first (so they appear behind)
    for start, end, color, lw, _ in correct_edges:
        draw_arrow(start, end, color, lw, zorder=2)
    
    # Draw erroneous edges (so they appear on top)
    for start, end, color, lw, _ in erroneous_edges:
        draw_arrow(start, end, color, lw, zorder=3)
    
    # Draw nodes
    for node, (x, y) in node_positions.items():
        ax.scatter(x, y, s=200, color="white", edgecolor="black", zorder=3)
        ax.text(x, y, node, ha="center", va="center", fontsize=10, zorder=4)
    
    # Add caption text at the bottom
    caption_text = "Red arrow: erroneous sibling edge (C → B)"
    ax.text(
        0.5,
        0.05,
        caption_text,
        ha="center",
        va="center",
        fontsize=8,
    )
    
    # Set axis limits and hide axes
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    
    savefig("rq4_error_case_study.pdf")
    plt.close(fig)


if __name__ == "__main__":
    plot_error_case_study()

