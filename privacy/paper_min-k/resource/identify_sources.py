#!/usr/bin/env python
"""identify_sources.py

从包含 Python 函数的 JSONL 文件（字段 "function"）中抽取函数签名，
利用 GitHub Code Search API 反向定位原始源码文件。

脚本统计：
1. 成功定位到的唯一 (repo/path) 文件数量；
2. 涉及的唯一仓库数量；
3. 为每条函数记录其匹配到的文件。

结果以 CSV 格式保存：func_index,repo,path

用法示例：
    export GITHUB_TOKEN=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   
    # 或在 PowerShell: setx GITHUB_TOKEN "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"
    python identify_sources.py \
        --jsonl python_dataset/positive/positive.jsonl \
        --output mapping.csv

注意：
• GitHub Search 速率限制：30 次/分钟 (authenticated)。脚本会根据响应头自动等待。
• 仅请求每个查询首个匹配 (per_page=1) 并添加 fork:false 过滤；
  若仍想严格排除 fork，可检查 repository["fork"] 字段。
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.parse as ul
from pathlib import Path
from typing import Dict, Set, Tuple

import requests
import re

API_ENDPOINT = "https://api.github.com/search/code"
HEADERS_BASE = {
    "Accept": "application/vnd.github.v3.text-match+json",
}


def _sanitize(text: str) -> str:
    """Remove characters that break GitHub search parsing (e.g., \" and backticks)."""
    remove_chars = '"`'
    return ''.join(ch for ch in text if ch not in remove_chars)


def extract_query(src: str, max_len: int = 120) -> str:
    """Construct a safe GitHub search query from a function snippet.

    We primarily use the first non-empty line (function signature) which is usually unique enough.
    To increase discrimination, append the next non-empty line *if* it doesn't contain quotes that
    could break query parsing. All double quotes/backticks are stripped. The combined string is
    truncated to *max_len* characters.
    """
    lines = [ln.strip() for ln in src.splitlines() if ln.strip()]
    if not lines:
        return ""

    sig = _sanitize(lines[0])
    # candidate for extra context
    next_line_raw = lines[1] if len(lines) > 1 else ""
    next_line = _sanitize(next_line_raw)

    candidate = f"{sig} {next_line}".strip()
    combined = candidate[:max_len]

    # Wrap in quotes to force exact phrase search; language filter restricts to python.
    return f'"{combined}" language:python fork:false'


def github_search(query: str, token: str | None) -> Tuple[str | None, str | None]:
    """Run GitHub code search; return (repo_full_name, file_path) for first match, else (None, None)."""
    if not query:
        return None, None
    params = {
        "q": query,
        "per_page": 1,
    }
    headers = dict(HEADERS_BASE)
    if token:
        headers["Authorization"] = f"token {token}"
    url = f"{API_ENDPOINT}?{ul.urlencode(params)}"
    while True:
        resp = requests.get(url, headers=headers)
        if resp.status_code == 403 and resp.headers.get("X-RateLimit-Remaining") == "0":
            # Hit the rate limit – wait until reset
            reset_ts = int(resp.headers.get("X-RateLimit-Reset", "0"))
            sleep_sec = max(reset_ts - int(time.time()) + 1, 60)
            print(f"Rate-limited. Sleeping {sleep_sec}s …", file=sys.stderr)
            time.sleep(sleep_sec)
            continue  # retry
        if resp.status_code == 422:
            # query parse error – return sentinel to invoke fallback
            return "__QUERY_ERROR__", None
        if resp.status_code != 200:
            print(f"Warning: GitHub API returned {resp.status_code}: {resp.text[:200]}", file=sys.stderr)
            return None, None
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return None, None
        item = items[0]
        repo = item["repository"]["full_name"]
        path = item["path"]
        return repo, path


def main():
    parser = argparse.ArgumentParser(description="Locate original GitHub source files for functions in JSONL dataset.")
    parser.add_argument("--jsonl", required=True, help="Path to JSONL file with 'function' field.")
    parser.add_argument("--output", default="mapping.csv", help="Output CSV file (func_index,repo,path).")
    parser.add_argument("--limit", type=int, default=None, help="Only process first N functions (debugging).")
    parser.add_argument("--sleep", type=float, default=2.0, help="Seconds to sleep between requests (basic throttle).")
    args = parser.parse_args()

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("[WARN] Environment variable GITHUB_TOKEN not set – proceeding unauthenticated (very low rate limit)", file=sys.stderr)

    jsonl_path = Path(args.jsonl)
    if not jsonl_path.is_file():
        parser.error(f"JSONL file not found: {jsonl_path}")

    unique_files: Set[str] = set()
    unique_repos: Set[str] = set()

    with jsonl_path.open(encoding="utf-8") as fp, open(args.output, "w", newline="", encoding="utf-8", buffering=1) as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["func_index", "repo", "path"])

        for idx, line in enumerate(fp, 1):
            if args.limit and idx > args.limit:
                break
            try:
                obj = json.loads(line)
                func_src = obj["function"]
            except (json.JSONDecodeError, KeyError):
                print(f"Skipping malformed line {idx}", file=sys.stderr)
                continue

            query_primary = extract_query(func_src)
            repo, path = github_search(query_primary, token)

            # fallback for 422 parse errors
            if repo == "__QUERY_ERROR__":
                func_name_match = re.search(r"def\s+([a-zA-Z0-9_]+)\s*\(", func_src)
                if func_name_match:
                    func_name = func_name_match.group(1)
                    query_secondary = f'"def {func_name}(" language:python fork:false'
                    repo, path = github_search(query_secondary, token)

            if repo and path and repo != "__QUERY_ERROR__":
                file_id = f"{repo}/{path}"
                unique_files.add(file_id)
                unique_repos.add(repo)
                writer.writerow([idx, repo, path])
                csvfile.flush()
                print(f"[{idx}] OK  -> {repo}/{path}", file=sys.stderr)
            else:
                writer.writerow([idx, "", ""])
                csvfile.flush()
                print(f"[{idx}] FAIL", file=sys.stderr)

            if idx % 50 == 0:
                print(f"Processed {idx} functions – found {len(unique_files)} unique files so far", file=sys.stderr)

            time.sleep(args.sleep)

    print("========== SUMMARY ==========")
    print(f"Total functions processed : {idx}")
    print(f"Located unique files      : {len(unique_files)}")
    print(f"Located unique repositories: {len(unique_repos)}")
    print(f"Detailed mapping written to {args.output}")


if __name__ == "__main__":
    main() 