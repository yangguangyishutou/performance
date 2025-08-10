import json
import random
from huggingface_hub import HfApi, hf_hub_download, get_repo_discussions
import os
from transformers import AutoModelForCausalLM
from peft import PeftModel
import torch
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis

class Model:
    def __init__(self, model_name, derive_type = None, father_model = None):
        self.model_name = model_name
        self.derive_type = derive_type
        self.father_model = father_model

    # 自定义比较方法，模型名字一致即认为相等
    def __eq__(self, other):
        if isinstance(other, Model):
            return self.model_name == other.model_name
        return False

    
class ExperimentTools:
    def __init__(self, path):
        self.path = path
        self.config = self.load_config()
        self.model_map = self.build_map()

    def load_config(self):
        with open(self.path, 'r') as file:
            return json.load(file)
    
    def build_map(self):
        model_map = {}
        for item in self.config:
            # 若未进map则添加
            if item["base_model"] not in model_map:
                model_map[item["base_model"]] = Model(item["base_model"])
            if item["model"] not in model_map:
                model_map[item["model"]] = Model(item["model"], item["derive_type"], item["base_model"])
        return model_map

    def get_model(self, model_name):
        return self.model_map.get(model_name, None)
    
    # 查找两个模型之间的关系
    # 传入两模型名字
    # 返回模型列表和关系列表
    def find_relationship(self, model_A, model_B):
        # 向上查找关系，A和B各进行一遍
        model_chain = [model_A]
        relationships_chain = []
        tmp_model = self.get_model(model_A)
        while tmp_model.father_model:
            relationships_chain.insert(0, tmp_model.derive_type)
            model_chain.insert(0, tmp_model.father_model)
            if tmp_model.father_model == model_B:
                return model_chain, relationships_chain
            tmp_model = self.get_model(tmp_model.father_model)

        model_chain = [model_B]
        relationships_chain = []
        tmp_model = self.get_model(model_B)
        while tmp_model.father_model:
            relationships_chain.insert(0, tmp_model.derive_type)
            model_chain.insert(0, tmp_model.father_model)
            if tmp_model.father_model == model_A:
                return model_chain, relationships_chain
            tmp_model = self.get_model(tmp_model.father_model)

        return None, None

    # 获取随机的一对模型
    # 传入参数默认为有关系，关系随机
    def get_random_pair(self, validity = True, derive_type = "random"):
        if validity:
            # 只获取有效的派生关系
            valid_models = [model for model in self.model_map.values() if model.derive_type == derive_type or
                             model.derive_type is not None and derive_type == "random"]
            model = random.choice(valid_models)
            return model.father_model, model.model_name, model.derive_type
        else:
            valid_models = list(self.model_map.values())
            while True:
                model_A, model_B = random.sample(valid_models, 2)
                if self.find_relationship(model_A.model_name, model_B.model_name) == (None, None):
                    return model_A.model_name, model_B.model_name, None

    def get_model_weights(self, model_name, save_path):
        """
        下载Hugging Face模型权重文件到指定路径
    
        参数:
            model_name: Hugging Face模型ID 
            save_path: 本地保存目录路径
    
        备注：
            AI生成 使用api下载 文件路径在 .../(model)/snapshots/(md5)/model.safetensors
        """
        # 确保保存路径存在
        os.makedirs(save_path, exist_ok=True)
    
        # 创建Hugging Face API客户端
        api = HfApi()
    
        # 获取仓库文件列表
        repo_files = api.list_repo_files(model_name)
    
        # 过滤出权重文件 (常见格式)
        weight_files = [
            f for f in repo_files
            if f.endswith(('.bin', '.safetensors', '.h5', '.ckpt', '.pth', '.pt'))
        ]
    
        # 如果没有找到权重文件，尝试使用默认名称
        if not weight_files:
            weight_files = [
                f for f in repo_files
                if f in ['pytorch_model.bin', 'model.safetensors', 'tf_model.h5']
            ]
    
        # 如果仍然找不到，获取仓库中最大的文件作为权重文件
        if not weight_files:
            file_sizes = {}
            for file in repo_files:
                try:
                    file_info = api.get_paths_info(model_name, [file])[0]
                    file_sizes[file] = file_info.size
                except Exception:
                    continue
        
            if file_sizes:
                weight_files = [max(file_sizes, key=file_sizes.get)]
    
        # 下载权重文件
        for weight_file in weight_files:
            file_path = hf_hub_download(
                repo_id=model_name,
                filename=weight_file,
                cache_dir=save_path,
                force_download=True,
                resume_download=False
            )
            print(f"下载完成: {os.path.basename(file_path)}")
    
        print(f"所有权重已保存至: {save_path}")
    

