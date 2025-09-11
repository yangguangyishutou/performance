# mother_recovery.py
import os
import json
import math
from typing import List, Dict, Tuple, Any, Optional
import numpy as np
from ModelCollectionAnalyzer import ModelCollectionAnalyzer


'''
Edmonds / Chu-Liu 算法实现（返回最小有向生成树）
输入:
  nodes: 可迭代的节点标识（可为字符串）
  edges: list of (u, v, cost) 有向边（cost 为 float）
  root: root 节点标识（必须在 nodes 中）
返回:
  (total_cost, selected_edges) 其中 selected_edges 是 (u,v,cost) 列表构成的 arborescence
'''
def chu_liu_edmonds(nodes: List[Any], edges: List[Tuple[Any, Any, float]], root: Any):
    """
    一个较为直观的 Edmonds 算法实现，包含环收缩与展开以重建最终边集合。
    若不存在入边使得每个非根节点可达，则抛出 ValueError。
    """
    # 将节点列表复制为 list，以便索引/顺序稳定
    nodes = list(nodes)
    if root not in nodes:
        raise ValueError("root 必须在 nodes 中。")

    # 内部递归函数：处理当前图（节点名可以是任意 hashable 对象）
    def _edmonds(curr_nodes, curr_edges, curr_root):
        # 1) 对每个节点（除 root）选择最小入边
        in_edge = {}  # v -> (u,v,cost)
        incoming_map = {}  # v -> list of incoming edges (用于检查连通性)
        for u, v, c in curr_edges:
            incoming_map.setdefault(v, []).append((u, v, c))
        for v in curr_nodes:
            if v == curr_root:
                continue
            incs = incoming_map.get(v, [])
            if not incs:
                # 无法找到进入 v 的边，说明无可行入树（图不连通或 v 无入边）
                raise ValueError(f"No incoming edges to node {v} — no arborescence exists.")
            # 选最小成本入边
            best = min(incs, key=lambda e: e[2])
            in_edge[v] = best

        # 2) 检测由这些入边构成的图中是否有环
        # 构建一个 map from node -> its parent (according to in_edge)
        parent = {}
        for v, e in in_edge.items():
            u, _, c = e
            parent[v] = u

        # 寻找环（使用访问标记）
        index = {}  # node -> index in visitation order within search
        visited = set()
        cycles = []  # list of lists (cycles)
        for v in curr_nodes:
            if v in visited or v == curr_root:
                continue
            path = []
            cur = v
            while True:
                if cur in path:
                    # found cycle starting from first occurrence of cur
                    start = path.index(cur)
                    cycle_nodes = path[start:]
                    cycles.append(cycle_nodes)
                    for n in cycle_nodes:
                        visited.add(n)
                    break
                if cur in visited or cur == curr_root:
                    # reached previously explored node or root -> no cycle on this chain
                    for n in path:
                        visited.add(n)
                    break
                path.append(cur)
                if cur not in parent:
                    # no parent (shouldn't really happen because we ensured incoming edges)
                    for n in path:
                        visited.add(n)
                    break
                cur = parent[cur]

        if not cycles:
            # 无环 => 直接返回当前选择的入边集合
            selected = list(in_edge.values())
            total_cost = sum(e[2] for e in selected)
            return total_cost, selected

        # 3) 存在至少一个环 — 取第一个环来收缩（算法可以任意选择环）
        cycle = cycles[0]
        cycle_set = set(cycle)
        cycle_id = ("__CYCLE__",) + tuple(cycle)  # 唯一标识符，用作新节点的 name

        # 构建映射：原节点 -> 新节点名称（把 cycle 中的节点映射到 cycle_id，其它保持不变）
        def rep(n):
            return cycle_id if n in cycle_set else n

        # 记录选中入边的成本，便于后续调整（in_edge[v]）
        in_cost = {v: in_edge[v][2] for v in in_edge}

        # 构建新的节点列表（contracted）
        new_nodes = [rep(n) for n in curr_nodes if rep(n) == n]  # unique nodes not in cycle
        new_nodes.append(cycle_id)

        # 为后续扩展保存：对于任何 (u->v) 原始边，若 v 属于 cycle，并 u 不在 cycle，
        # 我们需要记下 adjusted cost = cost - in_cost[v]，并保存对应的原始边用于展开。
        new_edges_dict = {}  # key=(u',v') -> (min_cost, original_edge_tuple_details)
        # original_edge_tuple_details 用以在展开阶段重建 (orig_u, orig_v, orig_cost, adjusted_cost, came_from)
        # came_from 表示: 用于标记在收缩后哪个原始 v 提供了该调整

        for (u, v, c) in curr_edges:
            u_rep = rep(u)
            v_rep = rep(v)
            if u_rep == v_rep:
                continue  # 忽略收缩后成环的自边
            if v_rep == cycle_id and v in cycle_set and u not in cycle_set:
                # 边从外部指向环内：需要调整 cost
                adjusted = c - in_cost[v]
                key = (u_rep, v_rep)
                prev = new_edges_dict.get(key)
                if (prev is None) or (adjusted < prev[0]):
                    # 保存 (adjusted_cost, original_edge=(u,v,c), entering_v = v)
                    new_edges_dict[key] = (adjusted, (u, v, c), v)
            elif u_rep == cycle_id and v_rep != cycle_id:
                # 边从环内部指向外：cost 不变（选择任意一个代表）
                key = (u_rep, v_rep)
                prev = new_edges_dict.get(key)
                if (prev is None) or (c < prev[0]):
                    new_edges_dict[key] = (c, (u, v, c), None)
            else:
                # 既不进入环也不从环出 => cost 不变
                key = (u_rep, v_rep)
                prev = new_edges_dict.get(key)
                if (prev is None) or (c < prev[0]):
                    new_edges_dict[key] = (c, (u, v, c), None)

        # 生成新的边列表供递归调用
        contracted_edges = []
        # 还需要保留 mapping 用于展开时检索哪个原始边对应进入环的最优 adjusted edge
        enter_edge_map = {}  # key = (u_rep, cycle_id) -> (orig_u, orig_v, orig_cost, adjusted)
        for (u_r, v_r), (cost_val, orig_edge, entering_v) in new_edges_dict.items():
            contracted_edges.append((u_r, v_r, cost_val))
            if v_r == cycle_id and entering_v is not None:
                enter_edge_map[(u_r, v_r)] = (orig_edge[0], orig_edge[1], orig_edge[2], cost_val, entering_v)

        # 递归在收缩图上解最小有向生成树
        sub_total, sub_selected = _edmonds(new_nodes, contracted_edges, curr_root if curr_root not in cycle_set else cycle_id)

        # sub_selected 是收缩图上的边集合。现在需要把它“展开”回原始节点空间
        # 找到在 sub_selected 中指向 cycle_id 的入边（如果有）
        entering_edge_to_cycle = None
        for (u, v, c) in sub_selected:
            if v == cycle_id:
                entering_edge_to_cycle = (u, v, c)
                break

        # 如果没有外部边进入 cycle_id（理论上应该有），则它是 root 或完全隔离的环
        if entering_edge_to_cycle is None:
            # 当环包含 root 时可能出现这种情况；但我们的 root 在上层已被替换为 cycle_id
            # 在这种情形下，我们应当保留环内的 in_edge 边（原本的 in_edge），并返回
            final_edges = []
            # 保留所有 in_edge[v] for v in cycle
            for v in cycle:
                final_edges.append(in_edge[v])
            # 加上 sub_selected 中除 cycle_id 外的其它边（替换 cycle_id 虚节点）
            for e in sub_selected:
                if e[0] == cycle_id or e[1] == cycle_id:
                    # 跳过 cycle_id 相关（它们将由上面补齐）
                    continue
                final_edges.append(e)
            total_cost = sum(e[2] for e in final_edges)
            return total_cost, final_edges

        # 把 contracted sub_selected 中的边（不含进入 cycle_id 的那条）直接加入 final_edges（将 cycle_id 当作占位）
        final_edges = []
        for (u, v, c) in sub_selected:
            if v == cycle_id:
                continue
            final_edges.append((u, v, c))

        # 现在需要把进入 cycle 的外部边替换为其对应的原始入边 (orig_u -> orig_v)
        u_rep, _, _ = entering_edge_to_cycle
        key = (u_rep, cycle_id)
        if key not in enter_edge_map:
            raise RuntimeError("在展开环时无法找到对应的原始进入边映射。")
        orig_u, orig_v, orig_cost, adjusted_cost, entering_v = enter_edge_map[key]

        # 将进入环的原始边加入 final_edges
        final_edges.append((orig_u, orig_v, orig_cost))

        # 对环内部：保留所有 in_edge[v]，但要去掉 orig_v 的 in_edge（因为 orig_v 的 in_edge 会被外部 orig_u->orig_v 替代）
        for v in cycle:
            if v == orig_v:
                continue
            final_edges.append(in_edge[v])

        # 再加入 sub_selected 中除 cycle_id 相关的边（上述已经加入）
        # 计算 total cost（原始代价）
        total_cost = 0.0
        # final_edges 现在包含的是原始边或 contracted edges（非 cycle_id 相关）
        # 对 final_edges 中可能仍有虚节点（非原始）进行过滤：它们应当都是原始边
        # 我们确保以原始 cost 进行求和
        for e in final_edges:
            total_cost += e[2]

        return total_cost, final_edges

    # 调用内部实现
    return _edmonds(nodes, edges, root)


