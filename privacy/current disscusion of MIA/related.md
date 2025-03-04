

问题: 7篇文章讨论清楚

问题：**目标对比工具**是否开源可以直接获取？他们实验的setup，1. 数据集 2. 生成的长度？

> 1.17 分配文章，运行现有的工具，使用benchmark的数据集
>
> 

问题：LOSS，交叉熵，概率分布之间的转换关系？

> **1.交叉熵和LOSS的关系**
>
> **交叉熵损失（Cross Entropy Loss）可以视作一种常用的 Loss（损失函数）策略。** 在分类任务中，交叉熵损失非常常见，因为它能直接衡量模型输出的**预测概率分布与真实分布**之间的差异，从而指导模型对参数进行优化。
>
> 
>
> **2. 概率分布、交叉熵和 MIA 的关系**
>
> 在 MIA 中，攻击者可以通过以下步骤利用概率分布和交叉熵损失来推断样本是否属于训练集：
>
> 1. **获取模型输出的预测概率分布：** 对于每个输入样本，攻击者首先获取模型的输出概率分布 q，即每个类别的预测概率。
>
> 2. **计算交叉熵损失：** 根据真实标签 p 和模型的输出概率分布 q，攻击者计算交叉熵损失：
>
>    H(p,q) = - logqk
>
>    交叉熵损失反映了模型对预测的信心程度，损失越小，预测越自信。
>
> 3. **区分训练集和非训练集样本：** 根据模型对训练集样本和非训练集样本的表现差异，攻击者通常会发现训练集样本的交叉熵损失较低（即模型对其更为自信），而非训练集样本的交叉熵损失较高。基于这一差异，攻击者就可以尝试推断样本是否属于训练集。
>
> 4. **训练集样本的高置信度：** 当样本属于训练集时，模型通常能较好地拟合这些样本，产生较高的 qk，从而导致较低的交叉熵损失。这使得训练集样本与非训练集样本在损失值上存在可辨识的差异。
>
> 5. **非训练集样本的低置信度：** 对于未见过的样本，尤其是那些在训练数据中不存在的样本，模型的预测通常会不那么确定，导致交叉熵损失较高。这使得攻击者可以通过损失值的高低来判断样本是否为训练集成员。
>
> 

认识阶段1: models tend to assign higher probabilities to their training samples than non-training points，缺点：simple thresholding of the model score in isolation tends to lead to high FPs

认识阶段2: reference-based attacks which compare model scores to those obtained from a reference model scores trained on similar data can substaintially improve the performance of MIA，缺点：需要确认两边的data distribution一致。



### Benchmark TODO

1. MIMIR http://github.com/iamgroot42/mimir
   * Do Membership Inference Attacks Work on Large Language Models
2. WIKIMIA
   * DETECTING PRETRAINING DATA FROM LARGE LANGUAGE MODELS
3. Gutenberg
   * Nob-MIAs: Non-biased Membership Inference Attacks Assessment on Large Language Models with Ex-Post Dataset Construction





## 大模型MIA

min-k; Neighbourhood, RECALL, blind,DC-PDD;

### A. 白盒LOSS： Perturbation/Neighborhood...

#### 1. Threshold

#### 2. Min-k

4. ICLR2024 DETECTING PRETRAINING DATA FROM LARGE LANGUAGE MODELS.pdf	——WangBo

> dataset：WIKIMIA
>
> We introduce a dynamic benchmark **WIKIMIA** that uses data created before and after model training to support gold truth detection.
>
> Min-k% Prob

> 提出了 MIN-K% PROB 方法，通过分析低概率 token 检测预训练数据的存在。
>
> 提供了动态基准数据集 WIKIMIA，用于多模型的训练数据检测评估。
>
> MIN-K% PROB for Robust and Scalable Pretraining Data Detection in LLMs.

6. Arxiv 2024 Min-K%++: Improved Baseline for Detecting Pre-Training Data from Large Language Models.pdf	——yuanheng

> 提出了 Min-K%++ 方法，通过局部极大值检测预训练数据，显著提升了成员推断攻击的检测性能。
>
> 提供了理论支持，适用于实时在线生成场景。
>
> Min-K%++ for Robust Pretraining Data Membership Inference in LLMs.

