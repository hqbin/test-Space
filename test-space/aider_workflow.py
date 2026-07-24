#!/usr/bin/env python3
"""
Aider 全自动开发工作流编排器
=============================
从一句话需求 → 自动优化 prompt → 制定计划 → 编码实现 → 代码审查 → 修复问题 → 回归测试 → 提交

用法:
    python aider_workflow.py "你的需求描述"
    python aider_workflow.py --skip-review "快速需求"
    python aider_workflow.py --config workflow_config.yaml "需求"
"""

import subprocess
import sys
import os
import json
import time
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# ============================================================
# 配置
# ============================================================

WORK_DIR = Path(__file__).parent
AIDER = "aider"
CHAT_HISTORY = WORK_DIR / ".aider.workflow.history.md"
STAGE_LOG = WORK_DIR / ".aider.workflow.log"
STATE_FILE = WORK_DIR / ".aider.workflow.state.json"


def load_state() -> dict:
    """加载工作流状态"""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_run": None, "last_stage": None, "last_requirement": None, "completed_stages": []}


def save_state(state: dict):
    """保存工作流状态"""
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def clear_state():
    """清除工作流状态"""
    if STATE_FILE.exists():
        STATE_FILE.unlink()
    if CHAT_HISTORY.exists():
        CHAT_HISTORY.unlink()
    log("已清除工作流状态和历史")

# 阶段定义
STAGES = {
    "analyze": {
        "name": "需求分析与Prompt优化",
        "icon": "🔍",
        "prompt_template": """你是一个需求分析专家。请对以下需求进行分析和优化：

【原始需求】
{requirement}

请完成以下任务：
1. 识别需求中的模糊点和缺失信息
2. 明确功能边界和验收标准
3. 指出潜在的技术风险和依赖
4. 输出优化后的需求描述（包含功能点、输入输出、边界条件、错误处理）
5. 如果需求有疑义，列出需要澄清的问题

请用中文输出分析结果。""",
        "auto_commit": False
    },
    "plan": {
        "name": "制定实现计划",
        "icon": "📋",
        "prompt_template": """你是一个架构师。基于上一轮的需求分析结果，请制定详细的实现计划。

请完成以下任务：
1. 列出需要修改的文件清单（包含路径）
2. 对每个文件说明修改内容和原因
3. 识别跨文件的依赖关系和修改顺序
4. 评估每个修改的风险等级（低/中/高）
5. 输出一个分步执行计划

请用中文输出计划，格式清晰。""",
        "auto_commit": False
    },
    "implement": {
        "name": "编码实现",
        "icon": "⚡",
        "prompt_template": """基于上一轮制定的实现计划，请开始编码实现。

【重要约束】
1. 严格遵循 CONVENTIONS.md 中的所有规范
2. 参考 DEVELOPMENT.md 中的项目架构和模块说明
3. 使用玻璃态设计系统（glass-panel、glass-button、glass-hover 等 CSS 类）
4. 弹窗必须使用 Teleport 规范（bg-black/30 backdrop-blur-sm + glass-panel rounded-[2rem]）
5. 页面根容器使用 flex flex-1 min-h-0，禁止使用 h-full
6. 所有函数标注完整类型，错误处理使用 try/catch
7. 修改完成后运行 npm run build 确保通过

请开始实现，每完成一个文件修改后简要说明修改了什么。""",
        "auto_commit": True
    },
    "review": {
        "name": "代码审查",
        "icon": "🔎",
        "prompt_template": """你是一个严格的代码审查员。请审查刚才的所有代码修改。

请从以下维度逐一检查：
1. **功能正确性**：代码是否实现了需求描述的功能
2. **规范遵循**：是否严格遵守 CONVENTIONS.md 的每一条规则
3. **UI一致性**：是否正确使用玻璃态 CSS 类、弹窗规范、布局规范
4. **类型安全**：是否有 any 类型、缺失类型标注、非空断言
5. **错误处理**：是否有未捕获的异常、静默吞掉的错误
6. **性能问题**：是否有内存泄漏、未清理的定时器、不必要的重渲染
7. **安全性**：是否有 SQL 注入、XSS、路径遍历等风险
8. **影响范围**：修改是否破坏了相邻模块的功能

请用中文输出审查报告，按严重程度（致命/严重/警告/建议）分类列出问题。
如果没有发现问题，请明确说明"审查通过"。""",
        "auto_commit": False
    },
    "fix": {
        "name": "修复审查问题",
        "icon": "🔧",
        "prompt_template": """基于上一轮的代码审查报告，请修复所有致命和严重的问题。

对于每个问题：
1. 修改对应的文件
2. 确保修复不引入新问题
3. 修复后自己验证逻辑正确性

警告级别的问题也请尽量修复，建议级别的问题可以酌情处理。

请逐个修复并说明修复了什么。""",
        "auto_commit": True
    },
    "test": {
        "name": "回归测试",
        "icon": "🧪",
        "prompt_template": """请运行项目的构建和测试命令，确保所有修改没有破坏现有功能。

执行以下命令并分析结果：
1. npm run build（TypeScript 类型检查 + Vite 构建）
2. 如果 src-tauri 有修改，运行 cd src-tauri && cargo check

如果构建失败，请分析错误原因并修复。如果修复后仍然失败，请报告具体错误信息。

请用中文输出测试结果。""",
        "auto_commit": False
    },
    "commit": {
        "name": "最终提交",
        "icon": "✅",
        "prompt_template": """请生成一个规范的 Git 提交信息，总结本次所有修改。

提交信息格式：
<type>(<scope>): <简短描述>

<详细说明修改内容>

请用中文写提交信息，遵循项目的 Git 提交规范。""",
        "auto_commit": True
    }
}


