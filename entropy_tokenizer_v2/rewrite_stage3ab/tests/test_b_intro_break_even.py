"""B3: intro / net vs repeat count for identical literals."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.channels.b_channel.reference_codec import ReferenceCodecV1

OUT = Path(__file__).resolve().parents[2] / "results_rewrite_200k"

LIT = '"xyzzy_duplicate_token_sink_abc"'


def test_b_intro_break_even_table():
    OUT.mkdir(parents=True, exist_ok=True)
    codec = ReferenceCodecV1()
    tok = "gpt4"
    lines = ["# B3 intro break-even (identical literal repeated)\n\n", "| n | raw_total | intro | ref_total | net |\n", "|---|----------|-------|----------|-----|\n"]
    for n in (2, 3, 4, 5):
        members = [LIT] * n
        rep = codec.select_representative(list(dict.fromkeys(members)), {"tokenizer_key": tok})
        sym = "_b0"
        sub = {
            "tokenizer_key": tok,
            "cluster_members": members,
            "member_spans": [],
            "cluster_path": "test",
            "fallback_reason": "",
        }
        em = codec.emit(rep, sym, sub)
        lines.append(
            f"| {n} | {em.raw_total_true} | {em.intro_tokens_true} | {em.ref_total_true} | {em.net_true} |\n"
        )
    (OUT / "b_intro_break_even.md").write_text("".join(lines), encoding="utf-8")
    em2 = codec.emit(
        LIT,
        "_b0",
        {
            "tokenizer_key": tok,
            "cluster_members": [LIT, LIT],
            "member_spans": [],
        },
    )
    assert em2.net_true != 0 or em2.raw_total_true > 0
