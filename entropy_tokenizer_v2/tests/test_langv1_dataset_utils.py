from config import EVAL_TOKENIZERS
from eval.langv1_dataset_utils import (
    build_cpt_record_text,
    build_humaneval_structured_prompt,
    build_sft_prompt,
    split_prefix_completion,
)


def test_qwen_tokenizer_preset_exists() -> None:
    cfg = EVAL_TOKENIZERS["qwen25-coder-15b"]
    assert cfg["type"] == "hf"
    assert cfg["name"] == "Qwen/Qwen2.5-Coder-1.5B"


def test_split_prefix_completion_prefers_line_boundary() -> None:
    text = (
        "def foo(x):\n"
        "    total = x + 1\n"
        "    if total > 3:\n"
        "        return total\n"
        "    return x\n"
    ) * 6
    prefix, completion = split_prefix_completion(
        text,
        prompt_ratio=0.5,
        min_prompt_chars=40,
        min_completion_chars=30,
    )
    assert prefix.endswith("\n")
    assert prefix.strip()
    assert completion.strip()
    assert prefix + completion == text


def test_build_sft_prompt_for_compressed_mode_includes_dictionary() -> None:
    prompt = build_sft_prompt(
        "<SYN_0> foo x",
        prompt_mode="compressed_to_compressed",
        dynamic_dict_text="__ab0 => user_name_long_identifier",
    )
    assert "<LANGV1_SFT>" in prompt
    assert "<DYNAMIC_DICT>" in prompt
    assert "__ab0 => user_name_long_identifier" in prompt
    assert "<COMPRESSED_PREFIX>" in prompt
    assert "<CONTINUATION>" in prompt


def test_build_sft_prompt_for_raw_mode_omits_compressed_primer() -> None:
    prompt = build_sft_prompt(
        "def foo(x):\n    return x\n",
        prompt_mode="raw_to_compressed",
    )
    assert "<LANGV1_SFT>" in prompt
    assert "<DYNAMIC_DICT>" not in prompt
    assert "<RAW_PREFIX>" in prompt


def test_build_cpt_record_text_uses_structured_blocks() -> None:
    text = build_cpt_record_text(
        "__ab0 = 1",
        dynamic_dict_text="__ab0 => user_name_long_identifier",
    )
    assert "<LANGV1_CPT>" in text
    assert "<DYNAMIC_DICT>" in text
    assert "<COMPRESSED_CODE>" in text


def test_build_humaneval_structured_prompt_uses_dynamic_dict_only() -> None:
    prompt = build_humaneval_structured_prompt(
        support_text="# [Compressed Support 1]\n__ab0 = 1",
        compressed=True,
        dynamic_dict_text="__ab0 => user_name_long_identifier",
        task_prompt="def foo(x):\n    pass\n",
    )
    assert "<LANGV1_HUMANEVAL>" in prompt
    assert "<DYNAMIC_DICT>" in prompt
    assert "<COMPRESSED_SUPPORT>" in prompt
    assert "<TASK_PROMPT>" in prompt
