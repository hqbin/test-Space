# Test Space 开发文档

> **重要**：每次对项目进行更新或修改后，必须同步更新本文档。所有新增、修改或删除的功能都要在对应页面模块中描述清楚。本文档是项目的核心参考文件。
>
> **UI/UX 一致性守则**：凡新增或修改功能，其交互控件（按钮、标签页、导航项、卡片、图标操作区等）必须统一使用本文档定义的 `.glass-button` / `.glass-hover` / `.glass-active` CSS 类，禁用 `bg-primary-container`、`bg-secondary-fixed`（作为活跃态时替换为 `glass-active`）、`text-primary`（作为可点击文字时替换为 `glass-button`）等旧样式。新页面或新控件不得自创样式模式，必须继承现有的液态玻璃设计系统。所有改动的 UI 元素在提交前须通过 `npm run build` 确保无类型/样式回归。
>
> **功能安全守则**：每次修改已有代码时，必须评估改动的影响范围，确保不破坏相邻或依赖模块的既有功能。以"最小改动、最大兼容"为原则：优先做增量调整而非重构重写；修改公共模块（composable、API 层、store、路由守卫、布局组件）时须同时验证所有调用方是否仍正常工作；删除或重命名任何导出、路由、CSS 类或 API 字段前，必须全局搜索确认无其他引用。提交前执行 `npm run build` 通过类型检查和构建，并对修改涉及的功能路径做人工冒烟验证。

---

## 一、项目概述

Test Space 是一款面向软件测试工程师的 Windows 桌面工作台，使用 Tauri 2 桌面框架 + Vue 3 前端技术栈构建。它将测试用例设计、测试平台管理、ADB 调试、串口调试、日志分析、脚本执行、知识沉淀整合到一个桌面应用中。

### 产品定位

Cursor for Testing — 非传统测试管理平台，而是桌面客户端和效率工具。

---

## 二、技术架构

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 桌面框架 | **Tauri 2** | 基于 Rust 的跨平台桌面框架，体积小、性能高 |
| 前端框架 | **Vue 3** (Composition API + `<script setup>`) | 现代化响应式 UI 框架 |
| 构建工具 | **Vite 6** | 极速开发服务器和构建 |
| 类型系统 | **TypeScript** | 全栈类型安全 |
| 状态管理 | **Pinia** | Vue 3 官方状态管理 |
| 路由 | **Vue Router 4** | SPA 路由管理 |
| 样式 | **TailwindCSS 3** | 原子化 CSS + 自定义设计 Token |
| HTTP 客户端 | **Axios** | JWT 鉴权 + 请求签名 + Token 滑动续期 |
| 图标 | **Material Symbols Outlined** | Google 可变字体图标 |
| 字体 | **Inter** | 无衬线字体家族 |
| 原生层 | **Rust** | ADB 执行、串口通信、脚本执行 |
| 插件 | `tauri-plugin-shell` / `tauri-plugin-dialog` / `tauri-plugin-fs` / `tauri-plugin-log` | Tauri 官方插件 |

### 依赖清单 (`package.json`)

```
生产依赖:
  @tanstack/vue-table ^8.20.6    — 表格视图（Case Space）
   @tiptap/starter-kit ^2.27.2    — 富文本编辑器核心（Notes Space）
   @tiptap/vue-3 ^2.27.2          — TipTap Vue 集成
   @tiptap/extension-underline ^2.27.2  — 下划线扩展
   @tiptap/extension-link ^2.27.2      — 超链接扩展
   @tiptap/extension-image ^2.27.2     — 图片嵌入扩展
   @tiptap/extension-placeholder ^2.27.2 — 占位提示扩展
   @tiptap/extension-typography ^2.27.2  — 排版扩展
  axios ^1.7.9                   — HTTP 请求
  echarts ^5.6.0                 — 图表（Analytics，Phase 3）
  xlsx ^0.18.5                   — Excel 导入解析（Case Space）
  html-to-image ^1.11.11         — HTML 导出为图片（Mind Map 快照）
  monaco-editor ^0.52.2          — 代码/SQL 编辑器（Phase 2）
  pinia ^2.3.1                   — 状态管理
  vue ^3.5.13                    — 核心框架
  vue-router ^4.5.0              — 路由

开发依赖:
  @tauri-apps/api ^2.2.0         — Tauri 前端 API
  @tauri-apps/cli ^2.2.0         — Tauri CLI
  @vitejs/plugin-vue ^5.2.1      — Vite Vue 插件
  tailwindcss ^3.4.17            — CSS 框架
  typescript ~5.7.2               — TypeScript
  vite ^6.0.5                    — 构建工具
  vue-tsc ^2.2.0                 — Vue TypeScript 类型检查
```

### Rust 依赖 (`src-tauri/Cargo.toml`)

```
tauri 2.11.2                     — Tauri 核心
serialport 4.3                   — 串口通信
tokio 1 (full)                   — 异步运行时
uuid 1 (v4)                      — UUID 生成
tauri-plugin-shell 2             — 调用外部命令
tauri-plugin-dialog 2            — 原生对话框
tauri-plugin-fs 2                — 文件系统访问
tauri-plugin-log 2               — 日志记录
```

---

## 三、项目结构

