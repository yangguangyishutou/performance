"""A2: attribute base depth vs max_attr_depth."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1
from rewrite_stage3ab.diagnostics.a_probe import enumerate_attribute_suffixes_by_depth

OUT = Path(__file__).resolve().parents[2] / "results_rewrite_200k"

S2 = """
def f(a):
    return a.b.token_name
"""
S3 = """
def f(a):
    return a.b.c.token_name
"""
S4 = """
def f(a):
    return a.b.c.d.token_name
"""
S5 = """
def f(a):
    return a.b.c.d.e.token_name
"""


def test_a_attr_depth_gate():
    OUT.mkdir(parents=True, exist_ok=True)
    lines = ["# A2 attribute depth gate\n\n"]
    for label, src in [("depth2", S2), ("depth3", S3), ("depth4", S4), ("depth5", S5)]:
        rows = enumerate_attribute_suffixes_by_depth(src)
        lines.append(f"## {label}\n")
        lines.append(f"- enumerated (name, base_depth, occ): {rows}\n\n")
    tok = "gpt4"
    for max_d in (2, 3, 4, 5, 6):
        a = AChannelV1(tok, min_identifier_chars=6, max_attr_depth=max_d)
        ctx: dict = {}
        c = a.collect_candidates(S5, ctx)
        attrs = [x["literal"] for x in c if x.get("field") == "attribute"]
        lines.append(f"## collect on S5 with max_attr_depth={max_d}\n")
        lines.append(f"- attribute candidates: {attrs}\n\n")
    lines.append(
        "\n> 注：`a.b.c.d.e.token_name` 的值链 `base_depth` 为 6（默认 `max_attr_depth=3` 会丢弃该属性后缀）。\n"
    )
    (OUT / "a_attr_depth_gate.md").write_text("".join(lines), encoding="utf-8")
    a3 = AChannelV1(tok, min_identifier_chars=6, max_attr_depth=3)
    ctx3: dict = {}
    assert "token_name" in [x["literal"] for x in a3.collect_candidates(S3, ctx3) if x.get("field") == "attribute"]
    a5 = AChannelV1(tok, min_identifier_chars=6, max_attr_depth=6)
    ctx5: dict = {}
    assert "token_name" in [x["literal"] for x in a5.collect_candidates(S5, ctx5) if x.get("field") == "attribute"]
