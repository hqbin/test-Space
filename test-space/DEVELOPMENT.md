# Test Space 开发文档

> **重要**：每次对项目进行更新或修改后，必须同步更新本文档。所有新增、修改或删除的功能都要在对应页面模块中描述清楚。本文档是项目的核心参考文件。
>
> **UI/UX 一致性守则**：凡新增或修改功能，其交互控件（按钮、标签页、导航项、卡片、图标操作区等）必须统一使用本文档定义的 `.glass-button` / `.glass-hover` / `.glass-active` CSS 类，禁用 `bg-primary-container`、`bg-secondary-fixed`（作为活跃态时替换为 `glass-active`）、`text-primary`（作为可点击文字时替换为 `glass-button`）等旧样式。新页面或新控件不得自创样式模式，必须继承现有的液态玻璃设计系统。所有改动的 UI 元素在提交前须通过 `npm run build` 确保无类型/样式回归。
>
> **弹窗/对话框守则**：所有 Teleport 弹窗必须遵循 4.4 节定义的弹窗规范，使用 `bg-black/30 backdrop-blur-sm` 背景遮罩 + `glass-panel rounded-[2rem] bg-white/60` 弹窗主体结构，禁止使用 `bg-black/10`、`bg-black/20`、`bg-black/50` 等其他深浅度的半透明背景。弹窗关闭按钮统一使用 `glass-button p-1 rounded` + `close` 图标。
>
> **功能安全守则**：每次修改已有代码时，必须评估改动的影响范围，确保不破坏相邻或依赖模块的既有功能。以"最小改动、最大兼容"为原则：优先做增量调整而非重构重写；修改公共模块（composable、API 层、store、路由守卫、布局组件）时须同时验证所有调用方是否仍正常工作；删除或重命名任何导出、路由、CSS 类或 API 字段前，必须全局搜索确认无其他引用。提交前执行 `npm run build` 通过类型检查和构建，并对修改涉及的功能路径做人工冒烟验证。
>
> **数据持久化守则**：只有真正需要跨会话持久化的业务数据和用户配置才写入 SQLite 数据库（`app_settings` 表或专用业务表）。临时性数据（如设备上次连接记录 `last_device_serial`、会话级状态等）应使用 `localStorage`，避免不必要的数据库写入。`localStorage` 还允许在非 Tauri 环境的开发降级方案中使用（如 `useFilePersistence.ts` 中 `isTauri() === false` 的 `else` 分支）。新增数据持久化时优先使用 `app_settings` 表的键值对模式（`getSetting`/`setSetting`），结构化数据需添加专用表并在 `migrateInternal` 中注册 `CREATE TABLE IF NOT EXISTS`，同时更新 `AppBackup`/`exportAllData`/`importAllData`/`validateBackup` 以纳入备份恢复流程。提交前须验证数据在应用重启后正确恢复。

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
| HTTP 客户端 | **@tauri-apps/plugin-http** | Rust 端 reqwest，绕过 CORS（云端备份） |
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
  @tiptap/extension-color ^2.27.2       — 字体颜色扩展（Notes Space）
  @tiptap/extension-text-style ^2.27.2  — 行内样式基座（Color 依赖）
  @tiptap/extension-table ^2.11.2     — 表格扩展
  @tiptap/extension-table-row ^2.11.2 — 表格行
  @tiptap/extension-table-cell ^2.11.2 — 表格单元格
  @tiptap/extension-table-header ^2.11.2 — 表格表头
  @tiptap/extension-code-block-lowlight ^2.27.2 — 代码块语法高亮
  lowlight ^3.x                   — highlight.js 轻量封装
  jspdf ^2.x                      — PDF 生成（Notes Space 导出）
  docx ^9.x                       — Word .docx 生成（Notes Space 导出）
  turndown ^7.x                   — HTML → Markdown 转换
  html-to-image ^1.11.13          — HTML 导出为图片（PDF 渲染）
  xlsx ^0.18.5                    — Excel 导入解析（Case Space）
  monaco-editor ^0.52.2           — 代码/SQL 编辑器
  pinia ^2.3.1                    — 状态管理
  vue ^3.5.13                     — 核心框架
  vue-router ^4.5.0               — 路由

开发依赖:
  @tauri-apps/api ^2.2.0         — Tauri 前端 API
  @tauri-apps/cli ^2.2.0         — Tauri CLI
  @tauri-apps/plugin-sql ^2.4.0  — SQLite 数据库插件
  @tauri-apps/plugin-dialog ^2.7.1 — 原生对话框插件
  @tauri-apps/plugin-fs ^2.5.1   — 文件系统插件
  @tauri-apps/plugin-http ^2     — HTTP 请求插件（云端备份）
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
tauri-plugin-single-instance 2   — 单实例（防止重复启动）
tauri-plugin-http 2              — HTTP 请求（绕过 CORS，用于云端备份）
http-mitm-proxy 0.18             — MITM 代理核心（HTTPS 解密，Phase 23）
rustls 0.23 (ring)               — TLS 加密库（代理 HTTPS，Phase 23）
regex 1                          — 正则表达式（重写规则匹配，Phase 23）
zip 2                            — ZIP 压缩（诊断包/文件夹打包，Phase 7）
encoding_rs 0.8                  — GBK 编码支持（Windows 中文输出，Phase 17）
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
│   ├── App.vue                         # 根组件（Ctrl+Tab 键盘快捷导航）
│   ├── env.d.ts                        # 类型声明
│   │
│   ├── styles/
│   │   └── main.css                    # TailwindCSS + 玻璃态 CSS 类 + 自定义滚动条
│   │
│   ├── types/
│   │   └── index.ts                    # 全局类型定义（UserInfo, DeviceInfo, LogEntry, ApiCapturedRequest 等）
│   │
│   ├── services/                         # 业务服务层
│   │   ├── database.ts                   # SQLite 数据库（CRUD + 迁移 + 备份导出导入）
│   │   ├── crypto.ts                     # AES-256-GCM 加密/解密 + PBKDF2 密钥派生
│   │   ├── cloudBackup.ts               # 云端备份 HTTP 客户端（Tauri HTTP 插件）
│   │   └── cloudSync.ts                 # 一键云端同步（exportAllData → 加密 → upload）
│   │
│   ├── stores/                         # Pinia 状态管理
│   │   └── caseFileStore.ts            # 用例文件状态管理
│   │
│   ├── router/
│   │   └── index.ts                    # 路由配置
│   │
│   ├── layouts/                        # 布局组件
│   │   ├── AppLayout.vue               # 主布局（Sidebar + 背景渐变 + <router-view />）
│   │   ├── CaseSpaceLayout.vue         # Case Space 二级导航（All Cases / Field Rules Tab + New Case 按钮）
│   │   ├── Sidebar.vue                 # 顶部浮动导航栏（触发区 + 滑出动画 + 云端同步按钮）
│   │   └── TitleBar.vue                # 标题栏（导航项 + 云端同步按钮 + 窗口控制，mirror 窗口使用）
│   │
│   ├── composables/                    # 可复用组合式函数
│   │   ├── useAdb.ts                   # ADB 操作（listDevices/shell/installApk 等）
│   │   ├── useSerial.ts                # 串口操作（listPorts/connect/send/read）
│   │   ├── useScriptExec.ts            # 脚本执行（Python/BAT/PowerShell）
│   │   ├── useScriptRunner.ts          # 脚本运行器（多标签终端 + 实时输出 + 进程管理）
│   │   ├── useTestCaseStore.ts         # 测试用例 + 字段规则状态管理
│   │   ├── useApiProxy.ts              # API 代理（MITM 代理控制 + 断点 + 重写规则）
│   │   ├── useFilePersistence.ts       # 文件持久化（Tauri fs + dialog / localStorage 降级）
│   │   └── useI18n.ts                  # 国际化（zh/en 双语，t() 翻译函数）
│   │
│   └── views/                          # 页面视图
│       ├── case-space/
│       │   ├── CaseSpacePage.vue       # 用例列表（卡片网格视图）
│       │   ├── editor/
│       │   │   └── CaseEditorPage.vue  # 用例编辑器（表格编辑 + 思维导图切换）
│       │   └── field-rules/
│       │       └── FieldRulesPage.vue  # 字段规则配置
│       ├── device-space/
│       │   ├── DeviceSpacePage.vue     # 设备空间（设备列表 + 遥测 + Logcat + ADB 工具）
│       │   └── StandaloneMirror.vue    # 独立屏幕镜像窗口（无侧栏，/mirror 路由）
│       ├── api-space/
│       │   └── ApiSpacePage.vue        # API 空间（MITM 代理 + 请求捕获 + 断点调试 + 重写规则）
│       ├── note-space/
│       │   └── NotesSpacePage.vue      # 笔记空间（文件树 + 富文本编辑器 + 上下文面板）
│       ├── script-space/
│       │   └── ScriptSpacePage.vue     # 脚本空间（分类 + 搜索 + 多标签终端）
│       └── settings/
│           └── SettingsPage.vue        # 设置页（语言 + 主题 + 数据管理 + 版本）
│
└── src-tauri/                          # Rust 原生层
    ├── Cargo.toml                      # Rust 依赖
    ├── tauri.conf.json                 # Tauri 配置（窗口、权限、插件）
    ├── build.rs                        # 构建脚本
    ├── windows/
    │   └── hooks.nsh                   # NSIS 安装程序钩子（防快捷方式重复）
    ├── capabilities/
    │   └── default.json                # Tauri 2 权限能力
    ├── icons/                          # 应用图标
    └── src/
        ├── main.rs                     # Rust 入口（#![windows_subsystem = "windows"]）
        ├── lib.rs                      # Tauri Builder + 所有命令注册
        ├── adb.rs                      # ADB 命令（devices/shell/install/push/pull/reboot/screenshot）
        ├── serial_port.rs              # 串口通信（list/connect/disconnect/send/read）
        ├── mirror.rs                   # 屏幕镜像（scrcpy-server H.264 + screencap 兜底）
        ├── proxy.rs                    # MITM 代理（http-mitm-proxy + HTTPS 解密 + 断点 + 重写）
        ├── script_exec.rs              # 脚本执行（Python/BAT/PowerShell/Shell）
        └── zip_util.rs                 # ZIP 工具（内存构建 ZIP 压缩包）
```

---

## 四、各模块实现说明

### 4.1 API 层（已移除）

本地桌面应用不涉及 HTTP 请求，所有数据通过 `src/services/database.ts`（SQLite）直接读写，无后端 API 层。

### 4.2 路由系统 (`src/router/index.ts`)

**路由表**：

| 路径 | 组件 | 说明 |
|------|------|------|
| `/` | `AppLayout.vue` | 嵌套子路由，默认 redirect 到 `/device-space` |
| `/case-space` | `CaseSpaceLayout.vue` → `CaseSpacePage.vue` | 用例空间（卡片列表） |
| `/case-space/editor` | `CaseEditorPage.vue` | 新建/编辑测试用例 |
| `/case-space/field-rules` | `FieldRulesPage.vue` | 字段规则配置 |
| `/device-space` | `DeviceSpacePage.vue` | 设备空间 |
| `/mirror` | `StandaloneMirror.vue` | 独立屏幕镜像窗口（无侧栏） |
| `/api-space` | `ApiSpacePage.vue` | API 空间（MITM 代理 + 请求捕获 + 断点调试） |
| `/notes-space` | `NotesSpacePage.vue` | 笔记空间 |
| `/script-space` | `ScriptSpacePage.vue` | 脚本空间 |
| `/settings` | `SettingsPage.vue` | 设置 |

### 4.3 布局系统

#### 4.3.1 AppLayout（主布局）

**实现**：
- 顶部浮窗导航（由 Sidebar 组件渲染，见 4.3.2）
- 主内容区 `<main>`：`px-margin-page pt-3 box-border flex-1 overflow-y-auto overflow-x-hidden min-h-0 flex flex-col`
  - `flex-1`：在外层 `h-screen flex flex-col` 中占满剩余高度（减去 TitleBar）
  - `flex flex-col`：提供 flex 列上下文，使子路由页面可以使用 `flex-1` / `min-h-0` 正确撑满高度（替代 `h-full` 百分比方案）
  - `overflow-y-auto`：纵向溢出时由 `<main>` 整体滚动（备用策略）
  - `overflow-x-hidden`：防止子页面的 `-mx-margin-page` 负边距产生水平滚动条
  - `min-h-0`：允许 flex 项收缩
- 每个 Space 有不同的背景径向渐变（通过 `route.path` 判断）

**背景渐变方案**：

| 页面 | 渐变 |
|------|------|
| Case Space | 左上角 lavender 渐变 + 右下角蓝色微光 |
| Device Space | 左中 secondary 微光 + 右中 primary 微光 |
| Notes Space | 顶部到下部渐变灰 |
| 其他 | 纯白 `#F9F9FB` |

#### 4.3.2 Sidebar → 顶部浮窗导航

**实现**：
- 不再是左侧固定 Sidebar（已移除），改为 **固定在顶部的浮动导航栏**
- 屏幕顶部有 8px 不可见触发区，鼠标移入后导航栏滑出
- 鼠标移出导航栏 1.5 秒后自动收起（有缓冲时间，悬停可暂停）
- 连接 `Transition` 动画：进入 `0.3s cubic-bezier(0.16,1,0.3,1)` + opacity 渐变，收起 `0.2s`
- `fixed` 定位，不占页面空间，不影响页面内容

**导航项**（按用户使用频率排序）：
Device → Notes → API → Scripts → Case → Settings（Settings 固定在右侧）

**云端同步快捷按钮**（Settings 右侧，`sync` 图标）：
- 点击执行与设置页「备份到云端」相同的流程（`syncBackupToCloud()`）
- 同步中：按钮 `sync` 图标 `animate-spin` 旋转 + 顶部居中 Toast「正在同步云端备份…」
- 成功/失败：顶部 Toast 显示 `check_circle` / `error` 图标 + 文案，5 秒后自动消失（不依赖 hover title）
- 实现位置：`Sidebar.vue`（主窗口顶栏）与 `TitleBar.vue`（`/mirror` 独立窗口）各一份，逻辑一致

**导航交互规则**：
- 当前活跃路由使用 `.glass-active` + `font-semibold` 样式
- 图标使用 Material Symbols，活跃态 `FILL 1`，非活跃态 `FILL 0`
- Case Space 使用 `path.startsWith()` 实现子路由高亮

### 4.4 设计系统 (`src/styles/main.css` + `tailwind.config.ts`)

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

**弹窗/对话框规范**（Teleport 模态框）：

所有弹窗必须使用以下统一结构，禁止使用半透明黑色背景 `bg-black/50`：

```html
<Teleport to="body">
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="close">
      <!-- 背景遮罩层 -->
      <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
      <!-- 弹窗主体 -->
      <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60 max-h-[80vh] flex flex-col">
        <!-- 标题栏 -->
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
            <span class="material-symbols-outlined text-[16px]">图标名</span>{{ 标题 }}
          </h3>
          <button class="glass-button p-1 rounded select-none" @click="close">
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>
        <!-- 内容区 -->
        <div class="flex-1 min-h-0 overflow-y-auto">
          <!-- 内容 -->
        </div>
        <!-- 底部按钮（可选） -->
        <div class="flex gap-2 justify-end pt-4 border-t border-outline-variant/30 mt-4">
          <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="close">取消</button>
          <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="confirm">确认</button>
        </div>
      </div>
    </div>
  </Transition>
</Teleport>
```

**样式要点**：
- 背景遮罩：`bg-black/30 backdrop-blur-sm`（30% 黑色 + 模糊，全应用统一）
- 弹窗主体：`glass-panel rounded-[2rem] p-6 bg-white/60`（玻璃面板 + 60% 白色背景）
- 最大宽度：`max-w-md`（普通弹窗）/ `max-w-2xl`（大内容弹窗如图片预览）
- 最大高度：`max-h-[80vh]` 或 `max-h-[85vh]`，内容区 `overflow-y-auto`
- 关闭按钮：`glass-button p-1 rounded`，使用 `close` 图标
- 标题栏：`font-label-md text-label-md font-semibold` + Material Symbols 图标

**下拉选择器规范**：

| 上下文 | 样式 | 说明 |
|--------|------|------|
| 弹窗/对话框内选项选择器（如导入目标文件夹、Space 切换） | 不透明白色面板：`bg-white rounded-lg shadow-xl border border-gray-200/80`；选项 `py-1.5 px-3 text-[11px]`；选中项 `bg-purple-100/60 text-secondary font-medium`，hover `hover:bg-gray-50 text-on-surface-variant` | 与弹窗玻璃面板形成对比，视觉聚焦于选项本身 |
| 页面内玻璃面板上下文下拉（如 Field Rule 选择器） | 玻璃面板：`glass-panel rounded-2xl` + `Transition` 淡入缩放；选项 `rounded-xl`，hover 白色半透明，选中绿色 check | 与玻璃背景融合，保持液态玻璃一致性 |

两种风格均使用：
- 触发器按钮：`glass-hover` 类 + `expand_more` 箭头图标（选中态箭头 `rotate-180`）
- 选中项左侧显示 `check` 图标（`visibility: hidden/visible` 控制，不使用 `v-if` 以保持布局稳定）
- 点击外部或选项自动关闭（`@click.stop` + document click listener）

### 4.5 Workspace 首页（已移除）

Workspace 页面已在 Phase 9 中移除，路由 redirect 改为 `/case-space`。`src/views/workspace/WorkspacePage.vue` 文件仍在磁盘上（未删除），但已不被路由引用，属于死代码。

### 4.6 Case（改版 Phase 2 — 多页路由架构）

Case 由三个子页面组成，通过 `CaseSpaceLayout` 统一管理导航和创建入口。从单页改为嵌套路由：`/case-space`（卡片列表）/ `/case-space/editor`（编辑器）/ `/case-space/field-rules`（字段规则）。

#### 4.6.1 CaseSpaceLayout (`src/layouts/CaseSpaceLayout.vue`)

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

#### 4.6.2 CaseSpacePage (`src/views/case-space/CaseSpacePage.vue`)

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

#### 4.6.3 CaseEditorPage (`src/views/case-space/editor/CaseEditorPage.vue`)

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

#### 4.6.4 FieldRulesPage (`src/views/case-space/field-rules/FieldRulesPage.vue`)

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

### 4.7 Device Space (`src/views/device-space/DeviceSpacePage.vue`)

**实现（Phase 7 — 完整重写为双分页布局 + Phase 8 交互优化 + Phase 19 文件管理器恢复与 UI/UX 全面优化）**：
- **连接栏**（上移，`flex-nowrap overflow-hidden`）：Tab 切换 + IP 输入（`min-w-[160px]`）+ Connect 按钮（`shrink-0`）+ 设备选择下拉 + Scan 按钮
- **设备选择下拉框**：自定义 `<Teleport to="body">` 下拉面板（匹配应用搜索历史样式），`fixed` 定位 + `getBoundingClientRect()` 坐标计算，避免 `glass-panel` 的 `backdrop-filter` 裁剪
- **设备连接持久化**：`selectDevice()` 写入 `localStorage('last_device_serial')`；`scanDevices()` 完成后恢复上次选中设备；断开当前设备时清除
- **设备列表自动刷新**：5s 轮询 `listDevices()`，所有 timeout/id 在 `onUnmounted` 清理
- **双分页布局**（`:tabs="['常用命令', '其他命令']"`）：
  - **分页一：常用命令**
    - **日志采集（Logcat）**：
      - 采集前**必须**执行 `prepareLogCapture()`：`adb root` → `adb logcat -G 64M`
      - 实时轮询 `adb -b all -t 1000`，日志缓冲区最多 500 条（圆形缓冲区）
      - 级别筛选（Verbose/Debug/Info/Warning/Error）+ 关键字搜索
      - 开始/停止按钮
    - **日志采集（Diagnostic）**：
      - 一次性采集：计时显示采集时长，stop 时一次性收集 logcat + dmesg + getprop + dumpsys + free + df + ps
      - 前置于 `prepareLogCapture()`（adb root + 扩大缓冲区）
    - **日志采集（Bugreport）**：
      - 调用 `adb bugreport`（Rust 后端 `adb_bugreport` 命令）
      - 前置于 `prepareLogCapture()`
    - **屏幕镜像**：双模式渲染 — 优先 scrcpy-server（adb push → forward → start_server → 服务器参数 `max_size=... video_bit_rate=... max_fps=... raw_stream=true send_device_meta=false send_codec_meta=false`），Rust 端读取原始 H264 Annex B 字节流，解析 NAL unit（`find_nal_start` 检测起始码），提取 SPS/PPS（NAL type 7/8），构建 avcC 后转换为 AVCC 格式（4 字节长度前缀），通过 `Channel<Vec<u8>>` 直接投递每帧原始字节（配置消息用 `0xFF` 标记，帧消息用 `0x00/0x01` 标记 key flag）。前端 WebCodecs VideoDecoder 直接在 Channel `onmessage` 中解码渲染，无队列、无 rAF 轮询、无 `adb_mirror_poll_frame` 命令。若 scrcpy-server push 失败（设备无 root/remount）自动降级为 `adb exec-out screencap -p` 轮询 + canvas.drawImage。所有逻辑在单个 Rust 阻塞线程中顺序执行（先试 scrcpy，失败则切 legacy），lib.rs 层 3 次重试（间隔 2s）减少首次降级。Canvas 点击/触摸支持：`input tap`（点击）、`input swipe`（拖拽 >10px）、右键 = `keyevent BACK`。坐标映射使用 `object-contain` letterbox + 设备物理分辨率（通过 `adb shell wm size` 查询）两级缩放。独立弹出窗口模式（`/mirror` 路由，无侧栏）。质量模式切换（smooth: 960/3Mbps/15fps vs quality: 1080/5Mbps/24fps）
    - **截图 + 录屏**：截图预览、录制/停止。录屏启动通过 Rust 异步 spawn 执行（不阻塞 UI），停止时 `pkill -SIGINT screenrecord` 后拉取文件
    - **ADB Shell**：命令输入 + 执行，输入历史走 SQLite `input_history` 表
    - **命令执行反馈浮窗**：长耗时操作（Root、Remount、重启、Bugreport 等）点击后在页面顶部弹出玻璃态浮动面板，显示实时执行状态和结果。所有命令执行完毕 3 秒自动关闭；鼠标悬停暂停计时，移出后恢复。快捷指令完成后不自动关闭，显示关闭按钮手动关闭
    - **执行输出面板**：ADB Shell 命令执行后在底部实时显示输出结果，支持清除输出内容
  - **分页二：其他命令**
    - **APK Manager**：安装（文件选择器）+ 卸载 + 已安装应用列表（按 web-adb-tool 规则排序 + 14 条分页 + 并行批量加载版本号（每批 4 个 `Promise.all`）+ 复制包名/版本 + 查询 APK 路径）
    - **File Manager**：Push/Pull 文件、目录列表（文件夹优先字母排序）、`..` 返回上级（`arrow_back` 图标）、文件预览（图片/视频/音频 + 缩放控件 + 鼠标滚轮缩放）、拖放上传（Tauri 原生 `onDragDropEvent`，遮罩 `absolute` 固定覆盖不随滚动消失）、文件编辑（Teleport 对话框）
    - **危险操作**（重装/remount）：点击触发确认弹窗（Teleport 红色警告）
    - **Custom Commands**（已迁移至 SQLite `app_settings` 表，key: `adb_custom_commands`，JSON 数组持久化命令名称、命令内容和排序）
    - **快捷指令**（右侧栏）：用户自定义的 ADB 命令按钮，点击即执行。通过管理弹窗增删改，支持拖拽上下箭头调整按钮顺序，顺序持久化到 SQLite `app_settings` 表（key: `adb_custom_commands`），主界面按钮顺序自动跟随
    - **遥控器**（右侧面板）：方向键/确认/返回/主页/音量键，响应式 4 级尺寸（`lg:`/`xl:`/`2xl:` 断点）
- **输入历史**：`text_input`、`app_search`、`connect_ip`、`remote_path` 四种 key 通过 `addInputHistory()` / `getInputHistory()` 走 SQLite `input_history` 表，每 key 最多 20 条。`remote_path` 在 `navigateToPath()`/`navigateToDir()` 中保存
- **历史下拉不透明**：文本历史、远程路径历史、应用搜索历史下拉均使用 `bg-white border shadow-lg` 不透明样式（非 `glass-panel`）
- **连接对话框**（Teleport）：玻璃面板浮层 + USB/TCP/IP 切换 + IP 输入 + 连接按钮
- **文件预览系统**：`previewDialog` + `loadPreviewContent(name)` 支持图片（JPEG/PNG/GIF/WebP/BMP/SVG/ICO）、视频（WebM/OGG/MP4/MOV/AVI/MKV）、音频（FLAC/MP3/WAV/OGG/AAC/M4A/WMA），缩放 0.25x–5x + 鼠标滚轮缩放 + 百分比显示；大文件（>10MB）弹窗确认后常显 loading 提示；不支持的文件类型（apk/exe/so/bin/zip 等）直接 toast 提示
- **文件右键菜单**：Copy Path（复制完整远程路径到剪贴板）+ Download + Edit（仅文件）+ Delete（二次确认）
- **文件夹下载**：直接 `adb pull`，不再设备端压缩；通过 `open({ directory: true })` 选择本地目录
- **大文件编辑保护**：`wc -c` 前置检测 > 5MB 弹窗确认，加载期间常显 loading 提示
- **confirmThen 重构**：返回 `Promise<boolean>`，支持 await 检查用户确认/取消；大文件（>10MB）弹窗确认后常显 loading 提示；不支持的文件类型（apk/exe/so/bin/zip 等）直接 toast 提示
- **文件右键菜单**：Copy Path（复制完整远程路径到剪贴板）+ Download + Edit（仅文件）+ Delete（二次确认）
- **文件夹下载**：直接 `adb pull`，不再设备端压缩；通过 `open({ directory: true })` 选择本地目录
- **大文件编辑保护**：`wc -c` 前置检测 > 5MB 弹窗确认，加载期间常显 loading 提示
- **confirmThen 重构**：返回 `Promise<boolean>`，支持 await 检查用户确认/取消
- **全局 `select-none` / `select-text`**：所有按钮/标题/根 div 使用 `select-none`，所有 input/textarea/pre 使用 `select-text`

