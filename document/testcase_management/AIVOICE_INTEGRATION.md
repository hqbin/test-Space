# AI语音测试模块 — 集成文档

## 概述

将「AI语音测试规范」项目（原 React + Express + SQLite）以 Vue 3 + Element Plus + FastAPI 的方式**直接集成**到主项目 `app/` 中，统一技术栈、数据库和认证权限。

## 新增文件结构

### 后端 (`backend/`)

```
backend/
├── models_aivoice.py            # ★ 9 个 SQLAlchemy 模型
├── schemas_aivoice.py           # ★ 所有 Pydantic Schema
└── api/aivoice/                 # ★ 8 个路由模块
    ├── __init__.py               # APIRouter 聚合
    ├── release_notes.py          # 发版说明
    ├── version_records.py        # 版本记录 + 状态流转
    ├── customer_problems.py      # 问题跟踪
    ├── version_issues.py         # 版本问题
    ├── knowledge_base.py         # 知识库 / 测试用例
    ├── apk_upload.py             # APK 上传管理
    ├── project_workspaces.py     # 工作区管理
    └── settings.py               # 键值设置
```

### 前端 (`frontend/`)

```
frontend/src/
├── api/
│   └── aivoice.js                # ★ 统一 API 调用
└── views/aivoice/                # ★ 11 个页面
    ├── AivoiceDashboard.vue      # 仪表盘
    ├── VersionRecords.vue        # 版本记录
    ├── ReleaseNotes.vue          # 发版说明
    ├── CustomerProblems.vue      # 问题跟踪
    ├── VersionWorkbench.vue      # 版本工作台
    ├── VoiceRecords.vue          # 语音记录（占位）
    ├── Recommendations.vue       # 推荐知识库
    ├── AliasTest.vue             # 别名测试（占位）
    ├── ApkManagement.vue         # APK 管理
    ├── ModuleCenter.vue          # 模块中心
    └── AivoiceSettings.vue       # 设置
```

## 修改的现有文件

| 文件 | 改动说明 |
|------|---------|
| `backend/main.py` | 导入 models_aivoice（第 14-18 行）；注册 aivoice_router（第 511-512 行） |
| `frontend/src/config/permissions.js` | 添加 11 项页面权限；添加菜单配置；`getUserMenus` 增加 `aivoiceMenus` 分组 |
| `frontend/src/router/index.js` | 添加 11 个路由（路径 `/aivoice/*`） |
| `frontend/src/views/Layout.vue` | 添加「AI语音测试」折叠子菜单；导入新图标 |

## 数据库表

9 张表，均在 `models_aivoice.py` 中定义：

| 表名 | 说明 | 关键字段 |
|------|------|---------|
| `aivoice_release_notes` | 发版说明 | version, author, changeType, severity, rdSmokeStatus, apk 文件 |
| `aivoice_version_records` | 版本记录 | versionNumber, versionStatus(状态机), riskLevel, 测试结果, 结论 |
| `aivoice_customer_problems` | 客户/QA 问题 | problemType, issueId, classification, status |
| `aivoice_version_issues` | 版本问题 | versionRecordId, title, severity, reporter, linkedPR |
| `aivoice_test_cases` | 测试用例知识库 | caseName, category, priority, steps(JSON), tags(JSON) |
| `aivoice_app_settings` | 键值设置 | key(PK), value |
| `aivoice_project_workspaces` | 工作区 | id, name, builtin |
| `aivoice_workspace_modules` | 工作区-模块关联 | workspaceId, moduleId (联合主键) |
| `aivoice_workspace_groups` | 工作区项目分组 | workspaceId, name, projectType |

表由 SQLAlchemy 自动创建（`Base.metadata.create_all`），首次启动时建表。

## API 路由

所有接口统一前缀 `/api/aivoice`，认证复用主项目 JWT。

### 发版说明 (`/api/aivoice/release-notes`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/release-notes` | 列表查询（树形/扁平，支持筛选、分页、关键词） |
| GET | `/release-notes/parent-versions` | 大版本号列表 |
| GET | `/release-notes/eligible-for-qa` | 可用于 QA 的 RD 版本 |
| GET | `/release-notes/stats/summary` | 统计（项目分布、类型分布） |
| GET | `/release-notes/impact-tags` | 影响模块标签列表 |
| PUT | `/release-notes/impact-tags` | 更新影响模块标签 |
| GET | `/release-notes/:id` | 详情 |
| POST | `/release-notes` | 新建 |
| PUT | `/release-notes/:id` | 编辑 |
| DELETE | `/release-notes/:id` | 删除 |

