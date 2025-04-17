# Presentation

1. 领导讲话 again！有条理地
2. PPT

# Todo

1. 收集 dataset unbiased 客观地 要有理由为什么这么选
2. 聚焦于找到子图比较所有权重的就好了
   1. 限时结束 已经解决
   2. 需要探索比较权重的方法
   3. 更多地比较 models 查看结构差异到底是什么问题
3. Steps
   1. dataset 中所有 models 丢到 pool 里面随机取两个
   2. Subgraph 匹配
   3. weight 比较
4. 写论文那会需要调研 related work
5. 代码 & 论文 丢 repo

# Questions

## Subgraph

1. 限时结束
2. finetune 之后结构很大不同
   1. 可能是下载方法不够完善
   2. 可能是加了任务头

## Significant param

大部分都是 data driven

1.  weight(nodes)
    1. pruning weights according to activation
    2. super weights
       1. a single parameter can destroy an LLM's ability to generate text
       2. 3 - 6 个
       3. mlp.down_proj in an early layer
       4. 之前人发现 Massive activations persist across many layers, feature constant magnitude, and always exist at the same position, **regardless of input**.
       5. Suggestion: massive activations are created by super weights
       6. Suggestion: instruct fine-tuning does not change the position of super weights
       7. Steps
          1. 步骤 1：通过输入一个提示（prompt），观察模型各层（尤其是 mlp.down_proj 层）的输入和输出激活分布，检测极端异常值（spikes）
          2. 步骤 2：根据异常值定位对应的权重坐标
          3. 步骤 3：移除已识别的超级权重，并重复上述过程，直至最大激活值显著降低。
2.  knowledge circuit(edges)
