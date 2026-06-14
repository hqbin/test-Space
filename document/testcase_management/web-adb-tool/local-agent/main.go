package main

import (
	"archive/zip"
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/gorilla/websocket"
)

// AdbCommand 表示 ADB 命令请求
type AdbCommand struct {
	Command string   `json:"command"`
	Args    []string `json:"args"`
}

// AdbResponse 表示 ADB 命令响应
type AdbResponse struct {
	Success bool   `json:"success"`
	Output  string `json:"output"`
	Error   string `json:"error"`
}

// Session 表示会话信息
type Session struct {
	ID        string
	DeviceID  string
	Type      string // "logcat", "recording", "boot_logcat"
	Cmd       *exec.Cmd
	StartTime time.Time
	FilePath  string
	Mode      string // for boot_logcat: "reboot" or "wait_connection"
	Connected bool   // for boot_logcat: device connection status
	Lines     []string // for boot_logcat: store log lines in memory
	MaxLines  int      // for boot_logcat: max lines to store
}

// 会话管理
var (
	sessions      = make(map[string]*Session)
	sessionsMutex sync.RWMutex
)

// WebSocket upgrader
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // 允许所有来源（开发环境）
	},
}

// 允许的来源（CORS）
var allowedOrigins = []string{
	"http://172.16.60.161:2333",
	"http://localhost:2333",
	"http://127.0.0.1:2333",
	"https://tms.zeasn.com",
	"http://tms.zeasn.com",
}

func main() {
	// 隐藏控制台窗口（避免终端显示）
	hideConsoleWindow()

	// 检查命令行参数
	if len(os.Args) > 1 {
		switch os.Args[1] {
		case "install":
			handleInstallCommand()
			return
		case "uninstall":
			handleUninstallCommand()
			return
		case "update":
			handleUpdateCommand()
			return
		case "version":
			fmt.Printf("%s v%s\n", AgentName, AgentVersion)
			return
		case "help":
			printHelp()
			return
		}
	}

	// 先检测并关闭旧版本进程（无论是否在用户目录）
	fmt.Println("正在检测旧版本代理...")
	if err := killOldAgentProcesses(); err != nil {
		fmt.Printf("警告: 关闭旧版本失败: %v\n", err)
		// 继续，不中断
	}

	// 检查是否在用户目录运行
	if !IsInstalledInUserDir() {
		fmt.Println("检测到从非用户目录运行，正在安装/更新到用户目录...")
		
		// 获取目标路径
		targetPath, err := GetAgentExecutablePath()
		if err != nil {
			fmt.Printf("错误: 无法获取目标路径: %v\n", err)
			fmt.Println("按任意键退出...")
			fmt.Scanln()
			os.Exit(1)
		}
		
		// 安装到用户目录（会覆盖旧文件）
		if err := InstallToUserDir(); err != nil {
			fmt.Printf("错误: 安装失败: %v\n", err)
			fmt.Println("按任意键退出...")
			fmt.Scanln()
			os.Exit(1)
		}
		
		fmt.Println("✓ 安装成功！")
		
		// 自动添加到启动项
		if !IsInStartup() {
			fmt.Println("正在添加到开机启动项...")
			if err := AddToStartup(); err != nil {
				fmt.Printf("警告: 添加到启动项失败: %v\n", err)
			} else {
				fmt.Println("✓ 已添加到开机启动项")
			}
		}
		
		// 启动新位置的程序
		fmt.Println("正在启动代理...")
		cmd := exec.Command(targetPath)
		hideWindow(cmd)
		if err := cmd.Start(); err != nil {
			fmt.Printf("错误: 启动失败: %v\n", err)
			fmt.Println("请手动运行: %s", targetPath)
			fmt.Println("按任意键退出...")
			fmt.Scanln()
			os.Exit(1)
		}
		
		fmt.Println("✓ 代理已启动！")
		fmt.Println("")
		fmt.Println("安装/更新完成！代理正在后台运行。")
		fmt.Println("您可以关闭此窗口，刷新浏览器页面开始使用。")
		fmt.Println("")
		fmt.Println("按任意键退出...")
		fmt.Scanln()
		
		// 退出当前进程
		os.Exit(0)
	}

	// 如果已经在用户目录运行，直接启动服务
	// 启动后台更新检查
	go AutoCheckUpdates()

	// 启动 HTTP 服务器
	startHTTPServer()
}

// startHTTPServer 启动 HTTP 服务器
func startHTTPServer() {
	// 设置路由
	http.HandleFunc("/health", handleHealth)
	http.HandleFunc("/adb", handleAdbCommand)
	http.HandleFunc("/shell", handleShellCommand)
	http.HandleFunc("/version", handleVersion)
	http.HandleFunc("/update/check", handleCheckUpdate)
	http.HandleFunc("/update/trigger", handleTriggerUpdate)
	http.HandleFunc("/upload", handleUpload)
	http.HandleFunc("/download", handleDownload)
	http.HandleFunc("/session/start", handleSessionStart)
	http.HandleFunc("/session/stop", handleSessionStop)
	http.HandleFunc("/session/status", handleSessionStatus)
	http.HandleFunc("/ws/mirror", handleScreenMirror)
	http.HandleFunc("/config/modify", handleModifyConfig)
	http.HandleFunc("/diagnostic/start", handleDiagnosticStart)
	http.HandleFunc("/diagnostic/stop", handleDiagnosticStop)
	http.HandleFunc("/boot-logcat/start", handleBootLogcatStart)
	http.HandleFunc("/boot-logcat/stop", handleBootLogcatStop)
	http.HandleFunc("/boot-logcat/status", handleBootLogcatStatus)
	http.HandleFunc("/shutdown", handleShutdown)

	// 启动服务器
	port := "9527"
	fmt.Printf("ADB Local Agent v%s starting on http://localhost:%s\n", AgentVersion, port)
	fmt.Println("Agent is running in background. Press Ctrl+C to stop.")

	if err := http.ListenAndServe("localhost:"+port, nil); err != nil {
		log.Fatal("Failed to start server:", err)
	}
}

// handleHealth 健康检查
func handleHealth(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)
	if r.Method == "OPTIONS" {
		return
	}
	w.WriteHeader(http.StatusOK)
	w.Write([]byte("OK"))
}

// handleVersion 返回版本信息
func handleVersion(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)
	if r.Method == "OPTIONS" {
		return
	}

	version := map[string]string{
		"version": AgentVersion,
		"name":    AgentName,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(version)
}

// handleShutdown 关闭代理程序
func handleShutdown(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)
	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 返回成功响应
	response := map[string]interface{}{
		"success": true,
		"message": "Agent is shutting down",
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)

	// 延迟关闭，确保响应已发送
	go func() {
		time.Sleep(500 * time.Millisecond)
		log.Println("Shutting down agent...")
		os.Exit(0)
	}()
}

