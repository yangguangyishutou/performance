
```bash
Starting translation for project: Cookie
Output directory: /path/to/output/Cookie/deepseek
Using model: deepseek

-- Loading translation graph...
Found 8 classes, 45 methods
Building call graph... Done

-- Generating translation schemes...
Class: Cookie -> Scheme generated
Class: Header -> Scheme generated

-- Translating methods...
Layer 0: 15 methods translated
Layer 1: 20 methods translated
Layer 2: 10 methods translated

-- Running compilation agent...
File: Cookie.cpp - Compiling... Error found
Error: Missing header <string>
Fix: Adding #include <string>
File: Cookie.cpp - Compiling... Success

Translation completed successfully!
Generated files available at: /path/to/output/Cookie/deepseek/result/
```