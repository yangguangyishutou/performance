"""
DC-PDD 多模型多语言评估脚本（方案 C）

特点：
- 支持多模型、多语言批量评估
- 每个模型只加载一次
- 使用方案 C（混合所有负样本作为通用代码语料）

用法:
    # 单模型单语言
    python src/run_dcpdd.py --languages java --sample_size 20 --models pythia-2.8b --half

    # 多模型多语言
    python src/run_dcpdd.py --languages c,java,javascript --sample_size 100 --models pythia-2.8b,gpt-neo-2.7b --half

    # 只用当前语言负样本
    python src/run_dcpdd.py --languages java --sample_size 100 --only_current_lang --half
"""

import argparse
import json
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer
from sklearn.metrics import auc, roc_curve
from pathlib import Path
import sys
import os

# 添加父目录到 path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dcpdd_evaluator import compute_global_token_frequency, evaluate_dcpdd_on_dataset


def load_jsonl(file_path: str):
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
        tokenizer.pad_token = tokenizer.eos_token

    print(f"✅ 模型加载完成")
    return model, tokenizer, device


def main():
    parser = argparse.ArgumentParser(
        description='DC-PDD 多模型多语言评估（方案 C）',
        epilog="""
示例用法:
  # 单模型单语言
  python src/run_dcpdd.py --languages java --sample_size 20 --models pythia-2.8b --half

  # 多模型多语言
  python src/run_dcpdd.py --languages c,java,javascript --sample_size 100 --models pythia-2.8b,gpt-neo-2.7b --half

  # 4 个模型
  python src/run_dcpdd.py --languages c,java,javascript --sample_size 1000 --models pythia-2.8b,gpt-neo-2.7b,stablelm-3b,gpt-j-6b --half
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
    parser.add_argument("--max_length", type=int, default=512,
                       help="最大序列长度")
    parser.add_argument("--a", type=float, default=0.01,
                       help="DC-PDD 截断参数")
    parser.add_argument("--only_current_lang", action="store_true",
                       help="只用当前语言负样本统计词频（不使用方案 C）")
    parser.add_argument("--output_dir", default="results",
                       help="输出目录")

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

    # 处理语言列表
    languages = [l.strip() for l in args.languages.split(',')]

    print("="*60)
    print(f"🔍 DC-PDD 评估（方案 C）")
    print("="*60)
    print(f"语言: {', '.join([l.upper() for l in languages])}")
    print(f"样本: {args.sample_size} × 2 (成员/非成员)")
    print(f"模型: {', '.join([name for name, _ in model_list])}")
    print(f"精度: {'bfloat16' if args.half else 'float32'}")
    if args.only_current_lang:
        print(f"⚠️  只用当前语言负样本（非方案 C）")
    else:
        print(f"✅ 方案 C：混合所有负样本作为通用代码语料")
    print("="*60)

    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集所有结果
    all_results = []

    # === 对每个模型进行评估 ===
    for model_key, model_name in model_list:
        print(f"\n{'='*60}")
        print(f"🤖 模型: {model_key} ({model_name})")
        print(f"{'='*60}")

        # 加载模型（只加载一次！）
        model, tokenizer, device = load_model(model_name, args.half)

        # === 方案 C：收集所有语言的负样本 ===
        if args.only_current_lang:
            # 只用当前语言负样本
            print(f"\n📊 准备词频统计（只用当前语言负样本）")
            negative_samples_by_lang = {}
            for lang in languages:
                neg_file = f"benchmark/data/negative/{lang}_negative.jsonl"
                neg_data = load_jsonl(neg_file)[:args.sample_size]
                negative_samples_by_lang[lang] = neg_data
                print(f"   {lang.upper()}: {len(neg_data)} 样本")
        else:
            # 方案 C：混合所有语言负样本
            print(f"\n📊 准备词频统计（方案 C：混合所有负样本）")
            negative_samples_by_lang = {}
            for lang in ['c', 'java', 'javascript']:
                try:
                    neg_file = f"benchmark/data/negative/{lang}_negative.jsonl"
                    neg_data = load_jsonl(neg_file)[:args.sample_size]
                    negative_samples_by_lang[lang] = neg_data
                    print(f"   {lang.upper()}: {len(neg_data)} 样本")
                except FileNotFoundError:
                    print(f"   {lang.upper()}: 文件不存在，跳过")

        # 计算全局词频（每个模型只计算一次）
        freq_dist = compute_global_token_frequency(
            negative_samples_by_lang,
            tokenizer,
            field="code",
            max_tok=args.max_length,
            quiet=False
        )

        # === 对每种语言评估 DC-PDD ===
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

            # 评估 DC-PDD
            results = evaluate_dcpdd_on_dataset(
                dataset,
                model,
                tokenizer,
                freq_dist,
                device,
                field="code",
                max_length=args.max_length,
                a=args.a,
                quiet=False
            )

            # 计算指标
            labels = [r["label"] for r in results]
            dcpdd_scores = [r["dcpdd"] for r in results]

            fpr, tpr, _ = roc_curve(labels, dcpdd_scores)
            auroc = auc(fpr, tpr)
            fpr95 = next((fpr[i] for i in range(len(tpr)) if tpr[i] >= 0.95), 1.0)
            tpr05 = next((tpr[i] for i in reversed(range(len(fpr))) if fpr[i] <= 0.05), 0.0)

            # 收集结果
            all_results.append({
                "model": model_key,
                "language": lang,
                "method": "dcpdd",
                "auroc": f"{auroc:.1%}",
                "fpr95": f"{fpr95:.1%}",
                "tpr05": f"{tpr05:.1%}"
            })

            print(f"   AUROC: {auroc:.1%} | FPR@95: {fpr95:.1%} | TPR@5: {tpr05:.1%}")

        # 清理内存
        del model
        del tokenizer
        torch.cuda.empty_cache()

    # 保存结果
    if all_results:
        df = pd.DataFrame(all_results)

        # 保存总结果
        combined_file = output_dir / "dcpdd_all_models.csv"
        df.to_csv(combined_file, index=False)

        # 显示结果汇总
        print(f"\n{'='*60}")
        print(f"📊 DC-PDD 跨模型结果汇总")
        print(f"{'='*60}")
        print(f"\n{'Model':<15} | {'Language':<10} | {'AUROC':<10}")
        print("-" * 50)

        for model_key in [m[0] for m in model_list]:
            model_data = df[df['model'] == model_key]
            if model_data.empty:
                continue

            for lang in languages:
                lang_data = model_data[model_data['language'] == lang]
                if lang_data.empty:
                    continue

                for _, row in lang_data.iterrows():
                    auroc = row['auroc']
                    print(f"{model_key:<15} | {lang.upper():<10} | {auroc}")

        print("-" * 50)
        print(f"\n💾 所有结果已保存: {combined_file}")

        # 保存每个模型的结果
        for model_key in [m[0] for m in model_list]:
            model_data = df[df['model'] == model_key]
            if not model_data.empty:
                model_file = output_dir / f"dcpdd_{model_key}.csv"
                model_data.to_csv(model_file, index=False)
                print(f"   {model_key}: {model_file}")

    print(f"\n✅ 完成！")


if __name__ == "__main__":
    main()
