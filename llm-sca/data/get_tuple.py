import requests
import json
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib.parse import quote
from requests.packages.urllib3.util.retry import Retry
from tqdm import tqdm

# ------------ Configuration ------------
# Input: list of base models (one per line, format: namespace/model)
BASE_MODEL_FILE = "base_models.txt"
# Output JSON file representing the forest
OUTPUT_JSON = "model_forest.json"
# Maximum depth to avoid infinite recursion
MAX_DEPTH = 4
# Types of derivation to consider
COM_TYPES = ["finetune", "adapter", "quantized", "merge"]
# Maximum number of siblings per derivation type to include
MAX_SIBLINGS_PER_TYPE = 6
# ------------ End Configuration ------------

# Retry strategy for HTTP errors
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# Create session with retry
def create_session():
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

ua = UserAgent()

# Scrape derived models for a given base and derivation type
def scrape_derived(session, base_full, com_type):
    base_id = quote(base_full.split("/")[0]) + "%2F" + quote(base_full.split("/")[1])
    url = f"https://huggingface.co/models?other=base_model:{com_type}:{base_id}&sort=likes"
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://huggingface.co/",
        "DNT": "1"
    }
    time.sleep(random.uniform(1, 2))
    resp = session.get(url, headers=headers, timeout=30)
    if resp.status_code != 200:
        return []
    soup = BeautifulSoup(resp.text, "html.parser")
    titles = []
    for article in soup.find_all("article"):
        header = article.find("header")
        if header and header.get("title"):
            titles.append(header["title"].strip())
    return titles

# Recursively build tree for one model node
def build_tree(session, model_full, depth=0, visited=None):
    if visited is None:
        visited = set()
    if depth >= MAX_DEPTH or model_full in visited:
        return None
    visited.add(model_full)

    node = {
        "model": model_full,
        "metadata": {
            "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "depth": depth
        },
        "children": []
    }

    # For each derivation type, limit siblings per type
    for com_type in COM_TYPES:
        derived = scrape_derived(session, model_full, com_type)
        for child in derived[:MAX_SIBLINGS_PER_TYPE]:
            subtree = build_tree(session, child, depth + 1, visited)
            if subtree:
                subtree["metadata"]["derived_type"] = com_type
                node["children"].append(subtree)

    return node

# Main: build forest for all base models with progress bar
if __name__ == "__main__":
    with open(BASE_MODEL_FILE) as f:
        bases = [l.strip() for l in f if "/" in l]

    session = create_session()
    forest = []
    # tqdm 显示基模型处理进度
    for bm in tqdm(bases, desc="Processing base models"):
        tree = build_tree(session, bm)
        if tree:
            forest.append(tree)
    session.close()

    # 写入 JSON 文件
    with open(OUTPUT_JSON, "w", encoding="utf-8") as outf:
        json.dump(forest, outf, ensure_ascii=False, indent=2)

    print(f"Forest saved to {OUTPUT_JSON} with {len(forest)} trees.")
