import re
from structure import Node, Header
from typing import List
import os
import pickle
import time
from pathlib import Path

def get_cpp_code(raw_content:str):
    pattern = r'```(\w*)\n(.*?)\n```'
    result = re.search(pattern, raw_content, re.DOTALL)
    if result:
        lang = result.group(1)
        code = result.group(2)
        if lang and lang != 'cpp':
            print(f"warning: \n{raw_content}\nlanguage {lang} is not supported")
        if code:
            return code
        else:
            print(f"warning: \n{raw_content}\ncannot find code in header translation result")
            return ""
    else:
        print(f"warning: \n{raw_content}\ncannot find code wrapped by ``` ``` in header translation result")
        return ""




def prompt_header(header: Header):
    return f"Following is a Java class/interface/enum declaration along with field and method declarations: \n{header.source_code}\nPlease translate it into a header file that conforms to the C++17 standard syntax and performs the same functions. The methods(if any) only needs to be declared, not implemented. Other classes that appear in the code have been implemented in C++. If necessary, you can use the header file with the same name."


def prompt_method(node: Node):
    if not node.code:
        print(f"Warning: {node.key} has no code")
        node.translate_status = 2
        return ""
    if not node.header.translated_code:
        print(f"Warning: {node.key} has not been translated yet")
        node.translate_status = 2
        return ""
    prompt = f"""
    {node.header.translated_code}\nPlease implement the following functions according to the contents of the above header file:\n{node.code}\n It is a Java method that you need to translate into a member function that conforms to the C++ standard syntax. Here are some rules you need to follow:
    1. Only implement this one method, and the others in the header file do not need to be implemented. Only one function is supposed to appear in your code.
    2. Other classes that appear in the code have been implemented in C++. If necessary, you can use the header file with the same name. 
    3. Only the in vitro implementation of the function is required, no other non-code content is required, and no usage examples are required.  
    4. Your code should conforms C++17 standard syntax. That means you have to not use any headers or syntaxes that are too old or too new.  
    5. Completely implement all functions of the function, do not omit error handling and special branches, etc.
    6. Double-check every function you call to make sure their header files are included. 
    7. If some of the allocated memory is no longer used, make sure to release it at the right time. 
    8. For the interface, you only need to maintain the function declaration, don't implement it.
    """
    referance = ""
    for other_node in node.children:
        if other_node.translated_code:
            referance += f"{other_node.translated_code}\n"
        else:
            print(f"Warning: {other_node.key} has not been translated yet")
            node.translate_status = 2
    if referance:
        prompt += f"\n Here are some related code that you may need to refer to:\n{referance}"
    return prompt

def save_data(path:str, headers:List[Header], method_nodes:List[List[Node]]):
    with open(path, 'wb') as f:
        data = {"headers": headers, "method_nodes": method_nodes}
        pickle.dump(data, f)
    print(f"数据已保存到 {path}")

def load_data(path:str):
    with open(path, 'rb') as f:
        data = pickle.load(f)
    return data['headers'], data['method_nodes']


def _translate(project_dir:str, project_name:str, generator: Generator, log_file:str):
    result_file = os.path.join(project_dir,"output_info", project_name, "nodes.pkl")
    
    if os.path.exists(result_file):
        header_nodes, method_nodes = load_data(result_file)
    else:
        data = retrieve(project_dir, project_name)
        header_nodes = data['headers']
        method_nodes = data['method_nodes']

    f = open(log_file, "w", encoding="utf-8")

    # 翻译头文件
    headers_to_translate:List[Header] = []
    header_prompts:List[str] = []
    header_results:List[str] = []
    f.write("+++++++++++++++++++++++Header++++++++++++++++++++++++\n")
    # 先查找需要翻译的头文件
    for header in header_nodes:
        if header.translate_status == 1:
            print(f"{header.key} has been translated, skip.")
            continue
        headers_to_translate.append(header)
        header.translate_prompt = prompt_header(header)
        header_prompts.append(header.translate_prompt)
    header_results = generator.generate(header_prompts)
    # 异步翻译
    for header, result in zip(headers_to_translate, header_results):
        f.write(f"--------------------Header {header.key}-------------------\n")
        header.raw_translated_code = result
        header.set_translated_code(get_cpp_code(result))
        f.write(f"Header prompt: \n{header.translate_prompt}\n translated code:\n {header.translated_code}\n")
    save_data(result_file, header_nodes, method_nodes) # 保存进度

    # 翻译方法
    f.write("+++++++++++++++++++++++Method+++++++++++++++++++++++\n")
    # 逐层翻译
    for index, layer in enumerate(method_nodes):
        f.write(f"=================Layer {index}=================\n")
        # 查找需要翻译的节点
        nodes_to_translate:List[Node] = []
        method_prompts:List[str] = []
        method_results:List[str] = []
        for node in layer:
            if node.translate_status == 1:
                print(f"{node.key} has been translated, skip.")
                continue
            nodes_to_translate.append(node)
            node.translate_prompt = prompt_method(node)
            method_prompts.append(node.translate_prompt)   
        # 异步翻译         
        method_results = generator.generate(method_prompts)
        for node, result in zip(nodes_to_translate, method_results):
            f.write(f"-------------------Method {node.key}-------------------\n")
            node.raw_translated_code = result
            node.set_translated_code(get_cpp_code(result))
            f.write(f"Method prompt: \n{node.translate_prompt}\n translated code:\n {node.translated_code}\n")
        # 保存进度
        save_data(result_file, header_nodes, method_nodes)
    f.close()

def translate(project_name:str, model_name:str):
    project_dir = r"C:\Users\30300\Desktop\workshop\sitp-dataset-main\sitp-dataset\translation_java-cpp"
    log_file = rf"{project_dir}\output_info\{project_name}\translate_log_{time.strftime('%Y%m%d_%H%M%S')}.txt"
    key = api_keys[model_name]
    generator = Generator(model_name, key)
    _translate(project_dir, project_name, generator, log_file)


def make_files(data_file:str,target_dir:Path):
    headers, method_nodes = load_data(data_file)
    if not target_dir.exists():
        target_dir.mkdir()
    for header in headers:
        with open(target_dir/f"{header.key}.h", "w", encoding="utf-8") as f:
            f.write(header.translated_code)
        
        with open(target_dir/f"{header.key}.cpp", "w", encoding="utf-8") as f:
            include_line = f"#include \"{header.key}.h\"\n"
            implement_line = ""
            for method_node in header.methods:
                for line in method_node.translated_code.split("\n"):
                    if "#include" in line:
                        if line not in include_line:
                            include_line += line + "\n"
                    else:
                        implement_line += line + "\n"
            f.write(include_line + "\n" + implement_line)





        




