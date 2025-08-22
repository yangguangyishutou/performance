import json
import random
from typing import List, Dict, Tuple, Optional

class LineageManager:
    """
    提供管理实验配置、模型关系。
    """
    def __init__(self, config_path: str):
        self.path = config_path
        try:
            with open(self.path, 'r', encoding='utf-8') as file:
                self.models = json.load(file)
        except FileNotFoundError:
            raise FileNotFoundError(f"配置文件未找到: {self.path}")
        except json.JSONDecodeError:
            raise ValueError(f"无法解析配置文件中的JSON: {self.path}")
        self._base_to_descendants = self._group_by_base_model(self.models)
        # for item in self._base_to_descendants.keys():
        #     print(f"基础模型: {item}，后代数量: {len(self._base_to_descendants[item])}")

    def _group_by_base_model(self, data: list) -> dict:
        """将模型按其最顶层的预训练模型进行分组。"""
        grouped = {}
        for model_data in data:
            # 确保 lineage 存在且不为空
            lineage = model_data.get('lineage')
            if lineage and isinstance(lineage, list) and lineage:
                base_model_name = lineage[0]
                if base_model_name not in grouped:
                    grouped[base_model_name] = []
                grouped[base_model_name].append(model_data)
        return grouped

    def get_models(self, model_name: str) -> list:
        """
        获取指定模型的详细信息。
        :param model_name: 模型名称。
        :return: 返回模型的详细信息列表，如果模型不存在则返回空列表。
        """
        return [model for model in self.models if model['model'] == model_name]

    def _find_direct_path(self, start_model_name: str, end_model_name: str) -> tuple:
        """
        辅助函数：检查 start_model 是否是 end_model 的祖先。
        如果是，则返回路径；否则返回空元组。
        """
        end_models = self.get_models(end_model_name)
        # 挑出 lineage 最长的那个
        end_models = sorted(end_models, key=lambda x: len(x['lineage']), reverse=True)
        if not end_models:
            return [], []
        end_model = end_models[0]
        # 确保模型存在且谱系信息完整
        if not end_model or 'lineage' not in end_model or 'full_derive_path' not in end_model:
            return [], []

        try:
            lineage = end_model['lineage']
            idx_start = lineage.index(start_model_name)
            idx_end = lineage.index(end_model_name)

            if idx_start < idx_end:
                path_models = lineage[idx_start : idx_end + 1]
                path_relations = end_model['full_derive_path'][idx_start : idx_end]
                return path_models, path_relations
        except ValueError:
            pass
        
        return [], []

    def find_relationship(self, model_A_name: str, model_B_name: str) -> tuple:
        """
        查找两个模型之间的派生关系链。
        返回 (模型名称列表, 派生关系列表)。
        如果找不到直接的祖先关系，则返回 ([], [])。
        """
        if model_A_name == model_B_name:
            return [model_A_name], []

        # 可能性 1: A -> B
        path_models, path_relations = self._find_direct_path(model_A_name, model_B_name)
        if path_models:
            return path_models, path_relations

        # 可能性 2: B -> A
        path_models, path_relations = self._find_direct_path(model_B_name, model_A_name)
        if path_models:
            return path_models, path_relations

        return [], []

    def get_random_pair(self, derive_type: str = "random", pretrained_model: str = None) -> tuple:
        """
        根据指定标准获取随机的一对模型。
        :return: 返回一个元组 (model_A_name, model_B_name, relations_list)。
        :raises: ValueError 如果找不到符合条件的模型对。
        """
        if pretrained_model:
            return self._get_pair_for_base(pretrained_model, derive_type)
        
        if derive_type == "random":
            return self._get_any_related_pair()
        else:
            return self._get_pair_by_type(derive_type)

    def _get_pair_for_base(self, pretrained_model: str, derive_type: type=None) -> tuple:
        """从指定的基础模型中，选择一个后代模型配对。"""
        candidate_models = self._base_to_descendants.get(pretrained_model, [])
        if not derive_type:
            candidate_models = [
                model for model in candidate_models 
                if derive_type in model.get('derive_path', [])
            ]
        
        if not candidate_models:
            raise ValueError(f"基础模型 '{pretrained_model}' 没有任何派生模型。")
        
        selected_model = random.choice(candidate_models)
        
        # 关系是完整的派生路径
        _, relations = self.find_relationship(pretrained_model, selected_model['model'])
        return pretrained_model, selected_model['model'], relations

    def _get_any_related_pair(self) -> Tuple[str, str, List[str]]:
        """
        在所有模型中，随机选择共享同一个基础模型的两个不同模型。
        如果一次随机选择的基础模型不满足条件，则会不断重试，直到成功。
        """
        # 获取所有基础模型的列表，用于随机选择
        base_models = list(self._base_to_descendants.keys())
        if not base_models:
            raise ValueError("数据中没有任何基础模型。")

        while True:
            # 1. 随机选择一个基础模型
            selected_base = random.choice(base_models)
            descendants = self._base_to_descendants[selected_base]
            
            # 2. 检查这个基础模型是否至少有两个后代（可以构成一对）
            if len(descendants) >= 2:
                # 3. 如果满足条件，从中随机抽取两个并返回
                model_A_data, model_B_data = random.sample(descendants, 2)
                model_A_name, model_B_name = model_A_data['model'], model_B_data['model']
                
                _, relations = self.find_relationship(model_A_name, model_B_name)
                return model_A_name, model_B_name, relations
            # 4. 如果不满足，循环将继续，自动尝试下一个随机基础模型

    def _get_pair_by_type(self, derive_type: str) -> Tuple[str, str, List[str]]:
        """
        获取一个具有特定直接派生关系的模型对。
        会不断随机选择基础模型，直到找到一个后代满足指定的派生类型。
        """
        valid_types = ["finetune", "adapter", "merge", "quantized"]
        if derive_type not in valid_types:
            raise ValueError(f"无效的派生类型: '{derive_type}'. 支持的类型: {valid_types}")

        base_models = list(self._base_to_descendants.keys())
        if not base_models:
            raise ValueError("数据中没有任何基础模型。")
            
        while True:
            # 1. 随机选择一个基础模型
            selected_base = random.choice(base_models)
            descendants = self._base_to_descendants[selected_base]
            
            # 2. 在这个基础模型的后代中，查找符合派生类型的候选模型
            candidate_models = []
            for model_data in descendants:
                if derive_type in model_data.get('derive_path'):
                    candidate_models.append(model_data)

            # 3. 如果找到了一个或多个候选模型
            if candidate_models:
                # 4. 随机选择一个，构建返回结果并跳出循环
                selected_model = random.choice(candidate_models)
                return (
                    selected_model['base_model'], 
                    selected_model['model'], 
                    [selected_model['derive_path']]
                )
            # 5. 如果没找到，循环继续，尝试下一个随机基础模型

if __name__ == "__main__":
    # 测试
    manager = LineageManager("./data/model_pairs_without_error.json")
    # 只存在于 base model 输出 []
    print(manager.get_models("openai-community/gpt2"))
    # 返回列表
    print(manager.get_models("smgriffin/pop-lyrics-generator-v1"))
    # 返回二元组 (['DZgas/GIGABATEMAN-7B', 'DreadPoor/Satyr_v2-7B-Model_Stock', 'PrunaAI/DreadPoor-Satyr_v2-7B-Model_Stock-bnb-8bit-smashed'], ['merge', 'quantized'])
    print(manager.find_relationship("DZgas/GIGABATEMAN-7B", "PrunaAI/DreadPoor-Satyr_v2-7B-Model_Stock-bnb-8bit-smashed"))
    # 返回自己 (['bert-base-uncased'], [])
    print(manager.find_relationship("bert-base-uncased", "bert-base-uncased"))
    # 返回 ([], [])
    print(manager.find_relationship("bert-base-uncased", "gpt2"))
    print(manager.get_random_pair(derive_type="random"))
    print(manager.get_random_pair(derive_type="finetune"))
    print(manager.get_random_pair(pretrained_model="tiiuae/falcon-7b"))