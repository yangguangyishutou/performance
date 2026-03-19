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


def plot_family_boxplot(family_name: str, metric_values: np.ndarray, metric_name: str, metric_display_name: str, output_filename: str):
    """
    Plot boxplot showing distance metric distribution for a specific model family.
    
    Args:
        family_name: Name of the model family (e.g., "Qwen", "LLaMA")
        metric_values: Array of distance metric values for models in this family
        metric_name: Short name of the metric (e.g., "l2", "cos")
        metric_display_name: Display name for the metric (e.g., "L2 Distance", "Cosine Similarity")
        output_filename: Output PDF filename
    """
    fig, ax = plt.subplots(figsize=(2.5, 3.0))
    
    # Create boxplot
    bp = ax.boxplot(
        [metric_values],
        # labels=[family_name],
        patch_artist=True,
        widths=0.6,
        showmeans=True,  # Show mean as a diamond
        meanline=False,
    )
    
    # Customize boxplot colors
    for patch in bp['boxes']:
        patch.set_facecolor('#4C72B0')
        patch.set_alpha(0.7)
    
    for element in ['whiskers', 'fliers', 'means', 'medians', 'caps']:
        plt.setp(bp[element], color='black', linewidth=1.2)
    
    # Set labels
    # ax.set_ylabel(metric_display_name, fontsize=9)
    # ax.set_xlabel('Model Family', fontsize=9)
    ax.tick_params(axis='both', labelsize=14)
    
    ax.set_xticklabels([])

    # Set y-axis limits with some padding
    # y_min = np.min(metric_values) * 0.95
    # y_max = np.max(metric_values) * 1.05
    # ax.set_ylim(y_min, y_max)
    ax.set_ylim(0, 1)
    
    # Add grid for better readability
    ax.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    savefig(output_filename)
    plt.close(fig)


