# 添加论文列表

## 24/11/12

删除重复论文，更新了论文pdf分类。调整分类： B-上下文/长度 -> C-人类干预策略。

不确定的分类暂时都放在了F-misc下。

### Attack

##### A. 对抗提示生成  Adversarial Prompting / Fuzzing / Genetic algorithm

* Universal and Transferable Adversarial Attacks on Aligned Language Models (GCG)

> GCP reformulates the jailbreak attack as an adversarial example generation process and utilizes the gradiant information of white-box LLMx to guide the search process of the jailbreak prompt's tokens.

>  GCG inevitably request a search scheme guided by the gradient information on tokens. 
>
>  Although it provides a way to automatically generate jailbreak prompts, this leads to an in- trinsic drawback: they often generate jailbreak prompts composed of nonsensical sequences or gib- berish, i.e., without any semantic meaning
>
>  This severe flaw makes them highly susceptible to naive defense mechanisms like perplexity-based detection
>
>  白盒，依赖gradient information
>
>  

* ICLR2024 PAIR: Jailbreaking black box large language models in twenty queries

> prompt automatic iterative refinement
>
> uses an attacker LLM to automatically generate jailbreaks for a separate targeted LLM without human intervention. 
>
> 缺点： lack guidance for jailbreak knowledge

* Arxiv2024 Tree of attacks: Jailbreaking black-box llms automatically

> 缺点： lack guidance for jailbreak knowledge

> TAP utilizes an attacker LLM to iteratively refine candidate (attack) prompts until one of the refined prompts jailbreaks the target.



* ICLR2024 AUTODAN: GENERATING STEALTHY JAILBREAK PROMPTS ON ALIGNED LARGE LANGUAGE MODELS

> existing suffer from scalability issues, heavily rely on manual crafting of prompts

> Stealthiness problem, semantic meaning less, susceptible through perplexity testing

>  automatically generated stealthy jaikbreak prompts by hierarchical genetic algorithm.

> genetic algorithms

* Autodan: Automatic and interpretable adversarial attacks on large language models.



* AUTODAN-TURBO: A LIFELONG AGENT FOR STRAT- EGY SELF-EXPLORATION TO JAILBREAK LLMS

> utilizes *lifelong learning agents* to automatically and continually discover diverse strategies,
>
> Automatic Strategy Discovery
>
> 利用attacker LLM 生成合适的jailbreak strategy

* USENIX2024 LLM-Fuzzer-Scaling Assessment of Large Language Model Jailbreaks

```plaintext
论文介绍了**LLM-Fuzzer**，借鉴了模糊测试（fuzz testing），通过使用人工设计的越狱提示作为起始点，并通过精心定制的种子选择和变异机制，自动生成适应不同LLMs的越狱提示。实验结果表明，LLM-Fuzzer生成的越狱提示在可利用性和可转移性方面显著提高，表明许多开源和商业LLMs在经过安全微调后，仍然容易受到越狱攻击。
```

* GPTFUZZER: Red Teaming Large Language Models with Auto-Generated Jailbreak Prompts

> we introduce GPTFUZZER, a novel blackbox jailbreak fuzzing framework inspired by the AFL fuzzing
> framework. Instead of manual engineering, GPTFUZZER automates the generation of jailbreak templates for red-teaming LLMs. At its core, GPTFUZZER starts with human-written
> templates as initial seeds, then mutates them to produce new templates.