```
D:\TestSpace\test-space/
├── index.html                          # 入口 HTML（Inter 字体 + Material Symbols）
├── package.json                        # NPM 依赖和脚本
├── vite.config.ts                      # Vite 配置（含 /api 代理到后端）
├── tailwind.config.ts                  # TailwindCSS 设计 Token 配置
├── postcss.config.js                   # PostCSS 配置
├── tsconfig.json                       # TypeScript 配置
│
├── src/                                # 前端源码
│   ├── main.ts                         # 应用入口（挂载 Pinia + Router）
│   ├── App.vue                         # 根组件（仅 <router-view />）
│   ├── env.d.ts                        # 类型声明
│   │
│   ├── styles/
│   │   └── main.css                    # TailwindCSS + 玻璃态 CSS 类 + 自定义滚动条
│   │
│   ├── types/
│   │   └── index.ts                    # 全局类型定义（UserInfo, DeviceInfo, LogEntry 等）
│   │
│   ├── api/                            # API 层
│   │   ├── request.ts                  # Axios 实例（JWT + 签名 + 滑动续期 + 401 兜底）
│   │   ├── auth.ts                     # 登录/登出/刷新 Token API
│   │   ├── captcha.ts                  # 验证码 API
│   │   ├── dashboard.ts                # 仪表盘 API（stats / quick-actions / projects）
│   │   ├── testcases.ts                # 测试用例 API（CRUD）
│   │   ├── version-releases.ts         # 版本发布 API（CRUD + publish）
│   │   ├── database.ts                 # 数据库管理 API（tables / sql execute）
│   │   ├── analytics.ts                # 数据埋点 API（stats / trends / feature-usage）
│   │   └── notes.ts                    # 笔记 API（CRUD + content sync）
│   │
│   ├── stores/                         # Pinia 状态管理
│   │   └── user.ts                     # 用户认证状态（login/logout/isLoggedIn/avatarUrl）
│   │
│   ├── router/
│   │   └── index.ts                    # 路由配置 + 导航守卫
│   │
│   ├── layouts/                        # 布局组件
│   │   ├── AppLayout.vue               # 主布局（Sidebar + TopNav + 背景渐变 + <router-view />）
│   │   ├── CaseSpaceLayout.vue         # Case Space 二级导航（All Cases / Field Rules Tab + New Case 按钮）
│   │   ├── Sidebar.vue                 # 左侧固定导航栏（256px，玻璃面板）
│   │   ├── TopNav.vue                  # 顶部导航栏（搜索框 + 通知/帮助/用户按钮）
│   │   └── PlatformLayout.vue          # Platform Space 二级导航（Tab 切换布局）
│   │
│   ├── composables/                    # 可复用组合式函数
│   │   ├── useAdb.ts                   # ADB 操作（listDevices/shell/installApk 等）
│   │   ├── useSerial.ts                # 串口操作（listPorts/connect/send/read）
│   │   ├── useScriptExec.ts            # 脚本执行（Python/BAT/PowerShell）
│   │   └── useTestCaseStore.ts         # 测试用例 + 字段规则状态管理
│   │
│   └── views/                          # 页面视图
│       ├── auth/
│       │   └── Login.vue               # 登录页（验证码 + 用户名/密码）
│       ├── workspace/
│       │   └── WorkspacePage.vue       # 首页（问候语 + 命令中心 + 快捷操作 + Continue Working）
│       ├── case-space/
│       │   ├── CaseSpacePage.vue       # 用例列表（卡片网格视图）
│       │   ├── editor/
│       │   │   └── CaseEditorPage.vue  # 用例编辑器（表格编辑 + 思维导图切换）
│       │   └── field-rules/
│       │       └── FieldRulesPage.vue  # 字段规则配置
│       ├── device-space/
│       │   └── DeviceSpacePage.vue     # 设备空间（设备列表 + 遥测 + Logcat + ADB 工具）
│       ├── note-space/
│       │   └── NotesSpacePage.vue      # 笔记空间（文件树 + 富文本编辑器 + 上下文面板）
│       ├── platform-space/
│       │   ├── analytics/
│       │   │   └── AnalyticsPage.vue   # 数据埋点/分析仪表盘
│       │   ├── database/
│       │   │   └── DatabasePage.vue    # 数据库管理（表浏览 + SQL 编辑器 + 安全确认）
│       │   └── version-release/
│       │       └── VersionReleasePage.vue # 版本发布管理（列表 + 编辑 + 发布）
│       ├── script-space/
│       │   └── ScriptSpacePage.vue     # 脚本空间（分类 + 搜索）
│       └── settings/
│           └── SettingsPage.vue        # 设置页（Profile + 主题 + 平台连接 + 登出）
│
└── src-tauri/                          # Rust 原生层
    ├── Cargo.toml                      # Rust 依赖
    ├── tauri.conf.json                 # Tauri 配置（窗口、权限、插件）
    ├── build.rs                        # 构建脚本
    ├── capabilities/
    │   └── default.json                # Tauri 2 权限能力
    ├── icons/                          # 应用图标
    └── src/
        ├── main.rs                     # Rust 入口（#![windows_subsystem = "windows"]）
        ├── lib.rs                      # Tauri Builder + 所有命令注册
        ├── adb.rs                      # ADB 命令（devices/shell/install/push/pull/reboot/screenshot）
        ├── serial_port.rs              # 串口通信（list/connect/disconnect/send/read）
        └── script_exec.rs              # 脚本执行（Python/BAT/PowerShell/Shell）
```

---

## 四、各模块实现说明

### 4.1 认证系统 (`src/views/auth/Login.vue`)

**实现**：
- 页面加载时调用 `GET /api/captcha` 获取验证码（base64 图片 + captcha_id）
- 用户输入用户名、密码、验证码后调用 `POST /api/auth/login`
- 登录成功后 JWT Token 存入 `localStorage['token']`，用户信息存入 `localStorage['user']`
- 若 `signKey` 存在，存入 `localStorage['signKey']` 用于请求签名
- 登录成功后跳转至 `redirect` 参数指定的页面或 `/workspace`

**相关文件**：
- `src/views/auth/Login.vue` — 登录页面 UI
- `src/api/auth.ts` — 登录 API 调用
- `src/api/captcha.ts` — 验证码 API
- `src/stores/user.ts` — 用户状态管理（`login`/`logout`/`isLoggedIn`/`displayName`/`avatarUrl`）

### 4.2 API 层 (`src/api/request.ts`)

**实现**：
- 基于 Axios 创建实例，`baseURL: '/api'`
- **请求拦截器**：自动附加 `Authorization: Bearer <token>` 请求头；检测 Token 剩余 TTL < 24h 时自动后台续签；若存在 `signKey` 则生成 `X-Timestamp`/`X-Nonce`/`X-Sign` 签名头
- **响应拦截器**：`code !== 200` 时 reject；`401` 时尝试静默刷新一次，失败则清除 Token 跳转登录页；`403` 返回无权限错误

**相关文件**：
- `src/api/request.ts`
- `src/api/auth.ts` — 登录/登出/刷新
- `src/api/captcha.ts` — 验证码

### 4.3 路由系统 (`src/router/index.ts`)

**路由表**：

| 路径 | 组件 | 说明 |
|------|------|------|
| `/login` | `Login.vue` | 公开页面，已登录自动跳转 Workspace |
| `/` | `AppLayout.vue` | 需认证，嵌套子路由 |
| `/workspace` | `WorkspacePage.vue` | 首页 |
| `/case-space` | `CaseSpaceLayout.vue` → `CaseSpacePage.vue` | 用例空间（卡片列表） |
| `/case-space/editor` | `CaseEditorPage.vue` | 新建测试用例 |
| `/case-space/editor/:id` | `CaseEditorPage.vue` | 编辑测试用例 |
| `/case-space/field-rules` | `FieldRulesPage.vue` | 字段规则配置 |
| `/device-space` | `DeviceSpacePage.vue` | 设备空间 |
| `/notes-space` | `NotesSpacePage.vue` | 笔记空间 |
| `/platform-space` | `PlatformLayout.vue` | 平台空间（二级 Tab 导航） |
| `/platform-space/analytics` | `AnalyticsPage.vue` | 数据埋点 |
| `/platform-space/database` | `DatabasePage.vue` | 数据库管理 |
| `/platform-space/version-release` | `VersionReleasePage.vue` | 版本发布 |
| `/script-space` | `ScriptSpacePage.vue` | 脚本空间 |
| `/settings` | `SettingsPage.vue` | 设置 |

**导航守卫**：
- `meta.public === false` 且无 Token → 重定向 `/login?redirect=xxx`
- 已登录访问 `/login` → 重定向 `/workspace`

### 4.4 布局系统

#### 4.4.1 AppLayout（主布局）

**实现**：
- 固定左侧 Sidebar（256px 宽）
- 固定顶部 TopNav（右偏移 256px，高 64px，z-40）
- 主内容区 `ml-[256px] pt-safe-area-top px-margin-page max-w-[1200px] mx-auto`
- 每个 Space 有不同的背景径向渐变（通过 `route.path` 判断）

**背景渐变方案**：

| 页面 | 渐变 |
|------|------|
| Workspace | `radial-gradient(circle at 50% 0%, #DAE1FF 0%, #F9F9FB 50%)` |
| Case Space | 左上角 lavender 渐变 + 右下角蓝色微光 |
| Device Space | 左中 secondary 微光 + 右中 primary 微光 |
| Notes Space | 顶部到下部渐变灰 |
| 其他 | 纯白 `#F9F9FB` |

#### 4.4.2 Sidebar（侧边栏）

**实现**：
- 固定定位，`w-[256px]`，玻璃面板（`bg-glass-surface/15 backdrop-blur-[60px]`）
- 导航项：当前活跃路由使用 `bg-secondary-fixed` + `font-semibold` 样式
- 图标使用 Material Symbols，活跃态 `FILL 1`，非活跃态 `FILL 0`
- Platform Space 判断使用 `path.startsWith()` 实现子路由高亮
- Settings 固定在底部（`mt-auto`）

**导航项**：
Workspace → Case Space → Device Space → Notes Space → Platform Space → Script Space → Settings

#### 4.4.3 TopNav（顶部导航）

**实现**：
- 固定顶部，`w-[calc(100%-256px)]`，玻璃面板
- 左侧搜索框（圆角胶囊，`bg-surface-container-low`，凹陷阴影，聚焦时蓝色光环）
- 右侧三个图标按钮：通知、帮助、用户头像（hover 变色 + 背景高亮）

