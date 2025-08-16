import json

INPUT_DATA_FILE = "./model_pairs.json"
OUTPUT_REPORT = "./model_pairs_without_error.json"
REF_FILE = "./model_validation_report.json"

with open(REF_FILE, 'r', encoding='utf-8') as f:
    ref_data = json.load(f)

ref_data = ref_data['results']
ref_models = [item['model'] for item in ref_data if item['error']]

with open(INPUT_DATA_FILE, 'r', encoding='utf-8') as f:
    input_data = json.load(f)

output_data = []
cnt = 0

for item in input_data:
    if item['model'] in ref_models:
        cnt += 1
        continue
    output_data.append(item)

with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
    json.dump(output_data, f, indent=4, ensure_ascii=False)

print(f'Filtered {cnt} models with errors. Output saved to {OUTPUT_REPORT}. Remaining models: {len(output_data)}.')
# Filtered 321 models with errors. Output saved to ./model_pairs_without_error.json. Remaining models: 4390.
