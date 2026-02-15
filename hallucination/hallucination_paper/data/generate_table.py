import pandas as pd

import pandas as pd
import numpy as np

def df_to_latex_basic(df, caption=None, label=None, escape=True):
    """
    将pandas DataFrame转换为LaTeX表格字符串
    
    Parameters:
    -----------
    df : pandas.DataFrame
        要转换的数据框
    caption : str, optional
        表格标题
    label : str, optional
        表格标签，用于引用
    escape : bool, default=True
        是否转义特殊字符（如_ % &等）
    
    Returns:
    --------
    str : LaTeX表格字符串
    """
    
    # 处理特殊字符
    if escape:
        df = df.applymap(lambda x: str(x).replace('_', r'\_').replace('%', r'\%')
                         .replace('&', r'\&').replace('#', r'\#')
                         .replace('$', r'\$').replace('{', r'\{')
                         .replace('}', r'\}'))
    
    # 开始构建LaTeX表格
    latex_str = []
    
    # 表格环境开始
    latex_str.append(r'\begin{table}[htbp]')
    latex_str.append(r'\centering')
    
    # 确定列格式
    n_cols = len(df.columns)
    col_format = 'l' * n_cols  # 全部左对齐
    latex_str.append(r'\begin{tabular}{' + col_format + '}')
    latex_str.append(r'\toprule')
    
    # 表头
    header = ' & '.join(df.columns) + r' \\'
    latex_str.append(header)
    latex_str.append(r'\midrule')
    
    # 数据行
    for _, row in df.iterrows():
        row_str = ' & '.join(row.astype(str)) + r' \\'
        latex_str.append(row_str)
    
    # 表格结束
    latex_str.append(r'\bottomrule')
    latex_str.append(r'\end{tabular}')
    
    # 标题和标签
    if caption:
        latex_str.append(r'\caption{' + caption + '}')
    if label:
        latex_str.append(r'\label{' + label + '}')
    
    latex_str.append(r'\end{table}')
    
    return '\n'.join(latex_str)


# 使用示例
if __name__ == "__main__":
    # 创建示例数据
    data = {
        'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
        'Age': [25, 30, 35, 28],
        'Score': [85.5, 92.3, 78.9, 88.7],
        'Grade': ['A', 'A+', 'B+', 'A']
    }
    df = pd.DataFrame(data)
    
    latex_code = df_to_latex_basic(df, caption="学生成绩表", label="tab:scores")
    print(latex_code)

