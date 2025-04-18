# Insgiht from PEFTGuard

- t-SNE 降维找能够进行二分类的依据是有必要的
- 参考使用的 PEFT 方法 & Models
- 但我们的 task/architecture/... 不同
- Our novelty maybe focuses on ML(Machine Learning) to build a classifier instead of DL(Deep Learning)

# Netron

Mr. Huang only focuses from a high-level perspective

但是咱们要看明白代码细节 ;(

# Goal

C(M1, M2) -> 0,1
to determine whether or not a given model is fine-tuned from a given base model

![](./img/tasks.png)

p.s. 识别 overlap 的子图(找算法)

# My Work

思考工作本身的 novelty & challenges

## Details

通过分析两个模型的参数空间重叠性，判断模型之间是否存在微调继承关系。具体而言，通过量化微调后模型与原模型参数的结构相似性（例如低秩矩阵的权重分布、适配器模块的稀疏性等），以及参数更新的路径依赖关系（如梯度更新方向的一致性），构建一种基于参数空间重叠度的白盒检测框架，以识别模型是否通过特定重参数化方法从原模型微调而来

## novelty

- Related Work: Watermarking
- Classifier using Machine Learning

## challenges

- 寻找重叠子图的时间开销
- Param 巨大
  - Reduce the dimension of param([PCA](https://zhuanlan.zhihu.com/p/77151308))
  - 量化
  - 挑选出 重要的参数 梯度信息 & loss 需要数据 Activation Value
    - selective PEFT(Freeze and Reconfigure (FAR), FishMask)
  - 分解向量方向
- unified framework for 那么多的微调方法 需要不同敏感度
  - 元学习：通过元学习技术，训练一个模型来学习不同微调方法对参数影响的模式，从而自适应地调整分析框架
- Config of FT 同样影响 param delta
- 统计显著性检验
  - param delta between pretrain & initial
  - param delta between FT