### 4.8 Notes Space (`src/views/note-space/NotesSpacePage.vue`)

**实现（Phase 11-13 — SQLite 持久化 + Space 结构 + 全功能增强）**：
- **Space 目录结构**：
  - `note_spaces` 表：顶层 Space 容器
  - `note_folders` 表：`space_id` + `parentId` 支持无限层级嵌套
  - Space 下拉选择器（左侧面板顶部）：切换/创建/重命名/删除 Space
  - `flatFolders` 递归展平树 + 缩进显示
  - 文件夹 "+" 按钮：Teleported 下拉框（New Folder / New Note）
  - 删除确认：自定义 Teleport 模态框（Space/文件夹/笔记均二次确认）
- **三面板布局**：
  - **根容器**：`flex flex-1 min-h-0 -mx-margin-page overflow-hidden pb-4 box-border select-none`（Phase 25 布局修复前为 `h-full`，修复原因见下方"布局修复说明"）
  - **左（256px）**：Space 下拉 + 搜索栏 + Favorites + 文件夹树 + Uncategorized
  - **中（flex-1）**：TipTap 富文本编辑器 + 标题栏 + 工具栏 + 编辑区（`max-w-[850px]` 居中 + 边框）
  - **右（Teleport 滑出面板）**：TOC 目录（层级展开/收起，85% 透明，弹性动画）
- **编辑器扩展（TipTap，当前实际启用）**：
  - `StarterKit`（H1/H2/H3、列表、引用、粗斜体等）
  - `Underline`、`Link`（`openOnClick: false`）、`Image`（`inline: true, allowBase64: true`）
  - `Placeholder`、`Typography`
  - `TextStyle` + `Color`（字体颜色，HTML 存为 `<span style="color: …">`）
  - 剪切板粘贴图片（`handlePaste` 检测 `image/*`）
  - 超链接插入（Teleport 弹窗，自动补 `https://`）
  - 图片插入（文件选择器转 base64）
- **复制为纯文本优化**（`editorProps.clipboardTextSerializer`）：
  - 块级节点分隔符使用单个 `\n`（避免 ProseMirror 默认 `\n\n` 导致每行下方多空行）
  - 归一化不可见空白：`\u00A0/\u202F/\u2007` → 普通空格，移除 `\u200B-\u200D/\uFEFF` 零宽字符
  - **场景**：从 AI 复制 SQL/脚本粘贴到笔记后再复制出去，避免 PostgreSQL 等执行器报 `SyntaxError`（NBSP 导致）
- **字体颜色工具栏**（Word 式分体按钮，类名 `color-split-btn`）：
  - **左侧「A」**：一键将 `currentTextColor` 应用到选区/后续输入（无需再打开下拉）
  - **右侧 `arrow_drop_down`**：打开预设色面板（Teleport 到 `body`，`z-[9999]`，避免被编辑区遮挡）
  - **A 下方色条**：显示当前选中预设色（自定义粗体 `A` + `.color-split-bar`，**不使用** `format_color_text` 图标——该图标自带下划线会与色条重叠）
  - **预设色**（8 色）：`#111827` 黑、`#ef4444` 红、`#f97316` 橙、`#eab308` 黄、`#22c55e` 绿、`#06b6d4` 青、`#3b82f6` 蓝、`#8b5cf6` 紫；当前色高亮 `ring-secondary`
  - 下拉选色：更新 `currentTextColor` 并立即 `setColor`；再次点「A」可重复应用同色
- **导出**：PDF（`html-to-image` + `jsPDF`，隐藏 iframe）、Word（`docx` 包生成真实 .docx）、Markdown（`turndown`）
- **自动保存**：1.5s 防抖写入 SQLite，版本快照 30s 无操作触发
- **数据持久化**：`note_spaces` / `note_folders` / `notes` / `note_versions` / `note_links` 五张表
- **导入弹窗**：Teleport 对话框内包含目标文件夹选择器，使用不透明白色下拉面板（`bg-white rounded-lg shadow-xl border border-gray-200/80`），与 Space 切换下拉框一致。选项 `py-1.5 px-3 text-[11px]`，选中态 `bg-purple-100/60 text-secondary font-medium`，hover `hover:bg-gray-50`。触发器按钮使用 `glass-hover` 类
- **工具栏**：`toolbar-btn` 无边框 + `toolbar-active` 淡紫色高亮；格式按钮 + Word 式字体颜色分体按钮 + 标题/列表/链接/图片/撤销重做
- **搜索**：全文搜索 + 自动展开匹配文件夹 + 黄色高亮匹配笔记
- **拖拽**：HTML5 drag-and-drop（`dragDropEnabled: false`），`dataTransfer` + `effectAllowed`
  - 根笔记拖拽目标使用 `__root__` 标识（原 `__uncategorized__`），`onDrop($event, null)` 将笔记移到根级别
  - 拖拽区域内交互按钮（添加/重命名/删除）统一添加 `@mousedown.stop` 防止 mousedown 事件冒泡触发拖拽
- **根笔记区域**：根级别笔记（无文件夹）始终渲染在文件夹树下方，可作为拖拽目标区域
- **文件夹/笔记创建行为**：
  - `createFolder()` 始终创建根级别文件夹（`parentId = null`），创建后自动选中新文件夹
  - `createNote()` 始终创建根级别笔记（`selectedFolderId = null`），创建后自动选中新笔记
  - `addNoteToFolder(folderId)` 在指定文件夹内新建笔记，创建后自动展开文件夹（`expandedFolders[folderId] = true`）并关闭添加下拉框（`folderAddDropdownId = null`）
- **单一选中态**：文件夹和笔记的选中态互斥——点击笔记时清除文件夹选中态（`selectedFolderId = null`），点击文件夹时清除笔记选中态（`selectedNoteId = null`），避免双重选中态
- **笔记排序**：`loadNotes()` 和 `loadNoteList()` 均按 `title COLLATE NOCASE ASC` 排序，文件夹内笔记按名称字母序排列，不区分大小写
- **删除防卡顿**：`doDeleteSpace()` 和 `doDeleteFolder()` 中的顺序 DB 调用之间插入 `yieldToMain()`（`setTimeout(0)`），避免大数据量时删除操作卡顿
- **删除乐观 UI**：`doDeleteNote()` 的 UI 状态清理（从 notes 数组过滤、清空编辑器）在 try-catch 外部执行，DB 删除失败时 UI 仍响应，笔记在下次重启后恢复
- **按钮内边距**：文件夹/笔记操作按钮统一使用 `px-1.5 py-0.5`（原 `p-0.5`），增加水平内边距提高可点击性
- **布局修复说明（Phase 25）**：修复编辑区无法滚动/卡片溢出的问题。根容器从 `h-full` 改为 `flex flex-1 min-h-0 overflow-hidden`，依赖 `<main>` 的 `flex flex-col` 上下文使 flex-1 正确撑满高度（替代 `h-full` 百分比方案）
  - **中栏编辑器区域**：
    - 中心面板：添加 `min-w-0` 防止 flex 项因内容超宽撑破布局
    - 编辑器卡片（`flex-1`）：添加 `min-w-0 min-h-0` 覆盖 flex 默认 `min-height: auto`，使内容区可正确收缩和滚动
    - 滚动容器：添加 `overflow-x-hidden` 防止编辑内容水平溢出滚动
    - 编辑内容区：保持 `min-h-full` 确保内容至少撑满卡片高度
  - **影响范围验证**：`<main>` 添加 `flex flex-col` 后，所有子路由页面变为 flex 项。经逐页验证发现 `h-full` 在 flex 列上下文中存在首次渲染不稳定的问题：
    - **受影响页面**（根 div `h-full` → `flex-1 min-h-0`）：NotesSpacePage（编辑器无法滚动）、ScriptSpacePage（分页器不显示）、DeviceSpacePage、SettingsPage、ApiSpacePage
    - **不受影响页面**：CaseSpaceLayout（根 div 无高度类）、通过 CaseSpaceLayout 嵌套的子页面（CaseSpacePage/CaseEditorPage/FieldRulesPage，其 `h-full` 解析于 CaseSpaceLayout 的 auto 高度，行为不变）

### 4.9 Script Space (`src/views/script-space/ScriptSpacePage.vue`)

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
- **布局修复说明（Phase 25）**：脚本页面左侧列表底部分页器在首次进入时不显示（改变窗口大小后才正常）。根容器 `h-full` → `flex flex-col flex-1 min-h-0`，与 NotesSpacePage 同理——`<main>` 变为 `flex flex-col` 后，`h-full` 百分比高度在首次渲染时可能不生效，导致页面高度为 `auto`，左侧列表区域高度不足分页器不可见。改用 flexbox 自身 `flex: 1 1 0%` 撑满剩余高度后修复。
  - **额外 JS 修复**：`pageSize` 初始值 `999` → `10`，防止 `totalPages = Math.ceil(N/999) = 1` 导致分页器 `v-if` 隐藏；移除 `nextTick` 包装，在 `loadScriptList` 后直接调用 `updatePageSize()`，避免 async `onMounted` 中 `nextTick` 回调未按预期触发的问题

### 4.10 Settings (`src/views/settings/SettingsPage.vue`)

**实现（Phase 14 重构 + Phase 16 i18n + Phase 17 优化 + 云端备份）**：
- **单卡片布局**：所有设置项合并到一个 `glass-panel` 卡片内，用分割线隔开四个区域
- **Language**：语言切换（中文 / English），点击即时切换，持久化到 `localStorage('app-lang')`
- **Appearance**：主题切换（Light / Dark 二选一）
  - `applyTheme()` 操作 `document.documentElement.classList` 的 `dark` 类
  - 主题持久化到 SQLite `app_settings` 表（key: `theme`）
  - Dark 模式 CSS：`html.dark` 暗色背景（`#0d0d1a`）+ `glass-panel`/`glass-card`/`glass-button`/`glass-active`/`glass-input` 暗色变体
- **Data Backup & Restore**：
  - **Device ID**：设备标识输入框（`bg-white` 不透明背景），自动生成 UUID，支持下拉历史记录切换，可复制到剪贴板
  - **备份数据**下拉菜单：
    - 备份到本地：导出全部数据为 `.tsb` 备份文件（JSON 格式），通过 `@tauri-apps/plugin-dialog` 原生文件对话框
    - 备份到云端：导出 → AES-256-GCM 加密 → 上传到 `https://tms.zeasn.com/api/TestSpace`
  - **恢复数据**下拉菜单：
    - 从本地恢复：从 `.tsb` 文件恢复数据，通过原生文件对话框选择；`JSON.parse` 有 try-catch 保护；成功后 1.5 秒自动 `window.location.reload()` 刷新所有页面数据
    - 从云端恢复：直接恢复最新云端备份（无需选择界面），下载 → 解密 → 导入；客户端按 `created_at` 降序排序确保取最新；解密失败（密钥不匹配）有明确错误提示；成功后 1.5 秒自动 `window.location.reload()` 刷新所有页面数据
  - **状态提示**：操作结果通过 `statusMessage` + `statusIsError` 显示，成功绿色 / 失败红色（`setStatus(msg, isError)` 统一控制，不再用 `startsWith('Error')` 匹配）
  - **防重复点击**：所有操作通过 `cloudBusy` 互斥锁防止重复触发
  - **取消操作**：文件选择器取消后自动清除状态消息
- **快捷云端同步**：导航栏 Settings 旁的 `sync` 按钮（见 4.3.2），调用 `src/services/cloudSync.ts` 的 `syncBackupToCloud()`，与「备份到云端」逻辑等价，无需进入设置页
- **Version**：显示应用版本号，通过 `@tauri-apps/api/app` 的 `getVersion()` 读取

### 4.11 云端备份服务层

**新增文件**：
- `src/services/crypto.ts` — AES-256-GCM 加密/解密 + PBKDF2 密钥派生
- `src/services/cloudBackup.ts` — 云端备份 HTTP 客户端
- `src/services/cloudSync.ts` — 导航栏一键云端备份（封装 deviceId 确保 + export + encrypt + upload）

**`cloudSync.ts` 流程**（`syncBackupToCloud()`）：
1. `db.checkDatabaseReady()` 确认数据库可用
2. `ensureDeviceId()`：读取 `cloud_device_id_last`，无则 `crypto.generateDeviceId()` 并写入列表
3. `db.exportAllData()` → `JSON.stringify` → `crypto.getOrCreateKey()` → `crypto.encryptBackup()`
4. `cloudApi.uploadBackup(deviceId, payload)` 上传至 `https://tms.zeasn.com/api/TestSpace`

与 `SettingsPage.handleCloudUpload()` 等价；设置页仍保留 Device ID 编辑、本地备份/恢复、密钥导入导出等完整能力。

**加密方案**（`crypto.ts`）：
- **密钥生成**：32 字节随机密钥，存储在 SQLite `app_settings` 表（key: `cloud_encryption_key`），永不离开客户端
- **加密流程**：主密钥 → PBKDF2（随机 salt，100,000 次迭代，SHA-256）→ AES-256-GCM 加密
- **每备份独立 salt**：每次加密生成新 salt 和 IV，确保相同明文产生不同密文
- **完整性校验**：加密前计算明文 SHA-256 checksum，解密后验证，防止数据损坏
- **设备 ID**：`crypto.randomUUID()` 自动生成，用户可手动编辑，支持多个设备 ID 历史记录

**云端 API 客户端**（`cloudBackup.ts`）：
- **服务器地址**：`https://tms.zeasn.com/api/TestSpace`（硬编码，不支持手动配置）
- **CORS 绕过**：使用 `@tauri-apps/plugin-http`（Rust 端 reqwest）绕过浏览器 CORS 限制
- **降级方案**：Tauri HTTP 插件不可用时降级为浏览器原生 `fetch`（开发模式）
- **API 端点**：

| 方法 | 路径 | 说明 | 请求头 |
|------|------|------|--------|
| POST | `/backups` | 上传加密备份 | `X-Device-ID` |
| GET | `/backups` | 列出设备备份 | `X-Device-ID` |
| GET | `/backups/:id` | 获取备份详情（含加密数据） | `X-Device-ID` |
| DELETE | `/backups/:id` | 删除备份 | `X-Device-ID` |

**Tauri 配置**：
- `src-tauri/Cargo.toml`：`tauri-plugin-http = "2"`
- `src-tauri/src/lib.rs`：注册 `tauri_plugin_http::init()`
- `src-tauri/capabilities/default.json`：`http:default` 权限，scope `https://tms.zeasn.com/api/TestSpace/*`

**数据库优化**（`database.ts`）：
- `initDb()`：`PRAGMA journal_mode = WAL`（数据库级，对所有连接生效）+ `PRAGMA busy_timeout = 30000`（连接级，仅对单个连接生效）
- `exportAllData()`：在 8 处顺序 DB 查询之间插入 `_yieldToMain()`（`setTimeout(0)`），避免大数据量导出时 UI 冻结
- `importAllData()`：导入前 `validateBackup()` 校验备份结构；重试 3 次（指数退避）检测数据库可用性；每条 DELETE/INSERT 独立自动提交（不使用事务，因 `@tauri-apps/plugin-sql` 连接池不保证同一连接）；失败项收集到 `failures[]` 最终汇总抛出；所有 INSERT 显式指定列名（跳过自增 `id`）
- `deleteNote()`：移除事务包裹（`BEGIN/COMMIT/ROLLBACK`），改为逐条 auto-commit DELETE（`note_versions` → `note_links` → `notes`），与 `importAllData` 同理——连接池下事务不可靠
- `getDeviceIdList()` / `saveDeviceIdList()` / `getLastDeviceId()` / `saveLastDeviceId()`：设备 ID 持久化
- `checkDatabaseReady()`：数据库就绪检测，用于导入前预检查

### 4.12 API Space (`src/views/api-space/ApiSpacePage.vue`)

**实现（Phase 23 — MITM 代理 + Phase 24 二进制响应优化）**：

- **代理核心**：基于 `http-mitm-proxy` Rust crate 实现 HTTPS 中间人代理，自动生成 CA 证书（首次启动在 `app_data_dir` 生成 `mitm-ca-cert.pem` / `mitm-ca-key.pem`，持久化复用）
- **控制栏**：
  - Start / Stop 代理按钮 + 运行状态指示灯（绿色脉冲 + 端口号）
  - 断点开关（`glass-active` 高亮）+ URL 路径过滤输入框 + 待处理断点计数徽章
  - 设备选择器（自定义 Teleport 下拉面板）+ 刷新按钮
  - 重写规则面板开关 + 规则计数
- **双面板布局**：
  - **左面板**（`flex:[0_0_40%] min-w-[360px] max-w-[50%]`）：请求列表（方法 + URL + 状态码 + 耗时），支持搜索过滤（含输入历史下拉）
  - **右面板**（flex-1）：请求/响应详情（Headers / Body / Raw 三个 Tab），支持 Copy 按钮
- **断点调试**：
  - `proxy:breakpoint:request` / `proxy:breakpoint:response` 事件自动弹出断点编辑框
  - 支持 `forward`（放行）、`drop`（丢弃）、`modify`（修改 headers/body/status_code）三种操作
  - `oneshot::channel` 300s 超时等待用户操作
- **重写规则引擎**：
  - 匹配方式：`contains` / `exact` / `prefix` / `regex` 四种
  - 动作：`modify_request_header/body`、`modify_response_header/body`、`drop` 五种
  - 规则持久化到 `app_data_dir/rewrite-rules.json`，CRUD 命令同步写入文件
  - 规则存储同时写入 SQLite `app_settings` 表（key: `proxy_rules`），纳入备份恢复流程
- **ADB 一键部署**：`adb root` → `adb remount` → push CA cert → 设置代理（LAN IP:port）
- **二进制响应处理**：
  - Rust 端 `body_to_string()` 尝试 UTF-8 校验，失败则 base64 编码并标记 `_is_base64: true`
  - 前端检测 `_is_base64` 标志：图片→`<img>` base64 预览，视频→`<video>`，音频→`<audio>`，其他→`[Binary data]` 占位
  - 断点编辑器中二进制 body 显示 `[Binary body — cannot edit in text mode]` 禁用编辑
- **Composable**：`src/composables/useApiProxy.ts` 封装代理控制、事件监听、断点管理、规则 CRUD
- **i18n**：所有按钮/标签/提示支持中英双语（`api.*` 翻译 key）

---

## 五、Rust 原生层

### 5.1 ADB 模块 (`src-tauri/src/adb.rs`)

**实现的 Tauri 命令**（Phase 22 后所有命令均为 `async` + `spawn_blocking`）：

| 命令 | 函数 | 说明 | 底层调用 |
|------|------|------|----------|
| `adb_list_devices` | `list_devices()` | 列出已连接设备（含 model 和 android_version） | `adb devices -l` |
| `adb_shell` | `shell_command(serial, command)` | 在指定设备执行 shell 命令 | `adb -s <serial> shell <command>` |
| `adb_install` | `tokio::process::Command::output()` | 安装 APK（-r 可选），120s 超时 | `adb -s <serial> install [-r] <path>` |
| `adb_uninstall` | `uninstall_apk(serial, package)` | 卸载应用 | `adb -s <serial> uninstall <pkg>` |
| `adb_push` | `push_file(serial, local, remote)` | Push 文件到设备 | `adb -s <serial> push <local> <remote>` |
| `adb_pull` | `pull_file(serial, remote, local)` | 从设备 Pull 文件 | `adb -s <serial> pull <remote> <local>` |
| `adb_reboot` | `reboot(serial)` | 重启设备 | `adb -s <serial> reboot` |
| `adb_screenshot` | `screenshot(serial, save_path)` | 截图并保存到本地 | `adb -s <serial> exec-out screencap -p` |
| `adb_logcat_buffer_resize` | `logcat_buffer_resize(serial, size)` | 扩大 logcat 缓冲区 | `adb -s <serial> logcat -G <size>` |
| `adb_bugreport` | `bugreport(serial)` | 生成 bugreport zip | `adb -s <serial> bugreport` |
| `adb_dmesg` | `dmesg(serial)` | 获取内核日志 | `adb -s <serial> shell dmesg` |
| `adb_list_packages` | `list_packages(serial, third_party_only)` | 列出已安装应用 | `adb shell pm list packages` |
| `adb_start_app` / `adb_stop_app` | `start_app` / `stop_app` | 启动/停止应用 | `adb shell am start/force-stop` |
| `adb_clear_app_data` | `clear_app_data` | 清除应用数据 | `adb shell pm clear` |
| `adb_get_current_app` | `get_current_app` | 获取前台应用 | `adb shell dumpsys window` |
| `adb_logcat_clear` / `adb_logcat` | `logcat_clear` / `logcat` | 清空/读取日志 | `adb shell logcat -c / -d` |
| `adb_get_battery` / `adb_get_cpu` / `adb_get_memory` | `get_battery_info` / `get_cpu_info` / `get_memory_info` | 设备信息 | `dumpsys battery/cpuinfo/meminfo` |
| `adb_connect` / `adb_disconnect` | `connect_device` / `disconnect_device` | TCP/IP 连接/断开 | `adb connect/disconnect` |
| `adb_reboot_recovery` / `adb_reboot_bootloader` | `reboot_recovery` / `reboot_bootloader` | 特殊重启 | `adb reboot recovery/bootloader` |
| `adb_root` / `adb_remount` | `root_device` / `remount_device` | Root/Remount | `adb root/remount` |
| `adb_get_properties` | `get_device_properties` | 设备属性 | `adb shell getprop` |
| `adb_input_keyevent/text/tap/swipe` | `input_keyevent/text/tap/swipe` | 输入操作 | `adb shell input` |
| `adb_get_display_size` | `get_display_size(serial)` | 获取设备屏幕分辨率 | `adb shell wm size` |
| `adb_kill_server` / `adb_start_server` | `kill_server` / `start_server` | ADB 服务管理 | `adb kill-server/start-server` |

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

### 5.4 屏幕镜像模块 (`src-tauri/src/mirror.rs`)

**实现的 Tauri 命令**：

| 命令 | 说明 | 底层 |
|------|------|------|
| `adb_mirror_start(serial, onFrame, maxSize?, videoBitRate?, maxFps?)` | 启动屏幕镜像（scrcpy-server → legacy 兜底），通过 `Channel<Vec<u8>>` 直接投递 H.264/PNG 帧数据到前端 | 单 Rust 阻塞线程：`adb push scrcpy-server.jar` → `adb forward tcp:27183` → `adb shell CLASSPATH=... app_process ...` 参数 `max_size={maxSize} video_bit_rate={videoBitRate} max_fps={maxFps} raw_stream=true send_device_meta=false send_codec_meta=false` → TCP 连接读取 H.264 raw stream；失败则 3 次重试（lib.rs），均失败降级 legacy（`adb exec-out screencap -p` 轮询）。清理 `pkill` + `adb forward --remove` |
| `adb_mirror_stop` | 停止镜像 | 设置停止标志 + 清理 forward |

**通信协议**（scrcpy 模式）：
- **传输**：不再使用队列 + rAF 轮询 + `adb_mirror_poll_frame` 命令，而是通过 Tauri `Channel<Vec<u8>>` 直接投递每帧原始字节。前端 `onmessage` 回调直接处理帧数据，消除了队列丢帧和 IPC 路径竞争导致的 H.264 花屏问题。
- **解码器配置**：通过同一 Channel 投递，使用 `0xFF` 标记字节区分配置消息与帧消息（`0xFF + avcC bytes`）。保证配置在首帧之前按序到达，避免解码器未配置的 `InvalidStateError`。
- TCP 连接 `127.0.0.1:27183`，发送 1 字节 dummy，服务器以原始 H264 Annex B 字节流响应（`raw_stream=true`）
- Rust 端用 `find_nal_start()` 检测 `0x00000001` / `0x000001` 起始码；提取 `nal_unit_type=7`（SPS）与 `nal_unit_type=8`（PPS）的数据用于构建 avcC extradata；SPS/PPS 与后续 VCL NAL 单元（type 1/5）合并为一个 access unit，转换为 AVCC 格式（4 字节长度前缀大端序）后通过 Channel 发送
- **Payload 格式**（Channel 投递）：
  - 配置消息：`[0xFF, ...avcC extradata bytes]` — 用于 `VideoDecoder.configure({ codec: "avc1.42E01E", description })`
  - 帧消息：`[0x01 (key frame) / 0x00 (delta frame), ...AVCC format NAL data]`
- **前端事件**：`mirror:mode`（scrcpy/legacy）、`mirror:error`、`mirror:ready`、`mirror:diagnostic`
- **Canvas 交互**：`input tap`（单击）、`input swipe`（拖拽 >10px）、右键 = `keyevent BACK`。坐标经过 CSS letterbox（`object-contain`）→ 视频分辨率 → 设备物理分辨率（通过 `adb shell wm size` 查询）两级映射

**质量模式切换**：
- 通过 `DeviceSpacePage.vue` 的 `qualityMode` ref（`'smooth' | 'quality'`）控制参数：
  - **Smooth（默认）**：`max_size=960, video_bit_rate=3_000_000, max_fps=15`
  - **Quality**：`max_size=1080, video_bit_rate=5_000_000, max_fps=24`
