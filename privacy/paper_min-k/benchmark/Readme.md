数据集包括python数据集和java数据集，每个数据集有正样本和负样本之分。
实验文件的字段包括function和label。负样本原始文件还包括commit_date，repo，file_path，stars字段。
正样本实验文件为positive.jsonl，负样本实验文件为negative.jsonl。（negative_raw.jsonl为负样本原始文件，只选取其中的function字段和label字段获得了negative.jsonl，这是负样本实验文件。）

python的正样本的获取：对于the pile数据集的代码部分，使用脚本提取其中的python函数，生成一个jsonl文件。从该文件中最前面开始，每100行取前30行，一共取了3000行，取得300个函数，获得positive.jsonl文件。
python的负样本的获取：使用脚本从github搜索 "language:python created:>=2024-01-01 pushed:>=2024-01-01"，从仓库的文件中寻找函数。当一个仓库搜索到30条函数后就换到下一个仓库，获得negative_raw.jsonl文件（多于300行）。取前300行作为负样本。

java的正样本的获取：对于the pile数据集的代码部分，使用脚本提取其中的java类，生成一个jsonl文件。再使用脚本提取类中的函数，生成positive.jsonl文件。
java的负样本的获取：使用脚本从github搜索 "language:java created:>=2024-01-01 pushed:>=2024-01-01"，从仓库的文件中寻找函数。当一个仓库搜索到30条函数后就换到下一个仓库,获得negative_raw.jsonl文件（多于300行）。取前300行作为负样本。