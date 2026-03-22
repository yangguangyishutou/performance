#!/usr/bin/env python3
"""
批量语法约束提取脚本 - Batch 版本

一次 API 调用处理多个构造，节省 API 调用次数。
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
    """加载语言文档索引"""
    index_file = f"{language}/{language}_index.json"

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
    """获取需要提取的构造列表"""
    constructs = []

    for construct_name, doc_data in index["index"].items():
        if not doc_data.get("has_syntax", False):
            continue

        construct = {
            "name": construct_name,
            "doc": doc_data.get("syntax", ""),
            "language": index["language"],
            "file": doc_data.get("file", "")
        }

        if not construct["doc"] or construct["doc"].strip() == "":
            print_warning(f"构造 {construct_name} 没有语法内容，跳过")
            continue

        constructs.append(construct)

        if limit and len(constructs) >= limit:
            break

    print_success(f"准备提取 {len(constructs)} 个构造")

    return constructs


def batch_extract_constructs(
    client: ZhipuLLMClient,
    constructs: List[Dict[str, str]],
    prompt_template: str,
    batch_size: int = 5,
    output_dir: str = None,
    checkpoint: str = None
) -> Dict[str, Any]:
    """
    批量提取约束 - 一次 API 调用处理多个构造

    Args:
        client: LLM 客户端
        constructs: 构造列表
        prompt_template: Prompt 模板
        batch_size: 每次批量处理的构造数量
        output_dir: 输出目录
        checkpoint: 检查点文件

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

    # 分批处理
    num_batches = (total - start_index + batch_size - 1) // batch_size
    print(f"\n开始批量提取: {start_index + 1}-{total} (共 {total - start_index} 个)")
    print(f"分 {num_batches} 批处理，每批最多 {batch_size} 个构造\n")

    for batch_idx in range(start_index, total, batch_size):
        batch_end = min(batch_idx + batch_size, total)
        batch_constructs = constructs[batch_idx:batch_end]

        print(f"\n{'='*70}")
        print(f" 批次 {batch_idx // batch_size + 1}/{num_batches} (构造 {batch_idx + 1}-{batch_end})")
        print(f"{'='*70}")

        # 构建批量 prompt
        batch_prompt = _build_batch_prompt(batch_constructs, prompt_template)

        try:
            # 调用 API
            print_info(f"调用 API 提取 {len(batch_constructs)} 个构造...")

            response_text = client._call_api(batch_prompt, max_tokens=8192)

            # 解析批量响应
            batch_results = _parse_batch_response(response_text, batch_constructs)

            # 保存每个结果
            for result in batch_results:
                if "error" not in result:
                    # 添加元数据
                    result["extracted_at"] = datetime.now().isoformat()

                    # 保存单个结果
                    output_file = os.path.join(output_dir, f"{result['construct'].replace('/', '_')}.json")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2)

                    print_success(f"✓ {result['construct']}")
                    results.append(result)
                else:
                    print_error(f"✗ {result['construct']}: {result['error']}")
                    failed.append(result)

            # 更新断点
            checkpoint_data = {
                "completed": batch_end,
                "total": total,
                "timestamp": datetime.now().isoformat()
            }
            with open(checkpoint, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            print_info(f"进度: {batch_end}/{total}")

        except KeyboardInterrupt:
            print_warning("\n\n用户中断")
            break

        except Exception as e:
            print_error(f"批次处理失败: {e}")
            # 记录整个批次失败
            for construct in batch_constructs:
                failed.append({
                    "construct": construct["name"],
                    "language": construct["language"],
                    "error": str(e),
                    "status": "failed"
                })
            import traceback
            traceback.print_exc()

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

    summary_file = f"{constructs[0]['language']}/{constructs[0]['language']}_extraction_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print_success(f"汇总结果已保存到: {summary_file}")

    return summary


def _build_batch_prompt(constructs: List[Dict[str, str]], prompt_template: str) -> str:
    """构建批量提取的 prompt"""
    language = constructs[0]["language"]

    # 构建所有构造的文档
    construct_docs = ""
    for i, construct in enumerate(constructs, 1):
        construct_docs += f"\n## 构造 {i}: {construct['name']}\n\n"
        construct_docs += f"```\n{construct['doc']}\n```\n\n"
        construct_docs += "---\n\n"

    # 替换 prompt 模板占位符
    batch_prompt = prompt_template.replace("{DOCUMENTATION}", construct_docs)
    batch_prompt = batch_prompt.replace("{CONSTRUCT_NAME}", "(批量模式)")
    batch_prompt = batch_prompt.replace("{LANGUAGE}", language)

    # 在末尾追加批量输出要求
    batch_prompt += f"\n\n**批量输出要求**：以上共 {len(constructs)} 个构造，请返回一个 JSON 数组，每个元素是一个构造的完整约束对象，确保 'construct' 字段与构造名称完全一致。"

    return batch_prompt


def _parse_batch_response(response_text: str, constructs: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """
    解析批量响应

    尝试从响应中提取多个构造的约束
    """
    results = []

    try:
        # 尝试直接解析为 JSON 数组
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            json_str = response_text[start:end].strip()
        else:
            json_str = response_text.strip()

        data = json.loads(json_str)

        # 如果是数组，处理每个元素
        if isinstance(data, list):
            for item in data:
                if "construct" in item:
                    results.append(item)
        elif "construct" in data:
            results.append(data)

        # 验证结果数量
        if len(results) != len(constructs):
            print_warning(f"提取结果数量({len(results)})与请求数量({len(constructs)})不匹配")

        return results

    except json.JSONDecodeError as e:
        print_error(f"JSON 解析失败: {e}")
        print_error(f"响应文本前500字符:\n{response_text[:500]}")
        print_error(f"响应文本后500字符:\n{response_text[-500:]}")

        # 如果批量解析失败，尝试按分隔符分割
        if "===CONSTRUCT_SEPARATOR===" in response_text:
            parts = response_text.split("===CONSTRUCT_SEPARATOR===")
            for part in parts:
                part = part.strip()
                if not part:
                    continue
                try:
                    # 尝试提取 JSON
                    if "```json" in part:
                        start = part.find("```json") + 7
                        end = part.find("```", start)
                        json_str = part[start:end].strip()
                    elif "```" in part:
                        start = part.find("```") + 3
                        end = part.find("```", start)
                        json_str = part[start:end].strip()
                    else:
                        json_str = part

                    if json_str:
                        data = json.loads(json_str)
                        if "construct" in data:
                            results.append(data)
                except:
                    continue

        if results:
            return results

        # 如果还是失败，返回错误
        for construct in constructs:
            results.append({
                "construct": construct["name"],
                "language": construct["language"],
                "error": "批量解析失败",
                "status": "failed"
            })

        return results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量提取语法约束（一次API调用处理多个构造）"
    )

    parser.add_argument(
        "--language",
        choices=["javascript", "java", "c", "python"],
        default="javascript",
        help="目标语言"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=5,
        help="每批处理的构造数量（默认5，建议3-8）"
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
        default="prompts/base_prompt_cn_v4.2.txt",
        help="Prompt 模板文件路径"
    )

    args = parser.parse_args()

    print("="*70)
    print(" 批量语法约束提取")
    print("="*70)
    print(f"语言: {args.language}")
    print(f"Prompt: {args.prompt}")
    print(f"批量大小: {args.batch_size}")
    if args.limit:
        print(f"限制数量: {args.limit}")

    # 初始化输出目录
    output_dir = f"{args.language}/extracted"
    os.makedirs(output_dir, exist_ok=True)

    checkpoint_file = f"{args.language}/checkpoint.json"

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
        summary = batch_extract_constructs(
            client=client,
            constructs=constructs,
            prompt_template=prompt_template,
            batch_size=args.batch_size,
            output_dir=output_dir,
            checkpoint=args.checkpoint or checkpoint_file
        )

        print(f"\n{GREEN}{'='*70}")
        print(" 提取完成！")
        print(f"{'='*70}{RESET}")
        print(f"成功率: {summary['successful']}/{summary['total']} ({summary['successful']/summary['total']*100:.1f}%)")
        print(f"API 调用次数: ~{(summary['total'] + args.batch_size - 1) // args.batch_size}")
        print(f"节省的 API 调用: {summary['total'] - ((summary['total'] + args.batch_size - 1) // args.batch_size)}")

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
