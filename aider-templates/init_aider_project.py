#!/usr/bin/env python3
"""
一键初始化 Aider 项目配置
=======================
在新项目中运行此脚本，自动检测技术栈并生成所有配置文件。

用法:
    python init_aider_project.py                          # 初始化当前目录
    python init_aider_project.py /path/to/project          # 初始化指定项目
    python init_aider_project.py --model deepseek/deepseek-chat  # 指定模型
    python init_aider_project.py --no-workflow             # 不复制工作流脚本
"""

import sys
import os
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# 模板目录（脚本所在目录）
TEMPLATE_DIR = Path(__file__).parent

# 工作流脚本位置（优先级：同目录 > 兄弟项目 test-space）
_WORKFLOW_LOCAL = TEMPLATE_DIR / "aider_workflow.py"
_WORKFLOW_PROJECT = TEMPLATE_DIR.parent / "test-space" / "aider_workflow.py"
PROJECT_WORKFLOW_DIR = TEMPLATE_DIR if _WORKFLOW_LOCAL.exists() else TEMPLATE_DIR.parent / "test-space"


def detect_tech_stack(project_dir: Path) -> dict:
    """自动检测项目技术栈"""
    stack = {
        "frontend": None,
        "backend": None,
        "database": None,
        "build_tool": None,
        "has_typescript": False,
        "has_rust": False,
        "has_python": False,
        "has_go": False,
        "has_java": False,
        "has_tailwind": False,
        "has_vue": False,
        "has_react": False,
        "has_svelte": False,
        "has_tauri": False,
        "has_electron": False,
        "lint_cmds": [],
        "test_cmd": None,
        "build_cmd": None,
    }

    # 检测前端框架
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        import json
        try:
            with open(pkg_json, encoding="utf-8") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            if "vue" in deps:
                stack["has_vue"] = True
                stack["frontend"] = "Vue"
            if "react" in deps:
                stack["has_react"] = True
                stack["frontend"] = "React"
            if "svelte" in deps:
                stack["has_svelte"] = True
                stack["frontend"] = "Svelte"
            if "typescript" in deps or "@types/" in str(deps):
                stack["has_typescript"] = True
            if "tailwindcss" in deps:
                stack["has_tailwind"] = True
            if "vite" in deps:
                stack["build_tool"] = "Vite"
            if "@tauri-apps" in str(deps):
                stack["has_tauri"] = True
            if "electron" in deps:
                stack["has_electron"] = True

            # 构建命令
            if stack["has_vue"] and stack["has_typescript"]:
                stack["build_cmd"] = "npm run build"
                stack["lint_cmds"].append("typescript: npm run build")
                stack["lint_cmds"].append("vue: npm run build")
            elif stack["has_react"] and stack["has_typescript"]:
                stack["build_cmd"] = "npm run build"
                stack["lint_cmds"].append("typescript: npm run build")
            elif stack["has_typescript"]:
                stack["build_cmd"] = "npm run build"
                stack["lint_cmds"].append("typescript: npm run build")

            if "jest" in deps or "vitest" in deps:
                stack["test_cmd"] = "npm test"
            elif "pytest" in str(deps):
                stack["test_cmd"] = "pytest"

        except Exception:
            pass

    # 检测 Rust
    cargo_toml = project_dir / "Cargo.toml"
    if cargo_toml.exists():
        stack["has_rust"] = True
        stack["backend"] = stack.get("backend") or "Rust"
        stack["lint_cmds"].append("rust: cargo check")

    # 检测 Python
    if list(project_dir.glob("*.py")) or (project_dir / "requirements.txt").exists() or (project_dir / "pyproject.toml").exists():
        stack["has_python"] = True
        if not stack["backend"]:
            stack["backend"] = "Python"
        stack["lint_cmds"].append("python: python -m py_compile *.py")

    # 检测 Go
    if (project_dir / "go.mod").exists():
        stack["has_go"] = True
        stack["backend"] = "Go"
        stack["lint_cmds"].append("go: go build ./...")

    # 检测 Java
    if list(project_dir.glob("pom.xml")) or list(project_dir.glob("build.gradle*")):
        stack["has_java"] = True
        stack["backend"] = "Java"
        if list(project_dir.glob("pom.xml")):
            stack["lint_cmds"].append("java: ./mvnw compile")
        else:
            stack["lint_cmds"].append("java: ./gradlew compileJava")

    # 检测数据库
    if (project_dir / "migrations").exists() or (project_dir / "alembic").exists():
        stack["database"] = "SQL"
    if list(project_dir.glob("**/*.sqlite")) or (project_dir / "prisma").exists():
        stack["database"] = "SQLite"

    return stack