> 提出了 Min-K%++ 方法，通过局部极大值检测预训练数据，显著提升了成员推断攻击的检测性能。

#### 3. Perturbation

1. Arxiv 2023 Membership Inference Attacks against Language Models via Neighbourhood Comparison.pdf	——zhuoyang

> dataset：article summaries， tweets， wikipedia
>
> simple thresholding of the model score in isola- tion tends to lead to high false-positive rates as it does not account for the intrinsic complexity of a sample
>
> reference-based attacks
>
> unrealistic assumption that an adversary has access to samples closely resembling the original training data
>
> neighbourhood attacks, which compare model scores for a given sample to scores of **synthetically generated neighbour texts** and therefore eliminate the need for access to the training data distribu- tion. 
>
> insight：neighbor 是经过变换得到，不是member，因此如果原有x与neighbor的loss接近，说明不是member，反之则是
>
> 
>
> TODO：if the model score of the target data is similar to the crafted neighbors, then they are all plausible points from the distribution and the target point is not a member of the training set. However, if a sample is much more likely under the target model’s distribution than its neighbors, we infer that this could only be a result of overfitting ： 用公式如何表示
>
> DO: 使用一种基于**neighbors**的决策规则，用来判断一个给定的样本 xxx 是否可能是模型训练集中的成员。具体做法是先构造若干与 xxx 语义、语法上极为相似但不在训练集中的邻居样本 {x~1,…,x~n}，计算目标模型对 xxx 的损失与对这些邻居的平均损失之间的差值，再与某个阈值 γ 进行比较。如果这个差值远小于 γ ，就说明模型对 xxx 可能存在“过拟合”，进而暗示 xxx 可能出现在训练集中。
>
> <img src="F:\GithubSITP\privacy\current disscusion of MIA\assets\neighbors1.png" style="zoom: 67%;" />
>
> L(f, x)损失值的具体计算：
>
> <img src="F:\GithubSITP\privacy\current disscusion of MIA\assets\image-20250226145532918.png" alt="image-20250226145532918" style="zoom: 67%;" />
>
> 
>
> 在论文中，为了得到表格中列出的**低 FPR**（1%、0.1%、0.01%），需要**有目的地调节这个阈值**，使得他们在这些指定的 FPR 下测量到的 TPR 是多少，从而比较不同攻击方法的效果。
>
> ![](F:\GithubSITP\privacy\current disscusion of MIA\assets\neighbor2.png)
>
> 思考：
>
> 1.目前的 **neighborhood** 决策规则中使用的是当前样本与其 **n** 个邻居样本之间的损失差异，可以引入多层邻居信息。**k-hop 邻居**：第1层邻居（直接邻居），第2层邻居（与第1层邻居的邻居）...
>
> <img src="F:\GithubSITP\privacy\current disscusion of MIA\assets\image-20250218204540804.png" alt="image-20250218204540804" style="zoom: 67%;" />
>
> - wi 是第 **i** 层邻居的权重，远离目标样本的邻居权重较小。
>
> - ni 是第 **i** 层邻居的数量。
> - 分别计算每个邻居的损失值最后取加权平均值
>
> 2.目前，对于同一个样本生成的若干个邻居都是相同地位的，可以动态地调整每个邻居的 权重。例如，与样本相似度更高的邻居可以赋予更高的权重，可能会使攻击效果更好。
>
> 3.输入构建：
>
> - **数据读取**：从 **CSV 文件**（如 Twitter、News、Wiki）加载原始文本。
>
> - **数据预处理**：对文本进行清洗、过滤，去掉不必要的字符或空值。
>
> - **文本标记化**：使用 **Tokenizer**（BERT、DistilBERT、RoBERTa）将原始文本转换为 **token ids**，并确保符合模型的输入要求（填充和截断）。
>  - **文本 Tokenization**： 每个文本会通过 `search_tokenizer` 进行 tokenization（标记化）。`search_tokenizer` 依赖于所选模型的 **Tokenizer**（BERT、DistilBERT 或 RoBERTa）。该过程将文本转化为模型可以处理的 **token ids** 格式，并且对超长的文本进行 **截断**，对短文本进行 **填充**，确保每个输入样本的长度符合模型的要求（最大 512 个 token）。
>   - **特殊 Token**：
>    - `[CLS]`：每个输入文本会以 `[CLS]` token 开始，用于标识序列的开始。对于分类任务来说，这个 token 的输出通常用于表示整个序列的表示。
>         - `[SEP]`：如果有两个句子作为输入，它们之间会用 `[SEP]` 进行分隔。在这种情况下，模型会分别对每个句子进行编码。
>    - 在模型输入时，原始文本会被处理为类似以下格式：[CLS] valkyria chronicles iii = [SEP] (second sentence if available) [SEP]
>
> - **模型输入**：将标记化后的文本输入模型进行推理，得到 logits 和其他输出信息（如概率分布）。
>
> 4.问题：缺少数据集中样本的真实标签
>
> - 作者将AG News数据集重新分为两个互不相交的子集（各60,000样本）：
>  - **训练集（Target Model Training Data）**：用于训练目标模型（如GPT-2），对应成员推断攻击中的“正样本”（即训练成员）。
>   - **非训练集（Non-Training Data）**：未被用于训练目标模型，作为成员推断攻击的“负样本”（即非成员）。
> - 此外，还有一个**第三子集**（可能来自原始数据集或其他来源，如NewsCatcher）用于训练参考模型（见第3.2节）。
>
> TODO:
>
> 1. 邮件追踪
>
> 2. 看相关的其他文章
> 3. 代码上的创新和可行性
>
> 邻居生成策略的改进
>
> 代码具有严格的语法和语义结构，直接替换词语可能导致功能错误。需设计**代码专用的邻居生成方法**：
>
> - **语法保留的变换**：
>   - **变量/函数重命名**：使用代码抽象语法树（AST）解析，安全替换标识符名称，确保作用域一致性。
>   - **控制流等价转换**：调整循环或条件语句结构（如将 `for` 循环改为 `while` 循环），保持逻辑不变。
>   - **注释插入或删除**：添加或移除不影响功能的注释。
>   - **代码格式调整**：修改缩进、空格或换行符，保持功能不变。
> - **基于代码模型的生成**：
>   - 使用预训练的代码模型（如 CodeBERT、Codex）生成语义等价的代码片段，例如通过掩码预测或代码补全。
>
> 

