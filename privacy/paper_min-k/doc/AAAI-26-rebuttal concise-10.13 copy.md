We appreciate the reviewers for their insightful comments and will address them in the revised version.



**Comparison with GotCha (Reviewer aruG & dXVB)**: We use baselines that uses zero-shot methods, namely the tool never saw the data prior to detection. We did not compare GotCha as it belongs to the type of methods that uses surrogate models, which comparatively was trained on the portion of the data, which either need to know the architecture of the targer model to train the surrogate model (the extent of knowledge on target model affects the MIA success rate),  heavily depends on the characteristics of the dataset, and  computationally extensive.

**Long Code Handling (Reviewer aruG & dXVB)**: For long functions or larger granularities like files/projects, LLMs exhibit strong generalization, memorizing only a subset of key information rather than the entire sequence. This leads to higher false negative rates (FNRs) on members, as shown in the original results(Long row: Pythia-2.8B: 75.12%, GPT-Neo-2.7B: 75.13%, StableLM-Alpha-3B: 66.04%, GPT-J-6B: 87.09%). The method can be extended to file/project levels by applying syntax pruning at those coarser granularities, though our current focus is function-level.

To mitigate this for long code, we propose slicing via sliding windows: encode the full n-token code without truncation using the tokenizer to get input IDs, attention masks, and offset mappings. Then, divide into m overlapping/non-overlapping windows and average SYNPRUNE scores across them.

We conducted two experiments on long functions:

- **Window 1 (max_length=512, stride=256, overlapping 256 tokens)**: FNR decreased by 7.51% (Pythia-2.8B), 5.32% (GPT-Neo-2.7B), 2.53% (StableLM-Alpha-3B), and 5.47% (GPT-J-6B).
- **Window 2 (max_length=128, stride=256, skipping 128 tokens)**: FNR decreased by 8.60% (Pythia-2.8B), 4.93% (GPT-Neo-2.7B), 3.33% (StableLM-Alpha-3B), and 6.35% (GPT-J-6B).



**Reviewer j7ev**:

**Benchmark**: The Pile dataset was randomly sampled from the GitHub corpus according to the ddd paper. *We filtered the Python functions from these samples to obtain the original files. Starting with the first function, we then selected the top 10 functions for every 100 functions, totaling 1,000 functions. Tracing these samples, we found 767 functions belonging to 235 different repositories, meaning an average of 3.26 functions were collected per repository.* **(Order?Each neighboring function entries has no  direct connections (neither same repo nor same file). Therefore, we believe the sampling process is random.)** We provide the script for reproduction at our replication site. For non-members, the extraction selects non-member functions from `.py` files, that are ordered lexicographically. **Finally, 1000 non-members come from 214 files and 100 repos.** **(Function order?) **We verify non-member non-reuse by searching the GitHub using small fragments. We manually verify the searched results and confirm the non-members occured no-whereelse.  Since the Pile dataset was sourced from the GitHub,  our search can realise contamination detection or deduplication check between members. 

**Dynamic Code Evaluation**: For timestamp cutoff, our benchmark considers duplicates and there is a time constraint. The Pile dataset was released in 2020 and will only collect repos before 2021, while non-members will only collect repos from 2024 and later. *For dynamically constructed benchmarks, our research differs from work like DyCodeEval and DynaCode in its objectives: they primarily focus on evaluating the problem-solving and reasoning capabilities of models using dynamic programming tasks, while our work focuses on the probability distribution of models. Therefore, dynamic evaluation frameworks are not directly applicable to our task setting.*

**Abnormal AUROC**: We evaluate baselines on their original benchmarks to confirm that the methods work correctly. The results indicates that existing zero-shot MIAs are originally designed for text-based MIAs, not adapted well to code.

**General-Purpose LLMs**: We select LLMs that we ensure that the LLMs are trained from the existing dataset (i.e., members). However, to the best of our knowledge, we did not find any disclousure of LLaMA and DeekSeek's training datasets,making the evaluation results on our constructed benchmark unsolid.



**Reviewer dXVB**:

**Manual Engineering Cost**: The synax rule construction process pilotly started with some frequent synax elements and finally ends with xx rules. Given that the assumption was validated, the construction process took in less than 30 human hours. When considering adapting to our method to other languages, we believe the adaption process would be sooner and can be automated since most of the modern language grammars are similar, and the automation process for multiple language can be seen as a following future work. However, our paper focuses on addressing the effectiveness of syntax and its effectiveness on code MIAs. Moreover, the popular languages (TIOBE top 10) accounts for 70.05% market share, indicating that the cost of adopting our method to mainstream programming languages is not such big.

**Performance on Obfuscated Code**: We evaluate our baseline on obfuscated samples at 1:5 ratio in the revision. After using variable renaming, AUROC decreased by **xxx% **for Loss, decreased by **xxx% **for ZLib, decreased by **xxx% **for Min-k and decreased by **xxx% **for SYNPRUNE, on average.

**Computational Overhead**:  The average compuatation **time** cost was (114.6, 0.17, 0.53, and 5.87) seconds, the average **GPU memory** cost was (10865.90, 10865.90, 10865.91, and 10865.93) MB, and the average **system memory** cost was (1521.23, 1521.23, 1521.24, and 1521.29) MB in 1:1 benchmark ratio, for Loss, ZLib, Min-k and SYNPRUNE.   respectively, 