#### 4.4.4 PlatformLayout（平台空间二级导航）

**实现**：
- 在顶部渲染玻璃态胶囊状 Tab 切换器
- 三个 Tab：Data Analytics、Database、Version Release
- 活跃 Tab 使用 `bg-secondary-fixed` + `shadow` 样式
- 子路由通过 `<router-view />` 渲染

### 4.5 设计系统 (`src/styles/main.css` + `tailwind.config.ts`)

**设计来源**：完全遵循 `stitch_liquid_glass_spatial_ui` 设计规范

**核心 CSS 类**：

| 类名 | 用途 | 样式 |
|------|------|------|
| `.glass-panel` | 背景面板 | 15% 白透明度 + 60px 模糊 + 双色边框 |
| `.glass-card` | 可交互卡片 | 20% 白透明度 + 60px 模糊 + hover 上移 + 阴影 |
| `.glass-card-active` | 选中状态卡片 | lavender 底色 + secondary 边框 + 彩色发光 |
| `.glass-button` | 按钮 | 玻璃毛边透明背景 + 深色文字；hover: 浅紫色渐变背景 + `scale(1.08)` + 四层阴影（`4px/16px/48px/80px`）；`glass-breath` 动画 1.5s 脉动；active: `scale(0.97)` |
| `.glass-hover` | 通用悬停效果 | 紫色渐变 hover（`!important`）+ `scale(1.05)` + 四层阴影 + 呼吸动画；用于非按钮交互元素（卡片、导航项、标签页切换器、实体标签） |
| `.glass-active` | 选中/激活态 | 更强紫色渐变填充 + 蓝紫色边框发光 + 阴影；替换旧的 `bg-secondary-fixed text-on-secondary-fixed-variant shadow` 模式 |
| `.glass-input` | 输入框 | 40% 白透明度 + 内阴影凹陷 + focus 蓝色边框 |
| `.recessed-input` | 凹陷输入框 | 内阴影 + focus 蓝色外发光 |
| `.status-pulse` | 状态脉冲 | `pulse-ring` 动画（缩放 + 淡出循环） |

**设计 Token**（`tailwind.config.ts`）：
- 完整颜色系统（primary/secondary/tertiary/surface/error/glass 等 50+ 色值）
- 圆角系统（DEFAULT: 1rem, lg: 2rem, xl: 3rem, full: 9999px）
- 间距系统（padding-card: 32px, margin-page: 40px, gutter-grid: 24px 等）
- 字体系统（Inter 家族，6 级字号 display-lg → caption）
- 所有值严格对应设计文档中的 YAML 定义

### 4.6 Workspace 首页 (`src/views/workspace/WorkspacePage.vue`)

**实现**：
- **问候语**：根据当前时间显示 "Good Morning/Afternoon/Evening"
- **命令中心**：玻璃面板圆角胶囊 + 搜索图标 + 文本输入 + Execute 按钮
- **快捷操作**：3 列网格，每项为 `glass-card` + 图标容器（48px 圆）+ hover 放大 + 标题 + 描述。数据来源：`fetchQuickActions()`（`src/api/dashboard.ts`）
- **Continue Working**：2 列网格项目卡片（`rounded-[2rem]` 超级圆角），含运行状态标签（LED 脉冲动画）+ 图标 + 标题 + 描述 + 底部时间 + 头像堆叠。数据来源：`fetchProjects()`（`src/api/dashboard.ts`）
- **数据加载**：`onMounted` 时并行请求 API，失败时回退到内置 mock 数据

### 4.7 Case Space（改版 Phase 2 — 多页路由架构）

Case Space 由三个子页面组成，通过 `CaseSpaceLayout` 统一管理导航和创建入口。从单页改为嵌套路由：`/case-space`（卡片列表）/ `/case-space/editor`（编辑器）/ `/case-space/field-rules`（字段规则）。

#### 4.7.1 CaseSpaceLayout (`src/layouts/CaseSpaceLayout.vue`)

**实现**：
- 顶部左侧 `+` 按钮（New Case）+ `file_download` 按钮（Import Excel，图标朝下）
- 右侧玻璃态胶囊状 Tab 切换器：All Cases / Field Rules
- **New Case 对话框**（Teleport 浮层）：
  - Case Name 输入框（必填）+ Field Rule **自定义玻璃下拉选择器**（替换原生 `<select>`）
  - **Field Rule 下拉框**：触发器为圆角胶囊（`bg-glass-surface/15 backdrop-blur-[20px] border-white/40 rounded-full`）+ 展开动画 chevron 图标；下拉面板为 `glass-panel rounded-2xl`，带 `Transition` 淡入+缩放动画；每个选项为 `rounded-xl`，hover 白色半透明背景，选中项显示绿色 `check` 图标 + `font-medium`；点击外部或选项自动关闭（`@click.stop` + document click listener）
  - "Start Editing" 确认后带 query（name+rule）跳转 `/case-space/editor`
  - `+` 按钮和空状态按钮通过 CustomEvent `case-space:create-new` 统一触发
- **Excel 导入**：通过 `xlsx` 库解析 .xlsx/.xls/.csv，字段多语言映射，导入后显示 Toast 提示数量
- 通过 `<router-view />` 渲染子路由

#### 4.7.2 CaseSpacePage (`src/views/case-space/CaseSpacePage.vue`)

**实现**：
- **卡片网格视图**：`grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4`
- **每张卡片**：
  - 头部：用例编号（mono 字体）+ 删除按钮（叉号）
  - 标题：`font-body-lg` 加粗，最多 2 行截断（`line-clamp-2`）
  - 模块路径：`folder` 图标 + truncate（`v-if="tc.module"`，无模块时不显示）
  - 底部：Steps 数量 + Automation 标签（绿色 Auto 图标）
- **空状态**：大图标 + "No test case files yet" + "Create Test Case File" 按钮（触发 CustomEvent）
- **删除确认**：点击删除 → Teleport 对话框二次确认（红色警告 + 不可撤销提示）
- **点击卡片**：跳转 `/case-space/editor/:id` 编辑
- **数据来源**：`useTestCaseStore` composable

#### 4.7.3 CaseEditorPage (`src/views/case-space/editor/CaseEditorPage.vue`)

**实现**：
- **顶部**：返回按钮 + 用例名（显示真实内容行数）+ Table ↔ Mind Map 切换 + Save 按钮
- **200 行 Excel 模式**：编辑器自动展示 200 行（含占位虚拟行），用户直接在任何空行输入，无需手动新增
- **列头筛选/排序**：每列表头右侧 `filter_list` 图标 → 浮层：升序/降序排序 + 按值复选框多选过滤（类似 WPS Excel）
- **列管理**："Columns" 按钮展开列选择面板，按字段规则勾选表头（select 类型 → `<select>` 渲染，其余 → `<textarea>` 就地编辑）
- **列拖拽调宽**：表头右侧 `cursor-col-resize` 拖拽手柄
- **行管理**："Row" 按钮添加新行，每行右侧复制/删除按钮，支持 Shift 多选 + Ctrl/Cmd 点选
- **空状态**：无内容行（虚拟行不计入）时显示 "No test cases yet"
- **状态栏**：底部显示真实行数 + 选中行数 + 删除选中按钮
- **右键菜单**：行上右键 → 在上方/下方插入、复制、删除；表头右键 → 添加/编辑/删除自定义列
- **快捷键**：`Ctrl+S` / `Cmd+S` 保存
- **保存**：Save 按钮 → 仅真实内容行写入 SQLite（空行不保存）；Save As → 导出 Excel(.xlsx) 或 思维导图(.png)
- **表格编辑器**（默认视图，电子表格风格，动态列来自字段规则）：
  - 选定字段规则后自动勾选可见字段列作为表头
  - 单元格无 placeholder 提示文本
  - `priority` 默认值为空（而非 `'P2'`）
