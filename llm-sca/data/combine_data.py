import json
json_files = ['model_pair_adapter.json', 'model_pair_finetune.json', 'model_pair_merge.json', 'model_pair_quantized.json']

output_path = 'model_pair.jsonl'

# 清空 output file
with open(output_path, 'w', encoding='utf-8') as f:
    pass

for file in json_files:
    with open(output_path, 'a', encoding='utf-8') as of:
        with open(file, 'r', encoding='utf-8') as f:
            pairs = json.load(f)
            for pair in pairs:
                line = json.dumps(pair, ensure_ascii=False)
                of.write(line + '\n')