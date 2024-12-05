import javalang

# 读取 Java 源码文件
with open(r'E:\sitp\SITP\hallucination\data_set\translation\Cookie\source\NameValuePair.java', 'r') as file:
    java_code = file.read()

# 解析 Java 代码
tree = javalang.parse.parse(java_code)

# 提取方法名和构造函数名
method_names = []
for path, node in tree.filter(javalang.tree.MethodDeclaration):
    method_names.append(node.name)

for path, node in tree.filter(javalang.tree.ConstructorDeclaration):
    method_names.append(node.name)

# 输出方法名和构造函数名
for method_name in method_names:
    print(method_name)