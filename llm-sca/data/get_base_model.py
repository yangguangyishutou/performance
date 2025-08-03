'''
This script retrieves a list of popular base models from Hugging Face for the task of text generation.

Selection Strategy:
- For base models, we aim to collect about 10–20 models.
- In total, we need 300–400 child model pairs, meaning 75–100 pairs per base model type.
- Each base model typically has 4–10 fine-tuned or merged child models.
- We focus on text generation models due to their widespread use in downstream tasks via fine-tuning or merging.

Filtering Criteria:
- Sorted by number of likes (popularity).
- Filtered by accessibility (e.g., non-gated models).
- Considered the number of child models and parameter count (though not explicitly filtered in this script).

Output:
- A list of model IDs is saved to `base_models.txt`.
'''

from huggingface_hub import HfApi

api = HfApi()

# Define the task of interest (can expand to other NLP tasks if needed)
tasks = [
    "text-generation"
]

output_file = "./base_models.txt"

# Retrieve and save the top models based on 'likes' for each specified task
for task in tasks:
    # Collect 50 first, we will do filtering later
    models = api.list_models(task=task, sort='likes', limit=50, gated=False)
    with open(output_file, 'w') as f:
        for model in models:
            f.write(model.id + '\n')

# The resulting file will contain the top non-gated text generation model IDs
