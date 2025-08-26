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

class Difference:
    """
    在两个模型之间做逐元素差值比较，并提供累计图、统计图与差值导出功能。

    - 如果使用 adapter 型 peft 模型，传入 model_type='adapter' 并提供 base_model_name
    - 全量拼接所有张量的差值在大模型上可能非常大，类提供 global_sample_max 参数来限制用于绘图/统计的总元素数量
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

    def compute_elementwise_differences(self,
                                       ignore_layers: set = None,
                                       absolute: bool = True,
                                       compare_values: bool = True,
                                       rtol: float = 1e-5,
                                       atol: float = 1e-8,
                                       global_sample_max: int = int(1e12)):
        """
        遍历两个模型的所有张量，计算元素级差值并返回每个张量的统计信息。

        参数:
            ignore_layers: 要忽略的张量名集合
            absolute: 是否记录绝对差值（abs(A-B)）为主要度量
            compare_values: 是否执行数值比较并记录差异
            rtol/atol: 用于近似比较时的容差
            global_sample_max: 为绘图/全局统计而拼接的最大元素数，超过时会进行抽样

        返回:
            stats_list: 每个张量的统计字典列表
            global_sample_array: 用于全局绘图/统计的样本数组（如果没有数值项则为 None）
        """
        if ignore_layers is None:
            ignore_layers = {"transformer.wte.weight", "lm_head.weight"}

        sd1 = self.model_A.state_dict()
        sd2 = self.model_B.state_dict()

        all_keys = sd1.keys() | sd2.keys()
        stats_list = []

        # 用于全局采样
        per_tensor_abs_diffs = []  # 存储小型 np 数组（按 tensor）
        per_tensor_sizes = []

        for name in all_keys:
            if name in ignore_layers:
                continue

            ta = sd1.get(name, None)
            tb = sd2.get(name, None)

            entry = {
                "tensor_name": name,
                "exists_in_model_A": ta is not None,
                "exists_in_model_B": tb is not None,
                "shape_model_A": list(ta.shape) if ta is not None else None,
                "shape_model_B": list(tb.shape) if tb is not None else None,
            }

            if ta is None or tb is None:
                entry.update({
                    "status": "missing_in_one_model"
                })
                stats_list.append(entry)
                continue

            if ta.shape != tb.shape:
                entry.update({
                    "status": "shape_mismatch"
                })
                stats_list.append(entry)
                continue

            if not compare_values:
                entry.update({
                    "status": "skipped_value_compare",
                })
                stats_list.append(entry)
                continue

            try:
                ta_cpu = ta.detach().cpu().double().view(-1).numpy()
                tb_cpu = tb.detach().cpu().double().view(-1).numpy()

                diff = ta_cpu - tb_cpu
                if absolute:
                    adiff = np.abs(diff)
                else:
                    adiff = diff

                # 基本统计量
                n_elem = adiff.size
                max_abs = float(np.nanmax(np.abs(adiff))) if n_elem > 0 else 0.0
                mean = float(np.nanmean(adiff)) if n_elem > 0 else 0.0
                median = float(np.nanmedian(adiff)) if n_elem > 0 else 0.0
                std = float(np.nanstd(adiff)) if n_elem > 0 else 0.0
                l1 = float(np.nansum(np.abs(adiff))) if n_elem > 0 else 0.0
                l2 = float(np.sqrt(np.nansum(adiff ** 2))) if n_elem > 0 else 0.0
                num_nonzero = int(np.count_nonzero(adiff))
                pct_nonzero = num_nonzero / n_elem * 100 if n_elem > 0 else 0.0

                # 偏度与峰度（对原始差值而非绝对值有意义）
                try:
                    sk = float(skew(diff)) if n_elem > 2 else float('nan')
                    kt = float(kurtosis(diff)) if n_elem > 3 else float('nan')
                except Exception:
                    sk = float('nan')
                    kt = float('nan')

                entry.update({
                    "status": "ok",
                    "num_elements": int(n_elem),
                    "max_abs": max_abs,
                    "mean": mean,
                    "median": median,
                    "std": std,
                    "l1_norm": l1,
                    "l2_norm": l2,
                    "num_nonzero": num_nonzero,
                    "pct_nonzero": pct_nonzero,
                    "skew": sk,
                    "kurtosis": kt,
                    "first_20_abs_diffs": (np.abs(diff)[:20].tolist()),
                    "first_20_signed_diffs": (diff[:20].tolist())
                })

                # 保存用于全局统计的绝对差值样本
                if n_elem > 0:
                    per_tensor_abs_diffs.append(adiff)
                    per_tensor_sizes.append(n_elem)

            except Exception as e:
                entry.update({
                    "status": "compare_error",
                    "error": str(e)
                })

            stats_list.append(entry)

        # 构建全局样本数组（控制最大元素数）        
        total_elements = int(np.sum(per_tensor_sizes)) if len(per_tensor_sizes) > 0 else 0
        global_sample_array = None

        if total_elements > 0:
            if total_elements <= global_sample_max:
                # 直接连接
                global_sample_array = np.concatenate(per_tensor_abs_diffs)
            else:
                # 按张量大小比例抽样
                sampled = []
                sizes = np.array(per_tensor_sizes, dtype=np.int64)
                # 将样本数按尺寸分配，确保总数不超过 global_sample_max
                raw_alloc = sizes / sizes.sum() * global_sample_max
                alloc = np.floor(raw_alloc).astype(int)
                # 分配剩余
                remainder = global_sample_max - alloc.sum()
                if remainder > 0:
                    # 把剩余按小数部分最大的优先分配
                    fractions = raw_alloc - np.floor(raw_alloc)
                    idxs = np.argsort(fractions)[::-1]
                    for i in idxs[:remainder]:
                        alloc[i] += 1

                # 现在对每个张量进行随机选择
                rng = np.random.default_rng()
                for arr, a in zip(per_tensor_abs_diffs, alloc):
                    if a <= 0:
                        continue
                    if a >= arr.size:
                        sampled.append(arr)
                    else:
                        idx = rng.choice(arr.size, size=a, replace=False)
                        sampled.append(arr[idx])
                if len(sampled) > 0:
                    global_sample_array = np.concatenate(sampled)
                else:
                    global_sample_array = None

        print(f"完成差值计算：共 {len(stats_list)} 个张量条目，合计元素数 {total_elements}（用于绘图采样上限 {global_sample_max}）")
        return stats_list, global_sample_array

    def export_differences_json(self, stats_list, output_json="./experiments/test/tensor_differences.json"):
        os.makedirs(os.path.dirname(output_json), exist_ok=True)
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(stats_list, f, indent=4, ensure_ascii=False)
        print(f"差值统计已导出到: {output_json}")
        return output_json

    def plot_diff_cumulative(self, global_sample_array=None, save_path=None, pct_thresholds=(50,90,99)):
        """
        绘制 abs(diff) 的累计分布: x 轴为 abs(diff), y 轴为 <= x 的元素占比（按元素计数）。
        如果没有提供 global_sample_array, 会尝试调用 compute_elementwise_differences 获取样本。

        !!! 特别提醒: 若global_sample_max过高(>1e6), 不要绘制累计图, 会导致卡死
        """
        if global_sample_array is None:
            raise ValueError("请先通过 compute_elementwise_differences 获取 global_sample_array，或将其传入此函数。")

        arr = np.asarray(global_sample_array)
        if arr.size == 0:
            print("没有差值样本可绘制。")
            return

        arr = np.sort(arr)
        n = arr.size
        cum_pct = np.arange(1, n + 1) / n * 100
        plt.rcParams['font.family'] = 'SimHei'  # 中文字体
        plt.figure(figsize=(8,5))
        plt.plot(arr, cum_pct, marker='.', linewidth=1)
        plt.xlabel('abs(A - B)')
        plt.ylabel('累计元素占比 (%)')
        plt.title(f'全模型绝对差值累计分布 ({self.model_A_name} vs {self.model_B_name})')
        plt.grid(True)

        # 标注几个常用百分位
        for p in pct_thresholds:
            idx = int(np.ceil(p / 100.0 * n)) - 1
            idx = max(0, min(idx, n-1))
            val = arr[idx]
            plt.axvline(x=val, linestyle='--', lw=1)
            plt.text(val, p, f'{p}% -> {val:.4e}', rotation=90, va='bottom')

        if save_path:
            plt.savefig(save_path)
            print(f"累计图已保存至: {save_path}")
        plt.show()

    def plot_diff_stats(self, global_sample_array=None, save_path=None, bins=80):
        """
        绘制差值直方图并计算统计量（mean, std, skewness, kurtosis, quantiles 等）。
        返回统计字典。
        """
        if global_sample_array is None:
            raise ValueError("请先通过 compute_elementwise_differences 获取 global_sample_array，或将其传入此函数。")

        arr = np.asarray(global_sample_array)
        if arr.size == 0:
            print("没有差值样本可统计。")
            return {}

        mean = float(np.nanmean(arr))
        std = float(np.nanstd(arr))
        sk = float(skew(arr)) if arr.size > 2 else float('nan')
        kt = float(kurtosis(arr)) if arr.size > 3 else float('nan')
        q25, q50, q75 = np.quantile(arr, [0.25, 0.5, 0.75])
        maxv = float(np.nanmax(arr))
        median = q50
        
        plt.rcParams['axes.unicode_minus'] = False  # 使用普通 ASCII '-'，不会乱码
        plt.rcParams['font.family'] = 'SimHei'  # 中文字体
        plt.figure(figsize=(8,5))
        plt.hist(arr, bins=bins, alpha=0.8)
        plt.axvline(mean, linestyle='-', lw=2, label=f'均值: {mean:.4e}')
        plt.axvline(mean + std, linestyle='--', lw=1.2, label=f'均值±1σ: {std:.4e}')
        plt.axvline(mean - std, linestyle='--', lw=1.2)
        plt.axvline(q25, linestyle=':', lw=1.2, label=f'25%: {q25:.4e}')
        plt.axvline(q50, linestyle=':', lw=1.2, label=f'50%: {q50:.4e}')
        plt.axvline(q75, linestyle=':', lw=1.2, label=f'75%: {q75:.4e}')
        plt.title(f'差值直方图 ({self.model_A_name} vs {self.model_B_name})')
        plt.xlabel('abs(A - B)')
        plt.ylabel('元素数量')
        plt.legend()
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path)
            print(f"统计图已保存至: {save_path}")
        plt.show()

        stats = {
            'mean': mean,
            'std': std,
            'skew': sk,
            'kurtosis': kt,
            '25%_quantile': q25,
            '50%_quantile': q50,
            '75%_quantile': q75,
            'max': maxv,
            'num_samples': int(arr.size)
        }
        print('差值统计：')
        for k, v in stats.items():
            print(f"  {k:15s}: {v}")
        return stats

    def detect_differences(self, save_json=None, save_cumulative=None, save_stats=None, **kwargs):
        """
        一键执行：计算差值 -> 导出统计 -> 绘制累计图与统计图。

        返回 (stats_list, global_sample_array, stats_summary)
        """
        stats_list, global_sample_array = self.compute_elementwise_differences(**kwargs)
        if save_json:
            self.export_differences_json(stats_list, save_json)

        stats_summary = None
        if global_sample_array is not None:
            if save_cumulative:
                self.plot_diff_cumulative(global_sample_array, save_path=save_cumulative)
            else:
                self.plot_diff_cumulative(global_sample_array)

            stats_summary = self.plot_diff_stats(global_sample_array, save_path=save_stats)
        else:
            print('没有用于全局绘图的样本。')

        return stats_list, global_sample_array, stats_summary

    def save_stats_to_json(self, stats, json_path="./experiments/cos_diff.json", pair_type=None,
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

if __name__ == '__main__':
    # 示例
    analyzer = Difference('amitom/gpt2-DiabloGPT-SLERP',
                                'amitom/gpt2-DiabloGPT-TA',
                                model_A_type = "",
                                model_A_base = "openai-community/gpt2",
                                model_A_gguf_file = None,
                                model_B_type = "",
                                model_B_base = "openai-community/gpt2",
                                model_B_gguf_file = None)
    
    stats_list, global_sample_array = analyzer.compute_elementwise_differences()
    # analyzer.export_differences_json(stats_list, "./experiments/test/tensor_differences.json")
    # analyzer.plot_diff_cumulative(global_sample_array)
    stats = analyzer.plot_diff_stats(global_sample_array)
    analyzer.save_stats_to_json(stats, update_existing=True)
    pass
