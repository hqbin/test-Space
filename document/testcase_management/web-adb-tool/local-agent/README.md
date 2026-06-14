# ADB 本地代理

## 简介

这是一个轻量级的本地 HTTP 服务器，用于在用户电脑上执行 ADB 命令。

## 功能

- 监听 `localhost:9527`
- 接收来自浏览器的 ADB 命令请求
- 执行本地 ADB 命令
- 返回执行结果

## 构建

### Windows

```batch
build.bat
```

### Mac/Linux

```bash
chmod +x build.sh
./build.sh
```

## 使用

### 启动代理

**Windows**:
```batch
adb-agent-windows.exe
```

**Mac**:
```bash
./adb-agent-mac
```

### 测试

```bash
# 健康检查
curl http://localhost:9527/health

# 执行 ADB 命令
curl -X POST http://localhost:9527/adb \
  -H "Content-Type: application/json" \
  -d '{"command":"adb","args":["devices","-l"]}'
```

## API

### GET /health

健康检查

**响应**:
```
OK
```

### GET /version

获取版本信息

**响应**:
```json
{
  "version": "1.0.0",
  "name": "ADB Local Agent"
}
```

### POST /adb

执行 ADB 命令

**请求**:
```json
{
  "command": "adb",
  "args": ["devices", "-l"]
}
```

**响应**:
```json
{
  "success": true,
  "output": "List of devices attached\n...",
  "error": ""
}
```

## 安全

- 只监听 `localhost`，外部无法访问
- 验证命令参数，防止注入攻击
- CORS 限制，只允许特定来源

## 文件大小

- Windows: 约 5-8MB
- Mac: 约 5-8MB

## 依赖

- Go 1.21+
- ADB（需要在系统 PATH 中）