- 切换按钮（`hdr_weak` 图标）位于主页面镜像按钮右侧，仅在空闲状态可操作
- 独立弹出窗口通过 URL 参数 `?quality=smooth|quality` 继承当前模式
- JS 端 `VideoDecoder` 创建于 `mirror:mode` 事件监听器中，`decoderConfigured` 标志在 Channel `onmessage` 中配置成功后置为 `true`

**历史遗留问题**：
- `mirror:ready` 事件在 `lib.rs` `spawn_blocking` 和 `mirror.rs` `connect_and_stream` 中各 emit 一次，导致 Toast 提示出现两次（不影响功能）

**历史架构变更**（旧 → 当前）：
1. 最初：`FramePayload { data: frame_b64 }` 通过 `emit_to("mirror:frame", ...)` 投递 base64 数据
2. 中间态：`Channel<FrameData>` 投递 base64，`VecDeque` 队列 + `AtomicBool` 信号 + rAF 轮询
3. **当前**：`Channel<Vec<u8>>` 直接投递原始字节，配置和帧共用同一 Channel 保证有序；移除 `FrameBuffer`、`adb_mirror_poll_frame`、所有队列和轮询代码

### 5.5 MITM 代理模块 (`src-tauri/src/proxy.rs`)

**实现（Phase 23 — MITM 代理核心 + Phase 24 二进制响应优化）**：

**Tauri 命令**：

| 命令 | 说明 | 底层 |
|------|------|------|
| `proxy_start(port, ca_dir)` | 启动 MITM 代理 | `http-mitm-proxy` 绑定 `0.0.0.0:port`，自动生成/加载 CA 证书 |
| `proxy_stop` | 停止代理 | 发送 shutdown 信号 + 清理资源 |
| `proxy_set_breakpoint(enabled, url_pattern?)` | 设置断点开关 | 启用/禁用请求拦截，可选 URL 过滤 |
| `proxy_continue(request_id, action, body?)` | 继续断点请求 | `forward` / `drop` / `modify` 三种操作 |
| `proxy_add_rule(rule)` | 添加重写规则 | 写入内存 + 持久化到 `rewrite-rules.json` |
| `proxy_remove_rule(rule_id)` | 删除重写规则 | 从内存和文件中移除 |
| `proxy_update_rule(rule)` | 更新重写规则 | 替换内存和文件中的规则 |
| `proxy_clear_rules` | 清空所有规则 | 清空内存和文件 |
| `proxy_get_rewrite_rules` | 获取规则列表 | 从内存返回当前规则 |
| `proxy_get_captured` | 获取已捕获请求 | 返回 `Vec<CapturedRequest>` |
| `proxy_get_status` | 获取代理状态 | 返回 `ProxyStatus`（running/port/captured_count） |
| `proxy_get_ca_cert` | 获取 CA 证书路径 | 返回 PEM 文件路径 |
| `proxy_set_device_proxy(serial, port)` | 设置设备代理 | `adb shell settings put global http_proxy` |
| `proxy_clear_device_proxy(serial)` | 清除设备代理 | `adb shell settings put global http_proxy :0` |
| `proxy_install_cert(serial, ca_path)` | 安装 CA 证书 | `adb root` → `adb remount` → push cert |
| `proxy_replay(request_id)` | 重放请求 | 重新发送已捕获的请求 |

**核心机制**：
- **CA 证书管理**：首次启动在 `app_data_dir` 生成 CA 公私钥（`mitm-ca-cert.pem` / `mitm-ca-key.pem`），持久化复用
- **请求/响应捕获**：通过 Tauri `emit` 将 `proxy:request` / `proxy:response` 事件发送到前端
- **断点拦截**：`proxy:breakpoint:request` / `proxy:breakpoint:response` 事件 + `oneshot::channel` 300s 超时等待用户操作
- **重写规则引擎**：`url_matches()` 支持 `contains` / `exact` / `prefix` / `regex` 四种匹配；规则按 `enabled` 状态过滤后逐条执行
- **二进制响应处理**：`body_to_string()` 尝试 `String::from_utf8()` 校验，失败则 base64 编码并标记 `_is_base64: true`

**Tauri 事件**：

| 事件 | 说明 |
|------|------|
| `proxy:request` | 新请求被捕获（含 method/url/headers/body） |
| `proxy:response` | 响应已接收（含 status_code/headers/body） |
| `proxy:breakpoint:request` | 请求被断点拦截，等待用户操作 |
| `proxy:breakpoint:response` | 响应被断点拦截，等待用户操作 |

### 5.6 ZIP 工具模块 (`src-tauri/src/zip_util.rs`)

**实现的 Tauri 命令**：

| 命令 | 说明 | 底层 |
|------|------|------|
| `create_zip(file_paths, output_path)` | 将多个文件打包为 ZIP | `zip` crate 内存构建，写入输出路径 |

用于 Diagnostic 采集（logcat + dmesg + getprop + dumpsys + free + df + ps + ANR traces 打包为 ZIP）和文件夹下载。

### 5.7 入口和命令注册 (`src-tauri/src/lib.rs`)

**实现**：
- 所有命令通过 `generate_handler!` 宏注册
- **单实例**：`tauri-plugin-single-instance` 插件注册为第一个插件，第二次启动时自动聚焦已有窗口并退出
- **HTTP 插件**：`tauri_plugin_http::init()` 注册，用于云端备份 API 调用（绕过 CORS）
- **系统托盘**：`setup` 中创建 `TrayIconBuilder`，图标使用应用默认窗口图标，tooltip "TestSpace"，右键菜单（显示窗口 / 退出）
- **关闭按钮拦截**：`on_window_event` 拦截 `CloseRequested`，`api.prevent_close()` 阻止关闭，`window.hide()` 隐藏到系统托盘

```rust
// 所有命令通过 generate_handler! 宏注册（Phase 22 后全部为 async）
.invoke_handler(tauri::generate_handler![
    adb_list_devices, adb_shell, adb_install, adb_uninstall,
    adb_push, adb_push_bytes, adb_pull, adb_reboot, adb_screenshot,
    adb_logcat_buffer_resize, adb_bugreport, adb_dmesg,
    adb_list_packages, adb_start_app, adb_stop_app, adb_clear_app_data,
    adb_get_current_app, adb_logcat_clear, adb_logcat,
    adb_get_battery, adb_get_cpu, adb_get_memory,
    adb_connect, adb_disconnect,
    adb_reboot_recovery, adb_reboot_bootloader,
    adb_root, adb_remount, adb_get_properties,
    adb_input_keyevent, adb_input_text, adb_input_tap, adb_input_swipe,
    adb_kill_server, adb_start_server,
    adb_start_screenrecord,
    adb_list_directory, adb_get_app_info,
    serial_list_ports, serial_connect, serial_disconnect,
    serial_send, serial_read,
    script_execute_python, script_execute_bat,
    script_execute_powershell, script_execute_shell,
    script_spawn, script_kill,
    write_text_file, write_script_file, read_text_file,
    create_zip,
    proxy::proxy_start, proxy::proxy_stop,
    proxy::proxy_set_breakpoint, proxy::proxy_continue,
    proxy::proxy_add_rewrite_rule, proxy::proxy_remove_rewrite_rule,
    proxy::proxy_update_rewrite_rule, proxy::proxy_clear_rewrite_rules,
    proxy::proxy_get_rewrite_rules,
    proxy::proxy_get_captured, proxy::proxy_get_status,
    proxy::proxy_get_ca_cert, proxy::proxy_set_device_proxy,
    proxy::proxy_clear_device_proxy, proxy::proxy_install_cert,
    proxy::proxy_replay,
])
```

---

## 六、前端 Composable

### 6.1 `useAdb` (`src/composables/useAdb.ts`)

封装 Tauri `invoke` 调用，提供类型安全的 ADB 操作接口：

```typescript
const { listDevices, shell, installApk, uninstallApk, pushFile, pullFile, reboot, screenshot, logcatBufferResize, bugreport, dmesg } = useAdb();
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

### 6.5 `useI18n` (`src/composables/useI18n.ts`)

国际化翻译 composable，支持中文/英文双语切换：

```typescript
const { lang, t, setLanguage, initLanguage } = useI18n();
// lang: Ref<'zh' | 'en'> — 当前语言
// t(key, params?): 翻译函数，支持 {param} 插值
// setLanguage(l): 切换语言并持久化到 localStorage
// initLanguage(): 启动时从 localStorage 恢复语言设置
```

**翻译 key 约定**：`页面.元素`（如 `scripts.new`、`device.connect`、`notes.toc`、`cloudSync.syncing`）

**云端同步 Toast key**（`cloudSync.*`）：`ready` / `syncing` / `success` / `fail`（中/英双语，用于导航栏同步按钮顶部 Toast）

**使用方式**：
- 模板中：`{{ t('scripts.new') }}` 或 `:placeholder="t('scripts.search')"`
- 脚本中：`showToast(t('scripts.saveSuccess'))`
- 带参数：`t('scripts.deleteDesc', { name: scriptName })`

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

### 8.1 云端备份 API

服务器地址：`https://tms.zeasn.com/api/TestSpace`

API 文档详见 `TestSpace_API.md`。

| 方法 | 路径 | 说明 | 请求头 |
|------|------|------|--------|
| POST | `/backups` | 上传加密备份 | `X-Device-ID`, `Content-Type: application/json` |
| GET | `/backups` | 列出设备备份（按 `created_at` 降序） | `X-Device-ID` |
| GET | `/backups/:id` | 获取备份详情（含加密数据） | `X-Device-ID` |
| DELETE | `/backups/:id` | 删除备份 | `X-Device-ID` |

**请求/响应格式**：
- 上传：`POST /backups`，body 为 `BackupUploadPayload`（`data`, `iv`, `salt`, `auth_tag`, `size_bytes`, `checksum`, `metadata`）
- 列表：`GET /backups`，返回 `BackupListItem[]`（`id`, `device_id`, `size_bytes`, `checksum`, `metadata`, `created_at`）
- 详情：`GET /backups/:id`，返回 `BackupDetail`（含 `data`, `iv`, `salt`, `auth_tag`）
- 删除：`DELETE /backups/:id`，返回 204

**客户端加密**：
- 加密算法：AES-256-GCM
- 密钥派生：PBKDF2（主密钥 + 随机 salt，100,000 次迭代，SHA-256）
- 主密钥：32 字节随机值，存储在本地 SQLite `app_settings` 表（key: `cloud_encryption_key`）
- 每次加密使用独立 salt 和 IV，确保相同明文产生不同密文

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

**备份数据格式**（`AppBackup`）：
```typescript
interface AppBackup {
  version: string            // 数据版本号（当前 1.6）
  exportedAt: string         // 导出时间 ISO 字符串
  fieldRuleSets: any[]       // 字段规则集
  caseFiles: any[]           // 用例文件
  recentFiles: any[]         // 最近文件记录
  favorites: string[]        // 收藏路径列表
  settings: Record<string, string>  // 应用设置（含 cloud_encryption_key）
  inputHistory: InputHistoryEntry[]  // 输入历史
  logSessions: LogSession[]  // 日志会话
  noteSpaces: NoteSpace[]    // 笔记 Space
  noteFolders: NoteFolder[]  // 笔记文件夹
  notes: NoteItem[]          // 笔记内容
  noteVersions: NoteVersion[]  // 笔记版本历史
  noteLinks: NoteLink[]      // 笔记双向链接
  scripts: Script[]          // 脚本文件
}
```

**自动加载流程**：
1. 应用启动时 `CaseSpaceLayout.onMounted` 检查 `localStorage['test-space:lastFilePath']`
2. 若存在路径，自动调用 `loadFromFile()` 恢复 `testCases`
3. Excel 导入完成后自动触发 `saveFile()` 持久化

### 9.2 数据库表结构

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `field_rule_sets` | 字段规则集 | id, name, rules(JSON), created_at, updated_at |
| `case_files` | 用例文件 | id, name, data(JSON), tags, custom_fields, rule_set_id |
| `recent_files` | 最近打开文件 | path, name, case_count, last_opened |
| `favorites` | 收藏路径 | path, added_at |
| `app_settings` | 应用设置 | key, value |
| `input_history` | 输入历史 | key_name, value, sort_order |
| `log_sessions` | 日志会话 | id, type, device_serial, status |
| `note_spaces` | 笔记 Space | id, name, sort_order |
| `note_folders` | 笔记文件夹 | id, space_id, name, parent_id, sort_order |
| `notes` | 笔记内容 | id, folder_id, title, content(HTML), tags(JSON), is_favorite |
| `note_versions` | 笔记版本历史 | id, note_id, content, saved_at |
| `note_links` | 笔记双向链接 | id, source_note_id, target_note_id |
| `scripts` | 脚本文件 | id, name, type, content, created_at, updated_at |
| `note_ai_memories` | AI 长期记忆 | id, content, created_at, updated_at |

### 9.3 权限配置

`src-tauri/capabilities/default.json` 添加：
- `"fs:default"` — 文件系统读写权限
- `"dialog:default"` — 原生对话框权限
- `"http:default"` — HTTP 请求权限（scope: `https://tms.zeasn.com/api/TestSpace/*`）
- `"core:webview:allow-create-webview-window"` — 弹出独立镜像窗口
- `windows: ["main", "mirror-*"]` — 允许 main 窗口和 `mirror-*` 模式窗口

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
| 布局组件（AppLayout / Sidebar / TopNav） | ✅ |
| Workspace 首页 | ✅ |
| Case Space（Table / MindMap / Document 视图） | ✅ |
| Device Space（设备列表 + 遥测 + Logcat + ADB Shell/APK/Files/Screen） | ✅ |
| Settings | ✅ |
| Notes Space（三面板 + 编辑器 + 目录树 + 上下文面板） | ✅ |
| Script Space | ✅ |
| Rust 原生层（ADB / 串口 / 脚本执行） | ✅ |

### Phase 2（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Notes Space TipTap 集成 | 替换 contenteditable 为 TipTap 富文本编辑器（Bold/Italic/Underline/Strike/H1/H2/H3/Lists/Blockquote/Code/Link/Image/Undo/Redo + Placeholder + BubbleMenu） | ✅ |
| Script Space 完整功能 | 脚本分类列表 + 命令输入 + 文件选择器（通过 tauri-plugin-dialog）+ Rust 后端执行 + 暗色终端实时输出 | ✅ |
| API 数据层（已移除） | 原 3 个 API 模块（dashboard / testcases / notes）已删除，本地应用无 HTTP 请求 | ✅ |
| Workspace API 对接（已移除） | 原 `fetchDashboardStats` / `fetchQuickActions` / `fetchProjects` 已删除，数据改为静态 mock | ✅ |
| Case Space API 对接（已移除） | 原 `fetchTestCases` 调用已删除，数据完全走本地 SQLite | ✅ |

### Phase 3（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Device Space ADB 对接 | `scanDevices` → `listDevices()` ADB 扫描 / `executeShell` → `shell()` 命令执行 / APK Install → `installApk()` 文件选择器 / Uninstall → `uninstallApk()` / Screenshot → `screenshot()` / File Push/Pull → `pushFile()`/`pullFile()` / Logcat 筛选 | ✅ |
| Case Space New Case（已移除） | 原 `createTestCase` API 对接已删除 | ✅ |

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
| 导航栏 | **Sidebar.vue** 6 个导航项 + Settings 链接：添加 `glass-hover`，活跃态替换为 `glass-active` | ✅ |
| 顶部导航（已移除） | **TopNav.vue** 整体删除 | ✅ |
| Tab 页签切换器 | **CaseSpaceLayout** / **CaseEditorPage** / **DeviceSpacePage** / **SettingsPage** 所有 tab 切换器：非活跃态 `glass-button`，活跃态 `glass-active` | ✅ |
| 卡片式交互 | **WorkspacePage** 快捷操作卡片 / **ScriptSpacePage** 分类卡片 / **DeviceSpacePage** 设备卡片 / **CaseSpacePage** 用例卡片 / **FieldRulesPage** 创建卡片 / **NotesSpacePage** 文件夹/文件/实体标签/问题卡片：添加 `glass-hover` | ✅ |
| 编辑器工具栏 | **NotesSpacePage** 15 个 TipTap 工具栏图标按钮 → `glass-button`，active 态切换为 `glass-active` | ✅ |
| 图标按钮 & 对话框 | 所有关闭/删除/取消/确认/返回/缩放图标按钮 → `glass-button`；危险操作按钮（删除确认）保留 `bg-error/10 text-error` 但使用 `glass-button` 框架 | ✅ |

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

### Phase 6 — 功能清理（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 移除登录页 | 删除 `Login.vue`、`auth.ts`、`captcha.ts`、`user.ts`（Pinia store），应用启动直入工作区 | ✅ |
| 简化 `request.ts` | 移除 JWT Token 注入、自动刷新、signKey 签名、401 重试等全部认证逻辑 | ✅ |
| 移除导航守卫 | 删除路由 `beforeEach` 守卫中的 token 检查和 `/login` 重定向 | ✅ |
| 移除 Platform Space | 删除 `AnalyticsPage.vue`、`DatabasePage.vue`、`VersionReleasePage.vue`、`PlatformLayout.vue` 及对应 3 个 API 模块 | ✅ |
| 清理路由 | 移除 `/login` 和 `/platform-space/*` 路由 | ✅ |
| 清理 Sidebar | 移除 "Platform Space" 导航项，精简 `isActive` 高亮逻辑 | ✅ |
| 清理类型定义 | 移除 `LoginCredentials`、`LoginResponse`、`CaptchaResponse`、`UserInfo`、`ApiResponse`、`VersionRelease`、`ChangelogItem`、`DatabaseTable` 接口 | ✅ |
| 简化 Settings | 移除 Platform Connection 卡片和 Sign Out 登出按钮，Profile 改为静态本地模式 | ✅ |
| 简化 Workspace | 问候语改为静态 "Tester"，移除 `useUserStore` 引用 | ✅ |
| 移除顶部导航栏 | 删除 `TopNav.vue`（每个页面顶部的 "Quick Action" 按钮栏），AppLayout 同步清理 | ✅ |
| 移除 HTTP API 层 | 删除 `request.ts`、`dashboard.ts`、`testcases.ts`、`notes.ts` 及 `src/api/` 目录，卸载 `axios`、`echarts` | ✅ |

### Phase 7 — Device Space 重构（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Device Space 双分页布局 | 重写为「常用命令」/「其他命令」双分页，连接栏上移，设备列表 5s 自动刷新 | ✅ |
| 日志采集前置准备 | Logcat/Diagnostic/Bugreport 统一前置 `prepareLogCapture()`：`adb root` → `logcat -G 64M` | ✅ |
| Logcat 圆形缓冲区 | 实时轮询 `-b all -t 1000`，缓冲区上限 500 条，级别/关键字筛选 | ✅ |
| Diagnostic 一次性采集 | 计时采集，stop 时一次性收集 logcat + dmesg + getprop + dumpsys + free + df + ps，每个日志类型保存为独立文件，最后打包为 ZIP 压缩包 | ✅ |
| Bugreport 集成 | 调用 Rust 后端 `adb_bugreport` 命令（异步执行，不阻塞 UI） | ✅ |
| Rust 后端新增 3 命令 | `adb_logcat_buffer_resize`、`adb_bugreport`、`adb_dmesg` — adb.rs + lib.rs 注册 | ✅ |
| Rust 新增 `adb_start_screenrecord` | 启动录屏时异步 spawn 执行，不阻塞 UI | ✅ |
| Rust 新增 `create_zip` | 传入文件列表和输出路径，直接生成 ZIP 压缩包（基于 `zip` crate） | ✅ |
| `useAdb` 新增 3 方法 | `logcatBufferResize()`、`bugreport()`、`dmesg()` | ✅ |
| SQLite `input_history` 表 | 输入历史走 `database.ts` CRUD，按 key+value 去重，每 key 最多 20 条 | ✅ |
| SQLite `log_sessions` 表 | 持久化运行中会话，`ON CONFLICT DO UPDATE` 幂等写入 | ✅ |
| 危险操作确认弹窗 | Reboot / Remount 触发 Teleport 红色警告弹窗 | ✅ |
| `exportAllData()` / `importAllData()` 同步 | 新增 `input_history` + `log_sessions` 表数据纳入完整导出/导入 | ✅ |
| 类型定义扩展 | `InputHistoryEntry`、`LogSession` 接口加入 `types/index.ts` | ✅ |
| 输入历史绑定 | text_input / app_search / connect_ip / remote_path 四种 key 绑定 SQLite 历史 | ✅ |
| 所有 Timer/ID 清理 | `onUnmounted` 中清理所有轮询 setTimeout/setInterval | ✅ |
| Custom Commands 保留 localStorage | 非业务数据、高频更新，仍用 localStorage | ✅ |
| 应用列表排序 | 与 web-adb-tool 一致排序规则：overlay 排末 → 四大应用置顶 → 优先级应用固定序 → whaletv → zeasn/rlaxxtv → 字母序 | ✅ |
| 应用列表分页 | 14 条/页 + 翻页按钮 + 版本号自动加载（队列化避免并发） | ✅ |
| 版本 chip + 复制 | 列表自动显示 v版本(Code) chip，点击包名/版本可复制到剪贴板 | ✅ |
| 查询 APK 路径 | 输入包名调用 `pm path` 查询安装路径 | ✅ |
| 设备信息内联显示 | 选中设备后自动展示序列号/型号/Android/分辨率/品牌/Build | ✅ |
| 配置修改对话框 | 支持路径 + 键名 + 值三段式写入设备（sed 模式） | ✅ |
| 应用列表自动刷新 | 选中设备时自动加载应用列表 + 首屏版本号 | ✅ |
| 执行输出面板 | ADB Shell 执行后底部实时显示输出，支持清除 | ✅ |

### Phase 8 — 交互优化与 Bug 修复（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 诊断包分文件打包 | stop 时收集每种日志到独立 txt 文件，最终打包为 ZIP 压缩包（基于 Rust `zip` crate 内存构建） | ✅ |
| 重启设备不卡 UI | `adb reboot`/`adb reboot recovery`/`adb reboot bootloader` 改为 Rust `spawn()` 异步执行，不等待返回值 | ✅ |
| 录屏启动不卡 UI | `screenrecord` 改为 Rust `adb_start_screenrecord` 命令通过 `spawn()` 异步启动，不阻塞 UI | ✅ |
| Bugreport 异步执行 | `adb_bugreport` 改为 `async fn` 通过 `tokio::task::spawn_blocking` 异步执行 | ✅ |
| Bugreport 保存路径修复 | 保存对话框默认扩展名改为 `.zip`，确保 ADB 正确识别输出路径 | ✅ |
| 命令执行反馈浮窗 | 长耗时操作（Root/Remount/重启/Bugreport/录屏等）点击后顶部弹出玻璃态浮动面板，显示实时执行状态和结果，完成后 2 秒自动关闭 | ✅ |

### Phase 10 — 导航重构与 UI 全面优化（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 左侧 Sidebar 改为顶部浮窗 | 固定左侧 256px Sidebar 移除，改为 fixed 顶部浮动导航栏，鼠标移入滑出，移出 400ms 后收起；进入动画 `0.3s cubic-bezier(0.16,1,0.3,1)` + opacity | ✅ |
| 导航项重命名 | Workspace 移除；Case Space→Case；Device Space→Device；Notes Space→Notes；Script Space→Scripts | ✅ |
| 布局适应 | AppLayout 移除 `md:ml-[256px]` 边距和 workspace 背景；CaseSpaceLayout 移除 `pt-12` | ✅ |
| 路由清理 | redirect `/workspace`→`/case-space`；移除 workspace route | ✅ |
| 窗口大小记忆 | `App.vue` onMounted 中用 `@tauri-apps/api/window` 保存/恢复窗口大小到 localStorage | ✅ |
| 命令执行弹窗优化 | 恢复为顶部通知横幅样式，不用全屏 modal；3 秒自动关闭，鼠标悬停暂停计时；快捷指令完成后不自动关闭 | ✅ |
| 字体放大 | Tailwind token: `caption` 11px→15px, `label-md` 13px→16px；加 `!important` 覆盖模板中的 `text-[11px]` 行内覆盖 | ✅ |
| 下拉列表不透明 | 文本历史、远程路径历史下拉从 `glass-panel` 改为 `bg-white border shadow-lg` | ✅ |
| 文件管理历史记录 | `navigateToPath()`/`navigateToDir()` 新增 `addInputHistory('remote_path')` 保存路径历史 | ✅ |
| navigateToParent 修复 | 根路径点"上级"正确导航到 `/` | ✅ |
| Windows 编码修复 | `script_exec.rs` 中 `chcp 65001>nul&&` 前缀解决中文命令输出乱码 | ✅ |
| Case Editor 工具栏修复 | 移除根 div `-mt-14`（导致 toolbar 推出视口），高度改为 `h-screen` | ✅ |
| Case 页面清理 | 移除 "Case Space" 标题和副标题，按钮行加 `mt-8` | ✅ |
| 文件列表圆角 | `rounded-xl`→`rounded`（4px） | ✅ |
| 屏幕镜像高度 | `min-h` 180px→300px，canvas `max-h` 300px→400px | ✅ |
| 快捷指令 2 列布局 | 单列 flex→`grid grid-cols-2 gap-2` | ✅ |

---

### Phase 22 — ADB 异步化 + 安装稳定性 + 拖拽优化 + 滚轮缩放（已完成 ✅）

> 解决三个核心问题：APK 下载冻结、APK 安装卡死、主窗口卡死。同时优化拖拽 APK 体验和图片预览滚轮缩放。

#### 22.1 ADB 命令全量异步化（`src-tauri/src/lib.rs`）

所有原同步 `#[tauri::command]` 改为 `async` + `tokio::task::spawn_blocking`，防止 ADB 进程阻塞 IPC 处理程序导致主窗口卡死：

