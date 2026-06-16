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
| HTTP 客户端 | 无 | 纯本地应用，无 HTTP 请求 |
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
│   ├── App.vue                         # 根组件（Ctrl+Tab 键盘快捷导航）
│   ├── env.d.ts                        # 类型声明
│   │
│   ├── styles/
│   │   └── main.css                    # TailwindCSS + 玻璃态 CSS 类 + 自定义滚动条
│   │
│   ├── types/
│   │   └── index.ts                    # 全局类型定义（UserInfo, DeviceInfo, LogEntry 等）
│   │
│   ├── api/                            #（已移除）本地应用无 HTTP API 层
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
│   │   └── Sidebar.vue                 # 左侧固定导航栏（256px，玻璃面板）
│   │
│   ├── composables/                    # 可复用组合式函数
│   │   ├── useAdb.ts                   # ADB 操作（listDevices/shell/installApk 等）
│   │   ├── useSerial.ts                # 串口操作（listPorts/connect/send/read）
│   │   ├── useScriptExec.ts            # 脚本执行（Python/BAT/PowerShell）
│   │   └── useTestCaseStore.ts         # 测试用例 + 字段规则状态管理
│   │
│   └── views/                          # 页面视图
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
│       ├── script-space/
│       │   └── ScriptSpacePage.vue     # 脚本空间（分类 + 搜索）
│       └── settings/
│           └── SettingsPage.vue        # 设置页（Profile + 主题 + 数据管理）
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
        ├── mirror.rs                   # 屏幕镜像（scrcpy-server H.264 + screencap 兜底）
        └── script_exec.rs              # 脚本执行（Python/BAT/PowerShell/Shell）
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
| `/notes-space` | `NotesSpacePage.vue` | 笔记空间 |
| `/script-space` | `ScriptSpacePage.vue` | 脚本空间 |
| `/settings` | `SettingsPage.vue` | 设置 |

### 4.3 布局系统

#### 4.3.1 AppLayout（主布局）

**实现**：
- 顶部浮窗导航（由 Sidebar 组件渲染，见 4.3.2）
- 主内容区 `px-margin-page pb-20 md:pb-12 box-border min-h-screen`
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
- 鼠标移出导航栏 2 秒后自动收起（有缓冲时间，悬停可暂停）
- 连接 `Transition` 动画：进入 `0.3s cubic-bezier(0.16,1,0.3,1)` + opacity 渐变，收起 `0.2s`
- `fixed` 定位，不占页面空间，不影响页面内容

**导航项**（按用户使用频率排序）：
Device → Notes → Case → Scripts → Settings（Settings 固定在右侧）

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

### 4.5 Workspace 首页（已移除）

Workspace 页面已在 Phase 9 中移除，路由 redirect 改为 `/case-space`。

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

**实现（Phase 7 — 完整重写为双分页布局 + Phase 8 交互优化）**：
- **连接栏**（上移，`gap-4`）：设备选择下拉 + Scan Devices 按钮 + Connect ADB 按钮 + 连接状态指示
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
    - **屏幕镜像**：双模式渲染 — 优先 scrcpy-server（adb push → forward → start_server → H.264 raw stream），前端 WebCodecs VideoDecoder 解码；若 scrcpy-server push 失败（设备无 root/remount）自动降级为 `adb exec-out screencap -p` 轮询 + canvas.drawImage。所有逻辑在单个 Rust 阻塞线程中顺序执行（先试 scrcpy，失败则切 legacy），避免竞态条件
    - **截图 + 录屏**：截图预览、录制/停止。录屏启动通过 Rust 异步 spawn 执行（不阻塞 UI），停止时 `pkill -SIGINT screenrecord` 后拉取文件
    - **ADB Shell**：命令输入 + 执行，输入历史走 SQLite `input_history` 表
    - **命令执行反馈浮窗**：长耗时操作（Root、Remount、重启、Bugreport 等）点击后在页面顶部弹出玻璃态浮动面板，显示实时执行状态和结果。所有命令执行完毕 3 秒自动关闭；鼠标悬停暂停计时，移出后恢复。快捷指令完成后不自动关闭，显示关闭按钮手动关闭
    - **执行输出面板**：ADB Shell 命令执行后在底部实时显示输出结果，支持清除输出内容
  - **分页二：其他命令**
    - **APK Manager**：安装（文件选择器）+ 卸载 + 已安装应用列表（按 web-adb-tool 规则排序 + 14 条分页 + 自动加载版本 chip + 复制包名/版本 + 查询 APK 路径）
    - **File Manager**：Push/Pull 文件
    - **危险操作**（重装/remount）：点击触发确认弹窗（Teleport 红色警告）
    - **Custom Commands**（仍使用 localStorage，非业务数据高频更新）
