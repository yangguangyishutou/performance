```python
class Generator:
    def __init__(self, ai_name, api_key, test_mode=False):
        if ai_name == 'deepseek':
            self.url = "https://ark.cn-beijing.volces.com/api/v3"
            self.model_name = "deepseek-v3-250324"
        elif ai_name == 'gpt':
            self.url = 'https://openkey.cloud/v1'
            self.model_name = "gpt-4-turbo"

        self.client = AsyncOpenAI(api_key=api_key, base_url=self.url)

    async def generate(self, prompts):
        # Asynchronous batch processing
        tasks = [self._generate_single(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        return results
```