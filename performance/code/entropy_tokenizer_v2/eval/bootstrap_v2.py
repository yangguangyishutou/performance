"""将 `entropy_tokenizer_v2` 包根目录加入 sys.path，供本目录下评估脚本导入。"""
from __future__ import annotations

import sys
from pathlib import Path

# 本文件位于 .../entropy_tokenizer_v2/eval/bootstrap_v2.py
V2_DIR = Path(__file__).resolve().parent.parent
CODE_DIR = V2_DIR.parent  # .../performance/code


def ensure() -> None:
    p = str(V2_DIR)
    if p not in sys.path:
        sys.path.insert(0, p)


def ensure_with_simpy() -> None:
    ensure()
    s = str(CODE_DIR / "Simpy-master")
    if s not in sys.path:
        sys.path.insert(0, s)
