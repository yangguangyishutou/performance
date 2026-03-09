import os
import ctypes
import json
from tree_sitter import Language, Parser

# === 路径配置 ===
CORE_LIB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../core/libssdc_core.so"))
LANG_LIB_PATH = os.path.abspath("build/my-languages.so")

# === C++ 接口定义 ===
class CompressResult(ctypes.Structure):
    _fields_ = [("data", ctypes.POINTER(ctypes.c_uint8)), ("size", ctypes.c_int)]

class DecompressResult(ctypes.Structure):
    _fields_ = [("tokens", ctypes.POINTER(ctypes.c_int)), 
                ("contexts", ctypes.POINTER(ctypes.c_int)),
                ("length", ctypes.c_int)]

# 加载库
try:
    if not os.path.exists(CORE_LIB_PATH): CORE_LIB_PATH = "/content/SSDC-Project/core/libssdc_core.so"
    if not os.path.exists(LANG_LIB_PATH): LANG_LIB_PATH = "/content/build/my-languages.so"
    
    ssdc_lib = ctypes.CDLL(CORE_LIB_PATH)
    
    # 压缩接口
    ssdc_lib.ssdc_compress_api.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.c_int]
    ssdc_lib.ssdc_compress_api.restype = ctypes.POINTER(CompressResult)
    ssdc_lib.ssdc_free_result.argtypes = [ctypes.POINTER(CompressResult)]
    
    # 解压接口
    ssdc_lib.ssdc_decompress_api.argtypes = [ctypes.POINTER(ctypes.c_uint8), ctypes.c_int]
    ssdc_lib.ssdc_decompress_api.restype = ctypes.POINTER(DecompressResult)
    ssdc_lib.ssdc_free_decomp_result.argtypes = [ctypes.POINTER(DecompressResult)]

except Exception as e:
    print(f"[Warning] Lib load failed: {e}")
    ssdc_lib = None

class SSDCProcessor:
    def __init__(self):
        self._setup_parser()
        # 预留结构化 ID
        self.token_map = {
            "<BLOCK_START>": 0, 
            "<BLOCK_END>": 1,
            "<STMT_END>": 2
        }
        self.reverse_map = {v: k for k, v in self.token_map.items()}
        self.next_id = 10 
        
        self.CTX_DEFAULT = 0
        self.CTX_CLASS = 1
        self.CTX_FUNC = 2
        self.CTX_DATA = 3

    def _setup_parser(self):
        global LANG_LIB_PATH
        if not os.path.exists(LANG_LIB_PATH):
            LANG_LIB_PATH = "/content/build/my-languages.so"
            
        if not os.path.exists(LANG_LIB_PATH): 
            print("[Error] Tree-sitter lib missing. Parser disabled.")
            return

        self.parser = Parser()
        self.parser.set_language(Language(LANG_LIB_PATH, 'python'))

    def get_token_id(self, text):
        if text not in self.token_map:
            self.token_map[text] = self.next_id
            self.reverse_map[self.next_id] = text
            self.next_id += 1
        return self.token_map[text]

    # === 功能 1: 压缩 ===
    def compress_file(self, code_bytes, output_path):
        tokens, contexts = self._parse_streams(code_bytes)
        length = len(tokens)
        c_tok = (ctypes.c_int * length)(*tokens)
        c_ctx = (ctypes.c_int * length)(*contexts)
        
        res = ssdc_lib.ssdc_compress_api(c_tok, c_ctx, length)
        compressed_data = bytes(res.contents.data[:res.contents.size])
        ssdc_lib.ssdc_free_result(res)
        
        with open(output_path, "wb") as f: f.write(compressed_data)
        
        # 保存 Map
        map_path = output_path + ".map"
        with open(map_path, "w") as f: json.dump(self.reverse_map, f)
            
        return len(compressed_data)

    # === 功能 2: 解压  ===
    def decompress_file(self, input_path):
        if not os.path.exists(input_path): return "Error: File not found"
        
        # 1. 读取数据
        with open(input_path, "rb") as f: data = f.read()
        
        # 2. 读取 Map
        map_path = input_path + ".map"
        if not os.path.exists(map_path): return "[Error] Map file missing."
        with open(map_path, "r") as f: 
            rev_map = {int(k): v for k, v in json.load(f).items()}
            
        # 3. C++ 解码
        c_data = (ctypes.c_uint8 * len(data))(*data)
        res = ssdc_lib.ssdc_decompress_api(c_data, len(data))
        
        restored_code = []
        indent_level = 0
        
        length = res.contents.length
        tokens_ptr = res.contents.tokens
        
        for i in range(length):
            tid = tokens_ptr[i]
            
            if tid == 0: # BLOCK_START
                indent_level += 1
                restored_code.append(":\n" + "    " * indent_level)
            elif tid == 1: # BLOCK_END
                indent_level = max(0, indent_level - 1)
                restored_code.append("\n" + "    " * indent_level)
            elif tid == 2: # STMT_END
                restored_code.append("\n" + "    " * indent_level)
            else:
                word = rev_map.get(tid, f"<{tid}>")

                # 只有当列表非空，且最后一个元素非空字符串时，才检查最后一个字符
                if restored_code and len(restored_code[-1]) > 0:
                    last_char = restored_code[-1][-1]
                    # 避免在换行符、空格、左括号后加空格
                    if last_char not in ['\n', ' ', '(', '[']:
                        restored_code.append(" ")

                
                restored_code.append(word)
                
        ssdc_lib.ssdc_free_decomp_result(res)
        return "".join(restored_code)

    def _parse_streams(self, code_bytes):
        if not hasattr(self, 'parser'): return [], []
        
        tree = self.parser.parse(code_bytes)
        cursor = tree.walk()
        tokens, contexts = [], []
        
        visited = False
        while True:
            if visited:
                if cursor.goto_next_sibling(): visited = False
                elif cursor.goto_parent(): visited = True
                else: break
            else:
                if cursor.node.child_count == 0:
                    text = code_bytes[cursor.node.start_byte:cursor.node.end_byte].decode('utf-8',errors='ignore')
                    ctx = self._determine_context(cursor.node)
                    
                    if text == ':': 
                        tokens.append(self.get_token_id(text))
                        contexts.append(ctx)
                        # 注入结构标记
                        tokens.append(0) # <BLOCK_START>
                        contexts.append(0)
                    else:
                        tokens.append(self.get_token_id(text))
                        contexts.append(ctx)
                    visited = True
                else:
                    if cursor.goto_first_child(): visited = False
                    else: visited = True
        return tokens, contexts

    def _determine_context(self, node):
        if not node.parent: return self.CTX_DEFAULT
        pt = node.parent.type
        nt = node.type
        if pt == 'class_definition' and nt == 'identifier': return self.CTX_CLASS
        if pt == 'function_definition' and nt == 'identifier': return self.CTX_FUNC
        if nt == 'string' or (pt in ['assignment','parameters'] and nt == 'identifier'): return self.CTX_DATA
        return self.CTX_DEFAULT
