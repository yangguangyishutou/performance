from collections import defaultdict, deque

class Graph:
    def __init__(self, vertices):
        self.graph = defaultdict(list)  # 邻接表
        self.V = vertices  # 顶点数

    def add_edge(self, u, v):
        self.graph[u].append(v)

    def topological_sort(self):
        # 计算每个顶点的入度
        in_degree = [0] * self.V
        for i in self.graph:
            for j in self.graph[i]:
                in_degree[j] += 1

        # 将所有入度为0的顶点加入队列
        queue = deque()
        for i in range(self.V):
            if in_degree[i] == 0:
                queue.append(i)

        # 初始化拓扑排序结果列表
        topo_order = []

        # 处理队列中的顶点
        while queue:
            u = queue.popleft()
            topo_order.append(u)

            # 减少相邻顶点的入度，并将入度为0的顶点加入队列
            for v in self.graph[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        # 检查是否有环
        if len(topo_order) != self.V:
            print("图中存在环，无法进行拓扑排序。")
        else:
            print("拓扑排序结果:", topo_order)