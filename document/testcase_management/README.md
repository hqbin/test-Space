# 测试用例管理平台

一个功能完整的测试管理系统，集成测试用例库管理和测试执行能力。

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- PostgreSQL 12+

### 一键启动

#### Windows 开发环境
```bash
scripts\start-dev.bat
```

#### Windows 生产环境
```bash
scripts\deploy-windows.bat    # 首次部署
scripts\service-manage.bat    # 服务管理
```

#### Linux 生产环境
```bash
chmod +x deploy/*.sh
bash deploy/deploy.sh              # 首次部署
bash deploy/service-manage.sh install   # 安装服务
bash deploy/service-manage.sh start     # 启动服务
```

启动后访问：
- 前端：http://localhost:2026
- 后端API：http://localhost:8080
- API文档：http://localhost:2026/docs（通过 Nginx 代理）

### 默认管理员账号

- 用户名：`admin`
- 密码：`Admin@whaletv.123!`

## 核心功能

- **测试用例管理**：CRUD操作、Excel批量导入导出、搜索分页
- **模块管理**：支持主模块和子模块的层级结构
- **测试计划管理**：创建计划、关联用例、分配执行人、跟踪进度
- **测试执行**：记录结果（通过/失败/阻塞/跳过）、添加备注、上传附件
- **测试报告**：生成和导出PDF/Excel格式的测试报告
- **用例校对**：自动检查用例质量，支持自定义校对规则
- **Zmind集成**：从外部Zmind平台同步测试用例
- **用户与项目管理**：基于角色的权限控制、项目授权
- **组织管理**：项目组管理、成员分配
- **通知系统**：站内通知、钉钉机器人通知、自定义通知规则和模板
- **ADB Tool**：集成的 Android 调试工具（Web ADB）
- **审计日志**：完整的操作历史跟踪

## 项目结构

```
testcase_management/
├── app/                          # 应用代码
│   ├── backend/                 # Python FastAPI 后端
│   │   ├── api/                # API 路由模块
│   │   ├── services/           # 业务服务层
│   │   ├── utils/              # 工具函数
│   │   └── data/               # 数据存储目录
│   └── frontend/                # Vue 3 前端
│       ├── src/                # 源代码
│       └── public/adb-tool/    # ADB Tool 静态文件
│
├── scripts/                      # Windows 部署和管理脚本
│   ├── deploy-windows.bat       # Windows 首次部署
│   ├── service-manage.bat       # Windows 服务管理
│   ├── update-deploy.bat        # Windows 代码更新
│   ├── db-migrate.bat           # 数据库迁移工具
│   ├── backup_database.py       # 数据库备份
│   └── 部署与运维手册.md         # Windows 运维手册
│
├── deploy/                       # Linux 部署和管理脚本
│   ├── deploy.sh                # Linux 首次部署
│   ├── service-manage.sh        # Linux 服务管理（systemd）
│   ├── update.sh                # Linux 代码更新
│   ├── backup.sh                # 数据库备份
│   ├── restore.sh               # 数据库恢复
│   ├── nginx.conf.template      # Nginx 配置模板
│   └── README.md                # Linux 运维手册
│
├── web-adb-tool/                 # ADB Tool 源码（独立 React 项目）
├── temp-scripts/                 # 临时脚本目录（调试、测试脚本）
├── docs/                         # 文档目录
└── README.md                    # 本文件
```

## 首次安装

### 1. 创建数据库

```sql
CREATE DATABASE testcase_platform;
```

### 2. 配置环境变量

编辑对应环境的配置文件：
- 后端：`app/backend/.env.production`（或 `.env.development`）
- 前端：`app/frontend/.env.production`（或 `.env.development`）

必须修改的配置项：
- `DATABASE_URL` - 数据库连接字符串
- `SECRET_KEY` - JWT密钥（生产环境必须使用强密钥）
- `CORS_ORIGINS` - 允许的前端域名

### 3. 部署

- Windows：参考 [scripts/部署与运维手册.md](scripts/部署与运维手册.md)
- Linux：参考 [deploy/README.md](deploy/README.md)

## 手动启动

### 后端
```bash
cd app/backend
python -m venv venv
source venv/bin/activate        # Linux
# venv\Scripts\activate         # Windows
pip install -r requirements.txt
cp .env.development .env
python main.py
```

### 前端
```bash
cd app/frontend
npm install
npm run dev
```

## 技术栈

### 后端
- FastAPI 0.104.1
- SQLAlchemy 2.0.23
- PostgreSQL 12+
- Python 3.9+
- Alembic（数据库迁移）

### 前端
- Vue 3.3.4
- Element Plus 2.3.14
- Vite 4.4.9
- Pinia 2.1.6
- Vue I18n（国际化）

### 部署
- Nginx（反向代理 + 静态文件）
- systemd（Linux 服务管理）
- NSSM（Windows 服务管理）

## 文档

- [Windows 部署与运维手册](scripts/部署与运维手册.md)
- [Linux 部署与运维手册](deploy/README.md)

## 故障排查

### 后端无法启动
1. 检查 Python 版本：`python --version`（需要 3.9+）
2. 检查数据库连接配置（`.env` 中的 `DATABASE_URL`）
3. 检查虚拟环境是否激活

### 前端无法启动
1. 检查 Node.js 版本：`node --version`（需要 16+）
2. 检查依赖是否安装：`npm install`
3. 检查 API 地址配置

### 数据库连接失败
1. 检查 PostgreSQL 服务是否启动
2. 检查数据库是否已创建
3. 检查用户名密码是否正确（注意特殊字符需要 URL 编码）

## 许可证

内部项目