class RelationshipDetector:
    #若是量化模型要填写gguf_file指定量化类型
    def __init__(self, model_A, model_B, model_A_gguf_file = None, model_B_gguf_file = None):
        self.model_A = model_A
        self.model_B = model_B
        self.model_A_gguf_file = model_A_gguf_file
        self.model_B_gguf_file = model_B_gguf_file
    
    # 返回模型A和模型B的余弦相似度列表
    def compare_models_cos(self, ignore_layers = None):
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}
            
        model_A = AutoModelForCausalLM.from_pretrained(self.model_A, gguf_file=self.model_A_gguf_file)
        model_B = AutoModelForCausalLM.from_pretrained(self.model_B, gguf_file=self.model_B_gguf_file)

        sd1 = model_A.state_dict()
        sd2 = model_B.state_dict()
        cos_ne = []


        for name in sd1.keys() & sd2.keys():
            if name in ignore_layers:
                continue
            p1 = sd1[name].view(-1).float()
            p2 = sd2[name].view(-1).float()
            if p1.numel() == 0 or p1.shape != p2.shape:
                continue

            # 计算余弦相似度
            dot = torch.dot(p1, p2)
            norm = torch.norm(p1) * torch.norm(p2)
            cos_sim = (dot / (norm + 1e-12)).item()
            ne = p1.numel()

            cos_ne.append((cos_sim, ne))
        print(f"模型 {self.model_A} 和 {self.model_B} 的余弦相似度计算完成，共计 {len(cos_ne)} 个张量。" +
              f"{self.model_A}原来有 {len(sd1)} 个张量，{self.model_B}原来有 {len(sd2)} 个张量。")
        return cos_ne

    def export_unmatched_tensors(self, output_json="./experiments/test/unmatched_tensors.json", ignore_layers=None):
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}
            
        # 加载模型
        model_A = AutoModelForCausalLM.from_pretrained(self.model_A, gguf_file=self.model_A_gguf_file)
        model_B = AutoModelForCausalLM.from_pretrained(self.model_B, gguf_file=self.model_B_gguf_file)

        sd1 = model_A.state_dict()
        sd2 = model_B.state_dict()

        unmatched_info = []

        # 遍历所有键的并集
        all_keys = sd1.keys() | sd2.keys()
        for name in all_keys:
            if name in ignore_layers:
                continue
            
            tensor_A = sd1.get(name, None)
            tensor_B = sd2.get(name, None)

            # 情况 1：一个模型没有该张量
            if tensor_A is None or tensor_B is None:
                unmatched_info.append({
                    "tensor_name": name,
                    "exists_in_model_A": tensor_A is not None,
                    "exists_in_model_B": tensor_B is not None,
                    "shape_model_A": list(tensor_A.shape) if tensor_A is not None else None,
                    "shape_model_B": list(tensor_B.shape) if tensor_B is not None else None,
                    "first_20_values_model_A": tensor_A.view(-1)[:20].tolist() if tensor_A is not None else None,
                    "first_20_values_model_B": tensor_B.view(-1)[:20].tolist() if tensor_B is not None else None
                })
                continue
            
            # 情况 2：shape 不同
            if tensor_A.shape != tensor_B.shape:
                unmatched_info.append({
                    "tensor_name": name,
                    "exists_in_model_A": True,
                    "exists_in_model_B": True,
                    "shape_model_A": list(tensor_A.shape),
                    "shape_model_B": list(tensor_B.shape),
                    "first_20_values_model_A": tensor_A.view(-1)[:20].tolist(),
                    "first_20_values_model_B": tensor_B.view(-1)[:20].tolist()
                })

        # 写入 JSON 文件
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(unmatched_info, f, indent=4, ensure_ascii=False)

        print(f"导出完成，共记录 {len(unmatched_info)} 个不匹配的张量到 {output_json}")
        return unmatched_info

    def compare_adapters_cos(self,
                         base_model = "openai-community/gpt2",
                         ignore_layers = None,
                         require_both_changed = True,
                         atol = 1e-6):
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}

        print("加载模型", self.model_A, self.model_B, base_model)
        model_base = AutoModelForCausalLM.from_pretrained(base_model, gguf_file=None)
        model_A = AutoModelForCausalLM.from_pretrained(self.model_A, gguf_file=self.model_A_gguf_file)
        model_B = AutoModelForCausalLM.from_pretrained(self.model_B, gguf_file=self.model_B_gguf_file)

        sd_base = model_base.state_dict()
        sdA = model_A.state_dict()
        sdB = model_B.state_dict()

        cos_list = []

        # 只比较同时在 A 和 B 中存在的张量
        common_keys = sdA.keys() & sdB.keys()

        for name in common_keys:
            if name in ignore_layers:
                continue

            tA = sdA[name]
            tB = sdB[name]

            # 形状检查
            if tA.numel() == 0 or tA.shape != tB.shape:
                continue

            # 判断是否与基模型相同（如果基模型中有该键且形状一致）
            changedA = True
            changedB = True
            if name in sd_base and sd_base[name].shape == tA.shape:
                # 使用 allclose 判定“相同”，避免浮点抖动误判
                sameA = torch.allclose(tA, sd_base[name], atol=atol, rtol=1e-5)
                sameB = torch.allclose(tB, sd_base[name], atol=atol, rtol=1e-5)
                changedA = not sameA
                changedB = not sameB
            else:
                # 基模型没有这个键（比如 adapter 新增的键），视为 changed/new
                changedA = True
                changedB = True

            # 如果要求两者都改变才比较，但其中一个没变则跳过
            if require_both_changed and not (changedA and changedB):
                continue

            # 舍弃同时与基模型相同的张量（既没被 A 改动也没被 B 改动）
            if not (changedA or changedB):
                continue

            # 计算 A vs B 的余弦相似度
            p1 = tA.view(-1).float()
            p2 = tB.view(-1).float()
            if p1.shape != p2.shape or p1.numel() == 0:
                continue

            dot = torch.dot(p1, p2)
            norm = torch.norm(p1) * torch.norm(p2)
            cos_sim = (dot / (norm + 1e-12)).item()
            ne = p1.numel()

            cos_list.append((min(cos_sim, 1.0), ne))

        print(f"比较完成：共找到 {len(cos_list)} 个（在 A&B 中且至少有一方与基模型不同的）张量用于比较。")
        # 可选择按相似度或按权重排序后返回
        return cos_list
    # 绘制累积曲线
    def plot_cosine_similarity_cumulative(self,cos_ne = None, save_path = None):
        if cos_ne is None:
            cos_ne = self.compare_models_cos()
        sims = np.array([c for c, w in cos_ne])
        weights = np.array([w for c, w in cos_ne])
        total = weights.sum()

        order = np.argsort(sims)
        sims_sorted = sims[order]
        weights_sorted = weights[order]

        cum_weights = np.cumsum(weights_sorted)
        y_pct = cum_weights / total * 100

        idx_start = np.searchsorted(y_pct, 1.0)
        x_start = sims_sorted[idx_start] if idx_start < len(sims_sorted) else sims_sorted[-1]

        plt.rcParams['font.family'] = 'SimHei'
        plt.figure(figsize=(8, 5))
        plt.plot(sims_sorted, y_pct, marker='.', linewidth=1)
        plt.xlabel("余弦相似度")
        plt.ylabel("余弦相似度 <=x 的张量的占比（根据张量大小加权）")
        plt.title(f"{self.model_A} vs {self.model_B}", fontsize=12)
        plt.xlim(x_start, 1.0)
        plt.ylim(0, 100)
        plt.grid(True)

        plt.axhline(y=1.0, color='r', linestyle='--', label='1% Threshold')
        plt.legend()

        if save_path:
            plt.savefig(save_path)
            print(f"图形已保存至: {save_path}")
        
        plt.show()

    # 绘制统计图并计算统计量
    def plot_cosine_similarity_stats(self, cos_ne = None, save_path = None, type = None, bins = 50):
        # 1. 获取余弦相似度 & 权重
        if cos_ne is None:
            cos_ne = self.compare_models_cos()
        sims = np.array([c for c, w in cos_ne], dtype=np.float64)
        weights = np.array([w for c, w in cos_ne], dtype=np.float64)
        w_sum = weights.sum()

        # 2. 计算加权统计量
        weighted_mean = np.dot(weights, sims) / w_sum

        # 二阶中心矩（加权方差）
        m2 = np.dot(weights, (sims - weighted_mean)**2) / w_sum
        weighted_std = np.sqrt(m2)

        # 三阶中心矩 & 偏度
        m3 = np.dot(weights, (sims - weighted_mean)**3) / w_sum
        weighted_skewness = m3 / (weighted_std**3 + 1e-12)

        # 四阶中心矩 & 峰度（减去 3 得到 Fisher 峰度）
        m4 = np.dot(weights, (sims - weighted_mean)**4) / w_sum
        weighted_kurtosis = m4 / (m2**2 + 1e-12) - 3

        # 分位数
        q25, q50, q75 = np.quantile(sims, [0.25, 0.5, 0.75])

        # 3. 绘图
        plt.rcParams['font.family'] = 'SimHei'  # 中文字体
        plt.figure(figsize=(8, 5))
        plt.hist(sims, bins=bins, weights=weights, alpha=0.7)
        plt.axvline(weighted_mean, linestyle='-', lw=2, label=f'加权平均: {weighted_mean:.4f}')
        plt.axvline(weighted_mean + weighted_std, linestyle='--', lw=1.5,
                    label=f'±1 加权标准差: {weighted_std:.4f}')
        plt.axvline(weighted_mean - weighted_std, linestyle='--', lw=1.5)
        plt.axvline(q25, linestyle=':', lw=1.5, label=f'第25百分位: {q25:.4f}')
        plt.axvline(q50, linestyle=':', lw=1.5, label=f'中位数: {q50:.4f}')
        plt.axvline(q75, linestyle=':', lw=1.5, label=f'第75百分位: {q75:.4f}')

        plt.title(f'{self.model_A} vs {self.model_B} 的余弦相似度分布')
        plt.xlabel('余弦相似度')
        plt.ylabel('参数数量')
        plt.plot([], [], ' ', label=f'偏度: {weighted_skewness:.4f}')
        plt.plot([], [], ' ', label=f'峰度: {weighted_kurtosis:.4f}')
        if type:
            plt.plot([], [], ' ', label=type) 
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
            print(f"图形已保存至: {save_path}")

        # plt.show()

        # 4. 输出统计结果
        stats = {
            'weighted_mean': weighted_mean,
            'weighted_std': weighted_std,
            'skewness': weighted_skewness,
            'kurtosis': weighted_kurtosis,
            '25%_quantile': q25,
            '50%_quantile': q50,
            '75%_quantile': q75
        }
        print("余弦相似度统计：")
        for k, v in stats.items():
            print(f"  {k:15s}: {v:.4f}")
        return stats

    def detect_cos_similarity(self, save_path = None, type = None):
        # self.compare_models_cos()
        # self.plot_cosine_similarity_cumulative()
        self.plot_cosine_similarity_stats(save_path, type)
        pass