2. Arxiv2024 Semantic Membership Inference Attack against Large Language Models.pdf	——zhuoyang

> SMIA **trains a neural network to analyze the target model’s behavior on perturbed inputs,** effectively capturing variations in output probability distributions between members and non-members
>
> Our central hypothesis is that **perturbing the input of a target model will result in differential changes** in its output probability distribution for members and non-members, contingent on the extent of semantic change distance.
>
> 对member和non-member perturb ，存在不同的differencial change





10. Arxiv 2024 RECALL Membership Inference via Relative Conditional Log-Likelihoods.pdf	——yuanheng

> 提出了基于条件对数似然变化的成员推断攻击方法，用于检测大语言模型的训练数据。
>
> 提出了 RECALL 分数，通过前缀干扰区分成员和非成员数据。
>
> Relative Conditional Log-Likelihoods for Membership Inference in LLMs.

11. Arxiv 2024 Blind Baselines Beat Membership Inference Attacks for Foundation Models.pdf	——yuanheng

> 通过“盲攻击”揭示现有成员推断评估方法的缺陷，强调分布偏差对评估结果的影响。
>
> 提出了改进建议，倡导基于随机训练-测试划分的评估方法。
>
> Blind Baselines for Membership Inference Evaluations in Foundation Models.
> TODO 具体说为啥是flawed？Unfortunately, we find that evaluations of MI attacks for foundation models are flawed, because they sample members and non-members from different distributions.

13. Arxiv 2024 DC-PDD  Pretraining Data Detection for Large Language Models.pdf	——caiyi

> 提出了 DC-PDD 方法，通过分布校准改进对预训练数据的检测性能，适用于多语言场景。
>
> 提供了新基准数据集 PatentMIA，针对中文预训练数据检测。
>
> Divergence-Calibrated Pretraining Data Detection for Robust Membership Inference in LLMs.
>
> We compute the cross-entropy (i.e., the diver- gence) between the token probability distri- bution and the token frequency distribution to derive a detection score



