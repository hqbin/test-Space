# TestSpace 备份服务 API 文档

**前缀**: `/api/TestSpace`
**请求格式**: JSON
**响应格式**: JSON

## Header 要求

所有接口需要在 Request Header 中携带：

| Header | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `X-Device-ID` | string | 是 | 设备UUID，用于区分不同设备的备份 |

---

## 1. 上传备份

`POST /api/TestSpace/backups`

上传加密的备份数据到服务器（服务器永不解密）。

### Request Body

```json
{
  "data": "base64编码的AES加密密文",
  "iv": "base64编码的IV",
  "salt": "base64编码的Salt",
  "auth_tag": "base64编码的认证标签",
  "size_bytes": 102400,
  "checksum": "sha256hex...",
  "metadata": {
    "version": "1.3",
    "exportedAt": "2026-06-18T14:30:22.000Z"
  }
}
```

### Response 201 Created

```json
{
  "id": "a3f2c8e1-9b47-4d2c-8f1d-3e6a9b0c7d2f",
  "created_at": "2026-06-18T14:30:25.123Z"
}
```

### Response 400 Bad Request

```json
{ "error": "data is required" }
```

---

## 2. 获取备份列表

`GET /api/TestSpace/backups`

### Response 200 OK

```json
[
  {
    "id": "a3f2c8e1-...",
    "device_id": "7f1a2b3c-...",
    "size_bytes": 102400,
    "checksum": "sha256hex...",
    "metadata": { "version": "1.3", "exportedAt": "..." },
    "created_at": "2026-06-18T14:30:25.123Z"
  }
]
```

---

## 3. 获取指定备份详情

`GET /api/TestSpace/backups/{id}`

### Response 200 OK

```json
{
  "id": "a3f2c8e1-...",
  "device_id": "7f1a2b3c-...",
  "data": "base64...",
  "iv": "base64...",
  "salt": "base64...",
  "auth_tag": "base64...",
  "size_bytes": 102400,
  "checksum": "sha256hex...",
  "metadata": { "version": "1.3", "exportedAt": "..." },
  "created_at": "2026-06-18T14:30:25.123Z"
}
```

### Response 404

```json
{ "error": "backup not found" }
```

### Response 403

```json
{ "error": "device_id mismatch" }
```

---

## 4. 删除备份

`DELETE /api/TestSpace/backups/{id}`

### Response 204 No Content

### Response 404/403 同上

---

## 数据库表结构

### cloud_backups

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | VARCHAR(36) PK | 备份唯一标识，自动生成 UUID |
| `device_id` | VARCHAR(255) | 设备标识，由客户端传入 |
| `data` | TEXT | Base64 编码的 AES-256-GCM 加密密文 |
| `iv` | TEXT | Base64 编码的 AES-GCM 初始化向量 |
| `salt` | TEXT | Base64 编码的密钥派生盐值 |
| `auth_tag` | TEXT | Base64 编码的 GCM 认证标签 |
| `size_bytes` | BIGINT | 原始 JSON 数据大小（字节） |
| `checksum` | VARCHAR(64) | 原始 JSON 数据的 SHA256 十六进制字符串 |
| `metadata` | TEXT | JSON 字符串 |
| `created_at` | TIMESTAMP | 备份创建时间 |

索引：`idx_cb_device` (device_id), `idx_cb_created` (created_at)

## 安全要点

| 要点 | 说明 |
|------|------|
| 数据机密性 | 服务器永不解密 data 字段，加密完全在客户端完成 |
| 设备隔离 | 用 device_id 隔离不同设备数据 |
| ID 保护 | id 是 UUID，不可枚举；即使猜到也需匹配 device_id |
