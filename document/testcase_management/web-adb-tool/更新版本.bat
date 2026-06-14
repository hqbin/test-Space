@echo off
chcp 65001 >nul
title ADB Web Tool - 更新版本号

echo ========================================
echo    ADB Web Tool - 更新版本号
echo ========================================
echo.

:: 提示输入新版本号
set /p NEW_VERSION="请输入新版本号 (格式: x.y.z，例如: 1.3.3): "

:: 验证版本号格式
echo %NEW_VERSION%| findstr /r "^[0-9][0-9]*\.[0-9][0-9]*\.[0-9][0-9]*$" >nul
if %errorlevel% neq 0 (
    echo.
    echo 【错误】 版本号格式不正确！
    echo 正确格式: x.y.z ^(例如: 1.3.3^)
    echo.
    pause
    exit /b 1
)

:: 拆分版本号
for /f "tokens=1,2,3 delims=." %%a in ("%NEW_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set PATCH=%%c
)

echo.
echo 【信息】 新版本号: %NEW_VERSION%
echo 【信息】 主版本: %MAJOR%
echo 【信息】 次版本: %MINOR%
echo 【信息】 修订版本: %PATCH%
echo.

:: 确认
set /p CONFIRM="确认更新版本号？(Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo.
    echo 【取消】 已取消更新
    echo.
    pause
    exit /b 0
)

echo.
echo ========================================
echo    开始更新版本号...
echo ========================================
echo.

:: 1. 更新 local-agent/installer.go
echo 【1/3】 更新 local-agent/installer.go...
powershell -Command "(Get-Content 'local-agent\installer.go') -replace 'AgentVersion = \"[0-9.]+\"', 'AgentVersion = \"%NEW_VERSION%\"' | Set-Content 'local-agent\installer.go'"
if %errorlevel% equ 0 (
    echo 【√】 installer.go 更新成功
) else (
    echo 【×】 installer.go 更新失败
)

:: 2. 更新 local-agent/versioninfo.json
echo 【2/3】 更新 local-agent/versioninfo.json...
powershell -Command "$json = Get-Content 'local-agent\versioninfo.json' -Raw | ConvertFrom-Json; $json.FixedFileInfo.FileVersion.Major = %MAJOR%; $json.FixedFileInfo.FileVersion.Minor = %MINOR%; $json.FixedFileInfo.FileVersion.Patch = %PATCH%; $json.FixedFileInfo.ProductVersion.Major = %MAJOR%; $json.FixedFileInfo.ProductVersion.Minor = %MINOR%; $json.FixedFileInfo.ProductVersion.Patch = %PATCH%; $json.StringFileInfo.FileVersion = '%NEW_VERSION%.0'; $json.StringFileInfo.ProductVersion = '%NEW_VERSION%.0'; $json | ConvertTo-Json -Depth 10 | Set-Content 'local-agent\versioninfo.json'"
if %errorlevel% equ 0 (
    echo 【√】 versioninfo.json 更新成功
) else (
    echo 【×】 versioninfo.json 更新失败
)

:: 3. 更新 frontend/public/api/agent/latest-version.json
echo 【3/3】 更新 frontend/public/api/agent/latest-version.json...
powershell -ExecutionPolicy Bypass -File "update-json-version.ps1" -NewVersion "%NEW_VERSION%"
if %errorlevel% equ 0 (
    echo 【√】 latest-version.json 更新成功
) else (
    echo 【×】 latest-version.json 更新失败
)

echo.
echo ========================================
echo    版本号更新完成！
echo ========================================
echo.

:: 显示更新后的版本信息
echo 更新的文件:
echo   - local-agent\installer.go
echo   - local-agent\versioninfo.json
echo   - frontend\public\api\agent\latest-version.json
echo.

echo 新版本号: %NEW_VERSION%
echo.

echo 【提示】 接下来需要：
echo   1. 运行 "打包代理.bat" 重新编译代理
echo   2. 或者手动执行以下命令：
echo      cd local-agent
echo      goversioninfo -64
echo      go build -ldflags="-H windowsgui" -o adb-agent-windows.exe
echo      copy adb-agent-windows.exe ..\frontend\public\downloads\
echo.

:: 询问是否立即编译
set /p BUILD="是否立即编译代理？(Y/N): "
if /i "%BUILD%"=="Y" (
    echo.
    echo 【信息】 开始编译代理...
    echo.
    call 打包代理.bat
) else (
    echo.
    echo 【提示】 请记得手动编译代理
    echo.
)

pause
