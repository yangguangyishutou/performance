from huggingface_hub import HfApi

api = HfApi()

authors = ['THUDM', 'meta-llama', 'Qwen', 'tencent', 'openai-community', 'bigscience', 'google']

# HF 列举的 NPL 任务
tasks = [
    "text-classification",
    "token-classification",
    "table-question-answering",
    "question-answering",
    "zero-shot-classification",
    "translation",
    "summarization",
    "feature-extraction",
    "text-generation",
    "text2text-generation",
    "fill-mask",
    "sentence-similarity",
    "text-ranking"
]

output_file = "./models.txt"
cnt = 0

with open(output_file, "w") as f:
    for task in tasks:
        for author in authors:
            models = api.list_models(author=author, task=task, sort='likes', limit=100)
            for model in models:
                model_id = model.id
                # print(model_id)
                f.write(model_id + "\n")
                cnt = cnt + 1

print(f"Model list saved to {output_file} with {cnt} records")
