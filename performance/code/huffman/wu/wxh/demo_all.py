
import os
import sys
sys.path.append(os.getcwd())
from ssdc.parser import SSDCProcessor
from ssdc.analyzer import SSDCAnalyzer

def main():
    input_file = "data/code_star100_10k.txt"
    compressed_file = "data/final_demo.ssdc"
    
    # 0. 准备数据
    if not os.path.exists(input_file):
        with open(input_file, "w") as f:
            f.write("class Demo:\n    def run(self):\n        if True:\n            print('Hello SSDC')\n")
    
    print("=== 1. SSDC Compression ===")
    with open(input_file, "rb") as f: code = f.read()
    proc = SSDCProcessor()
    size = proc.compress_file(code, compressed_file)
    print(f"Compressed to {size} bytes.")
    
    print("\n=== 2. Compressed Domain Analysis ===")
    analyzer = SSDCAnalyzer(compressed_file)
    analyzer.analyze()
    
    print("\n=== 3. Full Restoration (Decompression) ===")
    restored = proc.decompress_file(compressed_file)
    print("Restored Code Snippet:")
    print("-" * 20)
    print(restored[:200]) # 打印前200字符
    print("-" * 20)

if __name__ == "__main__":
    main()