- **输入历史**：`text_input`、`app_search`、`connect_ip`、`remote_path` 四种 key 通过 `addInputHistory()` / `getInputHistory()` 走 SQLite `input_history` 表，每 key 最多 20 条。`remote_path` 在 `navigateToPath()`/`navigateToDir()` 中保存
- **历史下拉不透明**：文本历史、远程路径历史、应用搜索历史下拉均使用 `bg-white border shadow-lg` 不透明样式（非 `glass-panel`）
- **连接对话框**（Teleport）：玻璃面板浮层 + USB/TCP/IP 切换 + IP 输入 + 连接按钮

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
  - **左（256px）**：Space 下拉 + 搜索栏 + Favorites + 文件夹树 + Uncategorized
  - **中（flex-1）**：TipTap 富文本编辑器 + 标题栏 + 工具栏 + 编辑区（`max-w-[850px]` 居中 + 边框）
  - **右（Teleport 滑出面板）**：TOC 目录（层级展开/收起，85% 透明，弹性动画）
- **编辑器扩展**：
  - `CodeBlockLowlight` + `highlight.js`（15 种语言语法高亮）
  - 代码块复制按钮（hover 显示，`addCopyButtons` 多次重试注入）
  - 剪切板粘贴图片（`allowBase64: true` + `handlePaste`）
  - 表格增删行列（`isInTable` computed + 工具栏条件显示）
  - 超链接插入（Teleport 弹窗，自动补 `https://`）
  - 图片插入（文件选择器转 base64）
- **导出**：PDF（`html-to-image` + `jsPDF`，隐藏 iframe）、Word（`docx` 包生成真实 .docx）、Markdown（`turndown`）
- **自动保存**：1.5s 防抖写入 SQLite，版本快照 30s 无操作触发
- **数据持久化**：`note_spaces` / `note_folders` / `notes` / `note_versions` / `note_links` 五张表
- **工具栏**：`toolbar-btn` 无边框 + `toolbar-active` 淡紫色高亮，图标 20px
- **搜索**：全文搜索 + 自动展开匹配文件夹 + 黄色高亮匹配笔记
- **拖拽**：HTML5 drag-and-drop（`dragDropEnabled: false`），`dataTransfer` + `effectAllowed`

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

### 4.10 Settings (`src/views/settings/SettingsPage.vue`)

**实现（Phase 14 重构）**：
- **Profile 模块已移除**：不再显示头像/用户名/角色信息
- **Appearance**：主题切换（Light / Dark / System 三选一）
  - `applyTheme()` 操作 `document.documentElement.classList` 的 `dark` 类
  - System 模式监听 `prefers-color-scheme` 媒体查询
  - 主题持久化到 SQLite `app_settings` 表（key: `theme`）
  - Dark 模式 CSS：`html.dark` 暗色背景（`#1a1a2e`）+ `glass-panel`/`glass-card`/`glass-button`/`glass-active`/`glass-input` 暗色变体
