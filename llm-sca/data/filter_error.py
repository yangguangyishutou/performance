import json

INPUT_DATA_FILE = "./data/new/adjacent_pairs.jsonl"
OUTPUT_REPORT = "./data/new/adjacent_pairs_without_error.json"
REF_FILE = "./data/new/model_validation_report.json"

with open(REF_FILE, 'r', encoding='utf-8') as f:
    ref_data = json.load(f)

ref_data = ref_data['results']
err_ids = [item['id'] for item in ref_data if item['error']]

with open(INPUT_DATA_FILE, 'r', encoding='utf-8') as f:
    data = [json.loads(line) for line in f]

filter_data = [item for item in data if item['id'] not in err_ids]

with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
    f.write(json.dumps(filter_data, ensure_ascii=False, indent=2))

print(f'filtering {len(filter_data)} data')
# filtering 1598 datas