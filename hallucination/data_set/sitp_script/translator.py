import os
from openai import OpenAI

def translate(source_dir, target_dir, _api_key):
    '''
    将source_dir中的所有文件翻译成cpp源文件放入target_dir中
    '''
    if _api_key is None:
        print("Please set the API key")
        return

    client = OpenAI(api_key = _api_key, base_url = "https://api.deepseek.com")
    for source_file_name in os.listdir(source_dir):
        name, extension = source_file_name.split('.')
        target_file_name = name + '.cpp'

        if not os.path.exists(target_dir):
                os.makedirs(target_dir)

        source_file_path = os.path.join(source_dir, source_file_name)
        target_file_path = os.path.join(target_dir, target_file_name)

        if (os.path.isfile(target_file_path)):
            print(f"skip {target_file_name}")
        else:
            print(f"current file: {target_file_name}")
            with open(source_file_path, 'r') as source_file:
                source_code = source_file.read()


            prompt = f"将以下java代码翻译成c++，假设相关依赖项已经实现{source_code}"
            response = client.chat.completions.create(
            model = "deepseek-chat",
            messages = [
                {"role":"system", "content": "你是一位经验丰富的高级程序设计师"},
                {"role":"user", "content": prompt}
            ],
            stream = False
            )
            target_code = response.choices[0].message.content

            
            with open(target_file_path, 'w') as target_file:
                target_file.write(target_code)
    
    
    

    
