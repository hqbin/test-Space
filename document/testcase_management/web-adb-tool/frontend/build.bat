@echo off
REM ============================================================
REM Web ADB Tool - 前端构建脚本 (Windows)
REM ============================================================

echo.
echo ============================================================
echo Web ADB Tool - 前端构建
echo ============================================================
echo.

REM 检查 Node.js 是否安装
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js 16+
    pause
    exit /b 1
)

REM 检查 npm 是否安装
npm --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 npm
    pause
    exit /b 1
)

echo [1/4] 检查依赖...
if not exist "node_modules" (
    echo [提示] 未找到 node_modules，正在安装依赖...
    call npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

echo [2/4] 清理旧的构建文件...
if exist "dist" rmdir /s /q dist

echo [3/4] 构建生产版本...
call npm run build
if errorlevel 1 (
    echo [错误] 构建失败
    pause
    exit /b 1
)

echo [4/4] 复制配置文件...
copy ".env.example" "dist\.env.example"

echo.
echo ============================================================
echo 构建完成！
echo ============================================================
echo.
echo 输出目录: dist\
echo.
echo 部署说明:
echo 1. 将 dist 文件夹内容复制到 Web 服务器
echo 2. 配置 Nginx 或 Apache 指向 dist 目录
echo 3. 确保后端 API 地址正确配置
echo.
echo 本地预览:
echo   npm run preview
echo.
pause
