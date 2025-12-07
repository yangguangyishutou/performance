### Review: #Program Committee j7ev

#### Strengths

1. This paper is well-written and easy to follow.
2. The studied problem is interesting and important.

#### Weaknesses

1. The main evaluation is conducted on the proposed private dataset, thus the effectiveness is unknown.
2. The reported baseline results are abnormal.
3. One contribution of this paper is the benchmark, however, there is no benchmark provided in the Supplementary Material, and the validity of the proposed benchmark is unclear.
4. Missing important related work on data contamination in code LLMs.

#### Detailed Comments

1. The details of the benchmark construction are not clear. For example, the authors only mentioned that “We randomly sampled 1,000 Python functions by selecting 10 functions from every 100 consecutive entries in the Pile dataset.” First, the Pile is a very large dataset without a natural ordering—how did the authors determine the order of the dataset? Second, how exactly were the 10 functions selected—were they uniformly sampled, or were the first 10 valid functions taken? The same issue arises for the non-member data samples: how were the 10 functions selected in each case? More importantly, since the non-members are also collected from GitHub, and because of heavy code reuse in open-source repositories, it is difficult to verify whether the so-called non-members were reused from existing GitHub code, and no contamination detection or deduplication check was conducted to ensure that non-members truly differ from members.
2. The main evaluation is based on the proposed private benchmark. However, since the benchmark construction process omits important details, the effectiveness of the benchmark is questionable. I suggest the authors conduct additional evaluation and discuss dynamic code evaluation [6, 8], for example, by leveraging benchmarks with a timestamp cutoff such as the LeetCode dataset [1, 7], or dynamically constructed benchmarks such as DyCodeEval, DynaCode, and PPM [2, 3, 4, 5]. 
3. The reported baseline results appear abnormal. For AUROC, the expected random-guess baseline should be around 50%, yet the reported numbers are even lower. Such results indicate that flipping the prediction labels could yield a very high AUROC. For example, in Table 4, ZLib 1:1 shows 33.2 AUROC for Pythia 2.8B—flipping predictions would yield 100 − 33.2 = 66.8 AUROC.
4. All evaluated models are domain-specific code LLMs. However, general-purpose LLMs such as LLaMa and DeepSeek are widely used for code generation. The effectiveness of the proposed method on these general-purpose models remains unknown. 

#### References

1. https://huggingface.co/datasets/newfacade/LeetCodeDataset
2. DyCodeEval: Dynamic Benchmarking of Reasoning Capabilities in Code Large Language Models Under Data Contamination. ICML 2025
3. DynaCode: A Dynamic Complexity-Aware Code Benchmark for Evaluating Large Language Models in Code Generation. ACL 2025 Findings
4. Is your benchmark (still) useful? dynamic benchmarking for code language models. Arivx
5. PPM: Automated Generation ofDiverse Programming Problems for Benchmarking Code Generation Models. FSE 2024
6. Recent Advances in Large Language Model Benchmarks against Data Contamination: From Static to Dynamic Evaluation. EMNLP 2026
7. LiveCodeBench: Holistic and Contamination Free Evaluation of Large Language Models for Code. ICLR 2025
8. A Comprehensive Survey of Contamination Detection Methods in Large Language Models. Arivx

#### Rating

6: Marginally above acceptance threshold

#### Confidence

4: The reviewer is confident but not absolutely certain that the evaluation is correct



### Review: #Program Committee aruG

#### Overview

This paper presents an optimised method to enhance the MIA applied to code by excluding tokens inherited from Python syntax conventions, which can be easily predicted due to the pattern based on the programming language. The paper proposed a comprehensive comparison between the approach proposed and prior MIA approaches like Loss, ZLIB, MIN-K%, showing how far the proposed method enhances the detection of code during the model training process while revealing some limits of the method when applied to long code.

#### Strengths

- Comprehensive presentation of the problem statement and the justification of the intuition behind the proposed approach.
- Comprehensive justification of the choice of the model and benchmarks.
- Relevant experiments allow us to show how it can be relevant to apply the proposed approach and highlight the impact of the category of syntax convention and the code length on the approach.

#### Weaknesses

- It could be nice to compare the approach with one of a code specialized MIA (like GOTCHA, ...).

#### Detailed Comments

This paper presents a method that enhances the detection of a model's training data applied to code. Indeed, due to the syntactic constraints of programming languages, many easily predictable patterns make the classic MIA difficult to apply to code. By removing the deterministic pattern (at least the consequence tokens), it is normal to catch more relevant information, allowing for leveraging these approaches to code. The paper presents a relevant justification for the model and benchmark used for the evaluation. Also, the comparison with prior MIA metrics allows highlighting the performance gain of the proposed approach while revealing its importance in the domain of model training code detection. The ablation study further explained the impact of the different pipeline components. The results are relevant and coherent. It is also important to highlight the limit of the approach on long code. That can open a door for further study to improve this method.

#### Questions

- How did the author plan to improve the method for long code?

#### Rating

7: Good paper, accept

#### Confidence

4: The reviewer is confident but not absolutely certain that the evaluation is correct



### Review: #Program Committee dXVB

#### Summary

This paper introduces SYNPRUNE, a syntax-aware, pruning-based membership inference attack (MIA) designed to determine whether specific code samples were included in the pretraining data of LLMs. Unlike previous MIAs that treat code as unstructured text, SYNPRUNE leverages the formal syntax of programming languages, systematically removing tokens that are mandated by grammar and thus do not reflect individual authorship. The authors curate a real, verifiable benchmark of member and non-member Python functions, and demonstrate through comprehensive experiments that SYNPRUNE outperforms state-of-the-art MIAs in detecting code memorization across several LLMs. Detailed ablation and robustness studies are conducted to support the claimed advantages.

#### Strengths

1. Clearly incorporates formal programming language syntax constraints into the MIA process, improving precision in detecting training data membership for code.
2. Provides a carefully verified, real-world Python function benchmark with traceable members and post-cutoff non-members, addressing limitations of synthetic datasets in prior work.
3. The method does not rely on training shadow models, making it feasible for scenarios where pretraining data or model weights are inaccessible.

#### Weaknesses

1. Function-level granularity only: The benchmark and experiments focus on function-level membership inference; it’s unclear how the method scales to larger code units (files, projects) or partial code fragments.
2. High Manual Rule Engineering Cost: Adapting the approach to each new programming language requires labor-intensive manual collection of numerous syntax conventions, limiting scalability.
3. Missing Key Baseline Comparison: Although the paper mentions the GOTCHA method, it does not include a direct comparison against this important baseline, leaving the performance advantage less convincing.

#### Questions

1. How does SYNPRUNE perform on code samples that intentionally obfuscate or minimally alter syntax while preserving semantics (e.g., variable renaming, added whitespace/comments, reordered arguments)?
2. What is the computational overhead (time, memory) of applying SYNPRUNE compared to standard MIAs?

#### Rating

5: Marginally below acceptance threshold

#### Confidence

4: The reviewer is confident but not absolutely certain that the evaluation is correct