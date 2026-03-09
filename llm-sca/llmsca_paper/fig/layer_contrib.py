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


def plot_layer_contribution(metric_name: str, metric_display_name: str, contributions: np.ndarray, output_filename: str):
    """
    Plot bar chart showing contribution of different layers to a specific distance metric.
    
    Args:
        metric_name: Short name of the metric (e.g., 'l2', 'cos', 'abs_mean')
        metric_display_name: Display name for the metric (e.g., 'L2 distance', 'Cosine similarity')
        contributions: Array of 5 values for [K, Q, V, O, MLP] contributions (normalized)
        output_filename: Output PDF filename
    """
    components = ["K", "Q", "V", "O", "MLP"]
    
    fig, ax = plt.subplots(figsize=(4.0, 2.8))
    bars = ax.bar(components, contributions, color="#4C72B0")
    
    ax.set_ylabel(f"Relative contribution to {metric_display_name}")
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
    
    savefig(output_filename)
    plt.close(fig)


def main():
    """Generate contribution plots for all distance metrics."""
    contributions_data = {
        "L2": {
            "display_name": "L2 distance",
            "values": np.array([0.22, 0.18, 0.27, 0.15, 0.18]),  # Example data
        },
        "Cos": {
            "display_name": "Cosine similarity",
            "values": np.array([0.20, 0.19, 0.25, 0.16, 0.20]),  # Example data
        },
        "Abs_Mean": {
            "display_name": "Abs Mean",
            "values": np.array([0.21, 0.17, 0.26, 0.17, 0.19]),  # Example data
        },
        "Abs_Max": {
            "display_name": "Abs Max",
            "values": np.array([0.23, 0.16, 0.28, 0.14, 0.19]),  # Example data
        },
        "Sparse_Abs": {
            "display_name": "Sparse Abs.",
            "values": np.array([0.19, 0.20, 0.24, 0.18, 0.19]),  # Example data
        },
        "Sparse_Rel": {
            "display_name": "Sparse Rel.",
            "values": np.array([0.20, 0.18, 0.25, 0.17, 0.20]),  # Example data
        },
    }
    
    # Generate plots for each metric
    for metric_key, metric_info in contributions_data.items():
        plot_layer_contribution(
            metric_name=metric_key,
            metric_display_name=metric_info["display_name"],
            contributions=metric_info["values"],
            output_filename=f"rq2_{metric_key.lower()}_layer_contrib.pdf"
        )


if __name__ == "__main__":
    main()

