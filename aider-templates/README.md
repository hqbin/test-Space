# Aider 全自动工作流 — 多项目复用方案

## 文件说明

| 文件 | 用途 |
|------|------|
| `init_aider_project.py` | **一键初始化脚本**（自动检测技术栈，生成所有配置） |
| `.aider.conf.yml.template` | Aider 主配置模板（手动复制用） |
| `CONVENTIONS.md.template` | 项目编码规范模板（手动复制用） |

工作流脚本（位于 `test-space/` 目录，由 `init_aider_project.py` 自动复制到新项目）：
- `aider_workflow.py` — 7 阶段全自动编排脚本
- `run_workflow.ps1` — PowerShell 快捷启动

---

## 新项目只需两步

### 1. 安装 Aider

```bash
pip install aider-chat
```

### 2. 一键初始化

```bash
# 进入你的项目目录
cd your-project

# 运行初始化脚本（自动检测 Vue/React/Python/Go/Rust 等）
python D:\code\test-Space\aider-templates\init_aider_project.py

# 或指定模型
python D:\code\test-Space\aider-templates\init_aider_project.py --model deepseek/deepseek-chat

# 或先看看会生成什么
python D:\code\test-Space\aider-templates\init_aider_project.py --dry-run
```

初始化后你的项目目录会多出：
```
your-project/
  .aider.conf.yml       ← 项目专属配置（自动检测 lint 命令）
  CONVENTIONS.md         ← 编码规范（自动填充技术栈）
  .aiderignore           ← 排除 node_modules/target 等
  aider_workflow.py      ← 全自动工作流脚本
  run_workflow.ps1       ← 一键启动
```

### 3. 开始用

```powershell
# 设置 API Key
$env:ANTHROPIC_API_KEY="sk-..."

# 交互式结对编程
aider

# 全自动工作流
python aider_workflow.py "你的需求描述"
```

---

## 三种使用模式

### 模式一：全自动（一句话需求）

```bash
python aider_workflow.py "在 Device Space 添加批量重启设备功能"
```

自动执行：分析需求 → 制定计划 → 编码实现 → 代码审查 → 修复问题 → 回归测试 → 提交

### 模式二：快速模式（跳过审查）

```bash
python aider_workflow.py --skip review,fix "修复 CSV 导出中文乱码"
```

### 模式三：交互模式（手动控制）

```bash
# 先和 AI 讨论需求，不改代码
aider
/ask 我想添加一个批量重启功能，帮我分析一下

# 确认后切到编码模式
/code 请实现这个功能

# 改完后审查
/ask 审查刚才的修改

# 满意后提交
/commit
```

---

## 多项目管理策略

### 不同项目不同技术栈时

初始化脚本会自动检测，无需手动配置：

| 项目类型 | 检测依据 | 自动配置的 lint |
|----------|----------|----------------|
| Vue + TypeScript | `package.json` 含 `vue` + `typescript` | `npm run build` |
| React + TypeScript | `package.json` 含 `react` + `typescript` | `npm run build` |
| Rust (Tauri) | `Cargo.toml` 存在 | `cargo check` |
| Python | `requirements.txt` / `pyproject.toml` | `python -m py_compile` |
| Go | `go.mod` 存在 | `go build ./...` |
| Java | `pom.xml` / `build.gradle` | `mvnw compile` / `gradlew compileJava` |

### 共享通用配置

用户级配置（`~/.aider.conf.yml`）放所有项目通用的设置：

```yaml
# 所有项目共享
model: claude-3-7-sonnet-20250219
weak-model: claude-3-5-haiku-20241022
auto-commits: false
dark-mode: true
code-theme: monokai
```

项目级配置（`项目/.aider.conf.yml`）只放项目特定设置。Aider 会先加载用户级，再覆盖项目级。

---

## 工作流阶段详解

```
①  analyze  需求分析   → 优化 prompt，识别模糊点，明确验收标准
②  plan     实现计划   → 列出文件清单、依赖关系、风险等级
③  implement 编码实现  → 遵循 CONVENTIONS.md，自动 commit
④  review   代码审查   → 8 维度检查（功能/规范/UI/类型/错误/性能/安全/影响）
⑤  fix      修复问题   → 修复致命和严重问题，自动 commit
⑥  test     回归测试   → npm run build + cargo check
⑦  commit   最终提交   → 生成规范提交信息
```

### 工作流命令参数

```bash
python aider_workflow.py "需求"              # 完整流程
python aider_workflow.py --skip review,fix   # 跳过审查和修复
python aider_workflow.py --from-stage plan   # 从计划阶段开始
python aider_workflow.py --dry-run           # 预演（看 prompt 不执行）
python aider_workflow.py --timeout 600       # 自定义超时
```

### 失败恢复

工作流执行过程中如果某阶段失败，日志会记录在 `.aider.workflow.log`。你可以：

```bash
# 查看日志
cat .aider.workflow.log

# 从失败阶段续跑
python aider_workflow.py --from-stage implement "原始需求"
```

---

## 常见问题

**Q: 切换到其他项目，Config 不需要改吗？**
A: 不需要。每个项目有自己的 `.aider.conf.yml`，Aider 自动从项目根目录加载。通用设置（模型、暗色模式等）放在 `~/.aider.conf.yml` 即可。

**Q: 工作流脚本需要修改吗？**
A: `aider_workflow.py` 完全通用，不依赖具体项目。它只依赖 `aider` 命令和项目根目录的 `.aider.conf.yml`。

**Q: 如何让 AI 更了解我的项目？**
A: 编辑 `CONVENTIONS.md`，补充项目特有的规则。当你在使用中纠正 AI 第二次时，就把那条规则加到 `CONVENTIONS.md` 里。

**Q: 可以用 DeepSeek 吗？**
A: 可以，初始化时指定 `--model deepseek/deepseek-chat`，或之后在 `.aider.conf.yml` 中修改 `model` 字段。

---

## 参考资源

- [Aider 官方文档](https://aider.chat/docs/)
- [Aider 配置文件参考](https://aider.chat/docs/config/aider_conf.html)
- [Aider 编码规范](https://aider.chat/docs/usage/conventions.html)
- [Aider 聊天命令](https://aider.chat/docs/usage/commands.html)
- [社区规范仓库](https://github.com/Aider-AI/conventions)