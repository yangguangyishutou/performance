"""
DC-PDD 评估模块

使用混合所有负样本作为通用代码语料，避免数据泄露。
"""

import numpy as np
import torch
import torch.nn.functional as F
from typing import List, Dict, Tuple
from tqdm import tqdm


def compute_global_token_frequency(
    datasets_by_lang: Dict[str, List[Dict]],
    tokenizer,
    field: str = "function",
    max_tok: int = 1024,
    quiet: bool = False
) -> np.ndarray:
    """
    从所有语言的负样本中计算全局 token 频率分布（方案 C）

    Args:
        datasets_by_lang: 语言到负样本列表的映射
            {"c": [neg1, neg2, ...], "java": [...], "javascript": [...]}
        tokenizer: 分词器
        field: 数据集中的文本字段名
        max_tok: 最大 token 数量
        quiet: 是否静默模式

    Returns:
        token 频率分布数组
    """
    # 收集所有负样本
    all_negative_samples = []
    for lang, neg_samples in datasets_by_lang.items():
        all_negative_samples.extend(neg_samples)

    if not quiet:
        print(f"📊 计算全局 token 频率...")
        print(f"   总负样本数: {len(all_negative_samples)}")
        for lang, samples in datasets_by_lang.items():
            print(f"   - {lang.upper()}: {len(samples)} 样本")

    # 首先扫描数据，找出实际的 token_id 范围
    max_token_id = 0
    for example in tqdm(all_negative_samples, disable=quiet, desc="扫描 token 范围"):
        text = example.get(field, example.get("text", example.get("code", "")))
        input_ids = tokenizer.encode(text)[:max_tok]
        if input_ids:
            max_token_id = max(max_token_id, max(input_ids))

    # 使用实际最大 token_id + 1 作为词汇表大小
    vocab_size = max(tokenizer.vocab_size, max_token_id + 1)
    freq_dist = np.zeros(vocab_size, dtype=np.float32)

    if not quiet:
        print(f"   实际 vocab_size: {vocab_size}")
        print(f"   计算频率分布...")

    # 统计频率
    for example in tqdm(all_negative_samples, disable=quiet, desc="统计词频"):
        text = example.get(field, example.get("text", example.get("code", "")))
        input_ids = tokenizer.encode(text)[:max_tok]

        for token_id in input_ids:
            if token_id < len(freq_dist):
                freq_dist[token_id] += 1

    # 加一平滑
    freq_dist = (freq_dist + 1) / (freq_dist.sum() + vocab_size)

    if not quiet:
        print(f"✅ 全局词频计算完成")

    return freq_dist


def compute_dcpdd_score(
    text: str,
    model,
    tokenizer,
    freq_dist: np.ndarray,
    device: str,
    max_length: int = 512,
    a: float = 0.01
) -> float:
    """
    计算单个样本的 DC-PDD 分数

    Args:
        text: 代码文本
        model: 语言模型
        tokenizer: 分词器
        freq_dist: 全局 token 频率分布
        device: 设备
        max_length: 最大序列长度
        a: DC-PDD 截断参数

    Returns:
        DC-PDD 分数（负值，成员样本应该更低）
    """
    # 编码文本
    input_ids = tokenizer.encode(text, max_length=max_length, truncation=True, return_tensors="pt").to(device)

    with torch.no_grad():
        outputs = model(input_ids, labels=input_ids)
        logits = outputs.logits

        # log_softmax 得到对数概率
        log_probs = F.log_softmax(logits[0][:-1], dim=-1)

        # 获取实际 token 的对数概率
        seq_len = log_probs.shape[0]
        actual_input_ids = input_ids[0][1:seq_len+1]
        token_log_probs = log_probs[torch.arange(seq_len, device=device), actual_input_ids]

    # 转换为概率（非对数）
    # 先转为 float32 再转为 numpy，避免 BFloat16 错误
    probs = torch.exp(token_log_probs).cpu().float().numpy()
    input_ids_list = actual_input_ids.cpu().tolist()

    # === DC-PDD 核心算法 ===
    # 只考虑第一次出现的 token（去重）
    indexes = []
    current_ids = []
    for i, token_id in enumerate(input_ids_list):
        if token_id not in current_ids:
            indexes.append(i)
            current_ids.append(token_id)

    # 获取这些 token 的概率和频率
    x_pro = probs[indexes]
    x_fre = freq_dist[np.array(input_ids_list)[indexes]]

    # 计算交叉熵并截断
    ce = x_pro * np.log(1 / x_fre)
    ce[ce > a] = a

    # DC-PDD 分数
    dcpdd_score = -np.mean(ce)

    return dcpdd_score


def evaluate_dcpdd_on_dataset(
    dataset: List[Dict],
    model,
    tokenizer,
    freq_dist: np.ndarray,
    device: str,
    field: str = "function",
    max_length: int = 512,
    a: float = 0.01,
    quiet: bool = False
) -> List[Dict]:
    """
    在数据集上计算 DC-PDD 分数

    Args:
        dataset: 评估数据集（包含成员和非成员）
        model: 语言模型
        tokenizer: 分词器
        freq_dist: 全局 token 频率分布
        device: 设备
        field: 数据集中的文本字段名
        max_length: 最大序列长度
        a: DC-PDD 截断参数
        quiet: 是否静默模式

    Returns:
        包含 dcpdd 分数和 label 的结果列表
    """
    results = []

    if not quiet:
        print(f"🔍 计算 DC-PDD 分数...")

    for example in tqdm(dataset, disable=quiet):
        text = example.get(field, example.get("text", example.get("code", "")))
        label = example.get("label", 0)

        dcpdd_score = compute_dcpdd_score(
            text, model, tokenizer, freq_dist, device, max_length, a
        )

        results.append({
            "dcpdd": dcpdd_score,
            "label": label
        })

    if not quiet:
        print(f"✅ DC-PDD 分数计算完成")

    return results
