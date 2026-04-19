from __future__ import annotations

import ast

from config import EVAL_TOKENIZERS
from repo_miner import _load_tokenizer
from stage3.exact.alias_codec import decode_exact_aliases, encode_exact_aliases
from stage3.routing.router import ABRoutingConfig


def _gpt4_tokenizer():
    cfg = EVAL_TOKENIZERS["gpt4"]
    return _load_tokenizer("gpt4", cfg)


def test_annotation_compound_spans_are_compressed_without_overlapping_inner_names() -> None:
    text = (
        "def normalize(\n"
        "    value: ResultPayload[NormalizedRecord],\n"
        ") -> ResultPayload[NormalizedRecord]:\n"
        "    cached: ResultPayload[NormalizedRecord] = value\n"
        "    return cached\n"
    )
    tokenizer, tok_type = _gpt4_tokenizer()
    res = encode_exact_aliases(
        text,
        tokenizer=tokenizer,
        tok_type=tok_type,
        route_cfg=ABRoutingConfig(),
        min_occ=2,
        min_net_gain=0,
        alias_style="short",
        alias_candidate_style="token_cost_sorted",
        enable_compound_spans=True,
        compound_min_raw_token_len=4,
        min_raw_token_len=1,
        max_alias_token_len=8,
    )
    assert any(e.field == "annotation" for e in res.entries)
    assert not any(e.literal == "ResultPayload" for e in res.entries)
    assert decode_exact_aliases(res.encoded_text, res.entries) == text
    ast.parse(res.encoded_text)


def test_import_module_compound_spans_are_compressed_and_roundtrip() -> None:
    text = (
        "from deeply.nested.service.runtime.client import api\n"
        "import deeply.nested.service.runtime.client\n"
        "from deeply.nested.service.runtime.client import models as runtime_models\n"
    )
    tokenizer, tok_type = _gpt4_tokenizer()
    res = encode_exact_aliases(
        text,
        tokenizer=tokenizer,
        tok_type=tok_type,
        route_cfg=ABRoutingConfig(),
        min_occ=2,
        min_net_gain=0,
        alias_style="short",
        alias_candidate_style="token_cost_sorted",
        enable_compound_spans=True,
        compound_min_raw_token_len=4,
        min_raw_token_len=1,
        max_alias_token_len=8,
    )
    assert any(
        e.field == "import_module" and e.literal == "deeply.nested.service.runtime.client"
        for e in res.entries
    )
    assert decode_exact_aliases(res.encoded_text, res.entries) == text
    ast.parse(res.encoded_text)
