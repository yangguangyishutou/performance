import json
import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis
from transformers import AutoModelForCausalLM
from peft import PeftModel
import math
import random

class ModelPairAnalyzer:
    """
    负责加载两个模型，并进行比较，计算模型间的距离和两个模型的峰度。
    """
    def __init__(self, model_A_name, model_B_name, **kwargs):
        self.model_A_name = model_A_name
        self.model_B_name = model_B_name
        print(f"正在加载模型 A: {model_A_name}...")
        self.model_A = self._load_model(model_A_name, 
                                        kwargs.get('model_A_type'), 
                                        kwargs.get('model_A_base'), 
                                        kwargs.get('model_A_gguf_file'))
        print(f"正在加载模型 B: {model_B_name}...")
        self.model_B = self._load_model(model_B_name, 
                                        kwargs.get('model_B_type'), 
                                        kwargs.get('model_B_base'), 
                                        kwargs.get('model_B_gguf_file'))

    def _load_model(self, model_name, model_type=None, base_model_name=None, gguf_file = None):
        if model_type == "adapter":
            if not base_model_name:
                raise ValueError("Adapter 模型必须提供 'base_model_name'.")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                # offload_folder="F:/Temp",
                # offload_state_dict=True
            )
            peft_model = PeftModel.from_pretrained(base_model, model_name)
            return peft_model.merge_and_unload()
        else:
            return AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                gguf_file=gguf_file,
                # offload_folder="F:/Temp",
                # offload_state_dict=True
            )


    def calculate_models_distance(self, ignore_layers: set = None, return_layerwise: bool = False,) -> float:
        """
        计算模型 A 与模型 B 在每个共同张量上的 L2 范数差（Frobenius norm）。
        返回格式：列表中每项为 (value, numel)。
        - 当两个张量完全相同时，value 为字符串 "equal"。
        - value 为 float 表示该张量差的 L2 范数（>=0）。
        另外会打印并返回总体的平均 L2：对参与比较的层取算术平均。
        """
        if ignore_layers is None:
            ignore_layers = {"lm_head.weight"}  

        sd1 = self.model_A.state_dict()
        sd2 = self.model_B.state_dict()
        results = []

        common_keys = sd1.keys() & sd2.keys()
        total_l2 = 0.0
        counted_layers = 0

        for name in sorted(common_keys):
            # 跳过被忽略的层（部分匹配）
            if any(ignored in name for ignored in ignore_layers):
                continue

            t1 = sd1[name]
            t2 = sd2[name]

            # 若某一边没有该张量（理论上不可能，因为我们遍历的是交集），仍做健壮处理
            if t1 is None or t2 is None:
                continue

            # 若 shape 不同，则跳过
            if t1.shape != t2.shape:
                # 这里不把 shape 不同的张量计入平均 L2
                results.append(("shape_mismatch:" + name, int(t1.numel() if t1 is not None else 0)))
                continue

            # 移到 cpu 并转 float32 做计算，避免不同 device/精度导致的问题
            try:
                ta = t1.detach().to(torch.float32).cpu()
                tb = t2.detach().to(torch.float32).cpu()
            except Exception:
                # 若 detach/转移失败，尝试直接拷贝
                ta = t1.to(torch.float32).cpu()
                tb = t2.to(torch.float32).cpu()

            # 完全相等的快速判定
            try:
                if torch.equal(ta, tb):
                    results.append(("equal", int(ta.numel())))
                    # 对于 exact equal 的张量，我们也把 L2 视为 0 并计入平均
                    total_l2 += 0.0
                    counted_layers += 1
                    continue
            except Exception:
                # 如果 torch.equal 在某些 dtype 上失败，退回到数值比较
                pass

            # 计算差的 L2 范数（对展平向量计算二范数）
            diff = (ta.view(-1) - tb.view(-1)).double()  # 用 double 提高数值稳定性
            # 可能张量很大，但这里直接计算 torch.norm 通常可行；如内存受限可做分块计算
            l2 = float(torch.norm(diff, p=2).item())
            results.append((l2, int(diff.numel())))

            total_l2 += l2
            counted_layers += 1

        # 计算总体平均 L2
        avg_l2 = float(total_l2 / counted_layers) if counted_layers > 0 else float('nan')

        print(f"模型 {self.model_A_name} vs {self.model_B_name}: 比较完成。")
        print(f"[calculate_models_distance] 共发现 {len(common_keys)} 个共同键，参与平均计算的层数: {counted_layers}，平均 L2: {avg_l2:.6f}")

        if return_layerwise:
            return results, avg_l2
        else:
            return avg_l2
    
    def compute_kurtosis(self,
                         which: str,
                         ignore_layers: set = None,
                         sample_threshold: int = int(1e8),
                         sample_size: int = int(1e7),
                         min_elements: int = 4,
                         return_layerwise: bool = False,
                         random_seed: int = 42) -> float:
        """
        计算某个模型的峰度得分 k(u)
        返回 (layer_kurtosis_dict, total_kurtosis)（当 return_layerwise=True）或 total_kurtosis（当 False）。

        参数：
        - which: "A" 或 "B"，选择 self.model_A 或 self.model_B。也可以直接传入模型对象（见下方说明）。
        - ignore_layers: set of substrings，用于排除包含这些子串的层（例如 {"lm_head.weight"}）。
        - sample_threshold: 若某层元素个数 > sample_threshold，则从该层随机采样 sample_size 个元素计算峰度。
        - sample_size: 采样时的样本量（若层非常大，使用此采样以节省内存）。
        - min_elements: 少于该元素数的张量跳过（因为无法可靠估计高阶矩，默认4）。
        - return_layerwise: 是否返回每层的峰度字典。若 False，仅返回总峰度。
        - random_seed: 采样时的随机种子（为了复现性）。

        返回：
        - (layer_kurtosis_dict, total_kurtosis) 或 total_kurtosis（取决于 return_layerwise）。
        注：使用 scipy.stats.kurtosis(..., fisher=False, bias=False) 计算原始峰度。
        """



        if ignore_layers is None:
            ignore_layers = {"lm_head.weight"}

        # 选择模型对象
        model_obj = None
        if which == "A":
            model_obj = self.model_A
        elif which == "B":
            model_obj = self.model_B
        elif hasattr(which, "state_dict"):  # 支持直接传入模型对象
            model_obj = which
        else:
            raise ValueError("参数 `which` 必须是 'A'/'B' 或 一个模型对象。")

        sd = model_obj.state_dict()
        layer_kurts = {}
        total_kurt = 0.0

        random.seed(random_seed)
        keys = sorted(sd.keys())

        for name in keys:
            # 跳过 ignore_layers（部分匹配）
            if any(ign in name for ign in ignore_layers):
                continue

            tensor = sd[name]
            if tensor is None:
                continue

            # 转到 CPU + float32
            try:
                arr_t = tensor.detach().to(torch.float32).cpu()
            except Exception:
                arr_t = tensor.to(torch.float32).cpu()

            numel = int(arr_t.numel())
            if numel < min_elements:
                # 无法稳健估计四阶矩，跳过或设为 nan
                # 这里我们跳过并不计入总和
                continue

            # 展平并转 numpy（float64 提高数值稳定性）
            # 若张量过大则采样
            if numel > sample_threshold and sample_size < numel:
                # 随机采样索引
                flat = arr_t.view(-1).numpy()
                idx = random.sample(range(numel), min(sample_size, numel))
                vals = flat[idx].astype("float64")
            else:
                vals = arr_t.view(-1).numpy().astype("float64")

            # 去中心化（scipy.kurtosis 已内部处理中心化，但我们确保数值稳定）
            # 使用 fisher=False 以得到原始峰度（不减3），bias=False 以做无偏估计
            try:
                k = float(kurtosis(vals, fisher=False, bias=False))
            except Exception:
                # 若计算出错（例如常数数组导致分母为0），跳过该层
                continue

            # 如果结果是 nan 或无穷，跳过
            if not np.isfinite(k):
                continue

            layer_kurts[name] = k
            total_kurt += k

        # 输出一些摘要
        if len(layer_kurts) == 0:
            print(f"[compute_kurtosis] 未找到匹配的层以计算峰度（which={which}）。")
            if return_layerwise:
                return {}, float('nan')
            else:
                return float('nan')

        mean_kurt = total_kurt / len(layer_kurts)
        print(f"[compute_kurtosis] 模型{which}: layers_count={len(layer_kurts)}, total_kurtosis={total_kurt:.6f}, mean_kurtosis={mean_kurt:.6f}")

        if return_layerwise:
            return layer_kurts, total_kurt
        else:
            return total_kurt


    

if __name__ == '__main__':

    model_forest = [
        {"name" : "openai-community/gpt2", "type": "", "base": None, "gguf_file": None},
        {"name" : "smgriffin/pop-lyrics-generator-v1", "type": "", "base": None, "gguf_file": None},
        {"name" : "Arjun-G-Ravi/chat-GPT2", "type": "", "base": None, "gguf_file": None},
    ]

    analyzer = ModelPairAnalyzer('openai-community/gpt2',
                                'smgriffin/pop-lyrics-generator-v1',
                                model_A_type = "",
                                model_A_base = "openai-community/gpt2",
                                model_A_gguf_file = None,
                                model_B_type = "",
                                model_B_base = "openai-community/gpt2",
                                model_B_gguf_file = None)
    results, dis = analyzer.calculate_models_distance()
    # analyzer.export_unmatched_tensors(output_json="./experiments/test/example_unmatched_tensors.json")