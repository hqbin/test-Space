package main

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
)

const (
	AgentVersion = "1.0.2"
	AgentName    = "ADB Local Agent"
)

// GetUserAgentDir Get user agent directory
func GetUserAgentDir() (string, error) {
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	agentDir := filepath.Join(homeDir, ".adb-agent")
	
	// Create directory if not exists
	if err := os.MkdirAll(agentDir, 0755); err != nil {
		return "", err
	}

	return agentDir, nil
}

// GetAgentExecutablePath Get target path for agent executable
func GetAgentExecutablePath() (string, error) {
	agentDir, err := GetUserAgentDir()
	if err != nil {
		return "", err
	}

	exeName := "adb-agent"
	if runtime.GOOS == "windows" {
		exeName += ".exe"
	}

	return filepath.Join(agentDir, exeName), nil
}

// IsInstalledInUserDir Check if already installed in user directory
func IsInstalledInUserDir() bool {
	targetPath, err := GetAgentExecutablePath()
	if err != nil {
		return false
	}

	currentPath, err := os.Executable()
	if err != nil {
		return false
	}

	// 解析符号链接（如果存在）
	currentPathResolved := currentPath
	if resolved, err := filepath.EvalSymlinks(currentPath); err == nil {
		currentPathResolved = resolved
	}
	
	targetPathResolved := targetPath
	if resolved, err := filepath.EvalSymlinks(targetPath); err == nil {
		targetPathResolved = resolved
	}

	return currentPathResolved == targetPathResolved
}

// InstallToUserDir Install to user directory
func InstallToUserDir() error {
	// Get current executable path
	currentPath, err := os.Executable()
	if err != nil {
		return fmt.Errorf("failed to get executable path: %v", err)
	}

	// Get target path
	targetPath, err := GetAgentExecutablePath()
	if err != nil {
		return fmt.Errorf("failed to get target path: %v", err)
	}

	// Resolve symlinks if exists
	currentPathResolved := currentPath
	if resolved, err := filepath.EvalSymlinks(currentPath); err == nil {
		currentPathResolved = resolved
	}
	
	targetPathResolved := targetPath
	if resolved, err := filepath.EvalSymlinks(targetPath); err == nil {
		targetPathResolved = resolved
	}

	// Skip if already at target location
	if currentPathResolved == targetPathResolved {
		return nil
	}

	// Copy file
	if err := copyFile(currentPath, targetPath); err != nil {
		return fmt.Errorf("failed to copy file: %v", err)
	}

	// Set execute permission (Unix systems)
	if runtime.GOOS != "windows" {
		if err := os.Chmod(targetPath, 0755); err != nil {
			return fmt.Errorf("failed to set permissions: %v", err)
		}
	}

	fmt.Printf("Installed to: %s\n", targetPath)
	return nil
}

// copyFile Copy file from src to dst
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	if _, err := io.Copy(destFile, sourceFile); err != nil {
		return err
	}

	return destFile.Sync()
}

// GetLogFilePath Get log file path
func GetLogFilePath() (string, error) {
	agentDir, err := GetUserAgentDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(agentDir, "agent.log"), nil
}

// GetUpdateInfoPath Get update info file path
func GetUpdateInfoPath() (string, error) {
	agentDir, err := GetUserAgentDir()
	if err != nil {
		return "", err
	}

	return filepath.Join(agentDir, "update.json"), nil
}