def generate_aider_conf(project_dir: Path, stack: dict, model: str) -> str:
    """生成 .aider.conf.yml"""
    lines = [
        "##########################################################",
        f"# Aider 配置文件 — {project_dir.name}",
        f"# 自动生成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "# https://aider.chat/docs/config/aider_conf.html",
        "##########################################################",
        "",
        "# ====================",
        "# 模型配置",
        "# ====================",
        "",
        f"model: {model}",
        "weak-model: claude-3-5-haiku-20241022",
        "timeout: 120",
        "",
        "# ====================",
        "# 项目规范文件",
        "# ====================",
        "",
        "read:",
        "  - CONVENTIONS.md",
    ]

    # 如果有开发文档
    dev_doc = project_dir / "DEVELOPMENT.md"
    if dev_doc.exists():
        lines.append("  - DEVELOPMENT.md")

    lines.extend([
        "",
        "# ====================",
        "# Git 配置",
        "# ====================",
        "",
        "git: true",
        "gitignore: true",
        "auto-commits: false",
        "dirty-commits: false",
        "attribute-author: true",
        "attribute-committer: true",
        "attribute-co-authored-by: true",
        "git-commit-verify: false",
        "",
        "# ====================",
        "# 代码质量",
        "# ====================",
        "",
        "auto-lint: true",
        "lint-cmd:",
    ])

    if stack["lint_cmds"]:
        for cmd in stack["lint_cmds"]:
            lines.append(f"  - \"{cmd}\"")
    else:
        lines.append('  - "all: echo lint placeholder"')

    lines.extend([
        "",
        "auto-test: false",
    ])

    if stack["test_cmd"]:
        lines.append(f"# test-cmd: {stack['test_cmd']}")

    lines.extend([
        "",
        "# ====================",
        "# 输出与交互",
        "# ====================",
        "",
        "dark-mode: true",
        "code-theme: monokai",
        "stream: true",
        "show-diffs: true",
        "suggest-shell-commands: true",
        "multiline: false",
        "notifications: false",
        "",
        "# ====================",
        "# 缓存与性能",
        "# ====================",
        "",
        "cache-prompts: true",
        "cache-keepalive-pings: 3",
        "map-refresh: auto",
        "",
        "# ====================",
        "# 历史记录",
        "# ====================",
        "",
        "restore-chat-history: true",
        "chat-history-file: .aider.chat.history.md",
        "input-history-file: .aider.input.history",
        "",
        "# ====================",
        "# 文件处理",
        "# ====================",
        "",
        "encoding: utf-8",
        "line-endings: platform",
        "aiderignore: .aiderignore",
        "add-gitignore-files: false",
        "",
        "# ====================",
        "# 其他",
        "# ====================",
        "",
        "chat-language: zh",
        "commit-language: zh",
        "vim: false",
        "detect-urls: true",
        "disable-playwright: true",
        "check-update: false",
        "",
        "# ====================",
        "# 全自动工作流 (python aider_workflow.py)",
        "# ====================",
        "# 阶段: analyze → plan → implement → review → fix → test → commit",
        "# 跳过审查:  python aider_workflow.py --skip review,fix \"需求\"",
        "# 预演模式:  python aider_workflow.py --dry-run \"需求\"",
    ])

    return "\n".join(lines)


