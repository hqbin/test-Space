# ============================================================
# Aider 全自动工作流 - 快捷启动脚本
# 用法:
#   .\run_workflow.ps1 "你的需求"
#   .\run_workflow.ps1 -Requirement "需求" -Skip "review,fix"
#   .\run_workflow.ps1 -Requirement "需求" -DryRun
# ============================================================

param(
    [Parameter(Position=0)]
    [string]$Requirement,
    
    [Parameter()]
    [string]$Skip = "",
    
    [Parameter()]
    [string]$FromStage = "",
    
    [Parameter()]
    [switch]$DryRun,
    
    [Parameter()]
    [int]$Timeout = 300
)

# 检查 Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "❌ 未找到 Python，请先安装 Python 3.8+" -ForegroundColor Red
    exit 1
}

# 检查 Aider
$aider = Get-Command aider -ErrorAction SilentlyContinue
if (-not $aider) {
    Write-Host "❌ 未找到 aider，请先安装: pip install aider-chat" -ForegroundColor Red
    exit 1
}

# 构建参数
$args_list = @()

if ($Requirement) {
    $args_list += "`"$Requirement`""
}

if ($Skip) {
    $args_list += "--skip"
    $args_list += $Skip
}

if ($FromStage) {
    $args_list += "--from-stage"
    $args_list += $FromStage
}

if ($DryRun) {
    $args_list += "--dry-run"
}

if ($Timeout -ne 300) {
    $args_list += "--timeout"
    $args_list += $Timeout
}

# 运行
$scriptPath = Join-Path $PSScriptRoot "aider_workflow.py"
$cmd = "python `"$scriptPath`" " + ($args_list -join " ")
Write-Host "🚀 启动全自动工作流..." -ForegroundColor Cyan
Write-Host "   命令: $cmd" -ForegroundColor Gray
Write-Host ""
Invoke-Expression $cmd