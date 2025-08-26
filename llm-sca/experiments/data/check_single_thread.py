import requests
import json
import time
import random
from urllib.parse import quote
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from tqdm import tqdm
import sys

# ------------ 配置 ------------
INPUT_DATA_FILE = "./data/new/test_adjacent_pairs.jsonl"
OUTPUT_REPORT = "./data/new/teat_model_validation_report.json"
REQUEST_INTERVAL = (0.1, 0.5)  # 请求间隔区间（秒）
# ------------ 配置结束 ------------

retry_strategy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)


def create_session():
    """创建全局或单次请求的 Session"""
    session = requests.Session()
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def get_all_files(session, model_full_name):
    """带流量控制的文件列表获取"""
    files = []
    stack = [('main',)]
    visited = set()

    while stack:
        time.sleep(random.uniform(*REQUEST_INTERVAL))
        current_path = stack.pop()
        path_str = '/'.join(current_path)
        if path_str in visited:
            continue
        visited.add(path_str)

        url = f"https://huggingface.co/api/models/{quote(model_full_name)}/tree/{path_str}"
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                continue
            for item in resp.json():
                if item['type'] == 'file':
                    full_path = f"{path_str}/{item['path']}" if path_str != 'main' else item['path']
                    files.append(full_path)
                elif item['type'] == 'directory':
                    stack.append(current_path + (item['path'],))
        except Exception:
            # 可选：打印或记录单个目录失败
            continue

    return files


def process_model(session, data_id, model_name, derive_type, father_model, is_father = False):
    """处理单个模型"""
    
    try:
        files = get_all_files(session, model_name)
        has_config = any(f.lower().endswith('config.json') for f in files)
        has_adapter_config = any(f.lower().endswith('adapter_config.json') for f in files)
        has_parameters = any(f.lower().endswith('.bin') for f in files) or \
            any(f.lower().endswith('.pt') for f in files) or \
            any(f.lower().endswith('.safetensors') for f in files)  or \
            any(f.lower().endswith('.ckpt') for f in files) or \
            any(f.lower().endswith('.gguf') for f in files) or \
            any(f.lower().endswith('.pth') for f in files) or \
            any(f.lower().endswith('.onnx') for f in files)
        has_gguf = any(f.lower().endswith('.gguf') for f in files)
        # 派生类型检查
        if derive_type == "adapter":
            type_mismatch = not has_adapter_config
        elif derive_type in ("finetune", "merge"):
            type_mismatch = not has_config
        elif derive_type == "quantized":
            type_mismatch = False
        else:
            type_mismatch = not (has_config or has_adapter_config)


        if not is_father:
            father_model_true = process_model(session, 9999, father_model, 0, 0, True)
            type_mismatch = type_mismatch or not father_model_true or not has_parameters

        # type_mismatch = type_mismatch or not has_parameters


        # 量化模型特殊逻辑
        error = type_mismatch

        if is_father:
            return has_parameters and (has_config or has_adapter_config)

        return {
            "id": data_id,
            "model": model_name,
            "derive_type": derive_type,
            "has_parameters": has_parameters,
            "father_model_true": father_model_true,
            "missing_config": not has_config,
            "missing_adapter_config": not has_adapter_config,
            "derive_type_mismatch": type_mismatch,
            "has_gguf": has_gguf,
            "file_count": len(files),
            "error": error
        }
    except Exception as e:
        print(f"处理失败 ID:{data_id} - {str(e)[:100]}", file=sys.stderr)
        return None


if __name__ == "__main__":
    # 读取数据
    try:
        with open(INPUT_DATA_FILE, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f]
    except FileNotFoundError:
        print(f"输入文件未找到: {INPUT_DATA_FILE}", file=sys.stderr)
        sys.exit(1)

    session = create_session()
    report = []

    # 单线程顺序处理
    for item in tqdm(data, desc="验证模型中"):
        result = process_model(session, item['id'], item['model'], item['derive_type'], item['base_model'])
        if result:
            report.append(result)

    # 排序并生成报告
    errors = [r for r in report if r['error']]
    try:
        report.sort(key=lambda x: x['id'])
        with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
            json.dump({
                "metadata": {"total_models": len(data), "errors": len(errors)},
                "results": report
            }, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"报告生成失败: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"验证完成，共处理 {len(report)} 个模型，其中错误 {len(errors)} 个。")
