import os
import json
import time
import requests
import base64
import hashlib
import re
import random
from tree_sitter import Language, Parser
import tree_sitter_java
import tree_sitter_c
import tree_sitter_javascript

# ==================== 配置区 ====================
# ⚠️ 请务必在此处填入 Token
GITHUB_TOKEN = "your_token" 

CREATED_AFTER = "2024-01-01"
TARGET_LANGS = ["java", "c", "javascript"]

# 【硬性指标】
TARGET_REPO_COUNT = 110      
FUNCS_PER_REPO = 10          
# 总计 = 1100 个负样本 

# 路径
POS_DIR = "../data/positive"
NEG_DIR = "../data/negative"
LOG_DIR = "../data/logs"
os.makedirs(NEG_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# ==================== 1. 结构化统计模块 (满足 Repo-File-Function 溯源) ====================
class Statistics:
    def __init__(self, lang):
        self.lang = lang
        self.trace_data = [] 
        self.current_repo_node = None
        self.current_file_node = None
        
        # 全局计数器
        self.total_repos_scanned = 0
        self.total_repos_accepted = 0
        self.total_files_scanned = 0
        self.total_funcs_scanned = 0
        self.total_funcs_accepted = 0

    def start_repo(self, repo_name):
        self.total_repos_scanned += 1
        self.current_repo_node = {
            "repo_name": repo_name,
            "status": "scanning",
            "files": [],
            "accepted_funcs_count": 0
        }

    def end_repo(self, status, reason=""):
        if self.current_repo_node:
            self.current_repo_node["status"] = status
            self.current_repo_node["reason"] = reason
            self.trace_data.append(self.current_repo_node)
            if status == "accepted":
                self.total_repos_accepted += 1
            self.current_repo_node = None

    def start_file(self, file_url):
        self.total_files_scanned += 1
        self.current_file_node = {
            "file_url": file_url,
            "status": "scanning",
            "functions": []
        }

    def end_file(self, status):
        if self.current_file_node and self.current_repo_node:
            self.current_file_node["status"] = status
            self.current_repo_node["files"].append(self.current_file_node)
            self.current_file_node = None

    def log_function(self, func_name, check_status, check_reason):
        self.total_funcs_scanned += 1
        if self.current_file_node:
            record = {
                "name": func_name,
                "status": check_status, 
                "reason": check_reason
            }
            self.current_file_node["functions"].append(record)
            
            if check_status == "accepted":
                self.total_funcs_accepted += 1
                if self.current_repo_node:
                    self.current_repo_node["accepted_funcs_count"] += 1

    def save_trace(self):
        # 保存详细的 JSON 溯源文件
        trace_path = os.path.join(LOG_DIR, f"{self.lang}_trace_detailed.json")
        with open(trace_path, 'w', encoding='utf-8') as f:
            json.dump(self.trace_data, f, indent=2)
            
        # 保存简报
        summary = {
            "Language": self.lang,
            "Repos Scanned": self.total_repos_scanned,
            "Repos Accepted": self.total_repos_accepted,
            "Files Scanned": self.total_files_scanned,
            "Functions Scanned": self.total_funcs_scanned,
            "Functions Accepted": self.total_funcs_accepted,
            "Target Achieved": self.total_repos_accepted == TARGET_REPO_COUNT
        }
        summary_path = os.path.join(LOG_DIR, f"{self.lang}_summary.json")
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"\n[Statistics] Trace saved to {trace_path}")

