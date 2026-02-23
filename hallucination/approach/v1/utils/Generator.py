from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from typing import List, Dict, Iterable
from itertools import islice
import random
import asyncio
class Generator:
    max_task_num = 30
    def __init__(self, ai_name, api_key, test_mode=False) -> None:
        if ai_name == 'deepseek':
            url = "https://ark.cn-beijing.volces.com/api/v3"
            model_name = "deepseek-v3-250324"
        elif ai_name == 'gpt':
            # url = 'https://openkey.cloud/v1'
            url = 'https://ph8.co/openai/v1'
            # model_name = "gpt-4-turbo"
            model_name = "gpt-5-mini"
        elif ai_name == 'gemini':
            url = 'https://generativelanguage.googleapis.com/v1beta/openai/'
            model_name = 'gemini-3-flash-preview'
        elif ai_name == 'qianwen':
            url = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
            model_name = 'qwen-plus'
        else:
            raise ValueError("Invalid model name")
        self.client = AsyncOpenAI(api_key=api_key, base_url=url)
        self.model_name = model_name
        self.test_mode = test_mode

        self.prompts = []


    def add_prompt(self, prompt):
        self.prompts.append(prompt)

    async def _generate_single(self, prompt:str|Iterable[ChatCompletionMessageParam]):
        if self.test_mode:
            t = random.uniform(0.1, 0.5)
            await asyncio.sleep(t)
            return """
<test result>
this is a test output.
```cpp
// this is a test code block
```
```java
// this is another test code block
```"""
        messages:Iterable[ChatCompletionMessageParam]  =[]
        if isinstance(prompt, str):
            messages = [
                {"role":"user", "content": prompt}
            ]
        else:
            messages = prompt

        wait_time = 2
        while True:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages = messages,
                    stream = True,
                )
                result = ''
                async for chunk in response:
                    if chunk.choices:
                        result += chunk.choices[0].delta.content or ''
                return result
            except Exception as e:
                prompt_str = str(prompt)
                if len(prompt_str) > 100:
                    prompt_str = prompt_str[:100] + '...'
                print(f"在处理prompt {prompt_str} 时发生错误：{e}, {wait_time}秒后重试...")
                await asyncio.sleep(wait_time)
                wait_time *= 2
    
        
    async def _generate(self, prompts:Iterable[str]|Iterable[Iterable[ChatCompletionMessageParam]]):
        tasks = [
            self._generate_single(prompt)
            for prompt in prompts
        ]
        if not tasks:
            return []
        results = await tqdm_asyncio.gather(*tasks)
        return results
    
    def generate(self, prompts:Iterable[str]|Iterable[Iterable[ChatCompletionMessageParam]]|str|Iterable[ChatCompletionMessageParam]|None=None)->List[str]:
        if prompts is None:
            prompts = self.prompts
            self.prompts = []
        elif not prompts:
            return []

        if isinstance(prompts, str):
            prompts = [prompts]
        elif isinstance(list(islice(prompts, 1))[0], Dict):
            prompts = [prompts] # type: ignore
        
        iter_prompts = iter(prompts)  # type: ignore
        results = [] 
        epoch = []
        try: 
            while True:
                for i in range(self.max_task_num):
                    epoch.append(next(iter_prompts))
                epoch_results = asyncio.run(self._generate(epoch))
                results.extend(epoch_results)
                epoch = []
        except StopIteration:
            epoch_results = asyncio.run(self._generate(epoch))
            results.extend(epoch_results)

        return results


from pathlib import Path
import sys
ppdir = str(Path(__file__).parent.parent)
if ppdir not in sys.path:
    sys.path.append(ppdir)
from utils.api_key import api_keys
default_generator = Generator('gpt',api_keys['gpt'])

if __name__ == "__main__":


    test1 = "Who are you?"

    test2 = [
        {"role":"user", "content": "Who are you?"},
        {"role":"assistant", "content": "I am a chatbot."},
        {"role":"user", "content": "What is your name?"},
    ]

    test3 = [
        "Who are you?",
        "What can you do?",
        "How do you work?"
    ]

    test4 = [
        [
            {"role":"user", "content": "Who are you?"},
            {"role":"assistant", "content": "I am a chatbot."},
            {"role":"user", "content": "What is your name?"},
        ],
        [
            {"role":"user", "content": "What can you do?"}
        ],
        [
            {"role":"user", "content": "How do you work?"}
        ]
    ]

    print(default_generator.generate(test1))
    print(default_generator.generate(test2)) # type: ignore
    print(default_generator.generate(test3))
    print(default_generator.generate(test4)) # type: ignore