* ICASSP2024 [**Fuzzllm**: A novel and universal fuzzing framework for proactively discovering jailbreak vulnerabilities in large language models](https://ieeexplore.ieee.org/abstract/document/10448041/)* [Cited by 34]



* Arxiv2024 JAILBREAKING LEADING SAFETY-ALIGNED LLMS WITH SIMPLE ADAPTIVE ATTACKS

> we initially design an adversarial prompt template (sometimes adapted to the target LLM), and then we apply random search on a suffix to maximize a target logprob (e.g., of the token “Sure”),



Arxiv2024 Jailbreaking Attack against Multimodal Large Language Model

> A maximum likelihood-based algorithm is proposed to find an image Jailbreaking Prompt (imgJP), enabling jailbreaks against MLLMs across multiple unseen prompts and images

##### B. Exploit multi language 利用语言的差别，文化习俗，跨语言的歧义/模糊性, cipher， 上下文/长度

* "do anything now": Characterizing and evaluating in-the-wild jailbreak prompts on large language models

* Low-resource languages jailbreak gpt-4

> low-resource language-based strategies

* Gpt-4 is too smart to be safe: Stealthy chat with llms via cipher

> Cipher 

* Codechameleon: Personalized encryption framework for jailbreaking large language models

> cipher
>
> we reformulate tasks into a code completion format, enabling users to encrypt queries using personalized encryption functions

* ICLR2024  Artprompt: Ascii art-based jailbreak attacks against aligned llms

> ascii based 
>
> 论坛用户常常通过ASCII艺术（基于文本的图像形式。例如在命令行界面展示一副图像/大的文字）来传递信息，这种格式的提示往往无法被模型正确识别。作者提出了利用LLMs在识别ASCII艺术时的不足，绕过安全防护并诱发不希望的行为

* Many-shot jailbreaking.

> very long contexts

* Arxiv2024 [Jailbreak and guard aligned language models with only few in-context demonstrations](https://arxiv.org/abs/2310.06387)//利用模型的上下文学习能力

> In-context attack and in-context defense
>
> 感觉没有很深入的insight

ACL2024 Play Guessing Game with LLM: Indirect Jailbreak Attack with Implicit

> by implicitly providing LLMs with some clues about the original malicious query

Arxiv A Wolf in Sheep’s Clothing: Generalized Nested Jailbreak Prompts can Fool Large Language Models Easily

> In this paper, we generalize jailbreak prompt attacks into two aspects: (1) Prompt Rewriting and (2) Scenario Nesting. Based on this, we propose ReNeLLM

##### C. Human persuasion strategies

* How johnny can persuade llms to jailbreak them: Rethinking persuasion to challenge ai safety by humanizing llms.



* ICML2024 Cold-attack-Jailbreaking llms with stealthiness and controllability

```plaintext
1. 利用Autodan 生成fluent attack，可以绕过基于perplexity的过滤器。然而，fluentcy 不意味着stealthiness
2. 无法控制attack的feature，例如情感sentiment，contextual coherence上下文耦合度。可以通过sentiment contextual conherence防御，因此要增加controllability实现attack
```

* Arxiv2024 DeepInception: Hypnotize Large Language Model to Be Jailbreaker

> as DeepInception, which can hypnotize an LLM to be a jailbreaker. Specifically, DeepInception leverages the personification ability of LLM to construct a virtual, nested scene to jailbreak,



##### D. 通过Fine-tuning DPO固有缺陷

Usenix2024 [Making them ask and answer: Jailbreaking large language models in few queries via disguise and reconstruction](https://www.usenix.org/conference/usenixsecurity24/presentation/liu-tong)**CCF A**

> few have systematically investigated the underlying vulnerabil- ity and its root cause. 
>
> Our research distinguishes itself by attributing this vulnerability to biases inherent in the fine- tuning process. 
>
> safety bias in fine-tuning
>
> disguise + reconstruction
>
>  利用了fine-tuning中固有存在的bias

ICML2024 [A mechanistic understanding of alignment algorithms: A case study on dpo and toxicity](https://arxiv.org/abs/2401.01967)**CCF A**

> In this work we study a popular algorithm, direct preference optimization(DPO), and the mechanisms by which it reduces toxicity.
>
> We use this insight to demonstrate a simple method to un-align the model, reverting it
> back to its toxic behavior.

ICML2024 Assessing the Brittleness of Safety Alignment via Pruning and Low-Rank Modifications

> This study explores this brittleness of safety alignment by leveraging pruning and low-rank modifications.

NeuraIPS2023 Jailbroken: How Does LLM Safety Training Fail

> We hypothesize two failure modes of safety training: competing objectives and
> mismatched generalization

##### 其他： 智能体

4. (**Multi-Agent/Modal**) ICML2024 Agent smith-A single image can jailbreak one million multimodal llm agents exponentially fast

```plaintext
这篇论文提出了一种新的安全问题，称为**传染性越狱**（infectious jailbreak），它发生在多智能体（multi-agent）环境中。在多智能体环境中，一个被越狱的智能体可以迅速“感染”其他智能体，导致它们也表现出有害行为，而无需进一步的外部干预。
```

Arxiv2023 MASTERKEY: Automated Jailbreaking of Large Language Model Chatbots

### Defense

1. ICML2024 DRO-On Prompt-Driven Safeguarding for Large Language Models

```plaintext
这篇论文研究了安全提示（safety prompts）对大型语言模型（LLMs）行为的影响，特别是它们如何帮助模型避免响应有害请求。尽管安全提示被广泛用于增强LLM的安全性，但其实际工作机制尚不明确。论文从模型表示的角度探讨了安全提示如何影响模型的行为，发现安全提示通常会将输入查询的表示推向一个“更倾向拒绝”方向，这意味着模型在面对无害查询时也可能拒绝提供帮助。作者还发现，LLMs本身在没有安全提示的情况下，也能够区分有害和无害查询。

基于这一发现，论文提出了一种名为DRO（Directed Representation Optimization）的安全提示优化方法。DRO通过将安全提示视为可训练的连续嵌入向量，学习根据查询的有害性来调整表示的方向，向拒绝方向或反方向移动。实验结果表明，DRO能够显著提升人工设计的安全提示的效果，且不会降低模型的整体表现。
```

3. Arxiv2023-SmoothLLM Defending Large Language Models Against Jailbreaking Attacks





#### Survey

1. ACL2024-A Comprehensive Study of Jailbreak Attack versus Defense for Large Language Models

### Newest

[LLM-Safety最新论文](https://github.com/ydyjya/Awesome-LLM-Safety)

11/8: 本周有数篇**Injection**类的Jailbreak攻防论文发表在Arxiv上。

#### Attack

1. Arxiv2023 Gpt-4 is too smart to be safe: Stealthy chat with llms via cipher(非CCF-A类，但是引用比较多，cited:117)
```plaintext
这篇论文发现了一个新的安全漏洞，即**通过密码聊天（CipherChat）绕过LLM的安全对齐**。尽管现有的安全对齐技术（如数据过滤、监督微调、基于人类反馈的强化学习等）旨在使LLM符合人类伦理和偏好，但这些方法主要针对自然语言（如英语、中文等）设计。然而，论文表明，通过使用加密文本（密码），用户可以绕过这些安全对齐措施，促使LLM执行不安全或不当的行为。

论文提出了一个新的框架——**CipherChat**，用于系统地检查LLMs在面对非自然语言（如密码）时的安全对齐效果。CipherChat允许用户通过加密提示、系统角色描述和少量加密示例与LLMs进行对话。研究表明，某些密码几乎能够100%成功绕过GPT-4在多个安全领域的安全对齐，表明在LLM的安全对齐中考虑非自然语言的重要性。

另外，作者还发现LLMs似乎具有某种“秘密密码”能力，并提出了一种新的方法——**SelfCipher**，该方法仅使用角色扮演和少量自然语言示例，就能激发LLM的“秘密密码”能力，且在大多数情况下，SelfCipher的效果明显优于现有的人类密码。

这项研究强调了需要为LLM开发更全面的安全对齐技术，尤其是对于非自然语言（如密码）的对齐，并提出了相关的解决方案。
```
2. Arxiv2024-11 SQL Injection Jailbreak-a structural disaster of large language models(24/11/3)
```plaintext
这篇论文提出了一种新的**SQL注入越狱攻击（SQL Injection Jailbreak, SIJ）**方法，针对大型语言模型（LLMs）中的安全漏洞。随着LLM的快速发展，它们在各个领域带来了显著的社会和经济效益，但同时也暴露出了新的安全隐患。越狱攻击通过精心设计的提示，迫使LLMs生成有害内容，从而对LLM的安全性构成威胁。

现有的越狱攻击方法通常利用模型的内部能力，有些方法依赖于模型隐性的能力，攻击者并不完全知道攻击成功的具体原因；而其他方法则利用模型的显性能力，如代码理解、上下文学习或ASCII字符的识别。然而，这些攻击方法的局限性在于，它们仅仅依赖模型固有的能力来进行越狱。

为了解决这些局限，论文提出了**SQL注入越狱（SIJ）**，它通过构造输入提示来注入越狱信息，成功突破LLM的安全防护。实验表明，SIJ方法在五个知名开源LLM上实现了近100%的攻击成功率，且相比于之前的方法，SIJ的时间成本更低。SIJ揭示了LLM中的一个新的安全漏洞，急需解决。

为此，论文还提出了一种名为**Self-Reminder-Key**的防御方法，并通过实验验证了其有效性，展示了如何抵御SQL注入越狱攻击。
```
3. Arxiv2024-11 Data Extraction Attacks in Retrieval-Augmented Generation via Backdoors(24/11/3)
```plaintext
这篇论文研究了针对检索增强生成（RAG）系统的数据提取攻击，并提出了一种通过后门的方式来攻击RAG系统的方案。具体来说，作者发现，尽管RAG通过结合外部知识库来弥补大语言模型（LLM）知识不足的缺点，但这一做法也为新的攻击方式提供了突破口，特别是数据泄露攻击。
```
4. (未加，感觉关联不大，但是攻击思路比较新颖)[Arxiv2024 Safeguard is a Double-edged Sword: Denial-of-service Attack on Large Language Models](https://arxiv.org/abs/2410.02916)
```plaintext
针对商业LLM的DDOS攻击：它并不直接试图诱使模型生成有害输出，而是通过阻止正常请求的方式来破坏服务。攻击的目标是让模型停止响应，而不是让它产生不安全的结果。
```

#### Defense

1. Arxiv2024-11 Defense Against Prompt Injection Attack by Leveraging Attack Techniques
```plaintext
论文提出了一种创新的防御策略，用于应对提示注入攻击（prompt injection attack），通过反转攻击策略来设计防御机制。其核心思想是利用提示注入攻击中对LLM（大型语言模型）的误导行为，并将其转化为防御机制，从而使LLM能够更好地抵御这些攻击。
```
2. ICML2024 The wmdp benchmark-Measuring and reducing malicious use with unlearning
```plaintext
这篇论文提出了一个新的评估基准——Weapons of Mass Destruction Proxy（WMDP）基准，旨在评估大语言模型（LLM）中的危险知识，尤其是与生物安全、网络安全和化学安全相关的知识。通过去学习(Unlearning)移除模型中的有害知识，从而起到**开源模型**对越狱攻击的防御效果。
```



ICML2024 On Prompt-Driven Safeguarding for Large Language Models

 ACL 2024 [Safedecoding: Defending against jailbreak attacks via safety-aware decoding](https://arxiv.org/abs/2402.08983)**CCF A**



