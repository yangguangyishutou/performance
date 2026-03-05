from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI
from typing import List
import asyncio
class Generator:
    max_task_num = 5
    def __init__(self, model, api_key) -> None:
        if model == 'deepseek':
            url = "https://ark.cn-beijing.volces.com/api/v3"
            model_name = "deepseek-v3-241226"
        elif model == 'gpt':
            url = 'https://openkey.cloud/v1'
            model_name = "gpt-4-turbo"
        else:
            raise ValueError("Invalid model name")
        self.client = AsyncOpenAI(api_key=api_key, base_url=url)
        self.model_name = model_name

    async def _generate_single(self, prompt):
        while True:
            try:
                response = await self.client.chat.completions.create(
                    model=self.model_name,
                    messages = [
                        {"role":"system", "content": "You are an experienced programmer"},
                        {"role":"user", "content": prompt}
                    ],
                    stream = True,
                )
                result = ''
                async for chunk in response:
                    if chunk.choices:
                        result += chunk.choices[0].delta.content or ''
                return result
            except Exception as e:
                print(f"在处理prompt {prompt} 时发生错误：{e}, 2秒后重试...")
                await asyncio.sleep(2)
    
        
    async def _generate(self, prompts):
        tasks = [
            self._generate_single(prompt)
            for prompt in prompts
        ]
        results = await tqdm_asyncio.gather(*tasks)
        return results
    
    def generate(self, prompts:List[str]):
        if len(prompts) > self.max_task_num:
            results = []
            for i in range(0, len(prompts), self.max_task_num):
                results.extend(asyncio.run(self._generate(prompts[i:i+self.max_task_num])))
            return results
        else:
            return asyncio.run(self._generate(prompts))