# api_keys = {
#     # 'gpt':'sk-Wf5pA5Goddqzktb695684491E1B64a15B165383dDf3eF540', # openkey
#     'gpt': 'sk-f670879e5ef147c6abc113191a4953ab', # pH8
#     'deepseek':'3b144066-c88f-4796-b19e-1fa3cc71253b',
#     # 'gemini': 'sk-f670879e5ef147c6abc113191a4953ab' # pH8
#     'gemini': 'AIzaSyBQd3tbyTK6_uijz-7I8lW8A0OphhnoS6E' # 官网免费版
# }

llm_api = {
    "deepseek": {
        "api_key": "sk-ed605d7c20f94ae48b94a882f668ebf0",
        "base_url": "https://api.deepseek.com",
        "model_name": "deepseek-chat",
    },
    "gpt": {
        "api_key": "sk-f670879e5ef147c6abc113191a4953ab",
        "base_url": "https://ph8.co/openai/v1",
        "model_name": "gpt-5-mini",
    },
    "gemini": {
        "api_key": "AIzaSyBQd3tbyTK6_uijz-7I8lW8A0OphhnoS6E",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gemini-1.5",
    },
    "qwen": {
        "api_key": "sk-4d4512f0acc0417495d7084eac8b31dc",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": "qwen3.5-plus",
    },
    "qwen-flash":{
        "api_key": "sk-4d4512f0acc0417495d7084eac8b31dc",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model_name": "qwen-flash",
    },
}

