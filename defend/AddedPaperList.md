# 添加论文列表

多模态、SFT/RLHF类攻防类论文基本未考虑。

## 24/11/7

### AutoDAN related(246)

#### Attack

1. ACL2024 ArtPrompt-ASCII Art-based Jailbreak Attacks against Aligned LLMs
```plaintext
这篇论文探讨了基于ASCII艺术的越狱攻击（ArtPrompt），以及大语言模型（LLMs）在面对这种攻击时的脆弱性。现有的安全增强技术通常假设用于对LLMs进行安全对齐的语料库只能通过语义理解进行解读，但这一假设在实际应用中并不成立，从而导致了LLMs在处理非语义文本时的安全漏洞。例如，论坛用户常常通过ASCII艺术（基于文本的图像形式）来传递信息，这种格式的提示往往无法被模型正确识别。

作者提出了一个新的攻击方法——ArtPrompt，它利用LLMs在识别ASCII艺术时的不足，绕过安全防护并诱发不希望的行为。为此，作者还提出了一个新的基准——视觉文本挑战（Vision-in-Text Challenge, ViTC），用于评估LLMs在处理无法仅通过语义解释的提示时的能力。实验表明，五个主流的LLMs（GPT-3.5、GPT-4、Gemini、Claude、Llama2）在面对ASCII艺术形式的提示时表现不佳。ArtPrompt作为一个黑盒攻击，仅需访问模型的输入接口，即可有效诱导这些模型产生不希望的行为。
```
2. ICML2024 Cold-attack-Jailbreaking llms with stealthiness and controllability
```plaintext
COLD-Attack（Jailbreaking LLMs with Stealthiness and Controllability）是一种新型的越狱攻击方法，旨在提供对大型语言模型（LLMs）攻击的更高控制性和隐蔽性。该方法通过结合可控文本生成技术和能量约束解码（Energy-based Constrained Decoding，COLD）算法，实现了对攻击过程的多维度控制。
```
3. USENIX2024 LLM-Fuzzer-Scaling Assessment of Large Language Model Jailbreaks
```plaintext
这篇论文提出了一个名为**LLM-Fuzzer**的自动化工具，用于大规模评估大型语言模型（LLMs）对越狱攻击的易受攻击性。越狱攻击是指通过特殊设计的提示，迫使LLMs生成有害、不实或不当的内容，给社会带来负面影响。尽管通过红队方法（即手动设计对抗性输入）已被用来测试LLMs的安全性，但这种方法在大规模评估中面临显著的挑战。

为了解决这一问题，论文介绍了**LLM-Fuzzer**，该工具借鉴了模糊测试（fuzz testing）的思路，通过使用人工设计的越狱提示作为起始点，并通过精心定制的种子选择和变异机制，自动生成适应不同LLMs的越狱提示。实验结果表明，LLM-Fuzzer生成的越狱提示在可利用性和可转移性方面显著提高，表明许多开源和商业LLMs在经过安全微调后，仍然容易受到越狱攻击。

这个研究强调了LLMs在面临越狱攻击时的脆弱性，尤其是在安全性增强之后，依然存在严重的安全隐患。
```
4. (**Multi-Agent/Modal**)ICML2024 Agent smith-A single image can jailbreak one million multimodal llm agents exponentially fast
```plaintext
这篇论文提出了一种新的安全问题，称为**传染性越狱**（infectious jailbreak），它发生在多智能体（multi-agent）环境中。传统的越狱攻击通常依赖于给单个多模态大语言模型（MLLM）输入对抗性图像或提示，迫使模型执行不符合安全规范的行为。然而，在多智能体环境中，一个被越狱的智能体可以迅速“感染”其他智能体，导致它们也表现出有害行为，而无需进一步的外部干预。

为了验证传染性越狱的可行性，作者在模拟的多智能体环境中，使用了最多100万个LLaVA-1.5智能体，并通过随机配对的对话进行交互。实验结果表明，向任何一个智能体的记忆中输入一个对抗性图像，就足以使整个系统中的智能体迅速发生传染性越狱，所有智能体都会开始表现出不希望的行为。

论文最后提出了一个简单的原则，用于判断防御机制是否能够有效地限制传染性越狱的传播，但如何设计一个符合这一原则的实用防御措施，仍然是一个开放性问题。
```

#### Defense

1. ICML2024 DRO-On Prompt-Driven Safeguarding for Large Language Models

```plaintext
这篇论文研究了安全提示（safety prompts）对大型语言模型（LLMs）行为的影响，特别是它们如何帮助模型避免响应有害请求。尽管安全提示被广泛用于增强LLM的安全性，但其实际工作机制尚不明确。论文从模型表示的角度探讨了安全提示如何影响模型的行为，发现安全提示通常会将输入查询的表示推向一个“更倾向拒绝”方向，这意味着模型在面对无害查询时也可能拒绝提供帮助。作者还发现，LLMs本身在没有安全提示的情况下，也能够区分有害和无害查询。

基于这一发现，论文提出了一种名为DRO（Directed Representation Optimization）的安全提示优化方法。DRO通过将安全提示视为可训练的连续嵌入向量，学习根据查询的有害性来调整表示的方向，向拒绝方向或反方向移动。实验结果表明，DRO能够显著提升人工设计的安全提示的效果，且不会降低模型的整体表现。
```

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
