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
    # 若是量化模型要填写gguf_file指定量化类型
    # 若是adapter要填写model_type指定类型，base指定基础模型
    def __init__(self,
                  model_A_name,
                  model_B_name, 
                  model_A_gguf_file = None, 
                  model_B_gguf_file = None, 
                  model_A_type = None, 
                  model_B_type = None,
                  model_A_base = None,
                  model_B_base = None):
        self.model_A_name = model_A_name
        self.model_B_name = model_B_name
        self.model_A_gguf_file = model_A_gguf_file
        self.model_B_gguf_file = model_B_gguf_file
        self.model_A_type = model_A_type
        self.model_B_type = model_B_type
        self.model_A_base = model_A_base
        self.model_B_base = model_B_base

        if model_A_type == "adapter":
            base_model_A = AutoModelForCausalLM.from_pretrained(model_A_base, 
                                                                torch_dtype=torch.float16,
                                                                device_map="auto")
            peft_model_A = PeftModel.from_pretrained(base_model_A, model_A_name)
            self.model_A = peft_model_A.merge_and_unload()
            
        else:
            self.model_A = AutoModelForCausalLM.from_pretrained(model_A_name, gguf_file=model_A_gguf_file)
        
        if model_B_type == "adapter":
            base_model_B = AutoModelForCausalLM.from_pretrained(model_B_base, 
                                                                torch_dtype=torch.float16,
                                                                device_map="auto")
            peft_model_B = PeftModel.from_pretrained(base_model_B, model_B_name)
            self.model_B = peft_model_B.merge_and_unload()
        else:
            self.model_B = AutoModelForCausalLM.from_pretrained(model_B_name, gguf_file=model_B_gguf_file)
    
    # 返回模型A和模型B的余弦相似度列表
    def compare_models_cos(self, ignore_layers = None):
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}
        
        model_A = self.model_A
        model_B = self.model_B

        sd1 = model_A.state_dict()
        sd2 = model_B.state_dict()
        cos_ne = []


        for name in sd1.keys() & sd2.keys():
            if name in ignore_layers:
                continue
            p1 = sd1[name].view(-1).double()
            p2 = sd2[name].view(-1).double()
            if p1.numel() == 0 or p1.shape != p2.shape:
                continue
            
            # 比较是否全部相等
            t1 = sd1[name]
            t2 = sd2[name]
            equal = False
            try:
                equal = torch.equal(t1, t2)
            except Exception:
                equal = False

            # 如果 dtype 不同但数值上相等，可以把它们都 cast 到同一 dtype 再比较
            if not equal and t1.dtype != t2.dtype:
                try:
                    equal = torch.equal(t1.to(torch.float32), t2.to(torch.float32))
                except Exception:
                    equal = False

            if equal:
                cos_sim = "equal"
                ne = t1.numel()
                cos_ne.append((cos_sim, ne))
                continue


            # 计算余弦相似度
            dot = torch.dot(p1, p2)
            norm = torch.norm(p1) * torch.norm(p2)
            cos_sim = (dot / (norm + 1e-12)).item()
            ne = p1.numel()

            cos_ne.append((cos_sim, ne))
        print(f"模型 {self.model_A_name} 和 {self.model_B_name} 的余弦相似度计算完成，共计 {len(cos_ne)} 个张量。" +
              f"{self.model_A_name}原来有 {len(sd1)} 个张量，{self.model_B_name}原来有 {len(sd2)} 个张量。")
        return cos_ne

    def export_unmatched_tensors(self, 
                                output_json="./experiments/test/unmatched_tensors.json", 
                                ignore_layers=None,
                                compare_values=True,
                                exact=True,
                                rtol=1e-5,
                                atol=1e-8):   # exact=True表示使用torch.equal进行严格比较，False表示使用torch.allclose进行近似比较
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}
            
        # 加载模型
        model_A = self.model_A
        model_B = self.model_B

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

             # 情况 3：相同 shape，但值不完全相同（根据 exact 或 allclose 判定）
            if compare_values:
                try:
                    # 将张量搬到 cpu 做数值比较，避免 device 不同导致的问题
                    ta = tensor_A.detach().cpu()
                    tb = tensor_B.detach().cpu()

                    if exact:
                        equal = torch.equal(ta, tb)
                        if not equal:
                            # 记录差异
                            diff_flat = (ta.view(-1).double() - tb.view(-1).double()).abs()
                            entry = {
                                "tensor_name": name,
                                "mismatch_type": "value_mismatch_exact",
                                "exists_in_model_A": True,
                                "exists_in_model_B": True,
                                "shape_model_A": list(ta.shape),
                                "shape_model_B": list(tb.shape),
                                "first_20_values_model_A": ta.view(-1)[:20].tolist(),
                                "first_20_values_model_B": tb.view(-1)[:20].tolist(),
                                "first_20_abs_diffs": diff_flat[:20].tolist(),
                                "max_abs_diff": float(diff_flat.max().item()),
                                "mean_abs_diff": float(diff_flat.mean().item()),
                                "num_different_elements": int((diff_flat != 0).sum().item()),
                                "total_elements": int(diff_flat.numel())
                            }
                            unmatched_info.append(entry)
                    else:
                        # 使用近似比较（allclose）
                        allclose = torch.allclose(ta, tb, rtol=rtol, atol=atol)
                        if not allclose:
                            # 计算差异统计量
                            ta_d = ta.view(-1).double()
                            tb_d = tb.view(-1).double()
                            abs_diff = (ta_d - tb_d).abs()
                            # 认为不同的元素： abs_diff > (atol + rtol * |tb|)
                            threshold = atol + rtol * tb_d.abs()
                            # handle possible NaN/inf: 标记为不同
                            is_diff_mask = (~torch.isfinite(abs_diff)) | (abs_diff > threshold)
                            num_different = int(is_diff_mask.sum().item())
                            entry = {
                                "tensor_name": name,
                                "mismatch_type": "value_mismatch_approx",
                                "exists_in_model_A": True,
                                "exists_in_model_B": True,
                                "shape_model_A": list(ta.shape),
                                "shape_model_B": list(tb.shape),
                                "first_20_values_model_A": ta.view(-1)[:20].tolist(),
                                "first_20_values_model_B": tb.view(-1)[:20].tolist(),
                                "first_20_diffs": (ta_d - tb_d)[:20].tolist(),
                                "first_20_abs_diffs": abs_diff[:20].tolist(),
                                "max_abs_diff": float(abs_diff.max().item()) if torch.isfinite(abs_diff).any() else None,
                                "mean_abs_diff": float(abs_diff.mean().item()),
                                "num_different_elements": num_different,
                                "total_elements": int(abs_diff.numel()),
                                "rtol": rtol,
                                "atol": atol
                            }
                            unmatched_info.append(entry)

                except Exception as e:
                    # 如果在比较过程中发生问题，也把信息记录下来，便于排查
                    unmatched_info.append({
                        "tensor_name": name,
                        "mismatch_type": "compare_error",
                        "error": str(e),
                        "exists_in_model_A": True,
                        "exists_in_model_B": True,
                        "shape_model_A": list(tensor_A.shape),
                        "shape_model_B": list(tensor_B.shape)
                    })


        # 写入 JSON 文件
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(unmatched_info, f, indent=4, ensure_ascii=False)

        print(f"导出完成，共记录 {len(unmatched_info)} 个不匹配的张量到 {output_json}")
        return unmatched_info

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
    def plot_cosine_similarity_stats(self, cos_ne=None, save_path=None, type=None, bins=50):
        # 1. 获取余弦相似度 & 权重
        if cos_ne is None:
            cos_ne = self.compare_models_cos()

        total_count = len(cos_ne)
        equal_count = sum(1 for c, w in cos_ne if isinstance(c, str) and c == "equal")

        # 过滤出数值项（排除 "equal"）
        numeric_pairs = [(float(c), float(w)) for c, w in cos_ne
                        if not (isinstance(c, str) and c == "equal")]

        if len(numeric_pairs) > 0:
            sims = np.array([c for c, w in numeric_pairs], dtype=np.float64)
            weights = np.array([w for c, w in numeric_pairs], dtype=np.float64)
            w_sum = weights.sum() + 1e-12  # 防止除零

            # 2. 计算加权统计量
            weighted_mean = np.dot(weights, sims) / w_sum

            # 二阶中心矩（加权方差）
            m2 = np.dot(weights, (sims - weighted_mean) ** 2) / w_sum
            weighted_std = np.sqrt(m2)

            # 三阶中心矩 & 偏度
            m3 = np.dot(weights, (sims - weighted_mean) ** 3) / w_sum
            weighted_skewness = m3 / (weighted_std ** 3 + 1e-12)

            # 四阶中心矩 & 峰度（减去 3 得到 Fisher 峰度）
            m4 = np.dot(weights, (sims - weighted_mean) ** 4) / w_sum
            weighted_kurtosis = m4 / (m2 ** 2 + 1e-12) - 3

            # 分位数（基于数值 sims）
            q25, q50, q75 = np.quantile(sims, [0.25, 0.5, 0.75])
        else:
            # 没有数值项时，返回 NaN 并绘制空图（但仍在 legend 中显示 equal 计数）
            sims = np.array([], dtype=np.float64)
            weights = np.array([], dtype=np.float64)
            weighted_mean = weighted_std = weighted_skewness = weighted_kurtosis = np.nan
            q25 = q50 = q75 = np.nan

        # 3. 绘图
        plt.rcParams['font.family'] = 'SimHei'  # 中文字体
        plt.figure(figsize=(8, 5))

        # 只有存在数值项时才绘制直方图与统计线
        if sims.size > 0:
            plt.hist(sims, bins=bins, weights=weights, alpha=0.7)
            plt.axvline(weighted_mean, linestyle='-', lw=2, label=f'加权平均: {weighted_mean:.4f}')
            plt.axvline(weighted_mean + weighted_std, linestyle='--', lw=1.5,
                        label=f'±1 加权标准差: {weighted_std:.4f}')
            plt.axvline(weighted_mean - weighted_std, linestyle='--', lw=1.5)
            plt.axvline(q25, linestyle=':', lw=1.5, label=f'第25百分位: {q25:.4f}')
            plt.axvline(q50, linestyle=':', lw=1.5, label=f'中位数: {q50:.4f}')
            plt.axvline(q75, linestyle=':', lw=1.5, label=f'第75百分位: {q75:.4f}')

            # 把偏度和峰度也放进 legend（用空 plot 占位）
            plt.plot([], [], ' ', label=f'偏度: {weighted_skewness:.4f}')
            plt.plot([], [], ' ', label=f'峰度: {weighted_kurtosis:.4f}')
        else:
            # 提示没有数值项可绘制
            plt.text(0.5, 0.5, 'No numeric cosine similarities to plot', ha='center', va='center',
                    transform=plt.gca().transAxes)

        # 始终在 legend 中添加 equal 统计信息
        plt.plot([], [], ' ', label=f'Equal count: {equal_count}/{total_count}')
        if type:
            plt.plot([], [], ' ', label=type)

        plt.title(f'{self.model_A_name} vs {self.model_B_name} 的余弦相似度分布')
        plt.xlabel('余弦相似度')
        plt.ylabel('参数数量')
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
            print(f"图形已保存至: {save_path}")

        # 4. 输出统计结果（包含 equal 计数）
        stats = {
            'weighted_mean': weighted_mean,
            'weighted_std': weighted_std,
            'skewness': weighted_skewness,
            'kurtosis': weighted_kurtosis,
            '25%_quantile': q25,
            '50%_quantile': q50,
            '75%_quantile': q75,
            'equal_count': equal_count,
            'total_count': total_count
        }
        print("余弦相似度统计：")
        for k, v in stats.items():
            try:
                print(f"  {k:15s}: {v:.4f}" if isinstance(v, (int, float, np.floating)) and not np.isnan(v) else f"  {k:15s}: {v}")
            except Exception:
                print(f"  {k:15s}: {v}")
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



    # detector = RelationshipDetector("monsterapi/gpt2_alpaca-lora", 
    #                                 "clemsadand/quote_generator", 
    #                                 model_A_type="adapter", 
    #                                 model_B_type="adapter",
    #                                 model_A_base="openai-community/gpt2",
    #                                 model_B_base="openai-community/gpt2")
    detector = RelationshipDetector("monsterapi/gpt2_alpaca-lora", 
                                    "openai-community/gpt2", 
                                    model_A_type="adapter", 
                                    model_A_base="openai-community/gpt2")
    detector.plot_cosine_similarity_stats(save_path="./experiments/figures/adapter_1.png", type="adapter")
    detector.export_unmatched_tensors(output_json="./experiments/test/unmatched_tensors_adapter.json")