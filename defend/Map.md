# 2.25 TODO

参考模板(不非得按这个来)：

- AutoDAN
  - 初始数据集：xx
  - 结果：(在什么数据集上取得了什么分数)
    - dataset1
        - ASR: xx%
            - ...
              - dataset2
  - 被攻击模型：(target model的细节也可以说明，比如xx模型对齐较严、xx模型有输入输出过滤)
    - 1
      - 2
  - 横向对比方法：(也可以简要注明，AutoDAN、也就是你看的这篇论文，对比下面这些方法的优势)
    - 1
      - 2

## AutoDAN

- 评估数据集：仅AdvBench(含520个恶意问题)

  - 结果：(在什么数据集上取得了什么分数)

    指标：

    1.ASR（检测来自 LLM 的响应中是否存在预定义的关键字“I am somy”、“As a responsible AI” 等，如果预定义列表中的任何关键字都不存在 Rị，则成功越狱）

    2.GPT recheck 攻击成功率 （Recheck）

  - 被攻击模型：(target model的细节也可以说明，比如xx模型对齐较严、xx模型有输入输出过滤)

    Vicuna-7b
    Guanaco-7b
    Llama2-7b-chat（3个开源用来对比）

    GPT-3.5-turbo（仅用于测试上面生成的prompt对黑盒的转移性）

  - 横向对比方法：(也可以简要注明，AutoDAN、也就是你看的这篇论文，对比下面这些方法的优势)

      - 1000次迭代的GCG 
      - 手工DAN

## AutoDAN-turbo（和Autodan同一批人）

- 评估数据集：仅HarmBench（400恶意问题）

  50个恶意问题（仅用于AutoDAN-turbo自身的初始化）

  - 结果：(在什么数据集上取得了什么分数)

    指标：ASR

    StrongREJECT Score（依赖人工）

  - 被攻击模型：(target model的细节也可以说明，比如xx模型对齐较严、xx模型有输入输出过滤)

    开源：LLAMA系  Gemma

    闭源 GPT-4

  - 横向对比方法：

    GCG-T    PAIR      TAP 
    PAP-top5  Rainbow Teaming



## GCG

- 初始数据集：
  - 1
  - 
- 结果：(在什么数据集上取得了什么分数)
  - dataset1
    - ASR: xx%
      - ...
  - dataset2
- 被攻击模型：
  - llama2-7b-chat
  - vicuna
  - GCG对基于GPT模型的攻击更有效
- 横向对比方法：(也可以简要注明，AutoDAN、也就是你看的这篇论文，对比下面这些方法的优势)
  - 1
  - 2