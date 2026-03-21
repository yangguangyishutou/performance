import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

FIG_DIR = Path(__file__).resolve().parent
DISTANCES_DIR = FIG_DIR.parent / "data" / "distances"
FAMILY_ORDER = ["Qwen", "LLaMA", "Granite", "Mistral", "Others"]

DISPLAY_NAME_MAP = {
    "l2": "L2 Distance",
    "cosine": "Cosine Distance",
    "mean_abs": "Mean Abs.",
    "max_abs": "Max Abs.",
    "sparse_update_rate_abs": "Sparse Abs.",
    "sparse_update_rate_relative": "Sparse Rel.",
    "ghostspec_mse": "GhostSpec MSE",
    "intrinsic_fingerprint": "PDF",
}


def savefig(name: str) -> None:
    """Save figure as PDF into the fig directory with tight layout."""
    path = FIG_DIR / name
    plt.tight_layout()
    plt.savefig(path, format="pdf", bbox_inches="tight")
    print(f"Saved {path}")


def infer_model_family(model_name: str) -> str:
    """Infer model family from model name."""
    low = model_name.lower()
    if "qwen" in low:
        return "Qwen"
    if "llama" in low:
        return "LLaMA"
    if "granite" in low:
        return "Granite"
    if "mistral" in low or "mixtral" in low:
        return "Mistral"
    return "Others"


def extract_upper_triangle_values(dist_matrix: dict) -> list[float]:
    """Extract upper-triangle (i<j) values from distance matrix."""
    keys = list(dist_matrix.keys())
    values: list[float] = []
    for i, row_key in enumerate(keys):
        row = dist_matrix.get(row_key, {})
        for j in range(i + 1, len(keys)):
            col_key = keys[j]
            val = row.get(col_key)
            if isinstance(val, (int, float)) and np.isfinite(val):
                values.append(float(val))
    return values


def collect_metrics_by_family() -> dict[str, dict[str, np.ndarray]]:
    """
    Collect distance values from all JSON files and group by:
    method -> model_family -> np.ndarray(values)
    """
    if not DISTANCES_DIR.exists():
        raise FileNotFoundError(f"Distance directory not found: {DISTANCES_DIR}")

    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    json_files = sorted(DISTANCES_DIR.glob("*.json"))
    if not json_files:
        raise FileNotFoundError(f"No JSON files found in {DISTANCES_DIR}")

    for path in json_files:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        method = data.get("method")
        dist_matrix = data.get("dist_matrix", {})
        model_names_map = data.get("model_names_map", {})
        root_model_name = model_names_map.get("0-X-X", "")

        if not isinstance(method, str) or not isinstance(dist_matrix, dict):
            continue

        family = infer_model_family(root_model_name)
        values = extract_upper_triangle_values(dist_matrix)
        grouped[method][family].extend(values)

    output: dict[str, dict[str, np.ndarray]] = {}
    for method, family_values in grouped.items():
        output[method] = {
            family: np.array(vals, dtype=float)
            for family, vals in family_values.items()
            if vals
        }
    return output


def plot_family_boxplot(
    family_name: str,
    metric_values: np.ndarray,
    metric_name: str,
    metric_display_name: str,
    output_filename: str,
    y_limits: tuple[float, float],
) -> None:
    """Plot one family-one metric boxplot."""
    fig, ax = plt.subplots(figsize=(2.5, 3.0))

    bp = ax.boxplot(
        [metric_values],
        patch_artist=True,
        widths=0.6,
        showmeans=True,
        meanline=False,
    )

    for patch in bp["boxes"]:
        patch.set_facecolor("#4C72B0")
        patch.set_alpha(0.7)

    for element in ["whiskers", "fliers", "means", "medians", "caps"]:
        plt.setp(bp[element], color="black", linewidth=1.2)

    ax.tick_params(axis="both", labelsize=14)
    ax.set_xticklabels([])
    ax.grid(True, alpha=0.3, axis="y", linestyle="--")
    ax.set_ylim(y_limits[0], y_limits[1])
    ax.set_title(family_name, fontsize=10)

    savefig(output_filename)
    plt.close(fig)


def main() -> None:
    """Generate family-wise boxplots for each distance metric."""
    metrics = collect_metrics_by_family()
    if not metrics:
        raise RuntimeError("No valid distance metric data collected from JSON files.")

    all_values = np.concatenate(
        [
            arr
            for family_data in metrics.values()
            for arr in family_data.values()
            if arr.size > 0
        ]
    )
    global_min = float(np.min(all_values))
    global_max = float(np.max(all_values))
    if np.isclose(global_min, global_max):
        y_limits = (global_min - 1e-6, global_max + 1e-6)
    else:
        padding = (global_max - global_min) * 0.05
        y_limits = (global_min - padding, global_max + padding)

    for metric_key in sorted(metrics.keys()):
        metric_display_name = DISPLAY_NAME_MAP.get(metric_key, metric_key)
        family_data = metrics[metric_key]
        for family_name in FAMILY_ORDER:
            metric_values = family_data.get(family_name)
            if metric_values is None or metric_values.size == 0:
                continue
            output_filename = f"rq1_{family_name.lower()}_{metric_key}_boxplot.pdf"
            plot_family_boxplot(
                family_name=family_name,
                metric_values=metric_values,
                metric_name=metric_key,
                metric_display_name=metric_display_name,
                output_filename=output_filename,
                y_limits=y_limits,
            )
            print(
                f"[{metric_key}] {family_name}: n={metric_values.size}, "
                f"mean={metric_values.mean():.6f}"
            )


if __name__ == "__main__":
    main()