### 版本记录 (`/api/aivoice/version-records`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/version-records` | 列表查询（支持状态/项目/关键词筛选） |
| GET | `/version-records/status-flow/options` | 状态流转选项 |
| GET | `/version-records/release-decisions/options` | 发布决策选项 |
| GET | `/version-records/:id` | 详情 |
| POST | `/version-records` | 新建 |
| PUT | `/version-records/:id` | 编辑 |
| DELETE | `/version-records/:id` | 删除 |
| POST | `/version-records/:id/transition` | 状态流转（参数：targetStatus） |

**状态流转规则**（仅向前流转）：
`待测试 → 测试中 → 阻塞 → 待结论 → 可发布 → 已发布`

### 问题跟踪 (`/api/aivoice/customer-problems`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/customer-problems` | 列表查询（支持类型/状态/分类筛选） |
| GET | `/customer-problems/:id` | 详情 |
| POST | `/customer-problems` | 新建 |
| PUT | `/customer-problems/:id` | 编辑 |
| DELETE | `/customer-problems/:id` | 删除 |

### 版本问题 (`/api/aivoice/version-issues`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/version-issues` | 列表查询（支持 versionRecordId 过滤） |
| GET | `/version-issues/:id` | 详情 |
| POST | `/version-issues` | 新建 |
| PUT | `/version-issues/:id` | 编辑 |
| DELETE | `/version-issues/:id` | 删除 |

### 知识库 (`/api/aivoice/knowledge-base`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/knowledge-base` | 列表查询（支持分类/项目/关键词筛选） |
| GET | `/knowledge-base/:id` | 详情 |
| POST | `/knowledge-base` | 新建 |
| PUT | `/knowledge-base/:id` | 编辑 |
| DELETE | `/knowledge-base/:id` | 删除 |

### APK 管理 (`/api/aivoice/apk`)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/apk/upload` | 上传 APK（multipart） |
| GET | `/apk/list` | APK 文件列表 |
| DELETE | `/apk/:fileName` | 删除 APK |

### 工作区 (`/api/aivoice/workspaces`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/workspaces` | 列表（含分组） |
| POST | `/workspaces` | 新建 |
| PUT | `/workspaces/:id` | 编辑 |
| DELETE | `/workspaces/:id` | 删除（级联删除分组和模块） |
| POST | `/workspaces/:id/groups` | 添加分组 |
| PUT | `/workspaces/groups/:groupId` | 编辑分组 |
| DELETE | `/workspaces/groups/:groupId` | 删除分组 |

### 设置 (`/api/aivoice/settings`)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/settings/:key` | 获取设置值 |
| PUT | `/settings/:key` | 保存设置值（body: `{"value": "..."}`） |

## 权限系统

新增 11 项页面级权限（`group: 'aivoice'`），由主项目的 RBAC 角色系统控制：

| 权限 Key | 菜单显示 | 路由路径 |
|----------|---------|---------|
| `aivoiceDashboard` | AI语音工作台 | `/aivoice/dashboard` |
| `aivoiceVersionRecords` | 版本记录 | `/aivoice/version-records` |
| `aivoiceReleaseNotes` | 发版说明 | `/aivoice/release-notes` |
| `aivoiceCustomerProblems` | 问题跟踪 | `/aivoice/customer-problems` |
| `aivoiceVersionWorkbench` | 版本工作台 | `/aivoice/version-workbench` |
| `aivoiceVoiceRecords` | 语音记录 | `/aivoice/voice-records` |
| `aivoiceRecommendations` | 推荐知识库 | `/aivoice/recommendations` |
| `aivoiceAliasTest` | 别名测试 | `/aivoice/alias-test` |
| `aivoiceApkManagement` | APK管理 | `/aivoice/apk-management` |
| `aivoiceModuleCenter` | 模块中心 | `/aivoice/module-center` |
| `aivoiceSettings` | AI语音设置 | `/aivoice/settings` |

## 侧边栏结构

```
▾ AI语音测试              ← 折叠菜单（有权限才显示）
  ▸ AI语音工作台
  ▸ 版本记录
  ▸ 发版说明
  ▸ 问题跟踪
  ▸ 版本工作台
  ▸ 语音记录
  ▸ 推荐知识库
  ▸ 别名测试
  ▸ APK管理
  ▸ 模块中心
  ▸ AI语音设置
```

