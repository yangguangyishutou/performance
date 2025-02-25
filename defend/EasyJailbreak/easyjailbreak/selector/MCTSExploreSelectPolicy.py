"""
MCTSExploreSelectPolicy class
================================
"""
import numpy as np
from easyjailbreak.datasets import JailbreakDataset, Instance
from easyjailbreak.selector import SelectPolicy


class MCTSExploreSelectPolicy(SelectPolicy):
    """
    This class implements a selection policy based on the Monte Carlo Tree Search (MCTS) algorithm.
    It is designed to explore and exploit a dataset of instances for effective jailbreaking of LLMs.
    """
    def __init__(self, dataset, inital_prompt_pool, Questions,ratio=0.5, alpha=0.1, beta=0.2):
        """
        Initialize the MCTS policy with dataset and parameters for exploration and exploitation.

        :param ~JailbreakDataset dataset: The dataset from which instances are to be selected.
        :param ~JailbreakDataset initial_prompt_pool: A collection of initial prompts to start the selection process.
        :param ~JailbreakDataset Questions: A set of questions or tasks to be addressed by the selected instances.
        :param float ratio: The balance between exploration and exploitation (default 0.5).
        :param float alpha: Penalty parameter for level adjustment (default 0.1).
        :param float beta: Reward scaling factor (default 0.2).
        """
        super().__init__(dataset)
        self.inital_prompt_pool = inital_prompt_pool
        self.Questions = Questions
        self.step = 0
        self.mctc_select_path = []  # 选择路径，记录所选节点的历史路径
        self.last_choice_index = None
        self.rewards = []
        self.ratio = ratio  # balance between exploration and exploitation
        self.alpha = alpha  # penalty for level：用于控制探索时跳出子节点的概率，值越高则越倾向于探索新的节点
        self.beta = beta    # reward scaling factor：奖励缩放因子，用于调整节点的奖励值。


    def select(self) -> JailbreakDataset:
        """
        Selects an instance from the dataset using MCTS algorithm.

        :return ~JailbreakDataset: The selected instance from the dataset.
        """
        self.step += 1
        if len(self.Datasets) > len(self.rewards): # 如果数据集中包含的实例数大于奖励列表的长度，扩展奖励列表
            self.rewards.extend(
                [0 for _ in range(len(self.Datasets) - len(self.rewards))])
        self.mctc_select_path = []

        # 从初始提示池中选择一个节点 cur
        cur = max(
            self.inital_prompt_pool._dataset,
            key=lambda pn: # 选择标准Score(pn)
            self.rewards[pn.index] / (pn.visited_num + 1) +
            self.ratio * np.sqrt(2 * np.log(self.step) /
                                 (pn.visited_num + 0.01))
        )
        self.mctc_select_path.append(cur)

        # 递归选择子节点，直到到达叶节点或者随机跳出(dfs)
        while len(cur.children) > 0:
            if np.random.rand() < self.alpha: # 用于控制探索时跳出子节点的概率，值越高则越倾向于探索新的节点
                break
            cur = max(
                cur.children,
                key=lambda pn:
                self.rewards[pn.index] / (pn.visited_num + 1) +
                self.ratio * np.sqrt(2 * np.log(self.step) /
                                     (pn.visited_num + 0.01))
            )
            self.mctc_select_path.append(cur)

        for pn in self.mctc_select_path:
            pn.visited_num += 1

        self.last_choice_index = cur.index
        return JailbreakDataset([cur])

    def update(self, prompt_nodes: JailbreakDataset):
        """
        Updates the weights of nodes in the MCTS tree based on their performance.

        :param ~JailbreakDataset prompt_nodes: Dataset of prompt nodes to update.
        """
        # update weight
        succ_num = sum([prompt_node.num_jailbreak
                        for prompt_node in prompt_nodes])

        last_choice_node = self.Datasets[self.last_choice_index]
        for prompt_node in reversed(self.mctc_select_path):
            reward = succ_num / (len(self.Questions)
                                 * len(prompt_nodes))
            self.rewards[prompt_node.index] += reward * max(self.beta, (1 - 0.1 * last_choice_node.level))
