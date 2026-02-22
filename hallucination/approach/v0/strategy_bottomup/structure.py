class Header:
    def __init__(self, key:str, source_code: str):
        self.key = key
        self.source_code = source_code
        self.translate_prompt = ""  # 翻译提示
        self.raw_translated_code = ""  # 原始翻译结果
        self.translated_code = ""  # 翻译后的代码
        self.translate_status = 0  # 0:未翻译，1:已翻译, 2:错误
        self.methods = []

    def set_translated_code(self, translated_code: str):
        self.translated_code = translated_code
        if self.translated_code:
            self.translate_status = 1
        else:
            self.translate_status = 2
        

class Node:
    def __init__(self, key: str, code: str, source_tag: str, header: Header):
        self.key = key # 类名::方法名
        self.code = code # 源代码
        self.translate_prompt = "" # 翻译提示
        self.raw_translated_code = "" # 原始翻译结果
        self.translated_code = "" # 翻译后的代码
        self.source_tag = source_tag # 如 file1.001
        self.children:set[Node] = set() # 被我调用的方法
        self.parents:set[Node] = set() # 调用我的方法
        self.header = header  # 头部信息
        self.translate_status = 0  # 0:未翻译，1:已翻译, 2:错误

    def __repr__(self):
        return f"Node({self.key})"
    
    def __str__(self):
        # 获取 children 和 parents 的 key 值作为字符串
        children_keys = ', '.join([child.key for child in self.children]) if self.children else 'None'
        parents_keys = ', '.join([parent.key for parent in self.parents]) if self.parents else 'None'
    
        # 返回格式化字符串，包含了所需的所有信息
        return (
            f"Key: {self.key}\n"  # 方法的唯一标识
            #f"Code:\n{self.code}\n"  # 方法的源代码
            f"Source Tag: {self.source_tag}\n"  # 源文件标签
            f"Children: {children_keys}\n"  # 被调用的方法
            f"Parents: {parents_keys}\n"  # 调用当前方法的其他方法
            "\n"
        )
    
    def __eq__(self, other):
        return self.key == other.key

    def __hash__(self):
        return hash(id(self))

    
    def set_translated_code(self, translated_code: str):
        self.translated_code = translated_code
        if self.translated_code:
            self.translate_status = 1
        else:
            self.translate_status = 2