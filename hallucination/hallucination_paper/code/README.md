# 代码块索引 - Code Block Index

本文档包含了论文中所有代码块对应的markdown文件，按章节和出现顺序组织。

## 文件命名规范
- `fig{章号}-{顺序号}-{描述}.md`
- 转换为PDF后对应论文中的图号引用

## 实现章节 (Chapter 3: Implementation)

### 图3-1: Java解析器核心逻辑
**文件**: `fig3-1-java-parser-core.md`
**论文引用**: `Figure \ref{fig:java-parser}`
**对应内容**: JavaParser工具的核心解析逻辑

### 图3-2: LLM生成器接口
**文件**: `fig3-2-llm-generator-interface.md`
**论文引用**: `Figure \ref{fig:llm-interface}`
**对应内容**: 统一的LLM接口实现

### 图3-3: 调用图构建
**文件**: `fig3-3-call-graph-construction.md`
**论文引用**: `Figure \ref{fig:call-graph}`
**对应内容**: 方法调用关系的构建算法

### 图3-4: 代理工具接口
**文件**: `fig3-4-agent-tool-interface.md`
**论文引用**: `Figure \ref{fig:agent-tools}`
**对应内容**: 编译代理的工具接口定义

### 图3-5: 数据结构定义
**文件**: `fig3-5-header-method-data-structures.md`
**论文引用**: `Figure \ref{fig:data-structures}`
**对应内容**: Header和Method类的核心数据结构

### 图3-6: 翻译管道执行
**文件**: `fig3-6-pipeline-execution.md`
**论文引用**: `Figure \ref{fig:pipeline}`
**对应内容**: 完整的翻译管道协调逻辑

## 工具演示章节 (Chapter 5: Tool Demonstration)

### 图5-1: 原始Java代码
**文件**: `fig5-1-cookie-original-java.md`
**论文引用**: `Figure \ref{fig:original-java}`
**对应内容**: Cookie类的原始Java实现

### 图5-2: 翻译方案
**文件**: `fig5-2-cookie-translation-scheme.md`
**论文引用**: `Figure \ref{fig:translation-scheme}`
**对应内容**: LLM生成的类级别翻译策略

### 图5-3: C++头文件
**文件**: `fig5-3-cookie-translated-h.md`
**论文引用**: `Figure \ref{fig:cpp-header}`
**对应内容**: 翻译后的C++头文件

### 图5-4: C++实现文件
**文件**: `fig5-4-cookie-translated-cpp.md`
**论文引用**: `Figure \ref{fig:cpp-impl}`
**对应内容**: 翻译后的C++实现文件

### 图5-5: 代理修复过程
**文件**: `fig5-5-agent-fix-process.md`
**论文引用**: `Figure \ref{fig:agent-fix}`
**对应内容**: 编译代理的错误修复流程

### 图5-6: Java泛型类
**文件**: `fig5-6-generic-java-class.md`
**论文引用**: `Figure \ref{fig:java-generics}`
**对应内容**: 原始Java泛型类示例

### 图5-7: C++模板等价物
**文件**: `fig5-7-cpp-template-equivalent.md`
**论文引用**: `Figure \ref{fig:cpp-templates}`
**对应内容**: 对应的C++模板实现

### 图5-8: Java内存管理
**文件**: `fig5-8-java-memory-management.md`
**论文引用**: `Figure \ref{fig:java-memory}`
**对应内容**: Java的垃圾回收内存管理

### 图5-9: C++ RAII等价物
**文件**: `fig5-9-cpp-raii-equivalent.md`
**论文引用**: `Figure \ref{fig:cpp-raii}`
**对应内容**: C++的RAII内存管理模式

### 图5-10: Java异常处理
**文件**: `fig5-10-java-exception-handling.md`
**论文引用**: `Figure \ref{fig:java-exceptions}`
**对应内容**: Java的检查异常处理

### 图5-11: C++异常处理
**文件**: `fig5-11-cpp-exception-handling.md`
**论文引用**: `Figure \ref{fig:cpp-exceptions}`
**对应内容**: C++的异常处理模式

### 图5-12: 移动语义优化
**文件**: `fig5-12-move-semantics-optimization.md`
**论文引用**: `Figure \ref{fig:move-semantics}`
**对应内容**: C++移动语义的性能优化

### 图5-13: 模板特化
**文件**: `fig5-13-template-specialization.md`
**论文引用**: `Figure \ref{fig:template-specialization}`
**对应内容**: 字符串连接的模板特化优化

### 图5-14: 工具执行输出
**文件**: `fig5-14-tool-execution-output.md`
**论文引用**: `Figure \ref{fig:tool-output}`
**对应内容**: 完整的工具执行过程输出

## 论文引用更新

论文中的所有代码块引用已经更新为指向 `code/` 目录中的PDF文件：

