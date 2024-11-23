

问题1: Benchmark



### 大模型MIA

1. Arxiv 2023 Membership Inference Attacks against Language Models via Neighbourhood Comparison.pdf

> simple thresholding of the model score in isola- tion tends to lead to high false-positive rates as it does not account for the intrinsic complexity of a sample
>
> reference-based attacks
>
>  unrealistic assumption that an adversary has access to samples closely resembling the original train- ing data
>
> neighbourhood attacks, which compare model scores for a given sample to scores of **synthetically generated neighbour texts** and therefore eliminate the need for access to the training data distribu- tion. 
>
> 



2. Arxiv 2024 Do Membership Inference Attacks Work on Large Language Models.pdf

> We find that MIAs barely outperform random guessing for most settings across varying LLM sizes and domains
>
> Our further analyses re- veal that this poor performance can be attributed to (1) the combination of a large dataset and few training iterations, and (2) an inherently fuzzy boundary between members and non-members.
>
> explore the challenges in evaluating membership inference attacks on LLMs, across an array of five commonly-used membership inference attacks
>
> LOSS Yeom et al., 2018  f (x; M) = L(x;M)
>
> Reference-based attacks, Carlini et al. 2022 Mireshghallah et al., 2022a f (x; M) = L(x; M) − L(x; Mref ).
>
> zlib entropy Carlini et al. 2021 : f (x; M) = L(x;M)/zlib(x)
>
> curvature Matern 2023
>
> Min-k% Prob Shi et al. 2023

>  We introduce MIMIR1, a unified repository for evaluating MIAs for LMs, with implementations of several attacks from literature. 

> 



3. Arxiv2024 Semantic Membership Inference Attack against Large Language Models.pdf

> SMIA trains a neural network to analyze the target model’s behavior on perturbed inputs, effectively capturing variations in output probability distributions between members and non-members
>
> Our central hypothesis is that perturbing the input of a target model will result in differential changes in its output probability distribution for members and non-members, contingent on the extent of semantic change distance.
>
> 对member和non-member perturb ，存在不同的differencial change

4. ICLR2024 DETECTING PRETRAINING DATA FROM LARGE LANGUAGE MODELS.pdf

> We introduce a dynamic benchmark **WIKIMIA** that uses data created before and after model training to support gold truth detection.
>
> Min-k% Prob

5. LLM Dataset Inference Did you train on my dataset.pdf

> 提出了比membership更大范围的dataset inference 问题



6. Usenix Sec2024 Did the Neurons Read your Book Document-level Membership Inference for Large Language Models.pdf

> we introduce the task of document-level membership inference for real-world LLMs,



7. ICML2024 Fast Adversarial Attacks on Language Models In One GPU Minute.pdf

> The computational efficiency of BEAST facilitates us to in- vestigate its applications on LMs for jailbreak- ing, eliciting hallucinations, and privacy attacks.
>
> 提出了方法可以快速实施攻击
>
> Beam Search-based Adversarial Attack (BEAST).

问题2: 文章是否足够全了？

问题3: 7篇文章讨论清楚





### 传统Machine Learning MIA



CCS2024 Is Difficulty Calibration All We Need- Towards More Practical MIA.pdf

> we take a further step towards a deeper un- derstanding of the role of difficulty calibration.
>
> Difficulty calibration is proposed by Watson et al. [57] to mitigate the aforementioned issues. It attempts to quantify the difficulty of sample points (i.e., the extent to the sample represented on the whole distribution) and uses this value to regularize the model’s original outputs, finally obtaining calibrated scores for MIAs.

### Other MIA

ICL

CCS2024 Membership Inference Attacks Against In-Context Learning.pdf

> ICL的MIA attack，和我们讨论的问题不太一样
>
> 

Vision Transformer

CCS2024 Membership Inference Attacks against Vision Transformers.pdf

> This paper presents the first comprehensive study on MIAs and corresponding defenses against ViTs. 
>
> we observe that the **attention**, an intermediate feature representation matrix to weigh the importance of different patches relative to each other, can lead to a membership leakage through an experiment.



### Others



Arxiv2023 LLaMA Open and Efficient Foundation Language Models.pdf

On Protecting the Data Privacy of Large Language Models(LLMs) A Survey.pdf

> 对于大模型数据隐私的threats和保护的survey



