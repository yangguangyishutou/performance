import json
import re
import sys
import shutil
from typing import List, Dict, Any, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pathlib import Path

pp_dir = str(Path(__file__).parent.parent)
if pp_dir not in sys.path:
    sys.path.append(str(pp_dir))

from utils.Generator import Generator
from path_config import cfg_review_dir_path, cfg_review_prompt_file_path, cfg_translate_result_dir_path, cfg_binary_graph_file_path
from graph.retrieval_tools import sort_headers, load_nodes
# from graph.header import Header

from .tools import get_all_tools


class CppCompilationAgent:
    """
    C++ Compilation and Code Repair Agent

    This agent handles multiple C++ source files and header files,
    compiling them sequentially and automatically fixing compilation errors.
    """

    def __init__(self, ai_name: str, project_name: str, file_path: Path):
        self.ai_name = ai_name
        self.llm = Generator(ai_name)
        self.file_path = file_path  # <--- [新增] 保存 file_path

        with open(cfg_review_prompt_file_path(), "r", encoding="utf-8") as p:
            self.prompt = p.read()

        tools = get_all_tools(ai_name, project_name)
        self.tools ={
            "compile_file":tools["compile_file"],
            "read_file":tools["read_file"],
            "write_file":tools["write_file"],
            "create_file":tools["create_file"]
        }
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        self.history_messages: list[ChatCompletionMessageParam] = [
            {"role":"system", "content":self.prompt},
            {"role":"user", "content":f"the file need to be compiles: {file_path.name}"}
        ]

    def save_history(self, file_path: Optional[Path]=None):
        if not file_path:
            file_path = Path("history.json")

        with open(file_path, "w", encoding="utf-8") as h:
            json.dump(self.history_messages, h, indent=4)


    def parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse the LLM response to extract tool calls and status information.
        Supports extracting JSON from ```json``` code blocks.

        Args:
            response: Raw response string from LLM

        Returns:
            Dictionary containing parsed response data
        """
        # Try to extract JSON from code blocks first
        json_content = self._extract_json_from_response(response)

        if json_content:
            try:
                parsed = json.loads(json_content)
                return self._validate_and_normalize_response(parsed)
            except json.JSONDecodeError:
                pass

        # If no valid JSON found in code blocks, try parsing the whole response
        try:
            parsed = json.loads(response)
            return self._validate_and_normalize_response(parsed)
        except json.JSONDecodeError:
            # If not JSON, create a basic response structure
            return {
                "current-file": "unknown",
                "success": False,
                "error-log": "something went wrong, please continue from the last valid information.",
                "note": "",
                "current-action": "waiting for valid response",
                "tool-calls": []
            }

    def _extract_json_from_response(self, response: str) -> str:
        """
        Extract JSON content from ```json``` code blocks in the response.

        Args:
            response: Raw response string

        Returns:
            Extracted JSON string or empty string if no JSON found
        """
        # Pattern to match ```json ... ``` blocks
        pattern = r'```json\s*(.*?)\s*```'
        matches = re.findall(pattern, response, re.DOTALL)

        if matches:
            # Return the first JSON block found
            return matches[0].strip()

        # Also try without the 'json' specifier
        pattern_generic = r'```\s*(.*?)\s*```'
        matches_generic = re.findall(pattern_generic, response, re.DOTALL)

        if matches_generic:
            # Check if the content looks like JSON
            content = matches_generic[0].strip()
            if content.startswith('{') and content.endswith('}'):
                return content

        return ""

    def _validate_and_normalize_response(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize the parsed response.

        Args:
            parsed: Parsed JSON response

        Returns:
            Normalized response dictionary
        """
        # Validate required fields
        required_fields = ["current-file", "success", "current-action"]
        for field in required_fields:
            if field not in parsed:
                parsed[field] = "unknown" if field == "current-file" else False

        # Ensure tool-calls is a list
        if "tool-calls" not in parsed:
            parsed["tool-calls"] = []
        elif not isinstance(parsed["tool-calls"], list):
            parsed["tool-calls"] = [parsed["tool-calls"]]

        # Normalize field names to match expected format
        field_mappings = {
            "current_file": "current-file",
            "currentFile": "current-file",
            "tool_calls": "tool-calls",
            "toolCalls": "tool-calls",
            "error_log": "error-log",
            "errorLog": "error-log",
            "current_action": "current-action",
            "currentAction": "current-action"
        }

        for old_name, new_name in field_mappings.items():
            if old_name in parsed and new_name not in parsed:
                parsed[new_name] = parsed.pop(old_name)

        return parsed
    
    def handle_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        tool_results:List[Dict[str, Any]] = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool")
            tool_args = tool_call.get("args", {})

            if tool_name not in self.tools:
                error_msg = f"Unknown tool: {tool_name}"
                print(f"Error: {error_msg}")
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": error_msg
                })
                continue

            try:
                # Call the tool with appropriate arguments
                tool_func = self.tools[tool_name]

                # Handle different tool parameter requirements
                if tool_name == "compile_file":
                    result = tool_func(tool_args.get("file", ""))
                elif tool_name == "read_file":
                    result = tool_func(tool_args.get("file", ""))
                elif tool_name == "write_file":
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("content", "")
                    )
                elif tool_name == "create_file":
                    result = tool_func(
                        tool_args.get("file", ""),
                        tool_args.get("content", "")
                    )
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}

                tool_results.append({
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result": result
                })

                print(f"Tool {tool_name} executed successfully")

            except Exception as e:
                error_msg = f"Tool execution failed: {e}"
                print(f"Error: {error_msg}")
                tool_results.append({
                    "tool": tool_name,
                    "success": False,
                    "result": {"error": error_msg}
                })

        return tool_results



    def run(self, max_attempts: int = 50) -> Dict[str, Any]:
        """
        Runs the agent execution loop.

        Args:
            max_attempts: Maximum number of compilation attempts (previously total interactions)

        Returns:
            Final status report
        """
        # 将 max_attempts 理解为最大编译尝试次数
        max_compile_attempts = max_attempts
        print(f"Starting C++ Compilation Agent with {max_compile_attempts} max compilation attempts")

        compile_attempts = 0
        interaction_count = 0
        # 设置一个较大的总交互上限，防止 Agent 在不编译的情况下无限循环 (例如反复读文件)
        max_interactions = max_compile_attempts * 10 

        # # --- [新增] 初始编译环节 ---
        # print(f"Running initial compilation for {self.file_path}...")
        # initial_result = self.tools["compile_file"](str(self.file_path))
        
        # if initial_result.get("success"):
        #     return {
        #         "status": "success",
        #         "message": "Initial compilation completed successfully without AI intervention.",
        #         "attempts": 1
        #     }
        
        # # 如果初始编译失败，将错误信息加入历史记录，并增加计数
        # compile_attempts += 1
        # self.history_messages.append({
        #     "role": "user",
        #     "content": json.dumps({
        #         "tool_results": [{
        #             "tool": "compile_file",
        #             "success": False,
        #             "result": initial_result
        #         }],
        #         "summary": "Initial compilation failed. Please fix the errors based on the result."
        #     })
        # })
        # # ---------------------------

        while compile_attempts < max_compile_attempts and interaction_count < max_interactions:
            interaction_count += 1
            print(f"\n--- Interaction {interaction_count} | Compilation Attempts: {compile_attempts}/{max_compile_attempts} ---")

            # Get response from LLM
            try:
                response = self.llm.generate(self.history_messages)[0]
                print(f"LLM Response: {response}...")
                self.history_messages.append({
                    "role": "assistant",
                    "content": response
                })
            except Exception as e:
                print(f"Error getting LLM response: {e}")
                self.save_history()
                return {
                    "status": "error",
                    "error": f"LLM communication failed: {e}",
                    "attempts": compile_attempts
                }

            # Parse the response
            parsed_response = self.parse_response(response)

            if parsed_response.get("success"):
                self.save_history()
                return {
                    "status": "success",
                    "message": "Compilation completed successfully",
                    "attempts": compile_attempts
                }

            tool_calls = parsed_response.get("tool-calls", [])
            
            # 检查本次交互是否包含编译操作
            is_compiling = False
            for tool_call in tool_calls:
                if tool_call.get("tool") == "compile_file":
                    is_compiling = True
                    break
            
            # 如果包含了编译操作，则增加编译计数
            if is_compiling:
                compile_attempts += 1

            tool_results = self.handle_tool_calls(tool_calls)
            print(json.dumps(tool_results, indent=4))

            # Add tool results to history
            self.history_messages.append({
                "role": "user",
                "content": json.dumps({
                    "tool_results": tool_results,
                    "summary": f"Completed {len(tool_results)} tool calls"
                })
            })

        # If we reach here, we hit max attempts
        self.save_history()
        
        if compile_attempts >= max_compile_attempts:
            return {
                "status": "max_compile_attempts_reached",
                "message": f"Reached maximum compilation attempts ({max_compile_attempts}) without completion",
                "attempts": compile_attempts
            }
        else:
            return {
                "status": "max_interactions_reached",
                "message": f"Reached maximum total interactions ({max_interactions}) without completion",
                "attempts": compile_attempts
            }



    
    


# if __name__ == "__main__":
#     main("deepseek", "Cookie")



