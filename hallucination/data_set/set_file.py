import sitp_script as sitp


# api key
sitp._api_key = 'sk-a9fd998286e04e8e9af58f9cfe2add77'

# 原始项目源文件路径
original_program_path = r'hallucination\data_set\original_programs\gson\gson\src\main\java\com'
# 待翻译文件路径（一条完整的调用链上的文件，从原始项目中复制过来存在该路径下）
source_file_dir_path = r'hallucination\data_set\translation\gson\source'
# 选中的基准文件名
source_file_name = 'GsonBuilder.java'
# 翻译后的文件保存路径
target_file_dir_path = r'hallucination\data_set\translation\gson\deepseek\class_method\GsionBuilder'


# 以选中的文件为基准，将调用链上的所有文件复制到指定目录下
sitp.clone_files(original_program_path, source_file_name, source_file_dir_path)

# 调用DeepSeek API进行翻译
# sitp.translate(source_file_dir_path, target_file_dir_path)



