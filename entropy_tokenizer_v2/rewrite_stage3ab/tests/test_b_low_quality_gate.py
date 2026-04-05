"""B2: low-quality gate on semantic-near strings."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.channels.b_channel.clustering_v1 import word_jaccard_literal
from rewrite_stage3ab.channels.b_channel.implementation_v1 import BChannelV1

OUT = Path(__file__).resolve().parents[2] / "results_rewrite_200k"

T1 = '"failed to load config from cache"'
T2 = '"unable to restore settings from disk"'
T3 = '"cannot recover user profile"'


def test_b_low_quality_gate_semantic_near():
    OUT.mkdir(parents=True, exist_ok=True)
    pairs = [
        word_jaccard_literal(T1, T2),
        word_jaccard_literal(T1, T3),
        word_jaccard_literal(T2, T3),
    ]
    avg = sum(pairs) / len(pairs)
    b = BChannelV1()
    ctx = {"tokenizer_key": "gpt4", "source_id": "t"}
    cl = {
        "cluster_id": "sem",
        "texts": [T1, T2, T3],
        "members": [],
        "member_spans": [],
        "cluster_path": "standard_hdbscan_or_lexical",
        "fallback_exact": False,
        "fallback_near_dup": False,
    }
    ev = b.evaluate_cluster(cl, ctx)
    lines = [
        "# B2 low-quality gate\n\n",
        f"- pairwise word_jaccard: {pairs}\n",
        f"- average: {avg:.4f}\n",
        f"- evaluate ok: {ev.get('ok')} reason: {ev.get('reason')}\n",
    ]
    (OUT / "b_low_quality_gate.md").write_text("".join(lines), encoding="utf-8")
    assert ev.get("reason") == "rejected_for_low_quality"
