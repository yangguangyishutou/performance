"""
优化版 Baseline 评估脚本

特点：
1. 每个模型只加载一次，对所有语言评估
2. DC-PDD 使用混合所有负样本作为通用代码语料（方案 C）
3. baseline 和 DC-PDD 共享同一个模型实例

用法:
    # 单模型
    python evaluation/evaluate_baseline_optimized.py --languages java --sample_size 20 --models pythia-2.8b --half

    # 多模型
    python evaluation/evaluate_baseline_optimized.py --languages c,java,javascript --sample_size 100 --models pythia-2.8b,gpt-neo-2.7b --half --include_dcpdd
"""

import argparse
import json
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.metrics import auc, roc_curve
import sys
import os

# 添加父目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.syntax_parser import TreeSitterSyntaxParser
from src.dcpdd_evaluator import compute_global_token_frequency, evaluate_dcpdd_on_dataset


def load_jsonl(file_path: str) -> List[Dict]:
    """加载 JSONL 数据集"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def load_model(name: str, half: bool):
    """加载语言模型和分词器"""
    print(f"🤖 加载模型: {name}")

    # 处理大模型缓存
    cache_dir = None
    if 'gpt-j' in name.lower() or '6b' in name.lower():
        cache_options = [
            '/root/autodl-tmp/huggingface_cache',
            '/root/autodl-fs/huggingface_cache',
            '/tmp/huggingface_cache',
        ]
        for cache_dir in cache_options:
            try:
                os.makedirs(cache_dir, exist_ok=True)
                test_file = os.path.join(cache_dir, 'test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                print(f"   💾 大模型缓存到: {cache_dir}")
                break
            except (OSError, IOError):
                cache_dir = None
                continue

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"   设备: {device}")

    model_kwargs = {"device_map": "auto", "return_dict": True}
    if cache_dir:
        model_kwargs["cache_dir"] = cache_dir
    if half:
        model_kwargs["torch_dtype"] = torch.bfloat16

    model = AutoModelForCausalLM.from_pretrained(name, **model_kwargs)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(name, cache_dir=cache_dir)
    if tokenizer.pad_token is None:
        tokenizer.add_special_tokens({'pad_token': '[PAD]'})
        model.resize_token_embeddings(len(tokenizer))

    print(f"✅ 模型加载完成")
    return model, tokenizer, device


def safe_compute_scores(token_log_probs: torch.Tensor, mask: torch.Tensor, ratio: float) -> float:
    """从掩码后的 token log_probs 中计算分数"""
    valid_probs = token_log_probs[mask]
    if len(valid_probs) == 0:
        return 0.0
    valid_probs = valid_probs - valid_probs.max()
    valid_probs = torch.exp(valid_probs)
    valid_probs = valid_probs / valid_probs.sum()
    k = min(int(len(valid_probs) * ratio), len(valid_probs))
    return 0.0 if k == 0 else torch.mean(torch.sort(valid_probs)[0][:k]).item()


def safe_compute_scores_mink_raw(token_log_probs: torch.Tensor, ratio: float) -> float:
    """从原始 token log_probs 中计算 Minkowski 分数"""
    k_length = int(len(token_log_probs) * ratio)
    if k_length == 0:
        return 0.0
    mink_score = np.sort(token_log_probs.detach().cpu().float().numpy())[:k_length]
    return float(np.mean(mink_score))


def get_syntax_mask_multi_language(tokenizer, text: str, input_ids: torch.Tensor,
                                    syntax_parser: TreeSitterSyntaxParser) -> torch.Tensor:
    """使用 Tree-sitter 生成语法掩码"""
    prune_ranges = syntax_parser.get_syntax_constrained_byte_ranges(text)

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
    mask = torch.ones(len(tokens) - 1, dtype=torch.bool)

    for i in range(len(tokens) - 1):
        token = tokens[i + 1]
        if token in ['[PAD]', '[EOS]', '[BOS]']:
            mask[i] = False
            continue

        if i < len(offset_mapping):
            token_start, token_end = offset_mapping[i + 1]
            should_prune = False
            for range_start, range_end in prune_ranges:
                if not (token_end <= range_start or token_start >= range_end):
                    should_prune = True
                    break
            mask[i] = not should_prune
        else:
            mask[i] = True

    return mask


def get_metrics(scores, labels):
    """计算 AUROC, FPR@95, TPR@5"""
    scores, labels = np.asarray(scores), np.asarray(labels)
    mask = ~np.isnan(scores)
    if mask.sum() == 0:
        return 0.0, 0.0, 0.0
    fpr, tpr, _ = roc_curve(labels[mask], scores[mask])
    auroc = auc(fpr, tpr)
    fpr95 = next((fpr[i] for i in range(len(tpr)) if tpr[i] >= 0.95), 1.0)
    tpr05 = next((tpr[i] for i in reversed(range(len(fpr))) if fpr[i] <= 0.05), 0.0)
    return auroc, fpr95, tpr05


def evaluate_baseline_on_dataset(
    dataset: List[Dict],
    model,
    tokenizer,
    device: str,
    use_synprune: bool,
    syntax_parser: TreeSitterSyntaxParser,
    max_length: int = 512,
    quiet: bool = False
) -> Dict[str, List]:
    """在数据集上评估 baseline 方法（loss, zlib, mink_0.2, synprune）"""
    scores_dict = {
        "loss": [],
        "zlib": [],
        "mink_0.2": [],
        "synprune": []
    }

    if not use_synprune:
        del scores_dict["synprune"]

    if not quiet:
        print(f"🔍 评估 baseline 方法...")

    for d in tqdm(dataset, disable=quiet, desc="Baseline"):
        code = d["code"]

        with torch.no_grad():
            input_ids_raw = torch.tensor(
                tokenizer.encode(code, max_length=max_length, truncation=True)
            ).unsqueeze(0).to(device)

            outputs_raw = model(input_ids_raw, labels=input_ids_raw, output_hidden_states=True)
            loss_raw, logits_raw = outputs_raw.loss, outputs_raw.logits
            ll = -loss_raw.item()

        # loss
        scores_dict["loss"].append(ll)

        # zlib
        try:
            import zlib
            zlib_score = ll / len(zlib.compress(bytes(code, 'utf-8')))
        except:
            zlib_score = 0.0
        scores_dict["zlib"].append(zlib_score)

        # mink_0.2
        with torch.no_grad():
            ids_next = input_ids_raw[0][1:].unsqueeze(-1)
            log_probs_raw = F.log_softmax(logits_raw[0, :-1], dim=-1)
            token_log_probs_raw = log_probs_raw.gather(dim=-1, index=ids_next).squeeze(-1)
            mink_0_2 = safe_compute_scores_mink_raw(token_log_probs_raw, ratio=0.2)
            scores_dict["mink_0.2"].append(mink_0_2)

        # synprune
        if use_synprune:
            encoding = tokenizer.encode_plus(
                code,
                max_length=max_length,
                truncation=True,
                return_tensors="pt",
                return_offsets_mapping=True,
                add_special_tokens=True,
                padding='max_length',
                pad_to_multiple_of=8
            )
            inp = encoding["input_ids"].to(device)
            attention_mask = encoding["attention_mask"].to(device)

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

    if not quiet:
        print(f"✅ Baseline 评估完成")

    return scores_dict


def main():
    parser = argparse.ArgumentParser(
        description='优化版多语言 baseline 评估（模型只加载一次）',
        epilog="""
