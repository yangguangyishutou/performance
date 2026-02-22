import os
import re
import pickle
import sys
from typing import Any, Dict
from collections import deque
from pathlib import Path

p_dir = str(Path(__file__).parent)
pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(pp_dir)
if p_dir not in sys.path:
    sys.path.append(p_dir)
from graph.structure import Method, Header
from path_config import *


def find_method(split_dir: str, log_file):
    method_nodes = {}
    file_id = 1

    class_pattern = re.compile(
        r"'''(class|interface|enum)[ \t]*\r?\n[ \t]*(?:\/\/\s*)?//classname:\s*([^\r\n]+)\r?\n([\s\S]*?)'''",
        re.IGNORECASE
    )

    method_pattern = re.compile(
        r"'''method[ \t]*\r?\n[ \t]*(?:\/\/\s*)?methodname:\s*([^\r\n]+)\r?\n([\s\S]*?)(?=\r?\n?'''|$)",
        re.IGNORECASE
    )

    imports_pattern = re.compile(
        r"'''import\s*([\s\S]*?)\s*'''"
    )

    fields_pattern = re.compile(
        r"'''fields\s*([\s\S]*?)\s*'''"
    )

    parents_pattern = re.compile(
        r"'''parents\s*([\s\S]*?)\s*'''"
    )

    headers = []

    for file in os.listdir(split_dir):
        if not file.endswith('.txt'):
            continue

        file_path = os.path.join(split_dir, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
        except UnicodeDecodeError:
            with open(file_path, 'r', encoding='gbk') as f:
                raw_content = f.read()

        class_matches = class_pattern.finditer(raw_content)
        for class_match in class_matches:
            class_type = class_match.group(1).strip()
            class_name = class_match.group(2).strip()
            class_code = class_match.group(3).strip()

            # 处理imports
            import_matches = imports_pattern.finditer(raw_content)
            try:
                imports_str = next(import_matches).group(1).strip() if import_matches else ""
                imports_list = [imp.strip() for imp in imports_str.split('\n')]
            except StopIteration:
                imports_list = []
            # 处理字段
            fields_matches = fields_pattern.finditer(raw_content)
            try:
                fields_str = next(fields_matches).group(1).strip() if fields_matches else ""
            except StopIteration:
                fields_str = ""
            # 处理父类和接口
            try:
                parents_matches = parents_pattern.search(raw_content)
                if parents_matches:
                    parent_items = parents_matches.group(1).strip().split('|')
                else:
                    parent_items = ["None", "None"]
                parent_class_name = parent_items[0].strip() if parent_items != "None"  else ""
                interface_names = parent_items[1].strip().split(',') if parent_items[1] != "None" else []
            except Exception as e:
                parent_class_name = ""
                interface_names = []

            log_file.write(f"{file} 提取{class_type}名为: {class_name}\n")

            header = Header(class_name, class_code)
            header.type = class_type
            header.imports = imports_list
            header.fields = fields_str
            header.parent_class = parent_class_name
            header.interfaces = interface_names
            headers.append(header)

            method_count = 1
            matches = method_pattern.finditer(raw_content)
            for method_match in matches:
                method_signature = method_match.group(1).strip()  # 方法签名
                method_body = method_match.group(2).strip()  # 方法体

                if '::' in method_signature:
                    method_class, method_name = method_signature.split('::')
                else:
                    method_class = class_name  # 默认使用类名
                    method_name = method_signature

                method_key = f"{method_class}:{method_name}"  # 类名 + 方法名
                source_tag = f"file{file_id}.{method_count:03}"

                # 创建并添加方法节点（Method），将其与 Header 正确关联
                node = Method(method_key, method_body, source_tag, header)
                method_nodes[method_key] = node
                header.methods.append(node)  # 将方法节点添加到 Header 的 methods 列表
                method_count += 1

        file_id += 1

    # 输出日志
    log_file.write(f"共识别出 {len(method_nodes)} 个方法：\n")
    for key in sorted(method_nodes.keys()):
        log_file.write(f"  - {key}\n")

    return method_nodes, headers

def build_call_graph(method_call_path: str, method_nodes: Dict[str, Method], log_file):
    # 存储被调用方存在但调用方不存在的方法
    missing_called_methods = {}

    def match_method(full_signature: str):
        if ':' not in full_signature:
            log_file.write(f"无效的签名: {full_signature}\n")
            return None
        class_part, method_part = full_signature.split(':', 1)
        class_name = class_part.split('.')[-1]

        method_name_only = method_part.split('(')[0].replace(' ', '')

        if method_name_only == '<init>':
            method_name_only = class_name

        # 参数串
        params = method_part.split('(')[1].split(')')[0]
        param_list = params.split(',') if params else []

        formatted_params = []
        for param in param_list:
            param_type = param.strip().split(' ')[0]
            simplified_type = param_type.split('.')[-1].replace(' ','')
            formatted_params.append(simplified_type)

        key = f"{class_name}:{method_name_only}({','.join(formatted_params)})"

        log_file.write(f"生成方法签名 key: {key}\n")

        if key in method_nodes:
            return key
        return None

    with open(method_call_path, 'r', encoding='utf-8') as f:
        count = 0
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) < 5:
                log_file.write(f"跳过无效行: {line}\n")
                continue
            caller = parts[2].replace('java.lang.String', 'String').replace('java.lang.Object', 'Object')
            callee = parts[3].replace('java.lang.String', 'String').replace('java.lang.Object', 'Object')

            callee_class = parts[3].split(':')[0]
            callee_method = parts[3].split(':')[1]

            caller_key = match_method(caller)
            callee_key = match_method(callee)

            if caller_key is None:
                log_file.write(f"caller_key 无效: {caller}\n")
                caller_key = 'None'
            if callee_key is None:
                log_file.write(f"callee_key 无效: {callee}\n")
                callee_key = 'None'

            # 1. 调用方存在，被调用方不存在
            if caller_key != 'None' and callee_key == 'None':
                # 被调用方不存在，创建被调用方的节点并存储在单独的字典中
                missing_called_methods[callee] = {'signature': callee, 'params': callee.split('(')[1].split(')')[0]}
                caller_node = method_nodes.get(caller_key)
                caller_node.children_external.append((callee_class, callee_method)) #type: ignore

                callee_node = Method(callee, "", "", Header(callee_class, ""))  # 被调用方的节点
                callee_node.parents.add(caller_node)  # 将调用方添加为父节点 # type: ignore
                # method_nodes[callee] = callee_node

                log_file.write(f"调用方存在，被调用方不存在，已创建被调用方节点: {callee}\n")

            # 2. 调用方不存在，被调用方存在
            elif caller_key == 'None' and callee_key != 'None':
                log_file.write(f"调用方不存在，忽略调用方: {caller}\n")

            # 3. 调用方和被调用方都不存在
            elif caller_key == 'None' and callee_key == 'None':
                log_file.write(f"调用方和被调用方都不存在，忽略调用关系: {line}\n")
                continue

            # 4. 调用方和被调用方都存在
            elif caller_key != 'None' and callee_key != 'None' and caller_key != callee_key:
                method_nodes[caller_key].children.add(method_nodes[callee_key])
                method_nodes[callee_key].parents.add(method_nodes[caller_key])
                count += 1
                log_file.write(f"添加调用关系: {caller_key} -> {callee_key}\n")

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

