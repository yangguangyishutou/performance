import os

def list_dependence(file_path: str)->list[str]:
    '''
    打开文件，查找其调用链
    '''
    dependence_list = []
    file = open(file_path, 'r', encoding='utf-8')
    for line in file.readlines():                                                                             
        if line.startswith('import '):
            if line.startswith('import java.'):
                continue
            name = line. split('.')[-1][0:-2]
            dependence_list.append(name + '.java')
    file.close()
    return dependence_list
    
def find_file(dir_path:str, file_name:str)->str:
    '''
    查找文件
    '''
    for root, dirs_names, file_names in os.walk(dir_path):
        if file_name in file_names:
            return os.path.join(root, file_name)
    return None


def clone_files(source_dir_path: str, source_file_name: str, target_dir_path:str) -> None:
    '''
    从source_dir中获取source_file的调用链，复制到target_dir中
    '''
    source_file_path = find_file(source_dir_path, source_file_name)
    if source_file_path is None:
        print(f'{source_file_name} not found in {source_dir_path}')
        return
    if os.path.exists(os.path.join(target_dir_path, source_file_name)):
        print(f'{source_file_name} already exists in {target_dir_path}')
        return
    
     # 复制文件
    os.makedirs(target_dir_path, exist_ok=True)
    os.system(f'copy "{source_file_path}" "{target_dir_path}"')

    dependence_list = list_dependence(source_file_path)
    for dependence in dependence_list:
        clone_files(source_dir_path, dependence, target_dir_path)
    

if __name__ == '__main__':
    source_dir_path = r'E:\sitp\SITP\hallucination\data_set\original_program\wso2-commons-httpclient\commons-httpclient\src\main'
    target_dir_path = r'E:\sitp\SITP\hallucination\data_set\translation\wso2-commons-httpclient\debug'
    source_file_name = 'HttpMethodDirector.java'

    clone_files(source_dir_path, source_file_name, target_dir_path)


