import requests
import json
import ast
from datetime import datetime
import time
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# 配置参数
GITHUB_TOKEN = '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'

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 搜索2024年后创建且有活动的Python仓库
SEARCH_QUERY = "language:python created:>=2024-01-01"
OUTPUT_FILE = "negative_raw.jsonl"
STATE_FILE = "crawler_state.json"  # 保存爬取状态的文件
FUNCTIONS_PER_REPO = 10  # 每个仓库最多收集的函数数量
MAX_RETRIES = 10  # 请求最大重试次数
RETRY_BACKOFF_FACTOR = 2  # 重试等待时间倍数
NETWORK_ERROR_SLEEP = 30  # 网络错误后的等待时间（秒）

def create_session():
    """创建带有重试机制的requests会话"""
    session = requests.Session()
    
    # 设置重试策略
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        status_forcelist=[429, 500, 502, 503, 504, 408],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    # 应用重试策略到HTTP和HTTPS连接
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    
    return session

def save_state(state):
    """保存当前爬取状态到文件"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f)

def load_state():
    """从文件加载爬取状态"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {
        'current_page': 1,
        'processed_repos': [],
        'processed_files': set(),
        'repo_function_counts': {}
    }

def parse_functions(source_code):
    """解析Python代码并返回函数列表"""
    try:
        tree = ast.parse(source_code)
    except Exception as e:
        print(f"解析代码失败: {str(e)}")
        return []
    
    functions = []
    source_lines = source_code.split('\n')
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not hasattr(node, 'end_lineno'):
                continue  # 跳过无法获取结束行号的函数
            
            start_line = node.lineno - 1
            end_line = node.end_lineno
            function_code = '\n'.join(source_lines[start_line:end_line])
            
            functions.append({
                'name': node.name,
                'code': function_code
            })
    
    return functions

def fetch_github_api(url, params=None, session=None):
    """发送GitHub API请求并处理速率限制和网络异常"""
    if not session:
        session = create_session()
        
    retries = 0
    
    while retries < MAX_RETRIES:
        try:
            response = session.get(url, headers=HEADERS, params=params, timeout=60, verify=True)
            
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = max(reset_time - time.time(), 0) + 5
                print(f"速率限制，等待 {sleep_time:.1f}秒")
                time.sleep(sleep_time)
                continue
                
            return response
            
        except requests.exceptions.SSLError as e:
            print(f"SSL错误: {str(e)}，尝试第 {retries+1}/{MAX_RETRIES} 次重试")
            retries += 1
            time.sleep(NETWORK_ERROR_SLEEP)  # 网络错误后等待更长时间
            
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {str(e)}，尝试第 {retries+1}/{MAX_RETRIES} 次重试")
            retries += 1
            time.sleep(NETWORK_ERROR_SLEEP)  # 网络错误后等待更长时间
    
    print(f"达到最大重试次数，跳过URL: {url}")
    return None

def get_file_creation_date(repo_full_name, file_path, commit_sha, session=None):
    """获取文件的创建日期（首次提交日期）"""
    # 获取文件的提交历史
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits?path={file_path}&per_page=100"
    commits_response = fetch_github_api(commits_url, session=session)
    
    if not commits_response or commits_response.status_code != 200:
        return None
    
    commits = commits_response.json()
    if not commits:
        return None
    
    # 最后一个提交是文件的首次提交
    first_commit = commits[-1]
    return first_commit['commit']['committer']['date']

