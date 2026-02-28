from pathlib import Path
from typing import Optional, LiteralString
from utils.clean_filename import sanitize_filename  # 导入清洗逻辑

class Header:

    temp_header_codes:dict[str, str] = {}  # filename.h, <code>

    def __init__(self, key:str, source_code: str):
        # 结构信息
        self.key = key
        self.file_name = sanitize_filename(key)
        self.type = "" # class, interface, enum
        self.source_code = source_code
        self.methods:list[Method] = []
        self.imports = []
        self.fields:str = ""
        self.parent_class:str = ""
        self.interfaces:list[str]|list[LiteralString] = []
        # self.external_classes:list[str] = []

        # 翻译信息
        self.translated_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translate_prompt = "" # 翻译提示
        self.translated_code = ""  # 翻译后的代码
        self.translated_fields:list[str] = []  # 翻译后的字段

        self.header_files:list[str] = [] # 包含的其他头文件
        self.implemented_header_files:list[str] = [] # 实现的头文件

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        self.compile_output = ""  # 编译输出
        # 标注信息
        self.errors = []

        # 迭代信息
        self.iter_suggestion = []  # 迭代建议
        self.history_iter_suggestions:list[list[str]] = []  # 迭代建议历史记录

    def __hash__(self):
        return hash(id(self))

    def add_iter_suggestion(self, suggestion:str):
        self.iter_suggestion.append(suggestion)


    def clean(self, store_iter_suggestion:bool=False, del_history_iter_suggestion:bool=False):
        self.translated_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translate_prompt = "" # 翻译提示
        self.translated_code = ""  # 翻译后的代码
        self.translated_fields = []  # 翻译后的字段

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        self.compile_output = ""  # 编译输出
        self.errors = []

        if store_iter_suggestion:
            self.history_iter_suggestions.append(self.iter_suggestion)
        else:
            if del_history_iter_suggestion:
                self.history_iter_suggestions = []
        self.iter_suggestion = []

    def find_method(self, key:str) :
        key = key.replace(' ','').replace('final','')
        for method in self.methods:
            if method.key.split(':')[1].replace(' ','') == key:
                return method
        return None
        
    def save_to_dir(self, dir_path:Path):
        dir_path.mkdir(exist_ok=True, parents=True)
        dir = dir_path
        dir.mkdir(exist_ok=True, parents=True)

        basic_info_file = dir / "basic_info.txt"
        source_code_file = dir / "source_code.java"

        translate_scheme_prompt_file = dir / "translate_scheme_prompt.xml"
        translate_scheme_file = dir / "translate_scheme.xml"

        translate_prompt_file = dir / "translate_prompt.xml"
        translated_file = dir / "translated.cpp"

        raw_translated_file = dir / "raw_translated.cpp"

        with open(basic_info_file, "w", encoding="utf-8") as f:
            f.write(self.key+'\n')
            f.write('type:'+ self.type+'\n')
            f.write('parent_class:'+ self.parent_class+'\n')
            f.write('interfaces:\n')
            for interface in self.interfaces:
                f.write("   "+interface+'\n')
            f.write('methods:\n')
            for method in self.methods:
                f.write("   "+method.key+'\n')
            f.write('imports:\n')
            for imp in self.imports:
                f.write("   "+imp+'\n')
            f.write('fields:\n')
            f.write(self.fields+'\n')
            f.write('header files:\n')
            f.write(','.join(self.header_files)+'\n')
            f.write('implemented header files:\n')
            f.write(','.join(self.implemented_header_files)+'\n')

        with open(source_code_file, "w", encoding="utf-8") as f:
            f.write(self.source_code)

        with open(translate_scheme_prompt_file, "w", encoding="utf-8") as f:
            f.write(self.translated_scheme_prompt)
        with open(translate_scheme_file, "w", encoding="utf-8") as f:
            f.write(self.translate_scheme)

        with open(translate_prompt_file, "w", encoding="utf-8") as f:
            f.write(self.translate_prompt)
        with open(translated_file, "w", encoding="utf-8") as f:
            f.write(self.translated_code)

        with open(raw_translated_file, "w", encoding="utf-8") as f:
            f.write(self.raw_translated_code)

    def apply(self, dir_path:Path):
        source_code_file = dir_path / "source_code.java"
        translate_scheme_prompt_file = dir_path / "translate_scheme_prompt.xml"
        translate_scheme_file = dir_path / "translate_scheme.xml"

        translate_prompt_file = dir_path / "translate_prompt.xml"
        translated_file = dir_path / "translated.cpp"

        raw_translated_file = dir_path / "raw_translated.cpp"

        with open(source_code_file, "r", encoding="utf-8") as f:
            self.source_code = f.read().strip()

        with open(translate_scheme_prompt_file, "r", encoding="utf-8") as f:
            self.translated_scheme_prompt = f.read().strip()
        with open(translate_scheme_file, "r", encoding="utf-8") as f:
            self.translate_scheme = f.read().strip()

        with open(translate_prompt_file, "r", encoding="utf-8") as f:
            self.translate_prompt = f.read().strip()
        with open(translated_file, "r", encoding="utf-8") as f:
            self.translated_code = f.read().strip()

        with open(raw_translated_file, "r", encoding="utf-8") as f:
            self.raw_translated_code = f.read().strip()

    @classmethod
    def get_all_header_name(cls, headers):
        return [header.key for header in headers]
    
    def is_translated(self) -> bool:
        """判断该头文件是否已经翻译完成"""
        # 如果是类/接口，看代码是否生成；如果是枚举，通常直接认为 source_code 存在即可
        # 这里建议以 translated_code 是否有内容为准
        return bool(self.translated_code and self.translated_code.strip())


