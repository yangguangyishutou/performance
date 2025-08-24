import json
import os
import torch
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import skew, kurtosis
from transformers import AutoModelForCausalLM
from peft import PeftModel
import tempfile

def _sanitize_value(v):
    """把 numpy 类型与 NaN 转为可 JSON 序列化的 Python 基本类型。"""
    if isinstance(v, (np.floating, float)):
        if np.isnan(v):
            return None
        return float(v)
    if isinstance(v, (np.integer, int)):
        return int(v)
    # 布尔类型等直接返回
    if v is None:
        return None
    try:
        # 有时用户会传入 numpy arrays 等，尽量降维
        if isinstance(v, (np.ndarray, list, tuple)):
            return [_sanitize_value(x) for x in list(v)]
    except Exception:
        pass
    return v

class CosSimilarty:
    """
    负责加载两个模型，并进行深度比较，包括张量级的余弦相似度分析和统计绘图。
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
                device_map="auto"
            )
            peft_model = PeftModel.from_pretrained(base_model, model_name)
            return peft_model.merge_and_unload()
        else:
            return AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                device_map="auto",
                gguf_file=gguf_file
            )


    def compare_models_cos(self, ignore_layers: set = None) -> list:
        """返回模型A和模型B的(余弦相似度, 张量大小)列表。"""
        if ignore_layers is None:
            ignore_layers = {"lm_head.weight"} # 常见需要忽略的层
        
        sd1 = self.model_A.state_dict()
        sd2 = self.model_B.state_dict()
        cos_ne = []

        common_keys = sd1.keys() & sd2.keys()
        for name in common_keys:
            if any(ignored in name for ignored in ignore_layers):
                continue
            
            t1 = sd1[name].to(torch.float32) # 统一转为 float32 CPU 计算
            t2 = sd2[name].to(torch.float32)

            if t1.shape != t2.shape:
                continue

            if torch.equal(t1, t2):
                cos_ne.append(("equal", t1.numel()))
                continue

            p1 = t1.view(-1)
            p2 = t2.view(-1)

            dot = torch.dot(p1, p2)
            norm = torch.norm(p1) * torch.norm(p2)
            cos_sim = (dot / (norm + 1e-12)).item()
            cos_ne.append((min(cos_sim, 1.0), p1.numel()))
            
        print(f"模型 {self.model_A_name} 和 {self.model_B_name} 的余弦相似度计算完成。")
        print(f"共比较 {len(common_keys)} 个共同张量，其中 {len(cos_ne)} 个进行了计算。")
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
        plt.rcParams['axes.unicode_minus'] = False  # 使用普通 ASCII '-'，不会乱码
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
        plt.show()

        if save_path:
            plt.savefig(save_path)
            print(f"图形已保存至: {save_path}")

        # 4. 输出统计结果（包含 equal 计数）
        stats = {
            'mean': weighted_mean,
            'std': weighted_std,
            'skew': weighted_skewness,
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

    def save_stats_to_json(self, stats, json_path="./experiments/cos_stats.json", pair_type=None,
                        update_existing=False, verbose=True):
        """
        将 stats（来自 plot_cosine_similarity_stats 返回值）追加到 json_path 文件中。
        - json_path: 目标文件路径（若不存在会创建）
        - pair_type: 可选，和 plot_cosine_similarity_stats 中的 type 一致，作为区分字段
        - update_existing: 如果已存在同一模型对且 pair_type 相同，是否替换/更新已有条目（默认 False）
        - 返回: dict {'action': 'added'|'skipped'|'updated'|'error', 'entry': <entry dict>}
        """

        # 构造 entry
        entry = {
            "model_A": getattr(self, "model_A_name", None),
            "model_B": getattr(self, "model_B_name", None),
            "pair_type": pair_type,
            "stats": {}
        }

        # sanitize stats 内容
        for k, v in stats.items():
            entry["stats"][k] = _sanitize_value(v)

        # 如果 model 名称没有提供，拒绝写入
        if not entry["model_A"] or not entry["model_B"]:
            msg = "model_A_name 或 model_B_name 未设置，无法保存。"
            if verbose:
                print(msg)
            return {"action": "error", "reason": msg}

        # 读取已有数据（如果有）
        data = []
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    # 兼容性：如果不是 list，强制转换为 list
                    data = [data]
            except Exception as e:
                msg = f"读取 JSON 文件失败: {e}"
                if verbose:
                    print(msg)
                return {"action": "error", "reason": msg}

        # 查找是否已存在：考虑 (A,B) 与 (B,A) 对称，并且 pair_type 一致（None 也必须一致）
        def same_pair(e1, e2):
            a1, b1, t1 = e1["model_A"], e1["model_B"], e1.get("pair_type", None)
            a2, b2, t2 = e2["model_A"], e2["model_B"], e2.get("pair_type", None)
            same_names = (a1 == a2 and b1 == b2) or (a1 == b2 and b1 == a2)
            return same_names and (t1 == t2)

        existing_index = None
        for idx, rec in enumerate(data):
            # 保证 rec 含必要字段，否则跳过
            if not isinstance(rec, dict):
                continue
            if same_pair(rec, entry):
                existing_index = idx
                break

        if existing_index is not None:
            if update_existing:
                # 替换已有条目（保留旧 timestamp 可选）
                data[existing_index] = entry
                action = "updated"
            else:
                if verbose:
                    print(f"已存在相同模型对（index={existing_index}），已跳过添加。若想覆盖请设 update_existing=True")
                return {"action": "skipped", "entry": data[existing_index]}
        else:
            data.append(entry)
            action = "added"

        # 原子写入：先写到临时文件再替换
        try:
            dirpath = os.path.dirname(os.path.abspath(json_path)) or "."
            with tempfile.NamedTemporaryFile("w", delete=False, dir=dirpath, encoding="utf-8") as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                tmpname = tf.name
            os.replace(tmpname, json_path)  # 原子替换（POSIX & Windows 支持）
            if verbose:
                print(f"保存成功（{action}）: {json_path}")
            return {"action": action, "entry": entry}
        except Exception as e:
            msg = f"写入 JSON 文件失败: {e}"
            if verbose:
                print(msg)
            return {"action": "error", "reason": msg}

    def detect_cos_similarity(self, save_path = None, type = None):
        # self.compare_models_cos()
        # self.plot_cosine_similarity_cumulative()
        self.plot_cosine_similarity_stats(save_path, type)
        pass

if __name__ == '__main__':
    analyzer = CosSimilarty('amitom/gpt2-DiabloGPT-SLERP',
                                'amitom/gpt2-DiabloGPT-TA',
                                model_A_type = "",
                                model_A_base = "openai-community/gpt2",
                                model_A_gguf_file = None,
                                model_B_type = "",
                                model_B_base = "openai-community/gpt2",
                                model_B_gguf_file = None)
    cos_ne = analyzer.compare_models_cos()
    # analyzer.plot_cosine_similarity_cumulative(cos_ne)
    stats = analyzer.plot_cosine_similarity_stats(cos_ne)
    analyzer.save_stats_to_json(stats, update_existing=True)
    # analyzer.export_unmatched_tensors(output_json="./experiments/test/example_unmatched_tensors.json")