- **Data Backup**（合并到 Appearance 卡片内）：
  - Export All Data：导出全部数据为 `.tsb` 备份文件（JSON 格式）
  - Import Data：从 `.tsb` 文件恢复数据（需重启应用）
  - 导出/导入通过 `@tauri-apps/plugin-dialog` 原生文件对话框

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
| `adb_logcat_buffer_resize` | `logcat_buffer_resize(serial, size)` | 扩大 logcat 缓冲区 | `adb -s <serial> logcat -G <size>` |
| `adb_bugreport` | `bugreport(serial)` | 生成 bugreport zip | `adb -s <serial> bugreport` |
| `adb_dmesg` | `dmesg(serial)` | 获取内核日志 | `adb -s <serial> shell dmesg` |

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
| `adb_mirror_start(serial)` | 启动屏幕镜像（scrcpy-server → legacy 兜底） | 单 Rust 阻塞线程：`adb push scrcpy-server.jar` → `adb forward tcp:27183` → `adb shell CLASSPATH=... app_process ...` → TCP 连接读取 H.264 raw stream；任一失败则降级为 `adb exec-out screencap -p` 轮询 |
| `adb_mirror_start_legacy(serial)` | 仅启动 legacy screencap 轮询 | `adb exec-out screencap -p` 循环，事件 `mirror:frame_data` |
| `adb_mirror_stop` | 停止镜像 | 设置停止标志 + 清理 forward |

**通信协议**（scrcpy 模式）：
- TCP 连接 `127.0.0.1:27183`，发送 1 字节 dummy，后续为长度前缀帧
- 帧类型：`0x00` = 编解码器配置（AVCC extradata），`0x01` = H.264 视频帧
- 前端事件：`mirror:mode`（scrcpy/legacy）、`mirror:config`（AVCC extradata base64）、`mirror:frame`（H264 数据 + key/pts）、`mirror:frame_data`（PNG base64）、`mirror:error`、`mirror:ready`

### 5.5 入口和命令注册 (`src-tauri/src/lib.rs`)

```rust
// 所有命令通过 generate_handler! 宏注册
.invoke_handler(tauri::generate_handler![
    adb_list_devices, adb_shell, adb_install, adb_uninstall,
    adb_push, adb_pull, adb_reboot, adb_screenshot,
    adb_logcat_buffer_resize, adb_bugreport, adb_dmesg,
    serial_list_ports, serial_connect, serial_disconnect,
    serial_send, serial_read,
    script_execute_python, script_execute_bat,
    script_execute_powershell, script_execute_shell,
    adb_kill_server, adb_start_server,
    adb_mirror_start, adb_mirror_stop,
    adb_mirror_start_legacy,
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

Test Space 作为桌面客户端，业务数据来源于现有测试平台后端 API（位于 `D:\TestSpace\testcase_management`）。以下为已集成的 API 端点：

| 平台 API | Test Space 使用位置 | 状态 |
|----------|---------------------|------|
无 — 纯本地桌面应用，不依赖任何后端 API。

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
  version: string            // 数据版本号（当前 1.3）
  exportedAt: string         // 导出时间 ISO 字符串
  fieldRuleSets: any[]       // 字段规则集
  caseFiles: any[]           // 用例文件
  recentFiles: any[]         // 最近文件记录
  favorites: string[]        // 收藏路径列表
  settings: Record<string, string>  // 应用设置
  inputHistory: InputHistoryEntry[]  // 输入历史
  logSessions: LogSession[]  // 日志会话
  noteSpaces: NoteSpace[]    // 笔记 Space
  noteFolders: NoteFolder[]  // 笔记文件夹
  notes: NoteItem[]          // 笔记内容
  noteVersions: NoteVersion[]  // 笔记版本历史
  noteLinks: NoteLink[]      // 笔记双向链接
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

### 9.3 权限配置

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
| H.264 WebCodecs 渲染 | 前端监听 `mirror:config` 事件 + AVCC extradata 配置 VideoDecoder，`mirror:frame` 事件送入 H.264 数据解码渲染 | ✅ |
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
