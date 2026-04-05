"""A3: string_exact_path gating."""

from __future__ import annotations

from pathlib import Path

from rewrite_stage3ab.channels.a_channel.implementation_v1 import AChannelV1
from rewrite_stage3ab.diagnostics.a_probe import count_string_exact_path_eligibility

OUT = Path(__file__).resolve().parents[2] / "results_rewrite_200k"

TEXT = '''
# side note
module_path = "com.example.long.path.to.resource"
'''


def test_a_string_exact_path_gate():
    OUT.mkdir(parents=True, exist_ok=True)
    path = "com.example.long.path.to.resource"
    lines = ["# A3 string_exact_path\n\n"]
    for allow in (False, True):
        for mismatch in (False, True):
            ctx = {
                "string_exact_path": path,
                "allow_string_exact_path": allow,
            }
            if mismatch:
                ctx["string_exact_path_expected_occ"] = 99
            a = AChannelV1("gpt4", min_identifier_chars=10)
            cands = a.collect_candidates(TEXT, ctx)
            fields = [c.get("field") for c in cands]
            probe = count_string_exact_path_eligibility(
                TEXT, exact_path=path, allow=allow, expected_occ=(99 if mismatch else None)
            )
            lines.append(f"## allow={allow} mismatch_expected_occ={mismatch}\n")
            lines.append(f"- probe: {probe}\n")
            lines.append(f"- candidate fields: {fields}\n\n")
            if allow and not mismatch:
                assert "string_exact_path" in fields
            else:
                assert "string_exact_path" not in fields
    (OUT / "a_string_exact_path_gate.md").write_text("".join(lines), encoding="utf-8")
