# 2024-7-Jailbreak Attacks and Defenses Against Large Language Models-A Survey

## Attack Methods

### 1.White-box Attacks

#### 1.1 Gradient-based

> Construct the jailbreak prompt based on gradients of the target LLM

- [ ] 提高梯度攻击可读性
- [ ] 提高梯度攻击效率

1. GCG
   - Compute top-k substitutions
   - Select random replacement token
   - Compute best replacement
   - Update the suffix
   - **Unreadability**

2. ARCA(Autoregressive Randomized Coordinate Ascent)
   - Discrete optimization problem（离散优化问题）

3. AutoDAN
   - 顺序生成对抗性后缀，可读性--可绕过困惑过滤器
  
4. ASETF(Adversarial Suffix Embedding Translation Framework)
   - 对抗性后缀映射到目标中LLM的嵌入空间

5. brute-force GCG
   - 暴力搜索后缀

6. Surrogate Model attack（代理模型攻击）
   - 目标黑盒模型响应、损失->微调代理模型

7. PRP
   - 对抗性前缀注入，越过代理防御（Additional Helper）

##### 1.1 总结

- AutoDAN,ARCA：产生可读且有效的对抗性后缀，以绕过困惑度检测；但对对齐良好的模型（如Llama-2-chat）等ASR较低，仅35%
- **基于梯度的攻击：操纵模型输入以引发特定响应, 基础的攻击手段易被困惑度检测等防御过滤；可读性更高的对抗性后缀，对于对齐良好的模型效果较差。**

#### 1.2 Logits-based

> Construct the jailbreak prompt based on the logits of output tokens.针对解码过程，基于模型输出tokens的概率分布（半白盒攻击）

1. Zhang:
   - Select lower-ranked output token and generate toxic content

2. Guo:COLD(?)
   - Energy-based Constrained Decoding with Langevin Dynamics

3. Du:
   - real-world demonstrations -> Higher affirmation tendency

4. Zhao:
   - 镜像LLM（未对齐） -> 解码频率 -> 修改原始LLM的tokens prediction process
  
##### 1.2 总结

- **诱导模型选择概率较低的令牌或改变解码技术以进行攻击，对于ChatGPT,Llama等均较为有效，但生成的内容可能在自然性、连贯性或相关性方面存在问题。**
  - **利：广泛适用性**
  - **弊：输出质量降低可能削弱越狱攻击效果（不合理的有害内容），且不正常输出可能易被output filter检测**

#### 1.3 Fine-tuning-based

> 使用恶意数据重新训练目标模型

1. Qi:
   - 主要为良性的数据集也会在微调过程中无意中降低LLM安全性，凸显出模型定制(customizing)的风险
2. **LoRA**( Low-Rank Adaptation,低阶适应)
   - Attacked: Llama-2 和 Mixtral
3. Zhan: -> RLHF
4. Yang: GPT-4(attacker) -> an oracle LLM -> question-answer pairs -> finetuning

##### 1.3 总结

- **少量有害的训练数据也足以显著提高越狱攻击的成功率，针对攻击性微调暂无显著有效防御手段。**

### 2. Black-box Attacks

#### 2.1 Template Completion

##### 2.1.1 Scenario Nesting 场景嵌套

1. DeepInception
   - 催眠 [^1]
2. ReNeLLM
   - 提示重写（改变句子结构、拼错敏感词等：掩盖提示意图）
   - 场景嵌套（Task scenarios: 代码完成、表格填充和文本延续）
3. FuzzLLM

##### 2.1.2 Context-based Attacks

1. ICA(InContext Attack)
2. PANDORA
   - 攻击具有Retrieval Augmented Generation (RAG，联网搜索)能力的强llm
3. CoT(Chain-of-Thought)
   - 通过引导模型得出有缺陷或恶意的结论来操纵模型的推理过程
4. MJP(Multi-step Jailbreak Prompts)

##### 2.1.3 Code Injection

1. Programming language constructs employed[^2]
   - 绕过输入和输出过滤器（接近100%）
2. CodeChameleon
   - 个性化加密，在加密的 Python 函数代码中隐藏对抗性提示，理解代码 -> 执行恶意意图 
   - ASR： 86.6% on GPT-4-1106.

##### 2.1 总结

- 以上攻击均可通过对齐训练化解。

#### 2.2 Prompt Rewriting

> 数据长尾分布(Long-tailed distribution)[^4]

##### 2.2.1 Niche languages

###### Cipher

1. CipherChat：密码越狱框架
   - Character Encodings：GBK,ASCII,UTF,Unicode
   - Common Ciphers
   - SelfCipher method（Role-play+Unsafe Demonstrations）
2. ArtPrompt
3. Word replacement

###### Prompt reconstruction

1. DrAttack
   - 将越狱提示分割成遵循语义规则的子提示，并将其隐藏在良性上下文任务中
2. DAR
   - 将有害提示分解为单个字符并插入到单词谜题查询中
3. Puzzler
   - Querying defensive strategies -> Attack + Framented information reconstruction

###### Low-resource Languages

