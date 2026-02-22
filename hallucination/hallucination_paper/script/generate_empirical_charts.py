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
df_errors = pd.read_csv("data/empirical_error_distribution.csv")
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
df_errors['model'] = df_errors['ai_name'].map(model_names)

# ===================================================================
# Chart 1: Overall Success Rate by Model and Strategy (RQ1)
# ===================================================================
fig, ax = plt.subplots(figsize=(10, 6))

# Group by model and strategy
grouped = df_data.groupby(['model', 'strategy'])['success_rate'].mean().reset_index()
pivot_data = grouped.pivot(index='model', columns='strategy', values='success_rate')

x = np.arange(len(pivot_data.index))
width = 0.35

bars1 = ax.bar(x - width/2, pivot_data['class'], width, label='File-by-file', color='#3498db', alpha=0.8)
bars2 = ax.bar(x + width/2, pivot_data['method'], width, label='Method-by-method', color='#e74c3c', alpha=0.8)

ax.set_xlabel('Model', fontsize=12, fontweight='bold')
ax.set_ylabel('Compilation Success Rate (%)', fontsize=12, fontweight='bold')
ax.set_title('RQ1: Translation Effectiveness by Model and Segmentation Strategy', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(pivot_data.index)
ax.legend(loc='upper right')
ax.grid(axis='y', alpha=0.3)

# Add value labels on bars
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}%', ha='center', va='bottom', fontsize=10)

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'empirical_success_rate.pdf', dpi=300, bbox_inches='tight')
plt.savefig(FIGURE_DIR / 'empirical_success_rate.png', dpi=300, bbox_inches='tight')
print("✓ Generated: empirical_success_rate.pdf/png")

# ===================================================================
# Chart 2: Success Rate by Project (RQ1)
# ===================================================================
fig, ax = plt.subplots(figsize=(12, 6))

projects = df_data['translation_unit'].unique()
models = df_data['model'].unique()
strategies = df_data['strategy'].unique()

x = np.arange(len(projects))
width = 0.13
bar_positions = np.arange(len(projects))

colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6']
bars_list = []

for i, (model, strategy) in enumerate([(m, s) for m in models for s in strategies]):
    data_subset = df_data[(df_data['model'] == model) & (df_data['strategy'] == strategy)]
    rates = [data_subset[data_subset['translation_unit'] == p]['success_rate'].values[0]
             if p in data_subset['translation_unit'].values else 0
             for p in projects]

    offset = (i - len(models)*len(strategies)/2 + 0.5) * width
    bars = ax.bar(bar_positions + offset, rates, width,
                  label=f'{model}\n({strategy})',
                  alpha=0.8, color=colors[i % len(colors)])
    bars_list.append(bars)

ax.set_xlabel('Translation Unit (Project)', fontsize=12, fontweight='bold')
ax.set_ylabel('Compilation Success Rate (%)', fontsize=12, fontweight='bold')
ax.set_title('RQ1: Success Rate Across Different Projects', fontsize=14, fontweight='bold')
ax.set_xticks(bar_positions)
ax.set_xticklabels([f'{p}\n({df_source[df_source["translation_unit"]==p]["domain"].values[0]})'
                    for p in projects], fontsize=9)
ax.legend(loc='upper right', fontsize=8, ncol=2)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'empirical_success_by_project.pdf', dpi=300, bbox_inches='tight')
plt.savefig(FIGURE_DIR / 'empirical_success_by_project.png', dpi=300, bbox_inches='tight')
print("✓ Generated: empirical_success_by_project.pdf/png")

# ===================================================================
# Chart 3: Error Type Heatmap (RQ2)
# ===================================================================
# Aggregate error rates by model and strategy
error_cols = [col for col in df_errors.columns if col not in
              ['translate_unit', 'ai_name', 'strategy', 'model']]

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

# ===================================================================
# Chart 4: Stacked Error Distribution by Configuration (RQ2)
# ===================================================================
# Aggregate error data
stacked_data = df_errors.groupby(['model', 'strategy'])[error_cols].mean().reset_index()
stacked_data['config'] = stacked_data['model'] + ' (' + stacked_data['strategy'].replace({
    'class': 'file-by-file',
    'method': 'method-by-method'
}) + ')'

# Select top 8 error types for clarity and group others
stacked_data_plot = stacked_data.set_index('config')[error_cols]
stacked_data_plot.columns = [error_labels.get(col, col) for col in stacked_data_plot.columns]

fig, ax = plt.subplots(figsize=(12, 6))