###  B. Empirical Accessment

2. Arxiv 2024 Do Membership Inference Attacks Work on Large Language Models.pdf	——zhuoyang

> We find that MIAs barely outperform random guessing for most settings across varying LLM sizes and domains
>
> Our further analyses re- veal that this poor performance can be attributed to (1) the combination of a large dataset and few training iterations, and (2) an inherently fuzzy boundary between members and non-members.
>
> explore the challenges in evaluating membership inference attacks on LLMs, across an array of five commonly-used membership inference attacks
>
> * LOSS Yeom et al., 2018  f (x; M) = L(x;M)
>* Reference-based attacks, Carlini et al. 2022 Mireshghallah et al., 2022a f (x; M) = L(x; M) − L(x; Mref ).
> * zlib entropy Carlini et al. 2021 : f (x; M) = L(x;M)/zlib(x)
>* curvature Matern 2023 neighborhood attack
> * Min-k% Prob Shi et al. 2023

>  We introduce MIMIR1, a unified repository for evaluating MIAs for LMs, with implementations of several attacks from literature. 

> released **benchmark**
>
> Non-members have high n-gram overlap with members e.g.non-members from the Pile Wikipedia and ArXiv test samples have aver- age 7-gram overlaps of over 30%. 



9. Arxiv 2024 Nob-MIAs Non-biased Membership Inference Attacks Assessment on Large Language Models with Ex-Post Dataset Construction.pdf	——xiaoyun

> 提出了用于评估成员推断攻击（MIA）的无偏数据集构建方法，重点在于消除 n-gram 偏差和分类偏差。
>
> 提出了	m 和 No-Class 两种算法以构建无偏数据集。
>
> Membership Inference Attacks (MIAs) aim to detect whether specific documents were used in a given LLM pretraining, but their effec- tiveness is undermined by biases such as **time-shifts and n-gram overlaps.**
>
> Non-biased MIAs Assessment for Large Language Models.
>
> This paper addresses the evaluation of MIAs on LLMs with partially inferable training sets, under the **ex-post hypothesis**:
>
> TODO 
>
> No-n-gram no-class 具体怎么做的？
>
> We provide algorithms for constructing ex-post datasets of two types:  No − Ngram (“No N-gram bias”) and No−Class (“non classifiable”), each designed to mitigate specific types of biases for MIA assessment.

### C. Dataset Document Inference

TODO Document Inference与现有技术的关系和创新？

5. LLM Dataset Inference Did you train on my dataset.pdf	——WangBo

> 提出了比membership更大范围的 **dataset inference** 问题
>
> Metrics for LLM Membership Inference 相关工作讲的听清楚

6. Usenix Sec2024 Did the Neurons Read your Book Document-level Membership Inference for Large Language Models.pdf	——WangBo

> we introduce the task of document-level membership inference for real-world LLMs,

### D. Adversarial 

7. ICML2024 Fast Adversarial Attacks on Language Models In One GPU Minute.pdf	——xiaoyun

> The computational efficiency of BEAST facilitates us to investigate its applications on LMs for jailbreak- ing, eliciting hallucinations, and privacy attacks.
>
> 提出了方法可以快速实施攻击
>
> Beam Search-based Adversarial Attack (BEAST).
>
> TODO Beam Search

### E. Blackbox LOSS（LOSS未知）

15. ACL 2024 DPDLLM A Black-Box Framework for Pretraining Data Detection in Large Language Models.pdf	——caiyi	

> 提出了 DPDLLM 框架，通过参考模型生成的概率序列，**无需访问模型内部信息即可检测预训练数据**。
>
> 构建了 WikiMIA2 和 BookMIA 等基准数据集，用于评估检测性能。
>
> DPDLLM for Black-Box Pretraining Data Detection in LLMs.
>
> TODO 总体思路？ 给定文本形式的输出内容，如何inference membership？

### F. Code Model

TSE 2024 Gotcha! This Model Uses My Code! Evaluating Membership Leakage Risks in Code Models

