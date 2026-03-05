import re
def sanitize_filename(name: str) -> str:
    """
    按照 apply_entire_class 的逻辑清洗文件名：
    : < > -> -
    ?     -> +
    """
    if not name:
        return "unnamed_file"

    # 1. 按照 apply_entire_class 的逻辑进行精确替换
    # : 替换为 -
    # < 替换为 -
    # > 替换为 -
    # ? 替换为 +
    name = name.replace(':', '-').replace('<', '-').replace('>', '-').replace('?', '+')

    # 2. (可选但建议) 处理 Windows 路径中其他绝对禁止的字符
    # 即使 apply_entire_class 没写，/ \ * " | 也会导致创建文件夹失败
    illegal_remaining = r'[\\/\*"|]'
    name = re.sub(illegal_remaining, '_', name)

    # 3. 处理 Windows 保留名称 (如 CON, PRN 等)
    reserved_names = {
        "CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", 
        "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", 
        "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
    }
    if name.upper() in reserved_names:
        name = f"_{name}"

    # 4. 长度限制
    if len(name) > 200:
        name = name[:200]

    return name