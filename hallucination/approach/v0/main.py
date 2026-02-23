import os
import sys
import asyncio

# 关键：直接运行本文件时，补全包搜索路径
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, "..", ".."))
APPROACH_ROOT = os.path.join(PROJECT_ROOT, "approach", "v0")
if APPROACH_ROOT not in sys.path:
    sys.path.insert(0, APPROACH_ROOT)
import asyncio

from file_operation import clone_files, init_logger
from strategy_class.translator import translate
from strategy_method.translator_method import translate_method
from dataset.data_set import create_data_set
from api_key import api_keys



###以下为必须设置###
###############################################################################################################################################################################################
# 基准文件
basic_file_name = 'RateLimiterExecutor.java'
# 使用模型
ai_model_name = 'qwen'  #deepseek, gpt, qwen
# 翻译形式
translation_form = 'method'  #class, method, bottomup
# 数据集来源：
data_set_source = ['Cookie',"EnableJUnit4MigrationSupport","HoverMenuService", "IntMath", "NoopIndexDAO"]
###############################################################################################################################################################################################


###以下可以不修改###
###############################################################################################################################################################################################
# 数据集路径
data_set_path = 'sitp-data-' + translation_form + '-' + ai_model_name + '.xlsx'
# 翻译文件夹
translation_dir_path = r'D:\projects\sitp\sitp-dataset\translation_java-cpp'
# 组名
group_name = basic_file_name.split('.')[0]
# 原始项目源文件路径
original_program_path = os.path.join(translation_dir_path, basic_file_name)
# 待翻译文件路径（一条完整的调用链上的文件，从原始项目中复制过来存在该路径下）
source_file_dir_path = os.path.join(translation_dir_path, group_name, "source") 
# 翻译后的文件保存路径
target_file_dir_path = os.path.join(translation_dir_path, group_name, ai_model_name, translation_form)

split_file_dir_path = os.path.join(translation_dir_path, group_name, "split")

# 以选中的文件为基准，将调用链上的所有文件复制到指定目录下
def clone_files_():
    logger = init_logger()
    clone_files(original_program_path, basic_file_name, source_file_dir_path, logger)

def translate_files():
    if translation_form == 'class':
        asyncio.run(translate(source_file_dir_path, target_file_dir_path, ai_model_name))
    elif translation_form == 'method':
        asyncio.run(translate_method(split_file_dir_path, target_file_dir_path, ai_model_name))

# 创建数据集
def create_data_sets():
    create_data_set(translation_dir_path, data_set_path, ai_model_name, data_set_source, translation_form)
###############################################################################################################################################################################################


if __name__ == '__main__':
    # clone_files()
    translate_files()
    # create_data_sets()
    pass




# import os
# import sys
# import asyncio

# # 关键：直接运行本文件时，补全包搜索路径
# THIS_DIR = os.path.dirname(os.path.abspath(__file__))
# PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, ".."))
# if PROJECT_ROOT not in sys.path:
#     sys.path.insert(0, PROJECT_ROOT)

# import sitp_script as sitp  # 现在可正常导入包


# ### ===== 必要配置（按需修改） =====
# basic_file_name   = "IntMath.java"
# ai_model_name     = "deepseek"        # "deepseek" 或 "gpt"
# translation_form  = "class"           # "class" | "method" | "bottomup"
# data_set_source   = ["Cookie", "EnableJUnit4MigrationSupport", "IntMath"]
# ### =================================


# # 路径：假设结构
# # <PROJECT_ROOT>/README.md
# # <PROJECT_ROOT>/translation_java-cpp/<项目>/
# # <PROJECT_ROOT>/sitp_script/...
# translation_dir_path = os.path.join(PROJECT_ROOT, "translation_java-cpp")

# # CSV 输出到 README 同级
# data_set_path = os.path.join(
#     PROJECT_ROOT,
#     f"dataset_{ai_model_name}_{translation_form}.csv"
# )

# # 如需翻译可用到的路径（仅生成数据集不必改）
# original_program_path  = translation_dir_path
# source_file_dir_path   = translation_dir_path
# target_file_dir_path   = os.path.join(translation_dir_path, ai_model_name, translation_form)
# split_file_dir_path    = os.path.join(translation_dir_path, "split")


# def clone_files():
#     """按基准文件复制调用链文件（委托 sitp_script 实现）"""
#     logger = sitp.init_logger()
#     sitp.clone_files(original_program_path, basic_file_name, source_file_dir_path, logger)

# def translate_files():
#     """根据策略执行翻译"""
#     if translation_form == "class":
#         asyncio.run(sitp.translate(source_file_dir_path, target_file_dir_path, ai_model_name))
#     elif translation_form == "method":
#         asyncio.run(sitp.translate_method(
#             split_file_dir_path,
#             target_file_dir_path,
#             ai_model_name,
#             sitp.api_keys[ai_model_name]
#         ))
#     elif translation_form == "bottomup":
#         if not data_set_source:
#             raise ValueError("data_set_source 为空，bottomup 至少需要一个项目名。")
#         asyncio.run(sitp.translate_bottomup(translation_dir_path, data_set_source[0], ai_model_name))
#     else:
#         raise ValueError(f"Unsupported translation_form: {translation_form}")

# def create_data_sets():
#     """生成数据集并将 CSV 保存到 README 同级"""
#     sitp.create_data_set(
#         translation_dir_path,
#         data_set_path,
#         ai_model_name,
#         data_set_source,
#         translation_form,
#     )
#     print("CSV saved to:", data_set_path)


# if __name__ == "__main__":
#     # 按需启用：
#     # clone_files()
#     # translate_files()
#     create_data_sets()
#     pass
