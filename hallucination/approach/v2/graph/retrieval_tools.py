import os
import re
import pickle
import sys
import json
from typing import Any, Dict
from collections import deque
from pathlib import Path

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)
from graph.header import Header
from graph.method import Method
from path_config import *


def find_method(split_dir: str, log_file):
    method_nodes = {}
    file_id = 1
    headers = []

    for file in os.listdir(split_dir):
        if not file.endswith('.json'):
            continue
        file_path = os.path.join(split_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                raw_content = f.read()

        json_data = json.loads(raw_content)
        class_type = json_data['type']
        class_name = json_data['className']

        log_file.write(f"{file} 提取{class_type}名为: {class_name}\n")

        header = Header(class_name, json_data['classDeclaration'])
        header.type = class_type
        header.imports = json_data['imports']
        header.fields = json_data['fieldDeclarations']
        header.parent_class = json_data['parentClass']
        header.interfaces = json_data['interfaces']
        headers.append(header)

        method_count = 1
        methods = json_data['methods']
        for method_match in methods:
            method_key = method_match['methodSignature']
            method_body = method_match['methodBody']
            statement_count = method_match['statementCount']

            source_tag = f"file{file_id}.{method_count:03}"

            # 创建并添加方法节点（Method），将其与 Header 正确关联
            node = Method(method_key, method_body, source_tag, header)
            if statement_count < 3:
                node.is_simple_method = True
            method_nodes[method_key] = node
            header.methods.append(node)  # 将方法节点添加到 Header 的 methods 列表
            method_count += 1

        file_id += 1

    # 输出日志
    log_file.write(f"共识别出 {len(method_nodes)} 个方法：\n")
    for key in sorted(method_nodes.keys()):
        log_file.write(f"  - {key}\n")

    return method_nodes, headers

def get_standard_signature(full_signature: str):
    if ':' not in full_signature:
        return None
    class_part, method_part = full_signature.split(':', 1)
    class_name = class_part.split('.')[-1] # 如果是嵌套类，class_name的格式为类名1$类名2$...$类名n

    method_name_only = method_part.split('(')[0].replace(' ', '')

    if method_name_only == '<init>':
        method_name_only = class_name

    # 参数串
    params = method_part.split('(')[1].split(')')[0]
    param_list = params.split(',') if params else []

    formatted_params = []
    for param in param_list:
        param_type = param.strip().split(' ')[0]
        simplified_type = param_type.split('.')[-1].split('$')[-1].replace(' ','')
        formatted_params.append(simplified_type)

    return f"{class_name}:{method_name_only}({','.join(formatted_params)})"


def build_call_graph(method_call_path: str, method_nodes: Dict[str, Method], log_file):
    # 存储被调用方存在但调用方不存在的方法
    missing_called_methods = {}

    with open(method_call_path, 'r', encoding='utf-8') as f:
        count = 0
        for line in f:
            try:
                parts = line.strip().split('\t')
                if len(parts) < 5:
                    log_file.write(f"跳过无效行: {line}\n")
                    continue
                caller = get_standard_signature(parts[2])
                callee = get_standard_signature(parts[3])

                if caller is None or callee is None:
                    log_file.write(f"无效的签名: {parts[2] or parts[3]}\n")
                    continue

                # 1. 调用方存在，被调用方不存在
                if caller in method_nodes and callee not in method_nodes:
                    # 被调用方不存在，创建被调用方的节点并存储在单独的字典中
                    missing_called_methods[callee] = {'signature': callee, 'params': callee.split('(')[1].split(')')[0]}
                    caller_node = method_nodes[caller]
                    callee_node = Method(callee, "", "", Header(callee.split(':')[0], ""))  # 被调用方的节点
                    callee_node.parents.add(caller_node)  # 将调用方添加为父节点 # type: ignore

                    log_file.write(f"调用方存在，被调用方不存在，已创建被调用方节点: {callee}\n")

                # 2. 调用方不存在，被调用方存在
                elif caller not in method_nodes and callee in method_nodes:
                    log_file.write(f"调用方不存在，忽略调用方: {caller}\n")

                # 3. 调用方和被调用方都不存在
                elif caller not in method_nodes and callee not in method_nodes:
                    log_file.write(f"调用方和被调用方都不存在，忽略调用关系: {line}\n")
                    continue

                # 4. 调用方和被调用方都存在
                elif caller in method_nodes and callee in method_nodes and caller != callee:
                    method_nodes[caller].children.add(method_nodes[callee])
                    method_nodes[callee].parents.add(method_nodes[caller])
                    count += 1
                    log_file.write(f"添加调用关系: {caller} -> {callee}\n")
            except Exception as e:
                log_file.write(f"处理行 {line} 时出错: {e}\n")
                print(f"处理行 {line} 时出错: {e}")
                print(f"caller: {caller}")
                print(f"callee: {callee}")
                raise

        log_file.write(f"共添加 {count} 条调用关系\n")

    if missing_called_methods:
        log_file.write("以下是调用方存在，但被调用方不存在的方法：\n")
        for callee, details in missing_called_methods.items():
            parents_keys = [parent.key for parent in callee_node.parents] #type: ignore
            log_file.write(f"  - {callee}\n")
            log_file.write(f"  Parents: {', '.join(parents_keys)}\n")  # 输出调用当前方法的其他方法

def get_ordered_method_groups(method_nodes: Dict[str, Method]):
    # Step 1: Initialize in-degree for each method (number of dependencies)
    in_degree = {key: len(node.children) for key, node in method_nodes.items()}
    
    # Step 2: Queue for methods with no dependencies (in-degree = 0)
    queue = deque([key for key, degree in in_degree.items() if degree == 0])
    
    # Step 3: BFS to create the layers
    ordered_groups = []
    while queue:
        current_group = []
        # For all nodes in the current layer
        for _ in range(len(queue)):
            key = queue.popleft()
            current_group.append(method_nodes[key])
            # Reduce the in-degree for each parent
            for parent in method_nodes[key].parents:
                in_degree[parent.key] -= 1
                if in_degree[parent.key] == 0:
                    queue.append(parent.key)

        ordered_groups.append(current_group)


    return ordered_groups

def sort_headers(headers: list[Header], key: str = "translated"):
    """
    对header节点按照调用关系进行排序
    key: 排序依据，为"translated"时按照翻译后的头文件包含关系排序，否则按照原始java文件中的import关系排序

    当存在循环依赖时，将无法排序的header节点按原顺序添加到已经排序的节点后
    """
    def find(headers:list[Header], key:str):
        for header in headers:
            if header.key == key:
                return header
        return None

    sorted_headers = []
    header_file_degree = {header.key: 0 for header in headers}
    point_to = {header.key: [] for header in headers}
    external_files = []
    if key == "translated":
        for header in headers:
            for include_file in header.external_header_files:
                include_class_name = include_file.split('.')[0]
                if include_class_name in header_file_degree:
                    header_file_degree[header.key] += 1
                    point_to[include_class_name].append(header)
                else:
                    if include_file not in external_files:
                        external_files.append(include_file)
    else:
        for header in headers:
            for imports_complete in header.imports:
                import_class_name = imports_complete.split('.')[-1]
                if import_class_name in header_file_degree:
                    header_file_degree[header.key] += 1
                    point_to[import_class_name].append(header)
                else:
                    if (import_class_name + '.java') not in external_files:
                        external_files.append(import_class_name + '.java')


    
    queue = deque([header for header in headers if header_file_degree[header.key] == 0])
    while queue:
        current_header = queue.popleft()
        sorted_headers.append(current_header)
        for point in point_to[current_header.key]:
            header_file_degree[point.key] -= 1
            if header_file_degree[point.key] == 0:
                queue.append(point)

    if max(header_file_degree.values()) > 0:
        print("存在循环依赖，无法排序")
        unsorted_headers = []
        for key, degree in header_file_degree.items():
            if degree > 0:
                if key == "translated":
                    print(f"{key}, include {[file for file in find(headers, key).external_header_files if file not in external_files]}") # type: ignore
                else:
                    print(f"{key}, import {[file.split('.')[-1] for file in find(headers, key).imports if (file.split('.')[-1] + ".java") not in external_files]}") # type: ignore
                unsorted_headers.append(find(headers, key))
        # return sorted_headers.extend(unsorted_headers)
        sorted_headers.extend(unsorted_headers) # 先执行扩展操作
        return sorted_headers                   # 然后返回列表对象
    sorted_headers.reverse()
    return sorted_headers
                

def save_nodes(data, file_path: str):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)
    print(f"方法节点已保存到 {file_path}")