- **思维导图视图**：
  - 左根节点（用例名）+ 右上方字段节点 + 右下方步骤节点列表
  - SVG 贝塞尔连接线 + 缩放控件（+ / - / fit / 百分比）

#### 4.7.4 FieldRulesPage (`src/views/case-space/field-rules/FieldRulesPage.vue`)

**实现**：
- **规则集卡片网格**：名称 / 可见字段数 / 创建时间 / 字段 chips 展示
- **点击卡片**：进入详细编辑视图（全字段属性编辑）
- **New Rule Set** 按钮 → 弹窗输入名称，创建后复制 Default Fields 作为初始字段集
- **删除**：二次确认（红色警告 + 不可撤销提示），Default Fields 不可删除
- **数据来源**：`useTestCaseStore`（`fieldRuleSets` + `activeFieldRules`）

**字段级编辑能力**：
- **编辑视图表格列**：# / Key / Label / Chinese Label / Type / Options / Visible / Required / 删除
- **Key（字段键名）**：可编辑，使用 `font-mono` 等宽字体，聚焦失焦时自动校验唯一性
- **Label（英文标签）**：可编辑文本框
- **Chinese Label（中文标签）**：可编辑文本框
- **Type（字段类型）**：下拉选择器（text / select / textarea / steps），切换类型自动清理/初始化 Options
- **Options（选项值）**：仅在 `type === 'select'` 时显示，逗号分隔输入，自动同步为字符串数组
- **Visible / Required**：pill 开关切换
- **删除字段**：每行右侧删除按钮，至少保留 1 个字段（底部 Add Field 新增）
- **Add Field**：底部按钮插入新字段行（自动生成唯一 key，默认值 New Field / 新字段 / text 类型）
- **规则集名称**：在编辑视图顶部可内联编辑（`input` 带底部边框聚焦样式）
- **保存**：清理 `optionsStr` 临时属性，非 select 类型 `options` 置为 `undefined`，select 类型至少保留 `['']`

### 4.8 Device Space (`src/views/device-space/DeviceSpacePage.vue`)

**实现**：
- **头部**：Large 标题 + "Scan Devices"（glass-card 按钮）+ "Connect ADB"（渐变玻璃按钮）
- **Bentō Grid（12 列）**：
  - **左栏（4 列）**：设备列表
    - 活动设备卡片（`glass-card-active` + 状态脉冲 + 遥测数据）
    - 非活动设备卡片（`glass-card` + 半透明内容）
    - 每项包含：设备名、状态文本、OS 版本、地址、图标
  - **右栏（8 列）**：
    - **遥测仪表盘**（3 列子网格）：CPU / RAM / 电池
      - 每项：glass-card + 底部渐变 + 数值 + 进度条（secondary 颜色 + glow shadow）
    - **ADB 工具 Tab 切换**：Logcat / Shell / APK / Files / Screen
    - **Logcat 终端**：
      - 头部：标题 + 级别按钮（Verbose/Debug/Error）+ 筛选输入 + 清除按钮
      - 主体：暗色背景（`#1a1c1d/5`）+ 等宽字体 + 时间戳/级别/标签/消息格式
      - Error 行红色背景 + 左边框
      - 底部渐变淡出遮罩
    - **ADB Shell**：
      - 输入框 + Run 按钮，模拟终端输出
    - **APK Manager**：
      - 安装/卸载按钮 + 已安装应用列表
    - **File Manager**：
      - Push/Pull 按钮 + 提示文本
    - **Screenshot & Recording**：
      - 截图按钮 + 录制/停止按钮 + 截图预览
- **连接对话框**（Teleport）：玻璃面板浮层 + USB/TCP/IP 切换 + IP 输入 + 连接按钮

### 4.9 Notes Space (`src/views/note-space/NotesSpacePage.vue`)

**实现（Phase 2 — 完整 TipTap 集成）**：
- **三面板布局**：
  - **左（256px）**：玻璃面板目录树
    - 文件夹/文件图标 + 嵌套缩进 + 选中高亮（`bg-white/40`）
    - 文件夹展开/折叠（`expanded` 状态）
    - "Create New Folder" / "New file" 按钮
    - 删除文件夹/文件按钮（hover 显示）
    - 点击文件时切换编辑器内容
  - **中（flex-1）**：完整 TipTap 富文本编辑器
    - **工具栏**（14 个按钮，分区）：
      - 文字样式：Bold / Italic / Underline / Strike
      - 标题层级：H1 / H2 / H3
      - 列表：Bullet List / Ordered List / Blockquote / Code Block
      - 插入：Link（弹窗输入 URL）/ Image（文件选择器转 base64）
      - 撤销 / 重做
    - **状态指示**：选中格式时按钮高亮（`editor.isActive()`），保存状态显示 "Saved"（绿色）/ "Unsaved"（脉冲）
    - **自动保存**：编辑触发 `onUpdate`，设置内容到对应文件对象，2s 后标记为已保存
    - **ProseMirror 扩展**：StarterKit + Underline + Link + Image + Placeholder + Typography
    - 内容区：`max-w-3xl` 居中 + prose 样式（H1/H2/H3/P/UL/OL/Blockquote/Code/Pre/Link）
  - **右（288px）**：上下文 & 链接面板
    - Entities Mentioned（动态从当前文件读取标签 chips + secondary-fixed 背景）
    - Linked Issues（从当前文件读取卡片列表 + bug_report/task_alt 图标）
- **内容管理**：每个文件对象存储 HTML 内容（`file.content`），切换文件时通过 `editor.commands.setContent()` 恢复

### 4.10 Platform Space - Analytics (`src/views/platform-space/analytics/AnalyticsPage.vue`)

**实现**：
- **统计卡片**：4 列网格（Page Views / Active Users / Interactions / Avg. Session）
  - 每项：图标 + 大数字 + 趋势百分比（绿色 ↑ / 红色 ↓）
- **Usage Trends**：ECharts 占位区域（API: `GET /analytics/trend`）
- **Feature Usage**：功能使用率进度条（Case Management / Execution / Report 等）
- **Active Users**：占位区域（API: `GET /analytics/execution-stats`）

### 4.11 Platform Space - Database (`src/views/platform-space/database/DatabasePage.vue`)

**实现**：
- **视图切换器**：Table Browser / SQL Editor
- **Table Browser**：
  - 左侧表名列表（可搜索）+ 右侧数据区域
  - 表搜索 + "Row" 和 "SQL" 快捷按钮
- **SQL Editor**：
  - Monaco Editor 风格文本区域（textarea 版）
  - "Run (Ctrl+Enter)" 按钮 + "History" 按钮
  - 查询结果表格（列名 + 行数据）
- **安全机制**：危险 SQL（DELETE/UPDATE/TRUNCATE/DROP）触发确认对话框
  - 红色警告图标 + 提示信息 + "Execute Anyway" / "Cancel" 按钮

### 4.12 Platform Space - Version Release (`src/views/platform-space/version-release/VersionReleasePage.vue`)

**实现**：
- **版本列表**：glass-card 列表
  - 版本号（首字母 + 色块徽标）
  - 状态标签（Published 绿色 / Draft 灰色）
  - Changelog 项目（type 颜色编码：new 绿色 / fix 橙色 / improve 蓝色 / delete 红色）
  - 底部：创建时间 + 发布时间
  - "Publish" 按钮（draft 状态时可用）+ "More" 菜单
- **新建对话框**（Teleport）：
  - 版本号输入 + 标题输入 + 动态 Changelog 列表（类型选择 + 描述输入 + 删除）
  - "Create Version" 按钮

### 4.13 Script Space (`src/views/script-space/ScriptSpacePage.vue`)