示例用法:
  # 单模型 + baseline
  python evaluation/evaluate_baseline_optimized.py --languages java --sample_size 20 --models pythia-2.8b --half

  # 多模型 + baseline + DC-PDD
  python evaluation/evaluate_baseline_optimized.py --languages c,java,javascript --sample_size 100 --models pythia-2.8b,gpt-neo-2.7b --half --include_dcpdd
        """
    )

    parser.add_argument("--languages", default="c,java,javascript",
                       help="逗号分隔的语言列表")
    parser.add_argument("--sample_size", type=int, default=20,
                       help="每类样本数量")
    parser.add_argument("--models",
                       help="逗号分隔的模型列表")
    parser.add_argument("--model", default="EleutherAI/pythia-2.8b",
                       help="单个模型名称（如果未指定 --models）")
    parser.add_argument("--half", action="store_true",
                       help="使用 bfloat16 推理")
    parser.add_argument("--output_dir", default="results",
                       help="输出目录")
    parser.add_argument("--include_dcpdd", action="store_true",
                       help="包含 DC-PDD 方法")
    parser.add_argument("--max_length", type=int, default=512,
                       help="最大序列长度")

    args = parser.parse_args()

    # 处理模型列表
    if args.models:
        models = {
            "pythia-2.8b": "EleutherAI/pythia-2.8b",
            "gpt-neo-2.7b": "EleutherAI/gpt-neo-2.7B",
            "stablelm-3b": "stabilityai/stablelm-base-alpha-3b",
            "gpt-j-6b": "EleutherAI/gpt-j-6B"
        }
        model_keys = [m.strip() for m in args.models.split(',')]
        model_list = [(key, models[key]) for key in model_keys if key in models]
    else:
        model_list = [("custom", args.model)]

    languages = [l.strip() for l in args.languages.split(',')]
    num_methods = 5 if args.include_dcpdd else 4

    print("="*60)
    print(f"🚀 优化版多语言成员推断攻击 | {num_methods} 种方法 × {len(model_list)} 个模型")
    print("="*60)
    print(f"语言: {', '.join([l.upper() for l in languages])}")
    print(f"样本: {args.sample_size} × 2 (成员/非成员)")
    print(f"模型: {', '.join([name for name, _ in model_list])}")
    print(f"精度: {'bfloat16' if args.half else 'float32'}")
    print("="*60)

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 所有结果
    all_results = []

    # 对每个模型进行评估
    for model_key, model_name in model_list:
        print(f"\n{'='*60}")
        print(f"🤖 模型: {model_key} ({model_name})")
        print(f"{'='*60}")

        # 加载模型（只加载一次！）
        model, tokenizer, device = load_model(model_name, args.half)

        # 初始化语法解析器
        use_synprune = True
        try:
            syntax_parsers = {}
            for lang in languages:
                syntax_parsers[lang] = TreeSitterSyntaxParser(lang)
        except Exception as e:
            print(f"⚠️  语法解析器初始化失败: {e}")
            use_synprune = False
            syntax_parsers = {}

        # === 方案 C：收集所有负样本用于计算全局词频 ===
        if args.include_dcpdd:
            print(f"\n📊 准备 DC-PDD 全局词频统计（方案 C）")
            negative_samples_by_lang = {}
            for lang in languages:
                neg_file = f"benchmark/data/negative/{lang}_negative.jsonl"
                neg_data = load_jsonl(neg_file)[:args.sample_size]
                negative_samples_by_lang[lang] = neg_data
                print(f"   {lang.upper()}: {len(neg_data)} 负样本")

            # 计算全局词频（混合所有负样本）
            freq_dist = compute_global_token_frequency(
                negative_samples_by_lang,
                tokenizer,
                field="function",
                max_tok=args.max_length,
                quiet=False
            )

        # === 对每种语言评估 baseline + DC-PDD ===
        for lang in languages:
            print(f"\n{'='*60}")
            print(f"🔍 {lang.upper()} | {args.sample_size} samples")
            print(f"{'='*60}")

            # 加载数据
            pos_file = f"benchmark/data/positive/{lang}_positive.jsonl"
            neg_file = f"benchmark/data/negative/{lang}_negative.jsonl"
            pos_data = load_jsonl(pos_file)[:args.sample_size]
            neg_data = load_jsonl(neg_file)[:args.sample_size]

            # 准备数据集
            dataset = []
            for d in pos_data:
                code = d.get('code', d.get('function', d.get('text', '')))
                dataset.append({'code': code, 'label': 1})
            for d in neg_data:
                code = d.get('code', d.get('function', d.get('text', '')))
                dataset.append({'code': code, 'label': 0})

            # 评估 baseline
            baseline_scores = evaluate_baseline_on_dataset(
                dataset,
                model,
                tokenizer,
                device,
                use_synprune,
                syntax_parsers.get(lang) if use_synprune else None,
                max_length=args.max_length,
                quiet=False
            )

            # 计算 baseline 指标
            labels = [d["label"] for d in dataset]
            for method, scores in baseline_scores.items():
                auroc, fpr95, tpr05 = get_metrics(scores, labels)
                all_results.append({
                    "model": model_key,
                    "language": lang,
                    "method": method,
                    "auroc": f"{auroc:.1%}",
                    "fpr95": f"{fpr95:.1%}",
                    "tpr05": f"{tpr05:.1%}"
                })

            # 评估 DC-PDD（如果启用）
            if args.include_dcpdd:
                dcpdd_results = evaluate_dcpdd_on_dataset(
                    dataset,
                    model,
                    tokenizer,
                    freq_dist,
                    device,
                    field="function",
                    max_length=args.max_length,
                    quiet=False
                )

                # 计算 DC-PDD 指标
                dcpdd_scores = [r["dcpdd"] for r in dcpdd_results]
                auroc, fpr95, tpr05 = get_metrics(dcpdd_scores, labels)
                all_results.append({
                    "model": model_key,
                    "language": lang,
                    "method": "dcpdd",
                    "auroc": f"{auroc:.1%}",
                    "fpr95": f"{fpr95:.1%}",
                    "tpr05": f"{tpr05:.1%}"
                })

        # 保存该模型的结果
        model_output_dir = output_dir / model_key
        model_output_dir.mkdir(parents=True, exist_ok=True)

        df_model = pd.DataFrame([r for r in all_results if r["model"] == model_key])
        df_model.to_csv(model_output_dir / f"{model_key}_results.csv", index=False)
        print(f"\n💾 {model_key} 结果已保存: {model_output_dir}")

        # 清理内存
        del model
        del tokenizer
        torch.cuda.empty_cache()

    # 保存所有模型的结果
    if all_results:
        df_all = pd.DataFrame(all_results)
        combined_file = output_dir / "combined_all_models.csv"
        df_all.to_csv(combined_file, index=False)

        # 显示结果汇总
        print(f"\n{'='*60}")
        print(f"📊 跨模型结果汇总")
        print(f"{'='*60}")
        print(f"\n{'Model':<15} | {'Language':<10} | {'Method':<15} | {'AUROC'}")
        print("-" * 70)

        for model_key in [m[0] for m in model_list]:
            model_data = df_all[df_all['model'] == model_key]
            if model_data.empty:
                continue

            for lang in languages:
                lang_data = model_data[model_data['language'] == lang]
                if lang_data.empty:
                    continue

                for _, row in lang_data.iterrows():
                    method = row['method']
                    auroc = row['auroc']
                    marker = "⭐" if method == "synprune" else "  "
                    print(f"{marker} {model_key:<13} | {lang.upper():<10} | {method:<15} | {auroc}")

        print("-" * 70)
        print(f"\n💾 所有结果已保存: {combined_file}")

    print(f"\n✅ 完成！")


if __name__ == "__main__":
    main()
