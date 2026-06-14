@echo off
chcp 65001 >nul
title ADB Web Tool - 打包本地代理

echo ========================================
echo    ADB Web Tool - 打包本地代理
echo ========================================
echo.

:: 检查 Go 是否安装
where go >nul 2>&1
if %errorlevel% neq 0 (
    echo 【错误】 Go 未安装或未在 PATH 中！
    echo 请先安装 Go: https://golang.org/dl/
    echo.
    pause
    exit /b 1
)

:: 显示 Go 版本
echo 【信息】 Go 版本:
go version
echo.

:: 进入本地代理目录
cd local-agent

:: 检查 goversioninfo 是否安装
where goversioninfo >nul 2>&1
if %errorlevel% neq 0 (
    echo 【警告】 goversioninfo 未安装，正在安装...
    go install github.com/josephspurrier/goversioninfo/cmd/goversioninfo@latest
    if %errorlevel% neq 0 (
        echo 【×】 goversioninfo 安装失败
        echo 【提示】 请手动安装: go install github.com/josephspurrier/goversioninfo/cmd/goversioninfo@latest
        cd ..
        pause
        exit /b 1
    )
    echo 【√】 goversioninfo 安装成功
    echo.
)

:: 下载依赖
echo 【0/5】 下载依赖...
go mod download
if %errorlevel% neq 0 (
    echo 【×】 依赖下载失败
    cd ..
    pause
    exit /b 1
)
echo 【√】 依赖下载成功
echo.

:: 生成版本信息资源文件
echo 【1/5】 生成版本信息资源文件...
goversioninfo -64
if %errorlevel% equ 0 (
    echo 【√】 版本信息资源文件生成成功: resource.syso
) else (
    echo 【×】 版本信息资源文件生成失败
    echo 【提示】 将继续编译，但 exe 文件将不包含版本信息
)
echo.

:: 编译 Windows 版本（隐藏控制台窗口）
echo 【2/5】 编译 Windows 版本...
set GOOS=windows
set GOARCH=amd64
go build -ldflags="-s -w -H windowsgui" -o adb-agent-windows.exe
if %errorlevel% equ 0 (
    echo 【√】 Windows 版本编译成功: adb-agent-windows.exe
) else (
    echo 【×】 Windows 版本编译失败
    cd ..
    pause
    exit /b 1
)

:: 编译 macOS Intel 版本
echo 【3/6】 编译 macOS Intel 版本...
:: 删除 Windows 资源文件（Mac 不需要）
if exist resource.syso del resource.syso
set GOOS=darwin
set GOARCH=amd64
go build -ldflags="-s -w" -o adb-agent-mac-intel
if %errorlevel% equ 0 (
    echo 【√】 macOS Intel 版本编译成功: adb-agent-mac-intel
) else (
    echo 【×】 macOS Intel 版本编译失败
    cd ..
    pause
    exit /b 1
)

:: 编译 macOS Apple Silicon 版本
echo 【4/6】 编译 macOS Apple Silicon 版本...
set GOOS=darwin
set GOARCH=arm64
go build -ldflags="-s -w" -o adb-agent-mac-arm64
if %errorlevel% equ 0 (
    echo 【√】 macOS Apple Silicon 版本编译成功: adb-agent-mac-arm64
) else (
    echo 【×】 macOS Apple Silicon 版本编译失败
    cd ..
    pause
    exit /b 1
)

:: 重新生成 Windows 资源文件（为下次编译准备）
goversioninfo -64 >nul 2>&1

:: 使用 amd64 版本作为默认 Mac 版本（兼容性更好）
echo 【5/6】 创建默认 Mac 版本...
copy /Y adb-agent-mac-intel adb-agent-mac >nul
echo 【√】 默认 Mac 版本已创建（Intel，兼容 Rosetta 2）

:: 复制到前端 public/downloads 目录
echo 【6/6】 复制到前端下载目录...
if not exist "..\frontend\public\downloads" mkdir "..\frontend\public\downloads"
copy /Y adb-agent-windows.exe ..\frontend\public\downloads\ >nul
copy /Y adb-agent-mac ..\frontend\public\downloads\ >nul
copy /Y adb-agent-mac-intel ..\frontend\public\downloads\ >nul
copy /Y adb-agent-mac-arm64 ..\frontend\public\downloads\ >nul
if %errorlevel% equ 0 (
    echo 【√】 文件已复制到前端下载目录
) else (
    echo 【×】 复制文件失败
)

:: 验证版本信息
echo 【5/5】 验证版本信息...
powershell -Command "(Get-Item adb-agent-windows.exe).VersionInfo | Select-Object FileVersion, ProductVersion, CompanyName, FileDescription | Format-List"
echo.

:: 重置环境变量
set GOOS=
set GOARCH=

cd ..

echo.
echo ========================================
echo    编译完成！
echo ========================================
echo.
echo 输出文件:
echo   - local-agent\adb-agent-windows.exe (含版本信息)
echo   - local-agent\adb-agent-mac (macOS 默认，Intel)
echo   - local-agent\adb-agent-mac-intel (macOS Intel 专用)
echo   - local-agent\adb-agent-mac-arm64 (macOS Apple Silicon 专用)
echo.
echo 前端下载文件:
echo   - frontend\public\downloads\adb-agent-windows.exe
echo   - frontend\public\downloads\adb-agent-mac (默认)
echo   - frontend\public\downloads\adb-agent-mac-intel
echo   - frontend\public\downloads\adb-agent-mac-arm64
echo.
echo 版本信息:
echo   ✓ 产品名称: ADB Local Agent
echo   ✓ 文件版本: 1.3.1.0
echo   ✓ 公司名称: WhaleTV
echo   ✓ 版权信息: Copyright (C) 2026 WhaleTV
echo.
echo Mac 版本说明:
echo   ✓ adb-agent-mac: Intel 版本（兼容 Rosetta 2）
echo   ✓ adb-agent-mac-intel: Intel Mac 专用
echo   ✓ adb-agent-mac-arm64: Apple Silicon (M1/M2/M3) 专用
echo   ✓ 两个版本都已编译，前端会自动检测并推荐合适版本
echo.
echo 新功能:
echo   ✓ 自动安装到用户目录 (%%USERPROFILE%%\.adb-agent\)
echo   ✓ 开机自动启动（完全后台运行）
echo   ✓ 自动更新检查
echo   ✓ 用户无感知运行（无界面）
echo   ✓ 修改配置功能（Pull-修改-Push）
echo   ✓ 支持执行非 ADB 命令（系统命令）
echo   ✓ 嵌入版本信息（减少安全警告）
echo.
echo 用户使用方式:
echo   1. 访问网页下载代理程序
echo   2. 双击运行（自动安装并添加到启动项）
echo   3. 程序完全后台运行，用户无需管理
echo.
echo 提示:
echo   - 版本信息可在文件属性中查看
echo   - 完全消除安全警告需要代码签名证书
echo.
pause
