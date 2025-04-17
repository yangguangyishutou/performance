# coding=utf-8
import mcsplit
import json
import networkx as nx
import matplotlib.pyplot as plt
import time

class Node:
    def __init__(self, name, type, attributes = []):
        # 节点名称 此处name指output的名称
        self.name = name
        self.type = type
        self.attributes = attributes

class GraphSolver:    

    def __init__(self, path):
        self.path = path
        self.G = nx.Graph()

    def findNode(self, name):
        for node in self.G.nodes():
            if node.name == name:
                return node
        return None
    
    def buildGraph(self):
        path = self.path
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # print(json.dumps(data, indent=4))

        # 模型的input
        try:  #bert
            for i in data["_graphs"][0]["_inputs"]:
                node = Node(i["name"], "input")
                self.G.add_node(node)
        except: #gpt2
            for i in data["graphs"][0]["inputs"]:
                node = Node(i["name"], "input")
                self.G.add_node(node)

        # nodes
        try:
            for i in data["_graphs"][0]["_nodes"]:
                name = i["outputs"][0]["value"][0]["_name"]
                type = i["type"]["name"]
                attributes = i["attributes"]
                node = Node(name, type, attributes)
                self.G.add_node(node)
        except:
            for i in data["graphs"][0]["nodes"]:
                name = i["outputs"][0]["value"][0]["name"]
                type = i["type"]["name"]
                attributes = i["attributes"]
                node = Node(name, type, attributes)
                self.G.add_node(node)
        # print(map)
        
        # 连边
        try:
            for i in data["_graphs"][0]["_nodes"]:
                for j in i["inputs"]:
                    node = self.findNode(i["outputs"][0]["value"][0]["_name"])
                    fatherNode = self.findNode(j["value"][0]["_name"])
                    if fatherNode != None:
                        self.G.add_edge(node, fatherNode)
                    else :
                        # print(f"KeyError: {j["value"][0]["_name"]} not found in map, node: {node.name}")
                        pass
        except:
            for i in data["graphs"][0]["nodes"]:
                for j in i["inputs"]:
                    node = self.findNode(i["outputs"][0]["value"][0]["name"])
                    fatherNode = self.findNode(j["value"][0]["name"])
                    if fatherNode != None:
                        self.G.add_edge(node, fatherNode)
                    else :
                        # print(f"KeyError: {j["value"][0]["name"]} not found in map, node: {node.name}")
                        pass
        return self.G


if __name__ == "__main__":

    # test
    # path1 = "./model_torch_jit.json"
    path2 = "./model_gpt2.json"
    # path1 = "../models/BERT/google-bertbert-base-uncased.json"
    # path2 = "../models/ME2-BERT/onnx/onnx_model.json"
    path1 = "../models/gpt2/onnx/onnx_model.json"
    # path2 = "../models/sst-gpt2/onnx/onnx_model.json"

    solver1 = GraphSolver(path1)
    solver2 = GraphSolver(path2)
    G1 = solver1.buildGraph()
    G2 = solver2.buildGraph()
    print(f"模型1节点数: {len(G1.nodes())}, 边数: {len(G1.edges())}")
    print(f"模型2节点数: {len(G2.nodes())}, 边数: {len(G2.edges())}")

    # 测试加边
    # G2 = G1.copy()
    # tmpnode1 = Node("tmp1", "Unsqueeze")
    # tmpnode2 = Node("tmp2", "Cast")
    # tmpnode3 = Node("tmp3", "Sub")
    # tmpnode4 = Node("tmp4", "Mul")
    # tmpnode5 = Node("tmp5", "Add")
    # G2.add_edges_from([(list(G1.nodes())[0], tmpnode1), (list(G1.nodes())[0],tmpnode2), (tmpnode1, tmpnode2), (tmpnode2, tmpnode3), (tmpnode3, tmpnode4)]) 
    # G1.add_edges_from([(list(G1.nodes())[0], tmpnode5)]) 


    solver = mcsplit.McSplitSolver(G1, G2)
    start_time = time.time()
    # size, matches = solver.solve()
    size, matches = solver.solve_iter()

    end_time = time.time()
    print(f"最大公共子图的大小: {size}")
    # print(f"节点匹配对: {matches}")
    print(f"用时: {end_time - start_time} 秒")


    # 根据匹配对构建公共子图
    # if size > 0:
    #     mapped_nodes_G1 = [u for u, v in matches]
    #     mapped_nodes_G2 = [v for u, v in matches]
    #     subgraph_G1 = G1.subgraph(mapped_nodes_G1)
    #     subgraph_G2 = G2.subgraph(mapped_nodes_G2)

        # print("\nG1中的公共子图节点:", subgraph_G1.nodes())
        # print("G1中的公共子图边:", subgraph_G1.edges())
        # print("\nG2中的公共子图节点:", subgraph_G2.nodes())
        # print("G2中的公共子图边:", subgraph_G2.edges())

    # solver.visualize(matches)