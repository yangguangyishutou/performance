import os
import sys
import chardet

def detect_encoding(file_path, sample_size=100000):
    """
    使用 chardet 检测文件编码
    """
    with open(file_path, 'rb') as f:
        raw_data = f.read(sample_size)
        result = chardet.detect(raw_data)
        return result['encoding']


def convert_to_utf8(file_path):
    """
    尝试将文件转换为 UTF-8 编码
    """
    try:
        # 先尝试用 UTF-8 打开
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        # print(f"[OK] UTF-8: {file_path}")
        return

    except UnicodeDecodeError:
        print(f"[TRY] 非 UTF-8，开始检测编码: {file_path}")

    # 猜测编码
    encoding = detect_encoding(file_path)

    if not encoding:
        print(f"[FAIL] 无法检测编码: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding=encoding, errors='strict') as f:
            content = f.read()

        # 以 UTF-8 覆盖写回
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"[CONVERTED] {file_path} | {encoding} -> utf-8")

    except Exception as e:
        print(f"[ERROR] {file_path} | {encoding} | {e}")


def process_directory(root_dir, extensions):
    """
    递归处理目录
    """
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                convert_to_utf8(file_path)


if __name__ == "__main__":
    # if len(sys.argv) < 3:
    #     print("Usage: python convert.py <directory> <ext1> <ext2> ...")
    #     print("Example: python convert.py ./data .txt .csv .py")
    #     sys.exit(1)

    # target_dir = sys.argv[1]
    # target_extensions = sys.argv[2:]
    target_dir = r"D:\projects\sitp\sitp-dataset\translation_java-cpp"
    target_extensions = [".cpp", ".h", ".json", ".txt"]

    process_directory(target_dir, target_extensions)