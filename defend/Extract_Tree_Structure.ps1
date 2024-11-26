# Extract_Tree_Structure.ps1

param(
    [string]$path = "./defend",
    [string]$OutputFile = "./defend/directory_structure.txt"
)

function Write-OutputBoth {
    param(
        [string]$Message,
        [System.ConsoleColor]$ForegroundColor = 'White'
    )
    Write-Host $Message -ForegroundColor $ForegroundColor
    $Message | Out-File -FilePath $OutputFile -Append -Encoding utf8
}

function Show-Tree {
    param(
        [string]$Path,
        [string]$Indent = "",
        [int]$Count = 1
    )

    $items = Get-ChildItem -Path $Path
    foreach ($item in $items) {
        if ($item.PSIsContainer) {
            # Directory display
            Write-OutputBoth "${Indent}[$Count] 📁 $($item.Name)" -ForegroundColor Blue
            Show-Tree -Path $item.FullName -Indent "    $Indent" -Count 1
            $Count++
        }
        else {
            # File display
            Write-OutputBoth "${Indent}└── 📄 $($item.Name)" -ForegroundColor Green
        }
    }
}

# Initialize output file with UTF-8 encoding
"" | Out-File -FilePath $OutputFile -Encoding utf8

# Main directory traversal
$folders = @("Attack", "Defend", "benchmark")
Write-OutputBoth "Directory Structure:" -ForegroundColor Yellow
Write-OutputBoth "===================" -ForegroundColor Yellow

foreach ($folder in $folders) {
    $fullPath = Join-Path $path $folder
    if (Test-Path $fullPath) {
        Write-OutputBoth "`n== $folder ==" -ForegroundColor Yellow
        Show-Tree -Path $fullPath
    }
    else {
        Write-OutputBoth "Directory '$fullPath' not found!" -ForegroundColor Red
    }
}

Write-OutputBoth "`nStructure has been saved to: $OutputFile" -ForegroundColor Cyan