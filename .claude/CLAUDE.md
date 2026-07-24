# Test Space 项目指南

## 语言
所有回答、注释、文档输出使用中文。

## 核心工作流
每次任务必须遵循闭环五阶段，不可跳过审查和测试阶段：
**理解需求 → 制定计划 → 执行 → 审查 → 测试**

完整规范见 `dev-workflow` skill 和 `.agents/AGENTS.md`。

## 任务类型自动路由

开始任务时，根据任务内容自动调用对应的 Agent Skill：

| 任务类型 | 条件 | 自动调用 Skill |
|---------|------|---------------|
| **前端修改** | 涉及 Vue 组件、CSS、布局、样式、UI 交互、动效 | `frontend-design` |
| **UI/UX 设计** | 视觉设计、配色、字体、图标、设计系统 | `ui-ux-pro-max` |
| **Bug 修复** | 功能异常、崩溃、错误、测试失败、意外行为 | `systematic-debugging` |
| **其他开发任务** | 后端、数据库、脚本、配置、文档等 | `dev-workflow` |

> **调用方式**：判断任务类型后，使用 `Skill` 工具调用对应的 skill。如果任务同时涉及多个类型，则依次调用。调用 skills 前不需要问我确认，直接执行。

## 项目结构速览

```
test-space/
├── src/                # Vue 前端
│   ├── views/          # 页面
│   ├── components/     # 通用组件
│   ├── composables/    # 组合式函数
│   ├── services/       # 数据服务
│   ├── router/         # 路由
│   ├── stores/         # Pinia 状态
│   └── styles/         # 样式
├── src-tauri/          # Rust 后端
│   └── src/            # Tauri 命令
└── .agents/            # 项目级 AGENT 规范
```

## 关键参考文件

- `test-space/DEVELOPMENT.md` — 主开发文档（架构、功能、UI 规范）
- `.agents/AGENTS.md` — AGENT 项目规范（编码约定、安全检查清单）
- `test-space/src/types/index.ts` — 全局类型定义
- `test-space/src/services/database.ts` — 数据库表结构和迁移
