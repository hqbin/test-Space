---
name: dev-doc-workflow
description: 必须遵守的开发文档工作流：开发前阅读开发文档，开发完成后更新开发文档。适用于本项目的任何开发任务。
hooks:
  UserPromptSubmit:
    - hooks:
        - type: command
          command: echo "[dev-doc-workflow] 开发前请先阅读 test-space\DEVELOPMENT.md 了解项目结构和规范。开发完成后请更新开发文档。"
  PostToolUse:
    - matcher: "Write|Edit"
      hooks:
        - type: command
          command: echo "[dev-doc-workflow] 已修改文件。开发完成后请记得更新 test-space\DEVELOPMENT.md（新增更新记录、更新API/数据库变更等）。"
  PreCompact:
    - matcher: "*"
      hooks:
        - type: command
          command: echo "[dev-doc-workflow] 本次修改是否已完成？如已完成，请更新 test-space\DEVELOPMENT.md 中的更新记录。"
---

# 开发文档工作流 (Dev Doc Workflow)

## 核心规则

> **本项目强制要求：每个开发任务都必须遵守"先读文档、后写文档"的工作流。**

## 第一阶段：开发前 — 阅读文档

在开始任何开发任务之前，**必须**先执行以下步骤：

1. **读取 `test-space\DEVELOPMENT.md`** — 打开项目根目录下的 `test-space\DEVELOPMENT.md` 文件并完整阅读
2. **理解技术栈** — 项目是单一 Tauri 2 + Vue 3 (Composition API + `<script setup>`) + TypeScript + TailwindCSS 3 桌面应用，无后端 API 层（4.1 节），所有数据通过 SQLite 直读
3. **理解项目结构** — 阅读"三、项目结构"章节了解前端 `src/` 和后端 `src-tauri/` 的目录组织方式
4. **确认编码规范** — 特别注意：
   - **禁止**使用 PowerShell `Set-Content` / `Out-File` 直接写入 UTF-8 源文件（除非指定 `-Encoding UTF8`）
   - 源代码文件修改**统一使用编辑器的文本替换工具**，不使用 Shell 脚本批量处理
   - 前端使用 TypeScript + Vue，Rust 原生层使用 src-tauri/
   - 所有 UI 交互控件必须使用 `.glass-button` / `.glass-hover` / `.glass-active` CSS 类（见 4.4 节设计系统）
5. **理解数据持久化规则** — 阅读文档开头的"数据持久化守则"和"九、文件持久化"的 9.2 节数据库表结构
6. **理解 UI/UX 一致性守则** — 阅读文档开头的"UI/UX 一致性守则"和"弹窗/对话框守则"

## 第二阶段：开发中 — 记录变更

开发过程中，**必须**记录以下信息以便最终更新文档：

- 新增/修改的文件路径（`src/views/`、`src/composables/`、`src/services/`、`src-tauri/src/` 等）
- 改动的核心逻辑说明
- 新增的数据库表/字段、Tauri 命令、Rust 模块
- 新增的依赖（`package.json` 或 `Cargo.toml`）
- 任何需要注意的架构决策或兼容性说明

## 第三阶段：开发后 — 更新文档

开发任务完成后，**必须**更新 `test-space\DEVELOPMENT.md`，步骤如下：

### 3.1 更新项目概览（如适用）
- 如果修改了技术栈或新增模块，更新"一、项目概述"和"二、技术架构"
- 如果修改了目录结构，更新"三、项目结构"的目录树
- 如果新增了依赖，更新依赖清单（42-104 行）

### 3.2 更新功能章节（如适用）
- 如果修改了路由或布局，更新"4.2 路由系统"或"4.3 布局系统"
- 如果修改了设计系统，更新"4.4 设计系统"
- 如果修改了具体 Space 功能，更新对应的 4.x 模块实现说明（4.6-4.12）
- 如果新增了 Rust 模块或 Tauri 命令，更新"五、Rust 原生层"对应的 5.x 节
- 如果新增了前端 composable，更新"六、前端 Composable"的 6.x 节
- 如果新增了数据库表/字段，更新"9.2 数据库表结构"
- 如果新增了文件持久化功能，更新"九、文件持久化"
- 如果修改了分阶段计划，更新"十、分阶段计划"中对应的 Phase

### 3.3 新增 Phase 记录（**必须**）

在"十、分阶段计划"末尾新增一个 Phase 小节，格式如下：

```markdown
### Phase N — 功能名称（已完成 ✅）

| 模块 | 说明 | 状态 |
|------|------|------|
| 模块名 | 具体改动描述 | ✅ |
| 另一个模块 | 具体描述 | ✅ |

**编译验证**：
| 检查项 | 结果 |
|--------|------|
| `npm run build` (vue-tsc + vite) | ✅ 通过 |
| `cargo check`（如涉及 Rust） | ✅ 通过 |
```

### 3.4 更新内容示例（前端改动）

```markdown
**前端：**

| 文件 | 改动内容 |
|------|---------|
| `src/views/xxx/xxxPage.vue` | 新增/修改了什么 |
| `src/composables/useXxx.ts` | 新增/修改了什么 |
| `src/router/index.ts` | 新增了什么路由 |

**Rust 原生层（如适用）：**

| 文件 | 改动内容 |
|------|---------|
| `src-tauri/src/xxx.rs` | 新增/修改了什么命令 |
| `src-tauri/src/lib.rs` | 注册的新命令 |
| `src-tauri/Cargo.toml` | 新增了什么依赖 |

**数据库变更（如适用）：**

| 表名 | 变更 |
|------|------|
| `xxx` | 新增列 `yyy` / 新建表 |

#### 注意事项

- 新增数据表后必须同步更新 `database.ts` 的 `exportAllData()` / `importAllData()`
- 新增设置项优先使用 `app_settings` 表的键值对模式
```

## 开发后验证清单

- [ ] `npm run build` 通过（TypeScript 类型检查 + Vite 构建）
- [ ] 如果涉及 Rust：`cargo check` / `cargo build` 通过
- [ ] 数据库变更已纳入 `exportAllData` / `importAllData`
- [ ] 新增数据表已在 `migrate()` 中注册 `CREATE TABLE IF NOT EXISTS`
- [ ] UI 新增元素使用 `.glass-button` / `.glass-hover` / `.glass-active` 类
- [ ] 弹窗使用 Teleport + 规范结构（见 4.4 节）
- [ ] `select-none` / `select-text` 全局规则已遵守

## 反模式（禁止行为）

- ❌ **不读文档直接开始编码**
- ❌ **开发完成后不更新文档**
- ❌ **文档更新不完整**（只写代码不记数据库/依赖/架构变更）
- ❌ **Phase 记录中遗漏涉及的源文件**
- ❌ **新增数据表后不更新 `exportAllData` / `importAllData`**
- ❌ **使用 `Set-Content` 无编码参数写入 UTF-8 文件**
- ❌ **自创 UI 样式模式而不使用液态玻璃设计系统**
