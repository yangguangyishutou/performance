import os
import json
import time
import numpy as np
from itertools import combinations, product
from typing import List, Dict, Optional, Any
from ModelPairAnalyzer import ModelPairAnalyzer


class ModelCollectionAnalyzer:
    """
    对一组模型做两两比较（调用已有的 ModelPairAnalyzer），并为每个模型计算峰度。
    输出包含：
      - pairwise_distances: NxN 矩阵（平均 L2），对角为 0
      - pairwise_layerwise: 可选的字典 {(i,j): layerwise_results} （当 request_layerwise=True 时）
      - kurtosis_by_model: 每个模型的 total kurtosis（以及可选的每层字典）
    参数：
      - models: list of model identifier strings (传给 ModelPairAnalyzer 的 model 名称)
      - model_meta: 可选 dict，键为 model name，值为 dict，用来传递每个模型的额外参数
                    (例如 {"my_adapter": {"model_type":"adapter", "base":"xxx"}, ...})
      - out_dir: 可选路径，将结果写成 JSON/npz 到该目录
      - verbose: 是否输出进度日志
    使用示例：
      mlist = ["gpt2", "EleutherAI/gpt-j-6B"]
      meta = {"my_adapt": {"model_type":"adapter", "model_A_base":"xxx"}}
      mca = ModelCollectionAnalyzer(mlist, model_meta=meta)
      res = mca.run_all(request_layerwise=False)
    """

    def __init__(self,
                 models: List[str],
                 model_meta: Optional[Dict[str, Dict[str, Any]]] = None,
                 out_dir: Optional[str] = None,
                 verbose: bool = True):
        self.models = list(models)
        self.n = len(self.models)
        self.model_meta = model_meta or {}
        self.out_dir = out_dir
        self.verbose = verbose

        if self.out_dir:
            os.makedirs(self.out_dir, exist_ok=True)

    def _log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def run_all(self,
                request_layerwise: bool = False,
                kurtosis_sample_threshold: int = int(1e8),
                kurtosis_sample_size: int = int(1e7),
                kurtosis_min_elements: int = 4,
                save_intermediate: bool = True) -> Dict[str, Any]:
        """
        对模型集合执行：
          - 为每个模型计算峰度（调用 ModelPairAnalyzer.compute_kurtosis via temporary instance）
          - 计算两两平均 L2 距离（调用 ModelPairAnalyzer.calculate_models_distance）

        返回字典，包含：
          - 'pairwise_distances': numpy.ndarray shape (N,N) (float)
          - 'kurtosis': dict {model_name: total_kurtosis}
          - 'layerwise_kurtosis': optional dict {model_name: {layer: kurt}} （当 request_layerwise=True）
          - 'pairwise_layerwise': optional dict {(i,j): layerwise_results} （当 request_layerwise=True）
        """
        # 结果容器
        distances = np.full((self.n, self.n), np.nan, dtype=float)
        kurtosis_totals = {}
        layerwise_kurtosis = {} if request_layerwise else None
        pairwise_layerwise = {} if request_layerwise else None

        #  这会加载该模型一次并允许我们复用 compute_kurtosis("A")）
        self._log(f"[run_all] 开始计算 {self.n} 个模型的峰度（kurtosis）...")
        for idx, m in enumerate(self.models):
            t0 = time.time()
            # 准备 meta kwargs
            meta = self.model_meta.get(m, {})
            # 构造一个 ModelPairAnalyzer，用同一个模型名作为 A 和 B 以便只加载一次模型 A
            try:
                mp = ModelPairAnalyzer(m, m,
                                       model_A_type=meta.get("model_type"),
                                       model_A_base=meta.get("base"),
                                       model_A_gguf_file=meta.get("gguf_file"),
                                       model_B_type=meta.get("model_type"),
                                       model_B_base=meta.get("base"),
                                       model_B_gguf_file=meta.get("gguf_file"))
                # 使用较保守的采样/参数，直接返回总峰度
                k_total = mp.compute_kurtosis("A",
                                              ignore_layers=meta.get("ignore_layers"),
                                              sample_threshold=kurtosis_sample_threshold,
                                              sample_size=kurtosis_sample_size,
                                              min_elements=kurtosis_min_elements,
                                              return_layerwise=request_layerwise)
                if request_layerwise:
                    layer_dict, total_k = k_total
                    layerwise_kurtosis[m] = layer_dict
                    kurtosis_totals[m] = total_k
                else:
                    kurtosis_totals[m] = k_total
                self._log(f"  [{idx+1}/{self.n}] {m}: kurtosis={kurtosis_totals[m]:.6f}  (t={time.time()-t0:.1f}s)")
            except Exception as e:
                self._log(f"  [{idx+1}/{self.n}] 计算 {m} 峰度时出错: {e}")
                kurtosis_totals[m] = float('nan')

        # 计算两两距离
        self._log("[run_all] 开始两两距离计算...")
        for i, j in product(range(self.n), range(self.n)):
            name_i = self.models[i]
            name_j = self.models[j]
            if i == j:
                distances[i, j] = 0.0
                continue
            
            # 判断方向，论文中父节点峰度较大
            if kurtosis_totals.get(name_i, float('nan')) < kurtosis_totals.get(name_j, float('nan')):
                distances[i, j] = -1.0  # 标记为无效
                continue

            if not np.isnan(distances[i, j]):
                # 已计算（理论上不会发生因为我们从空矩阵开始，但保留此检查以防未来并行或跳过）
                continue


            meta_i = self.model_meta.get(name_i, {})
            meta_j = self.model_meta.get(name_j, {})

            t0 = time.time()
            try:
                mp = ModelPairAnalyzer(name_i, name_j,
                                       model_A_type=meta_i.get("model_type"),
                                       model_A_base=meta_i.get("base"),
                                       model_A_gguf_file=meta_i.get("gguf_file"),
                                       model_B_type=meta_j.get("model_type"),
                                       model_B_base=meta_j.get("base"),
                                       model_B_gguf_file=meta_j.get("gguf_file"))
                if request_layerwise:
                    layerwise_results, avg_l2 = mp.calculate_models_distance(ignore_layers=meta_i.get("ignore_layers"),
                                                                              return_layerwise=True)
                    pairwise_layerwise[(name_i, name_j)] = layerwise_results
                else:
                    avg_l2 = mp.calculate_models_distance(ignore_layers=meta_i.get("ignore_layers"),
                                                          return_layerwise=False)
                distances[i, j] = avg_l2
                self._log(f"  [pair {i}->{j}] ({name_i} vs {name_j}): avg_l2={avg_l2:.6f}  (t={time.time()-t0:.1f}s)")
            except Exception as e:
                self._log(f"  [pair {i}->{j}] ({name_i} vs {name_j}) 计算出错: {e}")
                distances[i, j] = float('nan')

        results = {
            "models": self.models,
            "pairwise_distances": distances,
            "kurtosis": kurtosis_totals
        }
        if request_layerwise:
            results["layerwise_kurtosis"] = layerwise_kurtosis
            results["pairwise_layerwise"] = pairwise_layerwise

        # 保存到磁盘（如果指定 out_dir）
        if self.out_dir and save_intermediate:
            try:
                json_path = os.path.join(self.out_dir, "mca_results_summary.json")
                # JSON 不能直接保存 numpy，先转换
                serial = {
                    "models": self.models,
                    "kurtosis": {k: (v if isinstance(v, (float, int)) else float("nan")) for k, v in kurtosis_totals.items()}
                }
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(serial, f, indent=2, ensure_ascii=False)
                npz_path = os.path.join(self.out_dir, "pairwise_distances.npz")
                np.savez_compressed(npz_path, distances=distances)
                self._log(f"[run_all] 结果已保存到 {self.out_dir}")
            except Exception as e:
                self._log(f"[run_all] 保存结果出错: {e}")

        return results

if __name__ == '__main__':
    model_forest = [
        "openai-community/gpt2",
        "smgriffin/pop-lyrics-generator-v1",
        "Arjun-G-Ravi/chat-GPT2",
        "alibidaran/medical_transcription_generator",
    ]

    mother = ModelCollectionAnalyzer(model_forest)
    result = mother.run_all()
    print(result)
    # analyzer.export_unmatched_tensors(output_json="./experiments/test/example_unmatched_tensors.json")