import json
import itertools
from collections import deque

def process_tree(root, writer_adj, writer_non_adj):
    """处理单个树结构"""
    # 使用BFS遍历维护祖先路径
    queue = deque([(root, [], [])])  # (当前节点, 祖先模型列表, 派生类型链)
    
    while queue:
        current_node, ancestors, derive_chain = queue.popleft()
        current_model = current_node["model"]
        
        # 生成非相邻祖孙对（排除自己）
        for i, ancestor in enumerate(ancestors):
            derive_types = derive_chain[i:]  # 从祖先到当前节点的派生链
            writer_non_adj.write(json.dumps({
                "ancestor_model": ancestor,
                "model": current_model,
                "derive_type": derive_types
            }) + "\n")
        
        # 处理子节点
        for child in current_node.get("children", []):
            child_model = child["model"]
            derive_type = child["metadata"].get("derived_type", "unknown")
            
            # 写入相邻父子对
            writer_adj.write(json.dumps({
                "base_model": current_model,
                "model": child_model,
                "derive_type": derive_type
            }) + "\n")
            
            # 准备下一层遍历数据
            new_ancestors = ancestors + [current_model]
            new_derive_chain = derive_chain + [derive_type]
            queue.append((child, new_ancestors, new_derive_chain))

def main():
    # 创建输出文件
    with open("adjacent_pairs.jsonl", "w") as f_adj, \
         open("non_adjacent_pairs.jsonl", "w") as f_non_adj:
        
        # 处理所有输入文件
        filename = f"model_forest.json"
        try:
            with open(filename, "r") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading {filename}: {str(e)}")
            continue
        
        # 处理每个根节点
        for root_node in data:
            process_tree(root_node, f_adj, f_non_adj)

if __name__ == "__main__":
    main()