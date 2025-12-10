
```python
class Header:
    def __init__(self, key, source_code):
        self.key = key                    # Class name
        self.source_code = source_code    # Original Java code
        self.type = ""                    # class/interface/enum
        self.methods = []                 # Method instances
        self.imports = []                 # Import statements
        self.translated_code = ""         # Generated C++ code
        self.header_files = []            # Dependencies

class Method:
    def __init__(self, key, code, source_tag, header):
        self.key = key                    # Class:Method(params)
        self.code = code                  # Java implementation
        self.children = set()             # Called methods
        self.parents = set()              # Calling methods
        self.translated_code = ""         # C++ implementation
        self.compile_output = ""          # Compilation results
```