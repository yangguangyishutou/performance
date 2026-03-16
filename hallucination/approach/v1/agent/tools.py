import subprocess
import json
import os

from path_config import cfg_review_dir_path

def compile_file(file: str) -> dict:
    """
    Compile a single C++ file with -c flag (no linking).
    Input:  { "file": "xxx.cpp" }
    Output: { "success": true/false, "log": "compiler output" }
    """
    try:
        if not file or not os.path.exists(file):
            return {"success": False, "log": f"File not found: {file}"}

        # Derive object file name
        obj_file = os.path.splitext(file)[0] + ".o"

        # Run clang++ -c
        result = subprocess.run(
            ["clang++", "-c", file, "-o", obj_file],
            capture_output=True,
            text=True
        )

        success = result.returncode == 0
        log_output = result.stdout + result.stderr
        return {"success": success, "log": log_output}

    except Exception as e:
        return {"success": False, "log": str(e)}


def read_file(file: str) -> dict:
    """
    Read a file content.
    Input:  { "file": "xxx.cpp" }
    Output: { "success": true/false, "content": "file content" }
    """
    try:
        if not file or not os.path.exists(file):
            return {"success": False, "content": "file not found"}

        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        return {"success": True, "content": content}

    except Exception as e:
        return {"success": False, "content": f"[Error reading file: {e}]"}


def write_file(file: str, content: str) -> dict:
    """
    Overwrite or modify an existing file.
    Input:  { "file": "xxx.cpp", "content": "new content" }
    Output: { "success": true/false }
    """
    try:
        if not file:
            return {"success": False}

        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


def create_file(file: str, content: str) -> dict:
    """
    Create a new file.
    Input:  { "file": "xxx.cpp", "content": "file content" }
    Output: { "success": true/false }
    """
    try:
        if not file:
            return {"success": False, "error": "Missing file name"}

        if os.path.exists(file):
            return {"success": False, "error": "File already exists"}

        with open(file, "w", encoding="utf-8") as f:
            f.write(content)

        return {"success": True}

    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    # Example 1: Compile file
    print(compile_file("main.cpp"))

    # Example 2: Read file
    print(read_file("main.cpp"))

    # Example 3: Write file
    print(write_file("main.cpp", "// modified code"))

    # Example 4: Create new file
    print(create_file("new.cpp", "int main() { return 0; }"))
