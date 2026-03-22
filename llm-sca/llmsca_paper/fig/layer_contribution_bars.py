"""
Bar charts: per-distance relative layer contribution from data/statistics/layer_contrib.json
(avg_pct_across_nodes), matching the RQ2-style layout of the previous hardcoded example.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import numpy as np

FIG_DIR = Path(__file__).resolve().parent
REPO_ROOT = FIG_DIR.parent
DEFAULT_JSON = REPO_ROOT / "data" / "statistics" / "layer_contrib.json"

# Bar order in the figure (Transformer block component); maps to JSON keys q,k,v,o,mlp
COMPONENT_LABELS: List[str] = ["K", "Q", "V", "O", "MLP"]
JSON_KEY_ORDER: List[str] = ["k", "q", "v", "o", "mlp"]

# JSON method key -> short plot key (for output filename, similar to original rq2_l2_...)
METHOD_FILE_TAG: Dict[str, str] = {
    "l2": "l2",
    "cosine": "cos",
    "mean_abs": "abs_mean",
    "max_abs": "abs_max",
    "sparse_update_rate_abs": "sparse_abs",
    "sparse_update_rate_relative": "sparse_rel",
    "intrinsic_fingerprint": "intrinsic_fingerprint",
}

METHOD_DISPLAY_NAME: Dict[str, str] = {
    "l2": "L2 distance",
    "cosine": "Cosine distance",
    "mean_abs": "Mean abs.",
    "max_abs": "Max abs.",
    "sparse_update_rate_abs": "Sparse abs.",
    "sparse_update_rate_relative": "Sparse rel.",
    "intrinsic_fingerprint": "Intrinsic fingerprint",
}


def savefig(name: str) -> None:
    """Save figure as PDF into the fig directory with tight layout."""
    path = os.path.join(str(FIG_DIR), name)
    plt.tight_layout()
    plt.savefig(path, format="pdf", bbox_inches="tight")
    print(f"Saved {path}")


def load_layer_contrib_json(path: Path) -> Dict[str, Dict[str, float]]:
    with path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    avg = data.get("avg_pct_across_nodes")
    if not isinstance(avg, dict) or not avg:
        raise ValueError(f"Missing or empty 'avg_pct_across_nodes' in {path}")
    cleaned: Dict[str, Dict[str, float]] = {}
    for method, by_layer in avg.items():
        if not isinstance(by_layer, dict):
            continue
        cleaned[str(method)] = {str(k).lower(): float(v) for k, v in by_layer.items()}
    return cleaned


def pct_to_normalized_contributions(by_layer: Dict[str, float]) -> np.ndarray:
    """Convert percentage shares to normalized [0,1] contributions in bar order K,Q,V,O,MLP."""
    pcts = np.array([by_layer.get(k, 0.0) for k in JSON_KEY_ORDER], dtype=np.float64)
    s = float(pcts.sum())
    if s > 0:
        return pcts / s
    return pcts


def plot_layer_contribution(
    metric_name: str,
    metric_display_name: str,
    contributions: np.ndarray,
    output_filename: str,
) -> None:
    """
    Plot bar chart showing contribution of different layers to a specific distance metric.

    Args:
        metric_name: Short name of the metric (for logging)
        metric_display_name: Display name for the metric
        contributions: Array of 5 values for [K, Q, V, O, MLP] contributions (normalized)
        output_filename: Output PDF filename
    """
    fig, ax = plt.subplots(figsize=(4.0, 2.8))
    bars = ax.bar(COMPONENT_LABELS, contributions, color="#4C72B0")

    ax.set_ylabel(f"Relative contribution to {metric_display_name}")
    ax.set_ylim(0, 0.6)
    y_pad = 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0])

    for bar, value in zip(bars, contributions):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + y_pad,
            f"{value:.2f}",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
        )

    savefig(output_filename)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description="Plot layer contribution bars from layer_contrib.json.")
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_JSON,
        help="Path to layer_contrib.json",
    )
    args = parser.parse_args()
    path = args.input.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)

    avg_pct = load_layer_contrib_json(path)

    for method_key, by_layer in sorted(avg_pct.items()):
        tag = METHOD_FILE_TAG.get(method_key, method_key)
        display = METHOD_DISPLAY_NAME.get(
            method_key, method_key.replace("_", " ").title()
        )
        contribs = pct_to_normalized_contributions(by_layer)
        out_name = f"rq2_{tag}_layer_contrib.pdf"
        plot_layer_contribution(
            metric_name=method_key,
            metric_display_name=display,
            contributions=contribs,
            output_filename=out_name,
        )


if __name__ == "__main__":
    main()
