from __future__ import annotations

from config import EVAL_TOKENIZERS
from repo_miner import _load_tokenizer
from stage3.lexical.semantic_codec import encode_semantic_strings


def test_semantic_codec_clusters_similar_texts():
    tok, tt = _load_tokenizer("gpt4", EVAL_TOKENIZERS["gpt4"])
    text = (
        "a = 'Please verify the user login request before proceeding now and include account context details for the current session'\n"
        "b = 'Please verify user login request before proceeding immediately and include account context details for current session'\n"
        "c = 'Please verify the user login request before proceeding now and include account context details for the current session'\n"
        "d = 'Please verify user login request before proceeding immediately and include account context details for current session'\n"
    )
    res = encode_semantic_strings(
        text,
        tokenizer=tok,
        tok_type=tt,
        similarity_threshold=0.70,
        risk_threshold=0.60,
        min_cluster_size=2,
    )
    assert res.candidates >= 2
    assert res.used_clusters >= 1
    assert res.similarity_kind == "lexical_bow_cosine"
    assert res.mode == "lexical_free_text_baseline"


def test_semantic_codec_low_similarity_fallback():
    tok, tt = _load_tokenizer("gpt4", EVAL_TOKENIZERS["gpt4"])
    text = (
        "a = 'database connection timeout happened in worker'\n"
        "b = 'rendering colorful chart with bar values'\n"
    )
    res = encode_semantic_strings(
        text,
        tokenizer=tok,
        tok_type=tt,
        similarity_threshold=0.95,
        risk_threshold=0.95,
        min_cluster_size=2,
    )
    assert res.used_clusters == 0


def test_semantic_codec_supports_compact_code_and_net_greedy():
    tok, tt = _load_tokenizer("gpt4", EVAL_TOKENIZERS["gpt4"])
    text = (
        "a = 'User profile update failed: timeout while syncing account metadata for tenant alpha in region east'\n"
        "b = 'User profile update failed: timeout while syncing account metadata for tenant beta in region east'\n"
        "c = 'User profile update failed: timeout while syncing account metadata for tenant gamma in region east'\n"
        "d = 'User profile update failed: timeout while syncing account metadata for tenant delta in region east'\n"
    )
    res = encode_semantic_strings(
        text,
        tokenizer=tok,
        tok_type=tt,
        similarity_threshold=0.65,
        risk_threshold=0.55,
        min_cluster_size=2,
        code_style="base62",
        code_prefix="b",
        member_select_mode="net_greedy",
        definition_mode="shared_terms",
        similarity_norm="light",
    )
    assert res.used_clusters >= 1
    assert any(e.get("token") == "'b0'" for e in res.vocab_entries)


def test_semantic_codec_uses_global_norm_codebook():
    tok, tt = _load_tokenizer("gpt4", EVAL_TOKENIZERS["gpt4"])
    text = (
        "a = 'Artifact 0xA91B3F was linked to session 3f2504e0-4f89-11d3-9a0c-0305e82c3301 during triage flow'\n"
        "b = 'Artifact 0xB77CCD was linked to session 6ba7b810-9dad-11d1-80b4-00c04fd430c8 during triage flow'\n"
    )
    res = encode_semantic_strings(
        text,
        tokenizer=tok,
        tok_type=tt,
        similarity_threshold=0.95,
        risk_threshold=0.95,
        min_cluster_size=2,
        similarity_norm="light",
        global_norm_codebook={"Artifact <hex> was linked to session <uuid> during triage flow": "gb0"},
        global_code_definition={"gb0": "artifact session template"},
    )
    assert res.global_used_codes >= 1
    assert res.global_used_literals >= 2
    assert res.global_sequence_saved > 0
