import re

def get_cpp_code(str):
    if "```" in str:
        pattern = re.compile(r"```(cpp)?\s*([\s\S]*?)\s*```")
        match = pattern.search(str)
        if match:
            return match.group(2)
        else:
            return ""
    else:
        return str

def get_json_code(str):
    if "```" in str:
        pattern = re.compile(r"```(json)?\s*([\s\S]*?)\s*```")
        match = pattern.search(str)
        if match:
            return match.group(2)
        else:
            return ""
    else:
        if '{' in str:
            pattern = re.compile(r"({[\s\S]*})")
            match = pattern.search(str)
            if match:
                return match.group(1)
            else:
                return ""
        else:
            return ""

def test_get_cpp_code():
    # 测试用例1: 带cpp标记的代码块
    test1 = "```cpp\n#include <iostream>\nusing namespace std;\nint main() { cout << \"Hello World!\" << endl; return 0; }\n```"
    expected1 = "#include <iostream>\nusing namespace std;\nint main() { cout << \"Hello World!\" << endl; return 0; }"
    result1 = get_cpp_code(test1)
    print(f"Test 1: {'PASS' if result1 == expected1 else 'FAIL'}")
    print(f"Input: {test1}")
    print(f"Expected: {expected1}")
    print(f"Result: {result1}")
    print()
    
    # 测试用例2: 不带cpp标记的代码块
    test2 = "```\nint x = 5;\nint y = 10;\nint sum = x + y;\n```"
    expected2 = "int x = 5;\nint y = 10;\nint sum = x + y;"
    result2 = get_cpp_code(test2)
    print(f"Test 2: {'PASS' if result2 == expected2 else 'FAIL'}")
    print(f"Input: {test2}")
    print(f"Expected: {expected2}")
    print(f"Result: {result2}")
    print()
    
    # 测试用例3: 没有代码块的纯文本
    test3 = "This is just a plain text without code blocks"
    expected3 = "This is just a plain text without code blocks"
    result3 = get_cpp_code(test3)
    print(f"Test 3: {'PASS' if result3 == expected3 else 'FAIL'}")
    print(f"Input: {test3}")
    print(f"Expected: {expected3}")
    print(f"Result: {result3}")
    print()
    
    # 测试用例4: 包含代码块标记但没有匹配内容
    test4 = "```cpp```"
    expected4 = ""
    result4 = get_cpp_code(test4)
    print(f"Test 4: {'PASS' if result4 == expected4 else 'FAIL'}")
    print(f"Input: {test4}")
    print(f"Expected: {expected4}")
    print(f"Result: {result4}")
    print()

def test_get_json_code():
    # 测试用例1: 带json标记的代码块
    test1 = "```json\n{\"name\": \"John\", \"age\": 30, \"city\": \"New York\"}\n```"
    expected1 = '{\"name\": \"John\", \"age\": 30, \"city\": \"New York\"}'
    result1 = get_json_code(test1)
    print(f"Test 1: {'PASS' if result1 == expected1 else 'FAIL'}")
    print(f"Input: {test1}")
    print(f"Expected: {expected1}")
    print(f"Result: {result1}")
    print()
    
    # 测试用例2: 不带json标记的代码块
    test2 = "```\n{\"id\": 123, \"status\": \"active\"}\n```"
    expected2 = '{\"id\": 123, \"status\": \"active\"}'
    result2 = get_json_code(test2)
    print(f"Test 2: {'PASS' if result2 == expected2 else 'FAIL'}")
    print(f"Input: {test2}")
    print(f"Expected: {expected2}")
    print(f"Result: {result2}")
    print()
    
    # 测试用例3: 内嵌在文本中的JSON对象
    test3 = "The response is: {\"code\": 200, \"message\": \"success\"}"
    expected3 = '{\"code\": 200, \"message\": \"success\"}'
    result3 = get_json_code(test3)
    print(f"Test 3: {'PASS' if result3 == expected3 else 'FAIL'}")
    print(f"Input: {test3}")
    print(f"Expected: {expected3}")
    print(f"Result: {result3}")
    print()
    
    # 测试用例4: 没有JSON对象的纯文本
    test4 = "This is just a plain text without JSON"
    expected4 = ""
    result4 = get_json_code(test4)
    print(f"Test 4: {'PASS' if result4 == expected4 else 'FAIL'}")
    print(f"Input: {test4}")
    print(f"Expected: {expected4}")
    print(f"Result: {result4}")
    print()
    
    # 测试用例5: 包含代码块标记但没有匹配内容
    test5 = "```json```"
    expected5 = ""
    result5 = get_json_code(test5)
    print(f"Test 5: {'PASS' if result5 == expected5 else 'FAIL'}")
    print(f"Input: {test5}")
    print(f"Expected: {expected5}")
    print(f"Result: {result5}")
    print()

    # 测试用例6：包含嵌套JSON对象
    test6 = """some text ```json
{
    "name"": "John",
    "address":{
        "city": "New York",
        "state": "NY"
    }
}
```
    """
    expected6 = """{
    "name"": "John",
    "address":{
        "city": "New York",
        "state": "NY"
    }
}"""
    result6 = get_json_code(test6)
    print(f"Test 6: {'PASS' if result6 == expected6 else 'FAIL'}")
    print(f"Input: {test6}")
    print(f"Expected: {expected6}")
    print(f"Result: {result6}")
    print()

if __name__ == '__main__':
    print("Testing get_cpp_code function:")
    print("================================")
    test_get_cpp_code()
    print("\nTesting get_json_code function:")
    print("================================")
    test_get_json_code()
