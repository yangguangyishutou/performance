#!/usr/bin/env python3
"""
分析LLM翻译结果中的错误分布
回答以下研究问题：
RQ1: 翻译过程中出现的主要问题是什么？
RQ2: 这些问题的分布情况如何？
RQ3: File-level和Method-level翻译的性能对比？
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# 错误类型定义
ERROR_TYPES = {
    'Err_1': '引用不存在的方法或成员变量',
    'Err_2': '参数表不匹配',
    'Err_3': '缺少头文件',
    'Err_4': '方法未实现(全部缺失)',
    'Err_5': '代码逻辑/错误处理被简化',
    'Err_6': '变量初始化/使用错误',
    'Err_7': '逻辑/语义与原代码不符',
    'Err_8': '错误使用指针',
    'Err_9': '引用不存在的类',
    'Err_10': '方法部分未实现',
    'Err_11': '内存管理不当'
}

def load_data(filepath):
    """加载CSV数据并清理异常数据"""
    df = pd.read_csv(filepath)

    # 剔除Err_-1列（异常数据）
    if 'Err_-1' in df.columns:
        # 统计异常数据数量
        invalid_count = df['Err_-1'].notna().sum()
        if invalid_count > 0:
            print(f"警告: {filepath} 中发现 {invalid_count} 条异常数据(Err_-1)")

        # 剔除异常数据行
        df = df[df['Err_-1'].isna() | (df['Err_-1'] == '')]

    return df

def is_error_free(row):
    """判断是否无错误"""
    # 检查Err_0是否为None或空
    if pd.notna(row.get('Err_0')) and str(row['Err_0']).strip() not in ['', 'None']:
        return False

    # 检查Err_1到Err_11是否都为空
    for i in range(1, 12):
        col = f'Err_{i}'
        if pd.notna(row.get(col)) and str(row[col]).strip() not in ['', 'None']:
            return False

    return True

def classify_errors(row):
    """分类错误类型"""
    errors = []

    # 检查Err_1到Err_11
    for i in range(1, 12):
        col = f'Err_{i}'
        if pd.notna(row.get(col)) and str(row[col]).strip() not in ['', 'None']:
            errors.append(i)

    # 检查Err_0（未分类错误）
    if pd.notna(row.get('Err_0')) and str(row['Err_0']).strip() not in ['', 'None']:
        errors.append(0)

    return errors

def analyze_file(df, name):
    """分析单个数据文件"""
    print(f"\n{'='*80}")
    print(f"分析: {name}")
    print(f"{'='*80}")

    # 基本统计
    total_rows = len(df)
    error_free = sum(1 for _, row in df.iterrows() if is_error_free(row))
    has_errors = total_rows - error_free

    print(f"\n总条目数: {total_rows}")
    print(f"无错误: {error_free} ({error_free/total_rows*100:.1f}%)")
    print(f"有错误: {has_errors} ({has_errors/total_rows*100:.1f}%)")

    # 区分整体问题和方法级别问题
    method_level = df[df['Method'].notna() & (df['Method'] != '')]
    file_level = df[df['Method'].isna() | (df['Method'] == '')]

    print(f"\n方法级别条目: {len(method_level)}")
    print(f"文件级别条目: {len(file_level)}")

    # 统计各类错误数量
    error_counts = Counter()
    error_by_type = {i: 0 for i in range(12)}  # 0-11

    for _, row in df.iterrows():
        errors = classify_errors(row)
        for err in errors:
            error_by_type[err] += 1

    print(f"\n错误分布:")
    print("-" * 80)
    print(f"{'错误类型':<5} {'数量':<10} {'百分比':<10} {'描述'}")
    print("-" * 80)

    for err_type in [0] + list(range(1, 12)):
        count = error_by_type[err_type]
        pct = count / total_rows * 100 if total_rows > 0 else 0
        if err_type == 0:
            desc = "未分类错误"
        else:
            desc = ERROR_TYPES.get(f'Err_{err_type}', f'Err_{err_type}')

        print(f"Err_{err_type:<3} {count:<10} {pct:<10.1f}% {desc}")

    # 按项目统计
    print(f"\n按项目统计:")
    print("-" * 80)
    for project in df['Project'].unique():
        project_df = df[df['Project'] == project]
        p_total = len(project_df)
        p_errors = sum(1 for _, row in project_df.iterrows() if not is_error_free(row))
        p_error_rate = p_errors / p_total * 100 if p_total > 0 else 0
        print(f"{project:<30} 总数:{p_total:<5} 错误:{p_errors:<5} 错误率:{p_error_rate:.1f}%")

    return {
        'total': total_rows,
        'error_free': error_free,
        'has_errors': has_errors,
        'error_by_type': error_by_type,
        'method_level': len(method_level),
        'file_level': len(file_level)
    }

def compare_translations(class_stats, method_stats):
    """对比File-level和Method-level翻译"""
    print(f"\n{'='*80}")
    print("RQ3: File-level vs Method-level 翻译性能对比")
    print(f"{'='*80}")

    print(f"\n{'指标':<30} {'File-level':<20} {'Method-level':<20} {'差异'}")
    print("-" * 80)

    # 基本指标对比
    total_ratio = method_stats['total'] / class_stats['total'] if class_stats['total'] > 0 else 0

    metrics = [
        ('总条目数', class_stats['total'], method_stats['total']),
        ('无错误数量', class_stats['error_free'], method_stats['error_free']),
        ('错误数量', class_stats['has_errors'], method_stats['has_errors']),
    ]

    for name, class_val, method_val in metrics:
        diff = f"+{method_val - class_val}" if method_val >= class_val else str(method_val - class_val)
        print(f"{name:<30} {class_val:<20} {method_val:<20} {diff}")

    print("\n错误率对比:")
    class_error_rate = class_stats['has_errors'] / class_stats['total'] * 100
    method_error_rate = method_stats['has_errors'] / method_stats['total'] * 100
    print(f"File-level错误率:   {class_error_rate:.1f}%")
    print(f"Method-level错误率: {method_error_rate:.1f}%")
    print(f"差异: {method_error_rate - class_error_rate:+.1f}个百分点")

    # 各类错误对比
    print(f"\n各类错误数量对比:")
    print("-" * 80)
    print(f"{'错误类型':<30} {'File-level':<15} {'Method-level':<15} {'差异'}")
    print("-" * 80)

    for err_type in [0] + list(range(1, 12)):
        class_count = class_stats['error_by_type'][err_type]
        method_count = method_stats['error_by_type'][err_type]
        diff = method_count - class_count
        diff_str = f"{diff:+d}"

        if err_type == 0:
            desc = "未分类错误"
        else:
            desc = ERROR_TYPES.get(f'Err_{err_type}', f'Err_{err_type}')

        # 只显示有错误的类型
        if class_count > 0 or method_count > 0:
            print(f"{desc:<30} {class_count:<15} {method_count:<15} {diff_str}")

def generate_latex_tables(class_stats, method_stats, output_path):
    """生成LaTeX格式的表格"""
    latex_path = output_path / 'tables.tex'

    with open(latex_path, 'w', encoding='utf-8') as f:
        f.write("% 错误统计表格（自动生成）\n\n")

        # 表1: 总体对比
        f.write("\\begin{table}[h]\n")
        f.write("\\centering\n")
        f.write("\\caption{Translation Performance Comparison}\n")
        f.write("\\label{tab:performance-comparison}\n")
        f.write("\\begin{tabular}{lccc}\n")
        f.write("\\toprule\n")
        f.write("\\textbf{Metric} & \\textbf{File-level} & \\textbf{Method-level} & \\textbf{Difference} \\\\\\\\\n")
        f.write("\\midrule\n")

        total_items_class = class_stats['total']
        total_items_method = method_stats['total']

        error_rate_class = class_stats['has_errors'] / total_items_class * 100
        error_rate_method = method_stats['has_errors'] / total_items_method * 100

        f.write(f"Total Items & {total_items_class} & {total_items_method} & {total_items_method - total_items_class:+d} \\\\\\\\\n")
        f.write(f"Error-Free Items & {class_stats['error_free']} & {method_stats['error_free']} & {method_stats['error_free'] - class_stats['error_free']:+d} \\\\\\\\\n")
        f.write(f"Items with Errors & {class_stats['has_errors']} & {method_stats['has_errors']} & {method_stats['has_errors'] - class_stats['has_errors']:+d} \\\\\\\\\n")
        f.write(f"Error Rate (\\%) & {error_rate_class:.1f}\\% & {error_rate_method:.1f}\\% & {error_rate_method - error_rate_class:+.1f}pp \\\\\\\\\n")

        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n\n")

        # 表2: 错误类型分布
        f.write("\\begin{table}[h]\n")
        f.write("\\centering\n")
        f.write("\\caption{Error Type Distribution}\n")
        f.write("\\label{tab:error-distribution}\n")
        f.write("\\small\n")
        f.write("\\begin{tabular}{llcc}\n")
        f.write("\\toprule\n")
        f.write("\\textbf{Error Type} & \\textbf{Description} & \\textbf{File-level} & \\textbf{Method-level} \\\\\\\\\n")
        f.write("\\midrule\n")

        for err_type in [1] + list(range(2, 12)):
            class_count = class_stats['error_by_type'][err_type]
            method_count = method_stats['error_by_type'][err_type]

            if class_count == 0 and method_count == 0:
                continue

            desc = ERROR_TYPES.get(f'Err_{err_type}', f'Err_{err_type}')
            desc_short = desc[:40]  # 限制长度
            f.write(f"Err_{err_type} & {desc_short} & {class_count} & {method_count} \\\\\\\\\n")

        f.write("\\bottomrule\n")
        f.write("\\end{tabular}\n")
        f.write("\\end{table}\n\n")

    print(f"\nLaTeX表格已生成: {latex_path}")

def generate_plots(class_stats, method_stats, output_path):
    """生成可视化图表"""
    import pathlib
    output_path = pathlib.Path(output_path)

    # 图1: 总体性能对比
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # 子图1: 错误率对比
    ax1 = axes[0]
    methods = ['File-level', 'Method-level']
    error_rates = [
        class_stats['has_errors'] / class_stats['total'] * 100,
        method_stats['has_errors'] / method_stats['total'] * 100
    ]
    bars = ax1.bar(methods, error_rates, color=['#3498db', '#e74c3c'], alpha=0.8)
    ax1.set_ylabel('Error Rate (%)', fontsize=12)
    ax1.set_title('Translation Error Rate Comparison', fontsize=14, fontweight='bold')
    ax1.set_ylim(0, 100)

    # 添加数值标签
    for bar, rate in zip(bars, error_rates):
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{rate:.1f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

    # 子图2: 各类错误数量对比
    ax2 = axes[1]
    error_types = []
    class_counts = []
    method_counts = []

    for err_type in range(1, 12):
        class_count = class_stats['error_by_type'][err_type]
        method_count = method_stats['error_by_type'][err_type]
        if class_count > 0 or method_count > 0:
            error_types.append(f'Err_{err_type}')
            class_counts.append(class_count)
            method_counts.append(method_count)

    x = np.arange(len(error_types))
    width = 0.35

    bars1 = ax2.bar(x - width/2, class_counts, width, label='File-level', color='#3498db', alpha=0.8)
    bars2 = ax2.bar(x + width/2, method_counts, width, label='Method-level', color='#e74c3c', alpha=0.8)

    ax2.set_xlabel('Error Type', fontsize=12)
    ax2.set_ylabel('Count', fontsize=12)
    ax2.set_title('Error Type Distribution', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(error_types, rotation=45, ha='right')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    plot1_path = output_path / 'comparison.png'
    plt.savefig(plot1_path, dpi=300, bbox_inches='tight')
    print(f"\n图表已生成: {plot1_path}")
    plt.close()

def main():
    """主函数"""
    import pathlib
    data_dir = pathlib.Path(__file__).parent

    # 加载数据
    class_file = data_dir / 'sitp-data-class-deepseek.csv'
    method_file = data_dir / 'sitp-data-method-deepseek.csv'

    print("加载数据...")
    class_df = load_data(class_file)
    method_df = load_data(method_file)

    # 分析File-level翻译
    class_stats = analyze_file(class_df, "File-level Translation (sitp-data-class-deepseek.csv)")

    # 分析Method-level翻译
    method_stats = analyze_file(method_df, "Method-level Translation (sitp-data-method-deepseek.csv)")

    # 对比分析
    compare_translations(class_stats, method_stats)

    # 生成LaTeX表格
    generate_latex_tables(class_stats, method_stats, data_dir)

    # 生成图表
    generate_plots(class_stats, method_stats, data_dir)

    print(f"\n{'='*80}")
    print("分析完成！")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()