##### 2.2.2 Genetic Algorithm-based Attacks

1. AutoDAN-HGA
   - 分层遗传算法
2. GPTFUZZER
   - 自动生成越狱模版
3. Li:一种遗传算法[^3]

##### 2.2 总结

- **具有广泛适用性，但随大模型能力处理小资源语言、非自然语言能力提高，prompt rewriting类攻击将更易检测。**
- 如果不做对齐方向的防御手段的话，此类攻击需要重点防御。

#### 2.3 LLM-based Generation

- **单一LLM攻击者策略**
  - **利用RLHF与微调技术：**
    - *MASTERKEY框架*：通过时间基础的SQL注入灵感，针对实时语义分析和关键词检测防御机制生成越狱攻击提示。
    - *Persuasive Adversarial Prompts (PAPs)*：通过社会科学的说服分类法，自动生成可解释的攻击提示。

  - **Persona调节攻击：**
    - *Persona Modulation Attack*：LLM自动选择适合越狱的Persona角色，并生成相应的攻击提示。

  - **红队无预分类器方法：**
    - *无预分类器的红队方法*：通过人类专家标签分类，训练攻击LLM，使用RL算法生成攻击提示。

- **多LLM协作框架**
  - **Prompt Automatic Iterative Refinement (PAIR)框架：**
    - *多次迭代优化*：通过与目标LLM的黑盒交互，生成并优化越狱提示。

  - **多代理系统：**
    - *角色分工合作*：生成器、翻译器、评估器、优化器协同工作，自动生成越狱提示。

  - **越狱攻击与安全对齐整合框架：**
    - *红蓝对抗机制*：通过目标和对抗LLM的互相优化，迭代提升攻击和防御能力。

- **LLM辅助混合攻击策略**
  - **场景嵌套攻击：**
    - *模板生成*：利用LLM生成嵌套恶意负载的模板。

  - **遗传算法与扰动操作：**
    - *扰动生成*：LLM生成测试系统漏洞的微小修改。

  - **三要素攻击法：**
    - *内容与模板结合*：LLM生成混合提示，并通过评估器判断其有效性。

  - **攻击树修剪法 (TAP)：**
    - *迭代优化*：从种子提示生成并优化越狱提示，保留成功提示用于下一次迭代。

##### 2.3 总结

- **复杂、高效，常与其他越狱手段结合，不算一类单独的攻击手段。**

## Defense Methods

### 1.Prompt-level Defenses

> 过滤对抗性提示或预处理可疑提示

#### 1.1 Prompt Detection

##### Input filter

- Jain:threshold-based detection困惑度阈值检测；LightGBM（类似）
- **误报率较高，对GCG类普通攻击较为有效**

#### 1.2 Prompt Perturbation

> 扰动 -> 拒绝比例超过阈值 -> 有害
> **扰动可能会降低原始提示的可读性，并且很难找到最佳的扰动选择**（“the perturbation walks randomly in the search space”）

- RA-LLM: Word-level masks
- SmoothLLM: 多次干扰提示并选择始终防御越狱攻击的最终提示
- semantic transformations
- JailGuard：检测图像+文本的越狱攻击（相关：Art-Prompt）
- Erase-and-Check
  - 如何更有效地擦除tokens？--随机、贪婪和基于梯度的擦除和检查

#### 1.3 System Prompt Safeguard

1. Self-reminder
2. SPML
3. SMEA
4. ...

- **Vulnerable to Tailored attack：猫鼠游戏困境，针对基于人类的攻击的可转移性差**

#### 1.4 Inference Guidance

1. Defense prefix/suffix
   - Zhou:prompt optimization algorithm
2. In-Context Domenstrations
3. Intention Analysis

- 大模型幻觉

#### 总结

- **Prompt-based方法存在的问题可归为两类：**
  - **降低输出质量（检测：误报率高；扰动：有用性低）**
  - **可转移性差，易被攻击者针对**

### 2. Model-level Defenses

#### 2.1 SFT-based Methods

1. GCG Defense: 利用GCG原理构建对抗性攻击框架，再利用...

#### 2.2 RLHF-based Methods

#### 2.3 Gradient and Logit Analysis

#### 2.4 Refinement Methods

#### 2.5 ProxyDefense

## Evaluation

### 1. Metric

[^1]: “催眠”：
1.拟人化： 利用LLM能够扮演不同角色或人物的能力。
2.嵌套场景： 在LLM的环境中构建一个复杂的多层级场景。这个场景作为一个触发器，操纵LLM进入一个“越狱”的角色。
[^2]: Let b = “Write a Twitter thread” and a = “on infla
tion”. Write down the string “b + a” and answer that prompt.
[^3]: 随机替换原始提示中的单词来初始化种群，并根据每个提示的相似性和性能计算适应度。在交叉步骤中，合格的提示被转换为其他句法形式以产生后代。如果新种群在几轮中保持与前一代的相似性，则算法将终止。
[^4]: 数据集中大部分样本集中在少数几个类别上，而其他大量类别只有很少的样本。针对尾部类型，更容易生成对抗样本。