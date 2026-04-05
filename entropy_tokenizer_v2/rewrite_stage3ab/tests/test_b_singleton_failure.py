"""B1: singleton cluster cannot be evaluated (insufficient_members)."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.channels.b_channel.implementation_v1 import BChannelV1

OUT = Path(__file__).resolve().parents[2] / "results_rewrite_200k"


def test_b_singleton_insufficient_members():
    OUT.mkdir(parents=True, exist_ok=True)
    b = BChannelV1()
    ctx = {"tokenizer_key": "gpt4", "source_id": "t"}
    cl = {
        "cluster_id": "single",
        "texts": ['"""This is a long docstring that only appears once in isolation."""'],
        "members": [],
        "member_spans": [],
        "cluster_path": "synthetic",
    }
    ev = b.evaluate_cluster(cl, ctx)
    lines = [
        "# B1 singleton failure\n\n",
        f"- reason: {ev.get('reason')}\n",
        f"- ok: {ev.get('ok')}\n",
    ]
    (OUT / "b_singleton_failure.md").write_text("".join(lines), encoding="utf-8")
    assert ev.get("reason") == "insufficient_members"