**实现（Phase 2 — 完整脚本执行）**：
- **分类卡片**：3 列网格（Python / Shell-CMD / PowerShell），每类显示脚本数量列表
  - 点击卡片选中分类（高亮边框 `ring-2 ring-primary`），再次点击取消
- **执行面板**：
  - **输入区**：命令输入框 + "Run" 按钮（执行 Shell 命令）+ "Browse" 按钮（通过 `@tauri-apps/plugin-dialog` 打开文件选择器）
  - **文件选择**：打开系统对话框选择 `.py` / `.bat` / `.cmd` / `.ps1` / `.sh` 文件
  - **自动检测类型**：根据文件扩展名选择对应的 Rust 后端命令（Python / BAT / PowerShell / Shell）
  - **终端输出**暗色终端区域（`#1a1c1d` 背景 + 等宽字体 + 滚动）
    - 输入命令以绿色 `$` 前缀显示
    - stdout 白色文字，stderr 红色文字
    - 退出码显示 `[Exit code: N]`
    - 执行中显示脉冲动画指示器
  - **清除按钮**：清空终端输出
- **后端对接**：通过 `useScriptExec` composable 调用 Rust 原生命令
  - `executeShell(command)` — 任意 Shell 命令
  - `executePython(scriptPath, args)` — Python 脚本
  - `executeBat(scriptPath, args)` — BAT 脚本
  - `executePowershell(scriptPath, args)` — PowerShell 脚本

### 4.14 Settings (`src/views/settings/SettingsPage.vue`)

**实现**：
- **Profile**：头像首字母 + 用户名 + 邮箱 + 用户名/角色信息
- **Appearance**：Light / Dark 主题切换
- **Platform Connection**：服务器 URL 显示 + 连接状态指示（绿色圆点 + "Connected"）
- **Sign Out**：带 error 颜色的退出按钮，清除 Token 后跳转登录页

---

## 五、Rust 原生层

### 5.1 ADB 模块 (`src-tauri/src/adb.rs`)

**实现的 Tauri 命令**：

| 命令 | 函数 | 说明 | 底层调用 |
|------|------|------|----------|
| `adb_list_devices` | `list_devices()` | 列出已连接设备（含 model 和 android_version） | `adb devices -l` |
| `adb_shell` | `shell_command(serial, command)` | 在指定设备执行 shell 命令 | `adb -s <serial> shell <command>` |
| `adb_install` | `install_apk(serial, apk_path)` | 安装 APK（-r 覆盖安装） | `adb -s <serial> install -r <path>` |
| `adb_uninstall` | `uninstall_apk(serial, package)` | 卸载应用 | `adb -s <serial> uninstall <pkg>` |
| `adb_push` | `push_file(serial, local, remote)` | Push 文件到设备 | `adb -s <serial> push <local> <remote>` |
| `adb_pull` | `pull_file(serial, remote, local)` | 从设备 Pull 文件 | `adb -s <serial> pull <remote> <local>` |
| `adb_reboot` | `reboot(serial)` | 重启设备 | `adb -s <serial> reboot` |
| `adb_screenshot` | `screenshot(serial, save_path)` | 截图并保存到本地 | `adb -s <serial> exec-out screencap -p` |

### 5.2 串口模块 (`src-tauri/src/serial_port.rs`)

**实现的 Tauri 命令**：

| 命令 | 说明 | 底层 |
|------|------|------|
| `serial_list_ports` | 列出可用串口 | `serialport::available_ports()` |
| `serial_connect(port_name, baud_rate)` | 连接串口 | `serialport::new(port_name, baud_rate)` |
| `serial_disconnect` | 断开串口连接 | 清除 State 中的 Port |
| `serial_send(command)` | 发送串口命令 | `port.write(command.as_bytes())` |
| `serial_read` | 读取串口数据 | `port.read(&mut buf)` |

**状态管理**：使用 Tauri State 管理 `SerialState { port: Mutex<Option<Box<dyn SerialPort>>> }`，在 `lib.rs` 中通过 `.manage(SerialState {...})` 注册。

### 5.3 脚本执行模块 (`src-tauri/src/script_exec.rs`)

**实现的 Tauri 命令**：

| 命令 | 说明 | 底层调用 |
|------|------|----------|
| `script_execute_python(script_path, args)` | 执行 Python 脚本 | `python <script_path> <args>` |
| `script_execute_bat(script_path, args)` | 执行 BAT 脚本 | `cmd /c <script_path> <args>` |
| `script_execute_powershell(script_path, args)` | 执行 PowerShell 脚本 | `powershell -ExecutionPolicy Bypass -File <path>` |
| `script_execute_shell(command)` | 执行任意 Shell 命令 | `cmd /c <command>` |

### 5.4 入口和命令注册 (`src-tauri/src/lib.rs`)

```rust
// 所有命令通过 generate_handler! 宏注册
.invoke_handler(tauri::generate_handler![
    adb_list_devices, adb_shell, adb_install, adb_uninstall,
    adb_push, adb_pull, adb_reboot, adb_screenshot,
    serial_list_ports, serial_connect, serial_disconnect,
    serial_send, serial_read,
    script_execute_python, script_execute_bat,
    script_execute_powershell, script_execute_shell,
])
```

---

## 六、前端 Composable

### 6.1 `useAdb` (`src/composables/useAdb.ts`)

封装 Tauri `invoke` 调用，提供类型安全的 ADB 操作接口：

```typescript
const { listDevices, shell, installApk, uninstallApk, pushFile, pullFile, reboot, screenshot } = useAdb();
```

### 6.2 `useSerial` (`src/composables/useSerial.ts`)

封装串口操作：

```typescript
const { listPorts, connect, disconnect, send, read } = useSerial();
```

### 6.3 `useTestCaseStore` (`src/composables/useTestCaseStore.ts`)

共享测试用例数据和字段规则状态，支持跨页面（列表页 + 编辑器 + 字段规则页）同步：

```typescript
// 状态
const { testCases, fileName, fieldRuleSets, activeFieldRules }
// 测试用例 CRUD
const { setTestCases, addTestCase, updateTestCase, removeTestCase }
// 字段规则集 CRUD（含 FieldRuleSet 类型）
const { addFieldRuleSet, updateFieldRuleSet, removeFieldRuleSet, setActiveFieldRules, getVisibleFields }
// 字段级操作（FieldRuleSet 内单个字段的增删改）
const { addFieldToRuleSet, removeFieldFromRuleSet, updateFieldInRuleSet, reorderFieldsInRuleSet, availableFieldKeys }
```

### 6.4 `useScriptExec` (`src/composables/useScriptExec.ts`)

封装脚本执行：

```typescript
const { executePython, executeBat, executePowershell, executeShell } = useScriptExec();
```

---

## 七、设计规范引用

本项目的 UI/UX 设计严格遵循 `D:\TestSpace\stitch_liquid_glass_spatial_ui` 中的规范：

| 设计文件 | 对应实现 |
|----------|----------|
| `liquid_glass/DESIGN.md` | `tailwind.config.ts` 设计 Token + `src/styles/main.css` 玻璃态类 |
| `workspace_refined_lavender_edition/code.html` | `src/views/workspace/WorkspacePage.vue` |
| `case_space_refined_lavender_edition/code.html` | `src/views/case-space/CaseSpacePage.vue` |
| `device_space_refined_lavender_edition/code.html` | `src/views/device-space/DeviceSpacePage.vue` |
| `notes_space_refined_lavender_edition/code.html` | `src/views/note-space/NotesSpacePage.vue` |

---

## 八、平台 API 引用

Test Space 作为桌面客户端，所有业务数据来源于现有测试平台后端 API（位于 `D:\TestSpace\testcase_management`）。以下为已集成的 API 端点：

