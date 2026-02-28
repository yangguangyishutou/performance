We appreciate the reviewers for your insightful comments.

**Reviewer aruG&dXVB**

**GotCha Comparison**: Our baselines are zero-shot, meaning the tool has never seen the data before detection. We exclude GotCha because it belongs to the other approaches that rely on training surrogate models, assuming partial data access and knowledge of the model’s architecture. The assumption differs from zero-shot methods.

**Long Code**: The LLM may have strong generalization in long code. A potential solution is to sample short pieces. e.g., the average FNR dropped by 5.8% and 5.2% using sliding windows of 128 and 512 tokens with 256 strides.

**Reviewer j7ev**

**Benchmark**: The Pile was collected by random sampling. We took the first 10 functions for every 100 entries, resulting in members from 235 distinct projects. For non-members, we sampled functions from alphabetically ordered files spanning 214 files and 100 projects. We searched on GitHub to verify that they were not reused. Since the Pile was from GitHub, our process enables contamination detection and deduplication. We included the benchmark in our replicating site.

**Dynamic Evaluation**: Dynamic benchmarks mitigate data leakage. In our benchmark, we set a timestamp cutoff of 2021 for members and after 2024 for non-members, and remove duplicates. To support dynamic evaluation, non-members can be recollected and the cutoff updated.

**Abnormal Baseline**: The baselines are correctly reproduced on the original benchmarks. The abnormality suggests that existing methods, designed for texts, do not adapt well to code.

**LLaMa and DS**: We selected only the LLMs for which we could confirm the training dataset. However, there is no disclosure for LLaMA and DS, which would make the results less conclusive.

**Reviewer dXVB**

**Manual Cost**: The manual process required less than 30 human hours. When adopting SynPrune to other languages, we expect it to be faster and more automated, as most languages share grammar similarities. Notably, our paper focuses on the syntax potential of enhancing MIAs. Besides, considering languages' popularities (70% for the TIOBE top10), the adaptation cost is relatively low.

**Perturbations**: After applying the mentioned perturbations, the average AUROC dropped by 8%, 2%, 8% and 1% for Loss, ZLib, Min-K, and SynPrune, resp..

**Overhead**: The average time and memory overheads were 114s, 0.2s, 0.5s, 6s, and 1.7GB, 1.4GB, 1.5GB, 1.5 GB for Loss, ZLib, Min-K, and SynPrune, resp..
