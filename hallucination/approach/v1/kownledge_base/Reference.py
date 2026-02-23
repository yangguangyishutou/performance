import sys
from pathlib import Path

# 添加父目录到路径以便导入模块
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.structure import *
import json

try:
    knowledges = json.load(open(r"D:\projects\sitp\sitp-dataset\sitp_script\strategy_bottomup\Knowledge Base.json"))
except Exception as e:
    print(f"Knowledge Base.json loading failed: {str(e)}")
    knowledges = []

def get_TH_knowledges(h:Header, external_classes:dict[str,list[tuple[str, str]]]):
    results = []
    id_set = set()
    for k in knowledges:
        for clazz in external_classes.keys():
            if clazz in k["title"] or k["title"] in h.imports:
                if k['id'] not in id_set:
                    results.append(str(k['content']))
                    id_set.add(k['id'])

    for impor in h.imports:
        if "java.lang.reflect" in impor:
            if 29 not in id_set:
                results.append(str(knowledges[28]['content']))
    return results


def get_HP_knowledges(h:Header):
    results = []
    id_set = set()
    for k in knowledges:
        for clazz in h.imports:
            if clazz in k["title"] or k["title"] in h.imports:
                if k['id'] not in id_set:
                    results.append(str(k['content']))
                    id_set.add(k['id'])
    for impor in h.imports:
        if "java.lang.reflect" in impor:
            if 29 not in id_set:
                results.append(str(knowledges[28]['content']))

    return results


def get_MP_knowledge(n:Method):

    return []