| 平台 API | Test Space 使用位置 | 状态 |
|----------|---------------------|------|
| `GET /captcha` | `Login.vue` 验证码加载 | ✅ 已集成 |
| `POST /auth/login` | `Login.vue` 登录 | ✅ 已集成 |
| `POST /auth/logout` | 待集成 | 📋 Phase 2 |
| `POST /auth/refresh` | `request.ts` 滑动续期 | ✅ 已集成 |
| `GET /auth/me` | 待集成用户信息加载 | 📋 Phase 2 |
| `GET /dashboard/v2/stats` | `dashboard.ts` fetchDashboardStats | ✅ API 模块 |
| `GET /dashboard/v2/quick-actions` | `dashboard.ts` fetchQuickActions | ✅ API 模块 |
| `GET /dashboard/v2/projects` | `dashboard.ts` fetchProjects | ✅ API 模块 |
| `GET /testcases` | `testcases.ts` fetchTestCases | ✅ API 模块 |
| `POST /testcases` | `testcases.ts` createTestCase | ✅ API 模块 |
| `PUT /testcases/{id}` | `testcases.ts` updateTestCase | ✅ API 模块 |
| `DELETE /testcases/{id}` | `testcases.ts` deleteTestCase | ✅ API 模块 |
| `GET /version-releases` | `version-releases.ts` fetchVersions | ✅ API 模块 |
| `POST /version-releases` | `version-releases.ts` createVersion | ✅ API 模块 |
| `POST /version-releases/{id}/publish` | `version-releases.ts` publishVersion | ✅ API 模块 |
| `DELETE /version-releases/{id}` | `version-releases.ts` deleteVersion | ✅ API 模块 |
| `GET /database/tables` | `database.ts` fetchTables | ✅ API 模块 |
| `GET /database/tables/{name}/data` | `database.ts` fetchTableData | ✅ API 模块 |
| `POST /database/sql` | `database.ts` executeQuery | ✅ API 模块 |
| `GET /analytics/stats` | `analytics.ts` fetchAnalyticsStats | ✅ API 模块 |
| `GET /analytics/trend` | `analytics.ts` fetchUsageTrend | ✅ API 模块 |
| `GET /analytics/feature-usage` | `analytics.ts` fetchFeatureUsage | ✅ API 模块 |
| `GET /analytics/active-users` | `analytics.ts` fetchActiveUsers | ✅ API 模块 |
| `POST /behavior-tracker/track` | 埋点追踪 | 📋 Phase 3 |

---

## 九、文件持久化

### 9.1 `useFilePersistence` (`src/composables/useFilePersistence.ts`)

本地文件持久化 composable，支持 Tauri 原生文件系统和开发模式双路径：

```typescript
const { savedFilePath, isDirty, saveToFile, loadFromFile, saveAs, clearPath } = useFilePersistence()
```

**工作模式**：
- **Tauri 模式**（`window.__TAURI__` 存在）：使用 `@tauri-apps/plugin-dialog` 打开原生文件对话框，通过 `@tauri-apps/plugin-fs` 读写 `.json` 文件
- **开发模式降级**：使用 `localStorage['test-space:localData']` 存储 JSON 字符串

**关键函数**：

| 函数 | 说明 |
|------|------|
| `saveToFile(data, filePath?)` | 保存数据到文件。无路径时先弹出"另存为"对话框，路径存 `localStorage['test-space:lastFilePath']` |
| `loadFromFile(filePath?)` | 从文件加载数据。无路径时弹出"打开"对话框 |
| `saveAs(data)` | 强制弹出"另存为"对话框，切换保存路径 |
| `pickSavePath()` / `pickOpenPath()` | 仅弹出对话框返回路径，不执行读写 |
| `clearPath()` | 清除记忆的路径 |
| `markDirty()` | 标记数据未保存 |

**持久化数据格式**（`PersistenceData`）：
```typescript
interface PersistenceData {
  version: number        // 数据版本号
  testCases: any[]      // 测试用例列表
  fieldRuleSets: any[]  // 字段规则集（预留）
  exportedAt: string    // 导出时间 ISO 字符串
}
```

**自动加载流程**：
1. 应用启动时 `CaseSpaceLayout.onMounted` 检查 `localStorage['test-space:lastFilePath']`
2. 若存在路径，自动调用 `loadFromFile()` 恢复 `testCases`
3. Excel 导入完成后自动触发 `saveFile()` 持久化

### 9.2 权限配置

`src-tauri/capabilities/default.json` 添加：
- `"fs:default"` — 文件系统读写权限
- `"dialog:default"` — 原生对话框权限

`src-tauri/tauri.conf.json` 已配置 `fs.scope: ["**"]`（允许任意路径）。

---

```bash
# 启动开发模式（前端 Vite + Tauri）
npm run tauri dev

# 仅启动前端开发服务器
npm run dev

# 构建生产版本
npm run tauri build

# 检查 TypeScript 类型
npx vue-tsc --noEmit

# 构建前端
npm run build
```

### 环境要求

- Node.js >= 18
- Rust >= 1.77.2
- Visual Studio 2022 Build Tools（含 VC++ 工具集）
- ADB（Android Debug Bridge，用于 ADB 功能）

---

## 十、分阶段计划

### Phase 1（已完成 ✅）

| 模块 | 状态 |
|------|------|
| 项目脚手架（Tauri 2 + Vue 3 + TailwindCSS + Router + Pinia） | ✅ |
| 设计系统（玻璃态 CSS + 设计 Token + 字体/图标） | ✅ |
| 布局组件（AppLayout / Sidebar / TopNav / PlatformLayout） | ✅ |
| 认证系统（Login + Axios 拦截器 + 导航守卫） | ✅ |
| Workspace 首页 | ✅ |
| Case Space（Table / MindMap / Document 视图） | ✅ |
| Device Space（设备列表 + 遥测 + Logcat + ADB Shell/APK/Files/Screen） | ✅ |
| Settings | ✅ |
| Platform Space 二级导航布局 | ✅ |
| Notes Space（三面板 + 编辑器 + 目录树 + 上下文面板） | ✅ |
| Script Space | ✅ |
| Analytics / Database / Version Release 页面 | ✅ |
| Rust 原生层（ADB / 串口 / 脚本执行） | ✅ |

### Phase 2（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Notes Space TipTap 集成 | 替换 contenteditable 为 TipTap 富文本编辑器（Bold/Italic/Underline/Strike/H1/H2/H3/Lists/Blockquote/Code/Link/Image/Undo/Redo + Placeholder + BubbleMenu） | ✅ |
| Script Space 完整功能 | 脚本分类列表 + 命令输入 + 文件选择器（通过 tauri-plugin-dialog）+ Rust 后端执行 + 暗色终端实时输出 | ✅ |
| API 数据层 | 6 个 API 模块：dashboard / testcases / version-releases / database / analytics / notes | ✅ |
| Workspace API 对接 | Workspace 首页从 `fetchDashboardStats` / `fetchQuickActions` / `fetchProjects` 加载数据 | ✅ |
| Case Space API 对接 | Case Space 从 `fetchTestCases` 加载用例列表 | ✅ |
| Version Release API 对接 | 版本创建/发布通过 `createVersion` / `publishVersion` API | ✅ |
| Database API 对接 | 表列表 + SQL 执行通过 `fetchTables` / `executeQuery` API | ✅ |
| Analytics API 对接 | 统计面板 + Feature Usage 通过 `fetchAnalyticsStats` / `fetchFeatureUsage` API | ✅ |

### Phase 3（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Analytics 图表 | ECharts 渲染 Usage Trends（平滑折线图 + 渐变面积） + Active Users（折线面积图）+ 时间段切换 | ✅ |
| Analytics 统计卡片 | 实时统计面板（Page Views / Active Users / Interactions / Avg. Session）+ 趋势百分比 | ✅ |
| Device Space ADB 对接 | `scanDevices` → `listDevices()` ADB 扫描 / `executeShell` → `shell()` 命令执行 / APK Install → `installApk()` 文件选择器 / Uninstall → `uninstallApk()` / Screenshot → `screenshot()` / File Push/Pull → `pushFile()`/`pullFile()` / Logcat 筛选 | ✅ |
| Case Space New Case | 新建用例对话框（Module / Title / Priority / Status）+ `createTestCase` API 对接 | ✅ |
| Database 表数据浏览 | 点击表名自动加载数据表格（`fetchTableData`），列名 + 行数据渲染，API 失败回退 mock | ✅ |

