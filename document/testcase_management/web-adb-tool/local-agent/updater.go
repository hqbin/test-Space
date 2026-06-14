package main

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// UpdateInfo 更新信息
type UpdateInfo struct {
	LatestVersion string `json:"latest_version"`
	DownloadURL   string `json:"download_url"`
	Changelog     string `json:"changelog"`
	HasUpdate     bool   `json:"has_update"`
}

const (
	UpdateCheckURL = "http://172.16.60.161:2333/api/agent/latest-version.json"
)

// CheckForUpdates 检查更新
func CheckForUpdates() (*UpdateInfo, error) {
	// 发送请求到服务器
	resp, err := http.Get(UpdateCheckURL)
	if err != nil {
		return nil, fmt.Errorf("failed to check updates: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("server returned status: %d", resp.StatusCode)
	}

	// 解析响应
	var serverInfo struct {
		Version     string `json:"version"`
		DownloadURL string `json:"download_url"`
		Changelog   string `json:"changelog"`
	}

	if err := json.NewDecoder(resp.Body).Decode(&serverInfo); err != nil {
		return nil, fmt.Errorf("failed to decode response: %v", err)
	}

	// 比较版本
	hasUpdate := serverInfo.Version != AgentVersion

	return &UpdateInfo{
		LatestVersion: serverInfo.Version,
		DownloadURL:   serverInfo.DownloadURL,
		Changelog:     serverInfo.Changelog,
		HasUpdate:     hasUpdate,
	}, nil
}

// DownloadUpdate 下载更新
func DownloadUpdate(downloadURL string) (string, error) {
	// 创建临时文件
	agentDir, err := GetUserAgentDir()
	if err != nil {
		return "", err
	}

	tmpFile := filepath.Join(agentDir, "update.tmp")

	// 下载文件
	resp, err := http.Get(downloadURL)
	if err != nil {
		return "", fmt.Errorf("failed to download: %v", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("server returned status: %d", resp.StatusCode)
	}

	// 创建文件
	out, err := os.Create(tmpFile)
	if err != nil {
		return "", fmt.Errorf("failed to create file: %v", err)
	}
	defer out.Close()

	// 写入数据
	if _, err := io.Copy(out, resp.Body); err != nil {
		return "", fmt.Errorf("failed to write file: %v", err)
	}

	return tmpFile, nil
}

// saveUpdateInfo 保存更新信息
func saveUpdateInfo() error {
	updateInfoPath, err := GetUpdateInfoPath()
	if err != nil {
		return err
	}

	info := map[string]interface{}{
		"version":     AgentVersion,
		"update_time": time.Now().Format(time.RFC3339),
	}

	data, err := json.MarshalIndent(info, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(updateInfoPath, data, 0644)
}

// AutoCheckUpdates 自动检查更新（后台运行）
func AutoCheckUpdates() {
	// 首次启动时延迟1小时再检查，避免频繁检查
	time.Sleep(1 * time.Hour)
	
	// 立即检查一次
	performAutoUpdate()
	
	// 然后每24小时检查一次
	ticker := time.NewTicker(24 * time.Hour)
	defer ticker.Stop()

	for range ticker.C {
		performAutoUpdate()
	}
}

// performAutoUpdate 执行自动更新（静默）
func performAutoUpdate() {
	log.Println("Checking for updates...")
	
	updateInfo, err := CheckForUpdates()
	if err != nil {
		log.Printf("Failed to check for updates: %v", err)
		return
	}

	if !updateInfo.HasUpdate {
		log.Println("Agent is up to date")
		return
	}

	log.Printf("New version available: %s -> %s", AgentVersion, updateInfo.LatestVersion)
	log.Printf("Changelog: %s", updateInfo.Changelog)

	// 发现新版本，自动下载
	downloadURL := getFullDownloadURL(updateInfo.DownloadURL)
	log.Printf("Downloading update from: %s", downloadURL)
	
	updateFile, err := DownloadUpdate(downloadURL)
	if err != nil {
		log.Printf("Failed to download update: %v", err)
		return
	}
	
	log.Printf("Update downloaded to: %s", updateFile)

	// 应用更新
	log.Println("Applying update...")
	if err := ApplyUpdate(updateFile); err != nil {
		log.Printf("Failed to apply update: %v", err)
		// 清理下载的文件
		os.Remove(updateFile)
		return
	}

	// 更新成功，重启代理
	log.Println("Update applied successfully, restarting agent...")
	restartAgent()
}

// getFullDownloadURL 获取完整的下载URL
func getFullDownloadURL(relativeURL string) string {
	if strings.HasPrefix(relativeURL, "http://") || strings.HasPrefix(relativeURL, "https://") {
		return relativeURL
	}
	return "http://172.16.60.161:2333" + relativeURL
}

// restartAgent 重启代理
func restartAgent() {
	exePath, err := GetAgentExecutablePath()
	if err != nil {
		log.Printf("Failed to get executable path: %v", err)
		return
	}

	// 启动新进程
	cmd := exec.Command(exePath)
	
	// Windows 平台隐藏窗口
	if runtime.GOOS == "windows" {
		hideWindow(cmd)
	}
	
	if err := cmd.Start(); err != nil {
		log.Printf("Failed to start new agent: %v", err)
		return
	}

	log.Printf("New agent started successfully, exiting current process")
	
	// 等待一下确保新进程启动
	time.Sleep(500 * time.Millisecond)
	
	// 退出当前进程
	os.Exit(0)
}

// PerformUpdate 执行完整的更新流程
func PerformUpdate() error {
	fmt.Println("Checking for updates...")

	// 检查更新
	updateInfo, err := CheckForUpdates()
	if err != nil {
		return fmt.Errorf("failed to check updates: %v", err)
	}

	if !updateInfo.HasUpdate {
		fmt.Println("Already up to date")
		return nil
	}

	fmt.Printf("New version available: %s\n", updateInfo.LatestVersion)
	fmt.Printf("Changelog: %s\n", updateInfo.Changelog)

	// 下载更新
	fmt.Println("Downloading update...")
	updateFile, err := DownloadUpdate(updateInfo.DownloadURL)
	if err != nil {
		return fmt.Errorf("failed to download update: %v", err)
	}

	// 应用更新
	fmt.Println("Applying update...")
	if err := ApplyUpdate(updateFile); err != nil {
		return fmt.Errorf("failed to apply update: %v", err)
	}

	fmt.Println("Update completed successfully!")
	fmt.Println("Please restart the agent to use the new version")

	return nil
}
