"""Qwen SFT dataset and collator with strict ChatML loss masking."""

from __future__ import annotations

import argparse
import json
import logging
import tempfile
from pathlib import Path
from typing import Any, Iterable, Optional

import torch
from torch.utils.data import Dataset
from transformers import AutoTokenizer, PreTrainedTokenizerBase

IM_START = "<|im_start|>"
IM_END = "<|im_end|>"
IGNORE_INDEX = -100


class QwenSFTDataset(Dataset):
    """读取 OpenAI messages JSONL，并按 Qwen ChatML 规则构建训练样本。"""

    def __init__(
        self,
        jsonl_path: Path | str,
        tokenizer: PreTrainedTokenizerBase,
        *,
        max_length: Optional[int] = None,
    ) -> None:
        self.jsonl_path = Path(jsonl_path)
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.rows: list[dict[str, Any]] = self._load_rows(self.jsonl_path)

    @staticmethod
    def _load_rows(path: Path) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                raw = line.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError as exc:
                    logging.warning("Skip invalid JSON at line %d: %s", line_no, exc)
                    continue
                msgs = obj.get("messages")
                if not isinstance(msgs, list) or not msgs:
                    logging.warning("Skip line %d: missing messages", line_no)
                    continue
                rows.append(obj)
        return rows

    def __len__(self) -> int:
        return len(self.rows)

    def _encode(self, text: str) -> list[int]:
        return self.tokenizer(text, add_special_tokens=False)["input_ids"]

    def _append_segment(
        self,
        input_ids: list[int],
        labels: list[int],
        text: str,
        *,
        trainable: bool,
    ) -> None:
        seg_ids = self._encode(text)
        input_ids.extend(seg_ids)
        if trainable:
            labels.extend(seg_ids)
        else:
            labels.extend([IGNORE_INDEX] * len(seg_ids))

    def _build_single(self, row: dict[str, Any]) -> dict[str, Any]:
        input_ids: list[int] = []
        labels: list[int] = []
        messages = row.get("messages", [])

        for msg in messages:
            role = str(msg.get("role", "")).strip().lower()
            content = str(msg.get("content", ""))

            if role in {"system", "user"}:
                # system/user 整段都不参与 loss。
                full_turn = f"{IM_START}{role}\n{content}{IM_END}\n"
                self._append_segment(
                    input_ids,
                    labels,
                    full_turn,
                    trainable=False,
                )
                continue

            if role == "assistant":
                # assistant 的 header 掩码，content 与 <|im_end|> 参与 loss。
                header = f"{IM_START}assistant\n"
                self._append_segment(
                    input_ids,
                    labels,
                    header,
                    trainable=False,
                )
                self._append_segment(
                    input_ids,
                    labels,
                    content,
                    trainable=True,
                )
                self._append_segment(
                    input_ids,
                    labels,
                    IM_END,
                    trainable=True,
                )
                # turn 之间换行符不参与 loss，避免把结构分隔符学进目标。
                self._append_segment(
                    input_ids,
                    labels,
                    "\n",
                    trainable=False,
                )
                continue

            # 未知 role：按非目标文本处理，保证健壮性。
            fallback = f"{IM_START}{role}\n{content}{IM_END}\n"
            self._append_segment(
                input_ids,
                labels,
                fallback,
                trainable=False,
            )

        if self.max_length is not None and self.max_length > 0:
            input_ids = input_ids[: self.max_length]
            labels = labels[: self.max_length]

        attention_mask = [1] * len(input_ids)
        return {
            "task_id": str(row.get("task_id", "")),
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
        }

    def __getitem__(self, idx: int) -> dict[str, Any]:
        return self._build_single(self.rows[idx])


