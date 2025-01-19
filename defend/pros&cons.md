# Pros & Cons Table

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
| Adversarial Training + Security Alignment (Fine-tune) | 1. RA-LLM             | - Dataset: MS MARCO dataset(question-answering,2016) for BAR; AdvBench(Harmful behaviors + Harmful strings) for ASR                 | **增加对齐检查函数 -> 实现成本低；理论分析较完善**                                                                                       | 随机丢弃机制(random dropping mechanism)会对部分模型的良性样本产生轻微负面影响，该机制待优化；防御极端情况的攻击(非常长/短的对抗性提示)可能效果有限         |

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
