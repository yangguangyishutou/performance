"""Helpers for LangV1 learned-language dataset construction."""

from __future__ import annotations

from typing import Literal

PromptMode = Literal["compressed_to_compressed", "raw_to_compressed"]

LANGV1_CPT_TAG = "LANGV1_CPT"
LANGV1_SFT_TAG = "LANGV1_SFT"
LANGV1_HUMANEVAL_TAG = "LANGV1_HUMANEVAL"
DYNAMIC_DICT_TAG = "DYNAMIC_DICT"
COMPRESSED_CODE_TAG = "COMPRESSED_CODE"
COMPRESSED_PREFIX_TAG = "COMPRESSED_PREFIX"
RAW_PREFIX_TAG = "RAW_PREFIX"
COMPRESSED_SUPPORT_TAG = "COMPRESSED_SUPPORT"
RAW_SUPPORT_TAG = "RAW_SUPPORT"
TASK_PROMPT_TAG = "TASK_PROMPT"
CONTINUATION_TAG = "CONTINUATION"


def choose_split_index(
    text: str,
    *,
    prompt_ratio: float = 0.6,
    min_prompt_chars: int = 192,
    min_completion_chars: int = 96,
) -> int:
    raw = str(text or "")
    total = len(raw)
    if total < int(min_prompt_chars) + int(min_completion_chars):
        raise ValueError("text is too short for the requested split")

    lower = int(min_prompt_chars)
    upper = total - int(min_completion_chars)
    target = max(lower, min(upper, int(total * float(prompt_ratio))))

    candidates = [idx + 1 for idx, ch in enumerate(raw) if ch == "\n" and lower <= idx + 1 <= upper]
    if not candidates:
        return target
    return min(candidates, key=lambda idx: (abs(idx - target), -idx))


def split_prefix_completion(
    text: str,
    *,
    prompt_ratio: float = 0.6,
    min_prompt_chars: int = 192,
    min_completion_chars: int = 96,
) -> tuple[str, str]:
    split_idx = choose_split_index(
        text,
        prompt_ratio=prompt_ratio,
        min_prompt_chars=min_prompt_chars,
        min_completion_chars=min_completion_chars,
    )
    prefix = text[:split_idx]
    completion = text[split_idx:]
    if not prefix.strip():
        raise ValueError("empty prefix after split")
    if not completion.strip():
        raise ValueError("empty completion after split")
    return prefix, completion


def render_tag_block(tag: str, text: str) -> str:
    body = str(text or "").rstrip()
    if not body:
        return ""
    return f"<{tag}>\n{body}\n</{tag}>"


def render_dynamic_dict_block(dynamic_dict_text: str) -> str:
    return render_tag_block(DYNAMIC_DICT_TAG, dynamic_dict_text)


def build_cpt_record_text(
    compressed_text: str,
    *,
    dynamic_dict_text: str = "",
) -> str:
    parts = [f"<{LANGV1_CPT_TAG}>"]
    dyn = render_dynamic_dict_block(dynamic_dict_text)
    if dyn:
        parts.append(dyn)
    parts.append(render_tag_block(COMPRESSED_CODE_TAG, compressed_text))
    parts.append(f"</{LANGV1_CPT_TAG}>")
    return "\n".join(x for x in parts if x).rstrip() + "\n"


def build_sft_prompt(
    prefix_text: str,
    *,
    prompt_mode: PromptMode,
    dynamic_dict_text: str = "",
) -> str:
    mode = str(prompt_mode).strip().lower()
    if mode not in {"compressed_to_compressed", "raw_to_compressed"}:
        raise ValueError(f"unsupported prompt_mode: {prompt_mode}")

    parts = [f"<{LANGV1_SFT_TAG}>"]
    dyn = render_dynamic_dict_block(dynamic_dict_text)
    if dyn:
        parts.append(dyn)
    tag = COMPRESSED_PREFIX_TAG if mode == "compressed_to_compressed" else RAW_PREFIX_TAG
    parts.append(render_tag_block(tag, prefix_text))
    parts.append(f"<{CONTINUATION_TAG}>")
    return "\n\n".join(parts).rstrip() + "\n"


def build_humaneval_structured_prompt(
    *,
    support_text: str,
    compressed: bool,
    dynamic_dict_text: str = "",
    task_prompt: str,
) -> str:
    parts = [f"<{LANGV1_HUMANEVAL_TAG}>"]
    if compressed:
        dyn = render_dynamic_dict_block(dynamic_dict_text)
        if dyn:
            parts.append(dyn)
        parts.append(render_tag_block(COMPRESSED_SUPPORT_TAG, support_text))
    else:
        parts.append(render_tag_block(RAW_SUPPORT_TAG, support_text))
    parts.append(render_tag_block(TASK_PROMPT_TAG, task_prompt))
    parts.append(f"<{CONTINUATION_TAG}>")
    return "\n\n".join(x for x in parts if x).rstrip() + "\n"
