# Test Space 编码规范

> 本文档为 Aider / AI 编程助手提供项目特定的编码规范指导。
> 所有代码生成和修改必须遵循以下规则。

## 一、技术栈与架构

| 层级 | 技术选型 | 版本 |
|------|----------|------|
| 桌面框架 | Tauri | 2.x |
| 前端框架 | Vue | 3.5+ (Composition API + `<script setup>`) |
| 构建工具 | Vite | 6.x |
| 类型系统 | TypeScript | ~5.7 |
| 状态管理 | Pinia | 2.x |
| 路由 | Vue Router | 4.x |
| 样式 | TailwindCSS | 3.4+ |
| 原生层 | Rust | 1.77+ |
| 数据库 | SQLite (Tauri plugin-sql) | 2.x |

## 二、Vue 组件规范

### 2.1 组件结构

```vue
<script setup lang="ts">
// 1. 类型导入
// 2. Vue / 第三方库导入
// 3. 项目内部导入（别名 @/）
// 4. Props 定义（带默认值和类型）
// 5. Emits 定义
// 6. 组合式函数调用
// 7. 响应式状态
// 8. 计算属性
// 9. 方法
// 10. 生命周期钩子
// 11. 监听器
</script>

<template>
  <!-- 模板内容 -->
</template>

<style scoped>
/* 仅当需要深度定制时使用，优先用 Tailwind */
</style>
```

### 2.2 命名规范

- 组件文件名：**PascalCase**（如 `DeviceSpacePage.vue`）
- 组合式函数：**useXxx**（如 `useAdb.ts`）
- Store：**useXxxStore**（如 `usePerfMonitorStore.ts`）
- Props：camelCase，模板中使用 kebab-case 绑定
- 事件名：camelCase（如 `update:modelValue`）
- 路由 name：PascalCase 匹配组件名

### 2.3 Props 定义

必须使用 `withDefaults` 或对象形式提供完整类型和默认值：

```typescript
interface Props {
  deviceId: string
  autoConnect?: boolean
  maxRetries?: number
}

const props = withDefaults(defineProps<Props>(), {
  autoConnect: false,
  maxRetries: 3
})
```

### 2.4 Emits 定义

```typescript
const emit = defineEmits<{
  connect: [deviceId: string]
  error: [message: string, code: number]
  'update:modelValue': [value: boolean]
}>()
```

### 2.5 Keep-Alive 兼容

被 `keep-alive` 缓存的页面组件必须声明 `name`：

```vue
<script setup lang="ts">
defineOptions({ name: 'DeviceSpacePage' })
</script>
```

## 三、TypeScript 规范

### 3.1 类型定义

- 所有函数参数和返回值必须标注类型
- 优先使用 `interface` 定义对象类型
- 联合类型使用 `type`
- 枚举使用常量对象替代 `enum`

```typescript
// Good
interface DeviceInfo {
  serial: string
  model: string
  status: 'online' | 'offline' | 'unauthorized'
}

type LogLevel = 'verbose' | 'debug' | 'info' | 'warn' | 'error'

// 替代 enum
const LogLevel = {
  VERBOSE: 'verbose',
  DEBUG: 'debug',
  INFO: 'info',
  WARN: 'warn',
  ERROR: 'error'
} as const
```

### 3.2 错误处理

- 异步函数必须使用 `try/catch`
- 服务层函数返回 `{ data: T } | { error: string }`，不跨层抛异常
- 禁止静默吞掉错误

```typescript
async function fetchDevices(): Promise<{ data: DeviceInfo[] } | { error: string }> {
  try {
    const devices = await invoke<DeviceInfo[]>('list_devices')
    return { data: devices }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error('Failed to fetch devices:', message)
    return { error: message }
  }
}
```

### 3.3 空值检查

- 使用可选链 `?.` 和空值合并 `??`
- 数组操作前检查长度
- 禁止非空断言 `!` 除非绝对确定

## 四、样式规范（TailwindCSS + 玻璃态设计系统）

### 4.1 核心原则

- **禁止**自创样式模式，必须复用现有的液态玻璃设计系统
- **禁止**使用 `bg-primary-container`、`bg-secondary-fixed`、`text-primary` 等旧样式
- 所有交互控件必须使用以下 CSS 类

### 4.2 玻璃态 CSS 类

| 类名 | 用途 | 使用场景 |
|------|------|----------|
| `.glass-panel` | 背景面板 | 卡片容器、弹窗主体 |
| `.glass-card` | 可交互卡片 | 列表项、功能卡片 |
| `.glass-card-active` | 选中状态卡片 | 选中项、活跃态 |
| `.glass-button` | 按钮 | 所有按钮元素 |
| `.glass-hover` | 通用悬停效果 | 导航项、标签页、卡片 |
| `.glass-active` | 选中/激活态 | 当前路由、选中标签 |
| `.glass-input` | 输入框 | 表单输入 |
| `.recessed-input` | 凹陷输入框 | 特殊输入场景 |
| `.status-pulse` | 状态脉冲 | 连接状态、运行指示 |

### 4.3 弹窗/对话框规范（强制）

所有 Teleport 弹窗必须使用以下结构：

