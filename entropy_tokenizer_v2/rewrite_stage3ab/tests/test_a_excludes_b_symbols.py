"""A must not alias B reference symbols (_bN, _BREF*)."""

from __future__ import annotations

from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1

SRC = """
_b0 = 1
_BREF1 = 2
def f():
    return verylongname_xyzzy + _b0 + _BREF1
verylongname_xyzzy = 0
"""


def test_a_collect_skips_b_style_symbols() -> None:
    a = AChannelV1("gpt4", min_identifier_chars=8)
    ctx: dict = {"b_generated_symbols": {"_b0", "_BREF1"}}
    cands = a.collect_candidates(SRC, ctx)
    literals = {str(c.get("literal")) for c in cands}
    assert "_b0" not in literals
    assert "_BREF1" not in literals
    assert "verylongname_xyzzy" in literals


def test_a_collect_skips_prefix_even_without_ctx_set() -> None:
    a = AChannelV1("gpt4", min_identifier_chars=4)
    ctx: dict = {}
    src2 = "x = _b3 + _BREF9\n"
    cands = a.collect_candidates(src2, ctx)
    literals = {str(c.get("literal")) for c in cands}
    assert "_b3" not in literals
    assert "_BREF9" not in literals
