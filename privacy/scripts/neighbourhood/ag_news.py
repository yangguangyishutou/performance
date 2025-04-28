from datasets import load_dataset

# 加载 AG News 数据集
dataset = load_dataset("fancyzhx/ag_news", cache_dir="/mnt/data")

# 训练集 & 测试集
train_data = dataset['train']
test_data = dataset['test']

print(train_data[0])