| 命令 | 原实现 | 新实现 |
|------|--------|--------|
| `adb_shell` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_list_packages` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_start_app` / `adb_stop_app` / `adb_clear_app_data` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_get_current_app` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_logcat_clear` / `adb_logcat` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_get_battery` / `adb_get_cpu` / `adb_get_memory` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_list_directory` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_logcat_buffer_resize` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_dmesg` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_screenshot` | `async` 但直接调用 sync | `async fn` + `spawn_blocking` |
| `adb_connect` / `adb_disconnect` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_reboot` / `adb_reboot_recovery` / `adb_reboot_bootloader` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_root` / `adb_remount` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_get_properties` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_input_keyevent` / `adb_input_text` / `adb_input_tap` / `adb_input_swipe` | `fn` 同步 | `async fn` + `spawn_blocking` |
| `adb_kill_server` / `adb_start_server` | `fn` 同步 | `async fn` + `spawn_blocking` |

**原理**：`spawn_blocking` 将阻塞操作移到 Tokio 的阻塞线程池，不阻塞异步运行时和 IPC 处理程序。

#### 22.2 APK 安装修复（`src-tauri/src/lib.rs`）

| 问题 | 修复 |
|------|------|
| `adb install` 管道缓冲区死锁 | 改用 `tokio::process::Command::output()` — 使用 `try_join3` 并发读取 stdout/stderr，避免 Windows 管道缓冲区满时子进程阻塞 |
| 无超时，永远卡死 | 添加 `tokio::time::timeout(120s)`，超时后返回错误 |
| Windows 黑框 | `creation_flags(0x08000000)` (`CREATE_NO_WINDOW`) 通过 `as_std_mut()` 设置 |
| `run_adb_install` 辅助函数 | 已移除，直接在 `adb_install` 命令中实现 |

**旧实现**（`run_adb` + `std::process::Command::output()`）→ **新实现**（`tokio::process::Command::output()` + `timeout`）

#### 22.3 `adb_push_bytes` 修复（`src-tauri/src/lib.rs`）

| 问题 | 修复 |
|------|------|
| `push_file` 在 async 函数中同步调用 | 移入 `spawn_blocking` 线程池执行 |

#### 22.4 前端改动（`src/views/device-space/DeviceSpacePage.vue`）

| 改动 | 说明 |
|------|------|
| `reinstallApk` 默认值 | `ref(true)` → `ref(false)` |
| 前台应用加载动画 | 新增 `loadingForeground` ref，按钮显示 spinner（`border-2 border-t-white animate-spin`） |
| 拖拽临时文件清理 | 新增 `cleanApkTempPath()` 函数，通过 `@tauri-apps/plugin-fs` 的 `remove()` 删除旧临时文件 |
| 拖拽防并发 | `apkDropPending` 标志位，防止快速多次拖拽导致文件写入竞态 |
| 文件数据捕获时机 | `file.arrayBuffer()` 在任何 `await` 之前执行，避免 `e.dataTransfer` 引用过期 |
| 关闭对话框清理 | 新增 `closeApkDialog()` 函数，关闭时删除临时文件 |
| 安装成功清理 | `handleApkInstall` 成功后调用 `cleanApkTempPath` |
| 组件卸载清理 | `onUnmounted` 中遍历 `apkTempPaths` 数组删除所有残留临时文件 |
| 路径分隔符修复 | `baseDir` 和文件名之间补充分隔符（`sep` 变量） |
| 悬停显示完整路径 | `:title="apkFilePath"` 属性，鼠标悬停显示完整路径 |

#### 22.5 图片预览滚轮缩放（`src/views/device-space/DeviceSpacePage.vue`）

| 改动 | 说明 |
|------|------|
| 去掉 Vue `@wheel.prevent` | Vue 的 `@wheel.prevent` 在 WebView2 中不可靠 |
| 原生 `addEventListener` | `ref="previewContainerRef"` + `watch(previewDialog.content)` + `addEventListener('wheel', onPreviewWheel, { passive: false })` |
| `passive: false` | 确保 `preventDefault()` 能阻止浏览器默认滚动行为 |

#### 22.6 已知未修复项

| 项目 | 原因 |
|------|------|
| `install_apk` 死代码警告 | `adb.rs:117` 的 `install_apk` 函数不再被调用（`adb_install` 直接使用 `tokio::process::Command`），仅产生 `dead_code` 警告，不影响功能 |
| `adb input text` 非 ASCII 字符 | ADB 的 `input text` 命令不支持非 ASCII 字符（如 `·`、`×`），URL 编码后设备不解码，需配合特殊 IME 输入 |

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `cargo check` | ✅ 通过（1 warning: `install_apk` dead_code） |

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

### 11.5 通知与反馈

| # | 原则 | 说明 |
|---|------|------|
| 11 | **悬停暂停自动关闭** | 所有自动关闭的通知弹窗（命令执行结果等），鼠标悬停时必须暂停关闭计时，移出后恢复 |
| 12 | **不是全屏 modal** | 命令执行反馈使用顶部通知横幅（非全屏遮罩 modal），不遮挡页面内容 |

### 11.6 导航与布局

| # | 原则 | 说明 |
|---|------|------|
| 13 | **顶部浮动导航** | 导航栏为 fixed 顶部浮动条，鼠标移到屏幕顶部触发，移出后自动收起；不占页面空间、不影响内容布局 |
| 14 | **字体 > 11px** | 界面正文字号不得低于 13px，标注类文字（`caption`）不得低于 12px |
| 15 | **glass-panel 内 fixed 定位** | `glass-panel` 使用 `backdrop-filter: blur()` 会创建包含块，`position: fixed` 子元素被裁剪；下拉框/弹窗必须 `<Teleport to="body">` 脱离 glass-panel |
| 16 | **设备下拉框自定义** | 设备选择不得使用原生 `<select>`，必须使用自定义下拉面板（匹配应用搜索历史样式：`bg-white shadow-lg` 无边框），Teleport 到 body + `getBoundingClientRect()` 坐标定位 |
| 17 | **下拉列表无边框** | 所有输入框下拉列表（快捷操作输入历史、应用搜索历史、远程路径历史、设备选择下拉等）不得使用 `border` 类，仅用 `bg-white shadow-lg rounded-lg` 保持干净悬浮效果。边框线会让下拉列表显得粗糙臃肿，与玻璃态设计语言冲突 |
| 18 | **下拉条目 no-border** | `glass-panel` 内的 `<button>` 默认被 scoped CSS 加 `inset box-shadow` 模拟边框。若下拉条目（`<button>`）在 `.glass-panel` 内部（未 Teleport 到 body），必须添加 `no-border` 类排除该效果，否则条目间会出现分割线。Teleport 到 body 的下拉框天然不受影响 |

---

### 存储架构（持久化规则）

所有数据统一通过 SQLite 存储在用户的应用数据目录，**禁止**使用 localStorage（仅 dev 模式下文件读写降级）。

#### 数据库位置

- **Windows**: `%APPDATA%/com.testspace.app/test-space.db`
- **macOS**: `~/Library/Application Support/com.testspace.app/test-space.db`
- **Linux**: `~/.local/share/com.testspace.app/test-space.db`
- **开发模式**（浏览器 fallback）：页面数据从 `@tauri-apps/plugin-sql` 读取，若不可用则回退到 dev 文件读写

#### 数据表结构

| `note_ai_memories` | AI 长期记忆 | id, content, created_at, updated_at |

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `field_rule_sets` | 字段模板规则集 | `id`, `name`, `rules`(JSON), `created_at`, `updated_at` |
| `case_files` | 编写的用例文件 | `id`, `name`, `data`(全量 JSON), `tags`(JSON), `custom_fields`(JSON), `rule_set_id`, `created_at`, `updated_at` |
| `recent_files` | 打开历史记录 | `path`, `name`, `case_count`, `last_opened` |
| `favorites` | 收藏的文件 | `path`, `added_at` |
| `app_settings` | 应用设置（K/V） | `key`, `value` |
| `input_history` | 输入历史（Device Space） | `id`, `key`, `value`, `created_at` |
| `log_sessions` | 日志采集运行中会话 | `id`, `device_serial`, `session_type`, `status`, `started_at`, `ended_at`, `metadata`(JSON) |
| `note_folders` | 笔记文件夹 | `id`, `name`, `parent_id`, `sort_order`, `created_at`, `updated_at` |
| `notes` | 笔记内容 | `id`, `folder_id`, `title`, `content`(HTML), `tags`(JSON), `is_favorite`, `created_at`, `updated_at` |
| `note_versions` | 笔记版本历史（最多 20/条） | `id`, `note_id`, `content`, `saved_at` |
| `note_links` | 笔记双向链接 | `id`, `source_note_id`, `target_note_id`, `created_at` |

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

---

### Phase 9 — Device Space 应用管理优化（进行中）

| 模块 | 说明 | 状态 |
|------|------|------|
| 重启 ADB 服务 | 原 `shell echo restart` 替换为真正的 `adb kill-server` + `adb start-server`，新增 Rust 后端 `adb_kill_server` / `adb_start_server` 命令 | ✅ |
| 命令执行弹窗 | `showCmdExec` 新增 `command` 参数，显示实际执行的 ADB 命令（如 `adb root`、`adb reboot`），去重逻辑防止重复输出 | ✅ |
| 信息弹窗字体缩小 | 信息查询弹窗标题从 `text-headline-md` 改小为 `text-label-lg`，条目标签 `text-[13px]`，值 `text-[12px]` | ✅ |
| 密钥检查展开 | 密钥检查弹窗每项显示状态+命令，右侧折叠/展开按钮可查看原始输出 | ✅ |
| 前台应用获取 | 命令改为 `dumpsys window`（JS 侧过滤），兼容性更好 | ✅ |
| 设备断开清理 | `disconnectDeviceHandler` 清空 `apps` 列表；`scanDevices` 扫描时已选设备消失则自动清空状态 | ✅ |
| 前台应用/查询路径弹窗 | 不再内联显示在右侧，改为弹窗显示+复制按钮+手动关闭 | ✅ |
| 应用详情弹窗 | 去掉无用字段（首次安装/最近更新/安装来源/CPU架构），增加版本历史（多版本 `→` 连接）、应用大小/缓存大小/数据大小 | ✅ |
| 启动应用兜底 | monkey 失败后自动用 `am start -n` 解析主 Activity 兜底启动 | ✅ |
| 应用操作 cmdExec | 启动/停止/清除数据/卸载/下载 APK 均显示 cmdExec 命令执行弹窗（命令+进度+结果） | ✅ |
| 全局布局修复 | 主容器从 `h-[calc(100vh-80px)]` 改为 `h-screen`，消除底部 80px 空白；`html, body` 加 `overflow: hidden` 消除全局滚动条 | ✅ |
| 应用管理面板高度 | Row 3 从 grid 改为 flex，`flex-1 min-h-0` 填满 Tab 1 剩余空间；Panel `flex-1 min-h-0` 填满 Row 3 | ✅ |
| 应用列表自适应 | `recalcAppPageSize` 测量面板实际高度计算 `avail`，动态设置 `maxVisibleApps` 和 `maxHeight`；`ResizeObserver` + `window.resize` 监听变化 | ✅ |
| 应用条目间距 | 条目内边距从 `py-0.5` 减为 `py-0`，每条省 4px，显示更多应用 | ✅ |
| 翻页不重置 | `filteredApps` watcher 只在搜索关键词或总条数变化时重置页码，纯数据更新（如加载版本号）不重置 | ✅ |
| 页码位置 | 页码从列表底部移到搜索栏右侧，不影响列表高度计算 | ✅ |
| ADB 模块扩展 | `useAdb.ts` 新增 `killServer()` / `startServer()` 方法；`adb.rs` 新增 `kill_server()` / `start_server()`；`lib.rs` 注册 `adb_kill_server` / `adb_start_server` | ✅ |

---

### Phase 10 — 导航重构与 SQLite 全量迁移（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 顶部浮动导航栏重构 | 移除左侧固定 Sidebar，改为 8px 触发区 + 顶部浮动导航，带入场/收起动画 | ✅ |
| 导航项统一 glass 类 | 活跃态 `glass-active`，非活跃态 `glass-hover`，图标 FILL 0/1 | ✅ |
| Ctrl+Tab 快捷键 | 在 AppLayout 添加全局 `keydown` 监听，Ctrl+Tab 循环切换导航项 | ✅ |
| SQLite 全量迁移 | field_rule_sets / case_files / recent_files / favorites / app_settings / input_history / log_sessions 全部通过 `@tauri-apps/plugin-sql` 写入 `{appDataDir}/test-space.db` | ✅ |
| 开发模式降级 | 浏览器开发模式通过 `localStorage` 模拟 SQLite 读写 | ✅ |
| 数据库初始化防重 | `migrate()` 幂等执行：`CREATE TABLE IF NOT EXISTS` + 增量升级 | ✅ |
| `exportAllData` / `importAllData` | 统一 API 导出/导入 7 张表的全量数据，`AppBackup` 含版本号 | ✅ |
| 布局架构优化 | 重写页面高度链：`h-screen` → `flex-1 min-h-0` 链，消除底部空白，所有子面板弹性填充 | ✅ |
| Case 数据从 SQLite 读写 | `useTestCaseStore` 改为从 SQLite 加载/保存 field rule sets | ✅ |
| Device Space 输入历史持久化 | `addInputHistory` / `getInputHistory` 走 SQLite | ✅ |

### Phase 11 — Notes Space 完整重写：SQLite 持久化 + 全功能增强（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| SQLite 笔记表 | 新增 `note_folders` / `notes` / `note_versions` / `note_links` 四张表，`migrate()` 幂等创建，含索引 | ✅ |
| 笔记 CRUD 函数 | `loadNotes` / `saveNote` / `deleteNote` / `loadNoteFolders` / `saveNoteFolder` / `deleteNoteFolder` / `renameNoteFolder` | ✅ |
| 全文搜索 | `searchNotes()` 模糊匹配 title 和 content，支持实时输入搜索 | ✅ |
| 收藏功能 | `toggleNoteFavorite()` 切换星标，`getFavoriteNotes()` 加载收藏列表，Favorites 快捷入口 | ✅ |
| 标签管理 | 每个笔记多个标签，chips 展示可删除，输入框加 Enter 添加 | ✅ |
| 版本历史 | `saveNoteVersion()` 自动保存快照（30s 无操作触发），保留最近 20 个版本，`restoreVersion` 恢复 | ✅ |
| 双向链接 | `[[笔记标题]]` 语法自动解析，`addNoteLink` / `removeNoteLink` / `getNoteLinks` 管理 `note_links` 表，右侧面板显示链出和反链 | ✅ |
| 表格编辑器扩展 | `@tiptap/extension-table` + row/cell/header 子扩展，工具栏新增 Table 按钮，插入默认 3x3 表格 | ✅ |
| 导出/导入同步 | `AppBackup` 新增 `noteFolders` / `notes` / `noteVersions` / `noteLinks`，数据版本升至 `1.2` | ✅ |
| 全部通过 `npm run build` | TypeScript 类型检查零错误，Vite 构建零警告 | ✅ |

### Phase 12 — 屏幕镜像重构与导航优化（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| scrcpy-server 集成 | 下载 scrcpy-server v3.3.4（91KB）到 `src-tauri/bin/scrcpy-server`；`mirror.rs` 实现 push_server / setup_forward / remove_forward / start_server / connect_and_stream | ✅ |
| H.264 WebCodecs 渲染 | 通过 `Channel<Vec<u8>>` 直接投递原始字节（`0xFF + avcC` 标记配置消息，`0x00/0x01 + AVCC frame` 标记帧消息），前端 Channel `onmessage` 直接解码渲染，无队列、无 rAF 轮询、无 `adb_mirror_poll_frame` | ✅ |
| legacy screencap 兜底 | `adb_mirror_start` 在单 Rust 阻塞线程中顺序执行：先试 scrcpy（push → forward → start → 5s 等待 config），失败则 emit `mirror:mode=legacy` 切换到 `adb screencap` 轮询 — 无竞态条件 | ✅ |
| push_server 空 stderr 修复 | 原代码在 adb push 非零退出但 stderr 为空时返回 `Ok(())`，导致前端等待 H.264 帧永远超时；改为非零退出码直接返回 Err | ✅ |
| connect_and_stream 超时 | 增加 5 秒 config 包超时，超时返回 Err 触发 legacy 降级 | ✅ |
| 导航项重排序 | Tab 顺序改为 Device → Notes → Case → Scripts（router、Sidebar、App.vue Ctrl+Tab 快捷键同步更新） | ✅ |
| Device 页面静默扫描 | `onMounted` 中 `scanDevices(true)` 减少主线程阻塞 | ✅ |
| 全应用通过 `npm run build` 和 `cargo build` | TypeScript + Vite 构建和 Rust 编译均零错误零警告 | ✅ |

### Phase 13 — Notes Space 全面增强（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Space 目录结构 | 新增 `note_spaces` 表，`note_folders` 增加 `space_id` 字段；支持创建/重命名/删除 Space；文件夹支持无限层级嵌套（`parentId`） | ✅ |
| Space 下拉选择器 | 左侧面板顶部下拉框切换 Space，hover 显示编辑/删除按钮，删除有自定义 Teleport 模态二次确认 | ✅ |
| 文件夹嵌套 | `flatFolders` 递归展平树，`createSubFolder()` 在指定文件夹下创建子文件夹，缩进显示 | ✅ |
| 文件夹 "+" 下拉 | 点击文件夹右侧 "+" 弹出 Teleported 下拉框（`position: fixed` + `getBoundingClientRect`）：New Folder / New Note 两个选项，点击外部关闭 | ✅ |
| 拖拽移动笔记 | HTML5 drag-and-drop，`dragDropEnabled: false`（Tauri 配置），`onDragStart` 设置 `dataTransfer` + `effectAllowed`，`onDragEnd` 清理状态 | ✅ |
| 自动保存 | 1.5s 防抖自动写入 SQLite，`onUpdate` 触发，无需手动保存 | ✅ |
| 代码语法高亮 | `CodeBlockLowlight` + `highlight.js`（15 种语言：JS/TS/Python/CSS/XML/Bash/JSON/Markdown/SQL/C++/Java/PHP/Ruby/Rust/Go） | ✅ |
| 代码复制按钮 | `addCopyButtons()` 在 `onUpdate` / `selectNote` 中调用，`setTimeout` 多次重试确保 DOM 渲染完成 | ✅ |
| 剪切板粘贴图片 | `Image.configure({ allowBase64: true })` + `editorProps.handlePaste` 监听剪切板图片数据转 base64 | ✅ |
| 表格增删行列 | 光标在表格时工具栏显示：上/下加行、左/右加列、删行、删列（`isInTable` computed + `selectionVersion` 响应式） | ✅ |
| PDF 导出 | 隐藏 `<iframe>` 渲染 HTML 内容，对 `doc.body` 调用 `toPng` 避免污染主页面 DOM，`jsPDF` A4 多页分页 | ✅ |
| Word 导出 | `docx` npm 包生成真实 .docx 文件，`htmlToDocxChildren()` 解析 HTML → Paragraph/Table/Heading/Hyperlink | ✅ |
| Markdown 导出 | `turndown` HTML → Markdown | ✅ |
| TOC 目录面板 | `buildTocTree()` 构建标题树，`visibleTocItems` 展平可见节点，`tocCollapsed` 跟踪折叠状态；`bg-white/20` 80% 透明，全高度，点击外部关闭，`cubic-bezier(0.16,1,0.3,1)` 弹性动画 | ✅ |
| 工具栏样式 | `toolbar-btn` 无边框按钮，`toolbar-active` 淡紫色高亮，图标 20px | ✅ |
| 编辑区宽度 | `max-w-[850px]` 居中 + `border` 可见边框 + `shadow-md` 层次感 | ✅ |
| 搜索增强 | 搜索时自动展开含匹配结果的文件夹，匹配项黄色高亮 | ✅ |
| 选中态颜色 | 文件夹/文件/Favorites/TOC 选中态统一淡紫色 `bg-purple-100/60 text-secondary` | ✅ |
| 删除确认 | Space/文件夹/笔记删除均使用自定义 Teleport 模态框二次确认（红色删除按钮 + 白色取消按钮） | ✅ |
| DB 迁移兼容 | `ALTER TABLE note_folders ADD COLUMN space_id TEXT`（try-catch 防重复） | ✅ |
| `tauri.conf.json` | `dragDropEnabled: false` 启用 HTML5 拖放 | ✅ |
| 导出/导入同步 | `AppBackup` 新增 `noteSpaces` 字段（版本 1.3），导入含 `space_id` 列 | ✅ |
| 新增依赖 | `lowlight` / `@tiptap/extension-code-block-lowlight` / `jspdf` / `docx` / `turndown` | ✅ |

### Phase 14 — 设置优化与暗色模式（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| Settings 移除 Profile | 删除头像/用户名/角色静态展示区 | ✅ |
| Settings 合并模块 | Data Management 合并到 Appearance 卡片内，改为 "Data Backup" 子区域 | ✅ |
| Theme 切换 | Light / Dark / System 三选一，`applyTheme()` 操作 `document.documentElement.classList`，System 模式监听 `prefers-color-scheme`，持久化到 `app_settings` 表 | ✅ |
| Dark 模式 CSS | `main.css` 新增 `html.dark` 暗色模式：背景 `#1a1a2e`，`glass-panel`/`glass-card`/`glass-button`/`glass-active`/`glass-input` 暗色变体，文字颜色、选区颜色、滚动条适配 | ✅ |
| 窗口大小配置 | 移除窗口大小持久化逻辑（`App.vue` 无 `onResized`/`setSize`），`tauri.conf.json` 默认 1024×680 + 最小 1024×680 | ✅ |
| 导出/导入修复 | `exportAllData` 新增 `noteSpaces` 导出，`importAllData` 新增 `note_spaces` DELETE + INSERT，`note_folders` INSERT 含 `space_id` 列，版本升至 1.3 | ✅ |

### Phase 15 — Windows 黑框修复与版本发布（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| CREATE_NO_WINDOW | `adb.rs` / `script_exec.rs` / `mirror.rs` 所有 `Command::new()` 调用添加 `creation_flags(0x08000000)`（Windows `CREATE_NO_WINDOW`），消除执行 adb/shell 命令时弹出的黑色控制台窗口 | ✅ |
| 辅助函数封装 | `adb.rs` + `mirror.rs` 新增 `adb_cmd()` 封装函数，`script_exec.rs` 新增 `silent_cmd(prog)` 封装函数，统一注入 `CREATE_NO_WINDOW` 标志 | ✅ |
| 条件编译 | `#[cfg(target_os = "windows")]` 条件导入 `std::os::windows::process::CommandExt`，`creation_flags` 仅在 Windows 平台生效 | ✅ |
| 版本发布 | v0.1.1，作者 Bing，窗口默认 1024×680 | ✅ |
| productName 去空格 | `productName` 从 `"Test Space"` 改为 `"TestSpace"`（避免 MSI 卸载快捷路径编码异常）；窗口标题保持 `"Test Space"` | ✅ |

### Phase 16 — 国际化 i18n（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| i18n 系统 | `src/composables/useI18n.ts` — 轻量级 Vue composable，支持 `zh` / `en` 双语，`t()` 函数支持 `{param}` 插值，语言持久化到 `localStorage` | ✅ |
| Settings 语言切换 | Settings 页面顶部新增语言切换按钮（中文 / English），点击即时切换，无需重启 | ✅ |
| Settings 页面翻译 | 主题切换（浅色/深色）、数据备份与恢复、导出/导入按钮及状态提示 | ✅ |
| Sidebar 导航翻译 | 所有导航项（设备/笔记/脚本/用例/设置）支持双语 | ✅ |
| Scripts 页面翻译 | 工具栏按钮（新建/打开/保存/导出/运行）、控制台（运行中/已终止/清空/停止）、搜索框、排序标签、删除/类型切换确认对话框、Toast 提示、代码片段描述 | ✅ |
| Device 页面翻译 | 连接栏、设备操作、快捷操作、应用管理、快捷指令、文件管理、屏幕镜像、遥控器、截图/录屏、所有 Toast 提示和命令执行消息 | ✅ |
| Notes 页面翻译 | 搜索框、目录、新建文件夹/笔记、收藏、未分类、删除确认对话框、导出菜单、工具栏按钮（粗体/斜体/下划线/删除线/标题/列表/引用/撤销/重做） | ✅ |
| Case 页面翻译 | 模块/用例节点、字段标签（用例编号/所属模块/用例标题/前置条件/操作步骤/预期结果/用例等级/自动化/备注） | ✅ |
| useTestCaseStore 翻译 | `labelCn` 字段改用 `t()` 调用，支持双语切换 | ✅ |

**i18n 实现细节**：

- **文件位置**：`src/composables/useI18n.ts`
- **翻译 key 约定**：`页面.元素`（如 `scripts.new`、`device.connect`、`notes.toc`）
- **语言检测**：启动时从 `localStorage('app-lang')` 读取，默认 `zh`
- **响应式切换**：`lang` 是 `ref`，所有 `t()` 调用自动响应语言变化
- **插值语法**：`t('key', { param: value })` 替换 `{param}` 占位符
- **已翻译页面**：Settings、Sidebar、Scripts、Device、Notes、Case Editor、CaseSpacePage、useTestCaseStore

---

### 布局架构说明（Device Space）

页面高度链：

```
html, body          → overflow: hidden; height: 100%
主容器              → h-screen (100vh); overflow-hidden; flex
  内容区            → flex-1; flex flex-col; overflow-hidden
    Tab 1           → flex-col; flex-grow; min-h-0; overflow-hidden
      Row 1 (设备操作) → grid; 自适应高度
      Row 2 (日志采集) → grid; 自适应高度
      Row 3 (应用管理) → flex-1; min-h-0; flex flex-col
        Panel       → flex-1; min-h-0; flex flex-col
          Header    → 固定高度
          Search    → 固定高度
          App List  → flex-1; min-h-0; overflow-y-auto; maxHeight (动态)
```