class DataCollatorForQwenSFT:
    """动态 padding，并保证 pad 位置 labels 为 -100。"""

    def __init__(
        self,
        tokenizer: PreTrainedTokenizerBase,
        *,
        pad_to_multiple_of: Optional[int] = None,
    ) -> None:
        self.tokenizer = tokenizer
        self.pad_to_multiple_of = pad_to_multiple_of
        if self.tokenizer.pad_token_id is None:
            raise ValueError("Tokenizer pad_token_id is required for dynamic padding.")

    def __call__(self, features: list[dict[str, Any]]) -> dict[str, torch.Tensor]:
        if not features:
            raise ValueError("Empty features passed to collator.")

        max_len = max(len(x["input_ids"]) for x in features)
        if self.pad_to_multiple_of and self.pad_to_multiple_of > 0:
            remainder = max_len % self.pad_to_multiple_of
            if remainder != 0:
                max_len += self.pad_to_multiple_of - remainder

        batch_input_ids: list[list[int]] = []
        batch_attention_mask: list[list[int]] = []
        batch_labels: list[list[int]] = []

        for feat in features:
            input_ids = list(feat["input_ids"])
            attention_mask = list(feat["attention_mask"])
            labels = list(feat["labels"])

            pad_len = max_len - len(input_ids)
            if pad_len > 0:
                input_ids.extend([int(self.tokenizer.pad_token_id)] * pad_len)
                attention_mask.extend([0] * pad_len)
                labels.extend([IGNORE_INDEX] * pad_len)

            batch_input_ids.append(input_ids)
            batch_attention_mask.append(attention_mask)
            batch_labels.append(labels)

        return {
            "input_ids": torch.tensor(batch_input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(batch_attention_mask, dtype=torch.long),
            "labels": torch.tensor(batch_labels, dtype=torch.long),
        }


def _iter_debug_tokens(
    tokenizer: PreTrainedTokenizerBase,
    input_ids: Iterable[int],
    labels: Iterable[int],
) -> Iterable[str]:
    for tid, lab in zip(input_ids, labels):
        token_str = tokenizer.convert_ids_to_tokens(int(tid))
        token_str = token_str.replace("\n", "\\n")
        if int(lab) == IGNORE_INDEX:
            yield f"[{token_str}] -> Label: -100 (MASKED)"
        else:
            yield f"[{token_str}] -> Label: {int(lab)}"


def _build_mock_row() -> dict[str, Any]:
    return {
        "task_id": "he_045_comp2raw",
        "task_family": "HumanEval",
        "view_type": "compressed2raw",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert programming assistant. You may receive compressed "
                    "code contexts containing base62 aliases."
                ),
            },
            {
                "role": "user",
                "content": (
                    "<CODEBOOK>\n@A=val_list\n</CODEBOOK>\n"
                    "<CONTEXT>\ndef standard_deviation(@A):\n</CONTEXT>"
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "    mean = sum(val_list) / len(val_list)\n"
                    "    variance = sum((x - mean) ** 2 for x in val_list) / len(val_list)\n"
                    "    return variance ** 0.5\n"
                ),
            },
        ],
        "metadata": {
            "is_valid_sample": True,
            "delta_tokens": -4,
            "compression_ratio": 0.95,
            "a_hits": 2,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model-name",
        default="Qwen/Qwen1.5-0.5B-Chat",
        help="Tokenizer model name.",
    )
    parser.add_argument(
        "--max-length",
        type=int,
        default=0,
        help="Optional truncation length. 0 means no truncation.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

    logging.info("Loading tokenizer: %s", args.model_name)
    tokenizer = AutoTokenizer.from_pretrained(args.model_name, trust_remote_code=True)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    mock_row = _build_mock_row()
    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".jsonl", encoding="utf-8") as fp:
        fp.write(json.dumps(mock_row, ensure_ascii=False) + "\n")
        tmp_path = Path(fp.name)

    dataset = QwenSFTDataset(
        tmp_path,
        tokenizer,
        max_length=(args.max_length if args.max_length > 0 else None),
    )
    collator = DataCollatorForQwenSFT(tokenizer)
    batch = collator([dataset[0]])

    input_ids = batch["input_ids"][0].tolist()
    labels = batch["labels"][0].tolist()
    print("==== Loss Mask Debug ====")
    for line in _iter_debug_tokens(tokenizer, input_ids, labels):
        print(line)
    print("==== Summary ====")
    trainable = sum(1 for x in labels if x != IGNORE_INDEX)
    masked = sum(1 for x in labels if x == IGNORE_INDEX)
    print(f"total={len(labels)} trainable={trainable} masked={masked}")
    print(f"tmp_jsonl={tmp_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
