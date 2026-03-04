"""
Multi-language evaluation script for membership inference attack.

This script evaluates code samples from multiple programming languages (C, Java, JavaScript)
using four scoring methods: loss, zlib, mink_0.2, and synprune.

Adapted from the original Python-only run.py to support Tree-sitter based parsing.
"""

import argparse
import json
import zlib
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.metrics import auc, roc_curve
from collections import defaultdict
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from syntax_parser import TreeSitterSyntaxParser
except ImportError:
    print("Warning: syntax_parser not available. SynPrune method will be disabled.")
    TreeSitterSyntaxParser = None


def safe_compute_scores(token_log_probs: torch.Tensor, mask: torch.Tensor, ratio: float) -> float:
    """Compute scores from token log probabilities with mask."""
    valid_probs = token_log_probs[mask]
    if len(valid_probs) == 0:
        return 0.0
    valid_probs = valid_probs - valid_probs.max()
    valid_probs = torch.exp(valid_probs)
    valid_probs = valid_probs / valid_probs.sum()
    k = min(int(len(valid_probs) * ratio), len(valid_probs))
    return 0.0 if k == 0 else torch.mean(torch.sort(valid_probs)[0][:k]).item()


def safe_compute_scores_mink_raw(token_log_probs: torch.Tensor, ratio: float) -> float:
    """Compute Minkowski score from raw token log probabilities."""
    k_length = int(len(token_log_probs) * ratio)
    if k_length == 0:
        return 0.0
    # Convert to float32 before numpy to handle BFloat16
    mink_score = np.sort(token_log_probs.detach().cpu().float().numpy())[:k_length]
    return float(np.mean(mink_score))


