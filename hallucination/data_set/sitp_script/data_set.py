import os
import re
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

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
    excel_file_path = r"E:\sitp\SITP\hallucination\data_set\debug.xlsx"

    data_set = data_set(excel_file_path)
    data_set.write_files(file_dir_path, 'HttpClient')
    data_set.set_center_alignment()
    data_set.save_file()