# ==================== 2. 验证与查重模块 ====================
class Verifier:
    def __init__(self):
        self.pos_code_hashes = set()
        self.neg_code_hashes = set()
        self.neg_func_names = set()

    def load_positive_samples(self):
        print(">>> [Verifier] Loading positive samples...")
        count = 0
        if os.path.exists(POS_DIR):
            for f_name in os.listdir(POS_DIR):
                if not f_name.endswith(".jsonl"): continue
                path = os.path.join(POS_DIR, f_name)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line in f:
                            data = json.loads(line)
                            code = data.get('code', '').strip()
                            if code:
                                self.pos_code_hashes.add(self._get_hash(code))
                                count += 1
                except: pass
        print(f"    Loaded {count} positive sample fingerprints.")

    def _get_hash(self, text):
        # 移除空白符计算哈希，防止因为格式化差异导致的误判
        clean_text = re.sub(r'\s+', '', text)
        return hashlib.md5(clean_text.encode('utf-8')).hexdigest()

    def check(self, func_name, func_code):
        # 1. 空函数检查 (Scientific Rigor: 只剔除真正的空函数)
        # 去掉空格后，如果是 "{}", "{;}", "" 则拒绝
        clean_body = re.sub(r'\s+', '', func_code)
        if clean_body in ['{}', '{;}', '']:
            return "rejected", "empty_body"

        code_hash = self._get_hash(func_code)
        
        # 2. 污染检查
        if code_hash in self.pos_code_hashes:
            return "rejected", "conflict_with_positive"
        
        # 3. 内部代码查重
        if code_hash in self.neg_code_hashes:
            return "rejected", "duplicate_internal_code"
        
        # 4. 函数名查重
        if func_name and func_name in self.neg_func_names:
             return "rejected", "duplicate_function_name"

        # 通过
        self.neg_code_hashes.add(code_hash)
        if func_name:
            self.neg_func_names.add(func_name)
            
        return "accepted", "valid"

# ==================== 3. 核心功能 ====================

langs_conf = {
    'java': Language(tree_sitter_java.language()),
    'c': Language(tree_sitter_c.language()),
    'javascript': Language(tree_sitter_javascript.language())
}
parsers = { k: Parser(v) for k, v in langs_conf.items() }

def extract_funcs_with_name(code, lang):
    """从代码中解析 (函数名, 函数体)"""
    try:
        tree = parsers[lang].parse(bytes(code, "utf8"))
        results = [] 
        
        def traverse(node):
            func_name = None
            func_body = None
            target_node = False
            
            # --- Java 解析 ---
            if lang == 'java' and node.type == 'method_declaration':
                target_node = True
                for child in node.children:
                    if child.type == 'identifier':
                        func_name = code.encode('utf8')[child.start_byte : child.end_byte].decode('utf8')
                        break
            
            # --- C 解析 (改进版: 递归查找 declarator) ---
            elif lang == 'c' and node.type == 'function_definition':
                target_node = True
                curr = node.child_by_field_name('declarator')
                # 钻取 function_declarator 或 pointer_declarator 直到底层 identifier
                while curr:
                    if curr.type == 'function_declarator':
                        curr = curr.child_by_field_name('declarator')
                    elif curr.type == 'pointer_declarator':
                        curr = curr.child_by_field_name('declarator')
                    elif curr.type == 'parenthesized_declarator':
                        curr = curr.child_by_field_name('declarator')
                    elif curr.type == 'identifier':
                        func_name = code.encode('utf8')[curr.start_byte : curr.end_byte].decode('utf8')
                        break
                    else:
                        break # 无法识别的复杂结构
                        
            # --- JavaScript 解析 ---
            elif lang == 'javascript' and node.type in ['function_declaration', 'method_definition']:
                target_node = True
                for child in node.children:
                    if child.type in ['identifier', 'property_identifier']:
                        func_name = code.encode('utf8')[child.start_byte : child.end_byte].decode('utf8')
                        break

            # --- 统一提取逻辑 ---
            if target_node:
                func_body = code.encode('utf8')[node.start_byte : node.end_byte].decode('utf8', errors='ignore')
                
                # 【严谨性修正】不再检查 len > 50，仅检查是否有名字和是否非空
                if func_name and func_body:
                    results.append((func_name, func_body))
                return # 找到最外层函数后，不再递归进入其内部，避免重复提取子函数
            
            # 递归遍历
            for child in node.children:
                traverse(child)
                    
        traverse(tree.root_node)
        return results
    except Exception as e:
        # print(f"Parse Error: {e}") 
        return []

def get_file_list_tree(owner, repo, lang_ext):
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200: return []
        branch = resp.json().get("default_branch", "main")
        
        # 递归获取文件树 (recursive=1)
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{branch}?recursive=1"
        resp = requests.get(tree_url, headers=HEADERS, timeout=15)
        if resp.status_code != 200: return []
        
        tree = resp.json().get("tree", [])
        files = []
        BLACKLIST = ['test', 'doc', 'example', 'sample', 'build', 'node_modules', 'dist', 'out', 'vendor']
        
        for item in tree:
            path = item.get("path", "")
            # 1MB 限制，防止下载超大文件卡死
            if path.endswith(lang_ext) and item["type"] == "blob" and item.get("size", 0) < 1000000:
                if not any(x in path.lower() for x in BLACKLIST):
                    files.append(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}")
        
        # 限制单次处理文件上限，防止内存溢出，但要先 Shuffle
        if len(files) > 100: 
            return files[:100] 
        return files
    except: return []

