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


def plot_error_edge_pie():
    """
    RQ4: Pie chart showing proportion of different erroneous edge types.
    
    Error types:
    - Sibling–Sibling: Erroneous edges connecting sibling nodes
    - Grandparent–Child: Erroneous edges connecting grandparent and child (skipping parent)
    - Parent–Child (reversed): Erroneous edges with reversed direction (child -> parent)
    - Multi-hop: Erroneous edges with multiple hops
    - Other: Other types of erroneous edges
    """
    # Hard-coded data - replace with your real experimental data
    # Format: label -> proportion (should sum to 1.0)
    error_data = {
        "Sibling–Sibling": 0.35,          # Example: 35%
        "Grandparent–Child": 0.25,         # Example: 25%
        "Parent–Child (reversed)": 0.25,  # Example: 25%
        "Multi-hop": 0.15,                 # Example: 15%
        "Other": 0.15,                     # Example: 15%
    }
    
    # Extract labels and sizes from dictionary
    labels = list(error_data.keys())
    sizes = list(error_data.values())
    
    # Pastel color scheme (non-saturated colors)
    colors = ["#A8C5E0", "#A8D5BA", "#E8A8A8", "#C8B8E0", "#D0D0D0"]
    
    # Create figure
    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    
    # Draw pie chart
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",      # Display percentage with 0 decimal places
        startangle=90,           # Start from top (90 degrees)
        textprops={"fontsize": 8},
    )
    
    # Ensure pie is drawn as a circle
    ax.axis("equal")
    
    savefig("rq4_error_edge_pie.pdf")
    plt.close(fig)


if __name__ == "__main__":
    plot_error_edge_pie()