// handleCheckUpdate 检查更新
func handleCheckUpdate(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)
	if r.Method == "OPTIONS" {
		return
	}

	// 检查更新
	updateInfo, err := CheckForUpdates()
	if err != nil {
		// 如果检查失败，返回"无更新"而不是错误
		// 这样前端可以正常工作，不会因为网络问题而中断
		updateInfo = &UpdateInfo{
			LatestVersion: AgentVersion,
			DownloadURL:   "",
			Changelog:     "",
			HasUpdate:     false,
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(updateInfo)
}

// handleTriggerUpdate 触发更新
func handleTriggerUpdate(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)
	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 在后台执行更新
	go func() {
		// 延迟 1 秒，让响应先返回
		time.Sleep(1 * time.Second)
		performAutoUpdate()
	}()

	// 立即返回成功响应
	response := map[string]interface{}{
		"success": true,
		"message": "Update triggered, agent will restart shortly",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleAdbCommand 处理 ADB 命令
func handleAdbCommand(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	// 处理 OPTIONS 预检请求
	if r.Method == "OPTIONS" {
		return
	}

	// 只接受 POST 请求
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析请求
	var cmd AdbCommand
	if err := json.NewDecoder(r.Body).Decode(&cmd); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	// 验证命令
	if err := validateCommand(cmd); err != nil {
		sendErrorResponse(w, "Invalid command", err)
		return
	}

	// 执行 ADB 命令
	output, err := executeAdbCommand(cmd.Args)

	// 返回结果
	response := AdbResponse{
		Success: err == nil,
		Output:  output,
		Error:   "",
	}

	if err != nil {
		response.Error = err.Error()
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleShellCommand 处理任意 shell 命令
func handleShellCommand(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	// 处理 OPTIONS 预检请求
	if r.Method == "OPTIONS" {
		return
	}

	// 只接受 POST 请求
	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析请求
	var req struct {
		Command string `json:"command"`
	}
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	if req.Command == "" {
		sendErrorResponse(w, "Command is required", fmt.Errorf("empty command"))
		return
	}

	// 执行 shell 命令
	var cmd *exec.Cmd
	if runtime.GOOS == "windows" {
		// Windows: 直接使用 CMD 执行命令，不切换编码
		// Go 会自动处理 GBK 到 UTF-8 的转换
		cmd = exec.Command("cmd", "/c", req.Command)
	} else {
		cmd = exec.Command("sh", "-c", req.Command)
	}

	// 隐藏控制台窗口（Windows 平台）
	hideWindow(cmd)

	output, err := cmd.CombinedOutput()

	// Windows 下需要将 GBK 编码转换为 UTF-8
	outputStr := string(output)
	if runtime.GOOS == "windows" {
		// 尝试将 GBK 转换为 UTF-8
		if utf8Str, convErr := decodeGBK(output); convErr == nil {
			outputStr = utf8Str
		}
	}

	// 返回结果
	response := AdbResponse{
		Success: err == nil,
		Output:  outputStr,
		Error:   "",
	}

	if err != nil {
		response.Error = err.Error()
		// 如果有输出，也包含在错误信息中
		if len(output) > 0 {
			response.Error = fmt.Sprintf("%s\nOutput: %s", err.Error(), outputStr)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleUpload 处理文件上传
func handleUpload(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析 multipart form
	err := r.ParseMultipartForm(500 << 20) // 500MB max
	if err != nil {
		sendErrorResponse(w, "Failed to parse form", err)
		return
	}

	// 获取设备 ID
	deviceID := r.FormValue("device_id")
	if deviceID == "" {
		sendErrorResponse(w, "device_id is required", fmt.Errorf("missing device_id"))
		return
	}

	// 获取文件
	file, header, err := r.FormFile("file")
	if err != nil {
		sendErrorResponse(w, "Failed to get file", err)
		return
	}
	defer file.Close()

	// 创建临时目录
	tempDir := filepath.Join(os.TempDir(), "adb-agent")
	os.MkdirAll(tempDir, 0755)

	// 保存文件
	tempFile := filepath.Join(tempDir, header.Filename)
	dst, err := os.Create(tempFile)
	if err != nil {
		sendErrorResponse(w, "Failed to create temp file", err)
		return
	}
	defer dst.Close()

	_, err = io.Copy(dst, file)
	if err != nil {
		sendErrorResponse(w, "Failed to save file", err)
		return
	}

	// 执行 adb install
	args := []string{"-s", deviceID, "install", "-r", tempFile}
	output, err := executeAdbCommand(args)

	// 清理临时文件
	os.Remove(tempFile)

	// 返回结果
	response := AdbResponse{
		Success: err == nil && strings.Contains(output, "Success"),
		Output:  output,
		Error:   "",
	}

	if err != nil {
		// 如果有错误，返回错误信息和输出
		response.Error = fmt.Sprintf("%v\n输出: %s", err, output)
	} else if !strings.Contains(output, "Success") {
		// 如果没有 Success 标记，说明安装失败
		response.Success = false
		// 返回完整的 ADB 输出作为错误信息
		if output != "" {
			response.Error = fmt.Sprintf("安装失败: %s", output)
		} else {
			response.Error = "安装失败: 未知错误"
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleDownload 处理文件下载
func handleDownload(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 获取参数
	deviceID := r.URL.Query().Get("device_id")
	remotePath := r.URL.Query().Get("remote_path")
	fileType := r.URL.Query().Get("type") // screenshot, recording, apk

	if deviceID == "" {
		http.Error(w, "device_id is required", http.StatusBadRequest)
		return
	}

	// 创建临时目录
	tempDir := filepath.Join(os.TempDir(), "adb-agent")
	os.MkdirAll(tempDir, 0755)

	var localPath string
	var filename string

	if fileType == "screenshot" {
		// 截图：直接从设备读取
		args := []string{"-s", deviceID, "exec-out", "screencap", "-p"}
		output, err := executeAdbCommandBytes(args)
		if err != nil {
			http.Error(w, fmt.Sprintf("Failed to capture screenshot: %v", err), http.StatusInternalServerError)
			return
		}

		// 直接返回截图数据
		w.Header().Set("Content-Type", "image/png")
		w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=screenshot_%d.png", time.Now().Unix()))
		w.Write(output)
		return
	} else if remotePath != "" {
		// 从设备拉取文件
		filename = filepath.Base(remotePath)
		localPath = filepath.Join(tempDir, filename)

		args := []string{"-s", deviceID, "pull", remotePath, localPath}
		_, err := executeAdbCommand(args)
		if err != nil {
			http.Error(w, fmt.Sprintf("Failed to pull file: %v", err), http.StatusInternalServerError)
			return
		}
	} else {
		http.Error(w, "remote_path or type is required", http.StatusBadRequest)
		return
	}

	// 读取文件
	data, err := os.ReadFile(localPath)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to read file: %v", err), http.StatusInternalServerError)
		return
	}

	// 清理临时文件
	defer os.Remove(localPath)

	// 返回文件
	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	w.Write(data)
}

// handleSessionStart 启动会话
func handleSessionStart(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析请求
	var req struct {
		DeviceID string `json:"device_id"`
		Type     string `json:"type"` // logcat, recording
		Filename string `json:"filename,omitempty"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	if req.DeviceID == "" || req.Type == "" {
		sendErrorResponse(w, "device_id and type are required", fmt.Errorf("missing parameters"))
		return
	}

	// 创建临时目录
	tempDir := filepath.Join(os.TempDir(), "adb-agent")
	os.MkdirAll(tempDir, 0755)

	// 生成会话 ID
	sessionID := fmt.Sprintf("%s_%s_%d", req.Type, req.DeviceID, time.Now().Unix())

	var cmd *exec.Cmd
	var filePath string

	switch req.Type {
	case "logcat":
		// 准备设备日志采集环境（adb root、设置缓冲区大小）
		setupDeviceForLogcat(req.DeviceID)

		// 启动 logcat
		filePath = filepath.Join(tempDir, fmt.Sprintf("logcat_%s_%d.txt", req.DeviceID, time.Now().Unix()))
		cmd = exec.Command("adb", "-s", req.DeviceID, "logcat")

		// 创建输出文件
		outFile, err := os.Create(filePath)
		if err != nil {
			sendErrorResponse(w, "Failed to create log file", err)
			return
		}
		cmd.Stdout = outFile
		cmd.Stderr = outFile

	case "recording":
		// 启动录屏（添加 --size 1280x720 参数）
		if req.Filename == "" {
			req.Filename = fmt.Sprintf("recording_%d.mp4", time.Now().Unix())
		}
		remotePath := fmt.Sprintf("/sdcard/%s", req.Filename)
		filePath = remotePath
		
		// 使用 --size 1280x720 参数，与桌面版保持一致
		cmd = exec.Command("adb", "-s", req.DeviceID, "shell", "screenrecord", "--size", "1280x720", remotePath)

	default:
		sendErrorResponse(w, "Invalid session type", fmt.Errorf("unknown type: %s", req.Type))
		return
	}

	// 隐藏窗口
	hideWindow(cmd)

	// 启动命令
	if err := cmd.Start(); err != nil {
		sendErrorResponse(w, "Failed to start session", err)
		return
	}

	// 保存会话
	session := &Session{
		ID:        sessionID,
		DeviceID:  req.DeviceID,
		Type:      req.Type,
		Cmd:       cmd,
		StartTime: time.Now(),
		FilePath:  filePath,
	}

	sessionsMutex.Lock()
	sessions[sessionID] = session
	sessionsMutex.Unlock()

	// 返回结果
	response := map[string]interface{}{
		"success":    true,
		"session_id": sessionID,
		"message":    fmt.Sprintf("%s session started", req.Type),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleSessionStop 停止会话
func handleSessionStop(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析请求
	var req struct {
		SessionID string `json:"session_id"`
	}

	bodyBytes, err := io.ReadAll(r.Body)
	if err != nil || len(bodyBytes) == 0 {
		sendErrorResponse(w, "Invalid request format", fmt.Errorf("request body is empty"))
		return
	}

	if err := json.Unmarshal(bodyBytes, &req); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	if req.SessionID == "" {
		sendErrorResponse(w, "Invalid request format", fmt.Errorf("session_id is required"))
		return
	}

	// 获取会话
	sessionsMutex.Lock()
	session, exists := sessions[req.SessionID]
	if !exists {
		sessionsMutex.Unlock()
		// 会话可能已经过期或不存在，尝试清理设备上的录屏进程
		deviceID := r.URL.Query().Get("device_id")
		if deviceID != "" {
			go func() {
				executeAdbCommand([]string{"-s", deviceID, "shell", "pkill", "-9", "screenrecord"})
			}()
		}
		sendErrorResponse(w, "Session not found", fmt.Errorf("session %s does not exist or has already been stopped", req.SessionID))
		return
	}
	delete(sessions, req.SessionID)
	sessionsMutex.Unlock()

	// 停止命令
	if session.Cmd != nil && session.Cmd.Process != nil {
		session.Cmd.Process.Kill()
		session.Cmd.Wait()
	}

	// 清理设备上可能卡住的 screenrecord 进程
	if session.Type == "recording" && session.DeviceID != "" {
		go func() {
			time.Sleep(500 * time.Millisecond)
			executeAdbCommand([]string{"-s", session.DeviceID, "shell", "pkill", "-9", "screenrecord"})
		}()
	}

	// 对于录屏，需要从设备拉取文件
	var fileData []byte
	var pullErr error

	if session.Type == "recording" {
		// 等待一下让文件写入完成
		time.Sleep(1 * time.Second)

		// 从设备拉取文件
		tempDir := filepath.Join(os.TempDir(), "adb-agent")
		localPath := filepath.Join(tempDir, filepath.Base(session.FilePath))

		args := []string{"-s", session.DeviceID, "pull", session.FilePath, localPath}
		_, pullErr = executeAdbCommand(args)
		if pullErr == nil {
			fileData, pullErr = os.ReadFile(localPath)
			os.Remove(localPath)
			
			// 删除设备上的文件
			executeAdbCommand([]string{"-s", session.DeviceID, "shell", "rm", session.FilePath})
		}
	} else if session.Type == "logcat" {
		// 读取 logcat 文件
		fileData, pullErr = os.ReadFile(session.FilePath)
		os.Remove(session.FilePath)
	}

	if pullErr != nil {
		http.Error(w, fmt.Sprintf("Failed to get session file: %v", pullErr), http.StatusInternalServerError)
		return
	}

	// 返回文件
	filename := filepath.Base(session.FilePath)
	if session.Type == "recording" {
		filename = fmt.Sprintf("recording_%s_%d.mp4", session.DeviceID, session.StartTime.Unix())
	} else if session.Type == "logcat" {
		filename = fmt.Sprintf("logcat_%s_%d.txt", session.DeviceID, session.StartTime.Unix())
	}

	w.Header().Set("Content-Type", "application/octet-stream")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	w.Write(fileData)
}

// handleSessionStatus 查询会话状态
func handleSessionStatus(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		http.Error(w, "session_id is required", http.StatusBadRequest)
		return
	}

	// 获取会话
	sessionsMutex.RLock()
	session, exists := sessions[sessionID]
	sessionsMutex.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	// 检查进程状态
	running := false
	if session.Cmd != nil && session.Cmd.Process != nil {
		// 尝试发送信号 0 来检查进程是否存在
		err := session.Cmd.Process.Signal(os.Signal(nil))
		running = err == nil
	}

	response := map[string]interface{}{
		"success":    true,
		"session_id": session.ID,
		"device_id":  session.DeviceID,
		"type":       session.Type,
		"running":    running,
		"start_time": session.StartTime.Format(time.RFC3339),
		"duration":   time.Since(session.StartTime).Seconds(),
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleScreenMirror 处理屏幕镜像 WebSocket
func handleScreenMirror(w http.ResponseWriter, r *http.Request) {
	// 升级到 WebSocket
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("Failed to upgrade to WebSocket: %v", err)
		return
	}
	defer conn.Close()

	// 获取设备 ID
	deviceID := r.URL.Query().Get("device_id")
	if deviceID == "" {
		conn.WriteMessage(websocket.TextMessage, []byte(`{"error":"device_id is required"}`))
		return
	}

	// 获取帧率参数（默认 10 FPS）
	frameRate := 10
	if fpsStr := r.URL.Query().Get("fps"); fpsStr != "" {
		if fps, err := strconv.Atoi(fpsStr); err == nil && fps >= 1 && fps <= 30 {
			frameRate = fps
		}
	}

	// 获取最大分辨率参数（默认 1280）
	maxSize := 1280
	if sizeStr := r.URL.Query().Get("max_size"); sizeStr != "" {
		if size, err := strconv.Atoi(sizeStr); err == nil && size >= 480 && size <= 3840 {
			maxSize = size
		}
	}

	log.Printf("Screen mirror started for device: %s (FPS: %d, MaxSize: %d)", deviceID, frameRate, maxSize)

	// 计算帧间隔
	frameInterval := time.Duration(1000/frameRate) * time.Millisecond
	ticker := time.NewTicker(frameInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			// 截取屏幕
			args := []string{"-s", deviceID, "exec-out", "screencap", "-p"}
			
			output, err := executeAdbCommandBytes(args)
			if err != nil {
				log.Printf("Failed to capture screen: %v", err)
				continue
			}

			// 发送帧数据
			err = conn.WriteMessage(websocket.BinaryMessage, output)
			if err != nil {
				log.Printf("Failed to send frame: %v", err)
				return
			}
		}
	}
}

// setCORSHeaders 设置 CORS 头
func setCORSHeaders(w http.ResponseWriter, r *http.Request) {
	origin := r.Header.Get("Origin")

	// 检查来源是否允许
	allowed := false
	for _, allowedOrigin := range allowedOrigins {
		if origin == allowedOrigin {
			allowed = true
			break
		}
	}

	if allowed {
		w.Header().Set("Access-Control-Allow-Origin", origin)
	} else {
		// 默认允许所有本地来源（开发环境）
		w.Header().Set("Access-Control-Allow-Origin", "*")
	}

	w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
	w.Header().Set("Access-Control-Allow-Private-Network", "true")
}

// validateCommand 验证命令安全性
func validateCommand(cmd AdbCommand) error {
	// 检查命令是否为 adb
	if cmd.Command != "" && cmd.Command != "adb" {
		return fmt.Errorf("only adb commands are allowed")
	}

	// 检查参数
	for _, arg := range cmd.Args {
		// 防止路径遍历
		if strings.Contains(arg, "..") {
			return fmt.Errorf("invalid argument: path traversal detected")
		}

		// 注意：不再检查 shell 命令中的特殊字符（;|&）
		// 因为这些字符在 adb shell 命令中是合法的
		// ADB 本身会处理这些命令的安全性
	}

	return nil
}

// executeAdbCommand 执行 ADB 命令（返回字符串）
func executeAdbCommand(args []string) (string, error) {
	// 检查 ADB 是否可用
	if _, err := exec.LookPath("adb"); err != nil {
		return "", fmt.Errorf("ADB not found in PATH")
	}

	// 执行命令
	cmd := exec.Command("adb", args...)

	// 隐藏控制台窗口（Windows 平台）
	hideWindow(cmd)

	output, err := cmd.CombinedOutput()

	return string(output), err
}

// executeAdbCommandBytes 执行 ADB 命令（返回字节）
func executeAdbCommandBytes(args []string) ([]byte, error) {
	// 检查 ADB 是否可用
	if _, err := exec.LookPath("adb"); err != nil {
		return nil, fmt.Errorf("ADB not found in PATH")
	}

	// 执行命令
	cmd := exec.Command("adb", args...)

	// 隐藏控制台窗口（Windows 平台）
	hideWindow(cmd)

	output, err := cmd.CombinedOutput()

	return output, err
}

// executeAdbCommandWithTimeout 执行 ADB 命令（带超时）
func executeAdbCommandWithTimeout(timeout time.Duration, args []string) (string, error) {
	if _, err := exec.LookPath("adb"); err != nil {
		return "", fmt.Errorf("ADB not found in PATH")
	}

	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()

	cmd := exec.CommandContext(ctx, "adb", args...)
	hideWindow(cmd)

	output, err := cmd.CombinedOutput()
	if err != nil && ctx.Err() == context.DeadlineExceeded {
		return string(output), fmt.Errorf("adb command timed out after %v: adb %v", timeout, args)
	}
	return string(output), err
}

// setupDeviceForLogcat 准备设备日志采集环境
// 1. adb root（确保有权限访问所有日志缓冲区）
// 2. 等待 root 完成后设备重连
// 3. 设置 logcat 缓冲区大小为 16M
func setupDeviceForLogcat(deviceID string) {
	// 1. 提升 adbd 权限（带 10 秒超时）
	executeAdbCommandWithTimeout(10*time.Second, []string{"-s", deviceID, "root"})

	// 2. 等待 adbd 重启后设备重新就绪，最多等 15 秒
	for i := 0; i < 15; i++ {
		time.Sleep(1 * time.Second)
		output, err := executeAdbCommandWithTimeout(5*time.Second, []string{"-s", deviceID, "get-state"})
		if err == nil && strings.TrimSpace(output) == "device" {
			break
		}
	}

	// 3. 设置 logcat 缓冲区大小为 16M 并验证（各 5 秒超时）
	executeAdbCommandWithTimeout(5*time.Second, []string{"-s", deviceID, "logcat", "-G", "16M"})
	executeAdbCommandWithTimeout(5*time.Second, []string{"-s", deviceID, "logcat", "-g"})
}

// sendErrorResponse 发送错误响应
func sendErrorResponse(w http.ResponseWriter, message string, err error) {
	response := AdbResponse{
		Success: false,
		Output:  "",
		Error:   fmt.Sprintf("%s: %v", message, err),
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusBadRequest)
	json.NewEncoder(w).Encode(response)
}

// addToStartup 添加程序到开机启动项
func addToStartup() error {
	// 获取用户目录下的目标路径（不是当前进程路径）
	exePath, err := GetAgentExecutablePath()
	if err != nil {
		return err
	}
	exePath, err = filepath.Abs(exePath)
	if err != nil {
		return err
	}

	// 根据操作系统添加启动项
	switch runtime.GOOS {
	case "windows":
		return addToWindowsStartup(exePath)
	case "darwin":
		return addToMacStartup(exePath)
	default:
		return fmt.Errorf("unsupported operating system: %s", runtime.GOOS)
	}
}

// addToWindowsStartup 添加到 Windows 启动项
func addToWindowsStartup(exePath string) error {
	// 使用注册表添加启动项
	appName := "ADBLocalAgent"

	// 检查是否已经添加
	checkCmd := exec.Command("reg", "query",
		`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`,
		"/v", appName)
	hideWindow(checkCmd)
	if err := checkCmd.Run(); err == nil {
		// 已经存在，无需重复添加
		return nil
	}

	// 添加到注册表
	cmd := exec.Command("reg", "add",
		`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`,
		"/v", appName,
		"/t", "REG_SZ",
		"/d", exePath,
		"/f")
	hideWindow(cmd)

	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to add to Windows startup: %v", err)
	}

	log.Println("Successfully added to Windows startup")
	return nil
}

// addToMacStartup 添加到 Mac 启动项
func addToMacStartup(exePath string) error {
	// Mac 使用 LaunchAgent
	homeDir, err := os.UserHomeDir()
	if err != nil {
		return err
	}

	launchAgentDir := filepath.Join(homeDir, "Library", "LaunchAgents")
	plistPath := filepath.Join(launchAgentDir, "com.adbwebtool.agent.plist")

	// 检查是否已经存在
	if _, err := os.Stat(plistPath); err == nil {
		return nil // 已存在
	}

	// 创建目录
	if err := os.MkdirAll(launchAgentDir, 0755); err != nil {
		return err
	}

	// 创建 plist 文件
	plistContent := fmt.Sprintf(`<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.adbwebtool.agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>%s</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>`, exePath)

	if err := os.WriteFile(plistPath, []byte(plistContent), 0644); err != nil {
		return err
	}

	// 加载 LaunchAgent
	cmd := exec.Command("launchctl", "load", plistPath)
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("failed to load LaunchAgent: %v", err)
	}

	log.Println("Successfully added to Mac startup")
	return nil
}


// handleInstallCommand 处理安装命令
func handleInstallCommand() {
	fmt.Println("Installing ADB Local Agent...")

	// 安装到用户目录
	if err := InstallToUserDir(); err != nil {
		fmt.Printf("Error: Failed to install: %v\n", err)
		os.Exit(1)
	}

	// 添加到启动项
	if err := AddToStartup(); err != nil {
		fmt.Printf("Warning: Failed to add to startup: %v\n", err)
	}

	fmt.Println("Installation completed successfully!")
	fmt.Println("The agent will start automatically on next boot.")
}

// handleUninstallCommand 处理卸载命令
func handleUninstallCommand() {
	fmt.Println("Uninstalling ADB Local Agent...")

	// 从启动项移除
	if err := RemoveFromStartup(); err != nil {
		fmt.Printf("Warning: Failed to remove from startup: %v\n", err)
	}

	// 获取安装目录
	agentDir, err := GetUserAgentDir()
	if err != nil {
		fmt.Printf("Error: Failed to get agent directory: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Agent directory: %s\n", agentDir)
	fmt.Println("Please manually delete the directory if needed.")
	fmt.Println("Uninstallation completed!")
}

// handleUpdateCommand 处理更新命令
func handleUpdateCommand() {
	if err := PerformUpdate(); err != nil {
		fmt.Printf("Error: %v\n", err)
		os.Exit(1)
	}
}

// printHelp 打印帮助信息
func printHelp() {
	fmt.Printf("%s v%s\n\n", AgentName, AgentVersion)
	fmt.Println("Usage:")
	fmt.Println("  adb-agent              Start the agent with system tray")
	fmt.Println("  adb-agent install      Install to user directory and add to startup")
	fmt.Println("  adb-agent uninstall    Remove from startup")
	fmt.Println("  adb-agent update       Check and apply updates")
	fmt.Println("  adb-agent version      Show version information")
	fmt.Println("  adb-agent help         Show this help message")
}

// ModifyConfigRequest 修改配置请求
type ModifyConfigRequest struct {
	DeviceID    string `json:"device_id"`
	ConfigPath  string `json:"config_path"`
	ConfigKey   string `json:"config_key"`
	ConfigValue string `json:"config_value"`
}

// ModifyConfigResponse 修改配置响应
type ModifyConfigResponse struct {
	Success    bool   `json:"success"`
	Output     string `json:"output"`
	Error      string `json:"error"`
	ConfigPath string `json:"config_path,omitempty"`
}

// handleModifyConfig 处理修改配置请求
func handleModifyConfig(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)
	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析请求
	var req ModifyConfigRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request", err)
		return
	}

	// 验证必填字段
	if req.DeviceID == "" || req.ConfigKey == "" || req.ConfigValue == "" {
		sendErrorResponse(w, "Missing required fields", fmt.Errorf("device_id, config_key, and config_value are required"))
		return
	}

	// 如果没有指定配置路径，自动查找
	configPath := req.ConfigPath
	if configPath == "" {
		log.Printf("No config path specified, searching for config file containing key: %s", req.ConfigKey)
		foundPath, err := findConfigFile(req.DeviceID, req.ConfigKey)
		if err != nil {
			response := ModifyConfigResponse{
				Success: false,
				Error:   fmt.Sprintf("未找到包含该配置key的配置文件: %v", err),
			}
			w.Header().Set("Content-Type", "application/json")
			json.NewEncoder(w).Encode(response)
			return
		}
		configPath = foundPath
		log.Printf("Found config file: %s", configPath)
	}

	// 执行修改操作
	success, message, err := modifyDeviceConfig(req.DeviceID, configPath, req.ConfigKey, req.ConfigValue)

	response := ModifyConfigResponse{
		Success:    success,
		ConfigPath: configPath,
	}

	if success {
		response.Output = message
	} else {
		response.Error = message
		if err != nil {
			response.Error = fmt.Sprintf("%s: %v", message, err)
		}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// findConfigFile 自动查找包含指定 key 的配置文件
func findConfigFile(deviceID, configKey string) (string, error) {
	// 常见配置文件路径列表
	commonPaths := []string{
		"/system/build.prop",
		"/system/product/build.prop",
		"/system_ext/build.prop",
		"/vendor/build.prop",
		"/odm/build.prop",
		"/vendor/etc/build.prop",
		"system/vendor/build.prop",
		"/system/etc/prop.default",
		"vendor/tvconfig/cvte.prop",
		"/hotackoem/build.prop",
		"/smarttv/smarttv.json",
		"mnt/vendor/odm_ext/etc/tvconfig/stmbuild.prop",
		"/vendor/ctvbuild.prop",
		"/mnt/vendor/odm_ext/ctvbuild.prop",
		"/vendor/tvconfig/cultraview/ctvbuild.prop",
	}

	// 搜索常见配置文件路径
	for _, path := range commonPaths {
		// 检查文件是否存在
		checkCmd := []string{"-s", deviceID, "shell", "ls", path}
		if _, err := executeAdbCommand(checkCmd); err == nil {
			// 文件存在，检查是否包含该 key
			grepCmd := []string{"-s", deviceID, "shell", "grep", configKey, path}
			output, err := executeAdbCommand(grepCmd)
			if err == nil && strings.Contains(output, configKey) {
				return path, nil
			}
		}
	}

	return "", fmt.Errorf("未找到包含 key '%s' 的配置文件", configKey)
}

// modifyDeviceConfig 修改设备配置
// 实现逻辑：Pull → 修改 → Push
func modifyDeviceConfig(deviceID, configPath, configKey, configValue string) (bool, string, error) {
	// 创建临时文件
	tempFile, err := os.CreateTemp("", "config_*.tmp")
	if err != nil {
		return false, "创建临时文件失败", err
	}
	tempFilePath := tempFile.Name()
	tempFile.Close()
	defer os.Remove(tempFilePath)

	// 1. Pull 配置文件到本地
	log.Printf("Pulling config file from device: %s", configPath)
	pullCmd := []string{"-s", deviceID, "pull", configPath, tempFilePath}
	if _, err := executeAdbCommand(pullCmd); err != nil {
		return false, "拉取配置文件失败", err
	}

	// 2. 修改配置文件
	log.Printf("Modifying config file: key=%s, value=%s", configKey, configValue)
	
	// 检查是否是 JSON 格式
	isJSON := strings.HasSuffix(configPath, ".json")
	
	if isJSON {
		// 处理 JSON 格式
		if err := modifyJSONConfig(tempFilePath, configKey, configValue); err != nil {
			return false, "修改JSON配置文件失败", err
		}
	} else {
		// 处理普通文本格式
		if err := modifyTextConfig(tempFilePath, configKey, configValue); err != nil {
			return false, "修改配置文件失败", err
		}
	}

	// 3. Push 修改后的文件回设备
	log.Printf("Pushing modified config file back to device: %s", configPath)
	pushCmd := []string{"-s", deviceID, "push", tempFilePath, configPath}
	if _, err := executeAdbCommand(pushCmd); err != nil {
		return false, "推送配置文件失败，请确认设备是否remount", err
	}

	// 返回 JSON 格式的成功消息，供前端解析
	resultData := map[string]string{
		"config_path":  configPath,
		"config_key":   configKey,
		"config_value": configValue,
	}
	resultJSON, _ := json.Marshal(resultData)
	
	log.Printf("成功修改设备配置表：%s，key：%s，值：%s", configPath, configKey, configValue)
	return true, string(resultJSON), nil
}

// modifyJSONConfig 修改 JSON 格式的配置文件
func modifyJSONConfig(filePath, configKey, configValue string) error {
	// 读取 JSON 文件
	data, err := os.ReadFile(filePath)
	if err != nil {
		return err
	}

	// 解析 JSON
	var config map[string]interface{}
	if err := json.Unmarshal(data, &config); err != nil {
		return fmt.Errorf("解析JSON文件失败: %v", err)
	}

	// 支持嵌套的 key，例如："system.version"
	keys := strings.Split(configKey, ".")
	current := config

	// 遍历 key 的各个部分
	for i, keyPart := range keys {
		if i == len(keys)-1 {
			// 最后一个 key，修改值
			current[keyPart] = configValue
		} else {
			// 不是最后一个 key，继续遍历
			if _, ok := current[keyPart]; !ok {
				// 如果中间 key 不存在，创建一个新的 map
				current[keyPart] = make(map[string]interface{})
			}
			// 类型断言
			if nextMap, ok := current[keyPart].(map[string]interface{}); ok {
				current = nextMap
			} else {
				return fmt.Errorf("key路径 '%s' 不是一个对象", keyPart)
			}
		}
	}

	// 写回 JSON 文件
	newData, err := json.MarshalIndent(config, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(filePath, newData, 0644)
}

// modifyTextConfig 修改普通文本格式的配置文件
func modifyTextConfig(filePath, configKey, configValue string) error {
	// 读取文件内容
	data, err := os.ReadFile(filePath)
	if err != nil {
		return err
	}

	lines := strings.Split(string(data), "\n")
	modified := false
	var newLines []string

	// 遍历每一行
	for _, line := range lines {
		// 查找包含 key 的行
		if strings.Contains(line, configKey) && strings.Contains(line, "=") {
			// 检查是否是精确匹配（key 在等号左边）
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 && strings.TrimSpace(parts[0]) == configKey {
				// 替换值
				newLines = append(newLines, fmt.Sprintf("%s=%s", configKey, configValue))
				modified = true
				continue
			}
		}
		newLines = append(newLines, line)
	}

	// 如果没有找到 key，添加新行
	if !modified {
		log.Printf("Key '%s' not found in config file, adding new line", configKey)
		newLines = append(newLines, fmt.Sprintf("%s=%s", configKey, configValue))
	}

	// 写回文件
	newContent := strings.Join(newLines, "\n")
	return os.WriteFile(filePath, []byte(newContent), 0644)
}


// DiagnosticSession 诊断日志会话
type DiagnosticSession struct {
	ID        string
	DeviceID  string
	StartTime time.Time
	TempDir   string
	LogcatCmd *exec.Cmd
	LogcatFile *os.File
}

// killOldAgentProcesses 检测并关闭旧版本的代理进程
func killOldAgentProcesses() error {
	currentPID := os.Getpid()
	
	// 获取进程列表并查找同名进程
	killed := false
	
	if runtime.GOOS == "windows" {
		// Windows: 使用 tasklist 获取所有进程，然后过滤
		cmd := exec.Command("tasklist", "/FO", "CSV", "/NH")
		hideWindow(cmd)
		output, err := cmd.Output()
		if err != nil {
			return fmt.Errorf("无法获取进程列表: %v", err)
		}
		
		// 解析输出，查找 adb-agent 相关进程
		lines := strings.Split(string(output), "\n")
		for _, line := range lines {
			if line == "" {
				continue
			}
			
			// 检查是否是 adb-agent 进程
			if !strings.Contains(strings.ToLower(line), "adb-agent") {
				continue
			}
			
			// CSV 格式: "进程名","PID","会话名","会话#","内存使用"
			fields := strings.Split(line, ",")
			if len(fields) < 2 {
				continue
			}
			
			// 提取进程名和 PID
			processName := strings.Trim(fields[0], "\" ")
			pidStr := strings.Trim(fields[1], "\" ")
			pid, err := strconv.Atoi(pidStr)
			if err != nil {
				continue
			}
			
			// 跳过当前进程
			if pid == currentPID {
				continue
			}
			
			// 关闭进程
			fmt.Printf("发现旧版本代理进程: %s (PID: %d)，正在关闭...\n", processName, pid)
			killCmd := exec.Command("taskkill", "/F", "/PID", strconv.Itoa(pid))
			hideWindow(killCmd)
			if err := killCmd.Run(); err != nil {
				fmt.Printf("警告: 无法关闭进程 %d: %v\n", pid, err)
			} else {
				fmt.Printf("✓ 已关闭进程 %d\n", pid)
				killed = true
			}
		}
	} else {
		// macOS/Linux: 使用 pgrep 查找进程
		cmd := exec.Command("pgrep", "-f", "adb-agent")
		output, err := cmd.Output()
		if err != nil {
			// pgrep 没有找到进程时会返回错误，这是正常的
			return nil
		}
		
		// 解析 PID 列表
		lines := strings.Split(strings.TrimSpace(string(output)), "\n")
		for _, line := range lines {
			if line == "" {
				continue
			}
			
			pid, err := strconv.Atoi(line)
			if err != nil {
				continue
			}
			
			// 跳过当前进程
			if pid == currentPID {
				continue
			}
			
			// 关闭进程
			fmt.Printf("发现旧版本代理进程 (PID: %d)，正在关闭...\n", pid)
			killCmd := exec.Command("kill", "-9", strconv.Itoa(pid))
			if err := killCmd.Run(); err != nil {
				fmt.Printf("警告: 无法关闭进程 %d: %v\n", pid, err)
			} else {
				fmt.Printf("✓ 已关闭进程 %d\n", pid)
				killed = true
			}
		}
	}
	
	// 如果关闭了进程，等待一下确保端口释放
	if killed {
		fmt.Println("等待端口释放...")
		time.Sleep(2 * time.Second)
		fmt.Println("✓ 已关闭旧版本代理")
	}
	
	return nil
}

var (
	diagnosticSessions  = make(map[string]*DiagnosticSession)
	diagnosticMutex     sync.Mutex
)

// handleDiagnosticStart 启动完整诊断日志采集
func handleDiagnosticStart(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		DeviceID string `json:"device_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	if req.DeviceID == "" {
		sendErrorResponse(w, "device_id is required", fmt.Errorf("missing device_id"))
		return
	}

	// 创建临时目录
	tempDir := filepath.Join(os.TempDir(), "adb-agent", fmt.Sprintf("diagnostic_%s_%d", req.DeviceID, time.Now().Unix()))
	if err := os.MkdirAll(tempDir, 0755); err != nil {
		sendErrorResponse(w, "Failed to create temp directory", err)
		return
	}

	// 生成会话 ID
	sessionID := fmt.Sprintf("diagnostic_%s_%d", req.DeviceID, time.Now().Unix())

	// 准备设备日志采集环境（adb root、设置缓冲区大小）
	setupDeviceForLogcat(req.DeviceID)

	// 启动 logcat 采集
	logcatPath := filepath.Join(tempDir, "logcat.txt")
	logcatFile, err := os.Create(logcatPath)
	if err != nil {
		sendErrorResponse(w, "Failed to create logcat file", err)
		return
	}

	cmd := exec.Command("adb", "-s", req.DeviceID, "logcat", "-v", "time")
	cmd.Stdout = logcatFile
	cmd.Stderr = logcatFile
	hideWindow(cmd)

	if err := cmd.Start(); err != nil {
		logcatFile.Close()
		sendErrorResponse(w, "Failed to start logcat", err)
		return
	}

	// 保存会话
	session := &DiagnosticSession{
		ID:         sessionID,
		DeviceID:   req.DeviceID,
		StartTime:  time.Now(),
		TempDir:    tempDir,
		LogcatCmd:  cmd,
		LogcatFile: logcatFile,
	}

	diagnosticMutex.Lock()
	diagnosticSessions[sessionID] = session
	diagnosticMutex.Unlock()

	response := map[string]interface{}{
		"success":    true,
		"session_id": sessionID,
		"device_id":  req.DeviceID,
		"message":    "Diagnostic log capture started",
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleDiagnosticStop 停止完整诊断日志采集并打包
func handleDiagnosticStop(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		SessionID string `json:"session_id"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	diagnosticMutex.Lock()
	session, exists := diagnosticSessions[req.SessionID]
	if !exists {
		diagnosticMutex.Unlock()
		sendErrorResponse(w, "Session not found", fmt.Errorf("invalid session_id"))
		return
	}
	delete(diagnosticSessions, req.SessionID)
	diagnosticMutex.Unlock()

	// 停止 logcat
	if session.LogcatCmd != nil && session.LogcatCmd.Process != nil {
		session.LogcatCmd.Process.Kill()
		session.LogcatCmd.Wait()
	}
	if session.LogcatFile != nil {
		session.LogcatFile.Close()
	}

	// 采集额外信息
	captureAdditionalLogs(session.DeviceID, session.TempDir)

	// 打包成 zip
	zipPath := session.TempDir + ".zip"
	if err := zipDirectory(session.TempDir, zipPath); err != nil {
		http.Error(w, fmt.Sprintf("Failed to create zip: %v", err), http.StatusInternalServerError)
		return
	}

	// 读取 zip 文件
	zipData, err := os.ReadFile(zipPath)
	if err != nil {
		http.Error(w, fmt.Sprintf("Failed to read zip: %v", err), http.StatusInternalServerError)
		return
	}

	// 清理临时文件
	os.RemoveAll(session.TempDir)
	os.Remove(zipPath)

	// 返回 zip 文件
	filename := fmt.Sprintf("diagnostic_%s_%d.zip", session.DeviceID, session.StartTime.Unix())
	w.Header().Set("Content-Type", "application/zip")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	w.Write(zipData)
}

// captureAdditionalLogs 采集额外的日志信息
func captureAdditionalLogs(deviceID, baseDir string) {
	// getprop
	adbOutputToFile(deviceID, []string{"shell", "getprop"}, filepath.Join(baseDir, "getprop.txt"))
	
	// uptime
	adbOutputToFile(deviceID, []string{"shell", "uptime"}, filepath.Join(baseDir, "uptime.txt"))
	
	// free
	adbOutputToFile(deviceID, []string{"shell", "free", "-m"}, filepath.Join(baseDir, "free.txt"))
	
	// df
	adbOutputToFile(deviceID, []string{"shell", "df", "-h"}, filepath.Join(baseDir, "df.txt"))
	
	// dumpsys services
	services := []string{"package", "SurfaceFlinger", "power", "activity", "input", "window", "settings"}
	for _, service := range services {
		adbOutputToFile(deviceID, []string{"shell", "dumpsys", service}, filepath.Join(baseDir, fmt.Sprintf("dumpsys_%s.txt", service)))
	}
	
	// dmesg
	adbOutputToFile(deviceID, []string{"shell", "dmesg"}, filepath.Join(baseDir, "dmesg.txt"))
	
	// ps
	adbOutputToFile(deviceID, []string{"shell", "ps"}, filepath.Join(baseDir, "ps.txt"))
}

// adbOutputToFile 执行 ADB 命令并将输出保存到文件
func adbOutputToFile(deviceID string, args []string, outPath string) {
	fullArgs := append([]string{"-s", deviceID}, args...)
	output, err := executeAdbCommand(fullArgs)
	if err != nil {
		output = fmt.Sprintf("Error: %v", err)
	}
	os.WriteFile(outPath, []byte(output), 0644)
}

// zipDirectory 将目录打包成 zip 文件
func zipDirectory(sourceDir, zipPath string) error {
	zipFile, err := os.Create(zipPath)
	if err != nil {
		return err
	}
	defer zipFile.Close()

	archive := zip.NewWriter(zipFile)
	defer archive.Close()

	return filepath.Walk(sourceDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		relPath, err := filepath.Rel(sourceDir, path)
		if err != nil {
			return err
		}

		writer, err := archive.Create(relPath)
		if err != nil {
			return err
		}

		file, err := os.Open(path)
		if err != nil {
			return err
		}
		defer file.Close()

		_, err = io.Copy(writer, file)
		return err
	})
}

// handleBootLogcatStart 启动开机日志抓取
func handleBootLogcatStart(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req struct {
		DeviceID string `json:"device_id"` // 可选，为空表示等待连接模式
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		sendErrorResponse(w, "Invalid request format", err)
		return
	}

	// 生成会话 ID
	sessionID := fmt.Sprintf("boot_logcat_%d", time.Now().Unix())

	var mode string
	var message string
	var deviceID string

	if req.DeviceID != "" {
		// 模式 1: 设备已连接，自动重启并等待连接
		mode = "reboot"
		deviceID = req.DeviceID
		message = "Rebooting device and waiting for reconnection..."

		// 清空日志缓冲区
		clearCmd := []string{"-s", deviceID, "logcat", "-c"}
		if _, err := executeAdbCommand(clearCmd); err != nil {
			sendErrorResponse(w, "Failed to clear logcat buffer", err)
			return
		}

		// 创建会话（初始状态为未连接）
		session := &Session{
			ID:        sessionID,
			DeviceID:  deviceID,
			Type:      "boot_logcat",
			Mode:      mode,
			StartTime: time.Now(),
			Connected: false, // 等待重启后重新连接
			Lines:     make([]string, 0),
			MaxLines:  100000,
		}

		// 保存会话
		sessionsMutex.Lock()
		sessions[sessionID] = session
		sessionsMutex.Unlock()

		// 重启设备
		rebootCmd := []string{"-s", deviceID, "reboot"}
		go executeAdbCommand(rebootCmd) // 异步执行，不等待结果

		// 后台等待设备重新连接
		go func() {
			// 等待 5 秒让设备开始重启
			time.Sleep(5 * time.Second)

			ticker := time.NewTicker(1 * time.Second)
			defer ticker.Stop()

			for range ticker.C {
				sessionsMutex.RLock()
				sess, exists := sessions[sessionID]
				sessionsMutex.RUnlock()

				if !exists {
					// 会话已删除，停止轮询
					return
				}

				if sess.Connected {
					// 已连接，停止轮询
					return
				}

				// 检查设备是否重新连接
				checkCmd := []string{"-s", deviceID, "get-state"}
				output, err := executeAdbCommand(checkCmd)
				if err == nil && strings.TrimSpace(output) == "device" {
					// 设备已重新连接，准备日志采集环境（adb root、设置缓冲区大小）
					setupDeviceForLogcat(deviceID)

					// 启动 logcat
					cmd := exec.Command("adb", "-s", deviceID, "logcat", "-b", "all", "-v", "time")
					hideWindow(cmd)

					stdout, err := cmd.StdoutPipe()
					if err != nil {
						sessionsMutex.Lock()
						sess.Connected = true
						sessionsMutex.Unlock()
						return
					}

					if err := cmd.Start(); err != nil {
						sessionsMutex.Lock()
						sess.Connected = true
						sessionsMutex.Unlock()
						return
					}

					// 更新会话
					sessionsMutex.Lock()
					sess.Connected = true
					sess.Cmd = cmd
					sessionsMutex.Unlock()

					// 后台读取日志
					go func() {
						scanner := bufio.NewScanner(stdout)
						for scanner.Scan() {
							line := scanner.Text()
							sessionsMutex.Lock()
							if len(sess.Lines) >= sess.MaxLines {
								sess.Lines = sess.Lines[1:]
							}
							sess.Lines = append(sess.Lines, line)
							sessionsMutex.Unlock()
						}
					}()

					return
				}
			}
		}()

	} else {
		// 模式 2: 等待连接模式
		mode = "wait_connection"
		message = "Waiting for device connection..."

		// 创建会话
		session := &Session{
			ID:        sessionID,
			DeviceID:  "",
			Type:      "boot_logcat",
			Mode:      mode,
			StartTime: time.Now(),
			Connected: false,
			Lines:     make([]string, 0),
			MaxLines:  100000,
		}

		// 保存会话
		sessionsMutex.Lock()
		sessions[sessionID] = session
		sessionsMutex.Unlock()

		// 后台轮询设备
		go func() {
			ticker := time.NewTicker(1 * time.Second)
			defer ticker.Stop()

			for range ticker.C {
				sessionsMutex.RLock()
				sess, exists := sessions[sessionID]
				sessionsMutex.RUnlock()

				if !exists {
					// 会话已删除，停止轮询
					return
				}

				if sess.Connected {
					// 已连接，停止轮询
					return
				}

				// 检查设备列表
				output, err := executeAdbCommand([]string{"devices"})
				if err != nil {
					continue
				}

				// 解析设备列表
				lines := strings.Split(output, "\n")
				for _, line := range lines {
					line = strings.TrimSpace(line)
					if line == "" || strings.HasPrefix(line, "List of devices") {
						continue
					}

					parts := strings.Fields(line)
					if len(parts) >= 2 && parts[1] == "device" {
						// 找到设备
						foundDeviceID := parts[0]

						// 准备日志采集环境（adb root、设置缓冲区大小）
						setupDeviceForLogcat(foundDeviceID)

						// 启动 logcat
						cmd := exec.Command("adb", "-s", foundDeviceID, "logcat", "-b", "all", "-v", "time")
						hideWindow(cmd)

						stdout, err := cmd.StdoutPipe()
						if err != nil {
							continue
						}

						if err := cmd.Start(); err != nil {
							continue
						}

						// 更新会话
						sessionsMutex.Lock()
						sess.DeviceID = foundDeviceID
						sess.Connected = true
						sess.Cmd = cmd
						sessionsMutex.Unlock()

						// 后台读取日志
						go func() {
							scanner := bufio.NewScanner(stdout)
							for scanner.Scan() {
								line := scanner.Text()
								sessionsMutex.Lock()
								if len(sess.Lines) >= sess.MaxLines {
									sess.Lines = sess.Lines[1:]
								}
								sess.Lines = append(sess.Lines, line)
								sessionsMutex.Unlock()
							}
						}()

						return
					}
				}
			}
		}()
	}

	// 返回结果
	response := map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"session_id": sessionID,
			"mode":       mode,
			"device_id":  deviceID,
			"message":    message,
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

// handleBootLogcatStop 停止开机日志抓取并下载
func handleBootLogcatStop(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "POST" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 从 URL 路径中提取 session_id
	// 路径格式: /boot-logcat/stop?session_id=xxx
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		http.Error(w, "session_id is required", http.StatusBadRequest)
		return
	}

	// 获取会话
	sessionsMutex.Lock()
	session, exists := sessions[sessionID]
	if !exists {
		sessionsMutex.Unlock()
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}
	delete(sessions, sessionID)
	sessionsMutex.Unlock()

	// 停止命令
	if session.Cmd != nil && session.Cmd.Process != nil {
		session.Cmd.Process.Kill()
		session.Cmd.Wait()
	}

	// 生成文件内容
	content := strings.Join(session.Lines, "\n")

	// 生成文件名
	deviceIDSafe := strings.ReplaceAll(session.DeviceID, ":", "_")
	deviceIDSafe = strings.ReplaceAll(deviceIDSafe, ".", "_")
	filename := fmt.Sprintf("boot_logcat_%s_%d.txt", deviceIDSafe, session.StartTime.Unix())

	// 返回文件
	w.Header().Set("Content-Type", "text/plain")
	w.Header().Set("Content-Disposition", fmt.Sprintf("attachment; filename=%s", filename))
	w.Write([]byte(content))
}

// handleBootLogcatStatus 查询开机日志状态
func handleBootLogcatStatus(w http.ResponseWriter, r *http.Request) {
	setCORSHeaders(w, r)

	if r.Method == "OPTIONS" {
		return
	}

	if r.Method != "GET" {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 从 URL 路径中提取 session_id
	sessionID := r.URL.Query().Get("session_id")
	if sessionID == "" {
		http.Error(w, "session_id is required", http.StatusBadRequest)
		return
	}

	// 获取会话
	sessionsMutex.RLock()
	session, exists := sessions[sessionID]
	sessionsMutex.RUnlock()

	if !exists {
		http.Error(w, "Session not found", http.StatusNotFound)
		return
	}

	// 检查进程状态
	running := false
	if session.Cmd != nil && session.Cmd.Process != nil {
		err := session.Cmd.Process.Signal(os.Signal(nil))
		running = err == nil
	}

	response := map[string]interface{}{
		"success": true,
		"data": map[string]interface{}{
			"session_id": session.ID,
			"device_id":  session.DeviceID,
			"mode":       session.Mode,
			"running":    running || session.Mode == "wait_connection",
			"connected":  session.Connected,
			"line_count": len(session.Lines),
			"start_time": session.StartTime.Format(time.RFC3339),
		},
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}
