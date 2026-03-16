# """
# 数据加载和保存步骤
# 负责加载和保存翻译过程中的数据
# """
# import os
# import pickle
# from pathlib import Path
# from typing import Dict, Any
# import sys

# # 添加父目录到路径以便导入模块
# parent_dir = str(Path(__file__).parent.parent)
# if parent_dir not in sys.path:
#     sys.path.append(parent_dir)

# from graph.retrieval_tools import Header
# from graph.retrieval_tools import load_nodes, save_nodes
# from path_config import cfg_binary_graph_file_path,cfg_translate_detail_dir


# def load_translation_graph(ai_name: str, project_name: str, auto_update=False) -> Dict[str, Any]:
#     """
#     加载翻译数据

#     Args:
#         ai_name: AI名称
#         project_name: 项目名称

#     Returns:
#         包含headers和method_nodes的字典
#     """
#     graph_path = cfg_binary_graph_file_path(ai_name, project_name) 
#     if not graph_path.exists():
#         raise FileNotFoundError(f"Data file not found: {graph_path}")

#     data = load_nodes(graph_path)
#     if auto_update:
#         print("apply header updates...")
#         apply_header_updates(data["headers"], ai_name, project_name)

#     return data


# def save_translation_graph(data: Dict[str, Any], ai_name: str, project_name: str) -> None:
#     """
#     保存翻译数据

#     Args:
#         data: 要保存的数据
#         ai_name: AI名称
#         project_name: 项目名称
#     """
#     print("saving graph...")
#     graph_path = cfg_binary_graph_file_path(ai_name, project_name)
#     save_nodes(data, str(graph_path))
#     detail_data_dir_path = cfg_translate_detail_dir(ai_name, project_name)
#     print("detailed translation data...")
#     # 保存每个类到单独的文件
#     for header in data["headers"]:
#         save_entire_class(header, detail_data_dir_path / header.key)


# def apply_header_updates(headers: list[Header], ai_name: str, project_name: str) -> None:
#     """
#     应用头文件的更新

#     Args:
#         headers: 头文件列表
#         output_dir: 输出目录路径
#     """
#     detail_data_dir_path = cfg_translate_detail_dir(ai_name, project_name)
#     for header in headers:
#         apply_entire_class(header, detail_data_dir_path / header.key)