import matplotlib.pyplot as plt

# --- 数据定义 ---
# 错误分类数据
error_labels = ['Model Copy', 'Not Fine-Tuning', 'Base Model Error']
error_sizes = [14, 13, 2]
error_title = 'Error Types'

# 定义颜色主题（蓝色调）
colors_blue_shades = ['#4a90e2', '#7fb3d5', '#b0c4de'] 
center_bg_color = '#f4f8fb'

# --- 绘图函数 ---
def draw_donut_on_ax(ax, labels, sizes, title, colors, center_color):
    """
    在指定的 Axes(子图) 上绘制单个环形饼图。
    """
    # 确保颜色列表长度足够
    actual_colors = colors * (len(sizes) // len(colors)) + colors[:len(sizes) % len(colors)]

    # 绘制饼图
    wedges, texts, autotexts = ax.pie(
        sizes,
        autopct='%1.1f%%',
        startangle=90,
        colors=actual_colors,
        pctdistance=0.85,
        wedgeprops=dict(width=0.4, edgecolor='w')
    )

    # 添加中心圆，使其成为环形图
    center_circle = plt.Circle((0, 0), 0.58, fc=center_color)
    ax.add_artist(center_circle)

    # 设置百分比文本样式
    plt.setp(autotexts, size=16, weight="bold", color="white")

    # 在中心添加标题 (调整了字体大小以适应单图)
    ax.text(0, 0, title, ha='center', va='center', fontsize=24, fontweight='bold')

    # 设置图例
    legend = ax.legend(
        wedges, labels,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.05),  # 将图例放在图表正下方
        ncol=len(labels)  # 水平排列
    )
    plt.setp(legend.get_texts(), fontsize=16, weight='bold')

# --- 主绘图逻辑 ---

# 1. 创建包含 1 个子图的画布
fig, ax = plt.subplots(figsize=(8, 8))

# 2. 在子图上绘制错误分类环形图
draw_donut_on_ax(
    ax=ax, 
    labels=error_labels, 
    sizes=error_sizes, 
    title=error_title, 
    colors=colors_blue_shades, 
    center_color=center_bg_color
)

# 3. 调整整体布局以防止标题和图例被截断
fig.tight_layout(pad=3.0) 

# 4. 保存为 PDF 文件（适用于论文插入）
plt.savefig('fig/hf_error_pie.pdf', format='pdf', bbox_inches='tight')

# 关闭图形，释放内存
plt.close(fig)