if __name__ == "__main__":
    tools = ExperimentTools("./experiments/adjacent_pairs_without_error.json")
    print(f"当前文件路径： {tools.path}")
    # print(f"加载参数： {tools.config}")
    print(tools.find_relationship("deepseek-ai/DeepSeek-R1", "unsloth/MAI-DS-R1"))
    print(tools.find_relationship("unsloth/MAI-DS-R1", "wanlige/QWQ-stock"))
    print(tools.get_random_pair(False))


    ft_models = [
    # finetune
    ["smgriffin/pop-lyrics-generator-v1", "finetune"],
    ["Arjun-G-Ravi/chat-GPT2", "finetune"],
    ["alibidaran/medical_transcription_generator", "finetune"],
    
    #adapter
    ["monsterapi/gpt2_alpaca-lora", "adapter"],
    ["monsterapi/gpt2_124m_norobots", "adapter"],
    ["clemsadand/quote_generator", "adapter"],

    #merge
    ["amitom/gpt2-DiabloGPT-SLERP", "merge"],
    ["amitom/gpt2-DiabloGPT-TA", "merge"],
    ["amitom/gpt2-Distilgpt-SLERP", "merge"],

    #unrelated
    ]

    detector = RelationshipDetector("monsterapi/gpt2_alpaca-lora", "clemsadand/quote_generator")
    detector.plot_cosine_similarity_stats(save_path="./experiments/figures/adapter_1.png", type="adapter")
    detector.export_unmatched_tensors(output_json="./experiments/test/unmatched_tensors_adapter.json")