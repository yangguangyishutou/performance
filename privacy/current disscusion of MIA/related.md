

问题: 7篇文章讨论清楚

问题：目标对比工具是否开源可以直接获取？他们实验的setup，1. 数据集 2. 生成的长度？

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
> $$
> Δ=L(f 
> θ
> ​
>  ,x)− 
> n
> 1
> ​
>   
> i=1
> ∑
> n
> ​
>  L(f 
> θ
> ​
>  , 
> x
> ~
>   
> i
> ​
>  ).
> $$
> <img src="F:\GithubSITP\privacy\current disscusion of MIA\assets\neighbors1.png" style="zoom: 67%;" />
>
> 在论文中，为了得到表格中列出的**低 FPR**（1%、0.1%、0.01%），需要**有目的地调节这个阈值**，使得他们在这些指定的 FPR 下测量到的 TPR 是多少，从而比较不同攻击方法的效果。
>
> ![](F:\GithubSITP\privacy\current disscusion of MIA\assets\neighbor2.png)

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



