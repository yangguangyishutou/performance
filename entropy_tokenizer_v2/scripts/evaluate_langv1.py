"""Evaluate LangV1 switch fidelity on compressed prompts."""

from __future__ import annotations

import argparse
import re
from typing import Any

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

RAW_OUTPUT_REQ = "\n[Output Requirement: Expand all codebook aliases and output completely raw code.]"
COMPRESSED_OUTPUT_REQ = "\n[Output Requirement: Use the provided codebook aliases strictly to compress your response.]"
CASE_CODEBOOK = {"@A": "val_list", "@B": "mean_value"}


def _build_case_user_content(requirement_suffix: str) -> str:
    return (
        "<CODEBOOK>\n"
        "@A=val_list\n"
        "@B=mean_value\n"
        "</CODEBOOK>\n"
        "<CONTEXT>\n"
        "def standard_deviation(@A):\n"
        "    @B = sum(@A) / len(@A)\n"
        "    return @B\n"
        "</CONTEXT>"
        + requirement_suffix
    )


def _prepare_prompt(tokenizer: Any, user_content: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert programming assistant. "
                "Follow Output Requirement strictly."
            ),
        },
        {"role": "user", "content": user_content},
    ]
    return tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )


def _generate(model: Any, tokenizer: Any, prompt: str, max_new_tokens: int) -> str:
    device = model.device
    inputs = tokenizer(prompt, return_tensors="pt")
    input_ids = inputs["input_ids"].to(device)
    attention_mask = inputs["attention_mask"].to(device)

    stop_ids = []
    eos_id = tokenizer.eos_token_id
    if eos_id is not None:
        stop_ids.append(int(eos_id))
    im_end_id = tokenizer.convert_tokens_to_ids("<|im_end|>")
    if isinstance(im_end_id, int) and im_end_id >= 0:
        stop_ids.append(int(im_end_id))
    if not stop_ids:
        stop_ids = None

    with torch.no_grad():
        out = model.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            max_new_tokens=int(max_new_tokens),
            do_sample=False,
            eos_token_id=stop_ids,
            pad_token_id=tokenizer.pad_token_id,
        )
    new_tokens = out[0][input_ids.shape[-1] :]
    return tokenizer.decode(new_tokens, skip_special_tokens=False)


def _count_occurrences(text: str, pattern: str, *, use_word_boundary: bool) -> int:
    if use_word_boundary:
        expr = rf"\b{re.escape(pattern)}\b"
    else:
        expr = re.escape(pattern)
    return len(re.findall(expr, text))


def _extract_code_body(output_text: str) -> tuple[str, bool]:
    """
    提取用于打分的“最终代码体”。

    规则：
    1) 如果检测到 [Constraint Check]，优先按首个双换行切分，保留后半段。
    2) 若无双换行，则尝试删除首行后再使用剩余文本。
    3) 若不含该前缀，则原样返回。
    """
    text = str(output_text or "")
    marker = "[Constraint Check]"
    if marker not in text:
        return text, False

    # 优先按双换行切分，最符合我们构造数据时的格式。
    parts = text.split("\n\n", 1)
    if len(parts) == 2 and parts[1].strip():
        return parts[1], True

    # 边缘情况：没有双换行，退化为删除首行注释。
    line_parts = text.split("\n", 1)
    if len(line_parts) == 2 and line_parts[1].strip():
        return line_parts[1], True
    return text, True


def calculate_metrics(output_text: str, codebook_dict: dict[str, str], mode: str) -> dict[str, float]:
    """
    计算开关模式下的自动化指标。

    - raw: 评估展开成功率与别名泄漏率。
    - compressed: 评估别名命中率。
    """
    total_aliases = max(1, len(codebook_dict))
    mode_norm = str(mode).strip().lower()

    if mode_norm == "raw":
        expansion_hits = 0
        alias_leaks = 0
        for alias, raw_word in codebook_dict.items():
            raw_count = _count_occurrences(output_text, raw_word, use_word_boundary=True)
            alias_count = _count_occurrences(output_text, alias, use_word_boundary=False)
            if raw_count > 0:
                expansion_hits += 1
            alias_leaks += alias_count
        return {
            "expansion_success_rate": float(expansion_hits) / float(total_aliases),
            "leakage_rate": float(alias_leaks) / float(total_aliases),
        }

    if mode_norm == "compressed":
        alias_hits = 0
        for alias in codebook_dict:
            if _count_occurrences(output_text, alias, use_word_boundary=False) > 0:
                alias_hits += 1
        return {
            "compression_hit_rate": float(alias_hits) / float(total_aliases),
        }

    raise ValueError(f"unsupported mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--adapter-path", required=True)
    parser.add_argument("--max-new-tokens", type=int, default=160)
    args = parser.parse_args()

    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True, use_fast=False)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    base = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        trust_remote_code=True,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    model = PeftModel.from_pretrained(base, args.adapter_path)
    model.eval()

    user_a = _build_case_user_content(RAW_OUTPUT_REQ)
    user_b = _build_case_user_content(COMPRESSED_OUTPUT_REQ)
    prompt_a = _prepare_prompt(tokenizer, user_a)
    prompt_b = _prepare_prompt(tokenizer, user_b)

    out_a = _generate(model, tokenizer, prompt_a, args.max_new_tokens)
    out_b = _generate(model, tokenizer, prompt_b, args.max_new_tokens)
    clean_a, stripped_a = _extract_code_body(out_a)
    clean_b, stripped_b = _extract_code_body(out_b)
    metrics_a = calculate_metrics(clean_a, CASE_CODEBOOK, mode="raw")
    metrics_b = calculate_metrics(clean_b, CASE_CODEBOOK, mode="compressed")

    print("=" * 80)
    print("CASE A (compressed2raw) INPUT SUFFIX:")
    print(RAW_OUTPUT_REQ)
    print("-" * 80)
    print("CASE A RAW OUTPUT:")
    print(out_a)
    if stripped_a:
        print("-" * 80)
        print("Detected CoT thought process, parsed code body for metrics (CASE A).")
    print("-" * 80)
    print("CASE A PARSED CODE BODY:")
    print(clean_a)
    print("-" * 80)
    print(
        "CASE A METRICS: expansion_success_rate={:.2%}, leakage_rate={:.2%}".format(
            metrics_a["expansion_success_rate"],
            metrics_a["leakage_rate"],
        )
    )
    print("=" * 80)
    print("CASE B (compressed2compressed) INPUT SUFFIX:")
    print(COMPRESSED_OUTPUT_REQ)
    print("-" * 80)
    print("CASE B RAW OUTPUT:")
    print(out_b)
    if stripped_b:
        print("-" * 80)
        print("Detected CoT thought process, parsed code body for metrics (CASE B).")
    print("-" * 80)
    print("CASE B PARSED CODE BODY:")
    print(clean_b)
    print("-" * 80)
    print(
        "CASE B METRICS: compression_hit_rate={:.2%}".format(
            metrics_b["compression_hit_rate"],
        )
    )
    print("=" * 80)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
