"""Train a low-cost QLoRA adapter on LangV1 CPT or prompt/completion SFT data."""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys
from pathlib import Path

import torch
from datasets import Dataset
from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
from torch.utils.data import Subset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorForLanguageModeling,
    Trainer,
    TrainingArguments,
    default_data_collator,
)
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from scripts.sft_dataset import DataCollatorForQwenSFT, QwenSFTDataset
except Exception:
    from sft_dataset import DataCollatorForQwenSFT, QwenSFTDataset


def _load_rows(path: Path, limit: int | None, *, train_mode: str) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if train_mode == "sft":
                prompt = str(row.get("prompt", ""))
                completion = str(row.get("completion", ""))
                if not prompt.strip() or not completion.strip():
                    continue
                rows.append({"prompt": prompt, "completion": completion})
            else:
                text = str(row.get("text", "")).strip()
                if not text:
                    continue
                rows.append({"text": text})
            if limit is not None and len(rows) >= limit:
                break
    return rows


def _pick_torch_dtype(arg: str) -> torch.dtype:
    name = (arg or "float16").strip().lower()
    if name == "bfloat16":
        return torch.bfloat16
    if name == "float32":
        return torch.float32
    return torch.float16


def _tokenize_sft_example(
    *,
    tokenizer,
    prompt: str,
    completion: str,
    max_length: int,
) -> dict:
    prompt_ids = tokenizer(prompt, add_special_tokens=False)["input_ids"]
    completion_ids = tokenizer(completion, add_special_tokens=False)["input_ids"]
    eos_token_id = tokenizer.eos_token_id
    if eos_token_id is not None:
        completion_ids = list(completion_ids) + [int(eos_token_id)]
    prompt_ids = list(prompt_ids)
    completion_ids = list(completion_ids)

    if len(prompt_ids) + len(completion_ids) > int(max_length):
        keep_prompt = max(0, int(max_length) - len(completion_ids))
        prompt_ids = prompt_ids[-keep_prompt:] if keep_prompt else []
    if len(prompt_ids) + len(completion_ids) > int(max_length):
        completion_ids = completion_ids[: int(max_length) - len(prompt_ids)]

    input_ids = prompt_ids + completion_ids
    attention_mask = [1] * len(input_ids)
    labels = ([-100] * len(prompt_ids)) + completion_ids

    pad_token_id = tokenizer.pad_token_id
    if pad_token_id is None:
        raise ValueError("tokenizer.pad_token_id is required for SFT padding")
    pad_len = int(max_length) - len(input_ids)
    if pad_len > 0:
        input_ids.extend([int(pad_token_id)] * pad_len)
        attention_mask.extend([0] * pad_len)
        labels.extend([-100] * pad_len)

    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "labels": labels,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-jsonl", type=Path, required=True)
    parser.add_argument("--base-model", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--adapter-init-path", type=Path, default=None)
    parser.add_argument("--train-mode", choices=("cpt", "sft"), default="cpt")
    parser.add_argument("--max-samples", type=int, default=None)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--epochs", type=float, default=1.0)
    parser.add_argument("--learning-rate", type=float, default=2e-4)
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--grad-accum", type=int, default=8)
    parser.add_argument("--logging-steps", type=int, default=10)
    parser.add_argument("--save-strategy", default="epoch")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--lora-r", type=int, default=16)
    parser.add_argument("--lora-alpha", type=int, default=32)
    parser.add_argument("--lora-dropout", type=float, default=0.05)
    parser.add_argument("--torch-dtype", default="float16")
    parser.add_argument("--no-4bit", action="store_true")
    parser.add_argument("--chatml-sft", action="store_true")
    parser.add_argument("--sanity-check-overfit", action="store_true")
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    rows: list[dict] = []
    if not args.chatml_sft:
        rows = _load_rows(args.train_jsonl, args.max_samples, train_mode=args.train_mode)
        if not rows:
            raise SystemExit(f"empty train set: {args.train_jsonl}")
    if args.adapter_init_path is not None and not args.adapter_init_path.exists():
        raise SystemExit(f"missing adapter_init_path: {args.adapter_init_path}")

    tokenizer = AutoTokenizer.from_pretrained(
        args.base_model,
        trust_remote_code=True,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    if args.chatml_sft:
        tokenized = QwenSFTDataset(
            args.train_jsonl,
            tokenizer,
            max_length=int(args.max_length),
        )
        if len(tokenized) == 0:
            raise SystemExit(f"empty chatml-sft train set: {args.train_jsonl}")
    else:
        ds = Dataset.from_list(rows)

        def _tokenize(batch: dict) -> dict:
            if args.train_mode == "sft":
                input_ids = []
                attention_mask = []
                labels = []
                for prompt, completion in zip(batch["prompt"], batch["completion"]):
                    row = _tokenize_sft_example(
                        tokenizer=tokenizer,
                        prompt=str(prompt),
                        completion=str(completion),
                        max_length=int(args.max_length),
                    )
                    input_ids.append(row["input_ids"])
                    attention_mask.append(row["attention_mask"])
                    labels.append(row["labels"])
                return {
                    "input_ids": input_ids,
                    "attention_mask": attention_mask,
                    "labels": labels,
                }
            tok = tokenizer(
                batch["text"],
                truncation=True,
                max_length=int(args.max_length),
                padding="max_length",
            )
            tok["labels"] = tok["input_ids"].copy()
            return tok

        remove_columns = ["prompt", "completion"] if args.train_mode == "sft" else ["text"]
        tokenized = ds.map(_tokenize, batched=True, remove_columns=remove_columns)

    if args.sanity_check_overfit:
        tiny_n = min(8, len(tokenized))
        if tiny_n <= 0:
            raise SystemExit("sanity-check-overfit enabled but no train samples available")
        if args.chatml_sft:
            tokenized = Subset(tokenized, list(range(tiny_n)))
        else:
            tokenized = tokenized.select(range(tiny_n))
        print(f"[sanity-check-overfit] using tiny train set: n={tiny_n}")

    model_kwargs: dict = {
        "trust_remote_code": True,
    }
    use_4bit = torch.cuda.is_available() and not args.no_4bit
    if torch.cuda.is_available():
        model_kwargs["device_map"] = "auto"
        if use_4bit:
            model_kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=_pick_torch_dtype(args.torch_dtype),
            )
        else:
            model_kwargs["torch_dtype"] = _pick_torch_dtype(args.torch_dtype)
    else:
        model_kwargs["torch_dtype"] = torch.float32

    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    if use_4bit:
        model = prepare_model_for_kbit_training(model)
    model.config.use_cache = False

    if args.adapter_init_path is not None:
        model = PeftModel.from_pretrained(
            model,
            str(args.adapter_init_path),
            is_trainable=True,
        )
    else:
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        lora_alpha = int(args.lora_alpha)
        if args.chatml_sft:
            lora_alpha = int(args.lora_r) * 2
        peft_cfg = LoraConfig(
            r=int(args.lora_r),
            lora_alpha=lora_alpha,
            lora_dropout=float(args.lora_dropout),
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=target_modules,
        )
        model = get_peft_model(model, peft_cfg)

    same_output_as_init = (
        args.adapter_init_path is not None
        and args.output_dir.exists()
        and args.output_dir.resolve() == args.adapter_init_path.resolve()
    )
    if args.output_dir.exists() and not same_output_as_init:
        shutil.rmtree(args.output_dir)
    args.output_dir.parent.mkdir(parents=True, exist_ok=True)

    training_args = TrainingArguments(
        output_dir=str(args.output_dir),
        num_train_epochs=float(args.epochs),
        learning_rate=float(args.learning_rate),
        per_device_train_batch_size=int(args.batch_size),
        gradient_accumulation_steps=int(args.grad_accum),
        logging_strategy="steps",
        logging_steps=int(args.logging_steps),
        save_strategy=str(args.save_strategy),
        save_total_limit=1,
        save_only_model=True,
        report_to="none",
        remove_unused_columns=False,
        fp16=torch.cuda.is_available() and _pick_torch_dtype(args.torch_dtype) == torch.float16,
        bf16=torch.cuda.is_available() and _pick_torch_dtype(args.torch_dtype) == torch.bfloat16,
        seed=int(args.seed),
        do_train=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=(
            DataCollatorForQwenSFT(tokenizer=tokenizer)
            if args.chatml_sft
            else default_data_collator
            if args.train_mode == "sft"
            else DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)
        ),
    )
    train_result = trainer.train()
    trainer.save_model()
    tokenizer.save_pretrained(args.output_dir)

    summary = {
        "train_jsonl": str(args.train_jsonl),
        "base_model": args.base_model,
        "adapter_init_path": str(args.adapter_init_path) if args.adapter_init_path else "",
        "output_dir": str(args.output_dir),
        "train_mode": args.train_mode,
        "chatml_sft": bool(args.chatml_sft),
        "sanity_check_overfit": bool(args.sanity_check_overfit),
        "n_train_rows": len(tokenized),
        "max_length": int(args.max_length),
        "epochs": float(args.epochs),
        "learning_rate": float(args.learning_rate),
        "batch_size": int(args.batch_size),
        "grad_accum": int(args.grad_accum),
        "use_4bit": bool(use_4bit),
        "train_runtime": float(train_result.metrics.get("train_runtime", 0.0)),
        "train_loss": float(train_result.metrics.get("train_loss", 0.0)),
    }
    summary_path = args.output_dir / "train_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(summary_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
