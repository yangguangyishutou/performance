import requests
import json
import time
import random
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from requests.adapters import HTTPAdapter
from urllib.parse import quote
from requests.packages.urllib3.util.retry import Retry

# 配置重试策略 (应对429/5xx错误)
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

# 创建带重试的会话对象
def create_session():
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# 动态UA生成器
ua = UserAgent()

def scrape_huggingface_models(session, url):
    headers = {
        "User-Agent": ua.random,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://huggingface.co/",
        "DNT": "1"
    }
    
    try:
        time.sleep(random.uniform(1, 2))
        
        response = session.get(url, headers=headers, timeout=30)
        
        if response.status_code == 403:
            print("触发反爬限制，请考虑使用代理")
            return []
            
        if response.status_code != 200:
            print(f"请求失败: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        return [header["title"].strip() 
               for article in soup.find_all("article") 
               if (header := article.find("header")) and "title" in header.attrs]

    except Exception as e:
        print(f"请求异常: {str(e)}")
        return []

# 读取模型列表
# base_model_path = "models.txt"
base_model_path = "models_manual.txt"
with open(base_model_path, "r") as f:
    model_ids = [line.strip().split("/") for line in f if "/" in line]

com_types = ['finetune', 'adapter', 'quantized', 'merge']
# com_types = ['adapter', 'quantized', 'merge']
# com_types = ['merge']
# 3301 finetune
# 2443 adapter 
# 2663 quantized
# ? merge

# 创建全局会话
session = create_session()

for com_type in com_types:
    results = []
    
    for model_id in model_ids:
        # 参数编码处理
        base_id = f"{quote(model_id[0])}%2F{quote(model_id[1])}"
        # 只获取第一页
        url = f"https://huggingface.co/models?other=base_model:{com_type}:{base_id}&sort=likes"
        
        models = scrape_huggingface_models(session, url)
            
        results.extend({
            'base_model': f"{model_id[0]}/{model_id[1]}",
            'model': model,
            'type': com_type
        } for model in models[:10])
        
    # 保存结果时使用增量写入
    with open(f'model_pair_{com_type}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)

    print(f"Saved {len(results)} records to model_pair_{com_type}.json")

# 关闭会话
session.close()