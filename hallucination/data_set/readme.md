## 脚本使用流程：

1. 将初始文件从原始仓库中提取出来，集中储存在文件夹中
2. 调用api逐文件翻译，结果集中存放在文件夹中

3. 在结果文件中人工标注每个方法的错误类型
     - 每个方法的问题用//#...标记(错误类型可以写在声明处，也可以写在实现处，只需要写一次，必须保证和方法名在同一行)：
     - 如果有涉及头文件、类声明、成员变量等的错误，则用//##标记在文件中的任意一行（此行不能有其他内容）
       
    示例：
    ```cpp
    //##类层面的错误
  
    class MyClass{
        void method1(int var1, char var2);          //#错误类型
        int method2();                                         //#None
        string method3();
    } 
    void MyClass::method1(int var1, int var2){
         //some code
    }
    int MyClass::method2(int var1, int var2){
         //some code
    }
    string MyClass::method3(int var1, int var2){      //#错误类型
         //some code
    }
    ```

4. 脚本向数据集表格中填写文件名、方法名等
5. 脚本自动填写错误类型

## main.py参数设置

```python
# API的密钥
_api_key = 'your_api_key'
# 原始项目源文件路径
original_program_path = r"E:\sitp\SITP\hallucination\data_set\original_programs\gson\gson\src\main\java\com\google\gson"
# 基准文件
basic_file_name = 'GsonBuilder.java'
# 使用模型
ai_model_name = 'deepseek'  #暂不支持更改
# 翻译形式
translation_form = 'class'  #暂不支持更改

if __name__ == '__main__':
    # clone_files()
    # translate_files()
    # write_basic_info()
    # write_content()
    # set_center_alignment()
    # save_file()
```
