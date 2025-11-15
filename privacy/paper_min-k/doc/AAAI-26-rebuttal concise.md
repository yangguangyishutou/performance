We appreciate the reviewers for their insightful comments and will address them in the revised version.



**Benchmark (Reviewer j7ev & dXVB)**: The Pile dataset was randomly sampled from the GitHub corpus according to the ddd paper. **(Order?)** Each neighboring function entries has no  direct connections (neither same repo nor same file). Therefore, we believe the sampling process is random. We provide the script for reproduction at our replication site. For non-members, the extraction selects non-member functions from `.py` files, that are ordered lexicographically. **(Function order?)** We verify non-member non-reuse by searching the GitHub using small fragments. We manually verify the searched results and confirm the non-members occured no-whereelse.  Since the Pile dataset was sourced from the GitHub,  our search can realise contamination detection or deduplication check between members. 

**Comparison with GotCha (Reviewer aruG & dXVB)**: We use baselines that uses zero-shot methods, namely the tool never saw the data prior to detection. We did not compare GotCha as it belongs to the type of methods that uses surrogate models, which comparatively was trained on the portion of the data, which either need to know the architecture of the targer model to train the surrogate model (the extent of knowledge on target model affects the MIA success rate),  heavily depends on the characteristics of the dataset, and  computationally extensive.

**Long Code Handling (Reviewer aruG & dXVB)**: For long code, generalization limits memorization to key parts; we plan to improve via slicing (e.g., sliding windows) and will add experiments in the revision. The method extends to larger units (files/projects) or fragments by applying pruning at those granularities. **(+实验结果)**



**Reviewer j7ev**:

**Dynamic Code Evaluation**: **（笑云补充）**

**Abnormal AUROC**: We evaluate baselines on their original benchmarks to confirm that the methods work correctly. The results indicates that existing zero-shot MIAs are originally designed for text-based MIAs, not adapted well to code.

**General-Purpose LLMs**: We select LLMs that we ensure that the LLMs are trained from the existing dataset (i.e., members). However, to the best of our knowledge, we did not find any disclousure of LLaMA and DeekSeek's training datasets,making the evaluation results on our constructed benchmark unsolid.



**Reviewer dXVB**:

**Manual Engineering Cost**: The synax rule construction process pilotly started with some frequent synax elements and finally ends with xx rules. Given that the assumption was validated, the construction process took in less than 30 human hours. When considering adapting to our method to other languages, we believe the adaption process would be sooner and can be automated since most of the modern language grammars are similar, and the automation process for multiple language can be seen as a following future work. However, our paper focuses on addressing the effectiveness of syntax and its effectiveness on code MIAs. Moreover, the popular languages (TIOBE top 10) accounts for 70.05% market share, indicating that the cost of adopting our method to mainstream programming languages is not such big.

**Performance on Obfuscated Code**: We will evaluate SYNPRUNE on obfuscated samples (e.g., variable renaming, whitespace/comments, reordered arguments) at 1:5 ratio in the revision.**(+实验结果)**

**Computational Overhead**:  The average compuatation time cost was **(XX, XX, XX, and XX)** seconds and the average memory cost was **(XX, XX, XX, and XX),** in 1:1 benchmark ratio, for Loss, Lib, Min-k and SynPrune, respectively, 