stacked_data_plot.plot(kind='bar', stacked=True, ax=ax, colormap='tab20')
ax.set_xlabel('Model (Strategy)', fontsize=12, fontweight='bold')
ax.set_ylabel('Percentage of Methods with Error', fontsize=12, fontweight='bold')
ax.set_title('RQ2: Error Type Distribution by Configuration', fontsize=14, fontweight='bold')
ax.legend(title='Error Type', bbox_to_anchor=(1.05, 1), loc='upper left')
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'empirical_error_stacked.pdf', dpi=300, bbox_inches='tight')
plt.savefig(FIGURE_DIR / 'empirical_error_stacked.png', dpi=300, bbox_inches='tight')
print("✓ Generated: empirical_error_stacked.pdf/png")

# ===================================================================
# Chart 5: Error Type Occurrence Rate by Configuration (RQ2)
# ===================================================================
# Aggregate error data by model and strategy
error_by_config = df_errors.groupby(['model', 'strategy'])[error_cols].mean().reset_index()

# Create configuration labels
error_by_config['config'] = error_by_config['model'] + ' (' + error_by_config['strategy'].replace({
    'class': 'file-by-file',
    'method': 'method-by-method'
}) + ')'

# Melt the data for grouped bar plot
error_melted = error_by_config.melt(
    id_vars=['config'],
    value_vars=error_cols,
    var_name='error_type',
    value_name='occurrence_rate'
)

# Convert to percentage
error_melted['occurrence_rate'] = error_melted['occurrence_rate'] * 100

# Create short error labels
error_melted['error_label'] = error_melted['error_type'].map(error_labels)

# Sort by error type for better visualization
error_order = error_melted.groupby('error_label')['occurrence_rate'].mean().sort_values(ascending=False).index
error_melted['error_label'] = pd.Categorical(error_melted['error_label'], categories=error_order, ordered=True)

fig, ax = plt.subplots(figsize=(14, 7))

# Create grouped bar plot
sns.barplot(
    data=error_melted,
    x='error_label',
    y='occurrence_rate',
    hue='config',
    palette='tab10',
    ax=ax
)

ax.set_xlabel('Error Type', fontsize=12, fontweight='bold')
ax.set_ylabel('Percentage of Methods with Error (%)', fontsize=12, fontweight='bold')
ax.set_title('RQ2: Error Type Occurrence Rate by Model and Strategy', fontsize=14, fontweight='bold')
ax.legend(title='Configuration', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax.grid(axis='y', alpha=0.3)

# Rotate x labels for better readability
plt.xticks(rotation=45, ha='right')

# Add value labels on top of bars (only for values > 5% to avoid clutter)
for container in ax.containers:
    ax.bar_label(container, fmt='%.1f%%', fontsize=7, padding=2)

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'empirical_error_by_type.pdf', dpi=300, bbox_inches='tight')
plt.savefig(FIGURE_DIR / 'empirical_error_by_type.png', dpi=300, bbox_inches='tight')
print("✓ Generated: empirical_error_by_type.pdf/png")

# ===================================================================
# Chart 5b: Horizontal Bar Chart Version
# ===================================================================
fig, ax = plt.subplots(figsize=(12, 8))

# Create horizontal bar plot
sns.barplot(
    data=error_melted,
    y='error_label',
    x='occurrence_rate',
    hue='config',
    palette='tab10',
    ax=ax
)

ax.set_xlabel('Percentage of Methods with Error (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Error Type', fontsize=12, fontweight='bold')
ax.set_title('RQ2: Error Type Occurrence Rate by Model and Strategy (Horizontal)', fontsize=14, fontweight='bold')
ax.legend(title='Configuration', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax.grid(axis='x', alpha=0.3)

# Add value labels at the end of bars
for container in ax.containers:
    ax.bar_label(container, fmt='%.1f%%', fontsize=7, padding=3)

plt.tight_layout()
plt.savefig(FIGURE_DIR / 'empirical_error_by_type_horizontal.pdf', dpi=300, bbox_inches='tight')
plt.savefig(FIGURE_DIR / 'empirical_error_by_type_horizontal.png', dpi=300, bbox_inches='tight')
print("✓ Generated: empirical_error_by_type_horizontal.pdf/png")

# ===================================================================
# Print Summary Statistics
# ===================================================================
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

print("\n--- Top Error Types Across All Configurations ---")
error_summary = df_errors[error_cols].mean().sort_values(ascending=False)
for err_type, rate in error_summary.head(6).items():
    label = error_labels.get(err_type, err_type)
    print(f"{label}: {rate:.3f} errors/file")

print("\n" + "="*60)
print("All charts generated successfully!")
print("="*60)
