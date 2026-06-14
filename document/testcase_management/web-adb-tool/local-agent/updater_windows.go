//go:build windows

package main

import (
	"fmt"
	"os"
	"os/exec"
	"syscall"
)

// ApplyUpdate 应用更新 (Windows 版本)
func ApplyUpdate(updateFile string) error {
	// 获取当前执行文件路径
	currentPath, err := GetAgentExecutablePath()
	if err != nil {
		return fmt.Errorf("failed to get executable path: %v", err)
	}

	return applyUpdateWindows(updateFile, currentPath)
}

// applyUpdateWindows Windows 平台的更新逻辑
func applyUpdateWindows(updateFile, currentPath string) error {
	// 创建更新脚本
	scriptPath := currentPath + ".update.bat"
	backupPath := currentPath + ".backup"
	logPath := currentPath + ".update.log"

	// 改进的更新脚本：
	// 1. 等待更长时间确保旧进程完全退出
	// 2. 检查文件操作是否成功
	// 3. 记录日志
	// 4. 启动新进程时隐藏窗口
	script := fmt.Sprintf(`@echo off
echo [%%date%% %%time%%] Starting update... > "%s"

REM 等待旧进程完全退出
echo [%%date%% %%time%%] Waiting for old process to exit... >> "%s"
timeout /t 3 /nobreak >nul

REM 备份当前文件
echo [%%date%% %%time%%] Backing up current file... >> "%s"
if exist "%s" (
    copy /y "%s" "%s" >> "%s" 2>&1
    if errorlevel 1 (
        echo [%%date%% %%time%%] ERROR: Failed to backup current file >> "%s"
        exit /b 1
    )
    del "%s" >> "%s" 2>&1
)

REM 移动新文件到目标位置
echo [%%date%% %%time%%] Installing new version... >> "%s"
copy /y "%s" "%s" >> "%s" 2>&1
if errorlevel 1 (
    echo [%%date%% %%time%%] ERROR: Failed to install new version >> "%s"
    REM 恢复备份
    if exist "%s" (
        copy /y "%s" "%s" >> "%s" 2>&1
    )
    exit /b 1
)
del "%s" >> "%s" 2>&1

REM 启动新进程（隐藏窗口）
echo [%%date%% %%time%%] Starting new agent... >> "%s"
start "" /min "%s" >> "%s" 2>&1
if errorlevel 1 (
    echo [%%date%% %%time%%] ERROR: Failed to start new agent >> "%s"
    REM 尝试直接启动
    "%s" >> "%s" 2>&1
)

echo [%%date%% %%time%%] Update completed successfully >> "%s"

REM 等待一下确保新进程启动
timeout /t 2 /nobreak >nul

REM 删除备份文件
if exist "%s" del "%s" >> "%s" 2>&1

REM 删除脚本自身
del "%%~f0"
`, 
		logPath,                    // 日志文件
		logPath,                    // 等待日志
		logPath,                    // 备份日志
		currentPath,                // 检查当前文件是否存在
		currentPath, backupPath, logPath, // copy 备份操作
		logPath,                    // 备份失败日志
		currentPath, logPath,       // del 当前文件
		logPath,                    // 安装日志
		updateFile, currentPath, logPath, // copy 新文件
		logPath,                    // 安装失败日志
		backupPath,                 // 检查备份是否存在
		backupPath, currentPath, logPath, // copy 恢复备份
		updateFile, logPath,        // del 更新文件
		logPath,                    // 启动日志
		currentPath, logPath,       // start 启动新进程
		logPath,                    // 启动失败日志
		currentPath, logPath,       // 直接启动
		logPath,                    // 成功日志
		backupPath, backupPath, logPath, // 删除备份文件
	)

	if err := os.WriteFile(scriptPath, []byte(script), 0644); err != nil {
		return fmt.Errorf("failed to create update script: %v", err)
	}

	// 启动更新脚本（隐藏窗口）
	cmd := exec.Command("cmd", "/c", scriptPath)
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow:    true,
		CreationFlags: 0x08000000, // CREATE_NO_WINDOW
	}
	
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("failed to start update script: %v", err)
	}

	// 保存更新信息
	saveUpdateInfo()

	// 退出当前程序，让脚本完成更新
	os.Exit(0)
	return nil
}
