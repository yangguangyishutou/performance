import os
from transformers import AutoModel, AutoTokenizer
from optimum.exporters.onnx import main_export

# 模型名称或本地路径
model_name = "amitom/gpt2-DiabloGPT-SLERP"

# 导出 ONNX 模型保存路径
base_output_dir = f"./{model_name.split('/')[1]}"
onnx_output_dir = base_output_dir + "/onnx"

# 模型任务类型
task = "text-generation"

def export_model_to_onnx(model_name, onnx_output_dir, task):
    """
    使用Optimum库将HuggingFace模型导出为ONNX格式
    
    参数：
    model_name -- 模型标识符或本地路径
    onnx_output_dir -- ONNX输出目录路径
    task -- 模型任务类型
    
    """
    print(f"ONNX export model to onnx using optimum: output dir = {onnx_output_dir}")
    main_export(model_name_or_path=model_name, task=task, output=onnx_output_dir)
    
    # 另外下载 onnx 方法
    # os.system(f'optimum-cli export onnx --model {model_name} {onnx_output_dir + "2"}') 
    
    print("export finished")

def conver_json(onnx_output_dir):
    """
    使用Netron的脚本将ONNX模型转换为JSON格式
    
    参数：
    onnx_output_dir -- 包含model.onnx的目录路径
    
    注意：
    - 需要提前克隆Netron仓库并安装Node.js依赖
    - 确保make_model_json.js脚本路径存在于 Netron 仓库 source 文件夹
    """
    exit_code = os.system(f"node ../netron-main/source/make_model_json.js {onnx_output_dir}/model.onnx")

'''
已知问题说明：

1. TracerWarning 警告：
   模型中的条件判断语句（如 if tensor > 0）会导致跟踪警告，因为ONNX导出时
   需要静态图结构。这可能导致导出的模型在动态输入情况下行为不一致。

2. 权重共享问题：
   - lm_head.weight 和 transformer.wte.weight 是共享权重
   - 导出为ONNX时会被视为两个独立参数，可能导致：
     * 模型文件体积增大
     * 推理时潜在的一致性风险
'''

if __name__ == "__main__":
    export_model_to_onnx(model_name, onnx_output_dir, task)
    conver_json(onnx_output_dir)