def log(msg: str, level: str = "INFO"):
    """记录日志"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)
    with open(STAGE_LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def run_aider(message: str, auto_commit: bool = False, timeout: int = 300) -> dict:
    """
    运行 Aider 单次消息
    
    Returns:
        {"success": bool, "output": str, "error": str}
    """
    cmd = [
        AIDER,
        "--message", message,
        "--chat-history-file", str(CHAT_HISTORY),
        "--restore-chat-history",
        "--no-auto-commits" if not auto_commit else "",
        "--yes-always",  # 自动确认所有操作
        "--no-check-update",
    ]
    cmd = [c for c in cmd if c]  # 过滤空字符串
    
    log(f"执行命令: aider --message ... (auto_commit={auto_commit})")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(WORK_DIR),
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace"
        )
        
        output = result.stdout + result.stderr
        
        if result.returncode != 0:
            log(f"Aider 返回非零退出码: {result.returncode}", "WARN")
            # 非零退出码不一定意味着失败，可能是警告
            if "error" in result.stderr.lower() and "warning" not in result.stderr.lower():
                return {"success": False, "output": output, "error": result.stderr}
        
        return {"success": True, "output": output, "error": ""}
        
    except subprocess.TimeoutExpired:
        log(f"阶段超时（{timeout}秒）", "ERROR")
        return {"success": False, "output": "", "error": f"执行超时（{timeout}秒）"}
    except FileNotFoundError:
        log("找不到 aider 命令，请确保已安装: pip install aider-chat", "ERROR")
        return {"success": False, "output": "", "error": "aider 未安装"}
    except Exception as e:
        log(f"执行异常: {e}", "ERROR")
        return {"success": False, "output": "", "error": str(e)}


def estimate_complexity(requirement: str) -> str:
    """
    估算需求复杂度，决定是否跳过审查阶段
    simple: 简单需求（修复/小调整/文案修改）
    medium: 中等需求（新增功能/逻辑调整）
    complex: 复杂需求（大重构/多模块联动）
    """
    simple_keywords = ["修复", "fix", "bug", "错别字", "文案", "改一下", "改为", "改成", "改颜色",
                       "字号", "间距", "文案", "标题", "默认值", "提示", "rename", "移除",
                       "去掉", "隐藏", "显示", "禁用", "启用"]
    complex_keywords = ["重构", "架构", "重写", "redesign", "重新设计", "迁移", "从零",
                        "大改", "整体", "重构", "全量", "多模块", "跨模块", "系统级"]
    
    r = requirement.lower()
    simple_count = sum(1 for k in simple_keywords if k in r)
    complex_count = sum(1 for k in complex_keywords if k in r)
    
    if complex_count > 0:
        return "complex"
    if simple_count >= 2 or simple_count > 0 and len(requirement) < 20:
        return "simple"
    return "medium"


def run_workflow(requirement: str, skip_stages: list = None, dry_run: bool = False,
                 resume: bool = False, auto_skip_review: bool = False):
    """
    运行完整工作流
    
    Args:
        requirement: 用户需求
        skip_stages: 要跳过的阶段列表
        dry_run: 是否只打印不执行
        resume: 是否从上次失败处续跑
        auto_skip_review: 是否自动跳过审查（简单需求）
    """
    if skip_stages is None:
        skip_stages = []
    
    # 清空日志
    with open(STAGE_LOG, "w", encoding="utf-8") as f:
        f.write(f"# Aider 工作流日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    
    log("=" * 60)
    log(f"开始全自动工作流")
    log(f"需求: {requirement}")
    log(f"跳过阶段: {skip_stages if skip_stages else '无'}")
    if auto_skip_review:
        log(f"智能模式: 简单需求，自动跳过审查阶段")
    log("=" * 60)
    
    # 如果不是续跑模式，删除旧的历史文件
    if not resume:
        if CHAT_HISTORY.exists():
            CHAT_HISTORY.unlink()
            log("已清除旧会话历史")
    
    stage_order = ["analyze", "plan", "implement", "review", "fix", "test", "commit"]
    results = {}
    state = load_state()
    completed_stages = state.get("completed_stages", []) if resume else []
    
    for stage_key in stage_order:
        if stage_key in skip_stages:
            log(f"跳过阶段: {stage_key}", "SKIP")
            continue
        
        # 智能跳过：简单需求跳过审查和修复
        if auto_skip_review and stage_key in ("review", "fix"):
            log(f"智能跳过: {STAGES[stage_key]['name']}（简单需求）", "SKIP")
            results[stage_key] = {"success": True, "output": "(auto-skipped)", "error": ""}
            continue
        
        # 续跑模式：已完成的阶段跳过
        if resume and stage_key in completed_stages:
            log(f"续跑跳过: {STAGES[stage_key]['name']}（上次已完成）", "SKIP")
            results[stage_key] = {"success": True, "output": "(resumed)", "error": ""}
            continue
        
        stage = STAGES[stage_key]
        log(f"\n{'='*40}")
        log(f"阶段 {stage_order.index(stage_key)+1}/{len(stage_order)}: {stage['icon']} {stage['name']}")
        log(f"{'='*40}")
        
        prompt = stage["prompt_template"].format(requirement=requirement)
        
        if dry_run:
            log(f"[DRY RUN] 将发送 prompt ({len(prompt)} 字符):")
            log(f"[DRY RUN] {prompt[:200]}...")
            results[stage_key] = {"success": True, "output": "(dry run)", "error": ""}
            continue
        
        # 根据阶段类型设置超时
        timeout = 600 if stage_key in ("implement", "fix", "test") else 300
        
        result = run_aider(prompt, auto_commit=stage["auto_commit"], timeout=timeout)
        results[stage_key] = result
        
        # 保存状态
        if result["success"]:
            log(f"✅ 阶段 {stage['name']} 完成")
            completed_stages.append(stage_key)
            save_state({
                "last_run": datetime.now().isoformat(),
                "last_stage": stage_key,
                "last_requirement": requirement,
                "completed_stages": completed_stages
            })
        else:
            log(f"❌ 阶段 {stage['name']} 失败: {result['error']}")
            save_state({
                "last_run": datetime.now().isoformat(),
                "last_stage": stage_key,
                "last_requirement": requirement,
                "completed_stages": completed_stages
            })
            
            # 对于关键阶段失败，终止工作流
            if stage_key in ("implement", "fix"):
                log("关键阶段失败，终止工作流", "ERROR")
                break
            else:
                log("非关键阶段失败，继续下一阶段", "WARN")
    
    # 全部完成则清除状态
    all_stages = [s for s in stage_order if s not in skip_stages]
    if auto_skip_review:
        all_stages = [s for s in all_stages if s not in ("review", "fix")]
    
    success_stages = [k for k, r in results.items() if r.get("success")]
    if set(success_stages) >= set(all_stages):
        clear_state()
        log("✅ 所有阶段已完成，清除工作流状态")
    
    # 最终总结
    log(f"\n{'='*60}")
    log("工作流执行完毕")
    log(f"{'='*60}")
    
    for stage_key in stage_order:
        if stage_key in skip_stages:
            log(f"  ⏭️ {STAGES[stage_key]['name']}: 已跳过")
        elif stage_key in results:
            status = "✅" if results[stage_key]["success"] else "❌"
            log(f"  {status} {STAGES[stage_key]['name']}")
        else:
            log(f"  ⬜ {STAGES[stage_key]['name']}: 未执行")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Aider 全自动开发工作流 - 从需求到提交一站式自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python aider_workflow.py "在 Device Space 添加批量重启功能"
  python aider_workflow.py "修复性能监控的 CSV 导出 bug"
  python aider_workflow.py "改一下按钮颜色"
  python aider_workflow.py --dry-run "测试需求"
        """
    )
    
    parser.add_argument("requirement", nargs="?", help="开发需求描述")
    parser.add_argument(
        "--skip", "-s",
        help="跳过的阶段，逗号分隔",
        default=""
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="预演模式，只打印各阶段 prompt 不执行"
    )
    parser.add_argument(
        "--force-full", "-f",
        action="store_true",
        help="强制完整流程（不跳过审查，不自动续跑）"
    )
    
    args = parser.parse_args()
    
    # 交互式输入需求
    requirement = args.requirement
    if not requirement:
        print("\n" + "=" * 60)
        print("  Aider 全自动开发工作流")
        print("  从需求到提交，一站式自动化")
        print("=" * 60)
        print()
        
        # 检查是否有上次未完成的工作流
        state = load_state()
        if state.get("last_requirement") and state.get("last_stage"):
            print(f"📌 上次工作流: {state['last_requirement']}")
            print(f"   当前阶段: {STAGES.get(state['last_stage'], {}).get('name', state['last_stage'])}")
            print(f"   已完成: {', '.join(STAGES[s]['name'] for s in state.get('completed_stages', []) if s in STAGES)}")
            print()
            choice = input("[c] 继续上次  [n] 新需求  [r] 重新运行: ").strip().lower()
            if choice == "c":
                # 续跑模式
                print(f"\n🔁 续跑: {state['last_requirement']}")
                results = run_workflow(state["last_requirement"], resume=True, dry_run=args.dry_run)
                all_success = all(r["success"] for r in results.values())
                sys.exit(0 if all_success else 1)
            elif choice == "r":
                requirement = state["last_requirement"]
                clear_state()
            else:
                requirement = input("请输入开发需求: ").strip()
        else:
            requirement = input("请输入开发需求: ").strip()
        
        if not requirement:
            print("❌ 需求不能为空")
            sys.exit(1)
    
    # 解析跳过阶段
    skip_stages = [s.strip() for s in args.skip.split(",") if s.strip()]
    
    # 检查上次工作流状态（非交互模式下自动处理）
    state = load_state()
    resume = False
    auto_skip = False
    
    if not args.force_full and state.get("last_requirement"):
        # 如果是同一个需求且上次未完成
        if state["last_requirement"] == requirement and state.get("last_stage"):
            print(f"\n📌 检测到上次未完成的工作流:")
            print(f"   当前阶段: {STAGES.get(state['last_stage'], {}).get('name', state['last_stage'])}")
            print(f"   已完成: {', '.join(STAGES[s]['name'] for s in state.get('completed_stages', []) if s in STAGES)}")
            print(f"\n🔁 自动续跑...\n")
            resume = True
    
    # 如果不是续跑，估算复杂度，自动跳过简单需求的审查
    if not resume and not args.force_full:
        complexity = estimate_complexity(requirement)
        if complexity == "simple":
            print(f"\n🤖 智能判断: 简单需求，自动跳过审查阶段\n")
            auto_skip = True
        elif complexity == "complex":
            print(f"\n🧠 智能判断: 复杂需求，执行完整流程\n")
    
    # 如果不是续跑，先清除状态
    if not resume:
        clear_state()
    
    # 运行工作流
    results = run_workflow(
        requirement,
        skip_stages=skip_stages,
        dry_run=args.dry_run,
        resume=resume,
        auto_skip_review=auto_skip
    )
    
    # 返回退出码
    all_stages = ["analyze", "plan", "implement", "review", "fix", "test", "commit"]
    active_stages = [s for s in all_stages if s not in skip_stages]
    if auto_skip:
        active_stages = [s for s in active_stages if s not in ("review", "fix")]
    
    all_success = all(
        results.get(s, {}).get("success", False) for s in active_stages
    )
    sys.exit(0 if all_success else 1)


if __name__ == "__main__":
    main()