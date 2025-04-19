'''
As for base model about 10-20 is enough
We need 300-400 pairs, which means the number of each type is 75-100
each base model has 4-10 child models for each type
focusing on text generation tasks which is the most popular used for various downstream tasks by FT/Merging/...
sorted by likes
filtered by accessibility, child models' number, parameter number
'''
from huggingface_hub import HfApi

api = HfApi()

# authors = ['THUDM', 'meta-llama', 'Qwen', 'tencent', 'openai-community', 'bigscience', 'google', 'mistralai']

# HF 列举的 NPL 任务
tasks = [
    # "text-classification",
    # "token-classification",
    # "table-question-answering",
    # "question-answering",
    # "zero-shot-classification",
    # "translation",
    # "summarization",
    # "feature-extraction",
    "text-generation",
    # "text2text-generation",
    # "fill-mask",
    # "sentence-similarity",
    # "text-ranking"
]

output_file = "./models.txt"
cnt = 0

# with open(output_file, "w") as f:
#     for task in tasks:
#         for author in authors:
#             models = api.list_models(author=author, task=task, sort='likes', limit=100)
#             for model in models:
#                 model_id = model.id
#                 # print(model_id)
#                 f.write(model_id + "\n")
#                 cnt = cnt + 1

# print(f"Model list saved to {output_file} with {cnt} records")

for task in tasks:
    models = api.list_models(task=task, sort='likes', limit=30, gated=False)
    for model in models:
        print(model.id)

# Top 30
'''
deepseek-ai/DeepSeek-R1
bigscience/bloom
deepseek-ai/DeepSeek-V3
microsoft/phi-2
Qwen/QwQ-32B
openai-community/gpt2
deepseek-ai/DeepSeek-V3-0324
tiiuae/falcon-40b
xai-org/grok-1
perplexity-ai/r1-1776
nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
microsoft/phi-4
databricks/dolly-v2-12b
Qwen/Qwen2.5-Coder-32B-Instruct
Qwen/QwQ-32B-Preview
mattshumer/Reflection-Llama-3.1-70B
HuggingFaceH4/zephyr-7b-beta
microsoft/Phi-3-mini-128k-instruct
microsoft/Florence-2-large
EleutherAI/gpt-j-6b
deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
microsoft/phi-1_5
microsoft/Phi-4-multimodal-instruct
01-ai/Yi-34B
cognitivecomputations/dolphin-2.5-mixtral-8x7b
TinyLlama/TinyLlama-1.1B-Chat-v1.0
ai21labs/Jamba-v0.1
tiiuae/falcon-40b-instruct
microsoft/Phi-3-mini-4k-instruct
mosaicml/mpt-7b
'''

# Results in `models_manual.txt`