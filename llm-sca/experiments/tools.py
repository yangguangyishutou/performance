import json
import random
from huggingface_hub import HfApi, hf_hub_download, get_repo_discussions
import os
from transformers import AutoModelForCausalLM
import torch
import numpy as np
import matplotlib.pyplot as plt

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
    def __init__(self, model_A, model_B):
        self.model_A = model_A
        self.model_B = model_B
    
    # 返回模型A和模型B的余弦相似度列表
    def compare_models_cos(self, ignore_layers = None):
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}
        model_A = AutoModelForCausalLM.from_pretrained(self.model_A)
        model_B = AutoModelForCausalLM.from_pretrained(self.model_B)
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

        return cos_ne

    def plot_cosine_similarity(self, save_path = None):
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

    def detect_cos_similarity(self):
        self.compare_models_cos()
        self.plot_cosine_similarity()
        pass

if __name__ == "__main__":
    tools = ExperimentTools("./experiments/adjacent_pairs_without_error.json")
    print(f"当前文件路径： {tools.path}")
    # print(f"加载参数： {tools.config}")
    print(tools.find_relationship("deepseek-ai/DeepSeek-R1", "unsloth/MAI-DS-R1"))
    print(tools.find_relationship("unsloth/MAI-DS-R1", "wanlige/QWQ-stock"))
    print(tools.get_random_pair(False))

    detector = RelationshipDetector("amitom/gpt2-Distilgpt-SLERP", "openai-community/gpt2")
    detector.detect_cos_similarity()