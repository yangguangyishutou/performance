import sitp_script as sitp

_api_key = 'sk-a9fd998286e04e8e9af58f9cfe2add77'


###以下为参数设置###
###############################################################################################################################################################################################
# 原始项目源文件路径
original_program_path = "E:\\sitp\\SITP\\hallucination\\data_set\\original_programs\\wso2-commons-httpclient\\commons-httpclient\\src\\main\\java\\org\\apache\\commons\\httpclient"
# 基准文件
basic_file_name = 'Cookie.java'
# 使用模型
ai_model_name = 'deepseek'  #暂不支持更改
# 翻译形式
translation_form = 'class'  #暂不支持更改
###############################################################################################################################################################################################



###以下不需要修改###
###############################################################################################################################################################################################
# 数据集路径
data_set_path = r'hallucination\data_set\sitp-data.xlsx'
# 组名
group_name = basic_file_name.split('.')[0]
# 待翻译文件路径（一条完整的调用链上的文件，从原始项目中复制过来存在该路径下）
source_file_dir_path = "hallucination\\data_set\\translation\\" + group_name + "\\source" 
# 翻译后的文件保存路径
target_file_dir_path = "hallucination\\data_set\\translation\\" + group_name + "\\" + ai_model_name + "\\" + translation_form
# 创建数据集对象
data_set = sitp.data_set(data_set_path)

# 以选中的文件为基准，将调用链上的所有文件复制到指定目录下
def clone_files():
    sitp.clone_files(original_program_path, basic_file_name, source_file_dir_path)
# 调用DeepSeek API进行翻译
def translate_files():
    sitp.translate(source_file_dir_path, target_file_dir_path, _api_key)
# 将基本信息自动写入数据集中(根据source_file_dir_path中的文件自动填写文件、方法名)
def write_basic_info():
    data_set.write_files(source_file_dir_path, group_name)
    data_set.save_file()
# 填写数据集内容
def write_content():
    data_set.write_content(group_name, target_file_dir_path, ai_model_name, translation_form)
    data_set.save_file()
# 设置居中对齐
def set_center_alignment():
    data_set.set_center_alignment()
    data_set.save_file()
###############################################################################################################################################################################################


if __name__ == '__main__':
    # clone_files()
    # translate_files()
    # write_basic_info()
    write_content()
    # set_center_alignment()
    # save_file()