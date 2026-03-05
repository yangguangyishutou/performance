#!/usr/bin/env python3
"""
智谱 AI LLM 客户端

使用智谱 AI API 进行语法约束提取。
智谱 AI 提供兼容 Anthropic Claude API 的接口。

文档：https://open.bigmodel.cn/dev/api
"""

import os
import json
from typing import Dict, List, Optional, Any
from anthropic import Anthropic

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ZhipuLLMClient:
    """智谱 AI LLM 客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://open.bigmodel.cn/api/anthropic",
        model: str = "claude-3-5-sonnet-20241022"  # 智谱支持的模型
    ):
        """
        初始化智谱 AI 客户端

        Args:
            api_key: 智谱 AI API 密钥（默认从环境变量读取）
            base_url: API 基础 URL
            model: 使用的模型名称
        """
        # 从环境变量读取 API 密钥
        if api_key is None:
            api_key = os.environ.get("ZHIPU_API_KEY")

        if not api_key:
            raise ValueError(
                "未找到智谱 AI API 密钥！\n"
                "请设置环境变量：\n"
                "  export ZHIPU_API_KEY='your-api-key'\n"
                "或在初始化时传入 api_key 参数"
            )

        self.api_key = api_key
        self.base_url = base_url
        self.model = model

        # 初始化 Anthropic 客户端（智谱兼容）
        try:
            self.client = Anthropic(
                api_key=api_key,
                base_url=base_url
            )
            print(f"{GREEN}✓{RESET} 智谱 AI 客户端初始化成功")
        except Exception as e:
            raise RuntimeError(f"智谱 AI 客户端初始化失败: {e}")

    def extract_constraints(
        self,
        documentation: str,
        language: str,
        construct_name: str,
        prompt_template: str,
        few_shot_examples: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        提取语法约束

        Args:
            documentation: 语言文档内容
            language: 目标语言（javascript, python, java, c）
            construct_name: 构造名称（如 "if...else", "while loop"）
            prompt_template: Prompt 模板内容
            few_shot_examples: 少样本示例（JSON 格式）
            temperature: 温度参数（0.0-1.0，越低越确定）
            max_tokens: 最大输出 token 数

        Returns:
            提取的约束（字典格式）
        """
        # 组装完整的 Prompt
        full_prompt = self._build_prompt(
            documentation=documentation,
            language=language,
            construct_name=construct_name,
            prompt_template=prompt_template,
            few_shot_examples=few_shot_examples
        )

        # 调用 API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ]
            )

            # 解析响应
            response_text = response.content[0].text
            constraints = self._parse_response(response_text)

            print(f"{GREEN}✓{RESET} 成功提取 {construct_name} 的约束")

            return constraints

        except Exception as e:
            print(f"{RED}✗{RESET} 提取失败: {e}")
            raise

    def _build_prompt(
        self,
        documentation: str,
        language: str,
        construct_name: str,
        prompt_template: str,
        few_shot_examples: Optional[str] = None
    ) -> str:
        """
        组装完整的 Prompt

        Args:
            documentation: 文档内容
            language: 语言名称
            construct_name: 构造名称
            prompt_template: Prompt 模板
            few_shot_examples: 少样本示例

        Returns:
            完整的 Prompt 文本
        """
        # 替换模板中的占位符
        prompt = prompt_template.replace("{DOCUMENTATION}", documentation)
        prompt = prompt.replace("{CONSTRUCT_NAME}", construct_name)
        prompt = prompt.replace("{LANGUAGE}", language)

        # 添加少样本示例
        if few_shot_examples:
            prompt = prompt.replace("{FEW_SHOT_EXAMPLES}", few_shot_examples)
        else:
            # 移除少样本示例占位符
            prompt = prompt.replace("{FEW_SHOT_EXAMPLES}", "")

        return prompt

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        解析 LLM 响应

        Args:
            response_text: 原始响应文本

        Returns:
            解析后的约束字典
        """
        # 调试：打印原始响应
        print(f"\n{BLUE}ℹ{RESET} LLM 原始响应:")
        print("-" * 70)
        print(response_text)
        print("-" * 70)

        # 尝试提取 JSON 部分
        # 智谱 AI 可能会在 JSON 前后添加说明文字
        try:
            # 查找 JSON 代码块
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                print(f"{GREEN}✓{RESET} 找到 JSON 代码块")
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
                print(f"{GREEN}✓{RESET} 找到代码块（非 json）")
            else:
                # 尝试直接解析整个响应
                json_str = response_text.strip()
                print(f"{GREEN}✓{RESET} 直接解析响应")

            print(f"\n{BLUE}ℹ{RESET} 提取的 JSON 字符串:")
            print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

            # 解析 JSON
            constraints = json.loads(json_str)
            return constraints

        except json.JSONDecodeError as e:
            print(f"{RED}✗{RESET} JSON 解析失败: {e}")
            print(f"{RED}✗{RESET} JSON 字符串:\n{json_str}")
            raise ValueError(f"无法解析 LLM 响应为 JSON: {e}")

    def batch_extract_constraints(
        self,
        constructs: List[Dict[str, str]],
        prompt_template: str,
        few_shot_examples: Optional[str] = None,
        callback=None
    ) -> List[Dict[str, Any]]:
        """
        批量提取约束

        Args:
            constructs: 构造列表，每个元素包含 {name, doc, language}
            prompt_template: Prompt 模板
            few_shot_examples: 少样本示例
            callback: 进度回调函数 callback(current, total, construct_name)

        Returns:
            提取的约束列表
        """
        results = []
        total = len(constructs)

        print(f"\n{BLUE}ℹ{RESET} 开始批量提取 {total} 个构造的约束")

        for i, construct in enumerate(constructs, 1):
            construct_name = construct.get("name", "")
            documentation = construct.get("doc", "")
            language = construct.get("language", "javascript")

            print(f"\n[{i}/{total}] 处理: {construct_name}")

            try:
                # 提取约束
                constraints = self.extract_constraints(
                    documentation=documentation,
                    language=language,
                    construct_name=construct_name,
                    prompt_template=prompt_template,
                    few_shot_examples=few_shot_examples
                )

                # 添加元数据
                constraints["construct"] = construct_name
                constraints["language"] = language
                constraints["extracted_at"] = self._get_timestamp()

                results.append(constraints)

                # 调用回调
                if callback:
                    callback(i, total, construct_name)

            except Exception as e:
                print(f"{RED}✗{RESET} 提取失败: {construct_name} - {e}")
                # 记录失败的提取
                results.append({
                    "construct": construct_name,
                    "language": language,
                    "error": str(e),
                    "status": "failed"
                })

        print(f"\n{GREEN}✓{RESET} 批量提取完成: 成功 {len([r for r in results if 'error' not in r])}/{total}")

        return results

    def _get_timestamp(self) -> str:
        """获取当前时间戳（ISO 格式）"""
        from datetime import datetime
        return datetime.now().isoformat()

    def test_connection(self) -> bool:
        """
        测试 API 连接

        Returns:
            连接是否成功
        """
        try:
            print(f"{BLUE}ℹ{RESET} 测试智谱 AI API 连接...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                messages=[
                    {
                        "role": "user",
                        "content": "请回复 '连接成功'"
                    }
                ]
            )

            result = response.content[0].text
            print(f"{GREEN}✓{RESET} API 响应: {result}")
            return True

        except Exception as e:
            print(f"{RED}✗{RESET} 连接测试失败: {e}")
            return False


# =============================================================================
# 辅助函数
# =============================================================================

def load_prompt_template(template_path: str) -> str:
    """
    加载 Prompt 模板

    Args:
        template_path: 模板文件路径

    Returns:
        模板内容
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"找不到 Prompt 模板文件: {template_path}")
    except Exception as e:
        raise RuntimeError(f"读取 Prompt 模板失败: {e}")


def load_few_shot_examples(examples_path: str) -> str:
    """
    加载少样本示例

    Args:
        examples_path: 示例文件路径（JSON）

    Returns:
        示例的 JSON 字符串
    """
    try:
        with open(examples_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return json.dumps(data, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        print(f"{YELLOW}⚠{RESET} 找不到少样本示例文件: {examples_path}")
        return None
    except Exception as e:
        raise RuntimeError(f"读取少样本示例失败: {e}")


# =============================================================================
# 命令行接口
# =============================================================================

def main():
    """命令行测试"""
    import argparse

    parser = argparse.ArgumentParser(description="智谱 AI LLM 客户端测试")
    parser.add_argument("--test-connection", action="store_true", help="测试 API 连接")
    parser.add_argument("--api-key", help="API 密钥（覆盖环境变量）")

    args = parser.parse_args()

    # 初始化客户端
    try:
        client = ZhipuLLMClient(api_key=args.api_key)
    except ValueError as e:
        print(f"{RED}✗{RESET} {e}")
        return 1

    # 测试连接
    if args.test_connection:
        success = client.test_connection()
        return 0 if success else 1

    print("请使用 --test-connection 测试连接")
    return 0


if __name__ == "__main__":
    main()