def main():
    """Generate boxplots for all model families and all distance metrics."""
    # Hard-coded distance metric data for each model family
    # Format: metric_name -> {family_name -> array of values}
    # TODO: Replace with your real experimental data
    
    # Define all distance metrics
    metrics = {
        "l2": {
            "display_name": "L2 Distance",
            "data": {
                "Qwen": np.array([0.12, 0.15, 0.18, 0.14, 0.16, 0.13, 0.17, 0.15, 0.19, 0.14]),
                "LLaMA": np.array([0.22, 0.25, 0.28, 0.24, 0.26, 0.23, 0.27, 0.25, 0.29, 0.24, 0.21, 0.26]),
                "Granite": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.20, 0.23, 0.19]),
                "Mistral": np.array([0.16, 0.18, 0.20, 0.17, 0.19, 0.18, 0.21, 0.17, 0.19, 0.16, 0.20]),
                "Others": np.array([0.25, 0.28, 0.30, 0.27, 0.29, 0.26, 0.31, 0.28, 0.32, 0.27, 0.29, 0.30, 0.28]),
            }
        },
        "cos": {
            "display_name": "Cosine Similarity",
            "data": {
                "Qwen": np.array([0.85, 0.87, 0.89, 0.86, 0.88, 0.85, 0.90, 0.86, 0.91, 0.87]),
                "LLaMA": np.array([0.75, 0.77, 0.79, 0.76, 0.78, 0.75, 0.80, 0.76, 0.81, 0.77, 0.74, 0.78]),
                "Granite": np.array([0.80, 0.82, 0.84, 0.81, 0.83, 0.82, 0.85, 0.81]),
                "Mistral": np.array([0.82, 0.84, 0.86, 0.83, 0.85, 0.84, 0.87, 0.83, 0.85, 0.82, 0.86]),
                "Others": np.array([0.70, 0.72, 0.74, 0.71, 0.73, 0.70, 0.75, 0.72, 0.76, 0.71, 0.73, 0.74, 0.72]),
            }
        },
        "abs_mean": {
            "display_name": "Abs Mean",
            "data": {
                "Qwen": np.array([0.10, 0.12, 0.14, 0.11, 0.13, 0.10, 0.15, 0.12, 0.16, 0.11]),
                "LLaMA": np.array([0.20, 0.22, 0.24, 0.21, 0.23, 0.20, 0.25, 0.22, 0.26, 0.21, 0.19, 0.23]),
                "Granite": np.array([0.15, 0.17, 0.19, 0.16, 0.18, 0.17, 0.20, 0.16]),
                "Mistral": np.array([0.13, 0.15, 0.17, 0.14, 0.16, 0.15, 0.18, 0.14, 0.16, 0.13, 0.17]),
                "Others": np.array([0.22, 0.24, 0.26, 0.23, 0.25, 0.22, 0.27, 0.24, 0.28, 0.23, 0.25, 0.26, 0.24]),
            }
        },
        "abs_max": {
            "display_name": "Abs Max",
            "data": {
                "Qwen": np.array([0.25, 0.27, 0.29, 0.26, 0.28, 0.25, 0.30, 0.27, 0.31, 0.26]),
                "LLaMA": np.array([0.35, 0.37, 0.39, 0.36, 0.38, 0.35, 0.40, 0.37, 0.41, 0.36, 0.34, 0.38]),
                "Granite": np.array([0.30, 0.32, 0.34, 0.31, 0.33, 0.32, 0.35, 0.31]),
                "Mistral": np.array([0.28, 0.30, 0.32, 0.29, 0.31, 0.30, 0.33, 0.29, 0.31, 0.28, 0.32]),
                "Others": np.array([0.40, 0.42, 0.44, 0.41, 0.43, 0.40, 0.45, 0.42, 0.46, 0.41, 0.43, 0.44, 0.42]),
            }
        },
        "sparse_abs": {
            "display_name": "Sparse Abs.",
            "data": {
                "Qwen": np.array([0.08, 0.10, 0.12, 0.09, 0.11, 0.08, 0.13, 0.10, 0.14, 0.09]),
                "LLaMA": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.18, 0.23, 0.20, 0.24, 0.19, 0.17, 0.21]),
                "Granite": np.array([0.13, 0.15, 0.17, 0.14, 0.16, 0.15, 0.18, 0.14]),
                "Mistral": np.array([0.11, 0.13, 0.15, 0.12, 0.14, 0.13, 0.16, 0.12, 0.14, 0.11, 0.15]),
                "Others": np.array([0.20, 0.22, 0.24, 0.21, 0.23, 0.20, 0.25, 0.22, 0.26, 0.21, 0.23, 0.24, 0.22]),
            }
        },
        "sparse_rel": {
            "display_name": "Sparse Rel.",
            "data": {
                "Qwen": np.array([0.06, 0.08, 0.10, 0.07, 0.09, 0.06, 0.11, 0.08, 0.12, 0.07]),
                "LLaMA": np.array([0.16, 0.18, 0.20, 0.17, 0.19, 0.16, 0.21, 0.18, 0.22, 0.17, 0.15, 0.19]),
                "Granite": np.array([0.11, 0.13, 0.15, 0.12, 0.14, 0.13, 0.16, 0.12]),
                "Mistral": np.array([0.09, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.10, 0.12, 0.09, 0.13]),
                "Others": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.18, 0.23, 0.20, 0.24, 0.19, 0.21, 0.22, 0.20]),
            }
        },
        "ghostspec_mse": {
            "display_name": "GhostSpec MSE",
            "data": {
                "Qwen": np.array([0.06, 0.08, 0.10, 0.07, 0.09, 0.06, 0.11, 0.08, 0.12, 0.07]),
                "LLaMA": np.array([0.16, 0.18, 0.20, 0.17, 0.19, 0.16, 0.21, 0.18, 0.22, 0.17, 0.15, 0.19]),
                "Granite": np.array([0.11, 0.13, 0.15, 0.12, 0.14, 0.13, 0.16, 0.12]),
                "Mistral": np.array([0.09, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.10, 0.12, 0.09, 0.13]),
                "Others": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.18, 0.23, 0.20, 0.24, 0.19, 0.21, 0.22, 0.20]),
            }
        },
        "intrinsic_fingerprint": {
            "display_name": "PDF",
            "data": {
                "Qwen": np.array([0.06, 0.08, 0.10, 0.07, 0.09, 0.06, 0.11, 0.08, 0.12, 0.07]),
                "LLaMA": np.array([0.16, 0.18, 0.20, 0.17, 0.19, 0.16, 0.21, 0.18, 0.22, 0.17, 0.15, 0.19]),
                "Granite": np.array([0.11, 0.13, 0.15, 0.12, 0.14, 0.13, 0.16, 0.12]),
                "Mistral": np.array([0.09, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.10, 0.12, 0.09, 0.13]),
                "Others": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.18, 0.23, 0.20, 0.24, 0.19, 0.21, 0.22, 0.20]),
            }
        },
        "matrix_homology": {
            "display_name": "Matrix",
            "data": {
                "Qwen": np.array([0.06, 0.08, 0.10, 0.07, 0.09, 0.06, 0.11, 0.08, 0.12, 0.07]),
                "LLaMA": np.array([0.16, 0.18, 0.20, 0.17, 0.19, 0.16, 0.21, 0.18, 0.22, 0.17, 0.15, 0.19]),
                "Granite": np.array([0.11, 0.13, 0.15, 0.12, 0.14, 0.13, 0.16, 0.12]),
                "Mistral": np.array([0.09, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.10, 0.12, 0.09, 0.13]),
                "Others": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.18, 0.23, 0.20, 0.24, 0.19, 0.21, 0.22, 0.20]),
            }
        },
        "huref": {
            "display_name": "HuRef",
            "data": {
                "Qwen": np.array([0.06, 0.08, 0.10, 0.07, 0.09, 0.06, 0.11, 0.08, 0.12, 0.07]),
                "LLaMA": np.array([0.16, 0.18, 0.20, 0.17, 0.19, 0.16, 0.21, 0.18, 0.22, 0.17, 0.15, 0.19]),
                "Granite": np.array([0.11, 0.13, 0.15, 0.12, 0.14, 0.13, 0.16, 0.12]),
                "Mistral": np.array([0.09, 0.11, 0.13, 0.10, 0.12, 0.11, 0.14, 0.10, 0.12, 0.09, 0.13]),
                "Others": np.array([0.18, 0.20, 0.22, 0.19, 0.21, 0.18, 0.23, 0.20, 0.24, 0.19, 0.21, 0.22, 0.20]),
            }
        },
    }
    
    # Generate boxplots for each metric and each family
    for metric_key, metric_info in metrics.items():
        for family_name, metric_values in metric_info["data"].items():
            output_filename = f"rq1_{family_name.lower()}_{metric_key}_boxplot.pdf"
            plot_family_boxplot(
                family_name, 
                metric_values, 
                metric_key,
                metric_info["display_name"],
                output_filename
            )


if __name__ == "__main__":
    main()