## 与原始项目的差异

### 已完成的迁移

| 原始功能 | 集成状态 |
|---------|---------|
| 发版说明 CRUD + 树形列表 + 统计 | ✅ 完整迁移 |
| 版本记录 CRUD + 状态流转 | ✅ 完整迁移（流转规则简化） |
| 客户/QA 问题 CRUD | ✅ 完整迁移 |
| 版本问题 CRUD | ✅ 完整迁移 |
| 知识库测试用例 CRUD | ✅ 基本 CRUD |
| APK 上传/列表/删除 | ✅ 基本功能 |
| 工作区管理 | ✅ 完整迁移 |
| 设置项管理 | ✅ 完整迁移 |

### 本次未迁移的功能（后续按需添加）

| 原始功能 | 说明 | 优先级 |
|---------|------|--------|
| 文档上传 (docUpload) | 上传 xlsx/doc 原型文件到版本记录 | 低 |
| 问题附件 (issueAttachments) | 上传视频/截图/log 到版本问题 | 低 |
| 别名测试 (aliasTest) | TV 应用别名匹配和技能路由验证代理 | 中 |
| 语音自动化 (voiceAutomation) | 语音自动化测试作业管理 | 中 |
| MITM 代理 (mitmProxy) | HTTPS 流量捕获和规则引擎 | 低 |
| zmind 代理 (zmindProxy) | zmind 问题追踪系统集成代理 | 中 |
| 知识库 AI 推荐 | Azure OpenAI 智能推荐测试用例 | 低 |
| 问题 zmind 同步 | 创建问题自动同步到 zmind | 中 |
| APK 签名/下载 | 多品牌 APK 签名和打包下载 | 低 |

### 行为变化

| 特性 | 原始 | 本集成 |
|------|------|--------|
| 状态流转 | 基于 Map 的灵活规则（可停留、可跳转） | 简化版（仅向前顺序流转） |
| 数据存储 | SQLite (better-sqlite3) | PostgreSQL (SQLAlchemy) |
| 认证方式 | Token + Session 表 | JWT（复用主项目） |
| 用户管理 | 独立用户表 + 项目角色 | 复用主项目用户 + RBAC 角色 |

## 开发协作说明

### 协作者拉取代码后的动作

```bash
# 后端会自动创建 aivoice 表（第一次启动时）
cd app/backend
python main.py

# 前端无额外操作，路由和菜单自动生效
cd app/frontend
npm run dev
```

### 各模块负责人

| 页面 | 后端文件 | 前端文件 |
|------|---------|---------|
| 工作台 | — | `AivoiceDashboard.vue` |
| 版本记录 | `version_records.py` | `VersionRecords.vue` |
| 发版说明 | `release_notes.py` | `ReleaseNotes.vue` |
| 问题跟踪 | `customer_problems.py` | `CustomerProblems.vue` |
| 版本工作台 | 复用 `version_records.py` + `version_issues.py` | `VersionWorkbench.vue` |
| 语音记录 | （待添加）`voiceAutomation.py` | `VoiceRecords.vue` |
| 推荐知识库 | `knowledge_base.py` | `Recommendations.vue` |
| 别名测试 | （待添加）`alias_test.py` | `AliasTest.vue` |
| APK管理 | `apk_upload.py` | `ApkManagement.vue` |
| 模块中心 | `project_workspaces.py` | `ModuleCenter.vue` |
| 设置 | `settings.py` | `AivoiceSettings.vue` |

### API 响应格式

所有接口统一返回格式：

```json
// 成功
{ "success": true, "data": { ... } }

// 列表
{ "success": true, "data": { "data": [...], "total": N, "page": 1, "pageSize": 20, "totalPages": 5 } }

// 错误
{ "detail": "错误描述" }   // HTTP 4xx/5xx
```

### 添加新功能步骤

1. 在 `models_aivoice.py` 添加/修改模型
2. 在 `schemas_aivoice.py` 添加/修改 Schema
3. 在 `api/aivoice/` 下创建路由文件或修改已有文件
4. 在 `api/aivoice/__init__.py` 注册新路由
5. 在 `frontend/src/api/aivoice.js` 添加 API 调用
6. 在 `frontend/src/views/aivoice/` 下创建/修改 Vue 页面
7. 在 `frontend/src/config/permissions.js` 添加权限项（如需）
8. 在 `frontend/src/router/index.js` 添加路由（如需）