### Phase 4（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Case Space 多页路由重构 | `/case-space` 改为嵌套路由，新增 `CaseSpaceLayout.vue` 二级导航 + `editor/` 和 `field-rules/` 子路由 | ✅ |
| 新建用例弹窗流程 | `+` 按钮 + 空状态按钮统一触发 CustomEvent → 弹窗填写文件名 + 选择字段规则 → 带 query 跳转编辑器 | ✅ |
| 用例卡片网格视图 | `CaseSpacePage.vue` 重写为卡片网格（`grid-cols-3`），删除二次确认（Teleport 红色警告对话框） | ✅ |
| 电子表格编辑器 | `CaseEditorPage.vue`：动态列来自字段规则，select/textarea 就地编辑，Columns/Row 管理，空状态提示 | ✅ |
| 思维导图视图 | Table↔Mind Map 切换，左根节点 + 右字段 + 右步骤 + SVG 贝塞尔连接线 + 缩放控件 | ✅ |
| 字段规则集管理 | `FieldRulesPage.vue`：规则集卡片网格，创建/编辑/删除多个具名规则集，Default Fields 不可删除，二次确认 | ✅ |
| 字段级编辑 | 编辑视图表格：可新增/删除字段，编辑 Key/Label/ChineseLabel/Type/Options（select 类型逗号分隔），自动键名唯一性校验，保存时清理临时属性 | ✅ |
| `useTestCaseStore` 扩展 | 新增 `FieldRuleSet` 类型 + CRUD + 字段级操作（`addFieldToRuleSet` / `removeFieldFromRuleSet` / `updateFieldInRuleSet` / `reorderFieldsInRuleSet`） | ✅ |
| `.glass-button` 全局统一 | 所有按钮使用玻璃毛边液态透明样式（深色文字），hover 浅紫色背景 + scale(1.08) + 四层阴影呼吸动画 | ✅ |
| `.glass-hover` / `.glass-active` CSS 类 | `.glass-hover`：通用紫色 hover 效果（`!important` + scale(1.05) + 四层阴影 + 呼吸），用于非按钮交互元素；`.glass-active`：选中态紫色渐变填充，替换 `bg-secondary-fixed` 模式 | ✅ |
| **全应用交互元素统一** | 所有 15 个 `.vue` 文件中的 ~90 个交互元素统一为 `.glass-button` / `.glass-hover` / `.glass-active` 样式 |
| 导航栏 | **Sidebar.vue** 7 个导航项 + Settings 链接：添加 `glass-hover`，活跃态替换为 `glass-active` | ✅ |
| 顶部导航 | **TopNav.vue** 消息/帮助/用户 3 个按钮 → `glass-button` | ✅ |
| Tab 页签切换器 | **CaseSpaceLayout** / **PlatformLayout** / **CaseEditorPage** / **DeviceSpacePage** / **DatabasePage** / **SettingsPage** 所有 tab 切换器：非活跃态 `glass-button`，活跃态 `glass-active` | ✅ |
| 卡片式交互 | **WorkspacePage** 快捷操作卡片 / **ScriptSpacePage** 分类卡片 / **DeviceSpacePage** 设备卡片 / **CaseSpacePage** 用例卡片 / **FieldRulesPage** 创建卡片 / **NotesSpacePage** 文件夹/文件/实体标签/问题卡片：添加 `glass-hover` | ✅ |
| 编辑器工具栏 | **NotesSpacePage** 15 个 TipTap 工具栏图标按钮 → `glass-button`，active 态切换为 `glass-active` | ✅ |
| 图标按钮 & 对话框 | 所有关闭/删除/取消/确认/返回/缩放图标按钮 → `glass-button`；危险操作按钮（删除确认）保留 `bg-error/10 text-error` 但使用 `glass-button` 框架 | ✅ |
| 登录页 Dev Mode | 开发模式跳过按钮 → `glass-button` | ✅ |
| 导入图标修正 | `file_upload` → `file_download`（朝下） | ✅ |
| 卡片清理 | 移除 Level 标签、Status 状态文字、Uncategorized 默认文案（改为 `v-if` 条件渲染），清理无用 `levelClass`/`statusDotClass`/`statusLabel` 函数 | ✅ |

### Phase 5（进行中）

| 模块 | 说明 | 状态 |
|------|------|------|
| 本地文件持久化 | `useFilePersistence` composable：支持 Tauri 原生 `fs` + `dialog` 插件（生产模式）和 `localStorage` 降级（开发模式）双路径 | ✅ |
| 保存/打开按钮 | CaseSpaceLayout 工具栏新增 `folder_open`（打开文件）+ `save`（保存到文件）按钮，保存时弹出原生文件对话框选择 `.json` 路径 | ✅ |
| 自动加载 | 应用启动时从上次保存路径自动恢复数据（路径存 `localStorage['test-space:lastFilePath']`） | ✅ |
| 导入后自动保存 | Excel 导入完成后自动触发 `saveFile()`，确保导入数据立即持久化 | ✅ |
| `@tauri-apps/plugin-fs` 安装 | npm 依赖 + `capabilities/default.json` 添加 `"fs:default"` 和 `"dialog:default"` 权限 | ✅ |
| 数据模型简化 | 移除 `CaseStep` 接口，`CaseItem.steps` 从 `CaseStep[]` 改为 `string`，新增 `CaseItem.expected: string`；步骤/前置/预期均为独立 textarea 列 | ✅ |
| 模板字段完整应用 | `CaseSpacePage.confirmNew` 不再过滤模板字段，全部存入 `file.customFields`，key 映射：`name→title`、`level→priority`、`steps→textarea` | ✅ |
| 列顺序与渲染 | `CaseEditorPage.visibleCols` 改为模板列优先（`customCols + 非重叠默认列`）；优先级下拉用 `col.options` 取代硬编码 P0-P3；通用 v-else 按 `col.type` 分发 select/text/textarea 三种渲染 | ✅ |
| 列去重 | `CaseEditorPage.columns` 和 `visibleCols` 均跳过与自定义列 key 重叠的默认列，避免模板和默认列重复显示 | ✅ |
| 严格按模板显示列 | `visibleCols`：有模板时只显示模板字段（`custom`），不附加任何默认列；无模板时回退 `defaultColumns` | ✅ |
| 默认模板预选 | 新建对话框 `newCaseRule` 默认 `'default'`，确认后重置也为 `'default'`，无需手动点开下拉框 | ✅ |
| 模板字段拖拽排序 | FieldRulesPage 字段编辑表格添加 HTML5 drag-and-drop，拖拽时行半透明、目标行高亮 | ✅ |
| 简化 FieldRulesPage 编辑 | 去掉 Key、Label 列，只剩 Field Name（`labelCn`），Key 自动从标题 slugify 生成；类型选项仅 `textarea`/`select`，去除 `text`/`steps` | ✅ |
| 默认模板更新 | 改为：用例编号、所属模块、用例标题、前置条件、操作步骤、预期结果、用例等级(L1-L4)、自动化(Y/N)、备注 | ✅ |
| 用例编号自动生成 | `addCase`/`addCaseAt` 检测文件有 `case_number` 字段时自动填入递增序号 | ✅ |
| 列拖拽调整大小 | 表头右侧添加 `cursor-col-resize` 拖拽手柄，`colWidths` 记录宽度，最小 80px，`<th>`/`<td>` 同步应用 | ✅ |
| textarea 自动撑高（防止虚滚折叠） | 挂载时通过 `:ref` + `initTextarea`（`requestAnimationFrame` 布局后测量 `scrollHeight`）自动撑高；输入时 `onTextareaInput` 同步 resize；CSS `field-sizing: content` 作为现代浏览器原生方案 | ✅ |
| 虚滚滚动时测量新行高度 | `onBodyScroll` 中新增 `observeRenderedRows()` 调用，确保每次新建行都被测量和注册 ResizeObserver | ✅ |
| 测量前先撑高 textarea | `observeRenderedRows()` 先遍历 textarea 执行 `height=auto;height=scrollHeight`，再读行 `offsetHeight`（强制同步布局包含撑高结果），防止错误行高写入 `measuredHeights` | ✅ |
| 初始加载双 rAF 测量 | `onMounted` 改用双重 `requestAnimationFrame`（等 `initTextarea` 的 rAF 撑高完成 + 布局结算后），再测行高和校正虚拟滚动位置 | ✅ |
| SQLite 本地持久化 | 所有数据通过 `@tauri-apps/plugin-sql`（SQLite）存储在 `{appDataDir}/test-space.db`，替代 localStorage | ✅ |
| 数据迁移（localStorage→SQLite） | 旧数据保留在 localStorage（不自动迁移）；新数据全部写入 SQLite | ✅ |
| 200 空行模式（类 Excel） | 编辑器自动显示 200 行，用户直接输入无需点击"新增行"；保存/导出只输出有内容行（`hasContent()` 检查 title/steps/expected 等实际字段） | ✅ |
| 虚拟行性能优化 | 200 行中真实行才存入响应式 Store，空余行用轻量 `{ id, _virtual: true }` 占位；CSS Grid（`gridTemplateColumns`）+ 绝对定位叠加渲染，scroll 滚动驱动 `updateVirtualRows` 更新可视行；`measuredHeights` Map 记录每行真实高度，未测量行回退 `ROW_ESTIMATE=48px` | ✅ |
| 虚滚滚动时自动测量并观测新行 | 每次滚动 `onBodyScroll` → rAF → `updateVirtualRows()` 后必须调用 `observeRenderedRows()`，对新行执行：① 撑高 textarea ② 测量 `offsetHeight` 写入 `measuredHeights` ③ 设置 ResizeObserver。缺少此调用会导致新行始终无高度测量，`updateVirtualRows` 始终用 `ROW_ESTIMATE`，累计偏差使越下行越挤压 | ✅ |
| 删除单元格提示文本 | 所有 `placeholder` 属性从表格单元格中移除（module/text/textarea/tags），无干扰提示 | ✅ |
| 默认值清零 | `priority` 字段不再默认 `'P2'`，新建行优先级为空；`<select>` 首项为 `<option value="">--</option>` | ✅ |
| 列头筛选/排序 | 每个表头右侧 `filter_list` 图标 → 浮层支持升序/降序排序 + 按值多选过滤，类似 WPS Excel；筛选后虚拟行隐藏，排序基于筛选结果 | ✅ |
| 键盘快捷键 | `Ctrl+S` / `Cmd+S` 触发保存，与 Save 按钮行为一致 | ✅ |

