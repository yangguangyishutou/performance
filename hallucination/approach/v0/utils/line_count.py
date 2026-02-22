#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import argparse
from datetime import datetime

def count_lines_in_file(file_path):
    """
    统计单个Java文件的代码行数
    返回: (总行数, 非空行数, 代码行数(不含注释和空行))
    """
    total_lines = 0
    non_empty_lines = 0
    code_lines = 0
    in_block_comment = False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                total_lines += 1
                stripped_line = line.strip()
                
                # 统计非空行
                if stripped_line:
                    non_empty_lines += 1
                
                # 处理块注释
                if not in_block_comment:
                    # 检查是否进入块注释
                    if stripped_line.startswith('/*'):
                        in_block_comment = True
                        # 检查是否在同一行结束
                        if '*/' in stripped_line[2:]:
                            in_block_comment = False
                        continue
                    # 检查单行注释
                    elif stripped_line.startswith('//'):
                        continue
                    # 空行不计入代码行
                    elif not stripped_line:
                        continue
                    else:
                        code_lines += 1
                else:
                    # 在块注释中，检查是否结束
                    if '*/' in stripped_line:
                        in_block_comment = False
                    continue
                    
    except UnicodeDecodeError:
        # 如果UTF-8解码失败，尝试使用系统默认编码
        try:
            with open(file_path, 'r', encoding='gbk') as file:
                for line in file:
                    total_lines += 1
                    if line.strip():
                        non_empty_lines += 1
                    if line.strip() and not line.strip().startswith('//') and not line.strip().startswith('/*'):
                        code_lines += 1
        except:
            print(f"警告: 无法读取文件 {file_path}，跳过")
            return 0, 0, 0
    except Exception as e:
        print(f"警告: 处理文件 {file_path} 时出错: {e}")
        return 0, 0, 0
        
    return total_lines, non_empty_lines, code_lines

def scan_java_files(root_dir, exclude_dirs=None):
    """
    扫描指定目录下的所有Java文件
    """
    if exclude_dirs is None:
        exclude_dirs = ['.git', '.svn', 'target', 'build', 'bin', 'out']
    
    java_files = []
    root_path = Path(root_dir)
    
    for file_path in root_path.rglob('*.java'):
        # 检查是否应该排除
        should_exclude = False
        for exclude_dir in exclude_dirs:
            if exclude_dir in str(file_path.parent).split(os.sep):
                should_exclude = True
                break
        
        if not should_exclude:
            java_files.append(file_path)
    
    return java_files

def format_number(num):
    """格式化数字输出"""
    return f"{num:,}"

def main():
    parser = argparse.ArgumentParser(description='统计Java文件的代码行数')
    parser.add_argument('directory', nargs='?', default='.', 
                       help='要扫描的目录路径 (默认: 当前目录)')
    parser.add_argument('--exclude', '-e', nargs='+', 
                       default=['.git', '.svn', 'target', 'build', 'bin', 'out'],
                       help='要排除的目录名 (默认: .git .svn target build bin out)')
    parser.add_argument('--sort', '-s', choices=['name', 'lines', 'code'], 
                       default='name', help='排序方式 (name: 按文件名, lines: 按总行数, code: 按代码行数)')
    parser.add_argument('--reverse', '-r', action='store_true', 
                       help='反向排序')
    
    args = parser.parse_args()
    
    root_dir = os.path.abspath(args.directory)
    if not os.path.exists(root_dir):
        print(f"错误: 目录 '{root_dir}' 不存在")
        sys.exit(1)
    
    print(f"正在扫描目录: {root_dir}")
    print(f"排除的目录: {', '.join(args.exclude)}")
    print("-" * 80)
    
    # 扫描Java文件
    java_files = scan_java_files(root_dir, args.exclude)
    
    if not java_files:
        print("未找到Java文件")
        return
    
    print(f"找到 {len(java_files)} 个Java文件")
    print()
    
    # 统计每个文件的行数
    results = []
    total_files = len(java_files)
    total_lines = 0
    total_non_empty = 0
    total_code_lines = 0
    
    for i, file_path in enumerate(java_files, 1):
        relative_path = file_path.relative_to(root_dir)
        
        # 显示进度
        print(f"\r正在处理: {i}/{total_files}", end='')
        
        lines, non_empty, code = count_lines_in_file(file_path)
        results.append((str(relative_path), lines, non_empty, code))
        
        total_lines += lines
        total_non_empty += non_empty
        total_code_lines += code
    
    print("\r" + " " * 50 + "\r", end='')  # 清除进度行
    
    # 排序
    if args.sort == 'name':
        results.sort(key=lambda x: x[0], reverse=args.reverse)
    elif args.sort == 'lines':
        results.sort(key=lambda x: x[1], reverse=not args.reverse)
    elif args.sort == 'code':
        results.sort(key=lambda x: x[3], reverse=not args.reverse)
    
    # 打印结果
    print("\nJava文件代码行数统计:")
    print("-" * 100)
    print(f"{'序号':<6} {'文件名':<60} {'总行数':>10} {'非空行':>10} {'代码行':>10}")
    print("-" * 100)
    
    for idx, (file_path, lines, non_empty, code) in enumerate(results, 1):
        # 截断过长的文件名
        display_path = file_path if len(file_path) <= 60 else "..." + file_path[-57:]
        print(f"{idx:<6} {display_path:<60} "
              f"{format_number(lines):>10} "
              f"{format_number(non_empty):>10} "
              f"{format_number(code):>10}")
    
    print("-" * 100)
    print(f"{'总计':<6} {'':<60} "
          f"{format_number(total_lines):>10} "
          f"{format_number(total_non_empty):>10} "
          f"{format_number(total_code_lines):>10}")
    
    # 计算平均值
    if total_files > 0:
        print(f"\n统计信息:")
        print(f"  平均每文件总行数: {format_number(total_lines // total_files)}")
        print(f"  平均每文件非空行: {format_number(total_non_empty // total_files)}")
        print(f"  平均每文件代码行: {format_number(total_code_lines // total_files)}")
        print(f"  代码行占比: {(total_code_lines/total_lines*100):.1f}%" if total_lines > 0 else "  代码行占比: 0%")

def save_results_to_file(results, total_stats, output_file):
    """将结果保存到文件"""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Java文件代码行数统计 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 100 + "\n")
        f.write(f"{'文件名':<70} {'总行数':>10} {'非空行':>10} {'代码行':>10}\n")
        f.write("-" * 100 + "\n")
        
        for file_path, lines, non_empty, code in results:
            f.write(f"{file_path:<70} {format_number(lines):>10} "
                   f"{format_number(non_empty):>10} {format_number(code):>10}\n")
        
        f.write("-" * 100 + "\n")
        f.write(f"{'总计':<70} {format_number(total_stats['total_lines']):>10} "
               f"{format_number(total_stats['total_non_empty']):>10} "
               f"{format_number(total_stats['total_code_lines']):>10}\n")

if __name__ == "__main__":
    main()