
import os
from similarity_analyzer import SimilarityAnalyzer
from lineage_manager import LineageManager

def ensure_dir(directory):
    """确保目录存在。"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def run_single_comparison(model_a_name, model_b_name, output_dir, relation_type, model_a_params=None, model_b_params=None):
    """
    运行一次完整的模型对比分析。
    
    :param model_a_name: 模型A的名称
    :param model_b_name: 模型B的名称
    :param output_dir: 输出目录
    :param relation_type: 关系类型，用于文件名和图表标题
    :param model_a_params: 加载模型A所需的额外参数 (如 type, base)
    :param model_b_params: 加载模型B所需的额外参数
    """
    print("-" * 80)
    print(f"开始比较: {model_a_name} vs {model_b_name} (关系: {relation_type})")

    model_a_params = model_a_params or {}
    model_b_params = model_b_params or {}

    # 准备输出路径
    figure_save_path = os.path.join(output_dir, 'figures', f"{relation_type}_comparison.png")
    report_save_path = os.path.join(output_dir, 'test', f"{relation_type}_unmatched_tensors.json")
    ensure_dir(os.path.dirname(figure_save_path))
    ensure_dir(os.path.dirname(report_save_path))

    try:
        # 1. 初始化探测器（会自动加载模型）
        detector = SimilarityAnalyzer(
            model_A_name=model_a_name,
            model_B_name=model_b_name,
            model_A_type=model_a_params.get("type"),
            model_A_base=model_a_params.get("base"),
            model_B_type=model_b_params.get("type"),
            model_B_base=model_b_params.get("base")
        )

        # 2. 进行分析并保存结果
        cos_similarities = detector.compare_models_cos()
        detector.plot_cosine_similarity_stats(
            cos_ne=cos_similarities,
            save_path=figure_save_path,
            title_suffix=f"Type: {relation_type}"
        )
        # detector.export_unmatched_tensors(output_json=report_save_path) # 如果需要，取消注释

    except Exception as e:
        print(f"处理模型对 ({model_a_name}, {model_b_name}) 时发生严重错误: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数，定义和执行实验。"""
    config_file = "./data/model_pairs.json"
    output_base_dir = "./output/"
    
    # 初始化工具类
    manager = LineageManager(config_file)

    print(manager.model_map)

    # 示例2：运行一次 Adapter 与其 Base Model 的对比
    # run_single_comparison(
    #     model_a_name="monsterapi/gpt2_alpaca-lora",
    #     model_b_name="openai-community/gpt2",
    #     output_dir=output_base_dir,
    #     relation_type="adapter_vs_base",
    #     model_a_params={"type": "adapter", "base": "openai-community/gpt2"}
    # )
    
    # 示例3：运行一次两个无关模型的对比
    # run_single_comparison(
    #     model_a_name="openai-community/gpt2",
    #     model_b_name="google-bert/bert-base-uncased",
    #     output_dir=output_base_dir,
    #     relation_type="unrelated"
    # )

if __name__ == "__main__":
    main()