def generate_conventions(project_dir: Path, stack: dict) -> str:
    """生成 CONVENTIONS.md"""
    project_name = project_dir.name

    lines = [
        f"# {project_name} 编码规范",
        "",
        "> 本文档为 Aider / AI 编程助手提供项目特定的编码规范指导。",
        "> 所有代码生成和修改必须遵循以下规则。",
        "",
        "## 一、技术栈",
        "",
        "| 层级 | 技术选型 |",
        "|------|----------|",
    ]

    if stack["frontend"]:
        lines.append(f"| 前端框架 | {stack['frontend']} |")
    if stack["build_tool"]:
        lines.append(f"| 构建工具 | {stack['build_tool']} |")
    if stack["has_typescript"]:
        lines.append("| 类型系统 | TypeScript |")
    if stack["has_tailwind"]:
        lines.append("| 样式 | TailwindCSS |")
    if stack["backend"]:
        lines.append(f"| 后端 | {stack['backend']} |")
    if stack["has_tauri"]:
        lines.append("| 桌面框架 | Tauri |")
    if stack["has_electron"]:
        lines.append("| 桌面框架 | Electron |")
    if stack["database"]:
        lines.append(f"| 数据库 | {stack['database']} |")

    lines.extend([
        "",
        "## 二、命名规范",
        "",
        "- 组件/类：PascalCase",
        "- 变量/函数：camelCase",
        "- 常量：UPPER_SNAKE_CASE",
        "- 文件名：根据框架约定",
        "- 布尔值：isXxx / hasXxx / canXxx 前缀",
        "",
        "## 三、类型安全",
        "",
        "- 所有函数参数和返回值必须标注类型",
        "- 禁止使用 `any`，使用 `unknown` + 类型守卫",
        "- 使用可选链 `?.` 和空值合并 `??`",
        "- 禁止非空断言 `!` 除非绝对确定",
        "",
        "## 四、错误处理",
        "",
        "- 异步函数使用 `try/catch`",
        "- 禁止静默吞掉错误",
        "- 服务层返回 `{ data: T } | { error: string }`，不跨层抛异常",
        "",
        "## 五、Git 提交规范",
        "",
        "```",
        "<type>(<scope>): <subject>",
        "```",
        "",
        "**type**：feat / fix / perf / refactor / style / docs / test / chore",
        "",
        "## 六、禁止事项",
        "",
        "1. 禁止使用 `any` 类型",
        "2. 禁止静默吞错误",
        "3. 禁止跨层抛异常",
        "4. 禁止在组件中直接调用 API",
        "5. 禁止提交包含 `console.log` 的代码",
        "6. 禁止硬编码魔法数字",
        "",
        "---",
        "",
        "> **提示**：根据项目实际情况补充具体规范。当纠正 AI 第二次时，将规则加入本文档。",
    ])

    return "\n".join(lines)


