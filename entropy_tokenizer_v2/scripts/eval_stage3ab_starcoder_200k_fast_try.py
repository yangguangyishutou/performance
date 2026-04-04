#!/usr/bin/env python3
"""
Fast-try runner for the existing 200k StarCoder Stage3 AB experiment.

Goal: quickly test a less conservative configuration without rewriting the
current pipeline. This script only sets environment overrides, then delegates
execution to the committed 200k runner.

Key relaxations (chosen to match the current bottlenecks):
- A channel: lower entry threshold and widen alias search / combo search.
- B channel: remove low-priority suppression, lower lexical thresholds,
  allow singleton clusters to go through real gain checks, and enable mixed
  lexical+char similarity.
- Optional starvation probe: can be enabled via env to preserve some free-text
  before destructive Stage2 cleaning.
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
    # Keep the same experiment shape: gpt4 + hybrid_ab + 200k StarCoder.
    _setdefault("ET_STAGE3_BACKEND", "hybrid_ab")
    _setdefault("ET_STAGE3_AB_MODE", "hybrid")
    _setdefault("ET_STAGE3_AB_ENABLE_B", "1")

    # Route outputs to a sibling directory so we do not overwrite the baseline run.
    _setdefault("ET_RESULTS_DIR", str(ROOT / "results"))
    _setdefault("ET_STAGE3AB_FAST_TRY_OUT_SUBDIR", "stage3ab_starcoder_200k_fast_try")

    # A channel: relax the conservative GPT-4 gate.
    _setdefault("ET_STAGE3_AB_A_MIN_OCC", "2")
    _setdefault("ET_STAGE3_AB_MIN_RAW_TOKEN_LEN", "2")
    _setdefault("ET_STAGE3_AB_MAX_ALIAS_TOKEN_LEN", "3")
    _setdefault("ET_STAGE3_AB_A_ALIAS_RANK_POOL_CAP", "64")
    _setdefault("ET_STAGE3_AB_A_COMBO_GREEDY", "1")
    _setdefault("ET_STAGE3_AB_A_COMBO_MAX", "48")
    _setdefault("ET_STAGE3_AB_A_CONTEXT_GAIN_MARGIN", "0")

    # B channel: stop suppressing GPT-4 B by default and soften the cluster gate.
    _setdefault("ET_STAGE3_AB_B_CHANNEL_PRIORITY", "normal")
    _setdefault("ET_STAGE3_AB_B_SIMILARITY_KIND", "mixed")
    _setdefault("ET_STAGE3_AB_B_LEXICAL_WEIGHT", "0.6")
    _setdefault("ET_STAGE3_AB_B_CHAR_WEIGHT", "0.4")
    _setdefault("ET_STAGE3_AB_B_SIMILARITY_THRESHOLD", "0.78")
    _setdefault("ET_STAGE3_AB_B_RISK_THRESHOLD", "0.68")
    _setdefault("ET_STAGE3_AB_B_MIN_CLUSTER_SIZE", "1")

    # Optional: preserve some Stage2 free-text for B if the caller wants it.
    # Default is on for this quick try, but the user may override to 0 in shell.
    _setdefault("ET_STAGE2_B_STARVATION_PROBE", "1")

    # Reuse the existing committed 200k runner.
    target = ROOT / "scripts" / "eval_stage3ab_starcoder_200k.py"
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
