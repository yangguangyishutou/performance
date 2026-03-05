import json
import re
import sys
import shutil
import csv
from typing import List, Dict, Any, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pathlib import Path

pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(str(pp_dir))

from utils.Generator import Generator
from path_config import cfg_review_dir_path, cfg_translate_result_dir_path, cfg_graph_dir_path
from graph.retrieval_tools import sort_headers, load_nodes
from graph import Header, Method, Project
from agent.Agent import CppCompilationAgent

class AgentReviewStep:
    def __init__(self):
        pass

    def copy_files(self, ai_name, project_name):
        result_dir_path = cfg_translate_result_dir_path(ai_name, project_name)
        review_dir_path = cfg_review_dir_path(ai_name, project_name)
        if review_dir_path.exists():
            shutil.rmtree(review_dir_path)
        #复制文件
        shutil.copytree(result_dir_path, review_dir_path)

    def run_review(self, ai_name, project_name):
        print(f"Running review for {ai_name} on {project_name}")
        self.copy_files(ai_name, project_name)
        # data = load_nodes(cfg_binary_graph_file_path(ai_name, project_name))
        project = Project.load(cfg_graph_dir_path(ai_name, project_name))
        sorted_headers = sort_headers(project.headers, key="translated") 
        print(f"review order: {[header.key for header in sorted_headers]}") #type: ignore

        # 用于存储 CSV 数据的列表
        compilation_stats = []

        for header in sorted_headers: #type: ignore
            file_name = header.key + ".cpp"
            file_path = cfg_review_dir_path(ai_name, project_name) / file_name
            
            # 【修改点】：如果文件不存在，记录为 0 次尝试，而不是直接忽略
            if not file_path.exists():
                print(f"file skipped: {file_path}. Maybe an interface")
                compilation_stats.append([file_name, 0]) # 记录缺失的文件
                continue

            # Create agent
            agent = CppCompilationAgent(ai_name, project_name, file_path)

            # Run agent
            result = agent.run(max_attempts=10)
            
            # 收集文件名和编译次数
            attempts = result.get('attempts', 0)
            compilation_stats.append([file_name, attempts])

            # Print results
            print("\n" + "="*50)
            print("Agent Execution Complete")
            print("="*50)
            print(f"Status: {result['status']}")
            print(f"Attempts: {attempts}")
            if 'error' in result:
                print(f"Error: {result['error']}")
            if 'final_response' in result:
                print(f"Final Response: {result['final_response']}")
            print("\n" + "="*50)

        # 将统计数据写入 CSV 文件
        csv_file_path = cfg_review_dir_path(ai_name, project_name) / "compilation_stats.csv"
        try:
            with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                # 写入表头
                writer.writerow(["File Name", "Compilation Attempts"])
                # 写入统计数据
                writer.writerows(compilation_stats)
            print(f"Compilation statistics saved to: {csv_file_path}")
        except Exception as e:
            print(f"Failed to save compilation statistics CSV: {e}")



