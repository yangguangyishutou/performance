import os
import re
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from file_operation import find_file


def get_comment(code:str, method_name:str)->str:
    '''
    获取方法的注释
    '''
    comment_pattern = re.compile(r'.*{}.*//#(.*)#'.format(method_name))
    match = re.search(comment_pattern, code)
    if match:
        return match.group(1)
    else:
        return 'error: no comment found'




class data_set:
    strategies = ['class', 'method', 'Bottom-up method']

    def __init__(self, file_path):
        self.file_path = file_path
        self.workbook = None
        self.worksheet = None
        self.cur_row = 0
        if os.path.exists(file_path):
            self.workbook = load_workbook(file_path)
            self.worksheet = self.workbook['data_set']
            self.cur_row = self.worksheet.max_row
        else:
            self.workbook = Workbook()
            self.worksheet = self.workbook.active
            self.worksheet.title = 'data_set'
            self.cur_row = 1

    def write_files(self, file_dir_path, name):
        self.worksheet['A' + str(self.cur_row)] = name
        # 记录起始行
        start_group_row = self.cur_row
        # 遍历文件夹中的文件
        for file_name in os.listdir(file_dir_path):
            # 写入文件名
            print(f"单元格B{self.cur_row}写入{file_name}")
            self.worksheet['B' + str(self.cur_row)] = file_name
            # 打开文件，读取方法名
            with open(os.path.join(file_dir_path, file_name), 'r', encoding='utf-8') as f:
                code = f.read()
                pattern = r'\b(?:public|protected|private|static|\s)*\s([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{'
                matches = re.findall(pattern, code)
                # 记录文件名所在起始行
                start_file_row = self.cur_row
                # 写入方法名
                if matches:
                    for i in range(3):
                        print(f"单元格C{self.cur_row}写入{self.strategies[i]}")
                        self.worksheet['C' + str(self.cur_row)] = self.strategies[i]
                        # 记录策略所在行
                        start_strategy_row = self.cur_row
                        for match in matches:      
                            print(f"单元格D{self.cur_row}写入{match}")
                            self.worksheet['D' + str(self.cur_row)] = match
                            self.cur_row += 1
                        # 合并策略所在行
                        print(f"合并单元格C{start_strategy_row}:{self.cur_row}")
                        self.worksheet.merge_cells('C' + str(start_strategy_row) + ':C' + str(self.cur_row - 1))
                # 如果没有方法名，则空出一行
                else:
                    print(f"wenjian {file_name} 没有匹配到方法")
                    self.cur_row += 1
                # 合并文件名所在行
                print(f"合并单元格B{start_file_row}:{self.cur_row - 1}")
                self.worksheet.merge_cells('B' + str(start_file_row) + ':B' + str(self.cur_row - 1))
        #合并文件组所在行
        print(f"合并单元格A{start_group_row}:{self.cur_row}")
        self.worksheet.merge_cells('A' + str(start_group_row) + ':A' + str(self.cur_row - 1))


    def find_unit(self, col, name, start_row = 1, end_row = 0):
        '''
        查找列col中的单元格，返回单元格的起止行
        '''
        if end_row == 0:
            end_row = self.cur_row - 1

        result_start_row = 0
        result_end_row = 0
        for i in range(start_row, end_row + 1):
            if self.worksheet[col + str(i)].value == name:
                result_start_row = i
                break

        if result_start_row == 0:
            return None

        for i in range(result_start_row + 1, end_row + 1):
            if self.worksheet[col + str(i)].value is not None:
                break
        result_end_row = i - 1
        
        return (result_start_row, result_end_row)
        

    def write_content(self, name, file_dir_path, strategy):
        '''
        提取文件中的特定内容写入excel
        '''
        # 查找name所在行
        start_row, end_row = self.find_unit('A', name)

        cur_file_start_row = start_row
        cur_file_end_row = 0
        while(True):
            # 找到当前文件名
            cur_file_name = self.worksheet['B' + str(cur_file_start_row)].value
            if cur_file_name is None:
                print(f"找不到文件名{name}")
                break
            else:
                print(f"当前文件名{cur_file_name}")
            cur_file_start_row, cur_file_end_row = self.find_unit('B', cur_file_name, cur_file_start_row, end_row)
            
            # 打开对应文件
            cur_file_name = cur_file_name.split('.')[0] + '.cpp'
            file_dir = find_file(file_dir_path, cur_file_name)
            if file_dir is None:
                print(f"找不到文件{cur_file_name}")
            else:
                with open(file_dir, 'r', encoding='utf-8', errors='ignore') as f:
                    code = f.read()

                # 找到当前策略所在行
                ret = self.find_unit('C', strategy, cur_file_start_row, cur_file_end_row)
                if ret is None:
                    print(f"找不到策略{strategy}在文件{cur_file_name}中")
                else:
                    cur_method_start_row, cur_method_end_row = ret
                
                    # 写入每个方法的注释
                    for row in range(cur_method_start_row, cur_method_end_row + 1):
                        method_name = self.worksheet['D' + str(row)].value
                        comment = get_comment(code, method_name)
                        print(f"单元格E{row}写入{comment}")
                        self.worksheet['E' + str(row)] = comment

            # 如果当前功能的所有文件已经遍历完毕，则退出循环
            if cur_file_end_row >= end_row:
                break
            else:
                cur_file_start_row = cur_file_end_row + 1
                    

    def set_center_alignment(self):
        # 创建一个居中对齐的样式
        center_aligned_text = Alignment(horizontal='center', vertical='center')

        # 遍历工作表中的所有单元格并设置居中
        print("设置居中对齐")
        for row in self.worksheet.iter_rows():
            for cell in row:
                cell.alignment = center_aligned_text


    def save_file(self):
        self.workbook.save(self.file_path)




if __name__ == '__main__':
    file_dir_path = r"E:\sitp\SITP\hallucination\data_set\translation\wso2-commons-httpclient\source\HttpClient"
    target_file_dir_path = r"E:\sitp\SITP\hallucination\data_set\translation\wso2-commons-httpclient\deepseek\class_method\HttpClient"
    excel_file_path = r"E:\sitp\SITP\hallucination\data_set\debug.xlsx"

    data_set = data_set(excel_file_path)
    # data_set.write_files(file_dir_path, 'HttpClient')
    # data_set.set_center_alignment()
    # data_set.save_file()
    data_set.write_content('HttpClient', target_file_dir_path, 'class')
    data_set.set_center_alignment()
    data_set.save_file()