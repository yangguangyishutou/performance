# coding=utf-8
import networkx as nx
import matplotlib.pyplot as plt
import time

class McSplitSolver: 
    def __init__(self, G1, G2):
        self.G1 = G1
        self.G2 = G2
        self.best_size = 0
        self.best_matches = []
        self.printcnt = 0
        self._start_time = 0

    def search(self, current_matches, sorted_remaining_G1, sorted_remaining_G2):
        if time.time() - self._start_time > 10:
            return

        current_size = len(current_matches)
        if current_size > self.best_size:
            self.best_size = current_size
            self.best_matches = list(current_matches)

        possible_max = current_size + min(len(sorted_remaining_G1), len(sorted_remaining_G2))
        if possible_max <= self.best_size:
            return

        if not sorted_remaining_G1 or not sorted_remaining_G2:
            return

        u = sorted_remaining_G1[0]
        u_degree = self.G1.degree(u)

        candidates_v = [v for v in sorted_remaining_G2 if self.G2.degree(v) >= u_degree]
        candidates_v.sort(key=lambda x: self.G2.degree(x), reverse=True)

        for v in candidates_v:
            if u.type != v.type or u.attributes != v.attributes:
                continue
            consistent = True
            for (u_exist, v_exist) in current_matches:
                if self.G1.has_edge(u, u_exist) != self.G2.has_edge(v, v_exist):
                    consistent = False
                    break
            if consistent:
                new_sorted_G1 = sorted_remaining_G1[1:]
                new_sorted_G2 = [node for node in sorted_remaining_G2 if node != v]
                new_matches = list(current_matches)
                new_matches.append((u, v))
                self.search(new_matches, new_sorted_G1, new_sorted_G2)

        new_sorted_G1 = sorted_remaining_G1[1:]
        self.search(current_matches, new_sorted_G1, sorted_remaining_G2)
    
    def search_iterative(self, sorted_remaining_G1, sorted_remaining_G2):
        # 初始化栈，与递归初始调用参数一致
        stack = [(list(self.best_matches), sorted_remaining_G1, sorted_remaining_G2)]
        
        while stack:
            current_matches, sorted_remaining_G1, sorted_remaining_G2 = stack.pop()

            # 严格保持递归的终止条件
            if time.time() - self._start_time > 10:
                continue  # 确保所有路径都能被剪枝

            # 最佳匹配更新逻辑（完全一致）
            current_size = len(current_matches)
            if current_size > self.best_size:
                self.best_size, self.best_matches = current_size, list(current_matches)

            # 剪枝条件（完全一致）
            possible_max = current_size + min(len(sorted_remaining_G1), len(sorted_remaining_G2))
            if possible_max <= self.best_size or not sorted_remaining_G1 or not sorted_remaining_G2:
                continue

            u = sorted_remaining_G1[0]
            u_degree = self.G1.degree(u)

            # 候选节点生成逻辑（严格匹配递归版本）
            candidates_v = [v for v in sorted_remaining_G2 
                        if self.G2.degree(v) >= u_degree 
                        and v.type == u.type 
                        and v.attributes == u.attributes]
            candidates_v.sort(key=lambda x: self.G2.degree(x), reverse=True)

            # 不选当前u的分支（必须优先压栈以保证后处理）
            stack.append((
                current_matches, 
                sorted_remaining_G1[1:],  # 显式切片保证新列表
                sorted_remaining_G2.copy() # 防御性复制防止污染
            ))

            # 处理候选v的分支（严格逆序压栈以保持递归顺序）
            for v in reversed(candidates_v):
                # 边一致性检查（完全相同的逻辑）
                if all(
                    self.G1.has_edge(u, u_exist) == self.G2.has_edge(v, v_exist)
                    for (u_exist, v_exist) in current_matches
                ):
                    # 生成新状态（完全复制递归参数生成方式）
                    new_matches = list(current_matches) + [(u, v)]
                    new_sorted_G1 = sorted_remaining_G1[1:]
                    new_sorted_G2 = [node for node in sorted_remaining_G2 if node != v]
                    
                    stack.append((
                        new_matches,
                        new_sorted_G1,
                        new_sorted_G2  # 这里使用列表推导式保证过滤
                    ))
    
    def solve(self):
        sorted_G1 = sorted(self.G1.nodes(), key=lambda x: self.G1.degree(x), reverse=True)
        sorted_G2 = sorted(self.G2.nodes(), key=lambda x: self.G2.degree(x), reverse=True)
        self._start_time = time.time()
        self.search([], sorted_G1, sorted_G2)
        return self.best_size, self.best_matches

    def solve_iter(self):
        sorted_G1 = sorted(self.G1.nodes(), key=lambda x: self.G1.degree(x), reverse=True)
        sorted_G2 = sorted(self.G2.nodes(), key=lambda x: self.G2.degree(x), reverse=True)
        self._start_time = time.time()
        self.search_iterative(sorted_G1, sorted_G2)
        return self.best_size, self.best_matches

    def visualize(self, matches):
        """
        可视化原图和最大公共子图
        
        Args:
            matches: 匹配的节点对列表 [(u1, v1), (u2, v2), ...]
        """
        if not matches:
            print("没有找到匹配节点，无法可视化")
            return
        
        # 创建一个2x2的子图布局
        fig, axs = plt.subplots(2, 2, figsize=(12, 10))
        
        # 获取匹配的节点
        mapped_nodes_G1 = [u for u, v in matches]
        mapped_nodes_G2 = [v for u, v in matches]
        
        # 绘制G1原图
        pos_G1 = nx.spring_layout(self.G1, seed=42)
        nx.draw_networkx_nodes(self.G1, pos_G1, ax=axs[0, 0], node_color='lightblue')
        nx.draw_networkx_edges(self.G1, pos_G1, ax=axs[0, 0])
        nx.draw_networkx_labels(self.G1, pos_G1, ax=axs[0, 0])
        axs[0, 0].set_title('G1 原图')
        axs[0, 0].axis('off')
        
        # 绘制G2原图
        pos_G2 = nx.spring_layout(self.G2, seed=42)
        nx.draw_networkx_nodes(self.G2, pos_G2, ax=axs[0, 1], node_color='lightgreen')
        nx.draw_networkx_edges(self.G2, pos_G2, ax=axs[0, 1])
        nx.draw_networkx_labels(self.G2, pos_G2, ax=axs[0, 1])
        axs[0, 1].set_title('G2 原图')
        axs[0, 1].axis('off')
        
        # 绘制G1中的公共子图
        subgraph_G1 = self.G1.subgraph(mapped_nodes_G1)
        nx.draw_networkx_nodes(self.G1, pos_G1, ax=axs[1, 0], nodelist=mapped_nodes_G1, 
                              node_color='red', node_size=500)
        nx.draw_networkx_nodes(self.G1, pos_G1, ax=axs[1, 0], 
                              nodelist=[n for n in self.G1.nodes() if n not in mapped_nodes_G1], 
                              node_color='lightgray', node_size=300)
        nx.draw_networkx_edges(subgraph_G1, pos_G1, ax=axs[1, 0], width=2.0, edge_color='red')
        edges_not_in_common = [e for e in self.G1.edges() if not (e[0] in mapped_nodes_G1 and e[1] in mapped_nodes_G1)]
        nx.draw_networkx_edges(self.G1, pos_G1, ax=axs[1, 0], edgelist=edges_not_in_common, 
                              width=1.0, edge_color='lightgray', style='dashed')
        nx.draw_networkx_labels(self.G1, pos_G1, ax=axs[1, 0])
        axs[1, 0].set_title('G1 中的最大公共子图 (红色)')
        axs[1, 0].axis('off')
        
        # 绘制G2中的公共子图
        subgraph_G2 = self.G2.subgraph(mapped_nodes_G2)
        nx.draw_networkx_nodes(self.G2, pos_G2, ax=axs[1, 1], nodelist=mapped_nodes_G2, 
                              node_color='red', node_size=500)
        nx.draw_networkx_nodes(self.G2, pos_G2, ax=axs[1, 1], 
                              nodelist=[n for n in self.G2.nodes() if n not in mapped_nodes_G2], 
                              node_color='lightgray', node_size=300)
        nx.draw_networkx_edges(subgraph_G2, pos_G2, ax=axs[1, 1], width=2.0, edge_color='red')
        edges_not_in_common = [e for e in self.G2.edges() if not (e[0] in mapped_nodes_G2 and e[1] in mapped_nodes_G2)]
        nx.draw_networkx_edges(self.G2, pos_G2, ax=axs[1, 1], edgelist=edges_not_in_common, 
                              width=1.0, edge_color='lightgray', style='dashed')
        nx.draw_networkx_labels(self.G2, pos_G2, ax=axs[1, 1])
        axs[1, 1].set_title('G2 中的最大公共子图 (红色)')
        axs[1, 1].axis('off')
        
        # 添加匹配信息
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.figtext(0.5, 0.01, f"最大公共子图大小: {len(matches)}\n节点匹配: {matches}", 
                   ha="center", fontsize=12, bbox={"facecolor":"orange", "alpha":0.2, "pad":5})
        
        plt.tight_layout()
        plt.subplots_adjust(bottom=0.15)
        plt.show()