---

## 十一、用户使用习惯与设计要求

以下记录本应用在迭代过程中确立的用户偏好和设计原则，所有新功能开发必须遵守。

### 11.1 Excel 式编辑体验

| # | 原则 | 说明 | 违反示例 |
|---|------|------|----------|
| 1 | **即时可写** | 进入编辑器后表格直接可写，无需先点"新增行"。自动填充 200 个空行占位 | ❌ 点击 "+" 才能出现输入框 |
| 2 | **只存内容** | 保存/导出只保留有实际内容的行，空行（无论是否 200 行之一）不进入数据库和导出文件 | ❌ 保存了 200 个空行到数据库 |
| 3 | **无默认值** | 单元格不应有预设值。`priority` 默认空（而非 `'P2'`），所有 dropdown 首项为空选项 | ❌ 导出 Excel 时 priority 列全是 'P2' |
| 4 | **无提示文字** | 单元格内不应有 placeholder 提示文本，保持界面干净 | ❌ `placeholder="Enter title"` |

### 11.2 性能

| # | 原则 | 说明 |
|---|------|------|
| 5 | **进入无卡顿** | 打开编辑器页面不应有明显延迟。不允许在 `onMounted` 中同步创建 200 个响应式对象 |
| 6 | **操作流畅** | 复制行、筛选等操作不应卡顿。真实数据行（通常 < 50）存入 Store，空余行用轻量虚拟对象 `{ _virtual: true }` 代替完整 CaseItem |

### 11.3 交互

| # | 原则 | 说明 |
|---|------|------|
| 7 | **WPS/Excel 列头筛选** | 每列表头必须提供筛选/排序功能：点击图标弹出浮层，支持升序/降序 + 按值多选过滤 |
| 8 | **Ctrl+S 保存** | `Ctrl+S` / `Cmd+S` 必须拦截并触发 Save 功能，阻止浏览器默认"另存为" |

### 11.4 数据

| # | 原则 | 说明 |
|---|------|------|
| 9 | **SQLite 唯一存储** | 所有数据存 SQLite（`{appDataDir}/test-space.db`），禁止 localStorage |
| 10 | **导出/导入必须完整** | 新增数据表或字段后，必须同步更新 `database.ts` 的 `exportAllData()` / `importAllData()` |

---

### 存储架构（持久化规则）

所有数据统一通过 SQLite 存储在用户的应用数据目录，**禁止**使用 localStorage（仅 dev 模式下文件读写降级）。

#### 数据库位置

- **Windows**: `%APPDATA%/com.testspace.app/test-space.db`
- **macOS**: `~/Library/Application Support/com.testspace.app/test-space.db`
- **Linux**: `~/.local/share/com.testspace.app/test-space.db`
- **开发模式**（浏览器 fallback）：页面数据从 `@tauri-apps/plugin-sql` 读取，若不可用则回退到 dev 文件读写

#### 数据表结构

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `field_rule_sets` | 字段模板规则集 | `id`, `name`, `rules`(JSON), `created_at`, `updated_at` |
| `case_files` | 编写的用例文件 | `id`, `name`, `data`(全量 JSON), `tags`(JSON), `custom_fields`(JSON), `rule_set_id`, `created_at`, `updated_at` |
| `recent_files` | 打开历史记录 | `path`, `name`, `case_count`, `last_opened` |
| `favorites` | 收藏的文件 | `path`, `added_at` |
| `app_settings` | 应用设置（K/V） | `key`, `value` |

#### 分层架构

```
UI 组件 (Vue)
    ↓
Pinia Store / Composable
    ↓
src/services/database.ts  ←── 唯一的数据访问层
    ↓
@tauri-apps/plugin-sql (SQLite)
    ↓
{appDataDir}/test-space.db
```

#### 规则

1. **所有页面数据必须通过 `src/services/database.ts` 读写**，不得直接操作 localStorage 或文件系统
2. **新增表**必须先在 `database.ts` 的 `migrate()` 函数中添加 `CREATE TABLE IF NOT EXISTS`，然后导出对应的 CRUD 方法
3. **文件导出**（Save/Save As/Open）仍使用 `useFilePersistence` composable（基于 `@tauri-apps/plugin-dialog` + `plugin-fs`，仅供用户手动导出/导入 .tc 文件），不与 SQLite 冲突
4. **初始化时机**：`CaseSpacePage` 在 `onMounted` 中调用 `store.initStore()` 加载数据；`useTestCaseStore` 在模块加载时自动从 DB 读取 field rule sets
6. **新功能必须同步更新导出/导入**：每次新增数据表或修改数据结构后，必须同步更新 `database.ts` 中的 `exportAllData()` 和 `importAllData()`，确保新数据能被完整导出和恢复。缺少该步骤的 PR 不予合并。
