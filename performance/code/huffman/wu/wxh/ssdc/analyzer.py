import sys
import os
import ctypes
from .parser import SSDCProcessor, ssdc_lib, DecompressResult

class SSDCAnalyzer:
    def __init__(self, filepath):
        self.filepath = filepath
        
    def analyze(self):
        if not os.path.exists(self.filepath):
            print("File not found.")
            return

        # 1. 直接读取二进制流
        with open(self.filepath, "rb") as f: data = f.read()
        
        # 2. 调用 Core 进行“盲解码” (Blind Decode)
        # 我们不需要 TokenMap (字符串字典)，只需要 ID
        c_data = (ctypes.c_uint8 * len(data))(*data)
        res = ssdc_lib.ssdc_decompress_api(c_data, len(data))
        
        # 3. 结构分析
        # 直接在 ID 层面进行统计，速度极快
        tokens = res.contents.tokens
        length = res.contents.length
        
        max_depth = 0
        curr_depth = 0
        block_count = 0
        
        # ID=0 是我们在 Parser 里定义的 <BLOCK_START>
        for i in range(length):
            tid = tokens[i]
            if tid == 0: # <BLOCK_START>
                curr_depth += 1
                block_count += 1
                max_depth = max(max_depth, curr_depth)
            elif tid == 1: # <BLOCK_END> (如果 parser 实现了 dedent 检测)
                curr_depth = max(0, curr_depth - 1)
                
        ssdc_lib.ssdc_free_decomp_result(res)
        
        print(f"\n[SSDC Analyzer] Analysis Result (Without Full Decompression):")
        print(f"-----------------------------------------------------------")
        print(f"File: {self.filepath}")
        print(f"Total Tokens:   {length}")
        print(f"Logical Blocks: {block_count}")
        print(f"Max Nesting:    {max_depth} (Deep Logic Detected!)")
        print(f"-----------------------------------------------------------")
        print(f"Status: Analysis performed directly on compressed stream.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m ssdc.analyzer <file.ssdc>")
    else:
        analyzer = SSDCAnalyzer(sys.argv[1])
        analyzer.analyze()
