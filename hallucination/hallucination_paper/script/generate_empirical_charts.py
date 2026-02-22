"""
Generate charts for the empirical study chapter.
"""

import sys
from pathlib import Path

project_dir = Path(__file__).parent.parent
if str(project_dir) not in sys.path:
    sys.path.append(str(project_dir))

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Set style for academic papers
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.dpi'] = 300
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['savefig.bbox'] = 'tight'
plt.rcParams['axes.unicode_minus'] = False

# Data paths
DATA_DIR = project_dir / "data"
FIGURES_DIR = project_dir / "figures"

def load_data():
    """Load all empirical data."""
    df_data = pd.read_csv(DATA_DIR / "empirical_data.csv")
    df_error = pd.read_csv(DATA_DIR / "empirical_error_distribution.csv")
    df_source = pd.read_csv(DATA_DIR / "empirical_source.csv")

    return df_data, df_error, df_source

def calculate_success_rate(df):
    """Calculate success rates."""
    df['success_rate'] = df['success_file_count'] / df['total_cpp_count']
    return df

def create_success_rate_bar_chart(df, output_path):
    """Create bar chart comparing success rates across models and strategies."""
    df = calculate_success_rate(df)

    # Group by model and strategy, calculate mean success rate
    summary = df.groupby(['ai_name', 'strategy']).agg({
        'success_file_count': 'sum',
        'total_cpp_count': 'sum'
    }).reset_index()
    summary['success_rate'] = summary['success_file_count'] / summary['total_cpp_count']

    # Rename models for display
    model_names = {
        'deepseek-v3.2': 'DeepSeek-V3.2',
        'qwen-3.5plus': 'Qwen-3.5Plus',
        'ChatGPT-5.1': 'ChatGPT-5.1'
    }
    summary['ai_name_display'] = summary['ai_name'].map(model_names)

    strategy_names = {
        'class': 'File-by-File',
        'method': 'Method-by-Method'
    }
    summary['strategy_display'] = summary['strategy'].map(strategy_names)

    # Create figure
    fig, ax = plt.subplots(figsize=(7, 4.5))

    models = summary['ai_name_display'].unique()
    strategies = summary['strategy_display'].unique()

    x = np.arange(len(models))
    width = 0.35

    colors = ['#4472C4', '#ED7D31']

    for i, strategy in enumerate(strategies):
        data = summary[summary['strategy_display'] == strategy]['success_rate'].values
        offset = (i - 0.5) * width
        ax.bar(x + offset, data, width, label=strategy, color=colors[i])

    ax.set_xlabel('Model', fontweight='bold')
    ax.set_ylabel('Success Rate', fontweight='bold')
    ax.set_title('Translation Success Rates by Model and Strategy', fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.legend(loc='upper right')
    ax.set_ylim(0, 0.3)

    # Add value labels on bars
    for i, strategy in enumerate(strategies):
        data = summary[summary['strategy_display'] == strategy]['success_rate'].values
        offset = (i - 0.5) * width
        for j, val in enumerate(data):
            ax.text(j + offset, val + 0.005, f'{val:.2%}',
                   ha='center', va='bottom', fontsize=8)

    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    print(f"Saved: {output_path}")
    plt.close()

def create_success_rate_by_project(df, df_source, output_path):
    """Create grouped bar chart showing success rates by project."""
    df = calculate_success_rate(df)
    df = df.merge(df_source, on='translation_unit')

    # Rename models and strategies for display
    model_names = {
        'deepseek-v3.2': 'DeepSeek-V3.2',
        'qwen-3.5plus': 'Qwen-3.5Plus',
        'ChatGPT-5.1': 'ChatGPT-5.1'
    }
    df['ai_name_display'] = df['ai_name'].map(model_names)

    strategy_names = {
        'class': 'File-by-File',
        'method': 'Method-by-Method'
    }
    df['strategy_display'] = df['strategy'].map(strategy_names)

    # Create figure with subplots for each model
    models = df['ai_name_display'].unique()
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.5), sharey=True)

    projects = df['translation_unit'].unique()
    strategies = df['strategy_display'].unique()

    for idx, model in enumerate(models):
        ax = axes[idx]
        model_data = df[df['ai_name_display'] == model]

        x = np.arange(len(projects))
        width = 0.35

        for i, strategy in enumerate(strategies):
            data = []
            for proj in projects:
                proj_data = model_data[(model_data['translation_unit'] == proj) &
                                     (model_data['strategy_display'] == strategy)]
                if not proj_data.empty:
                    data.append(proj_data['success_rate'].values[0])
                else:
                    data.append(0)

            offset = (i - 0.5) * width
            ax.bar(x + offset, data, width, label=strategy, color=['#4472C4', '#ED7D31'][i])

        ax.set_xlabel('Project', fontweight='bold')
        ax.set_ylabel('Success Rate' if idx == 0 else '', fontweight='bold')
        ax.set_title(model, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([p[:15] for p in projects], rotation=15, ha='right')
        ax.set_ylim(0, 0.6)

        if idx == 2:
            ax.legend(loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    print(f"Saved: {output_path}")
    plt.close()

def create_error_distribution_heatmap(df_error, output_path):
    """Create heatmap showing error distribution."""
    # Load error type descriptions
    error_types_path = DATA_DIR / "empirical_error_types.txt"
    with open(error_types_path, 'r') as f:
        error_type_lines = f.readlines()

    error_type_labels = {}
    for line in error_type_lines:
        if ':' in line:
            num, desc = line.strip().split(':', 1)
            short_name = desc.split(':')[0].strip()
            error_type_labels[short_name] = desc

    # Aggregate error data across all projects for each model and strategy
    error_cols = [col for col in df_error.columns if col not in
                  ['translate_unit', 'ai_name', 'strategy']]

    summary = df_error.groupby(['ai_name', 'strategy'])[error_cols].mean().reset_index()

    # Rename for display
    model_names = {
        'deepseek-v3.2': 'DeepSeek',
        'qwen-3.5plus': 'Qwen',
        'ChatGPT-5.1': 'ChatGPT'
    }
    summary['model_display'] = summary['ai_name'].map(model_names)
    summary['strategy_display'] = summary['strategy'].map({
        'class': 'File', 'method': 'Method'
    })

    # Create labels
    summary['label'] = summary['model_display'] + '\n(' + summary['strategy_display'] + ')'

    # Select top error types
    error_means = summary[error_cols].mean()
    top_errors = error_means.nlargest(6).index.tolist()

    plot_data = summary.set_index('label')[top_errors] * 100  # Convert to percentage

    # Create figure
    fig, ax = plt.subplots(figsize=(9, 4))

    sns.heatmap(plot_data, annot=True, fmt='.1f', cmap='YlOrRd',
                cbar_kws={'label': 'Error Rate (%)'},
                linewidths=0.5, ax=ax)

    ax.set_xlabel('Error Type', fontweight='bold')
    ax.set_ylabel('Model (Strategy)', fontweight='bold')
    ax.set_title('Distribution of Common Error Types', fontweight='bold')

    # Shorten error type labels
    short_labels = {
        'TYPE_SYSTEM_ERROR': 'Type System',
        'MISSING_UNDEFINED_SYMBOLS': 'Missing/Undef. Symbols',
        'BUILD_INCLUDE_ERROR': 'Build/Include',
        'SYNTAX_LANGUAGE_ERROR': 'Syntax/Language',
        'REDEFINITION_ERROR': 'Redefinition',
        'DECLARE_DEFINITION_MISMATCH': 'Decl/Def Mismatch'
    }
    ax.set_xticklabels([short_labels.get(col, col) for col in top_errors])

    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    print(f"Saved: {output_path}")
    plt.close()

def create_error_distribution_stacked(df_error, df_source, output_path):
    """Create stacked bar chart of error distribution by project."""
    error_cols = [col for col in df_error.columns if col not in
                  ['translate_unit', 'ai_name', 'strategy']]

    # Merge with source info
    df_merged = df_error.merge(df_source,
                               left_on='translate_unit',
                               right_on='translation_unit',
                               how='left')

    # Aggregate by model and strategy
    summary = df_merged.groupby(['ai_name', 'strategy'])[error_cols].mean().reset_index()

    # Rename for display
    model_names = {
        'deepseek-v3.2': 'DeepSeek-V3.2',
        'qwen-3.5plus': 'Qwen-3.5Plus',
        'ChatGPT-5.1': 'ChatGPT-5.1'
    }
    summary['model_display'] = summary['ai_name'].map(model_names)
    summary['strategy_display'] = summary['strategy'].map({
        'class': 'File-by-File',
        'method': 'Method-by-Method'
    })

    # Select top error types for visualization
    error_means = summary[error_cols].mean()
    top_errors = error_means.nlargest(5).index.tolist()

    # Create figure
    fig, axes = plt.subplots(1, 3, figsize=(14, 3.5), sharey=True)

    models = summary['model_display'].unique()
    colors = plt.cm.Set3(range(len(top_errors)))

    for idx, model in enumerate(models):
        ax = axes[idx]
        model_data = summary[summary['model_display'] == model]

        strategies = model_data['strategy_display'].values
        x = np.arange(len(strategies))
        bottom = np.zeros(len(strategies))

        for i, error_type in enumerate(top_errors):
            values = model_data[error_type].values * 100
            ax.bar(x, values, bottom=bottom, label=error_type.replace('_', ' '),
                   color=colors[i], edgecolor='white', linewidth=0.5)
            bottom += values

        ax.set_xlabel('Translation Strategy', fontweight='bold')
        ax.set_ylabel('Error Rate (%)' if idx == 0 else '', fontweight='bold')
        ax.set_title(model, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(strategies, rotation=15, ha='right')

        if idx == 2:
            ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left',
                     fontsize=7, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path, format='pdf')
    print(f"Saved: {output_path}")
    plt.close()

def main():
    """Main function to generate all charts."""
    print("Loading data...")
    df_data, df_error, df_source = load_data()

    print("\nGenerating charts...")

    # 1. Success rate comparison chart
    print("\n1. Success rate bar chart...")
    create_success_rate_bar_chart(
        df_data,
        FIGURES_DIR / "empirical_success_rate.pdf"
    )

    # 2. Success rate by project
    print("\n2. Success rate by project...")
    create_success_rate_by_project(
        df_data,
        df_source,
        FIGURES_DIR / "empirical_success_by_project.pdf"
    )

    # 3. Error distribution heatmap
    print("\n3. Error distribution heatmap...")
    create_error_distribution_heatmap(
        df_error,
        FIGURES_DIR / "empirical_error_heatmap.pdf"
    )

    # 4. Error distribution stacked bar
    print("\n4. Error distribution stacked bar...")
    create_error_distribution_stacked(
        df_error,
        df_source,
        FIGURES_DIR / "empirical_error_stacked.pdf"
    )

    print("\nAll charts generated successfully!")

if __name__ == "__main__":
    main()
