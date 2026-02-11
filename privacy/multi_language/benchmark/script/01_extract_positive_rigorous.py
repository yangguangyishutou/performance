import os
import json
import time
import re
import hashlib
from datasets import load_dataset
from tree_sitter import Language, Parser
import tree_sitter_java
import tree_sitter_c
import tree_sitter_javascript

# ==================== 科研配置区 ====================
TARGET_LANGS = ["java", "c", "javascript"]
TARGET_FILE_COUNT = 100 
FUNCS_PER_FILE = 10

BASE_DIR = "../data"
OUTPUT_DIR = os.path.join(BASE_DIR, "positive")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

# ==================== 1. 严谨的统计与日志类 ====================
class Statistics:
    def __init__(self, lang):
        self.lang = lang
        self.start_time = time.time()
        self.trace_data = [] 
        
        self.entries_scanned = 0
        self.files_collected = 0
        self.funcs_total = 0
        self.funcs_accepted = 0
        self.funcs_rejected_empty = 0

    def log_entry(self, entry_id, status, count=0):
        # 仅记录被接受的条目，避免日志文件过大，但保留统计信息
        if status == "accepted":
            self.trace_data.append({
                "entry_id": entry_id,
                "status": status,
                "funcs_count": count,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            })
            print(f"  [√] Accepted Entry {entry_id} | Got {count} funcs")

    def save_logs(self):
        # 保存 Trace
        with open(os.path.join(LOG_DIR, f"{self.lang}_pos_trace.json"), 'w', encoding='utf-8') as f:
            json.dump(self.trace_data, f, indent=2)
            
        # 保存 Summary
        summary = {
            "language": self.lang,
            "duration": round(time.time() - self.start_time, 2),
            "scanned_entries": self.entries_scanned,
            "collected_files": self.files_collected,
            "extracted_functions": self.funcs_total,
            "accepted_functions": self.funcs_accepted,
            "rejected_empty": self.funcs_rejected_empty,
            "completion_status": "Success" if self.files_collected >= TARGET_FILE_COUNT else "Incomplete"
        }
        with open(os.path.join(LOG_DIR, f"{self.lang}_pos_summary.json"), 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"  [Log] {self.lang} summary saved.")

# ==================== 2. 工具函数 (Hash & Check) ====================
def calculate_sha256(text):
    """科研级去重：使用 SHA-256 并在计算前去除空白，忽略格式差异"""
    clean = re.sub(r'\s+', '', text)
    return hashlib.sha256(clean.encode('utf-8')).hexdigest()

def is_empty_function(code_str):
    """
    定义：仅包含空白字符或空花括号的函数视为'空'。
    注意：包含注释的函数 { // comment } 在此逻辑下不算空，
    这符合代码语义学（注释也是信息）。
    """
    clean = re.sub(r'\s+', '', code_str)
    return clean in ['', '{}', '{;}']

# ==================== 3. Tree-sitter 解析 ====================
parsers = {}
langs_def = {
    'java': tree_sitter_java.language(),
    'c': tree_sitter_c.language(),
    'javascript': tree_sitter_javascript.language()
}
for k, v in langs_def.items():
    parsers[k] = Parser(Language(v))

NODE_TYPES = {
    'java': ['method_declaration', 'constructor_declaration'],
    'c': ['function_definition'],
    'javascript': ['function_declaration', 'method_definition'] 
}

def extract_functions(code_text, lang, stats):
    try:
        tree = parsers[lang].parse(bytes(code_text, "utf8"))
        extracted = []
        
        def traverse(node):
            if node.type in NODE_TYPES[lang]:
                stats.funcs_total += 1
                func_bytes = code_text.encode('utf8')[node.start_byte : node.end_byte]
                func_str = func_bytes.decode('utf8', errors='ignore')
                
                if not is_empty_function(func_str):
                    # 记录 SHA256 指纹，方便后续查重
                    fingerprint = calculate_sha256(func_str)
                    extracted.append({
                        "code": func_str,
                        "fingerprint": fingerprint,
                        "start_byte": node.start_byte,
                        "end_byte": node.end_byte
                    })
                else:
                    stats.funcs_rejected_empty += 1
                return 
            for child in node.children:
                traverse(child)
        
        traverse(tree.root_node)
        return extracted
    except:
        return []

def detect_language(text):
    # 简单的启发式规则，仅用于辅助 Pile 数据集分类
    if "public class" in text and ("static void" in text or "public" in text): return 'java'
    if "#include" in text and ("int main" in text or "void " in text): return 'c'
    if "function " in text or ("const " in text and "=>" in text): return 'javascript'
    return None

# ==================== 主流程 ====================
def main():
    print(">>> [Positive] Connecting to The Pile (Streaming)...")
    ds = load_dataset("EleutherAI/the_pile_deduplicated", split="train", streaming=True)
    
    stats_map = {lang: Statistics(lang) for lang in TARGET_LANGS}
    
    # 对应语言的输出文件
    out_files = {
        lang: open(os.path.join(OUTPUT_DIR, f"{lang}_positive.jsonl"), "w", encoding="utf-8") 
        for lang in TARGET_LANGS
    }

    print("\n>>> Start Sampling...")

    try:
        for i, sample in enumerate(ds):
            # 终止条件：所有语言都采够了
            if all(s.files_collected >= TARGET_FILE_COUNT for s in stats_map.values()):
                break

            code = sample['text']
            lang = detect_language(code)
            
            if not lang: continue
            
            curr_stats = stats_map[lang]
            curr_stats.entries_scanned += 1
            
            if curr_stats.files_collected >= TARGET_FILE_COUNT:
                continue
            
            # 提取
            valid_funcs_data = extract_functions(code, lang, curr_stats)
            
            # 筛选逻辑：单文件必须够 10 个，保证 Context 密度
            if len(valid_funcs_data) >= FUNCS_PER_FILE:
                selected = valid_funcs_data[:FUNCS_PER_FILE]
                
                for item in selected:
                    record = {
                        "code": item['code'],
                        "language": lang,
                        "source_id": i,
                        "origin": "ThePile",
                        "fingerprint": item['fingerprint'] # 保留指纹用于验证
                    }
                    out_files[lang].write(json.dumps(record) + "\n")
                
                out_files[lang].flush()
                curr_stats.funcs_accepted += len(selected)
                curr_stats.files_collected += 1
                curr_stats.log_entry(i, "accepted", len(selected))
                
    except KeyboardInterrupt:
        print("\n[Stop] User interrupted.")
    finally:
        for f in out_files.values(): f.close()
        for s in stats_map.values(): s.save_logs()
        print("\n>>> Positive Sampling Finished.")

if __name__ == "__main__":
    main()