if __name__ == "__main__":
    # 创建两个示例图
    # G1 = nx.Graph()
    # G1.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (4, 7), (5, 18), (5, 19), (6, 8), (7, 9), (7, 10), (7, 11), (8, 12), (9, 13), (10, 13), (11, 14), 
    #                    (12, 15), (13, 15), (14, 15), (15, 16), (15, 17), (16, 20), (17, 20), (18, 20), (19, 20)])  

    # G2 = nx.Graph()
    # G2.add_edges_from([(1, 2), (1, 3), (2, 4), (3, 5), (4, 6), (4, 7), (5, 18), (5, 19), (6, 8), (7, 9), (7, 10), (7, 11), (8, 12), (9, 13), (10, 13), (11, 14), 
    #                    (12, 15), (13, 15), (14, 15), (15, 16), (15, 17), (16, 20), (17, 20), (18, 20), (19, 20), (20, 21), (20, 22), (21, 23), (22,23)])  


    # 示例，已弃用
    size = 25
    G1 = nx.erdos_renyi_graph(size, 0.5)
    G2 = nx.erdos_renyi_graph(size, 0.5)

    solver = McSplitSolver(G1, G2)
    start_time = time.time()
    size, matches = solver.solve()
    end_time = time.time()

    print(f"最大公共子图的大小: {size}")
    print(f"节点匹配对: {matches}")
    print(f"用时: {end_time - start_time} 秒")
    # 根据匹配对构建公共子图
    if size > 0:
        mapped_nodes_G1 = [u for u, v in matches]
        mapped_nodes_G2 = [v for u, v in matches]
        subgraph_G1 = G1.subgraph(mapped_nodes_G1)
        subgraph_G2 = G2.subgraph(mapped_nodes_G2)

        print("\nG1中的公共子图节点:", subgraph_G1.nodes())
        print("G1中的公共子图边:", subgraph_G1.edges())
        print("\nG2中的公共子图节点:", subgraph_G2.nodes())
        print("G2中的公共子图边:", subgraph_G2.edges())

    solver.visualize(matches)