def load_nodes(file_path):
    with open(file_path, 'rb') as f:
        return pickle.load(f)

def retrieve(split_dir:str, method_call_path:str, output_dir_path:str):
    log_path = os.path.join(output_dir_path, "log.txt")
    method_output_path = os.path.join(output_dir_path, "method_output.txt")
    header_output_path = os.path.join(output_dir_path, "header_output.txt")

    with open(log_path, "w", encoding="utf-8") as log_file:
        method_nodes, headers = find_method(split_dir, log_file)
        build_call_graph(method_call_path, method_nodes, log_file)
        sorted_methods = get_ordered_method_groups(method_nodes)
        

    with open(method_output_path, "w", encoding="utf-8") as f:
        for index, layer in enumerate[Any](sorted_methods):
            f.write(f"layer{index}==============================================\n")
            for node in layer:
                f.write(str(node))

    with open(header_output_path, "w", encoding="utf-8") as f:
        for header in headers:
            f.write(f"header==========\n")
            f.write(header.source_code)

    data = {"method_nodes": sorted_methods, "headers": headers}
    

    return data

def retrieve_project(ai_name, project_name):
    split_dir_path = cfg_split_output_dir_path(ai_name, project_name)
    output_dir_path = cfg_binary_graph_dir_path(ai_name, project_name)
    method_call_path = cfg_method_call_file_path(project_name)
    data = retrieve(str(split_dir_path), str(method_call_path), str(output_dir_path))
    headers = data["headers"]
    methods = data["method_nodes"]

    with open(output_dir_path/'output.txt', 'w', encoding='utf-8') as f:
        for header in headers:
            f.write("===============================================\n")
            f.write(header.key+'\n')
            for method in header.methods:
                f.write('    '+method.key+'\n')
                parents = [parent.key for parent in method.parents]
                f.write('      Parents: '+','.join(parents)+'\n')
                children = [child.key for child in method.children]
                f.write('      Children: '+','.join(children)+'\n')

    print(len(headers), sum([len(layer) for layer in methods]))

    sorted_headers = sort_headers(headers)
    for header in sorted_headers: #type: ignore
        print(header.key)

    return data


if __name__ == '__main__':
    ai_name = 'gpt'
    project_names = ['Cookie']
    for project_name in project_names:
        retrieve_project(ai_name, project_name)


    