```html
<Teleport to="body">
  <Transition name="fade">
    <div v-if="show" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="close">
      <!-- 背景遮罩层：必须是 bg-black/30 backdrop-blur-sm -->
      <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
      <!-- 弹窗主体 -->
      <div class="glass-panel rounded-[2rem] p-6 w-full max-w-md relative z-10 bg-white/60 max-h-[80vh] flex flex-col">
        <!-- 标题栏 -->
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
            <span class="material-symbols-outlined text-[16px]">icon_name</span>
            标题
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

**禁止**：
- 使用 `bg-black/10`、`bg-black/20`、`bg-black/50` 等其他遮罩透明度
- 自创弹窗样式
- 不使用 `glass-panel rounded-[2rem] bg-white/60`

### 4.4 布局规范

- 页面根容器使用 `flex flex-1 min-h-0 overflow-hidden`（不是 `h-full`）
- 内容区滚动由 `overflow-y-auto` 控制
- 防止水平溢出：`overflow-x-hidden`
- Flex 子项使用 `min-w-0` 和 `min-h-0` 防止撑破布局

## 五、状态管理（Pinia）

### 5.1 Store 结构

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useXxxStore = defineStore('xxx', () => {
  // State
  const items = ref<Item[]>([])
  const loading = ref(false)

  // Getters
  const itemCount = computed(() => items.value.length)
  const activeItems = computed(() => items.value.filter(i => i.active))

  // Actions
  async function loadItems() {
    loading.value = true
    try {
      items.value = await fetchItems()
    } finally {
      loading.value = false
    }
  }

  return {
    items,
    loading,
    itemCount,
    activeItems,
    loadItems
  }
})
```

### 5.2 持久化规则

- 跨会话持久化数据 → SQLite (`app_settings` 表或专用业务表)
- 会话级状态 → `localStorage`
- 优先使用 `app_settings` 键值对模式 (`getSetting`/`setSetting`)
- 结构化数据需：
  1. 添加专用表
  2. 在 `migrateInternal` 注册 `CREATE TABLE IF NOT EXISTS`
  3. 更新 `AppBackup`/`exportAllData`/`importAllData`/`validateBackup`

## 六、Tauri / Rust 命令规范

### 6.1 命令命名

- 使用 `snake_case`
- 前缀标识模块：`adb_xxx`、`serial_xxx`、`script_xxx`

### 6.2 错误处理

```rust
#[tauri::command]
pub async fn adb_shell(serial: String, command: String) -> Result<String, String> {
    match execute_adb_shell(&serial, &command).await {
        Ok(output) => Ok(output),
        Err(e) => {
            log::error!("ADB shell failed: {}", e);
            Err(format!("ADB shell 执行失败: {}", e))
        }
    }
}
```

### 6.3 异步命令

- IO 密集型操作（文件读写、网络请求、ADB 命令）使用 `async fn`
- 长耗时操作使用 `tokio::spawn` 避免阻塞 UI
- 状态变更通过 Channel 或 Event 通知前端

## 七、数据库操作规范

### 7.1 SQLite 最佳实践

- 初始化设置：`PRAGMA journal_mode = WAL`、`PRAGMA busy_timeout = 30000`
- 大数据量操作间插入 `yieldToMain()`（`setTimeout(0)`）避免 UI 冻结
- 连接池环境下**不使用事务**（`@tauri-apps/plugin-sql` 不保证同一连接）
- 每条操作独立自动提交
- 所有 `INSERT` 显式指定列名（跳过自增 `id`）

### 7.2 数据删除

- 大数据量删除插入 `yieldToMain()` 防卡顿
- 乐观 UI：先更新界面，再 fire-and-forget 数据库操作

## 八、性能优化规范

### 8.1 渲染优化

- 图表使用 `bucketingDownsample` 降采样（最多 600 点）
- 长列表使用虚拟滚动或分页
- `keep-alive` 缓存频繁切换的页面
- 定时器在 `onUnmounted` 中清理

### 8.2 内存管理

- 组件卸载时清理事件监听器和定时器
- 大文件操作使用流式处理
- 避免内存泄漏：取消未完成的异步请求

## 九、Git 提交规范

### 9.1 提交信息格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

**type 类型**：
- `feat`: 新功能
- `fix`: 修复
- `perf`: 性能优化
- `refactor`: 重构
- `style`: 样式调整
- `docs`: 文档更新
- `test`: 测试相关
- `chore`: 构建/工具

**scope 范围**：`device` | `notes` | `script` | `api` | `settings` | `perf` | `ui` | `rust` | `db`

### 9.2 示例

```
feat(device): 添加 APK 批量安装功能

- 支持多选 APK 文件
- 显示安装进度和结果
- 失败时提供重试机制

fix(db): 修复大数据量导出时 UI 冻结

perf(perf-monitor): 优化图表降采样算法
```

## 十、开发工作流检查清单

修改代码前确认：

- [ ] 评估影响范围，确保不破坏相邻模块
- [ ] 优先增量调整，避免不必要的重构
- [ ] 修改公共模块时验证所有调用方
- [ ] 删除/重命名前全局搜索确认无引用

修改代码后确认：

- [ ] 运行 `npm run build` 通过类型检查
- [ ] UI 元素使用正确的 glass 类
- [ ] 弹窗符合 Teleport 规范
- [ ] 数据持久化符合 SQLite / localStorage 规则
- [ ] 对修改功能做人工冒烟验证
- [ ] 更新 DEVELOPMENT.md 相关文档

## 十一、禁止事项

1. **禁止使用 `h-full` 作为页面根容器高度** — 改用 `flex flex-1 min-h-0`
2. **禁止自创弹窗样式** — 必须使用统一的 Teleport + glass-panel 规范
3. **禁止在 glass-panel 内使用 glass-panel** — 避免嵌套 backdrop-filter
4. **禁止跨层抛异常** — 服务层返回 `{error}` 对象
5. **禁止静默吞错误** — 所有错误必须日志记录或通知用户
6. **禁止修改后不复查调用方** — 公共 API 变更需全局验证
7. **禁止不使用 `yieldToMain()` 的大数据量操作** — 防止 UI 冻结
8. **禁止在 SQLite 连接池中使用事务** — 使用独立自动提交
