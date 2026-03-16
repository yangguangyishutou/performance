import json

def process_jsonl(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f_in, open(output_file, 'w', encoding='utf-8') as f_out:
        for line in f_in:
            data = json.loads(line)
            processed_data = {
                'function': data.get('function'),
                'label': data.get('label')
            }
            f_out.write(json.dumps(processed_data) + '\n')

if __name__ == "__main__":
    input_file = 'negative_raw.jsonl'
    output_file = 'negative.jsonl'
    process_jsonl(input_file, output_file)    