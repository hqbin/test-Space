//go:build darwin

package main

import (
	"os/exec"
)

// hideWindow 为 Mac 命令（空实现，Mac 不需要隐藏窗口）
func hideWindow(cmd *exec.Cmd) {
	// Mac 不需要特殊处理
}

// hideConsoleWindow 空实现（Mac 不需要隐藏控制台窗口）
func hideConsoleWindow() {
}
