# 自动化模块 完整设计方案

> 本文档是「Test Space - 自动化」模块的完整设计规范，涵盖架构、YAML 用例格式、AI 自修复、报告系统、数据库设计、UI 集成和实施路线图。

---

## 目录

1. [定位与目标](#一定位与目标)
2. [整体架构](#二整体架构)
3. [YAML 用例格式规范](#三yaml-用例格式规范)
4. [Python 引擎设计](#四python-引擎设计)
5. [AI 自修复系统](#五ai-自修复系统)
6. [报告系统设计](#六报告系统设计)
7. [数据库设计](#七数据库设计)
8. [Test Space UI 集成](#八test-space-ui-集成)
9. [团队协作设计](#九团队协作设计)
10. [实施路线图](#十实施路线图)

---

## 一、定位与目标

### 核心目标

| 目标 | 说明 |
|------|------|
| 健壮性优先 | 脚本在 UI 小幅变更后仍能运行，不是一改就挂 |
| 一次探索，持续回放 | 探索产物版本化存储，回放无需重新探索 |
| AI 自修复兜底 | 修复失败时有完整链路记录，不是黑盒 |
| 报告可分享 | HTML 报告自包含，微信/钉钉传一个文件即可 |
| 团队可协作 | YAML 用例入库管理，支持导入导出，Git 友好 |

### 适用场景

- Android TV / 机顶盒 UI 功能回归测试
- 发版前冒烟测试（smoke）
- UI 变更影响分析（新旧 StateGraph diff）
- 跨版本焦点导航稳定性验证

---

## 二、整体架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                  Test Space — 自动化模块                              │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Vue 前端层（/auto-space 路由）                    │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │   │
│  │  │ 用例管理  │ │ YAML编辑  │ │ 执行控制台 │ │ 报告查看器     │  │   │
│  │  │(列表/搜索)│ │(Monaco)  │ │(实时日志) │ │(内嵌+导出)     │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↕ Tauri IPC                                │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Rust 原生层                                       │   │
│  │  adb.rs（复用）  auto_runner.rs（新增：Python进程管理+管道）    │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↕ 子进程                                   │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Python 引擎层（tv_engine/）                       │   │
│  │  core/device.py    core/state.py    core/explorer.py         │   │
│  │  core/runner.py    core/healer.py   core/reporter.py         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                          ↕ ADB                                      │
│                   Android TV / 机顶盒                                │
└─────────────────────────────────────────────────────────────────────┘

数据层（SQLite，复用 database.ts 迁移体系）：
  auto_cases 表       — 用例元数据（id/name/tags/yaml内容）
  auto_run_records 表 — 每次执行记录（时间/设备/结果摘要）
  auto_run_steps 表   — 步骤级别执行记录（含截图路径/修复日志）
  auto_state_graphs 表 — StateGraph 版本存档

文件层（app data 目录，不入 SQLite）：
  screenshots/        — 步骤截图（按 run_id 分目录）
  reports/            — HTML 报告（自包含）
  graphs/             — StateGraph JSON
```

---

## 三、YAML 用例格式规范

### 3.1 设计原则

1. **意图驱动**：描述"导航到电影菜单"，而不是"按3次右键"
2. **多层定位**：每个 target 有 4 层 fallback，UI 改版自动降级
3. **元素指纹**：存储元素的多维特征（id + text + position + 视觉 hash）
4. **步骤自描述**：`desc` 字段直接生成报告文字，不需要额外注释
5. **失败策略可配置**：每步独立配置 on_failure（skip / abort / ai_heal / retry）

### 3.2 完整 YAML 格式

```yaml
# ============================================================
# Test Space 自动化用例 Schema v1.0
# ============================================================

meta:
  id: "TC-TV-001"                    # 唯一 ID，建议命名规范：TC-{模块}-{序号}
  name: "首页进入电影频道并验证播放"   # 用例名称（中英文均可）
  author: "zhangsan"                 # 作者，用于报告展示和 blame
  version: "1.2"                     # 用例版本，每次修改建议递增
  tags:
    - "smoke"                        # 标签：用于分组运行和报告筛选
    - "home"
    - "playback"
  priority: "P0"                     # P0/P1/P2/P3，影响报告排序和告警
  description: |                     # 用例描述（多行，出现在报告摘要）
    从首页导航到电影频道，
    选择第一个内容项并验证播放器正常启动。
  device_requirement:
    min_api: 28
    app_package: "com.example.tvlauncher"
    app_version_min: "2.0.0"         # 可选：最低 app 版本

# ── 前置条件 ────────────────────────────────────────────────
setup:
  - action: launch_app
    package: "com.example.tvlauncher"
    wait_activity: "com.example.tv.MainActivity"
    timeout: 8000

  - action: wait_stable                # 等待 UI 稳定（无新界面跳转）
    timeout: 3000

  - action: assert_app_foreground      # 断言 App 在前台
    package: "com.example.tvlauncher"

# ── 测试步骤 ────────────────────────────────────────────────
steps:

  # ---------- 导航到目标元素（TV 核心操作）--------------------
  - id: "step_01"
    desc: "从首页导航到电影频道菜单项"
    action: navigate_to
    target:
      primary:
        by: resource_id
        value: "com.example.tv:id/menu_movie"
      fallback1:
        by: content_desc
        value: "电影"
      fallback2:
        by: text_contains           # 文字包含匹配（宽松）
        value: "电影"
      fallback3:
        by: visual_match            # 视觉模板匹配（最后手段）
        template: "assets/ref/btn_movie.png"
        threshold: 0.82
    max_steps: 25                   # 最多按25次方向键，防死循环
    timeout: 8000
    on_failure: "ai_heal"           # 失败时触发 AI 修复

  # ---------- 断言当前焦点 ------------------------------------
  - id: "step_02"
    desc: "确认焦点已到达电影频道菜单项"
    action: assert_focused
    target:
      primary:
        by: resource_id
        value: "com.example.tv:id/menu_movie"
      fallback1:
        by: content_desc
        value: "电影"
    on_failure: "ai_heal"

  # ---------- 按键操作 ----------------------------------------
  - id: "step_03"
    desc: "按 OK 键进入电影频道"
    action: press_key
    key: DPAD_CENTER
    wait_after: 500                 # 操作后等待 ms

  # ---------- 等待条件 ----------------------------------------
  - id: "step_04"
    desc: "等待电影列表页面加载完成"
    action: wait_for
    condition:
      type: element_exists
      target:
        primary:
          by: resource_id
          value: "com.example.tv:id/movie_list"
        fallback1:
          by: content_desc
          value: "电影列表"
    timeout: 6000
    on_failure: "abort"             # 页面未加载直接终止

  # ---------- 截图断言 ----------------------------------------
  - id: "step_05"
    desc: "视觉断言：页面标题区域应包含「电影」文字"
    action: assert_visual
    check: region_contains_text
    region: "top_20_percent"        # 断言区域（top/center/bottom + 百分比）
    value: "电影"
    screenshot: true                # 强制截图（供报告展示）
    on_failure: "ai_heal"

  # ---------- 复合操作：导航 + 点击 ---------------------------
  - id: "step_06"
    desc: "导航到第一个电影内容项并进入"
    action: navigate_to
    target:
      primary:
        by: resource_id
        value: "com.example.tv:id/content_item_0"
      fallback1:
        by: index                   # 按可聚焦元素索引定位
        value: 0
        parent: "com.example.tv:id/movie_list"
      fallback2:
        by: class_and_index
        class: "androidx.leanback.widget.ImageCardView"
        index: 0
    max_steps: 15
    on_failure: "ai_heal"

  - id: "step_07"
    desc: "按 OK 键开始播放"
    action: press_key
    key: DPAD_CENTER

  # ---------- 等待 + 断言组合 ---------------------------------
  - id: "step_08"
    desc: "等待 10 秒后验证播放进度条出现"
    action: wait_then_assert
    wait_seconds: 10
    assert:
      type: element_exists
      target:
        primary:
          by: resource_id
          value: "com.example.tv:id/player_progress"
        fallback1:
          by: content_desc
          value: "播放进度"
        fallback2:
          by: visual_match
          template: "assets/ref/player_progress_bar.png"
          threshold: 0.75
    timeout: 15000
    screenshot: true
    on_failure: "abort"

  # ---------- 自定义 ADB Shell 断言 ---------------------------
  - id: "step_09"
    desc: "通过 dumpsys media 验证播放状态为 PLAYING"
    action: assert_shell
    command: "dumpsys media.player | grep -c 'state=PLAYING'"
    expected_output_contains: "1"
    on_failure: "skip"              # 此步失败不影响整体，记录警告继续

# ── 后置清理 ────────────────────────────────────────────────
teardown:
  - action: press_key
    key: HOME
  - action: wait_stable
    timeout: 1000

# ── 变量（可被 CI 注入覆盖）─────────────────────────────────
variables:
  target_package: "com.example.tvlauncher"
  max_nav_steps: 25
```

### 3.3 action 类型完整清单

| action | 说明 |
|--------|------|
| `launch_app` | 启动 App，可等待指定 Activity |
| `navigate_to` | TV 焦点导航到目标元素，自动规划 DPAD 路径 |
| `press_key` | 发送按键（DPAD_UP/DOWN/LEFT/RIGHT/CENTER/BACK/HOME/MENU 等） |
| `press_key_sequence` | 连续按键序列，如 `[RIGHT, RIGHT, DOWN, CENTER]` |
| `wait_for` | 等待条件满足（element_exists / activity_is / no_loading） |
| `wait_stable` | 等待 UI 稳定（500ms 内无新界面/元素变化） |
| `wait_then_assert` | 等待 N 秒后断言 |
| `assert_focused` | 断言指定元素当前拥有焦点 |
| `assert_visual` | 视觉断言（截图区域包含文字 / 视觉相似度） |
| `assert_element` | 断言元素存在/不存在/属性值 |
| `assert_app_foreground` | 断言指定 App 在前台 |
| `assert_shell` | 执行 ADB shell 命令断言输出 |
| `screenshot` | 强制截图并保存到报告 |
| `input_text` | 向焦点元素输入文字（搜索框等场景） |
| `swipe` | 滑动（TVApp 内少数需要触摸的场景）|
| `set_variable` | 运行时设置变量，供后续步骤引用 |

### 3.4 on_failure 策略说明

| 策略 | 行为 |
|------|------|
| `skip` | 跳过本步，记录 WARNING，继续后续步骤 |
| `abort` | 立即终止用例，标记为 FAILED，执行 teardown |
| `retry` | 原地重试 N 次（默认 2）后决定 skip 或 abort |
| `ai_heal` | 触发 AI 修复流程，修复成功则继续，修复失败则 abort |


---

## 四、Python 引擎设计

### 4.1 目录结构

```
tv_engine/                        # Python 引擎根目录（与 test-space/ 同级）
├── __init__.py
├── requirements.txt              # uiautomator2, Pillow, imagehash, pyyaml, requests
├── main.py                       # CLI 入口：run / explore / diff 子命令
│
├── core/
│   ├── device.py                 # 设备控制层（DPAD 导航、截图、UI tree）
│   ├── state.py                  # 状态定义（TVState + 指纹计算）
│   ├── navigator.py              # 焦点路径规划（BFS + 贪心降级）
│   ├── explorer.py               # 自动探索引擎（BFS 状态图构建）
│   ├── runner.py                 # 用例回放引擎（YAML 解析 + 步骤执行）
│   ├── healer.py                 # AI 自修复（多场景修复策略）
│   ├── reporter.py               # 报告生成（HTML 自包含报告）
│   └── locator.py                # 多层定位解析器（fallback 链）
│
├── actions/                      # action 实现（每个 action 一个文件）
│   ├── navigate.py
│   ├── press_key.py
│   ├── wait.py
│   ├── assert_actions.py
│   └── ...
│
├── assets/
│   └── ref/                      # 参考截图模板（用于 visual_match）
│
├── cases/                        # YAML 用例文件（从 DB 导出后存放于此）
│   └── *.yaml
│
├── graphs/                       # StateGraph JSON（版本化）
│   └── {package}_{version}_{date}.json
│
└── reports/                      # HTML 报告输出目录
    └── {run_id}/
        ├── index.html
        └── {case_id}/
            ├── report.html
            └── screenshots/
```

### 4.2 核心模块说明

#### device.py — 设备控制层

封装所有 uiautomator2 + ADB 操作，对上层只暴露高层语义接口：

```
关键方法：
  connect(serial)          → 连接设备
  get_ui_tree()            → 获取 XML UI Tree
  get_focused_element()    → 获取当前焦点元素（focused="true"）
  get_focusable_elements() → 获取所有可聚焦元素列表
  press_key(keycode)       → 发送按键
  screenshot()             → 截图，返回 PIL Image
  get_current_activity()   → 当前 Activity 名
  wait_stable(timeout)     → 等待 UI 稳定
```

#### state.py — 状态定义

```python
@dataclass
class TVState:
    activity: str            # 当前 Activity
    focused_id: str          # 焦点元素 resource-id
    focused_desc: str        # 焦点元素 content-desc
    focused_text: str        # 焦点元素 text
    focusable_ids: frozenset # 所有可聚焦元素 id 集合
    screenshot_hash: str     # 感知哈希（phash，用于视觉相似度）

    def fingerprint(self) -> str:
        # MD5(activity + focused_id + sorted(focusable_ids))
        # 相同 Activity 不同焦点 = 不同状态

    def visual_similarity(self, other: 'TVState') -> float:
        # 基于 phash 的 Hamming 距离，返回 0-1 相似度分
```

#### navigator.py — 焦点路径规划

**三级规划策略（按可靠性降级）：**

```
Level 1: 图谱规划（最优）
  - 从当前 StateGraph 查找已知的 (current_state → target_state) 路径
  - 直接按记录的按键序列执行
  - 适用于：探索过的路径，最快最准

Level 2: 空间贪心（中等）
  - 获取目标元素的 bounds 坐标
  - 获取当前焦点元素的 bounds 坐标
  - 计算方向向量（右/左/上/下），按方向逐步移动
  - 每步后检查焦点是否更靠近目标（欧氏距离）
  - 超过 max_steps 则降级 Level 3
  - 适用于：未探索的路径，TV 标准 Leanback 布局

Level 3: 全遍历搜索（兜底）
  - 从当前焦点 BFS 枚举所有可达焦点元素
  - 找到目标后按规划路径执行
  - 比 Level 2 慢但更可靠（处理自定义焦点逻辑的 TV UI）
  - 适用于：非标准焦点导航逻辑
```

---

## 五、AI 自修复系统

### 5.1 修复触发场景分类

AI 修复不只是"找不到元素"，需要覆盖以下 7 种异常场景：

| 场景 | 描述 | 修复策略 |
|------|------|---------|
| **UI_ELEMENT_MOVED** | 元素存在但位置/层级变了 | 视觉锚点重定位 |
| **UI_ELEMENT_RENAMED** | resource-id 或 content-desc 改了 | 语义相似度匹配 |
| **UI_ELEMENT_MISSING** | 元素完全消失（UI 重构） | LLM 视觉理解 + 全局搜索 |
| **NAVIGATION_PATH_CHANGED** | 路径变了（多了/少了一层菜单） | 重新探索局部子图 |
| **PAGE_LOAD_TIMEOUT** | 页面加载超时（性能劣化或网络） | 延长等待 + 重试 |
| **UNEXPECTED_DIALOG** | 意外弹出对话框/广告/更新提示 | 自动关闭弹窗后继续 |
| **APP_CRASH_OR_ANR** | App 崩溃或无响应 | 重启 App + 恢复到检查点 |

### 5.2 修复流程设计

```
触发条件：step 执行失败 且 on_failure == "ai_heal"

修复流程（按成本从低到高依次尝试）：

── 阶段 1：快速本地修复（无 LLM，毫秒级）──────────────────
1a. 多属性指纹匹配
    - 用步骤定义的 target 所有 fallback 层依次尝试
    - primary → fallback1 → fallback2 → fallback3
    - 成功则修复，记录"降级到 fallbackN"

1b. 语义相似度匹配
    - 取当前所有可聚焦元素的 (resource_id, content_desc, text)
    - 与 step target 的字段做编辑距离/包含关系匹配
    - 相似度 > 0.8 视为命中（如 "btn_movie_1" vs "btn_movie_entry"）
    - 成功则修复，记录"语义相似度匹配"

1c. 弹窗检测与自动关闭
    - 检测当前界面是否有 Dialog / AlertDialog / PopupWindow
    - 自动按 BACK 或找 close/cancel 按钮关闭
    - 关闭后重试原步骤
    - 适用于 UNEXPECTED_DIALOG 场景

── 阶段 2：LLM 视觉修复（有 LLM，秒级）──────────────────
2a. 构建 multimodal prompt：
    输入 1：step 定义（target + desc + action）
    输入 2：参考截图（探索时该步骤的成功截图）
    输入 3：当前截图
    输入 4：当前 UI tree XML（限 3000 字符，提取核心节点）

    Prompt 结构（调用已配置的 AI Provider）：
    ┌──────────────────────────────────────────────────────┐
    │ 系统：你是 Android TV UI 自动化修复专家。            │
    │                                                      │
    │ 任务：该自动化步骤执行失败，请分析原因并给出修复方案。│
    │                                                      │
    │ 步骤定义：{step_yaml}                                │
    │ 失败原因：{error_message}                            │
    │ 参考截图：[IMAGE_REF]（步骤正常时的截图）            │
    │ 当前截图：[IMAGE_CUR]（失败时的截图）                │
    │ 当前UI树：{ui_tree_summary}                          │
    │                                                      │
    │ 请以 JSON 格式返回：                                 │
    │ {                                                    │
    │   "failure_type": "UI_ELEMENT_MOVED|...",            │
    │   "analysis": "原因分析（一句话）",                  │
    │   "repair_action": "navigate_to|press_key|...",      │
    │   "new_target": {                                    │
    │     "primary": {"by": "...", "value": "..."},        │
    │     "fallback1": {...}                               │
    │   },                                                 │
    │   "additional_steps": [...],  // 如需先关弹窗等      │
    │   "confidence": 0.85,         // 修复置信度 0-1      │
    │   "update_suggestion": "..."  // 建议更新 YAML 的说明│
    │ }                                                    │
    └──────────────────────────────────────────────────────┘

2b. 解析 LLM 返回的修复方案，执行修复操作

2c. 验证修复结果（执行原步骤断言）

── 阶段 3：局部重新探索（重型修复，用于 PATH_CHANGED）────
3a. 从当前 Activity 重新探索可达状态
3b. 找到与 step 期望 Activity/元素匹配的状态
3c. 更新 StateGraph 局部子图
3d. 重新规划导航路径并执行

── 修复结果处理 ───────────────────────────────────────────
成功：
  - 继续后续步骤
  - 记录修复日志（阶段、方式、置信度）
  - 在报告中橙色标注，并展示 LLM 的 update_suggestion
  - 不自动修改 YAML（只建议，人工决定）

失败：
  - 标记步骤为 HEAL_FAILED
  - 根据 on_failure 配置决定 skip 或 abort
  - 报告中红色标注，展示完整修复尝试链
```

### 5.3 AI 接入方式

复用项目现有的 `aiSettings.ts` 体系，支持已配置的所有 Provider：
- Azure OpenAI（需视觉模型：gpt-4o / gpt-5）
- OpenAI（gpt-4o / gpt-4-vision）
- DeepSeek（deepseek-chat，文字分析为主）
- Custom Endpoint（任何兼容 OpenAI 格式的视觉模型）

Python 端通过调用 Test Space 暴露的 Tauri 命令获取 AI 配置，或从 SQLite 直接读取（Python 与同一个 DB 文件通信）。

### 5.4 修复置信度阈值

| 置信度 | 行为 |
|--------|------|
| ≥ 0.9 | 自动执行修复，不阻断用例 |
| 0.7 ~ 0.9 | 执行修复，报告中标注橙色警告 |
| < 0.7 | 修复为高风险，标记 UNCERTAIN，执行后额外截图验证 |
| AI 调用失败 | 降级为阶段 1 本地修复，记录 AI_UNAVAILABLE 日志 |


---

## 六、报告系统设计

### 6.1 设计理念

不参考 Allure（太工程化、样式陈旧）。报告设计对标现代 SaaS 产品的 Dashboard 风格：

- **视觉语言**：继承 Test Space 的液态玻璃设计系统（glass-panel、渐变色卡、Material Symbols 图标）
- **自包含**：CSS/JS/图片全部 inline，单个 HTML 文件，零依赖，离线可用
- **双语**：报告头部语言切换按钮（中/EN），所有标签文字切换，用例 desc 字段保持原样
- **可分享**：直接在 Test Space 内嵌查看，也可导出为独立 HTML 文件发给他人

### 6.2 套件报告（index.html）布局

```
┌──────────────────────────────────────────────────────────────────┐
│  🧪 Test Space 自动化报告             [中/EN]  [导出]  [刷新]     │  ← 顶部栏
│  执行时间：2026-07-08 14:30:22   设备：Xiaomi Box S (API 30)      │
│  App：com.example.tv v2.3.1      耗时：4分 32秒                  │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  总用例数     │  通过         │  失败         │  AI 修复介入        │
│    12        │   9 (75%)    │   2 (17%)    │   1 (8%)           │  ← 指标卡片
│  🔵 大圆圈   │  🟢 填充圈   │  🔴 填充圈   │  🟠 填充圈          │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│  状态分布（横向进度条）   ████████████████░░░░░░░░░░░░            │
│  标签筛选：[全部] [smoke] [home] [playback] [regress]             │
│  排序：[优先级 ▼] [耗时 ▼] [状态 ▼]                              │
├──────────────────────────────────────────────────────────────────┤
│  用例列表（卡片式，每行一条）                                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ✅ TC-TV-001  首页进入电影频道并验证播放          2分10秒  │   │
│  │  🏷 smoke  home  playback    步骤 9/9 通过               │   │
│  │  zhangsan · 设备 Xiaomi Box S                   [详情 ›] │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ ❌ TC-TV-003  搜索功能验证                        1分05秒  │   │
│  │  🏷 smoke  search    步骤 5/8 通过  失败于 step_06        │   │
│  │  lisi · 设备 Xiaomi Box S                        [详情 ›] │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 🔧 TC-TV-005  直播频道切换                        3分20秒  │   │
│  │  🏷 smoke  live    步骤 7/7 通过（含 1 次 AI 修复）        │   │
│  │  wangwu · 设备 Xiaomi Box S                      [详情 ›] │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  与上次执行对比：新增失败 1 条 / 修复 0 条 / 新增用例 2 条          │  ← 趋势对比
└──────────────────────────────────────────────────────────────────┘
```

### 6.3 用例详情报告（case_report.html）布局

```
┌──────────────────────────────────────────────────────────────────┐
│ ← 返回套件报告   TC-TV-001 首页进入电影频道并验证播放    [导出]     │
│ 作者：zhangsan  优先级：P0  标签：smoke home playback             │
│ 设备：Xiaomi Box S (API 30)  App v2.3.1  耗时：2分10秒           │
├──────────────────────────────────────────────────────────────────┤
│  步骤时间线                                                        │
│                                                                  │
│  ┌ ✅ step_01  从首页导航到电影频道菜单项              320ms ──────┐│
│  │  操作：navigate_to  定位：primary (resource_id)              ││
│  │  [展开] 操作前截图  →  操作后截图                             ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌ ✅ step_02  确认焦点已到达电影频道菜单项             85ms  ──────┐│
│  │  操作：assert_focused  定位：primary                         ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌ 🔧 step_03  按 OK 键进入电影频道                    210ms ──────┐│
│  │  ⚠️ AI 修复介入：UI_ELEMENT_MOVED                            ││
│  │  分析：电影频道菜单项 resource-id 未变，但焦点规则更新后需      ││
│  │       多按一次 DOWN 才能正确聚焦                              ││
│  │  修复方式：阶段1-语义相似度匹配  置信度：0.93                 ││
│  │  建议更新 YAML：在 step_02 后增加 press_key: DPAD_DOWN       ││
│  │  [修复前截图]  [修复后截图]                                   ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌ ❌ step_06  导航到第一个电影内容项并进入            超时 ────────┐│
│  │  失败原因：target 所有 fallback 均未找到元素                  ││
│  │  AI 修复：执行  置信度：0.62（< 0.7，高风险）                 ││
│  │  最终状态：HEAL_FAILED → abort                               ││
│  │  [失败时截图]  [期望参考截图（对比）]                          ││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│  原始日志                                             [展开/折叠]   │
│  设备信息快照                                                      │
└──────────────────────────────────────────────────────────────────┘
```

### 6.4 视觉设计规范

**色彩系统（在 HTML 报告中实现，与 Test Space 主题一致）：**

| 状态 | 颜色 | 说明 |
|------|------|------|
| PASSED | `#22c55e` 绿 | 通过 |
| FAILED | `#ef4444` 红 | 失败 |
| HEALED | `#f97316` 橙 | AI 修复后通过 |
| SKIPPED | `#94a3b8` 灰 | 跳过 |
| RUNNING | `#3b82f6` 蓝 | 执行中 |

**报告 CSS 核心（HTML 内联，不依赖外部）：**

- 背景：`#f0f2f5`（浅灰底），卡片 `white` + `border-radius: 16px` + `box-shadow`
- 顶部栏：毛玻璃效果（`backdrop-filter: blur(20px)`）
- 指标卡片：渐变色背景（绿/红/橙 径向渐变）+ 大号数字
- 步骤时间线：左侧竖线 + 圆点状态指示器 + 卡片展开动画
- 截图对比：左右并排，失败截图右上角红色标记，diff 区域高亮叠加
- 图表：进度条用 CSS 纯实现（无 JS 图表库），饼图用 SVG 实现

**中英文切换实现：**

```html
<!-- 报告中 JS 实现，无外部依赖 -->
<script>
const i18n = {
  zh: { suite_title: "执行报告", passed: "通过", failed: "失败", ... },
  en: { suite_title: "Test Report", passed: "Passed", failed: "Failed", ... }
}
let lang = 'zh'
function toggleLang() {
  lang = lang === 'zh' ? 'en' : 'zh'
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = i18n[lang][el.dataset.i18n]
  })
}
</script>
```

### 6.5 截图对比设计

失败步骤展示期望 vs 实际截图对比，差异区域高亮：

```
期望截图（探索时保存）          实际截图（执行时截取）
┌─────────────────────┐   ┌─────────────────────┐
│                     │   │                     │
│  [菜单项: 电影]     │   │  [菜单项: 影视]      │  ← 文字改了
│   ▶ 焦点在此        │   │                     │  ← 焦点位置不同
│                     │   │   ▶ 焦点在此        │
└─────────────────────┘   └─────────────────────┘
      期望状态                    实际状态
      [差异区域用红色半透明遮罩叠加]
```

差异区域高亮：用 Python `Pillow` 库计算两张截图的像素差（差值图 > 阈值的区域），生成 diff_mask，以红色半透明叠加在实际截图上，base64 内嵌到报告。

### 6.6 报告导出

在 Test Space 内查看报告时，导出按钮触发：

1. **导出 HTML**：报告已是自包含 HTML，直接调用 `plugin-dialog` 选择保存路径，`plugin-fs` 写文件
2. **导出 PDF**：复用现有 Notes Space 的 `html-to-image` + `jsPDF` 方案，对报告 DOM 截图转 PDF
3. **导出 JSON**：导出 `summary.json`（机读摘要，供 CI 消费）


---

## 七、数据库设计

### 7.1 新增表（在现有 `migrateInternal` 中注册）

```sql
-- 用例表（YAML 内容存库，支持增删改查和版本历史）
CREATE TABLE IF NOT EXISTS auto_cases (
  id          TEXT PRIMARY KEY,          -- UUID v4
  name        TEXT NOT NULL,             -- 用例名称
  file_key    TEXT NOT NULL UNIQUE,      -- 文件键名（供导出文件名使用）
  tags        TEXT NOT NULL DEFAULT '[]',-- JSON 数组
  priority    TEXT NOT NULL DEFAULT 'P2',-- P0/P1/P2/P3
  author      TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  yaml_content TEXT NOT NULL,            -- 完整 YAML 文本
  version     TEXT NOT NULL DEFAULT '1.0',
  created_at  TEXT NOT NULL,             -- ISO 8601
  updated_at  TEXT NOT NULL
);

-- 用例版本历史（每次保存一个快照，支持回溯）
CREATE TABLE IF NOT EXISTS auto_case_versions (
  id          TEXT PRIMARY KEY,
  case_id     TEXT NOT NULL REFERENCES auto_cases(id) ON DELETE CASCADE,
  version     TEXT NOT NULL,
  yaml_content TEXT NOT NULL,
  saved_by    TEXT NOT NULL DEFAULT '',
  saved_at    TEXT NOT NULL
);

-- 执行记录（每次运行一条）
CREATE TABLE IF NOT EXISTS auto_run_records (
  id          TEXT PRIMARY KEY,          -- run_id（目录名）
  trigger     TEXT NOT NULL DEFAULT 'manual', -- manual/scheduled/ci
  device_serial TEXT NOT NULL DEFAULT '',
  device_info TEXT NOT NULL DEFAULT '{}',-- JSON（型号/API/App版本等）
  suite_config TEXT NOT NULL DEFAULT '{}',-- JSON（标签筛选/用例列表）
  status      TEXT NOT NULL DEFAULT 'running', -- running/done/aborted
  total       INTEGER NOT NULL DEFAULT 0,
  passed      INTEGER NOT NULL DEFAULT 0,
  failed      INTEGER NOT NULL DEFAULT 0,
  healed      INTEGER NOT NULL DEFAULT 0,
  skipped     INTEGER NOT NULL DEFAULT 0,
  duration_ms INTEGER NOT NULL DEFAULT 0,
  report_path TEXT NOT NULL DEFAULT '',  -- HTML 报告文件路径
  started_at  TEXT NOT NULL,
  ended_at    TEXT
);

-- 步骤执行记录（每步一条，供报告生成和 AI 修复参考）
CREATE TABLE IF NOT EXISTS auto_run_steps (
  id            TEXT PRIMARY KEY,
  run_id        TEXT NOT NULL REFERENCES auto_run_records(id) ON DELETE CASCADE,
  case_id       TEXT NOT NULL,
  step_id       TEXT NOT NULL,           -- 对应 YAML 中的 step id
  step_desc     TEXT NOT NULL DEFAULT '',
  status        TEXT NOT NULL,           -- passed/failed/healed/skipped
  duration_ms   INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  heal_log      TEXT,                    -- JSON（修复过程记录）
  screenshot_before TEXT,               -- 文件路径（相对 app data）
  screenshot_after  TEXT,
  screenshot_ref    TEXT,               -- 参考截图路径（探索时保存）
  locator_used  TEXT,                   -- 实际命中的定位层（primary/fallback1/...）
  created_at    TEXT NOT NULL
);

-- StateGraph 版本存档
CREATE TABLE IF NOT EXISTS auto_state_graphs (
  id          TEXT PRIMARY KEY,
  app_package TEXT NOT NULL,
  app_version TEXT NOT NULL DEFAULT '',
  device_info TEXT NOT NULL DEFAULT '{}',
  graph_json  TEXT NOT NULL,             -- 完整图数据（节点+边）
  node_count  INTEGER NOT NULL DEFAULT 0,
  edge_count  INTEGER NOT NULL DEFAULT 0,
  explore_duration_ms INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL
);
```

### 7.2 数据持久化策略

| 数据类型 | 存储方式 | 说明 |
|---------|---------|------|
| 用例 YAML 内容 | SQLite `auto_cases.yaml_content` | 主存储，实时保存 |
| 用例文件导出 | 本地文件（用户选择路径）| 导出操作触发 |
| 截图文件 | App data 目录（不入库）| 路径存 DB，文件存磁盘 |
| HTML 报告 | App data 目录（不入库）| 路径存 DB，查看时读文件 |
| AI 配置 | 复用 `app_settings` 表 | 已有，无需新增 |
| StateGraph | SQLite `auto_state_graphs.graph_json` | 完整 JSON 存库 |

### 7.3 纳入备份恢复流程

新增表需更新 `database.ts` 中的：
- `AppBackup` 类型定义（新增 `auto_cases` / `auto_run_records` 字段）
- `exportAllData()` 函数
- `importAllData()` 函数
- `validateBackup()` 函数

---

## 八、Test Space UI 集成

### 8.1 新增路由与导航

**路由：** `/auto-space`（命名：`AutoSpacePage`）

**Sidebar 导航项新增**（在 Scripts 和 Case 之间）：
```
Device → Notes → API → Scripts → 【自动化】 → Case → Settings
图标：smart_toy（Material Symbols）
活跃态：glass-active + FILL 1
```

### 8.2 AutoSpacePage 页面布局

```
AutoSpacePage
├── 顶部工具栏
│   ├── 设备状态（复用 DeviceSpace 连接状态，显示当前连接的设备）
│   ├── 运行控制（▶ 运行选中 / ▶▶ 运行全部 / ■ 停止）
│   ├── 标签筛选下拉（smoke / regress / 自定义）
│   └── 右侧：[+ 新建用例] [导入 YAML] [报告历史]
│
├── 左侧面板（240px，可折叠）
│   ├── 用例分组（按 tags 自动分组，折叠/展开）
│   ├── 用例列表（卡片式，状态图标 + 名称 + 优先级徽章）
│   ├── 每条用例右键菜单：编辑 / 复制 / 导出 / 删除
│   └── 底部：[+ 新建用例]
│
└── 右侧主工作区（Tab 切换）
    ├── Tab 1：编辑器
    │   ├── 顶部：用例名（可编辑）+ 标签 + 优先级 + 保存状态
    │   ├── Monaco Editor（YAML 高亮 + 自动补全 Schema）
    │   └── 底部工具栏：[验证 YAML] [导出文件] [查看版本历史]
    │
    ├── Tab 2：执行控制台
    │   ├── 顶部：设备选择 + 运行按钮 + 进度（step 3/9）
    │   ├── 实时步骤日志（每步一行，状态图标 + desc + 耗时）
    │   │   ✅ [320ms] step_01 从首页导航到电影频道菜单项
    │   │   🔧 [210ms] step_03 AI修复介入 → 成功
    │   │   ❌ [超时]  step_06 失败：target 未找到
    │   ├── 实时截图预览（右侧小窗，显示最新步骤截图）
    │   └── 执行完成后：[查看报告] 按钮
    │
    └── Tab 3：报告
        ├── 历史执行列表（时间倒序）
        │   每条：时间 + 设备 + 通过/失败数 + [查看] [导出]
        └── 报告查看区（iframe 嵌入 HTML 报告，或 Vue 动态渲染）
```

### 8.3 YAML 编辑器增强

Monaco Editor 配置（复用 Script Space 的 Monaco 接入方式）：

```typescript
// YAML 语言 + 自动补全（关键字提示）
const yamlCompletionProvider = {
  provideCompletionItems: (model, position) => {
    // 根据光标上下文提示：
    // - action 类型列表
    // - by 类型列表（resource_id / content_desc / text_contains 等）
    // - on_failure 可选值
    // - KEYCODE 列表（DPAD_UP/DOWN/LEFT/RIGHT/CENTER/BACK/HOME 等）
  }
}
```

保存逻辑（与 Script Space 的自动保存一致）：
- 编辑后 1.5s 防抖，自动写入 `auto_cases.yaml_content`
- 同时保存一个版本快照到 `auto_case_versions`（每30s或手动保存触发）
- 保存状态提示：绿点"已保存" / 灰脉冲"保存中..."

### 8.4 执行控制台与 Rust 层通信

Python 引擎以子进程方式启动，通过 stdout 管道向 Rust 层实时输出结构化日志：

```
# Python 输出格式（JSON Lines，每行一个事件）
{"type": "step_start", "step_id": "step_01", "desc": "导航到电影频道"}
{"type": "step_done", "step_id": "step_01", "status": "passed", "ms": 320}
{"type": "step_heal", "step_id": "step_03", "phase": 1, "method": "semantic_match"}
{"type": "step_fail", "step_id": "step_06", "error": "target not found"}
{"type": "screenshot", "step_id": "step_01", "path": "screenshots/..."}
{"type": "suite_done", "passed": 9, "failed": 2, "healed": 1, "ms": 272000}
```

Rust `auto_runner.rs` 解析每行 JSON，通过 Tauri Event 推送到前端：
```
tauri::Emitter::emit(&app, "auto:step_event", &event_payload)
```

前端用 `listen("auto:step_event", ...)` 接收并实时更新控制台 UI。

---

## 九、团队协作设计

### 9.1 用例管理工作流

```
新建用例：
  1. 点击「+ 新建用例」
  2. 输入用例名、选标签、选优先级
  3. 生成 YAML 骨架（包含 meta/setup/一个示例步骤/teardown）
  4. 在 Monaco 编辑器中补充步骤
  5. 自动实时保存到 SQLite

导入用例（从文件）：
  1. 点击「导入 YAML」
  2. 选择本地 .yaml 或 .yml 文件（支持批量选择）
  3. 解析 meta.id，如 ID 已存在则弹窗：覆盖 / 新建副本
  4. 导入成功后自动保存到 SQLite

导出用例（到文件）：
  1. 右键用例 → 「导出 YAML」
  2. 选择保存路径
  3. 写出原始 YAML 文本（不做任何转换，保持可读性）
  4. 支持批量导出（全部导出 → ZIP）

版本历史查看：
  1. 编辑器底部点击「查看版本历史」
  2. 弹窗列出该用例的历史版本（时间 + 内容摘要）
  3. 点击某版本 → 预览 YAML diff（新增行绿色/删除行红色）
  4. 「恢复到此版本」按钮 → 覆盖当前内容（保存前二次确认）
```

### 9.2 多人协作规范

```
用例 ID 命名规范：
  TC-{模块缩写}-{3位序号}
  示例：TC-HOME-001, TC-PLAY-003, TC-SEARCH-012

文件键名规范（导出文件名）：
  {id}_{name_pinyin_or_english}.yaml
  示例：TC-HOME-001_home_to_movie.yaml

tags 使用规范：
  系统标签：smoke（冒烟）、regress（回归）、p0_daily（每日P0）
  模块标签：home、playback、search、live、settings 等
  禁止用中文 tag（影响文件名和 CI 脚本兼容性）

author 字段：
  使用团队统一的用户名，与 Git commit 保持一致
```

### 9.3 CI/CD 集成

Python 引擎支持命令行调用，可集成到 CI 流水线：

```bash
# 按 tag 运行冒烟用例
python tv_engine/main.py run --tags smoke --device 192.168.1.100:5555 --report-dir ./reports

# 探索新版本 App 并与上次对比
python tv_engine/main.py explore --package com.example.tv --device 192.168.1.100:5555
python tv_engine/main.py diff --package com.example.tv --since latest

# 退出码：0=全部通过，1=有失败，2=执行异常
```

CI 读取 `summary.json`：
```json
{
  "run_id": "run_20260708_143022",
  "status": "partial_fail",
  "total": 12, "passed": 9, "failed": 2, "healed": 1,
  "failed_cases": ["TC-TV-003", "TC-TV-007"],
  "report_url": "reports/run_20260708_143022/index.html"
}
```

---

## 十、实施路线图

### Phase 1（2周）— Python 引擎可用

**目标：** 命令行能跑通一个完整用例

- [ ] `tv_engine/core/device.py` — uiautomator2 封装，DPAD 操作，UI Tree 解析
- [ ] `tv_engine/core/state.py` — TVState + 指纹计算 + 视觉哈希
- [ ] `tv_engine/core/locator.py` — 多层 fallback 定位解析器
- [ ] `tv_engine/core/navigator.py` — Level 2 空间贪心导航（先跳过 Level 1/3）
- [ ] `tv_engine/core/runner.py` — YAML 解析 + 步骤执行框架
- [ ] 支持 action：`launch_app`, `navigate_to`, `press_key`, `wait_for`, `assert_focused`
- [ ] `tv_engine/core/reporter.py` — 基础 HTML 报告（步骤列表 + 截图）
- [ ] 命令行：`python main.py run cases/TC-001.yaml`

**验收标准：** 能完整跑通 3 条真实 TV 用例，报告可正常生成和打开

---

### Phase 2（1周）— Test Space 集成

**目标：** 在 Test Space 内编辑用例、触发执行、看控制台输出

- [ ] SQLite 新增 4 张表（用例/版本历史/执行记录/步骤记录）
- [ ] `database.ts` 更新迁移脚本和备份/恢复
- [ ] 新增 `/auto-space` 路由，注册 `AutoSpacePage` 组件
- [ ] Sidebar 新增「自动化」导航项
- [ ] 用例列表 + Monaco YAML 编辑器（含自动保存）
- [ ] Rust `auto_runner.rs` — Python 进程管理 + 管道 JSON 解析 + Tauri Event
- [ ] 前端控制台面板（实时步骤日志）
- [ ] 导入/导出 YAML 文件功能
- [ ] 更新 `DEVELOPMENT.md`

---

### Phase 3（1周）— 完整报告系统

**目标：** 报告美观、可分享、双语、可导出

- [ ] 套件报告（index.html）完整实现（指标卡片 + 用例列表 + 趋势对比）
- [ ] 用例详情报告（完整步骤时间线 + 截图 + AI 修复记录）
- [ ] 截图对比 diff 叠加（Pillow 生成 diff_mask）
- [ ] 中英文切换（JS 内联 i18n）
- [ ] 报告在 Test Space 内嵌 iframe 查看
- [ ] 报告导出（HTML / PDF / JSON）
- [ ] 历史报告列表（按时间倒序）

---

### Phase 4（1周）— AI 自修复

**目标：** 接入项目已有 AI 配置，实现 7 大场景修复

- [ ] `tv_engine/core/healer.py` — 完整修复流程（3阶段）
- [ ] 阶段 1：多属性指纹匹配 + 语义相似度 + 弹窗自动关闭
- [ ] 阶段 2：LLM 视觉修复（调用已配置 AI Provider）
- [ ] 阶段 3：局部重新探索
- [ ] 修复置信度阈值管控
- [ ] 修复日志写入 `auto_run_steps.heal_log`
- [ ] 报告中修复链路展示（橙色时间线节点）
- [ ] Settings 页新增：自动化 AI 修复开关 + 置信度阈值配置

---

### Phase 5（按需）— 探索引擎 + 进阶功能

- [ ] `tv_engine/core/explorer.py` — BFS 焦点状态图探索
- [ ] Level 1 图谱规划导航（依赖 StateGraph）
- [ ] Level 3 全遍历搜索导航
- [ ] StateGraph 版本 diff 报告（UI 变更影响分析）
- [ ] 从 StateGraph 自动生成用例骨架
- [ ] 定时探索任务（定期发现 UI 变更）

---

## 附录：目录结构（最终状态）

```
d:\code\test-Space\
├── AUTOMATION_DESIGN.md          ← 本文档
├── tv_engine/                    ← Python 引擎（独立目录，与 test-space 同级）
│   ├── requirements.txt
│   ├── main.py
│   ├── core/
│   │   ├── device.py
│   │   ├── state.py
│   │   ├── locator.py
│   │   ├── navigator.py
│   │   ├── explorer.py
│   │   ├── runner.py
│   │   ├── healer.py
│   │   └── reporter.py
│   ├── actions/
│   ├── assets/ref/
│   ├── cases/
│   ├── graphs/
│   └── reports/
│
└── test-space/                   ← 现有 Tauri 应用
    └── src/
        ├── views/
        │   └── auto-space/
        │       └── AutoSpacePage.vue    ← 新增
        └── services/
            └── autoRunService.ts        ← 新增（前端与引擎通信服务）
    └── src-tauri/src/
        └── auto_runner.rs               ← 新增（Python 进程管理）
```
