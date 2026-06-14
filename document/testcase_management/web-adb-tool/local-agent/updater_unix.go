//go:build !windows

package main

import (
	"fmt"
	"os"
	"runtime"
)

// ApplyUpdate 应用更新 (Unix 版本)
func ApplyUpdate(updateFile string) error {
	// 获取当前执行文件路径
	currentPath, err := GetAgentExecutablePath()
	if err != nil {
		return fmt.Errorf("failed to get executable path: %v", err)
	}

	return applyUpdateUnix(updateFile, currentPath)
}

// applyUpdateUnix Unix 平台的更新逻辑
func applyUpdateUnix(updateFile, currentPath string) error {
	// 备份当前文件
	backupPath := currentPath + ".backup"
	if err := copyFile(currentPath, backupPath); err != nil {
		return fmt.Errorf("failed to backup current file: %v", err)
	}

	// 替换文件
	if err := os.Remove(currentPath); err != nil {
		return fmt.Errorf("failed to remove old file: %v", err)
	}

	if err := copyFile(updateFile, currentPath); err != nil {
		// 恢复备份
		copyFile(backupPath, currentPath)
		return fmt.Errorf("failed to copy new file: %v", err)
	}

	// 设置执行权限（Unix 系统）
	if runtime.GOOS != "windows" {
		if err := os.Chmod(currentPath, 0755); err != nil {
			return fmt.Errorf("failed to set permissions: %v", err)
		}
	}

	// 删除临时文件
	os.Remove(updateFile)

	// 保存更新信息
	saveUpdateInfo()

	return nil
}