def download_content(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200 and 'content' in resp.json():
            return base64.b64decode(resp.json()['content']).decode('utf-8', errors='ignore')
    except: pass
    return None

def search_repos(lang, page):
    # sort=stars 确保质量，created 确保时效性
    query = f"language:{lang} created:>{CREATED_AFTER} sort:stars"
    url = f"https://api.github.com/search/repositories?q={query}&per_page=30&page={page}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200: return resp.json().get("items", [])
        if resp.status_code == 403:
            print("  [!] Rate Limit. Waiting 60s...")
            time.sleep(60)
            return search_repos(lang, page)
    except: pass
    return []

# ==================== 主流程 ====================

def main():
    if "在此处填入" in GITHUB_TOKEN:
        print("❌ 错误：请先在代码第 16 行填入你的 GitHub Token！")
        return

    verifier = Verifier()
    verifier.load_positive_samples()
    
    ext_map = {'java': '.java', 'c': '.c', 'javascript': '.js'}

    for lang in TARGET_LANGS:
        print(f"\n====================================")
        print(f">>> Processing Language: {lang}")
        print(f"====================================")
        
        stats = Statistics(lang)
        output_file = os.path.join(NEG_DIR, f"{lang}_negative.jsonl")
        
        # 检查是否断点续传，如果是新跑则清空文件
        if not os.path.exists(output_file):
            with open(output_file, 'w', encoding='utf-8') as f: pass
        
        page = 1
        while stats.total_repos_accepted < TARGET_REPO_COUNT:
            print(f"  > Page {page} | Collected Repos: {stats.total_repos_accepted}/{TARGET_REPO_COUNT}")
            repos = search_repos(lang, page)
            if not repos:
                page += 1
                if page > 50: break
                continue
            
            for repo in repos:
                if stats.total_repos_accepted >= TARGET_REPO_COUNT: break
                
                repo_name = repo['full_name']
                stats.start_repo(repo_name) 
                
                # 1. 扫描文件
                files = get_file_list_tree(repo['owner']['login'], repo['name'], ext_map[lang])
                
                # 【关键严谨性修改】打乱文件顺序，避免采样偏差 (Sampling Bias)
                random.shuffle(files)
                
                repo_funcs_buffer = [] 
                
                for file_url in files:
                    if len(repo_funcs_buffer) >= FUNCS_PER_REPO: break
                    
                    stats.start_file(file_url) 
                    code = download_content(file_url)
                    
                    if code:
                        funcs = extract_funcs_with_name(code, lang)
                        for func_name, func_code in funcs:
                            if len(repo_funcs_buffer) >= FUNCS_PER_REPO: break
                            
                            # 验证并记录
                            status, reason = verifier.check(func_name, func_code)
                            stats.log_function(func_name, status, reason)
                            
                            if status == "accepted":
                                repo_funcs_buffer.append({
                                    "code": func_code,
                                    "name": func_name,
                                    "repo": repo_name,
                                    "language": lang,
                                    "fingerprint": verifier._get_hash(func_code) # 方便后续处理
                                })
                    
                    stats.end_file("processed") 
                    # 适当休眠，虽然是串行但也不要太快
                    time.sleep(0.2)

                # 2. 结算仓库
                if len(repo_funcs_buffer) >= FUNCS_PER_REPO:
                    with open(output_file, 'a', encoding='utf-8') as f:
                        for item in repo_funcs_buffer[:FUNCS_PER_REPO]:
                            item['retrieved_at'] = time.strftime("%Y-%m-%d")
                            f.write(json.dumps(item) + "\n")
                    
                    stats.end_repo("accepted", "Collected 10 functions")
                    print(f"    [√] Accepted: {repo_name}")
                else:
                    stats.end_repo("rejected", f"Only found {len(repo_funcs_buffer)} valid funcs")
            
            page += 1
        
        stats.save_trace()

    print("\n>>> All tasks finished. Check 'data/logs/' for verification traces.")

if __name__ == "__main__":
    main()