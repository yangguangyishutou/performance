import matplotlib.pyplot as plt
import matplotlib
import os
import pandas as pd

'''
使用方式：运行文件，生成的文件位于主文件夹的error_reports文件夹下
'''

# 设置 Matplotlib 使用支持中文的字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
matplotlib.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 获取当前脚本的所在目录
script_dir = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(script_dir, "..", "sitp-data.xlsx")

# 生成的图表保存到 error_reports 目录
output_dir = os.path.join(script_dir, "..", "error_reports")
os.makedirs(output_dir, exist_ok=True)  # 确保目录存在

def load_and_filter_data(filename):
    """ 读取Excel文件并过滤数据 """
    df = pd.read_excel(filename)
    
    # 确保列名正确
    columns = ['项目名', '文件名', '总体错误代码', '总体错误类型', '方法名', '方法错误代码', '方法错误类型']
    df.columns = columns

    # 分割数据集
    df_overall = df[['文件名', '总体错误代码', '总体错误类型']].copy()
    df_method = df[['方法名', '方法错误代码', '方法错误类型']].copy()

    # 过滤无效值并转换类型
    df_overall = df_overall[df_overall['总体错误代码'] != -1]
    df_method = df_method[df_method['方法错误代码'] != -1]

    # 筛选出含有NaN或无效值的行
    df_overall = df_overall[~df_overall[['总体错误代码']].isna().any(axis=1)]
    
    df_overall['总体错误代码'] = df_overall['总体错误代码'].astype(int)
    df_method['方法错误代码'] = df_method['方法错误代码'].astype(int)

    return df_overall, df_method

def plot_error_distribution(df, error_column, include_zero=True, title_prefix=""):
    """ 绘制饼图和柱状图 """
    if include_zero:
        # 统计所有错误并合并
        df_copy = df.copy()
        df_copy[error_column] = df_copy[error_column].apply(lambda x: "正确" if x == 0 else '错误')
        filename_suffix = "正确率对比"
    else:
        df_copy = df[df[error_column] != 0]  # 只统计正确部分
        filename_suffix = "错误率对比"
    
    error_counts = df_copy[error_column].value_counts()

    error_counts_df = error_counts.reset_index()
    error_counts_df.columns = [error_column, '数量']  # 修改列名为 "错误类型" 和 "数量"

    error_counts_df.to_csv(os.path.join(output_dir, f"{title_prefix}_{filename_suffix}.csv"), index=False, encoding='utf-8')

    # 定义映射字典
    error_mapping = {
        1: "引用不存在的方法或成员变量",
        2: "参数表不匹配",
        3: "缺少头文件",
        4: "方法未实现(全部缺失)",
        6: "变量初始化/使用错误",
        8: "错误使用指针",
        9: "引用不存在的类",
        10: "方法部分未实现(部分缺失)",
        11: "内存管理不当"
    }

    df = pd.read_csv(os.path.join(output_dir, f"{title_prefix}_{filename_suffix}.csv"))

    for i in range(0, len(df)): 
        error_code = df.iloc[i, 0] 
        
        if error_code in error_mapping: 
            df.iloc[i, 0] = error_mapping[error_code]  # 替换为对应的字符串

    df.to_csv(os.path.join(output_dir, f"{title_prefix}_{filename_suffix}.csv"), index=False, encoding='utf-8')

    if error_counts.empty:
        print(f"⚠️ 警告：{title_prefix} {filename_suffix} 数据为空，跳过绘图。")
        return
    
    # ========== 绘制饼图 ==========
    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        error_counts, 
        labels=error_counts.index,
        autopct=lambda p: f'{p:.1f}%' if p >= 3 else '',
        startangle=140, 
        colors=plt.cm.Paired.colors
    )

    # 添加图例以防止标签重叠
    plt.legend(
        wedges, 
        [f"{idx} ({count})" for idx, count in zip(error_counts.index, error_counts)], 
        loc="lower left",  # 调整图例到左下角
        bbox_to_anchor=(-0.1, 0.1)  # 进一步调整，使其稍微偏移，避免重叠
    )
    plt.title(f"{title_prefix} {filename_suffix} - 饼图")
    plt.savefig(os.path.join(output_dir, f"{title_prefix}_{filename_suffix}_饼图.pdf"))
    
    # ========== 绘制柱状图 ==========
    plt.figure(figsize=(10, 6))
    bars = error_counts.plot(kind='bar', color='skyblue', edgecolor='black', width=0.6)
    
    for bar in bars.patches:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5, f'{int(bar.get_height())}', ha='center', va='bottom', fontsize=10, color='black')
    
    plt.xlabel("错误类型")
    plt.ylabel("数量")
    plt.title(f"{title_prefix} {filename_suffix} - 柱状图")
    plt.xticks(rotation=0)
    plt.savefig(os.path.join(output_dir, f"{title_prefix}_{filename_suffix}_柱状图.pdf"))

if __name__ == "__main__":
    df_overall, df_method = load_and_filter_data(data_file)
    
    # 合并所有错误代码用于总体分析
    combined_errors = pd.concat([
        df_overall['总体错误代码'].rename('所有错误代码'),
        df_method['方法错误代码'].rename('所有错误代码')
    ])
    combined_df = pd.DataFrame({'所有错误代码': combined_errors})

    # 1. 所有错误代码，包含正确部分
    plot_error_distribution(combined_df, "所有错误代码", include_zero=True, title_prefix="总体分析")
    
    # 2. 所有错误代码，不包含正确部分
    plot_error_distribution(combined_df, "所有错误代码", include_zero=False, title_prefix="总体分析")
    
    # 3. 仅包含总体错误代码，包含正确部分
    plot_error_distribution(df_overall, "总体错误代码", include_zero=True, title_prefix="文件整体错误分析")
    
    # 4. 仅包含总体错误代码，不包含正确部分
    plot_error_distribution(df_overall, "总体错误代码", include_zero=False, title_prefix="文件整体错误分析")
    
    # 5. 仅包含方法错误代码，包含正确部分
    plot_error_distribution(df_method, "方法错误代码", include_zero=True, title_prefix="方法错误分析")
    
    # 6. 仅包含方法错误代码，不包含正确部分
    plot_error_distribution(df_method, "方法错误代码", include_zero=False, title_prefix="方法错误分析")