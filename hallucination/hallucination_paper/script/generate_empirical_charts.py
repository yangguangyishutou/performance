"""
Generate empirical study charts for LLM-based code translation paper.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path

# Set style and parameters
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")
FIGURE_DIR = Path("figures")
FIGURE_DIR.mkdir(exist_ok=True)

# Load data
df_data = pd.read_csv("data/empirical_data.csv")
df_errors_method = pd.read_csv("data/empirical_error_distribution_method.csv")
df_errors_class = pd.read_csv("data/empirical_ereror_distribution_class.csv")
df_source = pd.read_csv("data/empirical_source.csv")

# Calculate success rate
df_data['success_rate'] = (df_data['success_file_count'] / df_data['total_cpp_count']) * 100

# Create readable model names
model_names = {
    'deepseek-v3.2': 'DeepSeek-V3.2',
    'qwen-3.5plus': 'Qwen-3.5Plus',
    'ChatGPT-5.1': 'ChatGPT-5.1'
}
df_data['model'] = df_data['ai_name'].map(model_names)
# For backward compatibility, use method-level errors as primary
df_errors = df_errors_method
# print(df_errors.columns)
df_errors['model'] = df_errors['ai_name'].map(model_names)
df_errors_class['model'] = df_errors_class['ai_name'].map(model_names)

# Convert error counts to percentages (rate per method/file)
error_type_cols = df_errors_method.columns.tolist()
# 移除 translate_unit,ai_name,strategy,method_count
for col in ['translate_unit', 'ai_name', 'strategy', 'method_count', 'all', "model", 'Other Errors']:
    error_type_cols.remove(col)

# Convert method-level errors to percentage of methods with error
for col in error_type_cols:
    df_errors[col] = df_errors[col] / df_errors['method_count'] * 100

# Convert class-level errors to percentage of files with error
for col in error_type_cols:
    df_errors_class[col] = df_errors_class[col] / df_errors_class['file_count'] * 100

XY_LABEL_SIZE = 28
FONT = 'Times New Roman'
LEGEND_SIZE = 20
XY_TICK_SIZE = 20
VAL_LABEL_SIZE = 19
BAR_ALPHA = 0.8

# Set font for all text elements
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
plt.rcParams['font.size'] = 12


# ===================================================================
# Chart 1: Overall Success Rate by Model and Strategy (RQ1)
# ===================================================================
if False:
    fig, ax = plt.subplots(figsize=(10, 6))

    # Group by model and strategy
    grouped = df_data.groupby(['model', 'strategy'])['success_rate'].mean().reset_index()
    pivot_data = grouped.pivot(index='model', columns='strategy', values='success_rate')

    x = np.arange(len(pivot_data.index))
    width = 0.30

    bars1 = ax.bar(x - width/2, pivot_data['class'], width, label='File-by-file', color='#4A7298', alpha=BAR_ALPHA)
    bars2 = ax.bar(x + width/2, pivot_data['method'], width, label='Method-by-method', color='#F3C846', alpha=BAR_ALPHA)  

    ax.set_xlabel('', fontsize=18, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel('Compilation Success Rate (%)', fontsize=XY_LABEL_SIZE, fontweight='bold', fontfamily=FONT)
    ax.set_xticks(x)
    ax.set_xticks(np.arange(-0.5, len(x), 0.5), minor=True)
    ax.set_xticklabels(pivot_data.index, fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.legend(loc='upper left', fontsize=LEGEND_SIZE, prop={'family': FONT, 'size': LEGEND_SIZE})
    # Add more grid lines
    ax.grid(True, axis='x', which='minor', alpha=0.3, color='gray')
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)

    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=VAL_LABEL_SIZE, fontfamily=FONT)

    plt.tight_layout()
    plt.savefig(FIGURE_DIR / 'empirical' / 'success_rate' / 'overall.pdf', dpi=300, bbox_inches='tight')
    # plt.savefig(FIGURE_DIR / 'empirical_success_rate.png', dpi=300, bbox_inches='tight')
    print("✓ Generated: empirical/success_rate/overall.pdf/png")

# ===================================================================
# Chart 2: Success Rate by Project (RQ1)
# ===================================================================
# Generate chart for class strategy
# File-by-file Strategy Chart
if False:
    fig, ax1 = plt.subplots(figsize=(10, 6))

    projects = ['Cookie','EnableJUnit4MigrationSupport','CircuitBreakerExecutor']
    models = df_data['model'].unique()

    # Professional color scheme (blues and grays)
    colors = ['#AC2124', '#ECB426', '#416594']

    width = 0.25
    bar_positions = np.arange(len(projects))

    for i, model in enumerate(models):
        data_subset = df_data[(df_data['model'] == model) & (df_data['strategy'] == 'class')]
        rates = [data_subset[data_subset['translation_unit'] == p]['success_rate'].values[0]
                if p in data_subset['translation_unit'].values else 0
                for p in projects]

        offset = (i - len(models)/2 + 0.5) * width
        bars = ax1.bar(bar_positions + offset, rates, width,
                    label=f'{model}', color=colors[i % len(colors)], alpha=BAR_ALPHA)

    ax1.set_xlabel('', fontsize=18, fontweight='bold', fontfamily=FONT)
    ax1.set_ylabel('Compilation Success Rate (%)', fontsize=XY_LABEL_SIZE, fontweight='bold', fontfamily=FONT)
    ax1.set_xticks(bar_positions)
    ax1.set_xticks(np.arange(0.5, len(projects) -0.5, 0.5), minor=True)
    ax1.set_xticklabels([p.replace('EnableJUnit4MigrationSupport', 'EnableJUnit4-\nMigrationSupport') for p in projects], fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax1.grid(True, axis='x', which='minor', alpha=0.3, color='gray')
    ax1.legend(loc='upper left', fontsize=LEGEND_SIZE, prop={'family': FONT, 'size': LEGEND_SIZE})
    ax1.set_yticks(np.arange(0, 101, 10))
    ax1.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax1.set_ylim(0, 100)
    
    # Add value labels on bars
    for bars in ax1.containers:
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=VAL_LABEL_SIZE, fontfamily=FONT)

    plt.tight_layout()
    plt.savefig(FIGURE_DIR / 'empirical' / 'success_rate' / 'by_project-class.pdf', dpi=300, bbox_inches='tight')
    # plt.savefig(FIGURE_DIR / 'empirical_success_by_project_class.png', dpi=300, bbox_inches='tight')
    print("✓ Generated: empirical/success_rate/by_project-class.pdf/png")
    plt.close()

    # Method-by-method Strategy Chart
    fig, ax2 = plt.subplots(figsize=(10, 6))

    for i, model in enumerate(models):
        data_subset = df_data[(df_data['model'] == model) & (df_data['strategy'] == 'method')]
        rates = [data_subset[data_subset['translation_unit'] == p]['success_rate'].values[0]
                if p in data_subset['translation_unit'].values else 0
                for p in projects]

        offset = (i - len(models)/2 + 0.5) * width
        bars = ax2.bar(bar_positions + offset, rates, width,
                    label=f'{model}', color=colors[i % len(colors)], alpha=BAR_ALPHA)

    ax2.set_xlabel('', fontsize=18, fontweight='bold', fontfamily=FONT)
    ax2.set_ylabel('Compilation Success Rate (%)', fontsize=XY_LABEL_SIZE, fontweight='bold', fontfamily=FONT)
    ax2.set_xticks(bar_positions)
    ax2.set_xticks(np.arange(0.5, len(projects) -0.5, 0.5), minor=True)
    ax2.set_xticklabels([p.replace('EnableJUnit4MigrationSupport', 'EnableJUnit4-\nMigrationSupport') for p in projects], fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax2.grid(True, axis='x', which='minor', alpha=0.3, color='gray')
    ax2.legend(loc='upper left', fontsize=LEGEND_SIZE, prop={'family': FONT, 'size': LEGEND_SIZE})
    ax2.grid(axis='y', alpha=0.3)
    ax2.set_yticks(np.arange(0, 101, 10))
    ax2.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax2.set_ylim(0, 100)
    
    # Add value labels on bars
    for bars in ax2.containers:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom', fontsize=VAL_LABEL_SIZE, fontfamily=FONT)

    plt.tight_layout()
    plt.savefig(FIGURE_DIR / 'empirical' / 'success_rate' / 'by_project-method.pdf', dpi=300, bbox_inches='tight')
    # plt.savefig(FIGURE_DIR / 'empirical_success_by_project_method.png', dpi=300, bbox_inches='tight')
    print("✓ Generated: empirical/success_rate/by_project-method.pdf/png")
    plt.close()

# ===================================================================
# Chart 3: Error Type Occurrence Rate by Configuration (RQ2)
# ===================================================================
# 定义错误类型短标签
error_labels = {
    "Language Syntax Violation": "Syntax",
    "Type Error": "Type System",
    "Declaration Mismatch": "Decl/Def Mismatch",
    "Undefined Symbols": "Undefined Symbols",
    "Duplicated Definitions": "Duplicated Definitions",
    "Header File Error": "Header File Error",
}
color_list = ["#4A7298", "#F3C846"]

# Helper function to process error data
def process_error_data(df, error_type_cols, error_labels):
    # Aggregate error data by strategy, averaging across models
    error_by_config = df.groupby(['strategy'])[error_type_cols].mean().reset_index()

    # Create configuration labels
    error_by_config['config'] = error_by_config['strategy'].replace({
        'class': 'file-by-file',
        'method': 'method-by-method'
    })

    # Melt the data for grouped bar plot
    error_melted = error_by_config.melt(
        id_vars=['config'],
        value_vars=error_type_cols,
        var_name='error_type',
        value_name='occurrence_rate'
    )

    # Create short error labels
    error_melted['error_label'] = error_melted['error_type'].map(error_labels)

    # Sort by error type for better visualization
    error_order = error_melted.groupby('error_label')['occurrence_rate'].mean().sort_values(ascending=False).index
    error_melted['error_label'] = pd.Categorical(error_melted['error_label'], categories=error_order, ordered=True)
    
    return error_melted, error_order

# Helper function to create vertical bar chart
def create_vertical_chart(data, error_order, y_label, output_path, color_list):
    fig, ax = plt.subplots(figsize=(14, 7))

    # Create grouped bar plot
    sns.barplot(
        data=data,
        x='error_label',
        y='occurrence_rate',
        hue='config',
        palette=color_list,
        alpha=BAR_ALPHA,
        ax=ax
    )

    ax.set_xlabel('', fontsize=12, fontweight='bold')
    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_xticklabels(error_order, fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.set_ylabel(y_label, fontsize=XY_LABEL_SIZE, fontweight='bold')
    ax.legend(loc='upper right', fontsize=LEGEND_SIZE)
    ax.grid(axis='y', alpha=0.3)

    # Rotate x labels for better readability
    plt.xticks(rotation=45, ha='right')

    # Add value labels on top of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', fontsize=VAL_LABEL_SIZE, padding=2)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Generated: {output_path}")
    plt.close()

# Helper function to create horizontal bar chart
def create_horizontal_chart(data, error_order, x_label, output_path, color_list):
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create horizontal bar plot
    sns.barplot(
        data=data,
        y='error_label',
        x='occurrence_rate',
        hue='config',
        palette=color_list,
        alpha=BAR_ALPHA,
        ax=ax
    )

    ax.set_xlabel(x_label, fontsize=XY_LABEL_SIZE, fontweight='bold')
    ax.set_ylabel('', fontsize=XY_LABEL_SIZE, fontweight='bold')
    ax.set_yticklabels(error_order, fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.set_xticks(np.arange(0, 101, 10))
    ax.set_xticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.legend( loc='lower right', fontsize=LEGEND_SIZE)
    ax.grid(axis='x', alpha=0.3)

    # Add value labels at the end of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', fontsize=VAL_LABEL_SIZE, padding=3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Generated: {output_path}")
    plt.close()

if True:
    overall_data = pd.read_csv('data/error_overall_statistics.csv')
    overall_data['level'] = overall_data['level'].map({'class': 'intra-class', 'method': 'intra-method'})
    
    # Melt the data for horizontal bar chart
    melted = overall_data.melt(
        id_vars=['level'],
        value_vars=['Language Syntax Violation', 'Type Error', 'Declaration Mismatch', 
                   'Undefined Symbols', 'Duplicated Definitions', 'Header File Error'],
        var_name='error_type',
        value_name='count'
    )
    
    # Calculate total errors for percentage
    total_errors = melted['count'].sum()
    melted['occurrence_rate'] = (melted['count'] / total_errors) * 100
    
    # Create short error labels
    melted['error_label'] = melted['error_type'].map(error_labels)
    
    # Sort by error count for better visualization
    col_sums = overall_data[['Language Syntax Violation', 'Type Error', 'Declaration Mismatch', 
                           'Undefined Symbols', 'Duplicated Definitions', 'Header File Error']].sum()
    sorted_error_order = col_sums.sort_values(ascending=False).index
    error_order = [error_labels[err] for err in sorted_error_order]
    
    # Set error_label as categorical with correct order
    melted['error_label'] = pd.Categorical(melted['error_label'], categories=error_order, ordered=True)
    
    # Create horizontal bar chart
    fig, ax = plt.subplots(figsize=(12, 8))

    # Create grouped bar plot
    sns.barplot(
        data=melted,
        y='error_label',
        x='occurrence_rate',
        hue='level',
        palette=color_list,
        alpha=BAR_ALPHA,
        ax=ax
    )

    ax.set_xlabel('Percentage of Errors (%)', fontsize=XY_LABEL_SIZE, fontweight='bold', fontfamily=FONT)
    ax.set_ylabel('', fontsize=XY_LABEL_SIZE, fontweight='bold')
    # Use get_yticklabels() to maintain correct order
    ax.tick_params(axis='y', labelsize=XY_TICK_SIZE, labelfontfamily=FONT)
    ax.set_xticks(np.arange(0, 31, 10))
    ax.set_xticklabels(np.arange(0, 31, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
    ax.legend(title='', loc='lower right', fontsize=LEGEND_SIZE)
    ax.grid(axis='x', alpha=0.3)

    # Add value labels at the end of bars
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f%%', fontsize=VAL_LABEL_SIZE, padding=3)

    plt.tight_layout()
    output_path = FIGURE_DIR / 'empirical' / 'error_analysis' / 'overall_distribution.pdf'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ Generated: {output_path}")
    plt.close()
    
    # create_vertical_chart(
    #     error_melted, 
    #     error_order, 
    #     'Percentage of Methods with Error (%)',
    #     FIGURE_DIR / 'empirical' / 'error_analysis' / 'method_level_distribution1.pdf',
    #     color_list
    # )
    
    # create_horizontal_chart(
    #     error_melted, 
    #     error_order, 
    #     'Percentage of Methods with Error (%)',
    #     FIGURE_DIR / 'empirical' / 'error_analysis' / 'method_level_distribution2.pdf',
    #     color_list
    # )
    
    # # Class-level charts
    # error_melted_class, error_order_class = process_error_data(df_errors_class, error_type_cols, error_labels)
    
    # create_vertical_chart(
    #     error_melted_class, 
    #     error_order_class, 
    #     'Percentage of Files with Error (%)',
    #     FIGURE_DIR / 'empirical' / 'error_analysis' / 'class_level_distribution1.pdf',
    #     color_list
    # )
    
    # create_horizontal_chart(
    #     error_melted_class, 
    #     error_order_class, 
    #     'Percentage of Files with Error (%)',
    #     FIGURE_DIR / 'empirical' / 'error_analysis' / 'class_level_distribution2.pdf',
    #     color_list
    # )

# ===================================================================
# Chart 3: Error Type Heatmap (RQ2)
# ===================================================================
if False:
    # Aggregate error rates by model and strategy
    error_cols = [col for col in df_errors.columns if col not in
                ['translate_unit', 'ai_name', 'strategy', 'model', 'method_count']]

    heatmap_data = df_errors.groupby(['model', 'strategy'])[error_cols].mean().reset_index()

    # Create combined label
    heatmap_data['config'] = heatmap_data['model'] + '\n(' + heatmap_data['strategy'].replace({'class': 'file-by-file',
        'method': 'method-by-method'}) + ')'

    # Reorder and prepare data
    heatmap_matrix = heatmap_data.set_index('config')[error_cols].T

    # Shorten error type names for display
    error_labels = {
        'SYNTAX_LANGUAGE_ERROR': 'Syntax',
        'TYPE_SYSTEM_ERROR': 'Type System',
        'DECLARE_DEFINITION_MISMATCH': 'Decl/Def Mismatch',
        'MISSING_UNDEFINED_SYMBOLS': 'Missing Symbols',
        'INHERITANCE_VIRTUAL_ERROR': 'Inheritance/Virtual',
        'CONSTRUCTOR_DESTRUCTOR_ERROR': 'Constructor/Destructor',
        'TEMPLATE_ERROR': 'Template',
        'ACCESS_SCOPE_ERROR': 'Access Scope',
        'REDEFINITION_ERROR': 'Redefinition',
        'BUILD_INCLUDE_ERROR': 'Build/Include',
        'OTHER_ERROR': 'Other'
    }

    heatmap_matrix.index = [error_labels.get(col, col) for col in heatmap_matrix.index]

    fig, ax = plt.subplots(figsize=(12, 8))

    sns.heatmap(heatmap_matrix, annot=True, fmt='.3f', cmap='YlOrRd',
                cbar_kws={'label': 'Percentage of Methods with Error'},
                linewidths=0.5, ax=ax)

    ax.set_title('RQ2: Error Type Distribution Across Models and Strategies', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model (Strategy)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Error Type', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURE_DIR / 'empirical_error_heatmap.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(FIGURE_DIR / 'empirical_error_heatmap.png', dpi=300, bbox_inches='tight')
    print("✓ Generated: empirical_error_heatmap.pdf/png")

    error_cols_class = [col for col in df_errors_class.columns if col not in
                    ['translate_unit', 'ai_name', 'strategy', 'model', 'file_count']]



    heatmap_data_class = df_errors_class.groupby(['model', 'strategy'])[error_cols_class].mean().reset_index()

    # Create combined label
    heatmap_data_class['config'] = heatmap_data_class['model'] + '\n(' + heatmap_data_class['strategy'].replace({'class': 'file-by-file',
        'method': 'method-by-method'}) + ')'

    # Reorder and prepare data
    heatmap_matrix_class = heatmap_data_class.set_index('config')[error_cols_class].T

    # Use same error labels
    heatmap_matrix_class.index = [error_labels.get(col, col) for col in heatmap_matrix_class.index]

    fig, ax = plt.subplots(figsize=(12, 8))

    sns.heatmap(heatmap_matrix_class, annot=True, fmt='.3f', cmap='YlOrRd',
                cbar_kws={'label': 'Percentage of Files with Error'},
                linewidths=0.5, ax=ax)

    ax.set_title('RQ2: Class-Level Error Type Distribution Across Models and Strategies', fontsize=14, fontweight='bold')
    ax.set_xlabel('Model (Strategy)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Error Type', fontsize=12, fontweight='bold')

    plt.tight_layout()
    plt.savefig(FIGURE_DIR / 'empirical_error_heatmap_class.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(FIGURE_DIR / 'empirical_error_heatmap_class.png', dpi=300, bbox_inches='tight')
    print("✓ Generated: empirical_error_heatmap_class.pdf/png")

# ===================================================================
# Chart 4: Stacked Error Distribution by Strategy (RQ2)  (class_level & method_level)
# ===================================================================
if False:
    # Load new error stack statistics data
    df_stack = pd.read_csv("data/error_stack_statistics.csv")
    
    # Define custom color scheme for error types
    error_colors = {
        'Syntax': '#CF7E9D',
        'Type System': '#CBBBC1',     
        'Decl/Def Mismatch': '#BD4146', 
        'Undefined Symbols': '#ECC68C', 
        'Duplicated Definitions': '#E4B7BC',
        'Header File Error': '#F5E4C8' 
    }
    
    # Define error type mappings
    error_type_mapping = {
        'Language Syntax Violation': 'Syntax',
        'Type Error': 'Type System',
        'Declaration Mismatch': 'Decl/Def Mismatch',
        'Undefined Symbols': 'Undefined Symbols',
        'Duplicated Definitions': 'Duplicated Definitions',
        'Header File Error': 'Header File Error'
    }
    
    # Process and create stacked charts for each strategy
    for strategy in df_stack['strategy'].unique():
        strategy_name = 'file-by-file' if strategy == 'class' else 'method-by-method'
        strategy_data = df_stack[df_stack['strategy'] == strategy]
        
        # Create combined ai_name and level categories
        strategy_data['ai_level'] = strategy_data['ai_name'] + ' (' + strategy_data['level'] + ')'
        
        # Melt for stacked chart
        melted = strategy_data.melt(
            id_vars=['ai_level'],
            value_vars=['Language Syntax Violation', 'Type Error', 'Declaration Mismatch', 
                       'Undefined Symbols', 'Duplicated Definitions', 'Header File Error'],
            var_name='error_type',
            value_name='rate'
        )
        
        # Convert to percentage and create short labels
        melted['rate'] = melted['rate'] * 100
        melted['error_label'] = melted['error_type'].map(error_type_mapping)
        
        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(16, 7))
        
        # Pivot for stacked plot
        pivot_data = melted.pivot(index='ai_level', columns='error_label', values='rate')
        pivot_data = pivot_data[list(error_colors.keys())]  # Ensure correct order
        
        pivot_data.plot(kind='bar', stacked=True, ax=ax, color=[error_colors[col] for col in pivot_data.columns])
        
        ax.set_xlabel('', fontsize=XY_LABEL_SIZE, fontweight='bold', fontfamily=FONT)
        ax.set_ylabel('Percentage of Errors (%)', fontsize=XY_LABEL_SIZE, fontweight='bold', fontfamily=FONT)
        # Remove chart title
        # ax.set_title(f'Error Distribution by Type - {strategy_name} Strategy', fontsize=XY_LABEL_SIZE + 2, fontweight='bold', fontfamily=FONT)
        # Move legend to top with three columns, no title
        ax.legend(loc='upper center', ncol=3, fontsize=LEGEND_SIZE, frameon=False)
        ax.grid(axis='y', alpha=0.3)
        ax.set_yticks(np.arange(0, 101, 10))
        ax.set_yticklabels(np.arange(0, 101, 10), fontsize=XY_TICK_SIZE, fontfamily=FONT)
        # Create two-line x-axis labels with level on first line
        ax.set_xticklabels(
            [label.split(' (')[1].replace(')', '').replace('class','intr-class').replace('method','intr-method') for label in pivot_data.index],
            fontsize=XY_TICK_SIZE, 
            fontfamily=FONT, 
            rotation=0, 
            ha='center'
        )
        
        # Add curly braces to group by ai_name using loop
        plt.subplots_adjust(bottom=0.2)
        
        # Define groups with their positions and names
        groups = [
            {'name': 'ChatGPT-5.1', 'start': 0, 'end': 1},
            {'name': 'deepseek-v3.2', 'start': 2, 'end': 3},
            {'name': 'qwen-3.5plus', 'start': 4, 'end': 5}
        ]
        
        # Loop through groups to add labels and braces
        for group in groups:
            # Calculate center position for group label
            center = (group['start'] + group['end']) / 2
            # Add group name label
            ax.text(center, -0.15, group['name'], transform=ax.get_xaxis_transform(),
                    ha='center', va='top', fontsize=XY_TICK_SIZE + 2, fontfamily=FONT, style='italic')
            # Add curly brace annotation
            ax.annotate('', xy=(group['start']-0.2, -0.1), xytext=(group['end']+0.2, -0.1),
                        xycoords=ax.get_xaxis_transform(),
                        arrowprops=dict(arrowstyle='|-|', color='black', linewidth=1.5, shrinkA=0, shrinkB=0))
        
        # Add value labels
        for p in ax.patches:
            width, height = p.get_width(), p.get_height()
            x, y = p.get_xy() 
            
            if height > 3:  # Only show labels for significant values
                ax.text(x + width/2, 
                        y + height/2,
                        f'{height:.1f}',
                        ha='center', 
                        va='center',
                        fontsize=VAL_LABEL_SIZE -5,
                        fontfamily=FONT)
        
        plt.tight_layout()
        output_path = FIGURE_DIR / 'empirical' / 'error_analysis' / f'stacked_error_distribution_{strategy}.pdf'
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"✓ Generated: {output_path}")
        plt.close()

# ===================================================================
# Print Summary Statistics
# ===================================================================
if False:
    print("\n" + "="*60)
    print("EMPIRICAL STUDY SUMMARY")
    print("="*60)

    print("\n--- Overall Success Rate by Model and Strategy ---")
    summary = df_data.groupby(['model', 'strategy']).agg({
        'success_rate': ['mean', 'std'],
        'total_cpp_count': 'sum',
        'success_file_count': 'sum'
    }).round(2)
    print(summary)

    print("\n--- Success Rate by Project ---")
    project_summary = df_data.groupby('translation_unit').agg({
        'success_rate': ['mean', 'min', 'max']
    }).round(2)
    print(project_summary)

    print("\n--- Top Error Types (Method-Level) ---")
    error_summary_method = df_errors[error_type_cols].mean().sort_values(ascending=False)
    for err_type, rate in error_summary_method.head(6).items():
        label = error_labels.get(err_type, err_type)
        print(f"{label}: {rate:.3f}% of methods")

    print("\n--- Top Error Types (Class-Level) ---")
    error_summary_class = df_errors_class[error_type_cols].mean().sort_values(ascending=False)
    for err_type, rate in error_summary_class.head(6).items():
        label = error_labels.get(err_type, err_type)
        print(f"{label}: {rate:.3f}% of files")

    print("\n" + "="*60)
    print("All charts generated successfully!")
    print("="*60)