def main():
    # 加载保存的状态
    state = load_state()
    page = state['current_page']
    processed_repos = state['processed_repos']
    processed_files = set(state.get('processed_files', []))
    repo_function_counts = state.get('repo_function_counts', {})
    
    session = create_session()
    
    with open(OUTPUT_FILE, 'a') as out_file:  # 以追加模式打开
        while True:
            # 搜索符合条件的仓库
            search_url = f"https://api.github.com/search/repositories?q={SEARCH_QUERY}&per_page=100&page={page}"
            response = fetch_github_api(search_url, session=session)
            
            if not response or response.status_code != 200:
                print(f"搜索失败，等待 {NETWORK_ERROR_SLEEP} 秒后重试")
                time.sleep(NETWORK_ERROR_SLEEP)
                continue
                
            data = response.json()
            if not data.get('items'):
                print(f"第 {page} 页没有搜索结果，退出")
                break
                
            print(f"处理第 {page} 页，共 {len(data['items'])} 个仓库")
            
            for repo_item in data['items']:
                repo_full_name = repo_item['full_name']
                
                # 跳过已处理的仓库
                if repo_full_name in processed_repos:
                    print(f"跳过已处理仓库: {repo_full_name}")
                    continue
                
                stars = repo_item['stargazers_count']
                print(f"\n处理仓库: {repo_full_name} (星标: {stars})")
                
                # 获取或初始化仓库函数计数器
                repo_function_count = repo_function_counts.get(repo_full_name, 0)
                
                # 获取仓库的默认分支
                repo_url = f"https://api.github.com/repos/{repo_full_name}"
                repo_response = fetch_github_api(repo_url, session=session)
                if not repo_response or repo_response.status_code != 200:
                    print(f"获取仓库信息失败，跳过 {repo_full_name}")
                    continue
                default_branch = repo_response.json().get('default_branch', 'main')
                
                # 获取仓库中的Python文件列表（递归获取）
                contents_url = f"https://api.github.com/repos/{repo_full_name}/contents?ref={default_branch}"
                stack = [contents_url]
                
                try:
                    while stack:
                        # 检查是否达到函数数量限制
                        if repo_function_count >= FUNCTIONS_PER_REPO:
                            print(f"已从 {repo_full_name} 收集 {repo_function_count} 个函数，达到上限，切换到下一个仓库")
                            break
                        
                        current_url = stack.pop()
                        contents_response = fetch_github_api(current_url, session=session)
                        
                        if not contents_response or contents_response.status_code != 200:
                            print(f"获取目录内容失败，跳过 {current_url}")
                            continue
                        
                        items = contents_response.json()
                        
                        for item in items:
                            # 检查是否达到函数数量限制
                            if repo_function_count >= FUNCTIONS_PER_REPO:
                                print(f"已从 {repo_full_name} 收集 {repo_function_count} 个函数，达到上限，切换到下一个仓库")
                                break
                                
                            if item['type'] == 'dir':
                                # 递归处理子目录
                                stack.append(item['url'])
                            elif item['name'].endswith('.py'):
                                file_path = item['path']
                                file_id = f"{repo_full_name}/{file_path}"
                                
                                if file_id in processed_files:
                                    continue
                                
                                # 获取文件内容
                                download_url = item['download_url']
                                file_response = fetch_github_api(download_url, session=session)
                                
                                if not file_response or file_response.status_code != 200:
                                    print(f"获取文件内容失败，跳过 {file_id}")
                                    continue
                                
                                # 获取文件内容的同时获取SHA（用于查询提交历史）
                                content_data = file_response.json() if 'json' in file_response.headers.get('Content-Type', '') else {}
                                sha = content_data.get('sha', '')
                                
                                # 获取文件创建日期
                                creation_date_str = get_file_creation_date(repo_full_name, file_path, sha, session=session)
                                if not creation_date_str:
                                    print(f"获取文件创建日期失败，跳过 {file_id}")
                                    continue
                                
                                creation_date = datetime.strptime(creation_date_str, "%Y-%m-%dT%H:%M:%SZ")
                                
                                # 严格检查文件创建日期
                                if creation_date < datetime(2024, 1, 1):
                                    print(f"文件 {file_id} 创建于 {creation_date_str}，早于2024-01-01，跳过")
                                    continue
                                
                                # 解析文件中的函数
                                source_code = file_response.text
                                functions = parse_functions(source_code)
                                
                                if not functions:
                                    print(f"文件 {file_id} 中未找到函数")
                                    continue
                                
                                print(f"从文件 {file_id} 中解析出 {len(functions)} 个函数")
                                
                                # 写入函数记录并更新计数器
                                for func in functions:
                                    if repo_function_count >= FUNCTIONS_PER_REPO:
                                        break
                                        
                                    record = {
                                        'function': func['code'],
                                        'creation_date': creation_date_str,
                                        'repo': repo_full_name,
                                        'file_path': file_path,
                                        'stars': stars,
                                        'label': 0
                                    }
                                    out_file.write(json.dumps(record) + '\n')
                                    repo_function_count += 1
                                    
                                    # 每处理10个函数保存一次状态
                                    if repo_function_count % 10 == 0:
                                        state = {
                                            'current_page': page,
                                            'processed_repos': processed_repos,
                                            'processed_files': list(processed_files),
                                            'repo_function_counts': repo_function_counts
                                        }
                                        save_state(state)
                                        print(f"已保存状态: 仓库 {repo_full_name} 已收集 {repo_function_count} 个函数")
                                
                                # 标记文件为已处理
                                processed_files.add(file_id)
                                
                        # 每处理完一个目录保存一次状态
                        state = {
                            'current_page': page,
                            'processed_repos': processed_repos,
                            'processed_files': list(processed_files),
                            'repo_function_counts': repo_function_counts
                        }
                        save_state(state)
                    
                except KeyboardInterrupt:
                    print("检测到用户中断，保存当前状态...")
                    state = {
                        'current_page': page,
                        'processed_repos': processed_repos,
                        'processed_files': list(processed_files),
                        'repo_function_counts': repo_function_counts
                    }
                    save_state(state)
                    print("状态已保存，程序退出。下次运行将从上次中断处继续。")
                    return
                    
                except Exception as e:
                    print(f"处理仓库 {repo_full_name} 时发生意外错误: {str(e)}")
                    print("保存当前状态，跳过该仓库...")
                    state = {
                        'current_page': page,
                        'processed_repos': processed_repos,
                        'processed_files': list(processed_files),
                        'repo_function_counts': repo_function_counts
                    }
                    save_state(state)
                    continue
                
                # 更新仓库函数计数
                repo_function_counts[repo_full_name] = repo_function_count
                
                # 标记仓库为已处理
                processed_repos.append(repo_full_name)
                
                # 保存状态
                state = {
                    'current_page': page,
                    'processed_repos': processed_repos,
                    'processed_files': list(processed_files),
                    'repo_function_counts': repo_function_counts
                }
                save_state(state)
                
                print(f"完成处理仓库 {repo_full_name}，共收集 {repo_function_count} 个函数")
            
            # 检查是否还有下一页
            if 'next' in response.links:
                page += 1
                # 保存页码状态
                state = {
                    'current_page': page,
                    'processed_repos': processed_repos,
                    'processed_files': list(processed_files),
                    'repo_function_counts': repo_function_counts
                }
                save_state(state)
                print(f"保存状态: 即将处理第 {page} 页")
            else:
                print(f"没有下一页，处理完成")
                break

if __name__ == "__main__":
    main()

'''
### 主要改进

1. **断点续传功能**：
   - 添加状态保存和加载机制
   - 记录已处理的仓库、文件和函数数量
   - 支持从上次中断的位置继续爬取

2. **增强的网络容错能力**：
   - 增加最大重试次数到10次
   - 网络错误后等待30秒再重试
   - 处理更多类型的HTTP错误状态码

3. **定期保存状态**：
   - 每处理10个函数保存一次状态
   - 每个目录处理完成后保存状态
   - 支持手动中断并保存当前进度

4. **文件追加模式**：
   - 以追加模式打开输出文件
   - 避免覆盖已收集的函数数据

### 使用说明

1. 正常运行脚本：
   ```bash
   python collect_script.py
   ```

2. 如需从头开始，删除状态文件：
   ```bash
   rm crawler_state.json
   ```

3. 网络恢复后，直接重新运行脚本即可从中断处继续

4. 调整参数：
   ```python
   # 增加重试次数或延长等待时间
   MAX_RETRIES = 15
   NETWORK_ERROR_SLEEP = 60
'''
