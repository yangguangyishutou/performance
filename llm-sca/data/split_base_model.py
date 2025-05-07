import os
import argparse

def split_file(input_file, num_parts):
    # 读取所有模型行
    with open(input_file, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]

    total = len(lines)
    part_size = total // num_parts
    remainder = total % num_parts

    print(f"Total models: {total}")
    print(f"Splitting into {num_parts} parts: {part_size} each, with {remainder} extra lines to distribute.")

    for i in range(num_parts):
        # 计算每份的起始和结束下标
        start_idx = i * part_size + min(i, remainder)
        end_idx = start_idx + part_size + (1 if i < remainder else 0)
        part_lines = lines[start_idx:end_idx]

        output_file = f"{os.path.splitext(input_file)[0]}_part_{i+1}.txt"
        with open(output_file, 'w') as f_out:
            for line in part_lines:
                f_out.write(line + '\n')
        print(f"Written {len(part_lines)} lines to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Split a text file into N approximately equal parts.")
    parser.add_argument("--input", type=str, default="base_models.txt", help="Path to input txt file")
    parser.add_argument("--parts", type=int, default=5, help="Number of parts to split into")

    args = parser.parse_args()
    split_file(args.input, args.parts)
