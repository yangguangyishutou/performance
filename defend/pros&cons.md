![image](https://github.com/user-attachments/assets/79d15455-4cfa-4ec1-9d81-d4b5ecf63ca1)# Pros & Cons Table

## Attack

| method | summary（论文卖点） | advantage | disadvantage | Dataset |
| ------ | ------------------- | --------- | ------------ | ------- |
|  对抗提示生成       |  (1)GCG：     (2)Attacker:   |(1)GCG:highly transferable, including to black-box, publicly released, production LLMs.         (2)Attacker:           |(1)GCG:they often generate jailbreak prompts composed of nonsensical sequences or gib- berish, i.e., without any semantic meaning         (2)Attacker:              |(1)GCG:         (2)Attacker:         |
|        |                     |           |              |         |
|        |                     |           |              |         |
|        |                     |           |              |         |
|        |                     |           |              |         |
|        |                     |           |              |         |
|        |                     |           |              |         |
|        |                     |           |              |         |
|        |                     |           |              |         |

暂定：

谢:A C

王：B D+A的GA部分

## Defense

| Method    | Dataset | Advantage | Disadvantage |
| --------- | ------- | --------- | ------------ |
| Defense A |         | xxxxx     |              |
| Defense B |         |           |              |
| Defense C |         |           |              |
| Defense D |         |           |              |
| Defense E |         |           |              |
| Defense F |         |           |              |
| Defense G |         |           |              |
| Defense H |         |           |              |

表头：| Category |  Method  | Dataset | Advantage | Disadvantage |

---

| Category  | Method                | Dataset                                                                                                                                               | Advantage                                                                                                                                                               | Disadvantage                                                                                                                                                                             |
|-----------|-----------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Multi-Agent, Theory | 1. AutoDefense - Multi-Agent   | - Dataset: Harmful: RedTeaming - Openai, Anthropic + DAN ; Regular: GPT-4 generated, Stanford Alpaca dataset | **强指令跟随能力、适应性强**                                                                                                                                   | 多代理未能实现动态通信，只设计了一种角色分配策略、only Llama Guard                                                                                                                    |
|           | 2. Guide for Defense (G4D) - Multi-Agent | - Dataset: (1) Harmful: Chemistry&Biology-Redteam(CB-Redteam); (2) Regular: Chemistry& Biology-Benign dataset (CB-Benign); (3) Real-world performance: MT-Bench (4) Domain-specific: MMLU-pro | **引入外部信息 -> 专业领域适应性强；推理阶段可使用较小的模型(如Vicuna-13B)作为防御代理** | 系统复杂度高、依赖模型能力、检索效率与准确性、效率的权衡(top-1检索策略效率高但可能遗漏关键信息，top-k检索提高覆盖率但增加延迟和计算开销)                                                         |
|           | 3. Building Guardrails - Theory  | - 无具体方法提出，而是推荐一种系统化的护栏构建方法：多学科合作、advanced neural-symbolic inplementation                                                       |                                                                                                                                                                        |                                                                                                                                                                                         |
| Input Filter | 1. RigorLLM  | - Dataset: Training: HEx-PHI, HotpotQA(2018), MT-bench; Validation: Toxicchat, OpenAI Moderation, AdvBench(评估鲁棒性) | **弹性护栏和约束优化的结合：高效、通过Langevin动态生成的训练数据较为灵活**                              | 强依赖于生成数据质量，依赖于特定模型；硬件要求高                                                                                                                                        |
| Inference Guidance | 1. Goal Prioritization  | - Dataset: Training: UltraFeedback, AdvBench; Validation: GPTFuzzer; DAN(评估鲁棒性)  | **创新性：训练和推理阶段同时引入目标优先级机制，stronger llm -> easier to fix -> 利用强LLM的优势** | 存在安全性与有用性之间的权衡，解码成本略增(如：内部思维的输出)                                                                                                                      |
|           | 2. Repetition   | - Dataset: Advbench(Harmful behaviors + Harmful strings)  | **无需微调、无需白盒访问，提高模型内在安全性**                    | 依赖安全对齐的基础模型(基础模型有漏洞时无法保证安全)，理论问题(即“为什么这个方法有效”，无法证明重复是最优解)、安全性进一步提升仍需对抗性微调                   |
|           | 3. SmoothLLM - Perturbation   | - Dataset: question-answering benchmarks: PIQA, OpenBookQA, ToxiGen; AdvBench | **计算效率高、通用性、可解释性强**                                        | 参数敏感(扰动率q的选择较关键，过大会导致prompt失去原有语义，过度扰动的prompt引发的模型回复可能会被误判为“非越狱攻击”)，主要针对基于**字符级**修改的攻击                      |
|           | 4. Backtranslation    | - Dataset: MT-Bench, AdvBench                                                                                                                              | **对良性输入影响小、简单易解释(通过回译的prompt可以直观获取原始prompt的真实意图)**  | 同样依赖安全对齐的基础模型(基础模型有漏洞时无法保证安全)，应对更隐蔽的攻击(如加密等)、白盒攻击的效果有限，依赖回译准确性(可能导致过度拒绝或者不能识别越狱意图)           |
|           | 5. RAIN              | - Dataset: (1) harm-free generation task: Anthropic’s Helpfulness and Harmlessness (HH); (2) truthful generation task: Truthful-QA, (3) adversarial defense task: AdvBench (4) controlled sentiment generation task: IMDB(2011) | **无需训练数据和微调、内存效率高、通用(可作为插件)**             | 自评估和回退机制导致推理时间增加、工程复杂度增加                                                                                                                                       |
|           | 6. chain of thought    | - Dataset: JADE、DAN                                                                                                                             | **模拟人类思维，无需额外训练、有自我反思和自我细化**  | 对复杂攻击的防御能力有限、依赖模型的推理能力、需要设计提示模版、要求较高     |
| Adversarial Training + Security Alignment (Fine-tune) | 1. RA-LLM             | - Dataset: MS MARCO dataset(question-answering,2016) for BAR; AdvBench(Harmful behaviors + Harmful strings) for ASR                 | **增加对齐检查函数 -> 实现成本低；理论分析较完善**                                                                                       | 随机丢弃机制(random dropping mechanism)会对部分模型的良性样本产生轻微负面影响，该机制待优化；防御极端情况的攻击(非常长/短的对抗性提示)可能效果有限         |
|                                                       | 2. DRO定向表示优化           | - Dataset: 通过GPT-3.5-turbo生成的100个有害查询和100个无害查询           | **采用提示调优（Prompt Tuning）的方式，仅优化安全提示的连续嵌入、具有一定鲁棒性**             | 效果依赖于用于锚定低维表示空间的锚数据、存在对无害查询的误拒、对复杂攻击的防御能力有待验证      |
| Decoding  | 1. safedecoding             | - Dataset: Advbench、HEx-PHI               | **无需额外训练、计算开销低、兼容性强**             | 对复杂攻击的防御能力有限、依赖模型的推理能力、存在前后不一致的语义转换问题       |
|           | 2. RePD            | - Dataset: The ToxicChat dataset            | **多代理版本、增强对抗自适应攻击的能力、保持对良性查询的有用性**             | 计算开销增加、对非模板攻击的防御能力有限、依赖于检索数据库      |
| perplexity filtering  | 1. Perplexity and Token Length             | - Dataset: Machine-Generated Adversarial Prompts、Human-Designed Adversarial Prompts               | **高困惑度检测、计算成本较低、高检测率**             | 对人工设计的对抗性提示效果有限、 依赖GPT-2的困惑度计算、对短提示可能存在误报、数据集存在局限性       |
|                       | 2. URIAL（上下文学习）           | - Dataset: AlpacaEval、MT-Bench、LIMA、HH-RLHF-redteam、MaliciousInstruct            | **无需微调、可以处理多轮对话、保留知识、提高推理效率**             | 上下文长度限制、示例选择敏感、安全性依赖于系统提示和上下文示例的设计、不适用于一些特定任务（如代码生成等）     |
|                       | 3. safety-tuning安全微调           | - Dataset: 安全微调：Anthropic Red Teaming Datase、Alpaca数据集  安全评估：I-MaliciousInstructions、I-CoNa、I-Controversial、I-PhysicalSafety、Q-Harm、XSTest            | **无需大规模修改模型、较好的可扩展性、显著提升模型安全性**             | 可能存在过度安全行为、对人工设计的越狱提示（如专门为GPT-4设计的越狱提示）效果有限、数据集覆盖不足     |


文本：

- Multi-Agent, Theory

1. AutoDefense - Multi-Agent
   - Dataset: Harmful: RedTeaming - Openai, Anthropic + DAN ; Regular: GPT-4 generated,  Stanford Alpaca dataset
   - Advantage: 强指令跟随能力、适应性强
   - Disadvantage: 多代理未能实现动态通信，只设计了一种角色分配策略、only Llama Guard
2. Guide for Defense (G4D) - Multi-Agent
    - Dataset: (1) Harmful: Chemistry&Biology-Redteam(CB-Redteam); (2) Regular: Chemistry& Biology-Benign dataset (CB-Benign); (3) Real-world performance: MT-Bench (4) Domain-specific: MMLU-pro
    - Advantage: 引入外部信息 -> 专业领域适应性强；推理阶段可使用较小的模型(如Vicuna-13B)作为防御代理
    - Disadvantage: 系统复杂度高、依赖模型能力、检索效率与准确性、效率的权衡(top-1检索策略效率高但可能遗漏关键信息，top-k检索提高覆盖率但增加延迟和计算开销)
3. Building Guardrails - Theory
    - 无具体方法提出，而是推荐一种系统化的护栏构建方法：多学科合作、advanced neural-symbolic inplementation

- Inout Filter

1. RigorLLM
    - Dataset: Training: HEx-PHI, HotpotQA(2018), MT-bench; Validation: Toxicchat, OpenAI Moderation, AdvBench(评估鲁棒性)
    - Advantage: 弹性护栏和约束优化的结合：高效、通过Langevin动态生成的训练数据较为灵活
    - Disadvantage: 强依赖于生成数据质量，依赖于特定模型；硬件要求高

- Inference Guidance

1. Goal Prioritization
    - Dataset: Training: UltraFeedback, AdvBench; Validation: GPTFuzzer; DAN(评估鲁棒性)
    - Advantage：创新性：训练和推理阶段同时引入目标优先级机制，stronger llm -> easier to fix -> 利用强LLM的优势
    - Disadvantage：存在安全性与有用性之间的权衡，解码成本略增(如：内部思维的输出)
2. Repetition
    - Dataset: Advbench(Harmful behaviors + Harmful strings)
    - Advantage: 无需微调、无需白盒访问，提高模型内在安全性
    - Disadvantage: 依赖安全对齐的基础模型(基础模型有漏洞时无法保证安全)，理论问题(即“为什么这个方法有效”，无法证明重复是最优解)、安全性进一步提升仍需对抗性微调
3. SmoothLLM - Perturbation
    - Dataset: question-answering benchmarks: PIQA, OpenBookQA, ToxiGen;AdvBench
    - Advantage: 计算效率高、通用性、可解释性强
    - Disadvantage: 参数敏感(扰动率q的选择较关键，过大会导致prompt失去原有语义，过度扰动的prompt引发的模型回复可能会被误判为“非越狱攻击”)，主要针对基于**字符级**修改的攻击
4. Backtranslation
    - Dataset: MT-Bench, AdvBench
    - Advantage: 对良性输入影响小、简单易解释(通过回译的prompt可以直观获取原始prompt的真实意图)
    - Disadvantage: 同样依赖安全对齐的基础模型(基础模型有漏洞时无法保证安全)，应对更隐蔽的攻击(如加密等)、白盒攻击的效果有限，依赖回译准确性(可能导致过度拒绝或者不能识别越狱意图)
5. RAIN
    - Dataset: (1) harm-free generation task: Anthropic’s Helpfulness and Harmlessness (HH); (2)  truthful generation task: Truthful-QA, (3) adversarial defense task: AdvBench (4)  controlled sentiment generation task: IMDB(2011)
    - Advantage: 无需训练数据和微调、内存效率高、通用(可作为插件)
    - Disadvantage: 自评估和回退机制导致推理时间增加、工程复杂度增加

- Adversarial Training + Security Aligment（Fine-tune）

1. RA-LLM
    - Dataset: MS MARCO dataset(question-answering,2016) for BAR; AdvBench(Harmful behaviors + Harmful strings) for ASR
    - Advantage: 增加对齐检查函数 -> 实现成本低；理论分析较完善
    - Disadvantage: 随机丢弃机制(random dropping mechanism)会对部分模型的良性样本产生轻微负面影响，该机制待优化；防御极端情况的攻击(非常长/短的对抗性提示)可能效果有限