class Method:
    def __init__(self, key: str, code: str, source_tag: str, header: Header):
        self.key = key # 类名:方法名(参数类型)
        self.file_name = sanitize_filename(key)
        self.code = code # 源代码
        self.children:set[Method] = set() # 被我调用的方法
        self.children_external:list[tuple[str, str]] = [] # 被我调用的外部方法
        self.parents:set[Method] = set() # 调用我的方法
        self.source_tag = source_tag # 如 file1.001
        self.header = header  # 头部信息

        self.is_boilerplate = False # 是否是样板代码

        # 翻译信息
        self.temp_header = "" # 临时头

        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translated_declaration = "" # 翻译后的声明

        self.translate_prompt = ""
        self.translated_code = "" # 翻译后的代码

        self.raw_translated_code = ""  # 未经过处理的翻译后的代码

        # 编译信息
        self.compile_unit = ""
        self.compile_output = ""

        # 标注信息
        self.errors = []

        # 迭代信息
        self.history_iter_suggestions:list[list[str]] = [] # 历史迭代建议
        self.iter_suggestion:list[str] = [] # 当前迭代建议

    def __repr__(self):
        return f"Method({self.key})"
    
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


    def add_iter_suggestion(self, suggestion:str):
        self.iter_suggestion.append(suggestion)
    

    def is_translated(self):
        return not self.translated_code == ""

    def get_name(self):
        return self.key.split(':')[1].split('(')[0]

    def clean(self, store_iter_suggestion:bool=False, del_history_iter_suggestion:bool=False):
        self.temp_header = "" # 临时头

        self.translate_scheme_prompt = ""  # 翻译方案提示
        self.translate_scheme = ""  # 翻译方案

        self.translated_declaration = "" # 翻译后的声明

        self.translate_prompt = ""
        self.translated_code = "" # 翻译后的代码

        if store_iter_suggestion:
            self.history_iter_suggestions.append(self.iter_suggestion)
        else:
            if del_history_iter_suggestion:
                self.history_iter_suggestions = []
        self.iter_suggestion = []

    def save_to_dir(self, dir_path:Path):
        dir_path.mkdir(exist_ok=True, parents=True)

        basic_info_file = dir_path / "basic_info.txt"

        translate_scheme_prompt_file = dir_path / "translate_scheme_prompt.xml"
        translate_scheme_file = dir_path / "translate_scheme.xml"

        translate_prompt_file = dir_path / "translate_prompt.xml"
        translated_file = dir_path / "translated.cpp"

        raw_translated_file = dir_path / "raw_translated.xml"

        temp_header_file = dir_path / "temp_header.h"

        complie_output_file = dir_path / "compile_output.txt"
        with open(basic_info_file, "w", encoding="utf-8") as f:
            f.write(self.key+'\n')

            f.write('===============================\n')
            f.write('is_boilerplate:' + str(self.is_boilerplate)+'\n')
            f.write('methods called by me:\n')
            for child in self.children:
                f.write("   "+child.key+'\n')
            for external_child in self.children_external:
                f.write("   "+external_child[0]+'::'+external_child[1]+'(external)\n')
            f.write('methods calling me:\n')
            for parent in self.parents:
                f.write("   "+parent.key+'\n')
            f.write('===============================\n')

            f.write('===============================\n')
            f.write('header:\n')
            f.write(self.header.key+'\n')
            f.write('translated_declaration:\n')
            f.write(self.translated_declaration+'\n')
            f.write('===============================\n')
            f.write('===============================\n')
            f.write('source_code:\n')
            f.write(self.code+'\n')
            f.write('===============================\n')

        with open(translate_scheme_prompt_file, "w", encoding="utf-8") as f:
            f.write(self.translate_scheme_prompt)
        with open(translate_scheme_file, "w", encoding="utf-8") as f:
            f.write(self.translate_scheme)

        with open(translate_prompt_file, "w", encoding="utf-8") as f:
            f.write(self.translate_prompt)
        with open(translated_file, "w", encoding="utf-8") as f:
            f.write(self.translated_code)

        with open(raw_translated_file, "w", encoding="utf-8") as f:
            f.write(self.raw_translated_code)

        with open(temp_header_file, "w", encoding="utf-8") as f:
            f.write(self.temp_header)

        with open(complie_output_file, "w", encoding="utf-8") as f:
            f.write(self.compile_output)

    def apply(self, dir_path:Path):
        translate_scheme_prompt_file = dir_path / "translate_scheme_prompt.xml"
        translate_scheme_file = dir_path / "translate_scheme.xml"

        translate_prompt_file = dir_path / "translate_prompt.xml"
        translated_file = dir_path / "translated.cpp"

        raw_translated_file = dir_path / "raw_translated.xml"

        temp_header_file = dir_path / "temp_header.h"

        with open(translate_scheme_prompt_file, "r", encoding="utf-8") as f:
            self.translate_scheme_prompt = f.read().strip()
        with open(translate_scheme_file, "r", encoding="utf-8") as f:
            self.translate_scheme = f.read().strip()

        with open(translate_prompt_file, "r", encoding="utf-8") as f:
            self.translate_prompt = f.read().strip()
        with open(translated_file, "r", encoding="utf-8") as f:
            self.translated_code = f.read().strip()

        with open(raw_translated_file, "r", encoding="utf-8") as f:
            self.raw_translated_code = f.read().strip()

        with open(temp_header_file, "r", encoding="utf-8") as f:
            self.temp_header = f.read().strip()

    def is_translated(self) -> bool:
        """判断该头文件是否已经翻译完成"""
        # 如果是类/接口，看代码是否生成；如果是枚举，通常直接认为 source_code 存在即可
        # 这里建议以 translated_code 是否有内容为准
        return bool(self.translated_code and self.translated_code.strip())

# class Project:
#     def __init__(self, name:str, headers:list[Header], methods:list[Method]):
#         self.name = name
#         self.headers = headers

        

def save_entire_class(header:Header, dir_path:Path):
    dir_path.mkdir(exist_ok=True, parents=True)
    # print('========================================')
    print(f'-- save class {header.key}... --')
    header.save_to_dir(dir_path/f'{header.file_name}{{header}}')
    for method in header.methods:
        # print(f'save method {method.key}...')
        method_dir_name = method.file_name
        method.save_to_dir(dir_path/method_dir_name)
    # print('========================================')


def apply_entire_class(header:Header, dir_path:Path):
    print(f'-- sync class {header.key}... --')
    header.apply(dir_path/f"{header.file_name}{{header}}")
    for method in header.methods:
        method_dir_name = method.file_name
        method.apply(dir_path/method_dir_name)