def load_jsonl_dataset(path: str):
    """Load JSONL dataset file."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f]


def get_metrics(scores, labels):
    """Compute AUROC, FPR@95, TPR@5 metrics."""
    scores, labels = np.asarray(scores), np.asarray(labels)
    mask = ~np.isnan(scores)
    if mask.sum() == 0:
        return 0.0, 0.0, 0.0
    fpr, tpr, _ = roc_curve(labels[mask], scores[mask])
    auroc = auc(fpr, tpr)
    fpr95 = next((fpr[i] for i in range(len(tpr)) if tpr[i] >= 0.95), 1.0)
    tpr05 = next((tpr[i] for i in reversed(range(len(fpr))) if fpr[i] <= 0.05), 0.0)
    return auroc, fpr95, tpr05


def load_model(name: str, int8: bool, half: bool):
    """Load language model and tokenizer."""
    import os

    # 只对大模型（GPT-J 6B）使用数据盘缓存，其他模型用系统盘默认缓存
    cache_dir = None
    if 'gpt-j' in name.lower() or '6b' in name.lower():
        # 尝试多个可能的缓存位置
        cache_options = [
            '/root/autodl-tmp/huggingface_cache',  # AutoDL 临时盘（最大）
            '/root/autodl-fs/huggingface_cache',   # AutoDL 数据盘
            '/tmp/huggingface_cache',               # 系统临时盘
        ]

        for cache_dir in cache_options:
            try:
                os.makedirs(cache_dir, exist_ok=True)
                # 测试是否可写
                test_file = os.path.join(cache_dir, 'test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"   💾 大模型缓存到: {cache_dir}")
                break
            except (OSError, IOError) as e:
                cache_dir = None
                continue
        else:
            print(f"   ⚠️  无法找到可用的缓存位置，使用系统默认")
            cache_dir = None

    int8_kwargs = {"load_in_8bit": True, "torch_dtype": torch.bfloat16} if int8 else {}
    half_kwargs = {"torch_dtype": torch.bfloat16} if half and not int8 else {}

    model_kwargs = {"device_map": "auto", "return_dict": True}
    if cache_dir:
        model_kwargs["cache_dir"] = cache_dir
    model_kwargs.update(int8_kwargs)
    model_kwargs.update(half_kwargs)

    model = AutoModelForCausalLM.from_pretrained(name, **model_kwargs)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(name, cache_dir=cache_dir)
    if hasattr(tokenizer, 'model_max_length'):
        tokenizer.model_max_length = 1024
    if hasattr(tokenizer, 'do_lower_case'):
        tokenizer.do_lower_case = False
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': '[PAD]'})
        model.resize_token_embeddings(len(tokenizer))
    return model, tokenizer


def ranges_overlap(range1: tuple, range2: tuple) -> bool:
    """Check if two byte ranges overlap."""
    start1, end1 = range1
    start2, end2 = range2
    return not (end1 <= start2 or end2 <= start1)


def get_syntax_mask_multi_language(tokenizer, text: str, input_ids: torch.Tensor,
                                    syntax_parser: TreeSitterSyntaxParser) -> torch.Tensor:
    """
    Generate syntax mask using Tree-sitter instead of Python AST.

    Key difference from original:
    - Original: Used Python ast module + manual constraint dictionaries
    - New: Uses Tree-sitter parser + universal classification rules

    Args:
        tokenizer: HuggingFace tokenizer
        text: Source code string
        input_ids: Token IDs tensor
        syntax_parser: TreeSitterSyntaxParser instance

    Returns:
        Boolean mask tensor where True = KEEP (compute score), False = PRUNE (mask out)
    """
    # 1. Get syntax-constrained byte ranges from Tree-sitter
    prune_ranges = syntax_parser.get_syntax_constrained_byte_ranges(text)

    # 2. Get token byte offsets from tokenizer
    encoding = tokenizer.encode_plus(
        text,
        return_offsets_mapping=True,
        add_special_tokens=True,
        max_length=len(input_ids[0]),
        truncation=True,
        padding="max_length"
    )

    offset_mapping = encoding['offset_mapping']
    tokens = tokenizer.convert_ids_to_tokens(input_ids[0])

    # 3. Create mask: True = KEEP, False = PRUNE
    mask = torch.ones(len(tokens) - 1, dtype=torch.bool)

    for i in range(len(tokens) - 1):
        token = tokens[i + 1]  # Skip [BOS] token

        # Handle special tokens
        if token in ['[PAD]', '[EOS]', '[BOS]']:
            mask[i] = False
            continue

        # Get byte offset for this token
        if i < len(offset_mapping):
            token_start, token_end = offset_mapping[i + 1]  # +1 to skip [BOS]

            # Check if token overlaps with any prune range
            should_prune = False
            for range_start, range_end in prune_ranges:
                if ranges_overlap((token_start, token_end), (range_start, range_end)):
                    should_prune = True
                    break

            mask[i] = not should_prune
        else:
            # Fallback: keep the token
            mask[i] = True

    return mask


def prepare_dataset(positive_samples: list, negative_samples: list,
                    sample_size: int = None, balanced: bool = True) -> list:
    """
    Prepare dataset with labels from positive and negative samples.

    Args:
        positive_samples: List of member samples (label=1)
        negative_samples: List of non-member samples (label=0)
        sample_size: Number of samples to use from each class
        balanced: If True, use equal number of positive and negative samples

    Returns:
        List of dictionaries with 'code' and 'label' keys
    """
    dataset = []

    # Process positive samples
    pos_count = min(len(positive_samples), sample_size) if sample_size else len(positive_samples)
    for i, sample in enumerate(positive_samples[:pos_count]):
        # Handle different data formats
        if 'code' in sample:
            code = sample['code']
        elif 'function' in sample:
            code = sample['function']
        else:
            continue

        dataset.append({
            'code': code,
            'label': 1,
            'language': sample.get('language', 'unknown')
        })

    # Process negative samples
    neg_count = min(len(negative_samples), sample_size) if sample_size else len(negative_samples)
    for i, sample in enumerate(negative_samples[:neg_count]):
        # Handle different data formats
        if 'code' in sample:
            code = sample['code']
        elif 'function' in sample:
            code = sample['function']
        else:
            continue

        dataset.append({
            'code': code,
            'label': 0,
            'language': sample.get('language', 'unknown')
        })

    return dataset


def main():
    parser = argparse.ArgumentParser(description='Multi-language membership inference attack evaluation')
    parser.add_argument("--model", default="EleutherAI/pythia-2.8b", help="Model name or path")
    parser.add_argument("--dataset", required=True, help="Language name (c/java/javascript)")
    parser.add_argument("--positive_path", help="Path to positive samples JSONL")
    parser.add_argument("--negative_path", help="Path to negative samples JSONL")
    parser.add_argument("--half", action="store_true", help="Use bfloat16 inference")
    parser.add_argument("--int8", action="store_true", help="Use 8-bit inference")
    parser.add_argument("--max_length", type=int, default=512, help="Maximum sequence length")
    parser.add_argument("--sample_size", type=int, default=None, help="Samples per class")
    parser.add_argument("--methods", default="loss,zlib,mink_0.2,synprune",
                       help="Comma-separated list of methods to evaluate")
    parser.add_argument("--output", default=None, help="Output CSV path")

    args = parser.parse_args()

    # Determine data paths
    language = args.dataset.lower()
    if language == 'js':
        language = 'javascript'

    if not args.positive_path:
        args.positive_path = f"benchmark/data/positive/{language}_positive.jsonl"

    if not args.negative_path:
        args.negative_path = f"benchmark/data/negative/{language}_negative.jsonl"

    print(f"Loading {language} dataset...")
    print(f"  Positive: {args.positive_path}")
    print(f"  Negative: {args.negative_path}")

    # Load datasets
    positive_samples = load_jsonl_dataset(args.positive_path)
    negative_samples = load_jsonl_dataset(args.negative_path)

    print(f"  Loaded {len(positive_samples)} positive, {len(negative_samples)} negative samples")

    # Prepare dataset
    dataset = prepare_dataset(positive_samples, negative_samples, args.sample_size)
    print(f"  Using {len(dataset)} samples total")

    # Initialize syntax parser if needed
    methods = args.methods.split(',')
    use_synprune = 'synprune' in methods

    syntax_parser = None
    if use_synprune:
        if TreeSitterSyntaxParser is None:
            print("Warning: synprune requested but syntax_parser not available")
            methods = [m for m in methods if m != 'synprune']
            use_synprune = False
        else:
            try:
                syntax_parser = TreeSitterSyntaxParser(language)
                print(f"  Tree-sitter parser initialized for {language}")
            except Exception as e:
                print(f"Warning: Failed to initialize syntax parser: {e}")
                methods = [m for m in methods if m != 'synprune']
                use_synprune = False

    # Load model
    print(f"\nLoading model {args.model}...")
    model, tokenizer = load_model(args.model, args.int8, args.half)
    print("  Model loaded")

    # Evaluate samples
    scores_dict = defaultdict(list)

    print(f"\nEvaluating {len(dataset)} samples...")
    for d in tqdm(dataset, desc="Processing"):
        code = d["code"]

        with torch.no_grad():
            input_ids_raw = torch.tensor(
                tokenizer.encode(code, max_length=args.max_length, truncation=True)
            ).unsqueeze(0).to(model.device)

            outputs_raw = model(input_ids_raw, labels=input_ids_raw, output_hidden_states=True)
            loss_raw, logits_raw = outputs_raw.loss, outputs_raw.logits
            ll = -loss_raw.item()

        # loss
        if 'loss' in methods:
            scores_dict["loss"].append(ll)

        # zlib
        if 'zlib' in methods:
            try:
                zlib_score = ll / len(zlib.compress(bytes(code, 'utf-8')))
            except:
                zlib_score = 0.0
            scores_dict["zlib"].append(zlib_score)

        # mink_0.2
        if 'mink_0.2' in methods:
            with torch.no_grad():
                ids_next = input_ids_raw[0][1:].unsqueeze(-1)
                log_probs_raw = F.log_softmax(logits_raw[0, :-1], dim=-1)
                token_log_probs_raw = log_probs_raw.gather(dim=-1, index=ids_next).squeeze(-1)
                mink_0_2 = safe_compute_scores_mink_raw(token_log_probs_raw, ratio=0.2)
                scores_dict["mink_0.2"].append(mink_0_2)

        # synprune
        if use_synprune and 'synprune' in methods:
            encoding = tokenizer.encode_plus(
                code,
                max_length=args.max_length,
                truncation=True,
                return_tensors="pt",
                return_offsets_mapping=True,
                add_special_tokens=True,
                padding='max_length',
                pad_to_multiple_of=8
            )
            inp = encoding["input_ids"].to(model.device)
            attention_mask = encoding["attention_mask"].to(model.device)

            with torch.no_grad():
                outputs_mask = model(inp, labels=inp, output_hidden_states=True, attention_mask=attention_mask)
                logits_mask = outputs_mask.logits

                mask = get_syntax_mask_multi_language(tokenizer, code, inp, syntax_parser)
                log_probs_mask = F.log_softmax(logits_mask[0, :-1], dim=-1)
                masked_log_probs = log_probs_mask.clone()
                masked_log_probs[~mask] = float('-inf')
                masked_log_probs = F.log_softmax(masked_log_probs, dim=-1)
                input_ids_for_mask = inp[0][1:].unsqueeze(-1)
                token_lp = masked_log_probs.gather(dim=-1, index=input_ids_for_mask).squeeze(-1)
                scores_dict["synprune"].append(safe_compute_scores(token_lp, mask, 1.0))

    # Compute metrics
    labels = [d["label"] for d in dataset]
    results = defaultdict(list)

    for method in methods:
        if method not in scores_dict:
            continue
        auroc, fpr95, tpr05 = get_metrics(scores_dict[method], labels)
        results["language"].append(language)
        results["method"].append(method)
        results["auroc"].append(f"{auroc:.1%}")
        results["fpr95"].append(f"{fpr95:.1%}")
        results["tpr05"].append(f"{tpr05:.1%}")

    # Display results
    df = pd.DataFrame(results)
    print("\n" + "="*60)
    print("Results:")
    print(df.to_string(index=False))
    print("="*60)

    # Save results
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, mode='a' if output_path.exists() else 'w', index=False, header=not output_path.exists())
        print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
