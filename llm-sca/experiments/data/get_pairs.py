import json
import itertools
from collections import deque

def process_tree(root):
    """处理单个树结构"""
    # 使用BFS遍历维护祖先路径
    queue = deque([(root, [], [])])  # (当前节点, 祖先模型列表, 派生类型链)
    output_data = []

    while queue:
        current_node, ancestors, derive_chain = queue.popleft()
        current_model = current_node["model"]
        
        # 生成非相邻祖孙对（排除自己）
        for i, ancestor in enumerate(ancestors):
            derive_types = derive_chain[i:]  # 从祖先到当前节点的派生链
            output_data.append({
                "base_model": ancestor,
                "model": current_model,
                "lineage": ancestors + [current_model],
                "full_derive_path": derive_chain,
                "derive_path": derive_types,
            })
        
        # 处理子节点
        for child in current_node.get("children", []):
            child_model = child["model"]
            derive_type = child["metadata"].get("derived_type", "unknown")
            
            # 准备下一层遍历数据
            new_ancestors = ancestors + [current_model]
            new_derive_chain = derive_chain + [derive_type]
            queue.append((child, new_ancestors, new_derive_chain))
    
    return output_data

def main():
    # 处理所有输入文件
    filename = f"model_forest.json"
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {str(e)}")
    
    output_data = []
    # 处理每个根节点
    for root_node in data:
        output_part = process_tree(root_node)
        output_data.extend(output_part)

    with open("model_pairs.json", "w") as f:
        json.dump(output_data, f, indent=2)

if __name__ == "__main__":
    main()