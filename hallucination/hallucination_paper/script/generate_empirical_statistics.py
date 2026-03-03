"""
Generate empirical study statistics for LLM-based code translation paper.
This script calculates detailed statistics from CSV data for the ch03-empirical section.
"""
import pandas as pd
import numpy as np

# Load data
df_data = pd.read_csv('data/empirical_data.csv')
df_errors_method = pd.read_csv('data/empirical_error_distribution_method.csv')
df_errors_class = pd.read_csv('data/empirical_ereror_distribution_class.csv')

# Calculate success rate
df_data['success_rate'] = (df_data['success_file_count'] / df_data['total_cpp_count']) * 100

print('=' * 60)
print('OVERALL SUCCESS RATE BY MODEL AND STRATEGY')
print('=' * 60)
grouped = df_data.groupby(['ai_name', 'strategy'])['success_rate'].mean()
print(grouped)

print()
print('=' * 60)
print('SUCCESS RATE BY PROJECT')
print('=' * 60)
for unit in df_data['translation_unit'].unique():
    subset = df_data[df_data['translation_unit'] == unit]
    for strategy in ['class', 'method']:
        sub = subset[subset['strategy'] == strategy]
        if len(sub) > 0:
            avg_rate = sub['success_rate'].mean()
            print(f'{unit} ({strategy}): {avg_rate:.1f}%')

print()
print('=' * 60)
print('ERROR DISTRIBUTION (METHOD LEVEL) - PERCENTAGE')
print('=' * 60)
error_cols = ['SYNTAX_LANGUAGE_ERROR', 'TYPE_SYSTEM_ERROR', 'DECLARE_DEFINITION_MISMATCH',
              'MISSING_UNDEFINED_SYMBOLS', 'INHERITANCE_VIRTUAL_ERROR', 'CONSTRUCTOR_DESTRUCTOR_ERROR',
              'TEMPLATE_ERROR', 'ACCESS_SCOPE_ERROR', 'REDEFINITION_ERROR', 'BUILD_INCLUDE_ERROR', 'OTHER_ERROR']

# Calculate percentage of methods with each error type
df_errors_method_norm = df_errors_method.copy()
for col in error_cols:
    df_errors_method_norm[col] = df_errors_method_norm[col] / df_errors_method_norm['method_count'] * 100

error_by_type = df_errors_method_norm[error_cols].mean().sort_values(ascending=False)
for err, rate in error_by_type.items():
    print(f'{err}: {rate:.2f}%')

print()
print('=' * 60)
print('ERROR DISTRIBUTION (CLASS LEVEL) - PERCENTAGE')
print('=' * 60)
# Calculate percentage of files with each error type
df_errors_class_norm = df_errors_class.copy()
for col in error_cols:
    df_errors_class_norm[col] = df_errors_class_norm[col] / df_errors_class_norm['file_count'] * 100

error_by_type_class = df_errors_class_norm[error_cols].mean().sort_values(ascending=False)
for err, rate in error_by_type_class.items():
    print(f'{err}: {rate:.2f}%')

print()
print('=' * 60)
print('ERROR DISTRIBUTION BY MODEL AND STRATEGY (METHOD LEVEL)')
print('=' * 60)
error_summary = df_errors_method_norm.groupby(['ai_name', 'strategy'])[error_cols].mean()
print(error_summary)

print()
print('=' * 60)
print('TOTAL METHODS AND FILES')
print('=' * 60)
total_methods = df_errors_method['method_count'].sum()
total_files = df_errors_class['file_count'].sum()
print(f'Total methods analyzed: {total_methods}')
print(f'Total files analyzed: {total_files}')

print()
print('=' * 60)
print('DETAILED: Success Rate by Model/Strategy (Overall)')
print('=' * 60)
models = ['deepseek-v3.2', 'qwen-3.5plus', 'ChatGPT-5.1']
for model in models:
    for strategy in ['class', 'method']:
        sub = df_data[(df_data['ai_name'] == model) & (df_data['strategy'] == strategy)]
        total_files = sub['total_cpp_count'].sum()
        success_files = sub['success_file_count'].sum()
        rate = (success_files / total_files) * 100 if total_files > 0 else 0
        print(f'{model} ({strategy}): {rate:.1f}% ({success_files}/{total_files})')

print()
print('=' * 60)
print('ERROR DISTRIBUTION BY MODEL AND STRATEGY (DETAILED)')
print('=' * 60)
for model in models:
    for strategy in ['class', 'method']:
        sub = df_errors_method_norm[df_errors_method_norm['ai_name'] == model]
        sub = sub[sub['strategy'] == strategy]
        if len(sub) > 0:
            avg_errors = sub[error_cols].mean()
            print(f'\n{model} - {strategy}:')
            for err in error_cols:
                if avg_errors[err] > 0.5:
                    print(f'  {err}: {avg_errors[err]:.1f}%')

print()
print('=' * 60)
print('SUMMARY FOR LATEX TABLE')
print('=' * 60)
print('Method-Level Top 3 Error Types by Model and Strategy:')
print()
print(r'\begin{tabular}{lcccc}')
print(r'\toprule')
print(r'\textbf{Model} & \textbf{Strategy} & \textbf{Missing Symbols (\%)} & \textbf{Type System (\%)} & \textbf{Build/Include (\%)} \\')
print(r'\midrule')
for model in models:
    for strategy in ['class', 'method']:
        sub = df_errors_method_norm[df_errors_method_norm['ai_name'] == model]
        sub = sub[sub['strategy'] == strategy]
        if len(sub) > 0:
            avg_errors = sub[error_cols].mean()
            model_display = model.replace('deepseek-v3.2', 'DeepSeek-V3.2').replace('qwen-3.5plus', 'Qwen-3.5Plus').replace('ChatGPT-5.1', 'ChatGPT-5.1')
            strategy_display = 'File-by-file' if strategy == 'class' else 'Method-by-method'
            missing = avg_errors['MISSING_UNDEFINED_SYMBOLS']
            typesys = avg_errors['TYPE_SYSTEM_ERROR']
            buildinc = avg_errors['BUILD_INCLUDE_ERROR']
            buildinc_str = f'{buildinc:.1f}' if buildinc > 0 else '--'
            print(f'{model_display} & {strategy_display} & {missing:.1f} & {typesys:.1f} & {buildinc_str} \\\\')
print(r'\bottomrule')
print(r'\end{tabular}')