### 实现章节 (Chapter 3)
- `Figure \ref{fig:java-parser}` → `code/fig3-1-java-parser-core.pdf`
- `Figure \ref{fig:llm-interface}` → `code/fig3-2-llm-generator-interface.pdf`
- `Figure \ref{fig:call-graph}` → `code/fig3-3-call-graph-construction.pdf`
- `Figure \ref{fig:agent-tools}` → `code/fig3-4-agent-tool-interface.pdf`
- `Figure \ref{fig:data-structures}` → `code/fig3-5-header-method-data-structures.pdf`
- `Figure \ref{fig:pipeline}` → `code/fig3-6-pipeline-execution.pdf`

### 工具演示章节 (Chapter 5)
- `Figure \ref{fig:original-java}` → `code/fig5-1-cookie-original-java.pdf`
- `Figure \ref{fig:translation-scheme}` → `code/fig5-2-cookie-translation-scheme.pdf`
- `Figure \ref{fig:cpp-header}` → `code/fig5-3-cookie-translated-h.pdf`
- `Figure \ref{fig:cpp-impl}` → `code/fig5-4-cookie-translated-cpp.pdf`
- `Figure \ref{fig:agent-fix}` → `code/fig5-5-agent-fix-process.pdf`
- `Figure \ref{fig:java-generics}` → `code/fig5-6-generic-java-class.pdf`
- `Figure \ref{fig:cpp-templates}` → `code/fig5-7-cpp-template-equivalent.pdf`
- `Figure \ref{fig:java-memory}` → `code/fig5-8-java-memory-management.pdf`
- `Figure \ref{fig:cpp-raii}` → `code/fig5-9-cpp-raii-equivalent.pdf`
- `Figure \ref{fig:java-exceptions}` → `code/fig5-10-java-exception-handling.pdf`
- `Figure \ref{fig:cpp-exceptions}` → `code/fig5-11-cpp-exception-handling.pdf`
- `Figure \ref{fig:move-semantics}` → `code/fig5-12-move-semantics-optimization.pdf`
- `Figure \ref{fig:template-specialization}` → `code/fig5-13-template-specialization.pdf`
- `Figure \ref{fig:tool-output}` → `code/fig5-14-tool-execution-output.pdf`

## LaTeX中的使用

在LaTeX论文中，所有图片都使用以下格式引用：

```latex
\begin{figure}[h]
\centering
\includegraphics[width=\columnwidth]{code/figX-Y-name.pdf}
\caption{Description}
\label{fig:label}
\end{figure}
```

## 转换说明

每个markdown文件都可以通过以下步骤转换为PDF：

1. 使用支持代码高亮的markdown编辑器打开文件
2. 导出为PDF格式（建议使用等宽字体）
3. 确保PDF文件保存在 `code/` 目录中
4. 文件名与markdown文件同名（扩展名为.pdf）

## PDF转换选项

我们提供了多种转换脚本来优化PDF尺寸和格式：

### 1. 标准转换
```bash
# Linux/macOS
./convert_to_pdf.sh

# Windows
convert_to_pdf.bat
```
**特点**:
- 页面尺寸: 7in x 9in
- 边距: 0.5in
- 字体: 9pt
- 适合大多数代码块

### 2. 紧凑转换（推荐）
```bash
# Linux/macOS
./convert_with_template.sh

# Windows
convert_with_template.bat
```
**特点**:
- 页面尺寸: 6.5in x 8.5in
- 边距: 0.4in
- 字体: 8pt
- 自定义代码高亮模板
- 最小化空白

### 3. 智能优化转换
```bash
# Linux/macOS
./convert_optimized.sh
```
**特点**:
- 根据代码行数自动调整页面尺寸
- 动态字体大小
- 智能边距设置
- 最小化空白区域
- 适合不同大小的代码块

### 手动转换示例
```bash
# 基本转换
pandoc fig3-1-java-parser-core.md -o fig3-1-java-parser-core.pdf

# 使用自定义模板
pandoc fig3-1-java-parser-core.md \
    --template=code-template.tex \
    --output fig3-1-java-parser-core.pdf \
    --pdf-engine=xelatex

# 超紧凑设置
pandoc fig3-1-java-parser-core.md \
    --output fig3-1-java-parser-core.pdf \
    --highlight-style=pygments \
    --pdf-engine=xelatex \
    --variable fontsize=7pt \
    --variable geometry:"paperwidth=5in, paperheight=7in, margin=0.2in"
```

## 注意事项

1. **统一目录**: 所有PDF文件必须保存在 `code/` 目录中
2. **命名规范**: PDF文件名必须与markdown文件名完全一致
3. **代码高亮**: 转换时确保保持代码的语法高亮和格式
4. **字体设置**: 建议使用等宽字体（如Courier New, Monaco）以保持代码对齐
5. **图片质量**: 确保PDF分辨率足够高，在论文中缩放后仍保持可读性
6. **尺寸控制**: 转换时适当设置页面大小以适应论文的列宽