from __future__ import annotations

import json
from dataclasses import dataclass

from config import EVAL_TOKENIZERS, resolve_hybrid_ab_settings
from repo_miner import _load_tokenizer
from stage3.backends.hybrid_ab_backend import HybridABStage3Backend
from stage3.global_dictionary import load_global_dictionary


def test_load_global_dictionary_parses_entries(tmp_path):
    fp = tmp_path / "global_dict.json"
    fp.write_text(
        json.dumps(
            {
                "version": "v1",
                "a_entries": [
                    {"field": "variable", "literal": "foo_bar_long_name", "alias": "g0"}
                ],
                "b_entries": [
                    {
                        "norm_key": "Artifact <hex> was linked to session <uuid> during triage flow",
                        "code": "gb0",
                        "definition": "artifact session template",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    gd = load_global_dictionary(fp)
    assert gd.a_alias_map[("variable", "foo_bar_long_name")] == "g0"
    assert gd.b_norm_map["Artifact <hex> was linked to session <uuid> during triage flow"] == "gb0"


@dataclass
class _RepoCfg:
    stage3_ab_summary: dict


def test_hybrid_ab_backend_uses_global_dictionary(tmp_path):
    fp = tmp_path / "global_dict.json"
    fp.write_text(
        json.dumps(
            {
                "version": "v1",
                "a_entries": [
                    {"field": "variable", "literal": "user_profile_sync_payload", "alias": "g0"}
                ],
                "b_entries": [
                    {
                        "norm_key": "Artifact <hex> was linked to session <uuid> during triage flow",
                        "code": "gb0",
                        "definition": "artifact session template",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    summary = resolve_hybrid_ab_settings("gpt4")
    summary["mode"] = "hybrid"
    summary["enable_b"] = True
    summary["global_dict_enabled"] = True
    summary["global_dict_path"] = str(fp)
    summary["global_dict_charge_vocab"] = False

    tok, tt = _load_tokenizer("gpt4", EVAL_TOKENIZERS["gpt4"])
    text = (
        "user_profile_sync_payload = 1\n"
        "print(user_profile_sync_payload)\n"
        "user_profile_sync_payload += 1\n"
        "a = 'Artifact 0xA91B3F was linked to session 3f2504e0-4f89-11d3-9a0c-0305e82c3301 during triage flow'\n"
        "b = 'Artifact 0xB77CCD was linked to session 6ba7b810-9dad-11d1-80b4-00c04fd430c8 during triage flow'\n"
    )
    backend = HybridABStage3Backend()
    res = backend.encode(text, _RepoCfg(summary), tokenizer=tok, tok_type=tt)
    m = res.metrics
    assert m.get("stage3_ab_global_dict_enabled") is True
    assert (
        int(m.get("stage3_ab_a_global_used_entries", 0))
        + int(m.get("stage3_ab_b_global_used_codes", 0))
    ) >= 1
    assert int(m.get("stage3_ab_global_sequence_saved", 0)) > 0
