import os

import matplotlib.pyplot as plt
import numpy as np


FIG_DIR = os.path.dirname(__file__)


def savefig(name: str):
    """Save figure as PDF into the fig directory with tight layout."""
    path = os.path.join(FIG_DIR, name)
    plt.tight_layout()
    plt.savefig(path, format="pdf")
    print(f"Saved {path}")


def plot_rq2_l2_layer_contrib():
    """RQ2 (1): Bar chart – contribution of different layers to L2 distance."""
    components = ["K", "Q", "V", "O", "MLP"]
    # Example synthetic contributions (normalized)
    contributions = np.array([0.22, 0.18, 0.27, 0.15, 0.18])

    fig, ax = plt.subplots(figsize=(4.0, 2.8))
    bars = ax.bar(components, contributions, color="#4C72B0")

    ax.set_ylabel("Relative contribution to L2 distance")
    ax.set_xlabel("Transformer block component")
    ax.set_ylim(0, max(contributions) * 1.2)

    # Annotate bars with values
    for bar, value in zip(bars, contributions):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    savefig("rq2_l2_layer_contrib.pdf")
    plt.close(fig)


def plot_rq2_layer_combo_heatmap():
    """RQ2 (2): Heatmap – accuracy for different layer combinations."""
    components = ["K", "Q", "V", "O", "MLP"]
    n = len(components)

    # Example synthetic accuracies (in %), symmetric matrix
    base = np.array(
        [
            [72, 74, 76, 73, 77],
            [74, 71, 75, 72, 76],
            [76, 75, 78, 74, 79],
            [73, 72, 74, 70, 75],
            [77, 76, 79, 75, 80],
        ],
        dtype=float,
    )

    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    im = ax.imshow(base, cmap="viridis", vmin=70, vmax=82)

    ax.set_xticks(np.arange(n))
    ax.set_yticks(np.arange(n))
    ax.set_xticklabels(components)
    ax.set_yticklabels(components)

    ax.set_xlabel("Included component 1")
    ax.set_ylabel("Included component 2")

    # Rotate tick labels
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    # Annotate cells
    for i in range(n):
        for j in range(n):
            ax.text(
                j,
                i,
                f"{base[i, j]:.0f}",
                ha="center",
                va="center",
                color="white" if base[i, j] < 76 else "black",
                fontsize=7,
            )

    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Accuracy (%)")

    savefig("rq2_layer_combo_heatmap.pdf")
    plt.close(fig)


def plot_rq4_error_edge_pie():
    """RQ4 (3): Pie chart – proportion of different erroneous edge types."""
    labels = [
        "Sibling–Sibling",
        "Grandparent–Child",
        "Parent–Child (reversed)",
        "Other",
    ]
    # Example synthetic proportions
    sizes = [0.35, 0.25, 0.25, 0.15]
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2"]

    fig, ax = plt.subplots(figsize=(3.2, 3.2))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        colors=colors,
        autopct="%1.0f%%",
        startangle=90,
        textprops={"fontsize": 8},
    )
    ax.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.

    savefig("rq4_error_edge_pie.pdf")
    plt.close(fig)


def plot_rq4_error_case_study():
    """RQ4 (4): Directed graph case study illustrating erroneous edges."""
    fig, ax = plt.subplots(figsize=(3.4, 2.6))

    # Simple lineage: A -> B -> C, plus an erroneous sibling edge B <-> C
    positions = {
        "A": (0.5, 0.8),
        "B": (0.2, 0.4),
        "C": (0.8, 0.4),
    }

    # Draw nodes
    for node, (x, y) in positions.items():
        ax.scatter(x, y, s=200, color="white", edgecolor="black", zorder=3)
        ax.text(x, y, node, ha="center", va="center", fontsize=10, zorder=4)

    def draw_arrow(start, end, color, style="-|>", lw=1.2, zorder=2):
        x0, y0 = positions[start]
        x1, y1 = positions[end]
        ax.annotate(
            "",
            xy=(x1, y1),
            xytext=(x0, y0),
            arrowprops=dict(
                arrowstyle=style,
                color=color,
                lw=lw,
                shrinkA=10,
                shrinkB=10,
            ),
            zorder=zorder,
        )

    # Correct edges (black)
    draw_arrow("A", "B", "black")
    draw_arrow("B", "C", "black")

    # Erroneous edge (red, sibling edge C -> B)
    draw_arrow("C", "B", "#C44E52", lw=1.6, zorder=3)

    ax.text(
        0.5,
        0.05,
        "Red arrow: erroneous sibling edge (C → B)",
        ha="center",
        va="center",
        fontsize=8,
    )

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    savefig("rq4_error_case_study.pdf")
    plt.close(fig)


def main():
    plot_rq2_l2_layer_contrib()
    plot_rq2_layer_combo_heatmap()
    plot_rq4_error_edge_pie()
    plot_rq4_error_case_study()


if __name__ == "__main__":
    main()


