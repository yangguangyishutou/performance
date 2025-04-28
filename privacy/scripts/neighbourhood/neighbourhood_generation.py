import torch
from transformers import BertTokenizer, BertForMaskedLM

# 加载 BERT 预训练模型
bert_tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
bert_model = BertForMaskedLM.from_pretrained("bert-base-uncased")

def generate_bert_neighbours(text, num_neighbours=5):
    words = text.split()
    neighbours = []
    
    for _ in range(num_neighbours):
        modified_words = words.copy()
        
        # 随机选择一个单词替换为 [MASK]
        idx = torch.randint(0, len(words), (1,)).item()
        modified_words[idx] = "[MASK]"
        masked_text = " ".join(modified_words)
        
        # 预测 MASK 的单词
        inputs = bert_tokenizer(masked_text, return_tensors="pt")
        with torch.no_grad():
            outputs = bert_model(**inputs)
        
        predictions = outputs.logits[0]  # 取 logits 输出
        predicted_index = torch.argmax(predictions[idx]).item()
        predicted_word = bert_tokenizer.decode([predicted_index])

        modified_words[idx] = predicted_word  # 替换 MASK
        neighbours.append(" ".join(modified_words))
    
    return neighbours

# 示例
sample_text = "Wall St. Bears Claw Back Into the Black (Reuters)"
neighbours = generate_bert_neighbours(sample_text, num_neighbours=3)
print(neighbours)
