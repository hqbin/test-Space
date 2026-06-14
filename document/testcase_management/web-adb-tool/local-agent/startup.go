package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
)

// AddToStartup 添加到系统启动项
func AddToStartup() error {
	switch runtime.GOOS {
	case "windows":
		return addToStartupWindows()
	case "darwin":
		return addToStartupMacOS()
	case "linux":
		return addToStartupLinux()
	default:
		return fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}
}

// RemoveFromStartup 从系统启动项移除
func RemoveFromStartup() error {
	switch runtime.GOOS {
	case "windows":
		return removeFromStartupWindows()
	case "darwin":
		return removeFromStartupMacOS()
	case "linux":
		return removeFromStartupLinux()
	default:
		return fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}
}

// IsInStartup 检查是否在启动项中
func IsInStartup() bool {
	switch runtime.GOOS {
	case "windows":
		return isInStartupWindows()
	case "darwin":
		return isInStartupMacOS()
	case "linux":
		return isInStartupLinux()
	default:
		return false
	}
}

// addToStartupWindows Windows 系统添加启动项
func addToStartupWindows() error {
	exePath, err := GetAgentExecutablePath()
	if err != nil {
		return err
	}

	// 使用注册表添加启动项
	// HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
	startupPath := filepath.Join(os.Getenv("APPDATA"), 
		"Microsoft\\Windows\\Start Menu\\Programs\\Startup\\ADB-Agent.lnk")

	// 创建快捷方式（需要使用 Windows API 或第三方库）
	// 这里使用简单的批处理文件作为替代
	batPath := filepath.Join(filepath.Dir(startupPath), "ADB-Agent.bat")
	batContent := fmt.Sprintf("@echo off\nstart \"\" \"%s\"", exePath)
	
	if err := os.WriteFile(batPath, []byte(batContent), 0644); err != nil {
		return err
	}

	fmt.Println("✓ Added to Windows startup")
	return nil
}

// removeFromStartupWindows Windows 系统移除启动项
func removeFromStartupWindows() error {
	batPath := filepath.Join(os.Getenv("APPDATA"), 
		"Microsoft\\Windows\\Start Menu\\Programs\\Startup\\ADB-Agent.bat")
	
	if err := os.Remove(batPath); err != nil && !os.IsNotExist(err) {
		return err
	}

	fmt.Println("✓ Removed from Windows startup")
	return nil
}

// isInStartupWindows 检查是否在 Windows 启动项中
func isInStartupWindows() bool {
	batPath := filepath.Join(os.Getenv("APPDATA"), 
		"Microsoft\\Windows\\Start Menu\\Programs\\Startup\\ADB-Agent.bat")
	
	_, err := os.Stat(batPath)
	return err == nil
}

// addToStartupMacOS macOS 系统添加启动项
func addToStartupMacOS() error {
	exePath, err := GetAgentExecutablePath()
	if err != nil {
		return err
	}

	homeDir, _ := os.UserHomeDir()
	plistPath := filepath.Join(homeDir, "Library/LaunchAgents/com.adb-agent.plist")

	plistContent := fmt.Sprintf(`<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.adb-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>%s</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>`, exePath)

	// 创建目录
	os.MkdirAll(filepath.Dir(plistPath), 0755)

	// 写入 plist 文件
	if err := os.WriteFile(plistPath, []byte(plistContent), 0644); err != nil {
		return err
	}

	fmt.Println("✓ Added to macOS startup")
	return nil
}

// removeFromStartupMacOS macOS 系统移除启动项
func removeFromStartupMacOS() error {
	homeDir, _ := os.UserHomeDir()
	plistPath := filepath.Join(homeDir, "Library/LaunchAgents/com.adb-agent.plist")

	if err := os.Remove(plistPath); err != nil && !os.IsNotExist(err) {
		return err
	}

	fmt.Println("✓ Removed from macOS startup")
	return nil
}

// isInStartupMacOS 检查是否在 macOS 启动项中
func isInStartupMacOS() bool {
	homeDir, _ := os.UserHomeDir()
	plistPath := filepath.Join(homeDir, "Library/LaunchAgents/com.adb-agent.plist")

	_, err := os.Stat(plistPath)
	return err == nil
}

// addToStartupLinux Linux 系统添加启动项
func addToStartupLinux() error {
	exePath, err := GetAgentExecutablePath()
	if err != nil {
		return err
	}

	homeDir, _ := os.UserHomeDir()
	desktopPath := filepath.Join(homeDir, ".config/autostart/adb-agent.desktop")

	desktopContent := fmt.Sprintf(`[Desktop Entry]
Type=Application
Name=ADB Local Agent
Exec=%s
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true`, exePath)

	// 创建目录
	os.MkdirAll(filepath.Dir(desktopPath), 0755)

	// 写入 desktop 文件
	if err := os.WriteFile(desktopPath, []byte(desktopContent), 0644); err != nil {
		return err
	}

	fmt.Println("✓ Added to Linux startup")
	return nil
}

// removeFromStartupLinux Linux 系统移除启动项
func removeFromStartupLinux() error {
	homeDir, _ := os.UserHomeDir()
	desktopPath := filepath.Join(homeDir, ".config/autostart/adb-agent.desktop")

	if err := os.Remove(desktopPath); err != nil && !os.IsNotExist(err) {
		return err
	}

	fmt.Println("✓ Removed from Linux startup")
	return nil
}

// isInStartupLinux 检查是否在 Linux 启动项中
func isInStartupLinux() bool {
	homeDir, _ := os.UserHomeDir()
	desktopPath := filepath.Join(homeDir, ".config/autostart/adb-agent.desktop")

	_, err := os.Stat(desktopPath)
	return err == nil
}