def init_project(project_dir: str, model: str = "claude-3-7-sonnet-20250219",
                 with_workflow: bool = True, dry_run: bool = False):
    """初始化项目"""
    project_path = Path(project_dir).resolve()

    if not project_path.exists():
        print(f"❌ 项目目录不存在: {project_path}")
        return False

    print(f"\n{'='*60}")
    print(f"  Aider 项目配置初始化")
    print(f"  目标: {project_path}")
    print(f"{'='*60}\n")

    # 检测技术栈
    print("🔍 检测技术栈...")
    stack = detect_tech_stack(project_path)

    print(f"   前端框架: {stack['frontend'] or '未检测到'}")
    print(f"   构建工具: {stack['build_tool'] or '未检测到'}")
    print(f"   类型系统: {'TypeScript' if stack['has_typescript'] else '未检测到'}")
    print(f"   后端:     {stack['backend'] or '未检测到'}")
    print(f"   数据库:   {stack['database'] or '未检测到'}")
    print(f"   样式:     {'TailwindCSS' if stack['has_tailwind'] else '未检测到'}")
    print(f"   桌面框架: {'Tauri' if stack['has_tauri'] else 'Electron' if stack['has_electron'] else '无'}")
    print()

    if dry_run:
        print("📋 [DRY RUN] 预演模式，不写入文件\n")
        conf_content = generate_aider_conf(project_path, stack, model)
        conventions_content = generate_conventions(project_path, stack)
        print("--- .aider.conf.yml 预览（前 30 行）---")
        for line in conf_content.split("\n")[:30]:
            print(f"  {line}")
        print("...")
        return True

    # 生成 .aider.conf.yml
    conf_path = project_path / ".aider.conf.yml"
    if conf_path.exists():
        print(f"⚠️  {conf_path.name} 已存在，跳过")
    else:
        conf_content = generate_aider_conf(project_path, stack, model)
        with open(conf_path, "w", encoding="utf-8") as f:
            f.write(conf_content)
        print(f"✅ 已创建 .aider.conf.yml")

    # 生成 CONVENTIONS.md
    conventions_path = project_path / "CONVENTIONS.md"
    if conventions_path.exists():
        print(f"⚠️  {conventions_path.name} 已存在，跳过")
    else:
        conventions_content = generate_conventions(project_path, stack)
        with open(conventions_path, "w", encoding="utf-8") as f:
            f.write(conventions_content)
        print(f"✅ 已创建 CONVENTIONS.md")

    # 复制工作流脚本
    if with_workflow:
        workflow_src = PROJECT_WORKFLOW_DIR / "aider_workflow.py"
        workflow_dst = project_path / "aider_workflow.py"

        if workflow_src.exists():
            if workflow_dst.exists():
                print(f"⚠️  aider_workflow.py 已存在，跳过")
            else:
                shutil.copy2(workflow_src, workflow_dst)
                print(f"✅ 已复制 aider_workflow.py")

        run_ps1_src = PROJECT_WORKFLOW_DIR / "run_workflow.ps1"
        run_ps1_dst = project_path / "run_workflow.ps1"

        if run_ps1_src.exists():
            if run_ps1_dst.exists():
                print(f"⚠️  run_workflow.ps1 已存在，跳过")
            else:
                shutil.copy2(run_ps1_src, run_ps1_dst)
                print(f"✅ 已复制 run_workflow.ps1")

    # 创建 .aiderignore
    ignore_path = project_path / ".aiderignore"
    if not ignore_path.exists():
        with open(ignore_path, "w", encoding="utf-8") as f:
            f.write("# 不纳入 Aider 编辑范围的文件\n")
            f.write("node_modules\n")
            f.write("dist\n")
            f.write("build\n")
            f.write("target\n")
            f.write(".git\n")
            f.write("*.log\n")
            f.write("*.lock\n")
            f.write("*.exe\n")
            f.write("*.dll\n")
            f.write(".env\n")
            f.write("package-lock.json\n")
        print(f"✅ 已创建 .aiderignore")

    print(f"\n{'='*60}")
    print(f"  ✅ 初始化完成！")
    print(f"{'='*60}")
    print(f"""
下一步:
  1. 设置 API Key: $env:ANTHROPIC_API_KEY="sk-..."
  2. 编辑 CONVENTIONS.md，补充项目特定规范
  3. 启动 Aider: cd {project_path.name} && aider
  4. 全自动工作流: python aider_workflow.py "你的需求"
""")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="一键初始化 Aider 项目配置",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python init_aider_project.py                          # 初始化当前目录
  python init_aider_project.py /path/to/my-project       # 指定项目路径
  python init_aider_project.py --model deepseek/deepseek-chat  # 指定模型
  python init_aider_project.py --no-workflow             # 不复制工作流脚本
  python init_aider_project.py --dry-run                 # 只检测不生成
        """
    )

    parser.add_argument(
        "project_dir", nargs="?",
        default=".",
        help="项目目录路径（默认当前目录）"
    )
    parser.add_argument(
        "--model", "-m",
        default="claude-3-7-sonnet-20250219",
        help="主模型（默认: claude-3-7-sonnet-20250219）"
    )
    parser.add_argument(
        "--no-workflow", "-n",
        action="store_true",
        help="不复制工作流脚本"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="只检测不生成文件"
    )

    args = parser.parse_args()
    init_project(args.project_dir, args.model, not args.no_workflow, args.dry_run)


if __name__ == "__main__":
    main()