import os
from openai import AsyncOpenAI
import asyncio
import re
    

def get_code(content):
    partten = re.compile(r'```(.*)```', re.DOTALL)
    match = partten.search(content)
    if match:
        if match.group(1).startswith("cpp"):
            return match.group(1)[4:]
        return match.group(1)
    else:
        return ""


async def single_translate(client, prompt, output_file_path, model_name, task_id):
    try:
        response = await client.chat.completions.create(
            model = model_name,
                messages = [
                    {"role":"system", "content": "You are an experienced programmer"},
                    {"role":"user", "content": prompt}
                ],
                stream = True
            )
    except Exception as e:
        print(f"在处理{output_file_path}时发生错误：{e}")
        return
    
    tokens = 0
    content = ''
    async for chunk in response:
        tokens += 1
        print(f"\033[{task_id + 3};1H]\033[2K", end='')
        if chunk.choices:
            print(f"{output_file_path}已生成{tokens}个token，当前token为[{chunk.choices[0].delta.content or '<empty>'}]", end='')
            content += chunk.choices[0].delta.content or ''
    
    if not content:
        print(f"{output_file_path}生成失败，可能是服务器繁忙，请尝试再次运行（已生成的文件会自动跳过）")
        return
    
    pattern = r"```cpp(.*?)```"
    matches = re.findall(pattern, content, re.DOTALL)
    if matches:
        header_code = matches[0]
        with open(output_file_path.replace('.cpp', '.h'), 'w', encoding='utf-8') as header_file:
            header_file.write(header_code)
    else:
        print(f"warning: {output_file_path} does not contain a header file")
    if len(matches) > 1:
        source_code = matches[1]
        with open(output_file_path, 'w', encoding='utf-8') as source_file:
            source_file.write(source_code)
    


                

example = """
```cpp
#ifndef MYCLASS_H
#define MYCLASS_H
#include "ClassA.h"
#include "ClassB.h"
public class Myclass {
    public:
        ClassA field1;
        ClassB field2;
        int myMethod(int a, int b);
}
#endif
```

```cpp
#include "Myclass.h"
int Myclass::myMethod(int a, int b) {
    return a + b;
}
```
"""



async def translate(source_dir,target_dir, model):
    '''
    将source_dir中的所有文件翻译成cpp源文件放入target_dir中
    '''
    task_params = []

    os.system('cls')
    task_num = 0
    for source_file_name in os.listdir(source_dir):
        name, extension = source_file_name.split('.')
        target_file_name = name + '.cpp'

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        source_file_path = os.path.join(source_dir, source_file_name)
        target_file_path = os.path.join(target_dir, target_file_name)

        if (os.path.isfile(target_file_path)):
            print(f"{target_file_name}已存在，跳过")
        else:
            print(f"将{target_file_name}添加到任务队列中")
            with open(source_file_path, 'r', encoding='utf-8') as source_file:
                task_num += 1
                source_code = source_file.read()
                prompt = f"Translate the following Java code into C++:\n{source_code}\nYour answer should include two parts: header file and source file(if the given java file contains an interface, source file are not required), every part should be surrounded by ```cpp```. assuming that the relevant dependencies have been implemented, provide the code only, no other non-code content is required, and no usage examples are required. Here is an example:{example}"

            task_params.append((prompt, target_file_path, task_num))

    
    if model == 'deepseek':
        url = "https://api.deepseek.com"
        model_name = "deepseek-chat"
        api_key = "sk-ed605d7c20f94ae48b94a882f668ebf0"
    elif model == 'gpt':
        url = 'https://ph8.co/openai/v1'
        model_name = "gpt-5.1-chat"
        api_key = "sk-f670879e5ef147c6abc113191a4953ab"
    elif model == 'qwen':
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        model_name = "qwen-plus"
        api_key = "sk-4d4512f0acc0417495d7084eac8b31dc"
    else:
        print(f"不支持的模型：{model}")
        return
    
    client = AsyncOpenAI(api_key = api_key, base_url = url)
    tasks = [asyncio.create_task(single_translate(client, prompt, target_file_path, model_name, task_id)) for prompt, target_file_path, task_id in task_params]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    path = r"translation_java-cpp\Cookie\deepseek\method\CookiePolicy.h"
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
        print(get_code(content))