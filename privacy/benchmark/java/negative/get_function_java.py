import requests
import json
import re
from datetime import datetime
import time
import os

# 配置参数
GITHUB_TOKEN = ''

HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 搜索2024年后创建且有活动的Java仓库
SEARCH_QUERY = "language:java created:>=2024-01-01 pushed:>=2024-01-01"
OUTPUT_FILE = "negative_raw.jsonl"
FUNCTIONS_PER_REPO = 30  # 每个仓库最多收集的函数数量

def parse_java_functions(source_code):
    """解析Java代码并返回函数列表"""
    # 匹配Java方法的正则表达式
    method_pattern = re.compile(r'''
        (?:public|private|protected|static|abstract|final|native|synchronized|transient|\s)*\s*  # 修饰符
        ([\w<>\[\]\.]+)\s+                            # 返回类型
        (\w+)\s*                                     # 方法名
        \(([^)]*)\)                                  # 参数列表
        \s*\{                                        # 开始大括号
        ([\s\S]*?)                                   # 方法体
        \}                                            # 结束大括号
    ''', re.VERBOSE | re.MULTILINE)
    
    functions = []
    
    for match in method_pattern.finditer(source_code):
        return_type = match.group(1).strip()
        method_name = match.group(2)
        parameters = match.group(3).strip()
        method_body = match.group(4).strip()
        
        # 提取方法签名和完整代码
        method_signature = f"{return_type} {method_name}({parameters})"
        method_code = f"{method_signature} {{\n{method_body}\n}}"
        
        functions.append({
            'name': method_name,
            'signature': method_signature,
            'code': method_code
        })
    
    return functions

def fetch_github_api(url, params=None):
    """发送GitHub API请求并处理速率限制"""
    while True:
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=30)
            if response.status_code == 403 and 'rate limit' in response.text.lower():
                reset_time = int(response.headers.get('X-RateLimit-Reset', 0))
                sleep_time = max(reset_time - time.time(), 0) + 5
                print(f"速率限制，等待 {sleep_time:.1f}秒")
                time.sleep(sleep_time)
                continue
            return response
        except requests.exceptions.RequestException as e:
            print(f"请求异常: {str(e)}，重试中...")
            time.sleep(10)

def get_file_creation_date(repo_full_name, file_path, commit_sha):
    """获取文件的创建日期（首次提交日期）"""
    # 获取文件的提交历史
    commits_url = f"https://api.github.com/repos/{repo_full_name}/commits?path={file_path}&per_page=100"
    commits_response = fetch_github_api(commits_url)
    
    if commits_response.status_code != 200:
        return None
    
    commits = commits_response.json()
    if not commits:
        return None
    
    # 最后一个提交是文件的首次提交
    first_commit = commits[-1]
    return first_commit['commit']['committer']['date']

def main():
    page = 1
    processed_files = set()
    
    with open(OUTPUT_FILE, 'w') as out_file:
        while True:
            # 搜索符合条件的仓库
            search_url = f"https://api.github.com/search/repositories?q={SEARCH_QUERY}&per_page=100&page={page}"
            response = fetch_github_api(search_url)
            
            if response.status_code != 200:
                print(f"搜索失败: {response.status_code} - {response.text}")
                break
                
            data = response.json()
            if not data.get('items'):
                print(f"第 {page} 页没有搜索结果，退出")
                break
                
            print(f"处理第 {page} 页，共 {len(data['items'])} 个仓库")
            
            for repo_item in data['items']:
                repo_full_name = repo_item['full_name']
                stars = repo_item['stargazers_count']
                print(f"\n处理仓库: {repo_full_name} (星标: {stars})")
                
                # 初始化仓库函数计数器
                repo_function_count = 0
                
                # 获取仓库的默认分支
                repo_url = f"https://api.github.com/repos/{repo_full_name}"
                repo_response = fetch_github_api(repo_url)
                if repo_response.status_code != 200:
                    continue
                default_branch = repo_response.json().get('default_branch', 'main')
                
                # 获取仓库中的Java文件列表（递归获取）
                contents_url = f"https://api.github.com/repos/{repo_full_name}/contents?ref={default_branch}"
                stack = [contents_url]
                
                while stack:
                    # 检查是否达到函数数量限制
                    if repo_function_count >= FUNCTIONS_PER_REPO:
                        print(f"已从 {repo_full_name} 收集 {repo_function_count} 个函数，达到上限，切换到下一个仓库")
                        break
                    
                    current_url = stack.pop()
                    contents_response = fetch_github_api(current_url)
                    
                    if contents_response.status_code != 200:
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
                        elif item['name'].endswith('.java'):
                            file_path = item['path']
                            file_id = f"{repo_full_name}/{file_path}"
                            
                            if file_id in processed_files:
                                continue
                            processed_files.add(file_id)
                            
                            # 获取文件的创建日期
                            download_url = item['download_url']
                            file_response = requests.get(download_url)
                            
                            if file_response.status_code != 200:
                                continue
                            
                            # 获取文件内容的同时获取SHA（用于查询提交历史）
                            content_data = file_response.json() if 'json' in file_response.headers.get('Content-Type', '') else {}
                            sha = content_data.get('sha', '')
                            
                            # 获取文件创建日期
                            creation_date_str = get_file_creation_date(repo_full_name, file_path, sha)
                            if not creation_date_str:
                                continue
                            
                            creation_date = datetime.strptime(creation_date_str, "%Y-%m-%dT%H:%M:%SZ")
                            
                            # 严格检查文件创建日期
                            if creation_date < datetime(2024, 1, 1):
                                print(f"文件 {file_id} 创建于 {creation_date_str}，早于2024-01-01，跳过")
                                continue
                            
                            # 解析文件中的函数
                            source_code = file_response.text
                            functions = parse_java_functions(source_code)
                            
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
                                
                    # 检查是否需要跳出目录处理循环
                    if repo_function_count >= FUNCTIONS_PER_REPO:
                        break
                
                print(f"完成处理仓库 {repo_full_name}，共收集 {repo_function_count} 个函数")
            
            # 检查是否还有下一页
            if 'next' in response.links:
                page += 1
            else:
                print(f"没有下一页，处理完成")
                break

if __name__ == "__main__":
    main()    