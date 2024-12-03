import sitp_script as sitp

# 数据集路径
data_set_path = r'hallucination\data_set\sitp-data.xlsx'
# 翻译文件路径
source_file_dir_path = r'hallucination\data_set\translation\gson\source'

# 将基本信息自动写入数据集中
data_set = sitp.data_set(data_set_path)
# 根据source_file_dir_path中的文件自动填写文件、方法名
data_set.write_files(source_file_dir_path, 'GsionBuilder')
# 设置居中对齐
data_set.set_center_alignment()
# 保存数据集
data_set.save_file()