`recalcAppPageSize` 测量面板实际高度，计算列表可用空间，动态设置 `maxVisibleApps`（分页条数）和 `maxHeight`（列表最大高度）。

---

## 十二、版本管理与发布流程

### 版本号来源

版本号同时记录在三个文件中，必须保持一致：

| 文件 | 路径 |
|------|------|
| `package.json` | `version` 字段 |
| `tauri.conf.json` | `version` 字段（Tauri 构建时读取） |
| `Cargo.toml` | `[package] version`（Rust 编译时读取） |

### 自动版本脚本 (`scripts/bump-version.mjs`)

一次性更新上述三个文件的版本号。

```bash
node scripts/bump-version.mjs patch    # 0.1.1 → 0.1.2
node scripts/bump-version.mjs minor    # 0.1.1 → 0.2.0
node scripts/bump-version.mjs major    # 0.1.1 → 1.0.0
```

### 清理脚本 (`scripts/clean.mjs`)

删除 `dist/` 前端缓存目录，确保打包时前端代码是最新的。
Rust 编译缓存（`src-tauri/target/`）通常无需清理，只在 Rust 代码缓存异常时执行 `node scripts/clean.mjs --full`。

### NPM Scripts

| 命令 | 说明 |
|------|------|
| `npm run version:patch` | 仅递增补丁版本号（如 0.1.1 → 0.1.2） |
| `npm run version:minor` | 仅递增次版本号（如 0.1.1 → 0.2.0） |
| `npm run version:major` | 仅递增主版本号（如 0.1.1 → 1.0.0） |
| `npm run release:patch` | **一键发布**：打补丁版本 → 清理缓存 → `tauri build` |
| `npm run release:minor` | **一键发布**：打次版本 → 清理缓存 → `tauri build` |
| `npm run release:major` | **一键发布**：打主版本 → 清理缓存 → `tauri build` |

### 发布流程

```bash
# 一键发布（推荐）
npm run release:patch

# 或手动分步执行
node scripts/bump-version.mjs patch
node scripts/clean.mjs
npm run tauri build
```

构建产物位于 `src-tauri/target/release/bundle/msi/`，文件名为 `TestSpace_x.y.z_x64.msi`（或 `.exe` NSIS 安装包）。

### 关于覆盖安装

Windows MSI 安装包根据**版本号**判断是否可以覆盖安装：

| 情况 | 结果 |
|------|------|
| 新版本号 > 已安装版本 | ✅ 自动升级，保留数据 |
| 新版本号 == 已安装版本 | ❌ 拒绝安装，提示先卸载 |
| 新版本号 < 已安装版本 | ❌ 提示"已安装更新版本" |

因此每次发布前必须**递增版本号**（`release:*` 脚本会自动处理）。`identifier`（`com.testspace.app`）保持不变，MSI 的 `UpgradeCode` 通过 identifier 自动生成，确保新旧版本可关联。应用数据存储在 `%APPDATA%/com.testspace.app/test-space.db`，升级安装不会丢失。旧版 MSI 无需手动卸载，新版直接覆盖即可。

### Phase 17 — i18n 补充 + 功能增强 + 系统托盘（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| CaseSpacePage 全面翻译 | 所有英文文本替换为 `t()` 调用（新建用例文件/字段模板/收藏/最近文件/空状态/新建对话框/删除确认等），新增 21 个中英文翻译键 | ✅ |
| CaseSpacePage 删除确认 | 最近文件删除按钮（close 图标）新增 Teleport 确认弹窗，防止误删 | ✅ |
| Default Fields 模板修复 | `useTestCaseStore` 中 `defaultSet.rules` 为空时自动填充 `makeDefaultFieldRules(t)`，修复数据库加载空规则导致模板字段丢失 | ✅ |
| Settings 卡片合并 | 四个独立卡片合并为单个 `glass-panel`，用分割线隔开语言/主题/备份/版本四个区域 | ✅ |
| Settings 层级感 | 卡片从 `glass-card` 改为 `glass-panel` + `shadow-md`，与设备页面风格一致 | ✅ |
| Settings 版本号 | 底部新增版本卡片，通过 `@tauri-apps/api/app` 的 `getVersion()` 读取版本号 | ✅ |
| 诊断包 ANR 导出 | `stopDiagnosticCapture` 新增 ANR traces 采集，遍历 `/data/anr/` 目录，逐个 cat 并以 `anr/` 前缀打包进 zip | ✅ |
| 运行中按钮样式 | 实时日志/诊断包/开机日志三个按钮运行时背景变红（`bg-error/20`），文字显示"停止"，倒计时用等宽字体显示 | ✅ |
| MAC 查询 adb root | `queryInfo("mac")` 中在读取 MAC 地址前先执行 `adbRoot(serial)` | ✅ |
| 关闭按钮→系统托盘 | 点击关闭按钮隐藏窗口到系统托盘（右下角通知区域），不退出应用 | ✅ |
| 系统托盘图标 | 使用应用默认图标，tooltip "TestSpace"，右键菜单：显示窗口 / 退出 | ✅ |
| 系统托盘点击恢复 | 左键或右键单击托盘图标弹出菜单，点击"显示窗口"恢复窗口并聚焦 | ✅ |
| NSIS 安装器配置 | `tauri.conf.json` 新增 `nsis` 和 `wix` 安装器配置，NSIS 支持 `installMode: "both"` | ✅ |
| 导出图标修正 | Settings 导出按钮改为 `file_upload`（↑），导入按钮改为 `file_download`（↓）；Scripts 导出按钮改为 `file_upload`（↑） | ✅ |
| Tauri 权限更新 | `capabilities/default.json` 新增 `core:window:allow-hide`、`core:window:allow-close`、`core:tray:default` | ✅ |
| Rust Cargo.toml | 新增 `tray-icon` feature；新增 `encoding_rs` 依赖（GBK 编码支持） | ✅ |

### Phase 18 — 单实例 + NSIS 快捷方式去重（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 单实例防重复启动 | 集成 `tauri-plugin-single-instance`（Cargo.toml + lib.rs），注册为 Builder 首个插件；第二次双击 exe 时自动 `show()` + `set_focus()` 聚焦已有窗口，第二进程退出 | ✅ |
| NSIS 快捷方式去重 | 新建 `src-tauri/windows/hooks.nsh`，通过 `NSIS_HOOK_PREINSTALL` 在安装前从当前用户和所有用户位置同时删除旧的桌面/开始菜单快捷方式，解决切换安装模式（perUser/perMachine）或升级不卸载产生的重复快捷方式 | ✅ |

**关联文件**：
| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `src-tauri/Cargo.toml:23` | 新增依赖 | `tauri-plugin-single-instance = "2"` |
| `src-tauri/src/lib.rs:17` | 新增导入 | `use tauri_plugin_single_instance::init as single_instance_init` |
| `src-tauri/src/lib.rs:369-375` | 新增调用 | 注册 single-instance 插件回调 `show()` + `set_focus()` |
| `src-tauri/windows/hooks.nsh` | 新建文件 | NSIS 预安装钩子，清理两个上下文位置的旧快捷方式 |
| `src-tauri/tauri.conf.json:47` | 新增配置 | `installerHooks: "./windows/hooks.nsh"` |

### Phase 21 — 文件管理器优化 + 大文件安全 + 云端备份收尾（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 文件预览取消支持 | 移除 `<Transition>` 包裹（动画阻止即时关闭），backdrop 直接 `@click="cancelPreview"`，所有按钮 `.stop` 修饰符防止事件冒泡，`previewGen` 计数器丢弃过期 `shell()` 结果 | ✅ |
| 大文件预览确认 | `previewFile`：`rawSize > 10MB` 时弹窗确认，用户点继续后 `showToast(msg, 'loading')` 常显 spinner 提示 UI 将卡住，加载完成后 `hideToast()` 关闭 | ✅ |
| 大文件编辑确认 | `editFile`：`wc -c` 检测 > 5MB 弹窗确认，流程同上 | ✅ |
| 不支持预览的文件类型 | 新增 `isUnsupportedFile()`：apk/exe/dll/so/dylib/bin/dat/db/sqlite/zip/tar/gz/rar/7z/woff/ttf/otf/pyc/class 等，点击直接 toast 提示不支持 | ✅ |
| Toast loading 类型 | 新增 `"loading"` 类型：spinner 旋转图标 + 不自动消失，`hideToast()` 手动关闭 | ✅ |
| confirmThen 重构 | 返回 `Promise<boolean>`，action 参数改为可选；取消/遮罩关闭调用 `onCancel()` 正确 resolve `false` | ✅ |
| 文件夹直接下载 | `downloadDir` 改用 `open({ directory: true })` 选择本地目录 + 直接 `adb pull`，移除设备端 `tar.gz` 压缩步骤 | ✅ |
| 右键菜单复制路径 | 文件右键菜单新增 Copy Path，`navigator.clipboard.writeText()` 复制完整远程路径 | ✅ |
| 云端备份恢复简化 | 移除 Cloud Manage Modal / Cloud Restore Modal / manage 按钮；云端恢复直接拉取最新备份 | ✅ |
| 设置页状态消息修复 | `statusIsError` ref 替代 `startsWith('Error')` 字符串匹配（适配多语言），`setStatus(msg, isError)` 统一控制红绿色 | ✅ |
| 取消操作清除状态 | `handleImport`/`handleExport`/`handleCloudRestore` 取消文件选择器后清除 statusMessage | ✅ |

#### 21.1 主窗口阻塞风险分析

| 操作 | 阻塞风险 | 说明 |
|------|----------|------|
| `loadPreviewContent` (`cat \| base64`) | **已知，用户接受** | 大文件 base64 结果通过 Tauri IPC 传输，期间 UI 线程阻塞；用户已确认弹窗提示后继续 |
| `editFile` (`cat`) | **已知，用户接受** | 同上，非媒体大文件 cat 阻塞 IPC；已加 wc -c 前置检查 + 确认弹窗 |
| `downloadDir` (`pullFile`) | **无风险** | `adb_pull` 在 Rust `spawn_blocking` 线程执行，不阻塞 JS 线程 |
| `downloadFile` (`pullFile`) | **无风险** | 同上 |
| `confirmThen` 弹窗 | **无风险** | Teleport 到 body，DOM 立即更新 |
| `showToast('loading')` | **无风险** | 纯前端响应式更新 |
| `open({ directory: true })` | **无风险** | Tauri 原生对话框，系统级渲染 |
| `isUnsupportedFile` 检查 | **无风险** | 纯正则匹配，< 1ms |

---

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `npx vue-tsc --noEmit` | ✅ 通过 |
| `npx vite build` | ✅ 通过 |

### Phase 19 — 文件管理器恢复与 UI/UX 全面优化（已完成 ✅）

> 基线提交：`d5c9017`

#### 19.1 文件管理器功能恢复

文件管理器在之前的一次代码损坏中丢失核心功能，本次完整恢复并增强：

| 功能 | 说明 | 状态 |
|------|------|------|
| 目录列表排序 | 文件夹在前、文件在后，各自按字母升序排列 | ✅ |
| `..` 返回上级 | 非根目录时自动在列表头部插入 `{ name: '..', isDir: true }`，catch 块同样保留 | ✅ |
| 单击交互 | `handleEntryDblClick` → `handleEntryClick`，单击条目即可导航/预览 | ✅ |
| `..` 返回上级导航 | 点击 `..` 条目调用 `navigateToParent()`，使用 `arrow_back` 图标 + `text-secondary` 颜色 | ✅ |
| 移除父目录按钮 | 顶部工具栏的"Parent Dir"按钮已删除，返回上级统一通过 `..` 条目 | ✅ |
| Tauri 原生拖放 | 监听 `onDragDropEvent`（Tauri 2 API），`onUnmounted` 中 `unlistenDragDrop` 清理 | ✅ |
| 拖放上传路径复用 | `uploadFilePath(selected)` 抽取为公共函数，拖放和文件选择器共用 | ✅ |
| 引号路径 | `adb push/pull` 命令中的本地/远程路径加双引号，避免空格路径问题 | ✅ |
| `finishCmdExec()` 补全 | upload/download/dir download 的 catch 块中调用 `finishCmdExec()` 确保命令弹窗正确关闭 | ✅ |
| `rawSize` 字段 | `FileEntry` 接口新增 `rawSize: number`（原始字节数），`parseLsLine` 解析并返回 | ✅ |
| `await nextTick()` | `uploadFile`/`downloadFile`/`downloadDir` 等重操作前先 `await nextTick()`，让 UI 响应后再执行 | ✅ |

#### 19.2 文件预览系统增强

| 功能 | 说明 | 状态 |
|------|------|------|
| `previewDialog` 重构 | `previewFile(entry: FileEntry)` 接收完整条目，打开对话框时重置 `previewScale = 1` | ✅ |
| `loadPreviewContent` MIME 映射 | 图片/视频/音频均使用精确 MIME 类型（如 `image/jpeg`、`video/webm`、`audio/flac`），不再用 `image/${ext}` 通配 | ✅ |
| 音频预览支持 | `isAudioFile()` 识别 FLAC/mp3/wav/ogg/aac/m4a/wma，`<audio controls autoplay>` 渲染，音频不套缩放 wrapper | ✅ |
| 缩放控件 | zoom in/out/reset 三按钮 + 百分比显示，范围 0.25x–5x，步进 0.25x | ✅ |
| 鼠标滚轮缩放 | `@wheel.prevent="onPreviewWheel"`， deltaY < 0 放大、> 0 缩小 | ✅ |
| 响应式对话框 | `w-[95vw] lg:w-[90vw] max-w-7xl max-h-[85vh] lg:max-h-[90vh]`，padding 响应式 `p-3 lg:p-4 xl:p-6` | ✅ |
| 图片不可拖拽 | `<img draggable="false">` + `select-none`，防止浏览器默认拖拽行为 | ✅ |
| i18n 新增 key | `device.dropToUpload`、`device.previewNotAvailable`（中/英） | ✅ |

#### 19.3 全局 `select-none` / `select-text`

跨 8 个页面 + AppLayout 统一应用文本选中行为：

| CSS 类 | 应用范围 |
|--------|----------|
| `select-none` | 所有 `<button>`、`<h3>`/`<h4>` 标题、根 `<div>`、文件历史下拉项、导航项 |
| `select-text` | 所有 `<input>`、`<textarea>`、`<pre>` 元素 |

#### 19.4 设备连接持久化

| 功能 | 说明 | 状态 |
|------|------|------|
| 记忆上次设备 | `selectDevice()` 中 `localStorage.setItem('last_device_serial', serial)` | ✅ |
| 启动恢复 | `scanDevices()` 完成后从 `localStorage.getItem('last_device_serial')` 恢复选中设备，若设备不存在则选首个 | ✅ |
| 断开清理 | `disconnectDeviceHandler(serial)` 中若断开的是当前选中设备，则 `localStorage.removeItem('last_device_serial')` | ✅ |

#### 19.5 应用列表版本号并行加载

| 优化前 | 优化后 |
|--------|--------|
| 逐个串行 `loadAppVersion(app)`，Promise 链式等待 | `Promise.all(batch)` 并行加载，每批 4 个，批间 `await new Promise(r => setTimeout(r, 80))` 限流 |
| 未使用的 `versionQueue` 变量 | 已删除 |

#### 19.6 设备选择下拉框自定义

| 功能 | 说明 | 状态 |
|------|------|------|
| 自定义下拉面板 | 替换原生 `<select>`，样式匹配应用搜索历史下拉（`bg-white border shadow-lg`） | ✅ |
| 显示内容 | 状态指示灯 + 设备名 + 序列号 + 断开按钮 | ✅ |
| Teleport 到 body | `<Teleport to="body">` 避免 `glass-panel` 的 `backdrop-filter: blur()` 创建包含块导致 `fixed` 定位被裁剪 | ✅ |
| 点击外部关闭 | `fixed inset-0 z-50` 透明遮罩 + `@click` 关闭 | ✅ |
| 扫描按钮关闭 | `scanDevices()` 调用前先 `showDeviceDropdown = false` | ✅ |

#### 19.7 连接栏布局修复

| 修复 | 说明 | 状态 |
|------|------|------|
| 防垂直堆叠 | `flex-nowrap overflow-hidden` 防止连接栏在窄窗口时子元素换行 | ✅ |
| 连接按钮不缩 | `shrink-0` 确保 Connect 按钮不被挤压 | ✅ |
| IP 输入框最小宽度 | `min-w-[160px] flex-1 max-w-[360px]` 确保输入框有合理宽度 | ✅ |
| 隐藏滚动条 | `overflow-hidden` 替代 `overflow-x-auto`，连接栏不再显示水平滚动条 | ✅ |

#### 19.8 拖放上传遮罩滚动修复

| 问题 | 修复 | 状态 |
|------|------|------|
| 拖放遮罩随列表滚动消失 | 拖放遮罩从滚动容器内部移出，放入 `relative flex-1 min-h-0` 包裹容器中；滚动容器改为 `absolute inset-0 overflow-y-auto`，遮罩 `absolute inset-0 z-10 pointer-events-none` 始终覆盖可视区域 | ✅ |

#### 19.9 其他样式调整

| 调整 | 说明 |
|------|------|
| 文件列表分隔线加粗 | `border-outline-variant/10` → `/20`，视觉区分更清晰 |
| 文件名加大 | `text-[11px]` → `text-[12px]`，提高可读性 |
| `..` 条目样式 | `arrow_back` 图标 + `text-secondary` 文字色，action 按钮隐藏 |
| 远程控制按钮响应式 | 4 级尺寸：`lg:`/`xl:`/`2xl:` 断点，按钮大小/间距/图标随视口缩放 |
| 文件列表移除灰底 | `bg-[#1a1c1d]/5` 背景移除 |
| 文件列表无文件大小列 | 模板中删除 size 列展示（`rawSize` 仅保留用于排序/预览逻辑） |
| 文件条目圆角+悬停 | `hover:bg-secondary/5 hover:scale-[1.02] transition-transform duration-200 rounded` |

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |

### Phase 20 — 全面代码审计与健壮性修复（已完成 ✅）

> 对全软件所有页面进行系统性审计，修复 8 个 CRITICAL + 12 个 HIGH + 15 个 MEDIUM 级别问题。

#### 20.1 数据库层修复（`src/services/database.ts`）

| 问题 | 严重级别 | 修复 |
|------|----------|------|
| `getDb()` 并发初始化创建多个连接 | CRITICAL | 改用 `dbPromise` 单例守卫，第二次调用等待第一次完成 |
| `importAllData()` 无事务保护 | CRITICAL | 包裹 `BEGIN TRANSACTION` / `COMMIT` / `ROLLBACK`，失败时回滚 |
| `deleteNoteSpace()` SQL 顺序错误 | CRITICAL | 调换顺序：先 `UPDATE notes SET folder_id=NULL` → 再 `DELETE folders` → 最后 `DELETE space` |
| `JSON.parse` 无保护 | MEDIUM | 新增 `safeJsonParse<T>(raw, fallback)` 辅助函数，所有 JSON 解析包裹 try/catch |
| SQL `LIKE` 通配符注入 | HIGH | 新增 `escapeLike(s)` 转义 `%` 和 `_`，`searchCaseFiles` / `searchNotes` 使用转义后的查询 |
| `saveNote` / `saveScript` 先查后写竞态 | MEDIUM | 改用 `INSERT ... ON CONFLICT DO UPDATE`（UPSERT），单条原子语句 |
| `deleteNote` 非原子 | HIGH | 包裹事务：`BEGIN` → `DELETE versions` → `DELETE links` → `DELETE note` → `COMMIT` |
| `toggleFavorite` TOCTOU 竞态 | HIGH | `INSERT OR IGNORE` 防止并发重复插入 |
| `deleteNoteFolder` 不处理子文件夹 | MEDIUM | BFS 收集所有后代文件夹 ID，批量移动笔记到未分类，再批量删除 |

#### 20.2 笔记页面修复（`NotesSpacePage.vue`）

| 问题 | 严重级别 | 修复 |
|------|----------|------|
| `onBeforeUnmount` 异步保存丢失 | CRITICAL | 改用 `lastEditorContent` ref 同步保存，不引用已销毁的 editor 实例 |
| `v-html` 存储型 XSS | CRITICAL | 删除确认对话框中用户输入改用 `escapeHtml()` 转义 |
| 版本快照捕获错误笔记 ID | HIGH | 定时器创建时捕获当前 `selectedNoteId`，执行时不再读取最新值 |
| `selectNote` 保存失败阻塞切换 | HIGH | `saveCurrentNote()` 包裹 try/catch，失败时仍允许切换 |
| 删除函数先关对话框后操作 | HIGH | 目标清空改为 `await` 之后 + try/catch |
| `uncategorizedNotes` 跨 Space | MEDIUM | 未选择 Space 时返回空数组 |
| `confirmRename` 无错误处理 | MEDIUM | 包裹 try/catch + 错误 toast |
| `onDrop` 无错误处理 | MEDIUM | `db.saveNote` 包裹 try/catch |
| 删除死代码 `deleteSpace` | LOW | 移除未使用的重复函数 |
| 复制多行文本多余空行 | HIGH | `clipboardTextSerializer` 块分隔改为单 `\n` |
| 复制 SQL/脚本含 NBSP 导致外部执行失败 | HIGH | 复制纯文本时归一化 `\u00A0` 等为普通空格，移除零宽字符 |
| 字体颜色工具栏 | 功能 | `TextStyle` + `Color` 扩展；Word 式分体按钮 + 8 色预设 Teleport 下拉 |
| 颜色面板被编辑区遮挡 | MEDIUM | 预设色面板 Teleport 到 `body`，`z-[9999]` |
| A 图标双下划线 | LOW | 弃用 `format_color_text` 图标，改用粗体 `A` + 自定义 `.color-split-bar` |

#### 20.3 用例编辑器修复（`CaseEditorPage.vue`）

| 问题 | 严重级别 | 修复 |
|------|----------|------|
| ResizeObserver 未断开 | CRITICAL | `onUnmounted` 中 `_resizeObserver?.disconnect()` |
| `saveFile` 交换模式数据丢失 | CRITICAL | 添加 `_isSaving` 守卫 + `try/finally` + 深拷贝 filtered content |
| document 事件监听器泄漏 | HIGH | `onUnmounted` 中清理所有 7 个 document 级监听器（`_docListeners` Map 追踪） |
| `initTextarea` rAF 泄漏 | MEDIUM | 改用 `WeakMap<HTMLElement, number>` 追踪，新 rAF 前取消旧的 |
| `clipboard.writeText` 无 catch | LOW | 添加 `.catch(() => {})` |

#### 20.4 设备页面修复（`DeviceSpacePage.vue`）

| 问题 | 严重级别 | 修复 |
|------|----------|------|
| Shell 命令注入（`queryPackageName`） | CRITICAL | 新增 `sanitizeShellArg()` 函数，应用于 6 处 shell 命令拼接 |
| `takeScreenshot` catch 缺 `finishCmdExec` | HIGH | catch 块添加 `finishCmdExec()`，防止弹窗卡死 |
| `stopDiagnosticCapture` null 断言崩溃 | HIGH | 入口添加 `if (!selectedDevice.value) return` 守卫 |
| `loadFileList` 竞态条件 | HIGH | 添加 `loadFileListGen` 生成计数器，await 后检查过期 |
| `infoDialogExpanded` Set 不触发响应式 | HIGH | `toggleInfoExpand` 每次创建新 Set 赋值 |
| `operationInProgress` 永远为 false | MEDIUM | 移除无用变量，改为内联检查 `pkgLoading`/`scanLoading`/`connecting` |
| `showToast` 定时器累积 | MEDIUM | 添加 `toastTimer` 变量，新 toast 前清除旧定时器 |
| 历史下拉不更新新条目 | MEDIUM | `addInputHistory` 后同步更新本地 `textHistory`/`remotePathHistory`/`appSearchHistory` 数组 |
| 版本加载每条 clone 全数组 | MEDIUM | 改为批量 fetch 完成后单次 `map` 更新 |
| `versionQueue` 死代码 | LOW | 移除未使用变量 |
| `v-for` key 使用索引 | LOW | 文件条目改用 `entry.name`，历史改用 `h` |

#### 20.5 脚本页面修复（`ScriptSpacePage.vue`）

