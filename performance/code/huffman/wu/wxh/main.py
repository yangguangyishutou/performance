import os
import time
import argparse
import sys

# 将当前目录加入 path 以便导入 ssdc 包
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ssdc.parser import SSDCProcessor

def main():
    parser = argparse.ArgumentParser(description="SSDC: Semantic-Structure Decoupled Compressor")
    parser.add_argument("input_file", help="Path to input source code")
    parser.add_argument("-o", "--output", help="Output file path", default="output.ssdc")
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found.")
        return

    # 1. 读取源码
    print(f"Reading {args.input_file}...")
    with open(args.input_file, "rb") as f:
        code_bytes = f.read()
    original_size = len(code_bytes)

    # 2. 初始化处理器
    print("Initializing SSDC Processor...")
    try:
        processor = SSDCProcessor()
    except Exception as e:
        print(f"Initialization Failed: {e}")
        return

    # 3. 执行压缩
    print("Compressing...")
    t0 = time.time()
    compressed_data = processor.process_and_compress(code_bytes)
    t1 = time.time()

    # 4. 保存结果
    with open(args.output, "wb") as f:
        f.write(compressed_data)
    
    compressed_size = len(compressed_data)
    
    # 5. 生成报表
    print("\n" + "="*40)
    print("      SSDC COMPRESSION REPORT      ")
    print("="*40)
    print(f"Input File:      {args.input_file}")
    print(f"Original Size:   {original_size:,} bytes")
    print(f"Compressed Size: {compressed_size:,} bytes")
    print("-" * 40)
    print(f"Ratio:           {original_size / compressed_size:.2f} : 1")
    print(f"Space Saved:     {100 * (1 - compressed_size / original_size):.2f}%")
    print(f"Time Taken:      {t1 - t0:.4f} sec")
    print("="*40)

    # 验证文件头魔数 (简单检查)
    # 我们的 ContextModel 写入的前 4 bit 是 ContextCount(4)，所以第一个字节的高4位应该是 0100
    first_byte = compressed_data[0]
    if (first_byte >> 4) != 4:
        print("Warning: Header sanity check failed. Data might be corrupted.")
    else:
        print("Integrity Check: Header Valid (4 Contexts Detected).")

if __name__ == "__main__":
    main()
