#!/usr/bin/env python3
"""
Safe fast-try runner for the existing 200k StarCoder Stage3 AB experiment.

This version writes to a separate results root so the baseline
results/stage3ab_starcoder_200k/ directory is not overwritten.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)


def _setdefault(name: str, value: str) -> None:
    os.environ.setdefault(name, value)


def main() -> None:
    _setdefault("ET_STAGE3_BACKEND", "hybrid_ab")
    _setdefault("ET_STAGE3_AB_MODE", "hybrid")
    _setdefault("ET_STAGE3_AB_ENABLE_B", "1")

    # Write all outputs into a separate root: entropy_tokenizer_v2/results_fast_try/...
    _setdefault("ET_RESULTS_DIR", str(ROOT / "results_fast_try"))

    # A channel relaxations.
    _setdefault("ET_STAGE3_AB_A_MIN_OCC", "2")
    _setdefault("ET_STAGE3_AB_MIN_RAW_TOKEN_LEN", "2")
    _setdefault("ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN", "3")
    _setdefault("ET_STAGE3_AB_A_ALIAS_RANK_POOL_CAP", "64")
    _setdefault("ET_STAGE3_AB_A_COMBO_GREEDY", "1")
    _setdefault("ET_STAGE3_AB_A_COMBO_MAX", "48")
    _setdefault("ET_STAGE3_AB_A_CONTEXT_GAIN_MARGIN", "0")

    # B channel relaxations.
    _setdefault("ET_STAGE3_AB_B_CHANNEL_PRIORITY", "normal")
    _setdefault("ET_STAGE3_AB_B_SIMILARITY_KIND", "mixed")
    _setdefault("ET_STAGE3_AB_B_LEXICAL_WEIGHT", "0.6")
    _setdefault("ET_STAGE3_AB_B_CHAR_WEIGHT", "0.4")
    _setdefault("ET_STAGE3_AB_B_SIMILARITY_THRESHOLD", "0.78")
    _setdefault("ET_STAGE3_AB_B_RISK_THRESHOLD", "0.68")
    _setdefault("ET_STAGE3_AB_B_MIN_CLUSTER_SIZE", "1")

    # Let Stage2 preserve some high-value free-text for B unless caller disables it.
    _setdefault("ET_STAGE2_B_STARVATION_PROBE", "1")

    target = ROOT / "scripts" / "eval_stage3ab_starcoder_200k.py"
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
