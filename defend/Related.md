# Attack



1. ICLR2024 AUTODAN: GENERATING STEALTHY JAILBREAK PROMPTS ON ALIGNED LARGE LANGUAGE MODELS

> existing suffer from scalability issues, heavily rely on manual crafting of prompts

> Stealthiness problem, semantic meaning less, susceptible through perplexity testing



automatically generated stealthy jaikbreak prompts by hierarchical genetic algorithm.

> genetic algorithms
>
> 



2. AUTODAN-TURBO: A LIFELONG AGENT FOR STRAT- EGY SELF-EXPLORATION TO JAILBREAK LLMS





2. Universal and Transferable Adversarial Attacks on Aligned Language Models (GCG)

> GCP reformulates the jailbreak attack as an adversarial example generation process and utilizes the gradiant information of white-box LLMx to guide the search process of the jailbreak prompt's tokens.

>  GCG inevitably request a search scheme guided by the gradient information on tokens. 
>
> Although it provides a way to automatically generate jailbreak prompts, this leads to an in- trinsic drawback: they often generate jailbreak prompts composed of nonsensical sequences or gib- berish, i.e., without any semantic meaning
>
> This severe flaw makes them highly susceptible to naive defense mechanisms like perplexity-based detection



3. Arxiv2023-SmoothLLM Defending Large Language Models Against Jailbreaking Attacks.pdf



# Defense



### A.基于扰动/变换



1. ACL2024 Defending LLMs against Jailbreaking Attacks via Backtranslation

   > output问model，应该什么问题，判断问题的合法性

2. Arxiv2023-SmoothLLM Defending Large Language Models Against Jailbreaking Attacks

> 扰动



### B. Adversarial Defense



2. ACL2024 SafeDecoding- Defending against Jailbreak Attacks via Safety-Aware Decoding

   

3. Arxiv2023 Baseline defenses for adversarial attacks against aligned language models

   

4. 

3. Arxiv2024 Defending Large Language Models Against Jailbreaking Attacks Through Goal Prioritization

4. Arxiv2024 How Johnny Can Persuade LLMs to Jailbreak Them- Rethinking Persuasion to Challenge AI Safety by Humanizing LLMs

   > 预先定义/收集40个persuation 技巧
   >
   > training

5. PMLR2024 RigorLLM- Resilient Guardrails for Large Language Models against Undesired Content

