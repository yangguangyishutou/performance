#!/bin/bash

# 批量转换markdown文件为PDF的脚本
# 用法: ./convert_to_pdf.sh

echo "开始转换代码markdown文件为PDF..."

# 检查是否安装了pandoc
if ! command -v pandoc &> /dev/null; then
    echo "错误: 未找到pandoc，请先安装pandoc"
    echo "安装方法:"
    echo "  Ubuntu/Debian: sudo apt-get install pandoc"
    echo "  macOS: brew install pandoc"
    echo "  Windows: choco install pandoc"
    exit 1
fi

# 创建PDF目录（如果不存在）
mkdir -p pdfs

# 转换所有fig开头的markdown文件
echo "正在转换文件..."
for file in fig*.md; do
    if [ -f "$file" ]; then
        pdf_name="${file%.md}.pdf"
        echo "转换 $file -> $pdf_name"

        # 使用pandoc转换，优化PDF尺寸和格式
        pandoc "$file" \
            --output "$pdf_name" \
            --highlight-style=tango \
            --pdf-engine=xelatex \
            --variable monofont="Courier New" \
            --variable fontsize=9pt \
            --variable geometry:"paperwidth=7in, paperheight=9in, margin=0.5in" \
            --variable colorlinks=true \
            --variable linkcolor=blue \
            --variable urlcolor=blue \
            --variable toccolor=blue \
            --variable pagestyle=empty

        if [ $? -eq 0 ]; then
            echo "✓ 成功转换 $file"
        else
            echo "✗ 转换失败 $file"
        fi
    fi
done

echo ""
echo "转换完成！"
echo "生成的PDF文件:"
ls -la *.pdf

echo ""
echo "使用说明:"
echo "1. 确保所有PDF文件都在code目录中"
echo "2. 在LaTeX论文中，使用 \\includegraphics{code/filename.pdf} 引用"
echo "3. 检查生成的PDF文件质量和可读性"
echo ""
echo "PDF优化设置:"
echo "- 页面尺寸: 7in x 9in (适合论文列宽)"
echo "- 边距: 0.5in"
echo "- 字体: 9pt 等宽字体"
echo "- 页面样式: 空白（减少多余元素）"
echo ""
echo "如需调整尺寸，可以修改脚本中的geometry参数"