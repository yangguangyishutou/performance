import json

def process_jsonl():
    """
    处理jsonl文件，每100行提取前10行，处理10000行，共提取1000行
    """
    # 定义输入和输出文件路径
    input_file = 'python_methods.jsonl'
    output_file = 'positive.jsonl'
    
    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        
        # 初始化计数器
        line_count = 0
        extracted_count = 0
        
        # 读取前10000行
        while line_count < 10000:
            line = infile.readline()
            if not line:  # 文件结束
                break
            
            line_count += 1
            # 计算当前行所在的100行块
            block_number = (line_count - 1) // 100
            # 计算当前行在块内的位置
            position_in_block = (line_count - 1) % 100
            
            # 如果是块内的前10行，则写入输出文件
            if position_in_block < 10:
                outfile.write(line)
                extracted_count += 1
    
    print(f"处理完成! 共读取 {line_count} 行，提取了 {extracted_count} 行。")
    print(f"提取的数据已保存到 {output_file}")

if __name__ == "__main__":
    process_jsonl()    