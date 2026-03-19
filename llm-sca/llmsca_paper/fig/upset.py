import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from upsetplot import UpSet
import itertools

# 1. 生成所有基础模块及其组合
layers = ['Q', 'K', 'V', 'O', 'MLP']
all_combinations = []
for r in range(1, len(layers) + 1):
    for combo in itertools.combinations(layers, r):
        # 保持元组形式，方便后续做布尔值匹配
        all_combinations.append(combo)

# 2. 准备数据（硬编码准确率数据，方便填入真实实验数据）
# 格式：组合元组 -> 准确率值
# 示例数据，请替换为你的真实实验结果
accuracy_dict = {
    ('Q',): 75,
    ('K',): 80,
    ('V',): 72,
    ('O',): 70,
    ('MLP',): 68,
    ('Q', 'K'): 82,
    ('Q', 'V'): 78,
    ('Q', 'O'): 76,
    ('Q', 'MLP'): 74,
    ('K', 'V'): 85,
    ('K', 'O'): 83,
    ('K', 'MLP'): 81,
    ('V', 'O'): 79,
    ('V', 'MLP'): 77,
    ('O', 'MLP'): 75,
    ('Q', 'K', 'V'): 88,
    ('Q', 'K', 'O'): 86,
    ('Q', 'K', 'MLP'): 84,
    ('Q', 'V', 'O'): 82,
    ('Q', 'V', 'MLP'): 80,
    ('Q', 'O', 'MLP'): 78,
    ('K', 'V', 'O'): 87,
    ('K', 'V', 'MLP'): 85,
    ('K', 'O', 'MLP'): 83,
    ('V', 'O', 'MLP'): 81,
    ('Q', 'K', 'V', 'O'): 89,
    ('Q', 'K', 'V', 'MLP'): 87,
    ('Q', 'K', 'O', 'MLP'): 85,
    ('Q', 'V', 'O', 'MLP'): 83,
    ('K', 'V', 'O', 'MLP'): 88,
    ('Q', 'K', 'V', 'O', 'MLP'): 90,
}

# 根据组合获取准确率，如果字典中没有则使用默认值（便于调试）
accuracies = [accuracy_dict.get(combo, 0) for combo in all_combinations]

# 3. 构建 UpSetPlot 所需的布尔值多重索引 (Boolean MultiIndex) 数据格式
# UpSetPlot 的核心要求是：每一列代表一个模块(True/False)，最后加上我们要展示的指标(Accuracy)
data_rows = []
min_accuracy = min(accuracies) if accuracies else 0
# 根据最小准确率，自动计算一个更接近最小值的 y 轴起点
# 这里按 5 的步长向下取整，例如 68 -> 65，既减少空白又不过于拥挤
y_min = max(0, (min_accuracy // 5) * 5)
for i, combo in enumerate(all_combinations):
    # 如果该模块在当前组合中，则为 True，否则为 False
    row = {layer: (layer in combo) for layer in layers}
    row['Accuracy'] = accuracies[i]
    data_rows.append(row)

df = pd.DataFrame(data_rows)

# 将所有的模块列设置为索引 (MultiIndex)
df_indexed = df.set_index(layers)

# 4. 绘制 UpSet Plot
plt.figure(figsize=(12, 8))

# 核心参数解释：
# - df_indexed['Accuracy']: 传入带有多重布尔索引的 Series
# - subset_size='sum': 默认 UpSet 会统计每个组合出现的次数(都是1)。
#   改为 'sum' 后，它会对传入的 Accuracy 求和（因为每个组合只有1条数据，求和也就是 Accuracy 本身），从而让上方柱状图直接显示准确率。
# - sort_by='cardinality': 按照 Accuracy 的大小从高到低对柱子进行排序，最直观。
upset = UpSet(df_indexed['Accuracy'], 
              subset_size='sum', 
              show_counts='%d%%', # 在柱子上显示具体数值 (百分比格式)
              sort_by='cardinality', 
              facecolor='#4c72b0', # 柱子和点的颜色
              element_size=40, # 柱子和点的尺寸
              totals_plot_elements=0,
              with_lines=False
              )

# 渲染图形
upset.plot()

plt.ylabel('Accuracy (%)')

# 调整纵坐标范围，从计算得到的 y_min 开始，以减少冗余空白
current_ylim = plt.ylim()
plt.ylim(y_min, current_ylim[1])

plt.savefig('fig/rq2_upset.pdf', bbox_inches='tight', format='pdf')
print("UpSet Plot 已成功保存为 rq2_upset.pdf")