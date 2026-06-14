//go:build windows

package main

import (
	"os/exec"
	"syscall"
)

const (
	CREATE_NO_WINDOW = 0x08000000
)

// hideWindow 为 Windows 命令隐藏控制台窗口
func hideWindow(cmd *exec.Cmd) {
	cmd.SysProcAttr = &syscall.SysProcAttr{
		HideWindow:    true,
		CreationFlags: CREATE_NO_WINDOW,
	}
}

// hideConsoleWindow 隐藏当前进程的控制台窗口
func hideConsoleWindow() {
	kernel32 := syscall.NewLazyDLL("kernel32.dll")
	freeConsole := kernel32.NewProc("FreeConsole")
	freeConsole.Call()
}