def sort_headers(headers: list[Header]):
    def find(headers:list[Header], key:str):
        for header in headers:
            if header.key == key:
                return header
        return None

    sorted_headers = []
    header_file_degree = {header.key: 0 for header in headers}
    point_to = {header.key: [] for header in headers}
    external_files = []
    for header in headers:
        for include_file in header.header_files:
            include_class_name = include_file.split('.')[0]
            if include_class_name in header_file_degree:
                header_file_degree[header.key] += 1
                point_to[include_class_name].append(header)
            else:
                if include_file not in external_files:
                    external_files.append(include_file)
    
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
                print(f"{key}, include {[file for file in find(headers, key).header_files if file not in external_files]}") # type: ignore
                unsorted_headers.append(find(headers, key))
        return sorted_headers.extend(unsorted_headers)
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
    output_file_path = os.path.join(output_dir_path, "nodes.pkl")

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
    

    save_nodes(data, output_file_path)
    return data



def main(ai_name, project_name):
    split_dir_path = cfg_split_output_dir_path(ai_name, project_name)
    output_dir_path = cfg_binary_graph_dir_path(ai_name, project_name)
    method_call_path = cfg_method_call_file_path(project_name)
    retrieve(str(split_dir_path), str(method_call_path), str(output_dir_path))
    data = load_nodes(output_dir_path/"nodes.pkl")
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


if __name__ == '__main__':
    ai_name = 'gpt'
    project_names = ['Cookie']
    for project_name in project_names:
        main(ai_name, project_name)


    

