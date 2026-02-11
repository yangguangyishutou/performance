import requests
import time
import json
import os

# ================= 配置区 =================
GITHUB_TOKEN = "your_token" # 【请务必填回您的Token】
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
CUTOFF_DATE = "2024-01-01"

# 路径设置
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
BASE_DIR = os.path.join(root_dir, "data", "negative")
OUTPUT_DIR = os.path.join(root_dir, "data", "final")

if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)

FILES_CONFIG = {
    "c": "c_negative.jsonl",
    "java": "java_negative.jsonl",
    "javascript": "javascript_negative.jsonl"
}

# ================= 暴力指纹提取 =================
def get_brute_force_snippet(content):
    if not content: return None
    # 压缩为一行，去除多余空格
    clean_code = content.replace('\\n', ' ').replace('\n', ' ').replace('\t', ' ')
    clean_code = " ".join(clean_code.split())
    
    snippet = clean_code[:100]
    if len(snippet) < 10: return None
    return snippet

# ================= 智能查重逻辑 (自适应休眠) =================
def check_github(snippet, lang):
    """
    智能版：根据 Header 里的剩余次数自动决定休眠多久
    """
    query = f'"{snippet}" language:{lang}'
    
    try:
        # 基础等待，避免过于频繁
        time.sleep(2) 
        
        resp = requests.get("https://api.github.com/search/code", headers=HEADERS, 
                          params={"q": query, "per_page": 5})
        
        # --- 核心修改：读取 GitHub 告诉我们的剩余额度 ---
        # x-ratelimit-remaining: 这一分钟还剩几次
        # x-ratelimit-reset: 重置时间戳
        remaining = int(resp.headers.get("X-RateLimit-Remaining", 10))
        reset_time = int(resp.headers.get("X-RateLimit-Reset", time.time() + 60))
        
        # 打印调试信息，让你看着安心
        # print(f" [剩余额度: {remaining}]", end="") 
        
        # 如果剩余次数少于 2 次，通过计算时间差，精确睡眠
        if remaining < 2:
            sleep_time = reset_time - int(time.time()) + 2 # 多睡2秒求稳
            if sleep_time > 0:
                print(f"⏳ 额度耗尽，智能休眠 {sleep_time} 秒...", end="\r")
                time.sleep(sleep_time)

        # 处理常规限流报错 (双重保险)
        if resp.status_code in [403, 429]:
            print("⏳ 触发滥用检测，强制休息 60 秒...", end="\r")
            time.sleep(60)
            return check_github(snippet, lang)

        data = resp.json()
        total = data.get("total_count", 0)
        
        if total == 0:
            return True, None
            
        items = data.get("items", [])
        for item in items:
            repo_url = item["repository"]["url"]
            html_url = item["repository"]["html_url"]
            
            try:
                r_resp = requests.get(repo_url, headers=HEADERS)
                # 仓库详情接口限额很高(5000/h)，一般不需要像搜索接口那样小心，但还是做个防错
                if r_resp.status_code in [403, 429]:
                    time.sleep(10) 
                    r_resp = requests.get(repo_url, headers=HEADERS)
                
                repo_info = r_resp.json()
                created_at = repo_info.get("created_at", "2099-01-01")
                
                if created_at < CUTOFF_DATE:
                    print(f"   ❌ 撞车: {item['repository']['full_name']} ({created_at[:10]})")
                    return False, html_url
            except:
                pass
        
        return True, None

    except Exception as e:
        print(f"   ⚠️ 请求出错: {e}")
        # 出错时保守起见休眠一下
        time.sleep(5)
        return False, "Error"

# ================= 主程序 =================
def main():
    print(f"读取目录: {BASE_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    
    for lang, fname in FILES_CONFIG.items():
        fpath = os.path.join(BASE_DIR, fname)
        # 干净文件的路径
        clean_outpath = os.path.join(OUTPUT_DIR, fname)
        # 【新增】被剔除文件的日志路径 (例如: c_negative_removed.jsonl)
        removed_outpath = os.path.join(OUTPUT_DIR, fname.replace(".jsonl", "_removed.jsonl"))
        
        if not os.path.exists(fpath):
            print(f"⚠️ 文件不存在: {fname}")
            continue
            
        print(f"\n>>> 处理 {fname}...")
        
        valid_samples = []   # 存放干净数据
        removed_samples = [] # 存放脏数据
        
        with open(fpath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        total = len(lines)
        
        for i, line in enumerate(lines):
            try:
                entry = json.loads(line)
                code_content = entry.get("code", "")
                snippet = get_brute_force_snippet(code_content)
                
                print(f"[{i+1}/{total}] ", end="")
                
                if not snippet:
                    print("⚠️ 代码为空或过短，跳过")
                    continue
                
                # print(f"搜: {snippet[:30]}... -> ", end="")
                
                # 获取结果和证据
                is_clean, evidence = check_github(snippet, lang)
                
                if is_clean:
                    print("✅ 通过")
                    valid_samples.append(entry)
                else:
                    print("🗑️ 剔除")
                    # 【记录证据】把找到的仓库地址写进数据里，方便你复查
                    entry["found_in_repo"] = evidence
                    removed_samples.append(entry)
                    
            except json.JSONDecodeError:
                print("JSON解析失败")

        # 1. 保存干净的数据
        with open(clean_outpath, 'w', encoding='utf-8') as f:
            for s in valid_samples:
                f.write(json.dumps(s, ensure_ascii=False) + '\n')
        
        # 2. 【新增】保存剔除的数据日志
        if removed_samples:
            with open(removed_outpath, 'w', encoding='utf-8') as f:
                for s in removed_samples:
                    f.write(json.dumps(s, ensure_ascii=False) + '\n')
            print(f"📝 已生成剔除日志: {os.path.basename(removed_outpath)} (共 {len(removed_samples)} 条)")
        else:
            print("🎉 真棒！没有数据被剔除。")

if __name__ == "__main__":
    main()