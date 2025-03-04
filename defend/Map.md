# 2.25 TODO

参考模板(不非得按这个来)：

- AutoDAN
  - 初始数据集：xx
  - 结果：(在什么数据集上取得了什么分数)
    - dataset1
      - ASR: xx%
      - ...
    - dataset2
  - 被攻击模型：(target model的细节也可以说明，比如xx模型对齐较严、xx模型有输入输出过滤)
    - 1
    - 2
  - 横向对比方法：(也可以简要注明，AutoDAN、也就是你看的这篇论文，对比下面这些方法的优势)
    - 1
    - 2

## 问题

很多论文发布时间早，实验的对比数据基本都已经过时，如果我们不自己重复实验的话，很难得到可信结果

可能需要关注一下最近的一些论文/综述

## AutoDAN

## GCG

- 初始数据集：
  - AdvBench
- 结果：![alt text](./img/GCG结果.png)
  - llama2-7b-chat 88%
  - vicuna 7B
  - GCG对基于GPT模型的攻击更有效：![alt text](./img/GCG-gpt.png)
- 横向对比方法：(也可以简要注明，AutoDAN、也就是你看的这篇论文，对比下面这些方法的优势)
  - GBDA
  - PEZ
  - AutoPrompt
- 技术细节

## GPT FUZZER

- 这篇论文没顶会，但仓库star很高，可能有些过时了，可以看下最新的相关方法

- 初始数据集：人工编写100条数据集
  - [ Yi Liu, Gelei Deng, Zhengzi Xu, Yuekang Li, Yaowen Zheng, Ying
 Zhang, Lida Zhao, Tianwei Zhang, and Yang Liu. Jailbreaking chat
gpt via prompt engineering: An empirical study. ]
  - [Training a helpful and harmless assistant with reinforce
ment learning from human feedback. arXiv preprint arXiv:2204.05862,
 2022.]
- 结果：
  - llama2-7b-chat 80% ASR
  - Vicuna-7B、Vicuna-13B和Baichuan-13B 100%
- 横向对比方法：
  - No Attack
  - GCG
  - Human written
  - MasterKey
- 技术细节：
  - fine-tune RoBERTa for judging tasks
  - torch 2.1, 8 A100