| 问题 | 严重级别 | 修复 |
|------|----------|------|
| `totalPages` computed 内修改 `currentPage` | HIGH | 移至 `watch(totalPages, ...)` ，放在 `filteredScripts` 定义之后 |
| `runCurrentScript` 无并发保护 | HIGH | 添加 `isRunning` 守卫 + `finally` 块 |
| `doDelete` 无 try/catch | MEDIUM | 包裹 try/catch + 错误 toast |
| `mkdir` 错误静默吞掉 | MEDIUM | 添加 `console.warn` 日志 |
| `genId` 低熵 | LOW | 改用 `crypto.randomUUID().slice(0, 12)` |
| 临时脚本文件未清理 | MEDIUM | （已知，待后续处理） |
| `useScriptRunner` elapsedTimer 泄漏 | MEDIUM | `onUnmounted` 中调用 `destroy()` |
| 路径拼接缺少分隔符 | HIGH | `appDataDir()` 结果后补 `\`，`mkdir` 加 `{ recursive: true }` |
| 分页按钮距离过远 | LOW | `justify-between` → `justify-center gap-2` |
| 代码片段气泡被截断 | MEDIUM | 位置自适应（上方空间不足时显示在下方）+ `max-h-[40vh] overflow-y-auto` |

#### 20.6 字段规则页面修复（`FieldRulesPage.vue`）

| 问题 | 严重级别 | 修复 |
|------|----------|------|
| `editRuleSet` 直接修改 store 引用 | HIGH | 改用 `JSON.parse(JSON.stringify(...))` 深拷贝到本地 `editingRules` |
| `addNewField`/`removeField` 修改 store | HIGH | 操作改为修改 `editingRules` 本地副本 |
| `onDragLeave` null relatedTarget | MEDIUM | 添加 null 检查 |
| `onDrop` stale dragIdx | MEDIUM | 添加越界检查 |

#### 20.7 其他文件修复

| 文件 | 问题 | 严重级别 | 修复 |
|------|------|----------|------|
| `useI18n.ts` | `replace()` 只替换第一个 `{param}` | HIGH | 改为 `split().join()` 替换所有实例 |
| `SettingsPage.vue` | `loadTheme()` 未 await | MEDIUM | `onMounted` 改为 `async` + `await loadTheme()` |
| `SettingsPage.vue` | `revokeObjectURL` 时机过早 | MEDIUM | 改为 `setTimeout(() => URL.revokeObjectURL(url), 1000)` |

#### 20.8 未修复项（LOW / COSMETIC）

| 项目 | 原因 |
|------|------|
| `useAdb.ts` 输入验证 | Rust 后端已有验证，前端验证为防御性措施 |
| 数据库外键约束 | 需要 schema 迁移，风险较高 |
| Workspace 午夜问候语 | 极低优先级，不影响功能 |
| `FieldRulesPage` computed setter 空操作 | 代码风格，无功能影响 |

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |

### Phase 21 — 文件管理器优化 + 大文件安全 + 云端备份收尾 + 导入健壮性（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 文件预览取消支持 | 移除 `<Transition>` 包裹（动画阻止即时关闭），backdrop 直接 `@click="cancelPreview"`，所有按钮 `.stop` 修饰符防止事件冒泡，`previewGen` 计数器丢弃过期 `shell()` 结果 | ✅ |
| 大文件预览确认 | `previewFile`：`rawSize > 10MB` 时弹窗确认，用户点继续后 `showToast(msg, 'loading')` 常显 spinner 提示 UI 将卡住，加载完成后 `hideToast()` 关闭 | ✅ |
| 大文件编辑确认 | `editFile`：`wc -c` 检测 > 5MB 弹窗确认，流程同上 | ✅ |
| 不支持预览的文件类型 | 新增 `isUnsupportedFile()`：apk/exe/dll/so/dylib/bin/dat/db/sqlite/zip/tar/gz/rar/7z/woff/ttf/otf/pyc/class 等，点击直接 toast 提示不支持 | ✅ |
| Toast loading 类型 | 新增 `"loading"` 类型：spinner 旋转图标（`progress_activity` + `animate-spin`）+ 不自动消失，`hideToast()` 手动关闭 | ✅ |
| confirmThen 重构 | 返回 `Promise<boolean>`，action 参数改为可选；取消/遮罩关闭调用 `onCancel()` 正确 resolve `false`；所有现有调用（reboot/remount/delete 等）仍兼容 | ✅ |
| 文件夹直接下载 | `downloadDir` 改用 `open({ directory: true })` 选择本地目录 + 直接 `adb pull`，移除设备端 `tar.gz` 压缩步骤 | ✅ |
| 右键菜单复制路径 | 文件右键菜单新增 Copy Path，`navigator.clipboard.writeText()` 复制完整远程路径 | ✅ |
| 云端备份恢复简化 | 移除 Cloud Manage Modal / Cloud Restore Modal / manage 按钮；云端恢复直接拉取最新备份 | ✅ |
| 设置页状态消息修复 | `statusIsError` ref 替代 `startsWith('Error')` 字符串匹配（适配多语言），`setStatus(msg, isError)` 统一控制红绿色 | ✅ |
| 取消操作清除状态 | `handleImport`/`handleExport`/`handleCloudRestore` 取消文件选择器后清除 statusMessage | ✅ |

#### 21.1 `importAllData` 事务与 PRAGMA 修复

| 问题 | 修复 |
|------|------|
| `PRAGMA synchronous = NORMAL` 在事务内执行报错 | 移除所有事务内 PRAGMA 设置 |
| `PRAGMA wal_checkpoint(TRUNCATE)` 阻塞数据库 | 移除 checkpoint 调用 |
| `BEGIN TRANSACTION` / `COMMIT` 在连接池下不保证原子性 | 移除事务包裹，改为自动提交模式 |
| `INSERT INTO table VALUES (?)` 未指定列名导致自增列报错 | 所有 INSERT 改为 `INSERT INTO table (col1, col2) VALUES (?, ?)` 显式指定列名 |

#### 21.2 导入数据验证与错误处理

| 功能 | 说明 |
|------|------|
| `validateBackup(backup)` | 导入前校验备份结构：检查 `version` 字段、各表字段类型（必须为数组/对象） |
| `failures[]` 错误收集 | 每条 DELETE/INSERT 独立 try-catch，失败项记录到 `failures[]`，最终汇总抛出 |
| JSON 解析保护 | `handleImport`/`handleCloudRestore` 中 `JSON.parse` 有 try-catch，提示"JSON 解析失败/解密失败" |
| 云端备份列表排序 | 客户端 `sort((a,b) => b.created_at.localeCompare(a.created_at))` 确保取最新 |

#### 21.3 主窗口阻塞风险分析

| 操作 | 阻塞风险 | 说明 |
|------|----------|------|
| `loadPreviewContent` (`cat \| base64`) | **已知，用户接受** | 大文件 base64 结果通过 Tauri IPC 传输，期间 UI 线程阻塞；用户已确认弹窗提示后继续 |
| `editFile` (`cat`) | **已知，用户接受** | 同上，非媒体大文件 cat 阻塞 IPC；已加 wc -c 前置检查 + 确认弹窗 |
| `downloadDir` (`pullFile`) | **无风险** | `adb_pull` 在 Rust `spawn_blocking` 线程执行，不阻塞 JS 线程 |
| `downloadFile` (`pullFile`) | **无风险** | 同上 |
| `confirmThen` 弹窗 | **无风险** | Teleport 到 body，DOM 立即更新 |
| `showToast('loading')` | **无风险** | 纯前端响应式更新 |
| `open({ directory: true })` | **无风险** | Tauri 原生对话框，系统级渲染 |
| `isUnsupportedFile` 检查 | **无风险** | 纯正则匹配，< 1ms |
| `importAllData`（自动提交） | **无风险** | 每条语句独立提交，锁持有时间极短 |

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `npx vue-tsc --noEmit` | ✅ 通过 |
| `npx vite build` | ✅ 通过 |

---

### Phase 23 — Api Space MITM 代理（已完成 ✅）

> 新增 Api Space 页面，集成 `http-mitm-proxy` 实现中间人代理，支持 HTTPS 解密、断点调试、重写规则。

#### 23.1 代理核心（`src-tauri/src/proxy.rs`）

| 功能 | 说明 | 状态 |
|------|------|------|
| `http-mitm-proxy` 集成 | 基于 `http-mitm-proxy = "0.18"` + `rustls = { features = ["ring"] }` 实现 HTTPS 中间人代理 | ✅ |
| 自动生成 CA 证书 | 首次启动在 `app_data_dir` 生成 CA 公私钥（`mitm-ca-cert.pem` / `mitm-ca-key.pem`），持久化复用 | ✅ |
| 请求/响应捕获 | 通过 Tauri `emit` 将 `proxy:request` / `proxy:response` 事件发送到前端 | ✅ |
| 断点拦截 | `proxy:breakpoint:request` / `proxy:breakpoint:response` 事件 + `oneshot::channel` 300s 超时等待用户操作 | ✅ |
| 断点操作 | 支持 `forward`、`drop`、`modify`（修改 headers/body/status_code） | ✅ |
| 重写规则引擎 | `url_matches()` 支持 `contains` / `exact` / `prefix` / `regex` 四种匹配方式；按 `modify_request_header/body`、`modify_response_header/body`、`drop` 五种动作实时拦截 | ✅ |
| ADB 一键部署 | `adb root` → `adb remount` → push CA cert → 设置代理（LAN IP:port） | ✅ |

#### 23.2 代理 Bug 修复

| 问题 | 修复 | 状态 |
|------|------|------|
| `proxy.bind()` 返回的 `server_handle` future 被 `drop(server_handle)` 丢弃，accept 循环从未运行，代理端口无响应 | `tokio::select! { _ = server_handle => {}, _ = shutdown_rx => {} }` 轮询 `server_handle` | ✅ |
| `rustls::CryptoProvider` panic — 未设置默认加密提供者 | `CryptoProvider::install_default(rustls::crypto::ring::default_provider())` 在 `MitmProxy::new()` 之前调用 | ✅ |
| ADB reverse 方式被用户否决，改为 LAN IP 广播 | 移除 `adb reverse tcp:...`，改用 `0.0.0.0` 绑定 + LAN IP 设置到设备代理 | ✅ |
| 断点请求修改未应用 headers | `action.get("headers").and_then(\|v\| v.as_object())` 解析后循环 `req_parts.headers.insert(n, val)` | ✅ |
| 断点响应修改未应用 headers | 同上逻辑，改为操作 `res_parts.headers` | ✅ |
| 重写规则 `match_type` 硬编码「contains」 | `url_matches()` 新增 `"regex"`（`regex::Regex::new`）和 `"prefix"`（`starts_with`）支持 | ✅ |
| 重写规则不持久化（重启丢失） | `save_rules_to_file()` / 启动时从 `app_data_dir/rewrite-rules.json` 加载；CRUD 命令均同步写入文件 | ✅ |
| 缺少获取规则列表的命令 | 新增 `proxy_get_rewrite_rules` Tauri 命令 | ✅ |

#### 23.3 Rust 依赖变更（`src-tauri/Cargo.toml`）

```toml
http-mitm-proxy = "0.18"
rustls = { version = "0.23", features = ["ring"] }
regex = "1"
```

#### 23.4 TypeScript 类型变更（`src/types/index.ts`）

| 变更 | 说明 |
|------|------|
| 移除 `redirect` / `replace_status` | 从 `ApiRewriteRule.action_type` 联合类型中删除，Rust 侧未实现且不计划实现 |
| 新增 `exact` match_type | 原已有 `contains` / `regex` / `prefix`，新增 `exact` |

#### 23.5 Composable 变更（`useApiProxy.ts`）

| 变更 | 说明 |
|------|------|
| 新增 `breakpointEvent` ref + `BreakpointEvent` 接口 | 监听 `proxy:breakpoint:request/response` 事件时同时设置 `breakpointEvent.value = { type, data }` |
| 新增 `loadRules()` | 调用 `proxy_get_rewrite_rules` 从后端加载持久化规则，在 `init()` 中自动调用 |
| 导出 `loadRules` | 供组件手动刷新规则列表 |

#### 23.6 页面组件变更（`ApiSpacePage.vue`）

| 变更 | 说明 |
|------|------|
| 移除方法/状态码筛选 | 删除了 `methodFilter`、`statusFilter` ref 及对应两个下拉按钮（Method/Status 筛选器） |
| 新增匹配方式下拉 | 在规则编辑器中新增「匹配方式」select：包含/精确/前缀/正则 |
| 修复 `handleEditRequest` | 统一为 `openBreakpointEditor(req, phase)`，支持 request 和 response 两种断点编辑 |
| 断点编辑器自动打开 | `watch(api.breakpointEvent)` 自动弹出断点编辑框，无需手动点「Edit」按钮 |
| 响应 Tab 编辑按钮 | 响应详情右侧新增 Edit Response 按钮，调用 `openBreakpointEditor(selectedRequest, 'response')` |
| 完整 URL 展示 | 请求标签页顶部显示 `{{ method }} {{ url }}` 完整请求行 |
| 规则持久化 | `saveRule()` / `editRule()` / `deleteRule()` 均通过 `api.addRule/updateRule/removeRule` 自动写入文件 |

#### 23.7 UI 调整

| 调整 | 说明 |
|------|------|
| 左侧面板宽度 | `w-[480px]` → `flex:[0_0_40%] min-w-[360px] max-w-[50%]` 响应式百分比宽度 |
| 调试日志面板 | 移除底部调试日志面板 |
| 重写规则位置 | 从底部面板移到控制栏下拉按钮（设备选择器右侧） |
| 代码块可读性 | `bg-[#1a1c2e]/80` → `bg-white/[0.06]` 亮背景深色文字；新增 Copy 按钮（请求头/响应头/请求体/响应体/Raw Tab） |
| 长文本换行 | `<pre>` 添加 `break-all`，JSON 和长字符串自动换行 |
| 圆角统一 | `rounded-xl` → `rounded-lg`（两个主面板） |
| 右侧面板可选 | 内容区 `select-text`（全局 `select-none` 下按钮不受影响） |

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `cargo check` | ✅ 通过 |
| `npm run build` (vue-tsc + vite) | ✅ 通过 |

---

## 二十四、Phase 24 — 二进制响应显示优化 & 弹窗 UI 改造

### 24.1 接口捕获二进制内容乱码修复

**问题**：MITM 代理捕获图片/音视频等二进制响应/请求体时，Rust 端用 `String::from_utf8_lossy()` 转换，非 UTF-8 字节被替换为 `�` 乱码。

**修复方案**：

| 文件 | 变更 | 说明 |
|------|------|------|
| `src-tauri/src/proxy.rs` | 新增 `body_to_string()` 函数 | 尝试 `String::from_utf8()` 校验，失败则用 base64 编码并标记 `_is_base64: true` |
| `src-tauri/src/proxy.rs` | `CapturedRequest` 结构体 | 新增 `request_body_is_base64: bool` / `response_body_is_base64: bool` |
| `src-tauri/src/proxy.rs` | 请求体/响应体/重放三处转换 | 全部改用 `body_to_string()` 替代 `String::from_utf8_lossy()` |
| `src/types/index.ts` | `ApiCapturedRequest` 接口 | 新增对应 `request_body_is_base64` / `response_body_is_base64` 字段 |
| `src/views/api-space/ApiSpacePage.vue` | 请求/响应 Tab | 检测 `_is_base64` 标志：图片→`<img>` base64 预览，视频→`<video>`，音频→`<audio>`，其他→`[Binary data — size — type]` 占位 |
| `src/views/api-space/ApiSpacePage.vue` | 断点编辑器 | 二进制 body 显示 `[Binary body — cannot edit in text mode]` 禁用编辑 |
| `src/views/api-space/ApiSpacePage.vue` | Raw Tab | 二进制 body 显示 `[Binary request/response body]` 占位，不输出原始 base64 字符串 |

### 24.2 Rust 死代码警告修复

| 警告 | 处理 | 文件 |
|------|------|------|
| `install_apk` 从未使用 | 删除该函数（`adb_install` 在 `lib.rs` 中直接使用 `tokio::process::Command`） | `src-tauri/src/adb.rs` |
| `proxy_get_rewrite_rules` 从未使用 | 注册到 `generate_handler!` 宏中（前端通过 `invoke` 调用但未注册，try-catch 静默失败） | `src-tauri/src/lib.rs` |

### 24.3 添加规则弹窗 UI 改造

**目标**：仿设备页「管理快捷指令」弹窗样式，提高白底清晰度。

| 变更 | 说明 |
|------|------|
| `<Transition name="fade">` | 添加淡入淡出动画 |
| 背景蒙层 | 独立 `div`，`bg-black/10 backdrop-blur-sm`，点击外部关闭 |
| 面板 | `glass-panel rounded-[2rem] ... bg-white/90 max-h-[80vh] flex flex-col`，90% 不透明白色 |
| 标题栏 | 带图标 + 关闭按钮，与表单区域分割 |
| 表单输入 | 统一使用 `bg-white/80 border border-outline-variant rounded-lg` 替换原 `glass-input` |
| 底部按钮 | 添加 `border-t border-outline-variant/30` 分割线 |

### 24.4 停止代理结果弹窗 UI 改造

**目标**：与添加规则弹窗统一风格。

| 变更 | 说明 |
|------|------|
| 结构与样式 | 完全对齐添加规则弹窗：`Transition` + 独立蒙层 + `bg-white/90` 白底面板 + 标题栏 icon + 关闭按钮 + 底部按钮分割线 |

### Phase 25 — 日志采集断开自动保存 & IP 设备功能兼容（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 日志采集设备断开自动保存 | 设备断开时 Logcat/Diagnostic 不再仅丢弃数据，改为调用 `stopLogcatCapture()` / `stopDiagnosticCapture()` 弹出文件保存对话框；新增 `logcatSerial` / `diagSerial` 变量记录启动时的序列号，确保断开后仍能通过 ADB 尝试 dump | ✅ |
| 实时日志按钮停止态 | `scheduleLogcatTimer` 中检测到 `selectedDevice` 为空时调用 `stopLogcatCapture()` 而非仅设 false + toast | ✅ |
| 诊断包按钮停止态 | `scheduleDiagTimer` 同理调用 `stopDiagnosticCapture()` | ✅ |
| 日志采集互斥锁 | Logcat / Diagnostic / BootLogcat 三个按钮相互禁用：任一个运行时，另两个的"开始"按钮禁用（"停止"按钮仍可用），避免共享 logcat 环形缓冲区的竞态数据丢失 | ✅ |
| 开机日志 IP 设备支持 | `scheduleBootPoll` 在 `wait_reconnect` 阶段检测 serial 包含 `:`（TCP 连接特征）且已断开超过 3 秒时，自动调用 `connectDevice(serial)` 重连 ADB TCP 连接 | ✅ |
| 屏幕镜像独立窗口 IP 兼容 | `mirrorPopout` 中 WebviewWindow label 使用 `serial.replace(/[^a-zA-Z0-9_-]/g, '_')` 过滤 IP 地址中的 `.` 和 `:`，避免 Tauri 窗口标签非法导致创建失败 | ✅ |
| i18n 新增 key | `device.logSaved` 中/英双语文案 | ✅ |
| 翻译文件 | `src/composables/useI18n.ts` — 新增 `"device.logSaved": "日志已保存" / "Log saved"` | ✅ |

**影响文件**：
| 文件 | 修改类型 | 说明 |
|------|----------|------|
| `src/views/device-space/DeviceSpacePage.vue` | 逻辑修改 | 日志断开保存、TCP 重连、窗口 label 过滤、按钮互斥锁 |
| `src/composables/useI18n.ts` | 新增翻译 | `device.logSaved` 中/英 |

---

## 二十六、Phase 26 — 笔记编辑器增强 & 导航栏云端快捷同步（已完成 ✅）

> 修复笔记复制到外部（SQL/脚本）格式损坏问题；新增 Word 式字体颜色；导航栏一键云端备份。

### 26.1 笔记复制纯文本修复（`NotesSpacePage.vue`）

| 问题 | 原因 | 修复 |
|------|------|------|
| 多行复制后每行下方多空行 | ProseMirror 默认段落间 `\n\n` 序列化 | `clipboardTextSerializer` 使用 `textBetween(..., "\n", "\n")` |
| SQL 粘贴到外部数据库报 `SyntaxError` | 富文本/HTML 粘贴带入 NBSP（`\u00A0`）或零宽字符 | 复制时替换 `\u00A0/\u202F/\u2007` 为普通空格，移除 `\u200B-\u200D/\uFEFF` |

### 26.2 字体颜色（`NotesSpacePage.vue`）

| 项 | 说明 |
|----|------|
| 依赖 | `@tiptap/extension-color` + `@tiptap/extension-text-style` |
| 交互 | 左侧「A」一键应用 `currentTextColor`；右侧下拉打开 8 色预设面板 |
| 预设色 | 黑/红/橙/黄/绿/青/蓝/紫（见 4.8 节色值表） |
| UI | `color-split-btn` 分体按钮；色条 `.color-split-bar` 随下拉选中色更新 |
| 面板 | Teleport 到 `body`，避免工具栏下方编辑区 `overflow` 裁剪导致无法点击 |

### 26.3 导航栏云端快捷同步

| 模块 | 说明 |
|------|------|
| `src/services/cloudSync.ts` | 新增 `syncBackupToCloud()`，复用设置页云端上传链路 |
| `src/layouts/Sidebar.vue` | Settings 右侧 `sync` 按钮 + 顶部 Toast 反馈 |
| `src/layouts/TitleBar.vue` | 同上（mirror 独立窗口） |
| `src/composables/useI18n.ts` | 新增 `cloudSync.ready/syncing/success/fail` |

**Toast 规范**：`fixed top-4 left-1/2 -translate-x-1/2 z-[99999]`；loading 显示旋转 `sync` 图标；成功 `check_circle`（绿色）；失败 `error`（红色）；3 秒自动消失。

### 26.4 影响文件一览

| 文件 | 修改类型 |
|------|----------|
| `package.json` | 新增 `@tiptap/extension-text-style` |
| `src/views/note-space/NotesSpacePage.vue` | 复制修复 + 字体颜色工具栏 |
| `src/services/cloudSync.ts` | 新增 |
| `src/layouts/Sidebar.vue` | 同步按钮 + Toast |
| `src/layouts/TitleBar.vue` | 同步按钮 + Toast |
| `src/composables/useI18n.ts` | `cloudSync.*` 文案 |

**编译验证**：

| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |

---

## 二十七、Phase 27 — 笔记互链 & AI 问答助手（已完成 ✅）

> 笔记间双向链接（含 `[[标题]]` 语法）；Settings 页 AI API 配置；笔记页浮动 AI 助手面板。

### 27.1 笔记互链（`NotesSpacePage.vue` + `wikiNoteLink.ts`）

| 功能 | 说明 |
|------|------|
| 笔记链接协议 | `note:{noteId}`，TipTap `NoteLinkExtension` 允许 `note:` 与 `https://` |
| Wiki 语法 | 输入 `[[笔记标题]]` 自动转为笔记链接（`WikiNoteLink` InputRule） |
| 插入方式 | 工具栏「笔记链接」按钮 → 弹窗选择目标笔记；或 Wiki 语法 |
| 点击跳转 | `editorProps.handleClick` 拦截 `note:` 链接，调用 `selectNote` |
| 双向链接同步 | 保存时 `syncNoteLinksFromContent` 解析 HTML 更新 `note_links` 表 |
| 链接面板 | 右侧浮动按钮打开滑出面板，显示链出 / 反链列表 |

### 27.2 AI 问答（`noteAi.ts` + `NoteAiPanel.vue`）

| 功能 | 说明 |
|------|------|
| 入口 | 右下角浮动 `smart_toy` 按钮，点击展开 400×480 聊天面板（不影响三栏布局） |
| 检索范围 | 当前笔记 / 智能检索（关键词相关 Top 6）/ 全部笔记 |
| Token 优化 | HTML→纯文本；图片替换为 `[图片]`；每笔记最多 2500 字；预估 token 显示 |
| 引用 | 回答附带可点击的参考笔记列表，点击跳转打开 |
| HTTP | Tauri `@tauri-apps/plugin-http` 绕过 CORS |

### 27.3 AI 配置（`SettingsPage.vue` + `aiSettings.ts`）

| 服务商 | 默认 Endpoint | 认证 |
|--------|---------------|------|
| Azure OpenAI | `…/openai/v1/chat/completions` | api-key |
| DeepSeek | `api.deepseek.com/chat/completions` | Bearer |
| 小米 MiMo | `api.xiaomimimo.com/v1/chat/completions` | api-key |
| OpenAI | `api.openai.com/v1/chat/completions` | Bearer |
| 自定义 | 用户填写 | 可选 |

配置持久化：`app_settings` 键 `ai_config`（JSON）。含测试连接按钮。

**Azure 调用规范**（对齐 `test_openai_key.py`）：
- Header：`api-key: $KEY`（非 Bearer）
- Body：`model` + `messages` + `temperature: 1`，**不传** `max_tokens`
- Tauri HTTP 白名单：`src-tauri/capabilities/default.json` 须包含 `https://*.openai.azure.com/**` 及 DeepSeek/MiMo/OpenAI 域名

**AI 上下文策略**：笔记 HTML 按标题/段落**语义切片**（`chunkNoteContent`），按问题关键词对相关片段打分排序，在 token 预算内择优纳入（最多 24 片段）；图片替换为 `[图片]`。回答内引用格式 `[标题](note:ID)` 渲染为可点击链接，不再重复展示底部参考列表。

**AI 面板 UI**：遵循 4.4 弹窗规范 — `bg-black/10 backdrop-blur-sm` 遮罩 + `glass-panel rounded-[2rem] bg-white/60` 主体；消息气泡 `rounded-md`。

### 27.4 影响文件

| 文件 | 修改类型 |
|------|----------|
| `src/extensions/wikiNoteLink.ts` | 新增 |
| `src/services/aiSettings.ts` | 新增 |
| `src/services/noteAi.ts` | 新增 |
| `src/components/notes/NoteAiPanel.vue` | 新增 |
| `src/views/note-space/NotesSpacePage.vue` | 笔记互链 + AI 面板 |
| `src/views/settings/SettingsPage.vue` | AI 配置区 |
| `src/composables/useI18n.ts` | `notes.*` / `settings.ai*` 文案 |

**编译验证**：`npm run build` ✅ 通过

---

## 二十八、Phase 28 — 笔记 AI 检索完整性、浮窗与配置持久化修复

> 修复笔记页 AI 检索漏内容、AI 助手浮窗遮挡页面、插入笔记链接显示原始 `<a>` 标签，以及 Settings 页 AI 配置切换丢失的问题。

### 28.1 AI 检索上下文修复

| 问题 | 修复 |
|------|------|
| AI 问答固定最多选取 24 个片段，笔记内容较多时会漏掉后续信息 | 移除固定片段数量上限，改为在 `maxContextTokens` 预算内持续纳入所有候选片段 |
| 查询分词对中英文标点不稳定 | 新增 Unicode 字母/数字分词逻辑，降低中文、英文、符号混合查询的漏召回 |
| 笔记页搜索直接匹配 HTML 内容，富文本标签会影响命中 | 搜索时用 `htmlToPlainText()` 剥离 HTML 后再做本地全文匹配，并与数据库搜索结果合并 |
| SQL `LIKE` 转义未真正生效 | `escapeLike()` 正确转义 `\`、`%`、`_` |

### 28.2 AI 助手浮窗修复

| 问题 | 修复 |
|------|------|
| AI 助手展开后使用全屏遮罩，遮住并拦截后方笔记页面 | 改为右下角固定悬浮面板，外层 `pointer-events-none`，只有面板本体可交互，不再加蒙版 |

### 28.3 笔记链接插入修复

| 问题 | 修复 |
|------|------|
| 插入笔记链接时编辑器显示原始 `<a href="note:...">...</a>` 文本 | 改为 TipTap 结构化 text node + link mark 插入，不再直接插入 HTML 字符串 |
| 普通 URL 链接同样依赖 HTML 字符串插入 | 同步改为结构化 link mark 插入 |

### 28.4 AI 配置持久化与云同步

| 项 | 说明 |
|----|------|
| 数据库存储 | AI 配置继续保存到 `app_settings.ai_config`，因此会随 `exportAllData()` 进入云端同步 |
| 多服务商配置 | `ai_config` 从单份配置升级为 `{ activeProvider, configs }`，每个 provider 独立保存 endpoint/model/authMode/maxContextTokens/apiKey |
| 兼容旧数据 | 旧版单份 `AiConfig` 会自动按其 provider 迁移为新结构 |
| 切换行为 | Settings 页切换 provider 前保存当前 provider 表单，切换后恢复目标 provider 上次填写的内容 |

### 28.5 AI 助手交互与检索审查补充

| 项 | 说明 |
|----|------|
| Settings 文案 | `settings.aiConfig` 从「AI 问答配置」调整为「AI配置」 |
| 内部笔记跳转 | `note:` 链接清除 `target/rel` 外链属性，并在编辑器容器捕获点击事件，统一调用 `openNoteById()` 内部跳转 |
| AI 浮窗关闭 | 保持无蒙版浮窗，新增 document 级 `pointerdown` 监听；点击面板外空白处自动关闭 |
| 检索排序 | 修正标题加权：只有标题命中查询时才加分，避免无关笔记片段被错误排到前面 |
| 成熟 RAG 参考 | 当前实现采用 HTML 语义切片 + 关键词/全文召回 + 片段排序 + 内联引用；后续可升级为向量召回、BM25/向量混合检索、reranker 重排、上下文压缩与引用校验 |

**影响文件**：
| 文件 | 修改 |
|------|------|
| `src/services/noteAi.ts` | AI 检索片段选择与分词 |
| `src/components/notes/NoteAiPanel.vue` | AI 助手浮窗去遮罩 |
| `src/views/note-space/NotesSpacePage.vue` | 搜索补全与链接插入 |
| `src/services/aiSettings.ts` | 多 provider AI 配置持久化 |
| `src/views/settings/SettingsPage.vue` | 切换 provider 保留配置 |
| `src/services/database.ts` | `LIKE` 转义修复 |
| `src/extensions/wikiNoteLink.ts` | `note:` 链接移除外链属性 |
| `src/composables/useI18n.ts` | Settings AI 配置标题文案 |

### 28.6 后续待办：AI 助手检索增强

> 本阶段只记录，不实现；后续按风险和依赖情况拆分实施。

| 待办 | 目标 |
|------|------|
| 向量检索 + BM25 混合召回 | 在关键词精确匹配之外补充语义召回，兼顾中文术语、命令片段、标题和正文内容 |
| reranker 重排 | 对初步召回的候选片段做二次排序，提高真正相关片段进入上下文的概率 |
| 上下文压缩 | 对长笔记和多片段结果做摘要/去重/合并，减少 token 浪费并降低遗漏 |
| 引用来源校验 | 回答生成后校验 `note:` 引用是否来自已纳入上下文的片段，避免无来源引用或错误跳转 |

### 28.7 笔记内部链接补充修复

| 问题 | 修复 |
|------|------|
| `note:` 链接在 TipTap Link 安全校验中未作为协议注册，切换笔记后可能丢失 href/样式，点击无反应 | `NoteLinkExtension` 注册 `protocols: ['note']` 并自定义 `isAllowedUri`，确保 `note:` 与 `#unresolved:` 能被解析和渲染 |
| 历史笔记链接可能没有 `note-link` class | CSS 兜底匹配 `a[href^="note:"]` 与 `a[href^="#unresolved:"]` |

---

## 二十九、Phase 29 — AI 长期记忆系统（已完成 ✅）

> 为 AI 助手添加长期记忆能力：自动从问答对话中提取关键知识点，持久化到 SQLite，下次提问时注入 context 供 AI 参考。

### 29.1 架构概览

```
用户提问 → 载入记忆 → BM25 搜笔记 → 注入记忆 + 笔记 → AI 回答 → 提炼新记忆 → 存入 SQLite
                              ↑                                   ↑
                        scoreMemories()                    extractMemories()
                         本地关键词排序                       轻量 AI 调用
```

### 29.2 数据层（`src/services/database.ts`）

| 变更 | 说明 |
|------|------|
| `note_ai_memories` 表 | `id TEXT PK`, `content TEXT NOT NULL`, `created_at TEXT`, `updated_at TEXT` |
| `saveAiMemory(content)` | 插入一条记忆，返回 `AiMemory` 对象 |
| `loadAiMemories()` | 查询全部记忆（按 `created_at DESC`） |
| `deleteAiMemory(id)` | 删除单条记忆 |
| `clearAiMemories()` | 清空全部记忆 |
| `AiMemory` 接口 | `{ id, content, createdAt, updatedAt }` 导出类型 |
| `AppBackup.aiMemories` | 纳入备份/恢复（版本升至 `1.6`） |

### 29.3 检索与提取（`src/services/noteAi.ts`）

| 函数 | 说明 |
|------|------|
| `scoreMemories(query, memories)` | 本地关键词重叠排序：对每条记忆统计查询词命中数 + 精确短语命中加分 → 返回 Top ≤10 条 |
| `chatWithNotes(..., memories)` | 新增可选 `memories` 参数。注入到 system prompt 的「已知长期记忆」区块 |
| `extractMemories(config, question, answer)` | 轻量 AI 调用（`temperature=0.1, max_tokens=300`），从问答对提取事实陈述，去重后返回字符串数组 |

**系统 prompt 修改**：
```
你是 Test Space 笔记助手。根据下方「参考笔记片段」和已知长期记忆回答用户问题。
...
已知长期记忆：
- MAC烧写命令: echo mac > name
- 用户偏好使用 AMIBA 方案烧写
```

### 29.4 UI 接入（`src/components/notes/NoteAiPanel.vue`）

| 变更 | 说明 |
|------|------|
| `memories` ref | `onMounted` 时从 DB 加载全部记忆 |
| `send()` | 传递 `memories` 给 `chatWithNotes()`；回答后调用 `extractMemories()`（fire & forget），去重后 `saveAiMemory()` |

提取不阻塞 UI：`extractMemories()` 的 Promise 在 `.then()` 中处理结果，用户可立即进行下一次提问。

### 29.5 记忆管理（`src/views/settings/SettingsPage.vue`）

| 功能 | 说明 |
|------|------|
| 管理入口 | AI 配置下方仅显示记忆数量概览 +「管理记忆」按钮，不展开列表 |
| 弹出模态 | 点击按钮弹出 Teleport 模态弹窗（`bg-white` 不透明背景，`fixed items-start pt-[8vh]` 防止溢出顶部），含标题 + 关闭按钮 + 筛选删除 |
| 选择/删除 | 每条记忆左侧圆圈选中，点击整行也可选中；底部「删除选中 (N)」批量删除；hover 显示单个 `×` 删除 |
| 清空全部 | 底部「清空全部」按钮 |
| 实时刷新 | 模态打开时自动重新加载记忆列表 |

### 29.6 i18n 新增

| Key | zh | en |
|-----|----|----|
| `settings.aiMemory` | AI 长期记忆 | AI Long-term Memory |
| `settings.aiMemoryEmpty` | 暂无长期记忆，使用 AI 助手时会自动提取 | No memories yet. They'll be auto-extracted when using the AI assistant. |
| `settings.aiMemoryClear` | 清空全部 | Clear All |
| `settings.aiMemoryDelete` | 删除 | Delete |
| `settings.aiMemoryDeleted` | 记忆已删除 | Memory deleted |
| `settings.aiMemoryCleared` | 全部记忆已清空 | All memories cleared |
| `settings.aiMemoryManage` | 管理记忆 | Manage Memories |
| `settings.aiMemoryCount` | 共 {count} 条记忆 | {count} memories |
| `settings.aiMemoryDeleteSelected` | 删除选中 ({count}) | Delete Selected ({count}) |

### 29.7 影响文件

| 文件 | 修改类型 |
|------|----------|
| `src/services/database.ts` | 新增表 + CRUD + 备份恢复 |
| `src/services/noteAi.ts` | 新增 `scoreMemories()` / `extractMemories()`；修改 `chatWithNotes()` |
| `src/components/notes/NoteAiPanel.vue` | 记忆加载与提取 |
| `src/views/settings/SettingsPage.vue` | 记忆管理面板 |
| `src/composables/useI18n.ts` | 新增 `settings.aiMemory*` 文案 |

### 29.8 编译验证

| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |

---

## 三十、Phase 30 — AI 面板增强 & 记忆管理 UI 优化 & 设置页 AI 配置重排（已完成 ✅）

> 优化 AI 助手面板交互（宽度加宽、历史记录持久化），修复长期记忆不生效的 bug，重构记忆管理 UI，调整设置页 AI 配置表单布局。

### 30.1 AI 面板宽度 & 历史持久化

| 改动 | 文件 | 说明 |
|------|------|------|
| 宽度调整 | `NoteAiPanel.vue` | 面板宽度从 `w-[400px]` 改为 `w-[500px]` |
| 对话历史持久化 | `NoteAiPanel.vue` + `database.ts` | 每次对话后自动将 `messages[]` 序列化 JSON 存到 `app_settings(key: 'ai_chat_history')`；面板打开时自动恢复；清空记录按钮（`delete_sweep` 图标）手动清除 |
| 历史加载时机 | `NoteAiPanel.vue` | `onMounted` 时加载 + `historyLoaded` 标志防止初始赋值触发重复存储 |
| 防抖存储 | `NoteAiPanel.vue` | 300ms 防抖 `watch(messages, { deep: true })` |

### 30.2 修复 `extractMemories` 长期记忆不生效

| 改动 | 文件 | 说明 |
|------|------|------|
| 改用 `callChatApi` | `noteAi.ts` | `extractMemories()` 原自行拼接请求体（`temperature: 0.1, max_tokens: 300`），未使用 `buildRequestBody()`，与不同 provider 的请求格式不兼容（如 MiMo 要求 `max_completion_tokens`、Azure 部署名在 URL），导致 API 调用静默失败返回空数组。现改为调用 `callChatApi()`，与主对话使用同一套请求构建逻辑。 |

### 30.3 记忆管理 UI 重构

| 改动 | 文件 | 说明 |
|------|------|------|
| 按钮 + 模态 | `SettingsPage.vue` | 设置页不再内联展示所有记忆，改为「管理记忆」按钮 + 数量概览 |
| 弹窗样式 | `SettingsPage.vue` | 跟随 4.4 弹窗规范：`<Teleport to="body">` 脱离 `glass-panel` 包含块；`bg-white` 不透明背景（替代 `bg-white/60`）；`items-start pt-[8vh]` 防止溢出顶部；独立 backdrop `bg-black/10 backdrop-blur-sm` |
| 选择/批量删除 | `SettingsPage.vue` | 每条记忆左侧圆圈复选框（`check_circle` / `radio_button_unchecked`），点击整行切换选中；底部「删除选中 (N)」批量删除；hover 显示单个 `×` 删除 |
| 清空全部 | `SettingsPage.vue` | 保留「清空全部」按钮在模态底部 |
| 实时刷新 | `SettingsPage.vue` | `watch(showMemoryModal)` 打开时自动调用 `loadMemories()` 并清空选中态 |

### 30.4 AI 配置表单重排

| 字段 | 说明 |
|------|------|
| 服务商 + 最大上下文 Token | 同一行 `grid-cols-2` 各占一半 |
| 模型 + 认证方式 | 同一行 `grid-cols-2` 各占一半 |
| API 地址 | 移到模型下方、API Key 上方 |
| 保存按钮 | 移到 header 行，在「测试连接」按钮右侧 |

### 30.5 i18n 新增

| Key | zh | en |
|-----|----|----|
| `notes.aiClearHistory` | 清空记录 | Clear history |
| `notes.aiHistoryCleared` | 对话记录已清空 | Conversation history cleared |
| `settings.aiMemoryManage` | 管理记忆 | Manage Memories |
| `settings.aiMemoryCount` | 共 {count} 条记忆 | {count} memories |
| `settings.aiMemoryDeleteSelected` | 删除选中 ({count}) | Delete Selected ({count}) |

### 30.6 影响文件

| 文件 | 修改类型 |
|------|----------|
| `src/components/notes/NoteAiPanel.vue` | AI 面板宽度、对话历史持久化、extractMemories 去重逻辑 |
| `src/services/noteAi.ts` | `extractMemories()` 改用 `callChatApi()` |
| `src/views/settings/SettingsPage.vue` | AI 配置布局重排、记忆管理模态弹窗 |
| `src/composables/useI18n.ts` | 新增 5 条 i18n 文案 |

### 30.7 编译验证

| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |
## 三十一、Phase 31 — 性能优化与内存管理

> 修复笔记页面骨架屏显示、大文件加载卡顿、数据库FTS5慢查询、弹窗不关闭等问题。

### 31.1 骨架屏优化

| 问题 | 修复 |
|------|------|
| dataLoading 骨架屏与按钮重叠 | 为包裹骨架屏的滚动容器添加 position:relative，骨架屏不再相对于视口定位 |
| contentLoading 使用沙漏图标 | 替换为与文件树一致的 32 行 skeleton-shimmer 骨架线，模拟文档段落布局 |
| 骨架屏不显示 | 将 .skeleton-shimmer / .skeleton-line / @keyframes skeletonPulse CSS 定义添加到 <style scoped> 中（之前只定义在 JS 模板字符串里） |

### 31.2 大文件加载优化

| 问题 | 修复 |
|------|------|
| editor.value.commands.setContent() 同步阻塞 | 调用前使用 setTimeout(0) yield，让浏览器先渲染骨架屏 |
| 渐进式 insertContent 更慢 | 回退到单次 setContent(content || "")，ProseMirror 解析 JSON 的开销远小于拆分的累积开销 |
| 3000MB 内存飙升 | 彻底删除了 div.innerHTML + DOM 切片的 setNoteContentProgressive 路径，改用单次 setContent |

### 31.3 数据库 FTS5 性能修复

| 问题 | 修复 |
|------|------|
| DELETE FROM notes_fts 耗时 1.2 秒 | 移除了 initDb() 中的 
ebuildFtsIndex() 调用。FTS5 索引通过每次 saveNote() / deleteNote() 增量维护，初始重建是多余的 |

### 31.4 ProseMirror 历史内存管理

| 问题 | 修复 |
|------|------|
| 快速切换笔记时 ProseMirror undo 历史积累 | 在 StarterKit 中配置 history: { depth: 20, newGroupDelay: 1000 }，限制 undo 栈深度 |
| 多次 setContent() 创建历史事务 | 每次内容加载完成后分发 scrollIntoView 事务关闭当前历史分组 |

### 31.5 缓存内存控制

| 功能 | 说明 |
|------|------|
| CACHE_MAX_SIZE = 30 | 笔记内容缓存上限 30 条，超出时淘汰最旧条目 |
| cappedCacheSet() | 替代直接 Map.set()，在写入前检查容量 |

### 31.6 弹窗修复

| 问题 | 修复 |
|------|------|
| 删除文件夹后弹窗未关闭 | deleteFolderTarget.value = null 移至 loadNotes() 之前，在数据库删除完成后立即关闭弹窗 |

### 31.7 影响文件

| 文件 | 修改 |
|------|------|
| src/views/note-space/NotesSpacePage.vue | 骨架屏、ProseMirror history 配置、cappedCacheSet、弹窗关闭时序 |
| src/services/database.ts | 移除 initDb() 中的 
ebuildFtsIndex() 调用 |

### 31.8 编译验证

| 检查项 | 结果 |
|--------|------|
| 
pm run build (vue-tsc + vite) | ✓ 通过 |

---

## 三十二、Phase 32 — AI 检索修复 & `saveNote` 空内容保护（已完成 ✅）

> 修复 AI 搜索找不到已导入笔记内容的根本原因（`saveNote` 被空内容覆盖）、BM25 分词不保留多字母 Latin 序列、新增 `plain_text` 自动修复机制。

### 32.1 BM25 分词修复

| 问题 | 修复 |
|------|------|
| CJK-Latin 边界正则 `[a-z\d]` 将 `MAC` 拆为 `M,A,C`，`WiFi` 拆为 `W,i,F,i` | 改为 `[a-z\d]+`，保留多字母 Latin 序列为单一 token，不影响原有 CJK-Latin 插入空格逻辑 |

### 32.2 `saveNote` 空内容保护

| 问题 | 修复 |
|------|------|
| `onDeactivated`/`onBeforeUnmount` 保存路径以 `note.content = lastEditorContent.value` 写入，对于导入后未打开的笔记，`lastEditorContent` 为 `""`，`saveNote` 无条件覆盖已有 `content`/`plain_text` | `ON CONFLICT(id) DO UPDATE SET` 中使用 `CASE WHEN length(trim(excluded.content)) = 0 THEN content ELSE excluded.content END`，空内容时不覆盖已有 `content`、`content_json`、`plain_text`，仅更新元数据（title、folder、tags 等） |

### 32.3 自动修复已损坏笔记

| 问题 | 修复 |
|------|------|
| 已有笔记 `plain_text` 被清空（`content` 存在但 `plain_text` 为 `''`），BM25 搜索不到 | 新增 `repairEmptyPlainText()` 函数：`SELECT` 检出 `content IS NOT NULL AND content != '' AND (plain_text IS NULL OR plain_text = '')` 的笔记，重新 `htmlToPlainText(DOMPurify.sanitize(content))` 写回 `plain_text` 并更新 FTS5 索引。通过 `_plainTextRepaired` 标记保证整个会话周期只执行一次。在 `loadNotes()` 和 `loadNoteList()` 入口处调用 |

### 32.4 记忆提取改为手动触发

| 问题 | 修复 |
|------|------|
| 每次 AI 回答后自动调用 `extractMemories()`，API 开销大且可能重复提取 | AI 面板头部新增手动「从当前对话提取长期记忆」按钮（`memory` 图标），仅在消息 >=2 条时可点击；`send()` 中移除自动提取调用；新增 `extractFromLastQA()` 传入已有记忆做模糊去重 |

### 32.5 影响文件

| 文件 | 修改 |
|------|------|
| `src/services/database.ts` | `saveNote()` 空内容保护（CASE）、新增 `repairEmptyPlainText()`、`loadNoteList()`/`loadNotes()` 调用修复、`_plainTextRepaired` 标记 |
| `src/services/noteAi.ts` | CJK-Latin 正则修复、移除 debug 日志、`extractMemeries()` 新增 `existingMemeries` 参数 |
| `src/components/notes/NoteAiPanel.vue` | 移除自动提取、新增手动提取按钮、记忆状态移至头部信息栏 |
| `src/composables/useI18n.ts` | 新增 `notes.aiExtractMemory` 双语文案 |

### 32.6 编译验证

| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |

---

## Phase 33 — 全面健壮性修复

### 33.1 问题清单与修复内容

| # | 位置 | 问题 | 修复 |
|---|------|------|------|
| 1 | `NoteAiPanel.vue` `send()` | `loading.value = false` 在 `try` 末尾和 `finally` 里各写一次，逻辑冗余 | 删除 `try` 末尾的多余赋值，仅保留 `finally` 里的 |
| 2 | `NotesSpacePage.vue` `loadData()` | 缓存命中（`_cachedNotes` 存在）时直接 `return`，不执行 `loadAiConfig()`，导致设置页修改 AI 配置后切回笔记页不生效 | 在 `onActivated` 钩子中补充 `loadAiConfig().then(c => aiConfig.value = c)` |
| 3 | `NotesSpacePage.vue` `_isUnmounted` | 模块级变量，`onBeforeUnmount` 设为 `true` 后，keep-alive remount 时不重置，导致第二次进入笔记页所有异步操作立即退出、笔记内容无法加载 | `onMounted` 开头添加 `_isUnmounted = false` |
| 4 | `NotesSpacePage.vue` `uncategorizedNotes` | 根笔记本身无 `spaceId` 字段，无法按 Space 精确过滤，加注释说明该约束 | 保持原有逻辑（`!n.folderId`），补充注释说明根笔记无 spaceId 字段的现有限制 |
| 5 | `NoteAiPanel.vue` 聊天历史 | `messages` 无条数限制，全量序列化写入 SQLite，长期使用后备份文件膨胀 | 引入 `MAX_HISTORY_MESSAGES = 50` 常量，持久化时仅保留最近 50 条 |
| 6 | `NoteAiPanel.vue` 记忆提取失败 | `extractFromLastQA` 失败只 `console.warn`，用户无任何反馈 | catch 分支写入 `error.value`，显示在面板错误区 |
| 7 | `NotesSpacePage.vue` PDF 导出 | PDF iframe 样式字符串中骨架屏 CSS 重复写入两遍，且对 PDF 输出无意义 | 删除重复的骨架屏 CSS，仅保留正文排版样式 |
| 8 | `noteAi.ts` | Round 1 选 chunk 时不跳过 score=0 的 `'(空)'` 占位，浪费 token budget | Round 1 改为跳过 `text === '(空)'` 的 chunk，优先取有内容的 chunk |
| 9 | `noteAi.ts` | `tokenizeQuery` 和 `tokenizeSearchQuery` 两个冗余函数，已被 `tokenizeFinalQuery` 覆盖 | 删除两个废弃函数 |
| 10 | `aiSettings.ts` + `SettingsPage.vue` | `maxContextTokens` 硬限 32000，现代大模型（GPT-4o/Claude 等）支持 128k+，用户填大值被静默截断 | 上限改为 200000，`SettingsPage` input `max` 同步更新 |
| 11 | `SettingsPage.vue` + `NotesSpacePage.vue` 弹窗背景色 | 各弹窗背景遮罩在这两个文件中混用 `bg-black/10`、`bg-black/20`，视觉不统一 | 统一为 `bg-black/30 backdrop-blur-sm`（以「删除设备 ID」弹窗为基准），同步更新弹窗规范文档 |

### 33.2 影响文件

| 文件 | 修改 |
|------|------|
| `src/components/notes/NoteAiPanel.vue` | `send()` loading 冗余赋值清理、聊天历史条数限制 MAX 50、记忆提取失败显示错误 |
| `src/views/note-space/NotesSpacePage.vue` | `_isUnmounted` remount 重置、`onActivated` 刷新 aiConfig、PDF 导出骨架屏 CSS 去重、弹窗背景色统一 |
| `src/services/noteAi.ts` | 删除冗余 tokenize 函数、Round 1 跳过空 chunk |
| `src/services/aiSettings.ts` | maxContextTokens 上限从 32000 → 200000 |
| `src/views/settings/SettingsPage.vue` | maxContextTokens input max 同步、弹窗背景色统一 |
| `DEVELOPMENT.md` | 弹窗规范 `bg-black/10` 更新为 `bg-black/30`，Phase 33 记录 |

---

## Phase 34 — 笔记导出反馈 + 脚本空间全面优化

### 34.1 笔记页面导出无反馈修复

**问题**：点击「导出为 PDF / Word / Markdown」及目录区「导入/导出」后没有任何提示，用户不知道是否成功。

**修复**：
- `NotesSpacePage.vue` 新增轻量 Toast 机制（`toast` ref + `showToast()` + 底部弹出模板，与 DeviceSpacePage 风格一致）
- `exportAs(format)` 重写：开始时显示 loading Toast「正在导出，请稍候…」；用户取消文件对话框时静默关闭；成功显示「已保存到 xxx.pdf/docx/md」；失败显示「导出失败：[错误]」
- `doImport()` 重写：成功显示「已导入 N 篇笔记」；部分失败显示「已导入 N 篇，M 篇失败」；整体异常显示具体错误
- `doExport()` 重写：选目录后显示 loading；成功显示「已导出 N 篇笔记」；部分失败显示统计
- `useI18n.ts` 新增 `notes.exportFileSaving`、`notes.exportFileSaved`、`notes.exportFileFail`、`notes.exportPartialFail`、`notes.importPartialFail` 中英双语 key
- `onBeforeUnmount` 中清理 `toastTimer`

### 34.2 脚本空间全面优化

#### 34.2.1 代码编辑器重构（光标对齐修复）

**问题根因**：编辑器采用透明 `<textarea>` 叠加 `<pre>` 高亮层方案，`<pre>` 中的 `<code>` 是 inline 元素，行高计算与 `<textarea>`（块级）不同，累积偏差导致光标错位；`whitespace-pre-wrap` 在长行折行时造成两层行高不一致。

**修复**：
- 去掉 `<code>` 包裹，`v-html` 直接绑定到 `<pre>` 上
- 全部改用固定像素值：`font-size: 13px; line-height: 21px; padding: 12px`（三层统一：行号栏 / `<pre>` / `<textarea>`）
- `white-space: pre`（不折行）替代 `whitespace-pre-wrap`
- `syncScroll` 补充 `scrollLeft` 同步
- `watch(editingContent)` 用 `nextTick + requestAnimationFrame` 补一次同步，修复删除内容时浏览器自动滚动后 `<pre>` 与光标位置偏移
- `padding-bottom: 48px` 确保最后一行始终完整显示

#### 34.2.2 快捷键修复（Tab / Shift+Tab / Ctrl+/）

**问题根因**：
1. `applyEdit` 用 `ta.select()` 全选后 `execCommand('insertText', false, 全文)` 替换，Ctrl+Z 撤销直接清空文件
2. `@keydown.tab.prevent` 和 `@keydown.shift.tab.prevent` 同时监听 Tab 键，Shift+Tab 触发两个处理器互相抵消

**修复**：
- 废弃 `execCommand` 方案，改用 `setRangeText(text, start, end, 'end')`（同步、光标行为可预测）
- 所有快捷键合并到 `onEditorKeydown(e: KeyboardEvent)` 统一处理，用 `e.key` 原生判断，彻底避免 Vue 修饰符组合键冲突
- `insertTab`：无选区插入2空格；有选区扩展到行首逐行加缩进
- `unindentTab`：逐行去掉最多2个前导空格，记录首行 delta 精确调整 selectionStart；无可去缩进时直接 return 不产生无效 undo
- `toggleComment`：只检测非空行，Python 用 `# `，BAT 用 `:: `；全部已注释则取消，否则添加

#### 34.2.3 脚本类型持久化

**问题**：切换 Python / BAT 类型后切换页面回来重置为默认值。

**修复**：`switchType` 和 `confirmTypeSwitch` 写 `localStorage('script-space:type')`，`onMounted` 读取恢复。

#### 34.2.4 模块导入修复（No module named 'exporter'）

**问题根因**：脚本存在数据库中，运行时写入 `AppData/temp_scripts/` 目录，Python 的 `sys.path[0]` 是脚本文件目录，不是工作目录，找不到同数据库中的 `exporter.py`。

**修复**：
- 运行前把**同类型的所有其他脚本**也写入 temp_scripts 目录，文件名用脚本名（如 `exporter.py`）
- 在脚本内容开头自动注入 `import sys as _sys; _sys.path.insert(0, r"<tmpDir>"); del _sys`，确保 `import exporter` 能找到同目录的模块
- 完全透明，用户无需任何额外操作，打包成 exe 后同样工作

| 场景 | 执行路径 | 工作目录 |
|------|----------|----------|
| 数据库脚本 | `temp_scripts/__ts_run_<id>.py` | `temp_scripts/`（含所有同类脚本） |
| 本地打开文件 | 直接写回原始文件路径 | 原始文件所在目录（自动派生） |

#### 34.2.5 脚本重复执行修复

**问题根因**：`useScriptRunner` 的 `setup()` 用 `setupCalled` 防重，但 HMR 热重载时模块重新执行 `setupCalled` 重置为 `false`，多次注册 `script-line` / `script-exit` 监听器，一次运行触发多次输出和多个 `[Exit N]`。

**修复**：
- `setup()` 开头无条件先调用旧的 unlisten，清理残留监听器
- 新增 `setupInProgress` 异步锁防止 `await listen()` 挂起期间的并发调用
- `destroy()` 重置 `setupInProgress`

#### 34.2.6 长时间运行输出限制

**问题**：压测两天等长时运行脚本持续输出大量日志，全部 push 进 `tab.output` 数组会导致内存溢出。

**修复**：`useScriptRunner` 新增 `MAX_OUTPUT_LINES = 5000` 常量，每次 push 后超出则从头部丢弃旧行（circular buffer），内存用量恒定。

### 34.3 影响文件

| 文件 | 修改 |
|------|------|
| `src/views/note-space/NotesSpacePage.vue` | Toast 机制、`exportAs` / `doImport` / `doExport` 全部加反馈 |
| `src/composables/useI18n.ts` | 新增导出/导入反馈相关 i18n key（中英双语） |
| `src/views/script-space/ScriptSpacePage.vue` | 编辑器光标对齐修复、快捷键重写（`onEditorKeydown`）、类型持久化、模块导入修复（同类脚本写入 temp）、`sys.path` 注入 |
| `src/composables/useScriptRunner.ts` | 重复执行修复（`setupInProgress` 锁）、输出行数上限（MAX 5000） |
| `src-tauri/src/script_exec.rs` | `script_spawn` 新增 `work_dir: Option<String>` 参数，`cmd.current_dir()` 支持 |

---

## Phase 35 — AI 助手笔记段落级跳转（已完成 ✅）

> 让 AI 助手回答里的笔记引用能精准跳转到具体段落标题，并在目标标题上以柔和的三次脉冲高亮提示。

### 35.1 引用格式扩展

**目标**：原本 AI 回答只能引用整篇笔记 `[标题](note:uuid)`，点击跳到笔记顶部；扩展后可精确定位到具体段落。

**新增格式**：`[显示文字](note:uuid#标题文字)`

- `#标题文字` 可选，填了就跳到笔记内对应 H1/H2/H3 标题
- 标题文字直接取自 chunk 的第一行（`chunkNoteContent()` 按 H1/H2/H3 切分，每个 chunk 第一行就是段标题）
- 兼容旧格式：不带 `#` 的引用行为不变

**文件**：`src/utils/parseNoteLinks.ts`

- 正则从 `\[(...)\]\(note:([a-f0-9-]{36})\)` 扩展为 `\[(...)\]\(note:([a-f0-9-]{36})(?:#([^)]*))?\)`
- `AnswerSegment` 接口新增可选 `headingAnchor?: string`
- 解析时 group 3 若存在则 trim 后赋给 `headingAnchor`

### 35.2 System Prompt 强化

**文件**：`src/services/noteAi.ts` 内 `chatWithNotes()`

- **长期记忆前移**：`memoriesBlock` 从 prompt 末尾移到开头，作为背景信息；规则列表放在末尾（LLM 对末尾指令遵循度更高，避免"有记忆就短路、忘记引用笔记"的问题）
- **规则调整**：
  1. 优先基于笔记片段，记忆仅作补充，不能替代
  2. 引用格式支持 `#标题` 定位段落
  3. 标题文字必须原样复制 chunk 第一行（保留大小写、空格、中英文），不改写不总结不加 `#`
  4. 不列末尾参考清单，引用内嵌在正文
  5. 即使记忆能直答也要检查笔记是否更详细，有则引用
- **记忆标注**："仅供参考，不可替代笔记引用"

**未改动**：`selectContextChunks()` 的 BM25 检索、`chunkNoteContent()` 切片、上下文预算——AI 检索准确性和覆盖度完全一致。

### 35.3 AI 面板点击笔记链接后自动关闭

**问题**：AI 面板 `fixed right-4 bottom-4 z-[60]`、`bg-white/60` + `backdrop-filter: blur(60px)`，几乎不透明毛玻璃，占屏幕右侧 500px 全高。用户点击笔记引用后，目标笔记内容和高亮闪烁都在面板正后方，肉眼看不见。

**修复**：`NoteAiPanel.vue` 的 `onOpenNote()` 在 `emit('openNote', ...)` 之后设 `open.value = false`。

- 面板关闭后目标笔记完全可见
- 聊天历史、长期记忆全部保留（存在 SQLite `app_settings` / `ai_memories` 表）
- 用户想继续对话时，点右下角浮球重新打开即可

### 35.4 标题查找与滚动

**文件**：`src/views/note-space/NotesSpacePage.vue`

**核心函数 `scrollToHeadingByText(anchor: string)`**：

采用 TipTap 官方 TOC 扩展的成熟模式——通过 ProseMirror state API 定位节点，不用不稳定的 DOM 查询：

```
editor.state.doc.descendants((node, pos) => {
  if (node.type.name !== 'heading') return true
  // 评分匹配：完全相等=100 / 前缀=60 / 包含=30
  const dom = editor.view.nodeDOM(pos)  // TipTap 官方公有 API
  ...
})
```

- **文本规范化 `normalizeAnchorText()`**：`\u00A0` 等特殊空白→普通空格、collapse whitespace、去中英文标点、大小写归一，让"如何烧写MAC"和"如何烧写 mac"能对上
- **评分匹配**：完全相等直接取；否则收集所有 fuzzy 匹配，按 score 降序取最优；避免 AI 输出的锚点文字略有偏差时匹配到错误标题

**同笔记内跳转 vs 跨笔记跳转**：

- `openNoteById(noteId, anchor?)` 判断 `selectedNoteId.value === noteId`
  - 相同笔记：直接调 `scrollToHeadingByText()`
  - 不同笔记：设 `_pendingHeadingAnchor` 模块级变量，调 `selectNote()` 加载笔记
- `selectNote()` 末尾（`contentLoading = false` + `nextTick` 之后）消费 `_pendingHeadingAnchor`——保证大文件加载完成后才滚动

### 35.5 高亮闪烁 —— Overlay 方案

**踩坑记录**：先后尝试过三种方案都失败——

1. `@keyframes heading-flash` + `.heading-flash` CSS 类：CSS 已进构建产物，但 `<style scoped>` 里 `:deep(.prose-editor h1)`（specificity `0,2,1`）加上 `glass-panel` 的 `backdrop-filter` 图层压制了 h1 的背景色渲染
2. JS 直接在 h1 上设 inline style：inline style specificity 最高，但视觉上仍被吞（PM MutationObserver、scoped 样式、backdrop-filter 多层叠加）
3. 加 outline 也不显示：同上，还是被压

**最终方案 `flashHeadingInline(el)`**：**不动 h1 本身**，在 `document.body` 里 `createElement('div')` 一个 fixed overlay：

- `position: fixed` + 精确视口坐标（`getBoundingClientRect()` + 4~6px padding 让光环包裹标题）
- `z-index: 1000` 压过一切；`pointer-events: none` 不影响交互
- **完全脱离 ProseMirror 树、脱离所有 scoped 样式作用域、脱离所有 backdrop-filter 图层**
- 三次脉冲用 setTimeout 编排：`on(0) → off(320) → on(520) → off(840) → on(1040) → off(1360) → remove(1620)`
- 颜色柔和：淡紫 `rgba(196, 181, 253, 0.28)` 背景 + `0 0 16px 4px rgba(196, 181, 253, 0.35)` 光晕；无实心边框，符合应用玻璃态设计

### 35.6 滚动同步 `waitForScrollSettle()`

**位置歪的根因**：固定 450ms 延迟等 smooth scroll 完成不可靠——短距离滚动 300ms 就到位，长距离 800ms+，450ms 一刀切时，`getBoundingClientRect()` 抓到的是中途位置，overlay 就固定在了错误的坐标。

**修复**：新增 `waitForScrollSettle(done)`：

- 每 60ms 采样一次 `editorScrollRef.scrollTop`
- 若与上次相同（不再变化），认为滚动稳定，触发回调
- 1200ms 兜底超时防意外卡死

`scrollToHeadingByText` 里改成：`el.scrollIntoView(...)` 后 `waitForScrollSettle(() => flashHeadingInline(el))`。滚动一停就立刻捕获准确坐标画 overlay，位置 100% 对齐。

### 35.7 影响文件

| 文件 | 修改 |
|------|------|
| `src/utils/parseNoteLinks.ts` | 正则支持 `#anchor`、`AnswerSegment.headingAnchor` |
| `src/services/noteAi.ts` | System prompt 重排（记忆前移、引用格式扩展、标题选取规则） |
| `src/components/notes/NoteAiPanel.vue` | emit 签名加 `headingAnchor?`、`onOpenNote` 透传 anchor 并关闭面板 |
| `src/views/note-space/NotesSpacePage.vue` | `_pendingHeadingAnchor`、`openNoteById(id, anchor?)`、`normalizeAnchorText`、`scrollToHeadingByText`、`waitForScrollSettle`、`flashHeadingInline` overlay 方案 |

### 35.8 关键教训

- **绕开容器**：需要在管理型 DOM 树（ProseMirror / contenteditable）内做视觉高亮时，不要直接改被管理元素的样式；用 body 级 fixed overlay 一劳永逸
- **滚动时机**：`scrollIntoView({ behavior: 'smooth' })` 的实际完成时间不可预测，需要用 `scrollend` 事件或轮询 `scrollTop` 检测稳定状态；固定 setTimeout 延迟必然翻车
- **LLM prompt 位置权重**：模型对 prompt 末尾指令遵循度最高——重要规则放末尾，背景信息放开头
- **CSS specificity 陷阱**：`<style scoped>` 里 `:deep()` 选择器有相当高的 specificity，动态添加的普通类可能显示不出效果；这时 inline style 也未必救得回来（多层图层混合），overlay 才是终极方案


---

## Phase 36 — AI 助手全局化 + 脚本页面 AI 写脚本（已完成 ✅）

> 将 `NoteAiPanel` 从笔记页提升为应用级全局组件；触发按钮只在笔记页和脚本页显示；进入不同页面自动切换 AI 模式（无感知）；脚本页 AI 助手支持自动选择 BAT/Python、新建并保存脚本。

### 36.1 架构改动

| 变更 | 说明 |
|------|------|
| `NoteAiPanel` 移入 `AppLayout.vue` | 从 `NotesSpacePage` 移除，改由 `AppLayout` 全局宿主管理，生命周期与应用同步，切页不销毁 |
| 触发按钮可见性 | `showTrigger` computed：只在 `mode === 'notes'` 或 `mode === 'script'` 时显示，其他页面（设备、API、用例、设置）不显示 |
| 模式自动切换 | `AppLayout` 根据 `route.path` 计算 `aiMode`（`'notes'` / `'script'`），切页时自动更新，用户无感知；面板 watch `mode` 变化时自动关闭，避免在错误页面停留 |
| `defineExpose` | `NotesSpacePage` expose `{ notes, openNoteById }`；`ScriptSpacePage` expose `{ globalType, editingContent, siblingScriptNames, applyAiScript }` |
| `pageRef` 通信 | `AppLayout` 通过 `:ref="onPageRef"` 获取当前路由页面实例，读取 expose 的数据传给 `NoteAiPanel` |

### 36.2 新增文件

| 文件 | 说明 |
|------|------|
| `src/services/scriptAi.ts` | 脚本 AI 服务层：`callScriptAi()` 构建脚本写作 system prompt，解析 AI 返回的 JSON `{ scriptType, name, code, description }`，处理模型未返回标准 JSON 时的降级 |

### 36.3 NoteAiPanel 多模式改造

**新增 props**：
```ts
mode: 'notes' | 'script'
scriptType?: 'bat' | 'py'
currentScriptContent?: string   // 编辑器当前内容（用于修改现有脚本）
scriptNames?: string[]           // 同类型其他脚本名称（供 AI import 感知）
```

**新增 emit**：`applyScript: [payload: ScriptAiResult]`

**send() 分支**：
- `mode === 'notes'`：走原有 `chatWithNotes()` RAG 链路，逻辑不变
- `mode === 'script'`：调用 `callScriptAi()`，回复卡片带「新建并保存此脚本」按钮

### 36.4 脚本 AI 流程

1. 用户在脚本页打开 AI 面板，用自然语言描述需求
2. `callScriptAi()` 将当前编辑器内容、当前类型、同库脚本名一并发给模型
3. AI 返回 JSON：`scriptType`（自动决策 bat/py）、`name`（脚本名）、`code`（完整代码）、`description`（一句话说明）
4. 面板展示代码预览 +「新建并保存此脚本」按钮
5. 点击按钮触发 `emit('applyScript', payload)` → `AppLayout.onAiApplyScript()` → `ScriptSpacePage.applyAiScript()`
6. `applyAiScript()` 执行：切换类型 → 去重生成名称 → 加载到编辑器 → 自动保存到 SQLite → Toast 反馈

**已有脚本修改**：如果编辑器有内容，AI 会拿到 `currentScriptContent` 作为上下文，可以直接让 AI 修改/优化现有代码。

**Python 模块互调**：`scriptNames` 包含同类型所有脚本名，AI system prompt 明确告知「可以用 `import <name>` 调用同库脚本，runner 会自动注入 sys.path」。

### 36.5 修改文件汇总

| 文件 | 修改类型 |
|------|----------|
| `src/components/notes/NoteAiPanel.vue` | 重构：多模式支持、triggerTitle/panelTitle、脚本模式 UI、showTrigger 控制 |
| `src/services/scriptAi.ts` | 新增：脚本 AI 服务层 |
| `src/layouts/AppLayout.vue` | 重构：全局 AI 面板宿主、pageRef 通信、路由感知模式切换 |
| `src/views/note-space/NotesSpacePage.vue` | 移除本地 `<NoteAiPanel>`、新增 `defineExpose` |
| `src/views/script-space/ScriptSpacePage.vue` | 新增 `applyAiScript()`、`siblingScriptNames`、`defineExpose` |
| `src/composables/useI18n.ts` | 新增 `scripts.aiAssistant/aiPlaceholder/aiInputPlaceholder/aiModeHint/aiApplyScript` 双语文案 |

---

## Phase 37 — AI 助手稳定性修复 & 脚本 AI 全面优化（已完成 ✅）

> Phase 36 发布后针对 AI 助手和脚本页面发现的所有问题的修复与优化，包含 API 兼容性、模式自动切换、脚本编辑行为、BAT 编码、提示词工程等多个维度。

### 37.1 API 兼容性修复（`noteAi.ts` / `scriptAi.ts`）

| 问题 | 根本原因 | 修复 |
|------|----------|------|
| `temperature does not support 0.2` | Azure 新版及 o-series 模型拒绝非默认 temperature 值 | 完全不发 `temperature` 字段，让部署使用默认值 |
| `max_tokens is not supported` | 新版 Azure/OpenAI 模型已废弃 `max_tokens` | 全部改用 `max_completion_tokens` |
| `finish_reason: length` / 空回复 | 之前硬编码 `max_completion_tokens: 2048` 且计算逻辑错误（误用 `maxContextTokens/4`），导致 prompt 占满窗口后输出空间为零 | 完全不发此字段，让模型使用部署默认值（通常 4096+）；`maxContextTokens` 字段只用于 RAG chunk 预算控制，与输出 token 上限无关 |
| 笔记助手空气泡（无报错） | `chatWithNotes` 拿到空 answer 时静默返回，未抛出错误 | 添加空回复检测，抛出含 `finish_reason` 的可见错误 |
| AI returned an empty response | Azure o-series 模型收到 `system` role 直接返回空内容 | 新增 `resolveSystemRole(config)`：按模型名称（`o1`/`o3`/`o4-mini` 等精确匹配）判断是否用 `developer` role；`gpt-5` 等不确定名称不再匹配，避免误判 |

**`resolveSystemRole` 设计原则**：
- 基于 model 名称而非 provider 字段，`custom` endpoint 也能正确识别
- 只匹配明确的 o-series 名称（`/^o[1-9](-mini|-preview|-pro)?$|^o4-mini/`），宁可漏判也不误判
- `resolveSystemRole` 作为 export 统一在 `noteAi.ts` 定义，`scriptAi.ts` 导入复用，消除重复实现

### 37.2 AI 触发按钮可见性修复（`NoteAiPanel.vue` / `AppLayout.vue`）

**问题**：触发按钮在设备页、API 页、用例页、设置页等非 AI 页面也显示。

**根本原因**：`showTrigger` computed 依赖 `mode` prop，而 `mode` 在非笔记/脚本页 fallback 为 `'notes'`，条件始终满足。

**修复**：
- `NoteAiPanel` 新增 `visible: boolean` prop
- `showTrigger` 改为直接返回 `props.visible`
- `AppLayout` 计算 `aiPanelVisible`：只有 `/notes-space` 和 `/script-space` 路由返回 `true`

### 37.3 脚本切换后控制台残留输出（`ScriptSpacePage.vue`）

**问题**：运行脚本 A 后切换到脚本 B，控制台仍显示 A 的输出。

**根本原因**：`activeTabId` 是 `useScriptRunner` 模块级全局 ref，切换脚本时只更新编辑器内容，未重置 `activeTabId`。

**修复**：`loadScript()`、`newScript()`、`openLocalFile()` 三处均加入 `activeTabId.value = ""`，切换后控制台显示空的等待提示。

### 37.4 AI 助手重复创建文件问题（`ScriptSpacePage.vue`）

**问题**：用 AI 助手生成脚本后补充信息继续修改，每次都创建新文件而非更新原文件。

**根本原因**：`applyAiScript` 始终调用 `genId()` 生成新 ID。

**修复**：
- 判断 `currentScript.value` 是否存在
- **有脚本（更新模式）**：复用原 `id` 和 `name`，`db.saveScript` 做 upsert 覆盖
- **无脚本（新建模式）**：生成新 `id`，去重命名

### 37.5 脚本 AI 模式锁定（`scriptAi.ts`）

**问题**：AI 助手有时将 BAT 请求改写成 PowerShell 或其他格式。

**根本原因**：system prompt 第1条规则「由 AI 自行决定脚本类型」+ 示例中硬编码 `SCRIPT_TYPE: bat`，模型可能会自主切换类型。

**修复**：
- 删除「AI 自行决定类型」的规则
- System prompt 改为强制声明：`You MUST generate a ${scriptTypeName} script. Do NOT use PowerShell, Python, or any other language.`
- `SCRIPT_TYPE:` 和 `\`\`\`` 中的语言标记均用变量注入，消除歧义

### 37.6 脚本 AI 自动应用（`NoteAiPanel.vue`）

**修改**：AI 生成脚本后不再显示「新建并保存此脚本」手动按钮，改为 `sendScript()` 拿到结果后立即 `emit('applyScript', result)` 自动保存。消息气泡只显示 AI 的一句话描述 + 绿色「已自动新建并保存：{name}」状态提示。

### 37.7 BAT 脚本中文编码问题（`scriptAi.ts`）

**问题**：AI 生成的 BAT 脚本在控制台运行时，`echo`/`rem`/`::` 行中的中文全角标点和 `->` 箭头变成乱码 `◆◆` 并被当作命令执行。

**根本原因**：脚本以 UTF-8 保存，Windows cmd.exe 默认 GBK（CP936）执行，中文 UTF-8 多字节序列被错误解析为命令分隔符。

**修复（双保险）**：

1. **System prompt 规则**：要求 BAT 脚本开头固定写 `@echo off` + `chcp 65001 >nul`；禁止在 echo/rem/注释行使用全角标点和 `->` / `=>` 箭头

2. **`sanitizeBatEchoLines()` 后处理函数**：
   - 对 `echo`、`rem`、`::` 开头的行自动替换 14 种全角标点为 ASCII 等价字符
   - 替换 `->` / `=>` 为 ` to `
   - 如果代码里没有 `chcp 65001`，自动在 `@echo off` 后插入一行
   - 所有 4 条解析策略（结构化头部、JSON 降级、裸 fence、原始代码）均调用此函数

### 37.8 脚本 AI 不添加环境检测（`scriptAi.ts`）

System prompt 新增规则：**除非用户明确要求，不在脚本里添加 adb/python 等工具的环境检测代码**，默认假设环境已就绪。

### 37.9 代码健康度总结（本次审查）

**无问题项**：
- `vue-tsc --noEmit` 零错误零警告
- 所有 AI 调用路径（chatWithNotes / extractMemories / testAiConnection / callScriptAi）统一使用 `resolveSystemRole(config)`，无遗漏的硬编码 `'system'`
- `scriptAi.ts` 中 `callApi` 的无用 `systemRole` 变量已清理
- `NoteAiPanel` 的 `scriptPayload` 不写入持久化历史（strip 后再 `setSetting`），避免 SQLite 膨胀

**已知限制**（不影响使用，后续可优化）：
- `AppLayout` 通过 `:ref="onPageRef"` 读取子页面 expose 数据，`ScriptSpacePage` 没有 keep-alive 缓存，首次进入前 `pageRef.value` 为 null，这一帧内 `scriptType`/`editingContent` 返回默认值；由于 AI 面板只有用户主动打开后才发送请求，此时页面必然已挂载，实际不会出现问题
- `maxContextTokens` 字段名有歧义（用户可能误以为它控制模型输出 token 数），建议后续在 Settings 页面加 tooltip 说明：「此值控制笔记内容检索时塞入 prompt 的最大 token 预算，建议设为模型上下文窗口的 60%～75%」

### 37.10 修改文件汇总

| 文件 | 修改内容 |
|------|----------|
| `src/services/noteAi.ts` | 新增 `resolveSystemRole()` export；`AiChatMessage.role` 加 `'developer'`；`buildRequestBody` 不发 `temperature`/`max_completion_tokens`；三处 AI 调用改用 `resolveSystemRole`；`chatWithNotes` 空回复抛错 |
| `src/services/scriptAi.ts` | 新增文件（Phase 36）；本 Phase 重构 system prompt（类型锁定）；新增 `sanitizeBatEchoLines()` BAT 编码后处理；响应解析改为结构化文本格式（4 级降级策略）；`resolveSystemRole` 改为从 `noteAi.ts` 导入；清理无用 `systemRole` 变量 |
| `src/components/notes/NoteAiPanel.vue` | 新增 `visible` prop 控制触发按钮显示；`sendScript()` 改为自动应用；消息气泡改为状态提示 |
| `src/layouts/AppLayout.vue` | 新增 `aiPanelVisible` computed；传 `:visible` 给 `NoteAiPanel` |
| `src/views/script-space/ScriptSpacePage.vue` | `loadScript`/`newScript`/`openLocalFile` 加 `activeTabId.value = ""`；`applyAiScript` 改为 upsert 更新模式 |
| `src/composables/useI18n.ts` | 新增 `scripts.aiAutoSaved` 双语文案 |
