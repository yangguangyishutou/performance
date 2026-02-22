import os
import re
from typing import List, Dict, Set, Optional


def extract_imports(java_file: str) -> List[str]:
    """
    解析 Java 文件中的 import 语句
    """
    imports = []
    pattern = re.compile(r'^import\s+([a-zA-Z0-9_.]+);', re.MULTILINE)

    with open(java_file, 'r', encoding='utf-8') as f:
        content = f.read()
        imports = pattern.findall(content)

    # 排除 JDK 自带的类
    imports = [imp for imp in imports if not imp.startswith(("java.", "javax."))]
    return imports


def resolve_import_to_file(import_path: str, project_root: str) -> Optional[str]:
    """
    根据 import 语句解析实际的 Java 文件路径
    例如：com.example.util.Helper → project_root/com/example/util/Helper.java
    """
    parts = import_path.split(".")
    file_path = os.path.join(project_root, *parts) + ".java"

    return file_path if os.path.exists(file_path) else None


def analyze_dependencies(java_file: str, project_root: str, visited: Optional[Set[str]] = None) -> Dict:
    """
    递归分析依赖链，返回一个树状结构
    """
    if visited is None:
        visited = set()

    if java_file in visited:
        return {java_file: "already analyzed"}

    visited.add(java_file)

    # 提取 import
    imports = extract_imports(java_file)

    children = {}
    for imp in imports:
        target_file = resolve_import_to_file(imp, project_root)

        if target_file:
            # 递归搜索
            children[imp] = analyze_dependencies(target_file, project_root, visited)
        else:
            children[imp] = "file not found"

    return {java_file: children}


def print_dependency_tree(tree: Dict, indent=0):
    """
    美观打印依赖树
    """
    for key, value in tree.items():
        print(" " * indent + os.path.basename(key))
        if isinstance(value, dict):
            print_dependency_tree(value, indent + 4)
        else:
            print(" " * (indent + 4) + str(value))


# if __name__ == "__main__":
#     # 示例：起始文件与项目根目录
#     start_file = r"/path/to/project/src/main/java/com/example/Main.java"
#     project_root = r"/path/to/project/src/main/java"

#     tree = analyze_dependencies(start_file, project_root)
#     print("\n=== Dependency Tree ===")
#     print_dependency_tree(tree)