>**GOTCHA如何工作?**
>
>GOTCHA是一种针对代码补全模型的MIA方法，分为两个主要步骤：
>
>1. 训练代理模型(Surrogate Model)1.
>
>   - 攻击者使用部分已知的训练数据训练一个代理模型，模拟目标模型(Victim Model)的行为
>   - 代理模型会接收训练数据和非训练数据，生成相应的输出。
>
>2. 训练成员分类器(MIAClassifier)
>
>   - 使用代理模型的输入、输出和真实答案(Ground Truth)，生成代码嵌入(CodeEmbeddings)
>
>   - 基于这些嵌入，训练一个二元分类器，判断某段代码是否属于训练集。
>
>**关键创新**
>
>GOTCHA同时考虑了三类信息:
>
>- 模型输入:代码补全任务的初始代码，
>- 模型输出:代理模型生成的补全代码。
>- 真实答案:正确的补全代码。 这些信息被编码为嵌入向量，输入到一个神经网络分类器中。
>
>**受害者模型（Victim Models）**
>
>- 主要使用**CodeGPT**（基于GPT-2架构的代码补全模型），并扩展到其他五个开源模型（CodeGen、CodeParrot、GPT-Neo、PolyCoder-160M/0.4B）。
>- 模型在JavaCorpus数据集上微调，包含约1.3万训练样本和8千测试样本。
>
>**数据集**
>
>使用`JavaCorpus`数据集，包含14,000多个GitHub上的Java项目。实验中将数据分为
>
>- 受害者模型的训练集(12,934个样本)和测试集(8,268个样本)
>- 攻击者可访问的部分训练数据(例如10%或20%)用于训练代理型。
>
>**训练数据与微调**
>
>- 预训练数据: `CodeGPT`最初在`CodeSearchNet`的Java子集上预训练。
>- 微调数据: 研究者使用`JavaCorpus`数据集(包含14,000多个GitHub Java项目)的1%子集进行微调。
>
>**获取训练数据**
>
>- **CodeSearchNet:** 这是一个公开数据集，可从GitHub下载:https://github.com/github/CodeSearchNet
>- **JavaCorpus:** 由Allamanis和Sutton收集，包含大量Java项目。论文中提到`CodeXGLUE`(https://github.com/microsoft/CodeXGLUE)对JavaCorpus进行了预处理(例如移除注释、长字符串等)

## MIA Defense 

### A.  Differencial Privacy

XXX

### B. Privacy Auditing

8. Arxiv 2024 PANORAMIA Privacy Auditing of Machine Learning Models without Retraining.pdf	——xiaoyun

> PANORAMIA 提出了基于生成数据的隐私审计框架，可在无需重复训练模型或真实非成员数据的情况下评估隐私泄漏。
>
> 提出了使用生成数据进行隐私审计的新方法
>
> Privacy Auditing with NO Retraining by using Artificial data for Membership Inference Attacks (PANORAMIA).
>
> 1. Training Machine Learning (ML) models with Differential Privacy (DP) Dwork et al. (2006), such as with DP-SGD Abadi et al. (2016), upper-bounds the worst-case privacy loss incurred by the training data.
>
> 2. privacy auditing aims to empirically lower-bound the privacy loss of a target ML model or algorithm.



## 传统Machine Learning MIA



CCS2024 Is Difficulty Calibration All We Need- Towards More Practical MIA.pdf

> we take a further step towards a deeper un- derstanding of the role of difficulty calibration.
>
> Difficulty calibration is proposed by Watson et al. [57] to mitigate the aforementioned issues. It attempts to quantify the difficulty of sample points (i.e., the extent to the sample represented on the whole distribution) and uses this value to regularize the model’s original outputs, finally obtaining calibrated scores for MIAs.

##  Other MIA

ICL

CCS2024 Membership Inference Attacks Against In-Context Learning.pdf

> ICL的MIA attack，和我们讨论的问题不太一样
>



Vision Transformer

CCS2024 Membership Inference Attacks against Vision Transformers.pdf

> This paper presents the first comprehensive study on MIAs and corresponding defenses against ViTs. 
>
> we observe that the **attention**, an intermediate feature representation matrix to weigh the importance of different patches relative to each other, can lead to a membership leakage through an experiment.



## Others

Arxiv2023 LLaMA Open and Efficient Foundation Language Models.pdf

On Protecting the Data Privacy of Large Language Models(LLMs) A Survey.pdf

> 对于大模型数据隐私的threats和保护的survey



