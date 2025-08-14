import json
import random
import os
from huggingface_hub import HfApi, hf_hub_download

class LineageManager:
    """
    提供管理实验配置、模型关系和下载模型权重的工具。
    """
    def __init__(self, config_path: str):
        self.path = config_path
        self.model_map = self._build_map()
    
    def _build_map(self) -> dict:
        """根据配置构建模型名称到完整信息的映射。"""
        with open(self.path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        model_map = {item['model']: item for item in data}
        return model_map

    def get_model(self, model_name: str) -> dict:
        """根据模型名称获取完整信息。"""
        return self.model_map.get(model_name, None)
    
    def find_relationship(self, model_A_name: str, model_B_name: str) -> tuple:
        """
        查找两个模型之间的派生关系链。
        返回一个元组，包含两个列表：(模型名称列表, 派生关系列表)。
        如果找不到关系，则返回 (None, None)。
        如果模型名称相同，则返回 ([model_name], [])。
        """
        # 处理两个模型名称相同的情况
        if model_A_name == model_B_name:
            return [model_A_name], []

        # 假设 self.get_model(name) 可以根据模型名称获取其完整数据结构
        model_A = self.get_model(model_A_name)
        model_B = self.get_model(model_B_name)

        # 确保两个模型的数据都成功获取
        if model_A and model_B:
            # 可能性 1: 检查 model_A 是否为 model_B 的祖先
            # 这意味着 A 和 B 都应该出现在 B 的 lineage 中，且 A 的索引小于 B
            if 'lineage' in model_B and 'full_derive_path' in model_B:
                try:
                    # 在 model_B 的谱系中查找 A 和 B 的位置
                    idx_A = model_B['lineage'].index(model_A_name)
                    idx_B = model_B['lineage'].index(model_B_name)

                    if idx_A < idx_B:
                        # 找到了！A 是 B 的祖先
                        # 截取从 A 到 B 的模型路径
                        path_models = model_B['lineage'][idx_A : idx_B + 1]
                        # 截取对应的派生关系路径
                        # full_derive_path[i] 是 lineage[i] -> lineage[i+1] 的关系
                        path_relations = model_B['full_derive_path'][idx_A : idx_B]
                        return path_models, path_relations
                except ValueError:
                    # 如果 .index() 找不到模型，会抛出 ValueError，说明不在此谱系中，可安全忽略
                    pass

            # 可能性 2: 检查 model_B 是否为 model_A 的祖先
            # 这意味着 B 和 A 都应该出现在 A 的 lineage 中，且 B 的索引小于 A
            if 'lineage' in model_A and 'full_derive_path' in model_A:
                try:
                    # 在 model_A 的谱系中查找 B 和 A 的位置
                    idx_B = model_A['lineage'].index(model_B_name)
                    idx_A = model_A['lineage'].index(model_A_name)

                    if idx_B < idx_A:
                        # 找到了！B 是 A 的祖先
                        # 截取从 B 到 A 的模型路径
                        path_models = model_A['lineage'][idx_B : idx_A + 1]
                        # 截取对应的派生关系路径
                        path_relations = model_A['full_derive_path'][idx_B : idx_A]
                        return path_models, path_relations
                except ValueError:
                    # 模型不在此谱系中，安全忽略
                    pass

        # 如果模型数据不存在，或以上两种可能性都不成立，则它们之间没有直接的派生关系
        return None, None

    def get_random_pair(self, derive_type: str = "random", pretrained_model: str = None) -> tuple:
        """
        获取随机的一对模型。
        :param derive_type: 指定派生类型，默认为 "random"。
        :return: 返回一个元组 (model_A_name, model_B_name, relation_type)。
        """
        assert derive_type in ["random", "finetune", "adapter", "merge", "quantized"], "Invalid derive_type specified."
        
        if pretrained_model:
            candidate_models = [model for model in self.model_map.values() if model['lineage'][0] == pretrained_model]
            # 随机选择一个
            if not candidate_models:
                raise ValueError(f"No models found for pretrained model: {pretrained_model}")
            selected_model = random.choice(candidate_models)
            return pretrained_model, selected_model['model'], selected_model['full_derive_path']

        # 返回同一个 pretrained model 下的任意两个模型
        # 注意 lineage 中的第一个模型即为 pretrained model 此时不要选它

        # 根据派生类型过滤模型
        if derive_type == "random":            
            base_models = {model['lineage'][0] for model in self.model_map.values()}
            if not base_models:
                raise ValueError("No pretrained models found in the configuration.")
            selected_base = random.choice(list(base_models))
            # 给定 pretrained model 选择两个
            candidate_models = [model for model in self.model_map.values() if model['lineage'][0] == selected_base]
            if len(candidate_models) < 2:
                raise ValueError(f"Not enough models found for base model: {selected_base}")
            model_A, model_B = random.sample(candidate_models, 2)

            # 使用 find_relationship 方法获取关系
            _, relations = self.find_relationship(model_A['model'], model_B['model'])
            return model_A['model'], model_B['model'], relations
        else:
            # 根据 pretrained model 并且 lineage 长度大于 2 的模型 并且 base_model 不等于 selected_base
            # 随机选一个 pretrained model
            while True:
                base_models = {model['lineage'][0] for model in self.model_map.values()}
                if not base_models:
                    raise ValueError("No pretrained models found in the configuration.")
                selected_base = random.choice(list(base_models))
                candidate_models = [model for model in self.model_map.values() if 
                    model['lineage'][0] == selected_base 
                    and len(model['lineage']) > 2 
                    and derive_type in model['derive_path']
                    and model['base_model'] != selected_base]
                if candidate_models:
                    break
            
            selected_model = random.choice(candidate_models)
            return selected_model['base_model'], selected_model['model'], selected_model['derive_path']

if __name__ == "__main__":
    # 测试
    manager = LineageManager("./data/model_pairs.json")
    print(manager.get_model("openai-community/gpt2"))
    print(manager.get_model("smgriffin/pop-lyrics-generator-v1"))
    print(manager.find_relationship("DZgas/GIGABATEMAN-7B", "PrunaAI/DreadPoor-Satyr_v2-7B-Model_Stock-bnb-8bit-smashed"))
    print(manager.find_relationship("bert-base-uncased", "bert-base-uncased"))
    print(manager.find_relationship("bert-base-uncased", "gpt2"))
    print(manager.get_random_pair(derive_type="random"))
    print(manager.get_random_pair(derive_type="finetune"))