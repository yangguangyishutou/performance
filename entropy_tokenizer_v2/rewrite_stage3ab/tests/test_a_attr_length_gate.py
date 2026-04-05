"""A1: attribute / variable length gate vs min_identifier_chars (pytest + markdown)."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1

OUT = Path(__file__).resolve().parents[2] / "results_rewrite_200k"
SAMPLE = '''
class C:
    def run(self):
        x = self.config
        y = self.headers
        z = self.profile
        w = self.configuration
        return x + y + z + w
'''


def test_a_attr_length_gate_collect_variants():
    OUT.mkdir(parents=True, exist_ok=True)
    tok = "gpt4"
    lines = [
        "# A1 attribute length gate\n",
        "Sample uses attrs: config(6), headers(7), profile(7), configuration(13)\n\n",
        "> 注：`min_identifier_chars=8` 时仍只会留下 `configuration`，`headers`/`profile` 需阈值≤7。\n\n",
    ]
    for m in (10, 8, 6):
        a = AChannelV1(tok, min_identifier_chars=m, max_attr_depth=3)
        ctx: dict = {}
        cands = a.collect_candidates(SAMPLE, ctx)
        attrs = sorted([c["literal"] for c in cands if c.get("field") == "attribute"])
        lines.append(f"## min_identifier_chars={m}\n")
        lines.append(f"- n_candidates_total: {len(cands)}\n")
        lines.append(f"- attribute_literals: {attrs}\n\n")
        assert "configuration" in attrs
        if m <= 6:
            assert "config" in attrs
            assert "profile" in attrs
            assert "headers" in attrs
    (OUT / "a_attr_length_gate.md").write_text("".join(lines), encoding="utf-8")
