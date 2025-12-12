@echo off
REM 批量转换markdown文件为PDF的脚本 (Windows版本)
REM 用法: convert_to_pdf.bat
chcp 65001

echo 开始转换代码markdown文件为PDF...

REM 检查是否安装了pandoc
pandoc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到pandoc，请先安装pandoc
    echo 安装方法:
    echo   Windows: choco install pandoc 或从 https://pandoc.org/installing.html 下载
    pause
    exit /b 1
)

echo 正在转换文件...

REM 转换所有fig开头的markdown文件
for %%f in (fig*.md) do (
    echo 转换 %%f -> %%~nf.pdf

    REM 使用pandoc转换，优化PDF尺寸和格式
    pandoc "%%f" ^
        --output "%%~nf.pdf" ^
        --syntax-highlighting=tango ^
        --pdf-engine=xelatex ^
        --variable monofont="Courier New" ^
        --variable fontsize=12pt ^
        --variable geometry:"paperwidth=10in, paperheight=12in, margin=0.5in" ^
        --variable colorlinks=true ^
        --variable linkcolor=blue ^
        --variable urlcolor=blue ^
        --variable toccolor=blue ^
        --variable pagestyle=empty

    if %errorlevel% equ 0 (
        echo ✓ 成功转换 %%f
    ) else (
        echo ✗ 转换失败 %%f
    )
)

echo.
echo 转换完成！
pause