#!/usr/bin/env python3
"""
批量语法约束提取脚本

从文档索引中读取所有构造，批量提取语法约束。

使用方法：
    python scripts/2_extract_constraints.py --language javascript
    python scripts/2_extract_constraints.py --language javascript --limit 5
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# 添加 scripts 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from llm_client import ZhipuLLMClient
from llm_client import load_prompt_template

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def print_success(msg):
    print(f"{GREEN}✓{RESET} {msg}")

def print_error(msg):
    print(f"{RED}✗{RESET} {msg}")

def print_info(msg):
    print(f"{BLUE}ℹ{RESET} {msg}")

def print_warning(msg):
    print(f"{YELLOW}⚠{RESET} {msg}")


def load_document_index(language: str) -> Dict[str, Any]:
    """
    加载语言文档索引

    Args:
        language: 语言名称 (javascript, java, c, python)

    Returns:
        文档索引字典
    """
    index_file = f"data/raw/{language}_index.json"

    if not os.path.exists(index_file):
        print_error(f"找不到文档索引: {index_file}")
        print_info(f"请先运行: python scripts/1_collect_docs.py --language {language}")
        sys.exit(1)

    with open(index_file, 'r', encoding='utf-8') as f:
        index = json.load(f)

    print_success(f"加载文档索引: {language} ({index['total_constructs']} 个构造)")
    print_info(f"包含语法: {index['constructs_with_syntax']}")

    return index


def get_constructs_to_extract(index: Dict[str, Any], limit: int = None) -> List[Dict[str, str]]:
    """
    获取需要提取的构造列表

    Args:
        index: 文档索引
        limit: 限制数量（用于测试）

    Returns:
        构造列表，每个元素包含 {name, doc, language}
    """
    constructs = []

    for construct_name, doc_data in index["index"].items():
        # 只处理包含语法的构造
        if not doc_data.get("has_syntax", False):
            continue

        construct = {
            "name": construct_name,
            "doc": doc_data.get("syntax", ""),
            "language": index["language"],
            "file": doc_data.get("file", "")
        }

        # 检查文档内容
        if not construct["doc"] or construct["doc"].strip() == "":
            print_warning(f"构造 {construct_name} 没有语法内容，跳过")
            continue

        constructs.append(construct)

        # 限制数量
        if limit and len(constructs) >= limit:
            break

    print_success(f"准备提取 {len(constructs)} 个构造")

    return constructs


def extract_single_construct(
    client: ZhipuLLMClient,
    construct: Dict[str, str],
    prompt_template: str,
    output_dir: str
) -> Dict[str, Any]:
    """
    提取单个构造的约束

    Args:
        client: LLM 客户端
        construct: 构造信息
        prompt_template: Prompt 模板
        output_dir: 输出目录

    Returns:
        提取的约束字典
    """
    construct_name = construct["name"]
    print(f"\n处理: {construct_name}")

    try:
        # 提取约束
        constraints = client.extract_constraints(
            documentation=construct["doc"],
            language=construct["language"],
            construct_name=construct_name,
            prompt_template=prompt_template,
            few_shot_examples=None,
            temperature=0.1,
            max_tokens=4096
        )

        # 添加元数据
        constraints["construct"] = construct_name
        constraints["language"] = construct["language"]
        constraints["source_file"] = construct["file"]
        constraints["extracted_at"] = datetime.now().isoformat()

        # 保存单个结果
        output_file = os.path.join(output_dir, f"{construct_name.replace('/', '_')}.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(constraints, f, ensure_ascii=False, indent=2)

        print_success(f"已保存: {output_file}")

        return constraints

    except Exception as e:
        print_error(f"提取失败: {e}")
        # 返回失败记录
        return {
            "construct": construct_name,
            "language": construct["language"],
            "error": str(e),
            "status": "failed"
        }


def batch_extract_constraints(
    constructs: List[Dict[str, str]],
    prompt_template: str,
    output_dir: str,
    client: ZhipuLLMClient,
    checkpoint: str = None
) -> Dict[str, Any]:
    """
    批量提取约束

    Args:
        constructs: 构造列表
        prompt_template: Prompt 模板
        output_dir: 输出目录
        client: LLM 客户端
        checkpoint: 检查点文件（用于断点续传）

    Returns:
        批量提取结果
    """
    total = len(constructs)
    results = []
    failed = []

    # 检查断点
    start_index = 0
    if checkpoint and os.path.exists(checkpoint):
        with open(checkpoint, 'r') as f:
            checkpoint_data = json.load(f)
            start_index = checkpoint_data.get("completed", 0)
            print_info(f"从断点恢复: {start_index}/{total}")

    print(f"\n开始批量提取: {start_index + 1}-{total} (共 {total - start_index} 个)")

    for i in range(start_index, total):
        construct = constructs[i]
        print(f"\n[{i+1}/{total}] ", end="")

        try:
            result = extract_single_construct(
                client=client,
                construct=construct,
                prompt_template=prompt_template,
                output_dir=output_dir
            )

            if "error" not in result:
                results.append(result)
            else:
                failed.append(result)

            # 更新断点（每 5 个保存一次）
            if (i + 1) % 5 == 0:
                checkpoint_data = {
                    "completed": i + 1,
                    "total": total,
                    "timestamp": datetime.now().isoformat()
                }
                with open(checkpoint, 'w') as f:
                    json.dump(checkpoint_data, f, indent=2)
                print_info(f"已保存断点: {checkpoint_data['completed']}/{total}")

        except KeyboardInterrupt:
            print_warning("\n\n用户中断")
            break

        except Exception as e:
            print_error(f"处理失败: {e}")
            failed.append({
                "construct": construct["name"],
                "error": str(e)
            })

    # 汇总
    print(f"\n\n{'='*70}")
    print(" 批量提取完成")
    print(f"{'='*70}")
    print(f"总构造数: {total}")
    print_success(f"成功: {len(results)}")
    if failed:
        print_error(f"失败: {len(failed)}")

    # 保存汇总结果
    summary = {
        "language": constructs[0]["language"] if constructs else "unknown",
        "total": total,
        "successful": len(results),
        "failed": len(failed),
        "extracted_at": datetime.now().isoformat(),
        "results": results,
        "failed": failed
    }

    summary_file = f"../{args.language}/data/{args.language}_extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print_success(f"汇总结果已保存到: {summary_file}")

    return summary


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量提取语法约束",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取所有 JavaScript 构造
  python scripts/2_extract_constraints.py --language javascript

  # 提取前 5 个构造（测试用）
  python scripts/2_extract_constraints.py --language javascript --limit 5

  # 从断点继续
  python scripts/2_extract_constraints.py --language javascript --checkpoint data/extracted/checkpoint.json
        """
    )

    parser.add_argument(
        "--language",
        choices=["javascript", "java", "c", "python"],
        default="javascript",
        help="目标语言"
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="限制提取数量（用于测试）"
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default=None,
        help="检查点文件路径（用于断点续传）"
    )

    parser.add_argument(
        "--prompt",
        type=str,
        default="prompts/base_prompt_cn_v4.0.txt",
        help="Prompt 模板文件路径"
    )

    args = parser.parse_args()

    print("="*70)
    print(" 批量语法约束提取")
    print("="*70)
    print(f"语言: {args.language}")
    print(f"Prompt: {args.prompt}")
    if args.limit:
        print(f"限制数量: {args.limit}")

    # 初始化输出目录（按语言分离）
    output_dir = f"../{args.language}/data"
    os.makedirs(output_dir, exist_ok=True)

    checkpoint_file = f"../{args.language}/data/checkpoint.json"

    # 加载文档索引
    index = load_document_index(args.language)

    # 获取构造列表
    constructs = get_constructs_to_extract(index, args.limit)

    if not constructs:
        print_error("没有找到需要提取的构造")
        return 1

    # 初始化 LLM 客户端
    try:
        client = ZhipuLLMClient()
        print_success("LLM 客户端初始化成功")
    except ValueError as e:
        print_error(f"LLM 客户端初始化失败: {e}")
        return 1

    # 加载 Prompt 模板
    try:
        prompt_template = load_prompt_template(args.prompt)
        print_success(f"加载 Prompt 模板: {args.prompt}")
    except Exception as e:
        print_error(f"加载 Prompt 失败: {e}")
        return 1

    # 开始批量提取
    try:
        summary = batch_extract_constraints(
            constructs=constructs,
            prompt_template=prompt_template,
            output_dir=output_dir,
            client=client,
            checkpoint=args.checkpoint or checkpoint_file
        )

        print(f"\n{GREEN}{'='*70}")
        print(" 提取完成！")
        print(f"{'='*70}{RESET}")
        print(f"成功率: {summary['successful']}/{summary['total']} ({summary['successful']/summary['total']*100:.1f}%)")

        return 0

    except KeyboardInterrupt:
        print_warning("\n\n用户中断")
        return 1

    except Exception as e:
        print_error(f"批量提取失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    main()