class MoTHer:
    def __init__(self,
                 models: List[str],
                 model_meta: Optional[Dict[str, Dict[str, Any]]] = None,
                 out_dir: Optional[str] = None,
                 verbose: bool = True):
        self.models = list(models)
        self.model_meta = model_meta or {}
        self.out_dir = out_dir
        self.verbose = verbose
        if self.out_dir:
            os.makedirs(self.out_dir, exist_ok=True)

    def _log(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def build_graph_edges(self,
                          pairwise_distances: np.ndarray,
                          kurtosis: Dict[str, float],
                          invalid_marker: float = -1.0) -> List[Tuple[str, str, float]]:
        """
        从 pairwise_distances 和 kurtosis 构建有向边列表 (u, v, cost)：
          - 仅当 distances[i,j] 非 nan 且 != invalid_marker 时认为 i->j 是候选边
          - 同时应满足方向约束：kurtosis[i] >= kurtosis[j]（或用户可修改规则）
          - cost 直接使用 distances[i,j]
        """
        edges = []
        n = len(self.models)
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                d = float(pairwise_distances[i, j])
                if math.isnan(d):
                    continue
                if d == invalid_marker:
                    continue
                name_i = self.models[i]
                name_j = self.models[j]
                # 方向约束（paper 经验：父峰度通常 >= 子峰度）
                ki = kurtosis.get(name_i, float('nan'))
                kj = kurtosis.get(name_j, float('nan'))
                if math.isnan(ki) or math.isnan(kj):
                    # 如果某个节点没有峰度信息，保守做法是允许该边（或跳过）；这里允许但警告
                    self._log(f"[build_graph_edges] 警告：{name_i} 或 {name_j} 无峰度信息，允许该边。")
                else:
                    if ki < kj:
                        # 不满足高峰度->低峰度，跳过（用户先前也使用了这种约束）
                        continue
                edges.append((name_i, name_j, d))
        self._log(f"[build_graph_edges] 构建了 {len(edges)} 条候选有向边。")
        return edges

    def compute_mdst(self,
                     root: Optional[str] = None,
                     request_layerwise: bool = False,
                     save_to: Optional[str] = None) -> Dict[str, Any]:
        """
        主流程：
          - 调用 ModelCollectionAnalyzer 得到 pairwise_distances 与 kurtosis
          - 构建边并运行 Chu-Liu-Edmonds 算法得到最小有向生成树（以 root 为根）
          - 返回字典：{ 'root': root, 'total_cost': float, 'edges': [(u,v,cost), ...] }
        """
        # 1) 运行 ModelCollectionAnalyzer
        mca = ModelCollectionAnalyzer(self.models, model_meta=self.model_meta, out_dir=None, verbose=self.verbose)
        res = mca.run_all(request_layerwise=request_layerwise)

        pairwise = res["pairwise_distances"]
        kurt = res["kurtosis"]

        # 2) 选择 root（默认：峰度最大的模型）
        if root is None:
            # 选择峰度最大（数值）作为 root（paper 中 root 往往是 foundation model）
            best = None
            best_val = -float("inf")
            for k, v in kurt.items():
                try:
                    if float(v) > best_val:
                        best_val = float(v)
                        best = k
                except Exception:
                    continue
            if best is None:
                raise RuntimeError("无法从 kurtosis 中选出 root，请显式传入 root。")
            root = best
            self._log(f"[compute_mdst] 未指定 root，自动选择峰度最大的节点作为 root：{root} (kurtosis={best_val:.6f})")

        # 3) 构建候选边
        edges = self.build_graph_edges(pairwise, kurt)

        # 4) 调用 Edmonds
        try:
            total_cost, selected_edges = chu_liu_edmonds(self.models, edges, root)
            self._log(f"[compute_mdst] MDST 总成本: {total_cost:.6f}, 边数: {len(selected_edges)}")
        except ValueError as e:
            # 无法形成 arborescence（例如某些节点无入边），返回失败信息
            self._log(f"[compute_mdst] 生成树失败: {e}")
            return {"success": False, "reason": str(e)}

        # 5) 保存结果（可选）
        result = {
            "success": True,
            "root": root,
            "total_cost": float(total_cost),
            "edges": [{"parent": u, "child": v, "cost": float(c)} for (u, v, c) in selected_edges]
        }

        if save_to is None and self.out_dir:
            save_to = os.path.join(self.out_dir, "mothertree.json")
        if save_to:
            with open(save_to, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            self._log(f"[compute_mdst] 结果已保存到 {save_to}")

        return result



if __name__ == "__main__":
    models = [
        "openai-community/gpt2",
        "smgriffin/pop-lyrics-generator-v1",
        "Arjun-G-Ravi/chat-GPT2",
        "alibidaran/medical_transcription_generator",
    ]



    rec = MoTHer(models, out_dir="./mother/mother_out", verbose=True)
    tree = rec.compute_mdst()  # 默认选择峰度最大的模型作为 root
    print(json.dumps(tree, indent=2, ensure_ascii=False))
