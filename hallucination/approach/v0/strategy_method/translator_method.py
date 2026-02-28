import os
import re
from openai import AsyncOpenAI
from api_key import api_keys
import asyncio


#Following is a Java class/interface declaration along with field and method declarations:
#{code}
#Please translate it into a header file that conforms to the C++17 standard syntax and performs the same functions. The method only needs to be declared, not implemented. Other classes that appear in the code have been implemented in C++. If necessary, you can use the header file with the same name.

def get_code(content):
    partten = re.compile(r'```(.*?)```', re.DOTALL)
    match = partten.search(content)
    if match:
        if match.group(1).startswith("cpp"):
            return match.group(1)[4:]
        return match.group(1)
    else:
        return ""
    
def merge_temp_files(temp_dir, target_dir, file_base_name):
    includes = f"#include \"{file_base_name}.h\"\n"
    result_code = ""

    for file_name in os.listdir(temp_dir):
        if file_base_name in file_name and not file_name.endswith(".h"):
            with open(os.path.join(temp_dir, file_name), 'r', encoding='utf-8') as f:
                for line in f:
                    if '#include' in line :
                        if line not in includes:
                            includes = includes + line
                    else:
                        result_code += line

    if len(result_code) != 0:
        with open(os.path.join(target_dir, file_base_name + ".cpp"), 'w', encoding='utf-8') as f:
            f.write(includes)
            f.write(result_code)
    

def prompt_header(file_path):
    with open (file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        pattern = re.compile(r"'''(\w+)\s*([\s\S]*?)'''")
        matches = pattern.findall(content)
        prompts = []
        for tag, code in matches:
            if tag == "class" or tag == "interface" or tag == "enum":
                prompts.append(f"Following is a Java class/interface declaration along with field and method declarations: \n{code}\nPlease translate it into a header file that conforms to the C++17 standard syntax and performs the same functions. The method only needs to be declared, not implemented. Assuming other classes and all dependencies that appear in the code have been implemented in C++, you can directly include the header file with the same name. The response should only contain one header code block with ```cpp```mark, do not output any other text content")
        if len(prompts) == 0:
            print(f"No Java class/interface/enum declarations found in the file {file_path}.")
        elif len(prompts) > 1:
            print(f"Multiple Java class/interface/enum declarations found in the file {file_path}. Please provide the code for each declaration.")
        
        return prompts[0]
    

def prompt_method(file_path, header_path):
    with open (file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        pattern = re.compile(r"'''(\w+)\s*([\s\S]*?)'''")
        matches = pattern.findall(content)

    p_dir = os.path.dirname(file_path)
    if not os.path.exists(p_dir):
        os.makedirs(p_dir, exist_ok=True)
    with open (header_path, 'r', encoding='utf-8') as f:
        header_content = f.read()

    prompts = []
    for tag, code in matches:
        if tag == "interface":
            return []
        if tag == "method":
            prompts.append( f"{header_content}\nPlease implement the following functions according to the contents of the above header file:\n {code}\n It is a Java method that you need to translate into a member function that conforms to the C++17 standard syntax. Assuming other classes that appear in the code have been implemented in C++, you can use the header file with the same name. Only the in vitro implementation of the function is required, no other non-code content is required, and no usage examples are required")

    if len(prompts) == 0:
        print(f"No Java method declarations found in the file {file_path}.")

    return prompts


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
    content = get_code(content)
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(content)


                

async def translate_method(split_dir, target_dir, model):
    '''
    将source_dir中的所有文件翻译成cpp源文件放入target_dir中
    '''
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
    
    os.makedirs(os.path.join(target_dir, "temp"), exist_ok=True)

    
    os.system('cls')
    task_file_base_names = []
    task_params = []
    task_num = 0
    for source_file_name in os.listdir(split_dir):
        name, extension = source_file_name.split('.')
        target_file_name = name + '.h'

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        target_file_path = os.path.join(target_dir, target_file_name)
        split_file_path = os.path.join(split_dir, source_file_name)

        if (os.path.isfile(target_file_path)):
            print(f"{target_file_name}已存在，跳过")
        else:
            print(f"将{target_file_name}添加到任务队列中")
            task_num += 1
            header_prompt = prompt_header(split_file_path)
            task_file_base_names.append(name)
            task_params.append((header_prompt, target_file_path, task_num))


    client = AsyncOpenAI(api_key = api_key, base_url = url)
    tasks = [asyncio.create_task(single_translate(client, prompt, target_file_path, model_name, task_id)) for prompt, target_file_path, task_id in task_params]
    await asyncio.gather(*tasks)

    task_params = []
    for split_file_base_name in task_file_base_names:
        if os.path.exists(os.path.join(target_dir, split_file_base_name + ".cpp")):
            print(f"{split_file_base_name}.cpp已存在，跳过")
            continue

        split_file_path = os.path.join(split_dir, split_file_base_name + ".txt")
        header_path = os.path.join(target_dir, split_file_base_name + ".h")

        method_prompts = prompt_method(split_file_path, header_path)
        for j in range(len(method_prompts)):
            temp_file_name = split_file_base_name + '_' + str(j) + '.cpp'
            temp_file_path = os.path.join(target_dir, "temp", temp_file_name)
            if os.path.exists(temp_file_path):
                print(f"{temp_file_name}已存在，跳过")
                continue
            print(f"将{temp_file_name}添加到任务队列中")
            task_params.append((method_prompts[j], temp_file_path, j))

    while len(task_params) > 0:
        os.system('cls')
        tasks = [asyncio.create_task(single_translate(client, prompt, target_file_path, model_name, task_id%10)) for prompt, target_file_path, task_id in task_params[:10]]
        await asyncio.gather(*tasks)
        task_params = task_params[10:]


    for file_base_name in task_file_base_names:
        merge_temp_files(os.path.join(target_dir, "temp"), target_dir, file_base_name)

    
        
            


    





if __name__ == "__main__":
    temp_dir = "translation_java-cpp\\EnableJUnit4MigrationSupport\\deepseek\\method\\temp"
    target_dir = "translation_java-cpp\\EnableJUnit4MigrationSupport\\deepseek\\method"
    for file_name in os.listdir(target_dir):
        if file_name.endswith(".h"):
            file_base_name, extension = file_name.split('.')
            merge_temp_files(temp_dir, os.path.join(target_dir, "temp"), file_base_name)
    

            

    
