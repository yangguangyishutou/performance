"""
单独运行 Baseline 评估脚本

支持方法：loss, zlib, mink_0.2, synprune

用法:
    # 单语言
    python src/run_baseline.py --language java --sample_size 20 --model EleutherAI/pythia-2.8b --half

    # 指定方法
    python src/run_baseline.py --language java --sample_size 20 --methods loss,synprune --half
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

from syntax_parser import TreeSitterSyntaxParser


def load_jsonl(file_path: str):
    """加载 JSONL 数据集"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


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


def main():
    parser = argparse.ArgumentParser(
        description='Baseline 评估：loss, zlib, mink_0.2, synprune',
        epilog="""
示例用法:
  # 单语言，所有方法
  python src/run_baseline.py --language java --sample_size 20 --model EleutherAI/pythia-2.8b --half

  # 指定方法
  python src/run_baseline.py --language java --sample_size 20 --methods loss,synprune --half

  # 自定义数据路径
  python src/run_baseline.py --language java --positive_path data/java_pos.jsonl --negative_path data/java_neg.jsonl
        """
    )

    parser.add_argument("--language", required=True,
                       help="语言名称 (c/java/javascript)")
    parser.add_argument("--sample_size", type=int, default=None,
                       help="每类样本数量")
    parser.add_argument("--model", default="EleutherAI/pythia-2.8b",
                       help="模型名称或路径")
    parser.add_argument("--half", action="store_true",
                       help="使用 bfloat16 推理")
    parser.add_argument("--int8", action="store_true",
                       help="使用 8-bit 推理")
    parser.add_argument("--max_length", type=int, default=512,
                       help="最大序列长度")
    parser.add_argument("--methods", default="loss,zlib,mink_0.2,synprune",
                       help="逗号分隔的方法列表")
    parser.add_argument("--positive_path",
                       help="正样本路径（默认：benchmark/data/positive/{lang}_positive.jsonl）")
    parser.add_argument("--negative_path",
                       help="负样本路径（默认：benchmark/data/negative/{lang}_negative.jsonl）")
    parser.add_argument("--output", default="results",
                       help="输出目录")

    args = parser.parse_args()

    # 确定数据路径
    lang = args.language.lower()
    if lang == 'js':
        lang = 'javascript'

    if not args.positive_path:
        args.positive_path = f"benchmark/data/positive/{lang}_positive.jsonl"
    if not args.negative_path:
        args.negative_path = f"benchmark/data/negative/{lang}_negative.jsonl"

    methods = args.methods.split(',')

    print("="*60)
    print(f"🔍 Baseline 评估")
    print("="*60)
    print(f"语言: {args.language.upper()}")
    print(f"样本: {args.sample_size} × 2 (成员/非成员)")
    print(f"模型: {args.model}")
    print(f"方法: {', '.join(methods)}")
    print(f"精度: {'bfloat16' if args.half else 'float32'}")
    print("="*60)

    # 加载数据
    print(f"\n📂 加载数据...")
    positive_samples = load_jsonl(args.positive_path)
    negative_samples = load_jsonl(args.negative_path)

    pos_count = min(len(positive_samples), args.sample_size) if args.sample_size else len(positive_samples)
    neg_count = min(len(negative_samples), args.sample_size) if args.sample_size else len(negative_samples)

    # 准备数据集
    dataset = []
    for sample in positive_samples[:pos_count]:
        code = sample.get('code', sample.get('function', sample.get('text', '')))
        dataset.append({'code': code, 'label': 1})

    for sample in negative_samples[:neg_count]:
        code = sample.get('code', sample.get('function', sample.get('text', '')))
        dataset.append({'code': code, 'label': 0})

    print(f"✅ 数据加载完成: {len(dataset)} 样本")

    # 初始化语法解析器
    syntax_parser = None
    if 'synprune' in methods:
        try:
            syntax_parser = TreeSitterSyntaxParser(args.language)
            print(f"✅ 语法解析器初始化完成")
        except Exception as e:
            print(f"⚠️  语法解析器初始化失败: {e}")
            methods = [m for m in methods if m != 'synprune']

    # 加载模型
    model, tokenizer, device = load_model(args.model, args.half)

    # 评估
    scores_dict = {method: [] for method in methods}
    labels = []

    print(f"\n🔍 评估 {len(dataset)} 个样本...")
    for d in tqdm(dataset, desc="Processing"):
        code = d["code"]
        labels.append(d["label"])

        with torch.no_grad():
            input_ids_raw = torch.tensor(
                tokenizer.encode(code, max_length=args.max_length, truncation=True)
            ).unsqueeze(0).to(device)

            outputs_raw = model(input_ids_raw, labels=input_ids_raw, output_hidden_states=True)
            loss_raw, logits_raw = outputs_raw.loss, outputs_raw.logits
            ll = -loss_raw.item()

        # loss
        if 'loss' in methods:
            scores_dict["loss"].append(ll)

        # zlib
        if 'zlib' in methods:
            try:
                import zlib
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
        if 'synprune' in methods and syntax_parser:
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

    # 计算指标
    results = []
    for method in methods:
        if method not in scores_dict:
            continue
        auroc, fpr95, tpr05 = get_metrics(scores_dict[method], labels)
        results.append({
            "language": args.language,
            "method": method,
            "auroc": f"{auroc:.1%}",
            "fpr95": f"{fpr95:.1%}",
            "tpr05": f"{tpr05:.1%}"
        })

    # 显示结果
    df = pd.DataFrame(results)
    print(f"\n{'='*60}")
    print(f"📊 结果")
    print(f"{'='*60}")
    print(df.to_string(index=False))
    print(f"{'='*60}")

    # 保存结果
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / f"{args.language}_baseline.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 结果已保存: {output_file}")

    print(f"\n✅ 完成！")


if __name__ == "__main__":
    main()
