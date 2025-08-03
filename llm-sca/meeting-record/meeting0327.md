# Discussion

- [Lei Ma](https://www.malei.org/) 的工作 也许选择 param 相关
  - Zhibo Liu, Yuanyuan Yuan, Shuai Wang, Xiaofei Xie, Lei Ma: Decompiling x86 Deep Neural Network Executables. USENIX Security Symposium 2023
  - (ICSE 2023) Qiang Hu, Yuejun Guo, Xiaofei Xie, Maxime Cordy, Mike Papadakis, Lei Ma, Yves Le Traon: Aries: Efficient Testing of Deep Neural Networks via Labeling-Free Accuracy Estimation
  - (TOSEM 2022) Xiaofei Xie, Tianlin Li, Jian Wang, Lei Ma, Qing Guo, Felix Juefei-Xu and Yang Liu. “NPC: Neuron Path Coverage via Characterizing Decision Logic of Deep Neural Networks” in ACM Transactions on Software Engineering and Methodology, no. 3 (2022): 1-27
- Pre 不讲 “这个、那个” 无意义的词
- 我们这个场景 也许是可以忍受这个时间开销（找重叠子图）
- 两条腿走路
  - tech 算法 ok
  - 但是要有个 **intuition** 人去看确实觉得这样可行
- 人家导师也在做相关工作 交流一下不要重复了

# TODO

LLM Coarse grained Component Analyssis

- Experiment Setup
  - Collect LLM_A ---Composition---> LLM_B
  - 100 Pair
    - (deepseek, deepseek-lora, adapter)
  - Composition type
    - FT
      - FFT
      - LoRA 有代表性的
      - Adapter
      - ...
    - Merge
    - quantization
    - ...
- Empirical Study
  - RQ1 柱状图：不同 FT 的区别
    - 横轴 FT 方法
    - 纵轴 White-Box 结构/权重 的区别
- Challenge
- Tool Approach
  - **Databse: LLM_A 的集合 200 个左右 + None**
  - 给定 LLM_B 判断是否与 Database 中的某个 LLM_A 存在 Composition type 关系，如果是 那么是 什么 Composition type 方法
- Experiment
  - RQ2 识别是否由某个模型 FT 得到
    - 哪个模型来的
    - 是否
  - RQ2 Accuracy, Precision, Recall 90%
  - RQ3 Real-world detection 80%

FT 足够复杂之后 LLM Fine grained FT Analysis

- Experiment Setup
  - Collect LLM_A ---Fine-tune---> LLM_B
  - 100 Pair
  - FT
    - FFT 50 pairs
    - LoRA
    - Adapter
    - DoRA
    - QLoRA
    - ...
- Tool Approach
  - **Databse: LLM_A 的集合 200 个左右 + None**
  - 给定 LLM_B 判断是否与 Database 中的某个 LLM_A 存在 FT 关系，如果是 那么是 什么 FT 方法
- 原理 Evaluation
  - FFT 二分类：precision & recall
  - 如果有个 LLM_C 相差特别大

## dataset collection

- different sizes and architectures
- sufficient “None” category (e.g., 20-30% of the total) to test negative cases
- "None" category
  - varying sizes & architectures
  - models trained on different datasets
  - models trained with different training procedures
  - Similarity Spectrum(Focus more on models that are similar enough to be challenging)
    - models that resemble your database models in architecture or size but are independently trained
    - distinct models

## neuron comparison

### Potential Methods

1. **Statistical Summaries of Weights**:

   - Compute simple statistics (e.g., mean, variance, skewness) for the weights in each layer or module.
   - Compare these between the two models using metrics like cosine similarity or Euclidean distance.
   - **Pros**: Fast and lightweight.
   - **Cons**: May miss detailed structural differences.

2. **Weight Norms and Entropy**:

   - Calculate the L1 or L2 norm of weight vectors/matrices per layer to measure magnitude differences.
   - Compute entropy of weight distributions to assess their spread.
   - Compare these values across models.
   - **Pros**: Quick overview of weight properties.
   - **Cons**: Lacks specificity about where differences lie.

3. **Dimensionality Reduction**:

   - Use PCA or random projections to reduce the high-dimensional weight space into a smaller set of features.
   - Compare the reduced representations between models.
   - **Pros**: Reduces computation while capturing key patterns.
   - **Cons**: Some information may be lost.

4. **Hashing-Based Fingerprints**:

   - Apply locality-sensitive hashing (LSH) to create compact fingerprints of weight matrices or layers.(将高维数据（如权重矩阵）映射到低维哈希值 相似的输入在哈希后更可能产生相同或相近的指纹)
   - Compare these fingerprints to estimate similarity.
   - **Pros**: Scalable and efficient for large models.
   - **Cons**: Approximate, may need tuning for accuracy.

5. **Singular Value Decomposition (SVD)**:

   - Perform SVD on weight matrices and compare singular values or vectors to analyze structural differences.
   - Comparison
     - 奇异值分布 奇异值衰减模式
     - 非零奇异值的数量
     - 奇异向量的余弦相似性或投影值
   - **Pros**: Highlights effective rank and principal components.
   - **Cons**: Computationally heavy for huge models.

6. **Targeted Comparison for Composition Types**:

   - Tailor the comparison to the suspected composition method:
     - **Fine-tuning (e.g., LoRA)**: Compare low-rank update matrices or specific layers.
     - **Adapters**: Focus on adapter module weights.
     - **Merging**: Check if weights are linear combinations of other models.
     - **Quantization**: Look at weight value distributions for quantization patterns.
   - **Pros**: Precise and efficient for known methods.
   - **Cons**: Less generalizable across unknown methods.

7. **Hierarchical Comparison**:
   - Use a two-step process:
     1. **Screening**: Compare high-level features (e.g., statistical summaries, norms, fingerprints) to quickly identify potential matches.
     2. **Detailed Analysis**: For similar pairs, compute layer-wise differences or targeted comparisons.
   - **Pros**: Balances speed and depth, ideal for large databases.
   - **Cons**: Requires setting a similarity threshold.

### Recommended Approach

Since you’re likely comparing a new LLM against a database (e.g., 200 models), a **hierarchical method** works best:

- **Step 1**: Precompute features (e.g., statistical summaries or fingerprints) for all database models. For a new model, compute the same features and find the closest matches using a distance metric.
- **Step 2**: For the shortlisted matches, perform a detailed comparison (e.g., layer-wise differences or SVD on key layers).

### Tips for Large Models

- **Sampling**: Compare a subset of parameters or layers (e.g., embedding or attention layers) to save time.
- **Layer Focus**: Prioritize layers affected by composition methods (e.g., later layers for fine-tuning).
- **Efficiency**: Use random projections or hashing if full comparisons are too slow.
