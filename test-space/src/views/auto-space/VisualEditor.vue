<template>
  <div class="flex-1 w-full flex flex-col overflow-y-auto custom-scrollbar px-4 py-3 gap-3">
    <!-- Meta Section -->
    <div class="glass-panel rounded-lg p-3 bg-white/30">
      <div class="text-[12px] font-semibold text-on-surface-variant/60 mb-2 flex items-center gap-1.5">
        <span class="material-symbols-outlined text-[14px]">info</span>测试用例信息
      </div>
      <div class="grid grid-cols-4 gap-2">
        <div>
          <label class="text-[11px] text-on-surface-variant/50 block mb-1">用例名称</label>
          <input :value="name" @input="e => updateMeta('name', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2.5 py-1.5 text-[12px] select-text focus:outline-none focus:border-white/40" placeholder="用例名称" />
        </div>
        <div>
          <label class="text-[11px] text-on-surface-variant/50 block mb-1">模块</label>
          <input :value="module" @input="e => updateMeta('module', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2.5 py-1.5 text-[12px] select-text focus:outline-none focus:border-white/40" placeholder="模块名" />
        </div>
        <div>
          <label class="text-[11px] text-on-surface-variant/50 block mb-1">标签</label>
          <input :value="tags" @input="e => updateMeta('tags', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2.5 py-1.5 text-[12px] select-text focus:outline-none focus:border-white/40" placeholder="smoke, home, playback" />
        </div>
        <div>
          <label class="text-[11px] text-on-surface-variant/50 block mb-1">优先级</label>
          <VSelect :model-value="priority" @update:model-value="e => updateMeta('priority', e)" :options="[{value:'P0',label:'P0 最高'},{value:'P1',label:'P1 高'},{value:'P2',label:'P2 普通'},{value:'P3',label:'P3 低'}]" placeholder="优先级" />
        </div>
      </div>
    </div>

    <!-- Steps Section -->
    <div class="glass-panel rounded-lg p-3 bg-white/30">
      <div class="flex items-center justify-between mb-2">
        <div class="text-[12px] font-semibold text-on-surface-variant/60 flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[14px]">format_list_bulleted</span>测试步骤 (steps)
        </div>
        <button class="glass-button px-2 py-1 rounded text-[10px] flex items-center gap-1 select-none" @click="addStep">
          <span class="material-symbols-outlined text-[12px]">add</span>添加步骤
        </button>
      </div>
      <div v-if="steps.length === 0" class="text-[11px] text-on-surface-variant/30 text-center py-3">暂无测试步骤</div>
      <div v-for="(step, idx) in steps" :key="step._key" class="mb-1.5 last:mb-0">
        <div class="rounded-lg bg-white/20 border border-white/10 overflow-hidden">
          <div class="px-2.5 py-1.5 space-y-1">
            <div class="flex items-start gap-1.5">
              <div class="flex-1 grid grid-cols-4 gap-1.5">
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">动作类型</label>
                  <VSelect :model-value="step.action" @update:model-value="e => updateStep(idx, 'action', e)" :options="[{value:'navigate_to',label:'导航点击'},{value:'input_text',label:'输入文本'},{value:'swipe',label:'滑动'},{value:'press_key',label:'按键'},{value:'wait_for',label:'等待条件'},{value:'screenshot',label:'截图'},{value:'assert_element',label:'断言元素'},{value:'assert_visual',label:'图片对比'},{value:'assert_shell',label:'Shell断言'},{value:'set_variable',label:'设置变量'},{value:'launch_app',label:'启动应用'}]" placeholder="动作类型" />
                </div>
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">定位方式</label>
                  <VSelect :model-value="step.targetBy" @update:model-value="e => updateStep(idx, 'targetBy', e)" :options="[{value:'',label:'无'},{value:'resource_id',label:'resource_id (资源ID)'},{value:'content_desc',label:'content_desc (内容描述)'},{value:'text',label:'text (文本)'},{value:'text_contains',label:'text_contains (文本包含)'},{value:'visual_match',label:'visual_match (视觉匹配)'},{value:'index',label:'index (索引)'},{value:'class_and_index',label:'class_and_index (类名+索引)'}]" placeholder="选择定位方式" />
                </div>
                <div class="col-span-2">
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">定位值</label>
                  <input :value="step.targetValue" @input="e => updateStep(idx, 'targetValue', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] font-mono select-text focus:outline-none focus:border-white/40" placeholder="元素定位值" />
                </div>
              </div>
              <button class="mt-4 p-1 rounded hover:bg-red-500/20 text-red-400/60 hover:text-red-400" @click="removeStep(idx)">
                <span class="material-symbols-outlined text-[14px]">close</span>
              </button>
            </div>
            <div v-if="step.action === 'navigate_to'">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">最大导航步数</label>
                <input :value="step.maxSteps" type="number" @input="e => updateStep(idx, 'maxSteps', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="25" />
              </div>
            </div>
            <div v-if="step.action === 'input_text'" class="space-y-1.5">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">输入文本</label>
                <input :value="step.text" @input="e => updateStep(idx, 'text', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="要输入的文本" />
              </div>
              <label class="flex items-center gap-1.5 cursor-pointer">
                <input type="checkbox" :checked="step.clearFirst === 'true'" @change="e => updateStep(idx, 'clearFirst', (e.target as HTMLInputElement).checked ? 'true' : 'false')" class="w-3 h-3 accent-purple-500" />
                <span class="text-[10px] text-on-surface-variant/40">先清空再输入</span>
              </label>
            </div>
            <div v-if="step.action === 'swipe'" class="space-y-1.5">
              <div class="grid grid-cols-2 gap-1.5">
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">方向</label>
                  <VSelect :model-value="step.direction" @update:model-value="e => updateStep(idx, 'direction', e)" :options="[{value:'',label:'坐标'},{value:'UP',label:'上滑'},{value:'DOWN',label:'下滑'},{value:'LEFT',label:'左滑'},{value:'RIGHT',label:'右滑'}]" placeholder="方向" />
                </div>
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">步数</label>
                  <input :value="step.steps" type="number" @input="e => updateStep(idx, 'steps', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="10" />
                </div>
              </div>
              <div class="grid grid-cols-4 gap-1.5">
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">起始X</label>
                  <input :value="step.start_x" type="number" @input="e => updateStep(idx, 'start_x', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" />
                </div>
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">起始Y</label>
                  <input :value="step.start_y" type="number" @input="e => updateStep(idx, 'start_y', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" />
                </div>
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">结束X</label>
                  <input :value="step.end_x" type="number" @input="e => updateStep(idx, 'end_x', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" />
                </div>
                <div>
                  <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">结束Y</label>
                  <input :value="step.end_y" type="number" @input="e => updateStep(idx, 'end_y', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" />
                </div>
              </div>
            </div>
            <div v-if="step.action === 'press_key'" class="grid grid-cols-1">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">按键</label>
                <VSelect :model-value="step.key" @update:model-value="e => updateStep(idx, 'key', e)" :options="KEY_OPTIONS" placeholder="按键" />
              </div>
            </div>
            <div v-if="step.action === 'wait_for'" class="grid grid-cols-1">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">等待超时 (毫秒)</label>
                <input :value="step.duration" type="number" @input="e => updateStep(idx, 'duration', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" />
              </div>
            </div>
            <div v-if="step.action === 'set_variable'" class="grid grid-cols-2 gap-1.5">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">变量名</label>
                <input :value="step.name" @input="e => updateStep(idx, 'name', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="变量名" />
              </div>
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">变量值</label>
                <input :value="step.value" @input="e => updateStep(idx, 'value', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="变量值" />
              </div>
            </div>
            <div v-if="step.action === 'launch_app'" class="grid grid-cols-3 gap-1.5">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">包名</label>
                <input :value="step.package" @input="e => updateStep(idx, 'package', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="com.example" />
              </div>
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">启动页</label>
                <input :value="step.wait_activity" @input="e => updateStep(idx, 'wait_activity', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder=".MainActivity" />
              </div>
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">超时 (秒)</label>
                <input :value="step.timeout" type="number" @input="e => updateStep(idx, 'timeout', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" />
              </div>
            </div>
            <div v-if="step.action === 'assert_shell'" class="grid grid-cols-1">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">Shell 命令</label>
                <input :value="step.command" @input="e => updateStep(idx, 'command', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="input keyevent HOME" />
              </div>
            </div>
            <div class="grid grid-cols-2 gap-1.5">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">失败处理</label>
                <VSelect :model-value="step.onFailure" @update:model-value="e => updateStep(idx, 'onFailure', e)" :options="[{value:'ai_heal',label:'AI 自动修复'},{value:'skip',label:'跳过'},{value:'abort',label:'终止'},{value:'retry',label:'重试'}]" placeholder="失败处理" />
              </div>
              <div v-if="step.action === 'screenshot'">
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">截图路径</label>
                <input :value="step.path" @input="e => updateStep(idx, 'path', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="screenshot.png" />
              </div>
              <template v-else-if="step.action === 'assert_visual'">
                <div class="flex items-end gap-1.5">
                  <div class="flex-1">
                    <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">参考截图路径</label>
                    <input :value="step.refScreenshot" @input="e => updateStep(idx, 'refScreenshot', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="ref.png" />
                  </div>
                  <button class="glass-button px-2 py-1.5 rounded text-[10px] flex items-center gap-1 select-none whitespace-nowrap" @click="captureScreenshot(idx)" title="从设备截图">
                    <span class="material-symbols-outlined text-[12px]">photo_camera</span>截图
                  </button>
                </div>
              </template>
            </div>
            <div v-if="step.action === 'assert_visual'" class="grid grid-cols-2 gap-1.5">
              <div>
                <label class="text-[10px] text-on-surface-variant/40 block mb-0.5">相似度阈值</label>
                <input :value="step.similarity" type="number" step="0.05" min="0" max="1" @input="e => updateStep(idx, 'similarity', (e.target as HTMLInputElement).value)" class="w-full bg-white/10 border border-white/20 rounded px-2 py-1 text-[11px] select-text focus:outline-none focus:border-white/40" placeholder="0.9" />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, watch, defineComponent, h, Teleport } from "vue"

const props = defineProps<{
  yaml: string
  name: string
  module: string
  tags: string
  priority: string
  description: string
  screenshotPath: string
}>()

const emit = defineEmits<{
  'update:yaml': [value: string]
  'update:name': [value: string]
  'update:module': [value: string]
  'update:tags': [value: string]
  'update:priority': [value: string]
  'update:description': [value: string]
  'request-screenshot': []
}>()

const KEY_OPTIONS = [
  { value: 'DPAD_UP', label: 'DPAD_UP (↑)' },
  { value: 'DPAD_DOWN', label: 'DPAD_DOWN (↓)' },
  { value: 'DPAD_LEFT', label: 'DPAD_LEFT (←)' },
  { value: 'DPAD_RIGHT', label: 'DPAD_RIGHT (→)' },
  { value: 'DPAD_CENTER', label: 'DPAD_CENTER' },
  { value: 'DPAD_OK', label: 'DPAD_OK' },
  { value: 'ENTER', label: 'ENTER' },
  { value: 'BACK', label: 'BACK' },
  { value: 'HOME', label: 'HOME' },
  { value: 'MENU', label: 'MENU' },
  { value: 'SETTINGS', label: 'SETTINGS' },
  { value: 'POWER', label: 'POWER' },
  { value: 'VOLUME_UP', label: 'VOLUME_UP' },
  { value: 'VOLUME_DOWN', label: 'VOLUME_DOWN' },
  { value: 'MEDIA_PLAY_PAUSE', label: 'MEDIA_PLAY_PAUSE' },
  { value: 'MEDIA_PLAY', label: 'MEDIA_PLAY' },
  { value: 'MEDIA_PAUSE', label: 'MEDIA_PAUSE' },
  { value: 'MEDIA_STOP', label: 'MEDIA_STOP' },
  { value: 'MEDIA_NEXT', label: 'MEDIA_NEXT' },
  { value: 'MEDIA_PREVIOUS', label: 'MEDIA_PREVIOUS' },
  { value: 'MEDIA_REWIND', label: 'MEDIA_REWIND' },
  { value: 'MEDIA_FAST_FORWARD', label: 'MEDIA_FAST_FORWARD' },
  { value: 'MEDIA_RECORD', label: 'MEDIA_RECORD' },
  { value: 'SEARCH', label: 'SEARCH' },
  { value: 'GUIDE', label: 'GUIDE' },
  { value: 'INFO', label: 'INFO' },
  { value: 'LIVE', label: 'LIVE' },
  { value: 'DVR', label: 'DVR' },
  { value: 'CAPTIONS', label: 'CAPTIONS' },
  { value: 'SUBTITLE', label: 'SUBTITLE' },
  { value: 'PAGE_UP', label: 'PAGE_UP' },
  { value: 'PAGE_DOWN', label: 'PAGE_DOWN' },
  { value: 'CHANNEL_UP', label: 'CHANNEL_UP' },
  { value: 'CHANNEL_DOWN', label: 'CHANNEL_DOWN' },
  { value: 'TAB', label: 'TAB' },
  { value: 'SPACE', label: 'SPACE' },
  { value: 'DEL', label: 'DEL' },
  { value: 'MOVE_HOME', label: 'MOVE_HOME' },
  { value: 'MOVE_END', label: 'MOVE_END' },
  { value: 'ZOOM_IN', label: 'ZOOM_IN' },
  { value: 'ZOOM_OUT', label: 'ZOOM_OUT' },
  { value: 'INPUT', label: 'INPUT' },
  { value: 'SLEEP', label: 'SLEEP' },
  { value: 'WAKEUP', label: 'WAKEUP' },
]

const VSelect = defineComponent({
  props: ['modelValue', 'options', 'placeholder'],
  emits: ['update:modelValue'],
  data() {
    return { open: false, pos: { top: 0, left: 0, width: 0 } }
  },
  computed: {
    label() {
      const found = (this.options || []).find((o: any) => String(o.value) === String(this.modelValue))
      return found ? found.label : (this.placeholder || '')
    }
  },
  methods: {
    toggle() {
      if (this.open) { this.open = false; return }
      const el = this.$el as HTMLElement
      if (el) {
        const rect = el.getBoundingClientRect()
        const count = (this.options || []).length
        const estH = Math.min(count * 30 + 8, 192) + 8
        const estW = Math.max(rect.width, 120)
        let top = rect.bottom + 4
        let left = rect.left
        if (top + estH > window.innerHeight - 8) top = Math.max(8, rect.top - estH - 4)
        if (left + estW > window.innerWidth - 8) left = Math.max(8, window.innerWidth - estW - 8)
        this.pos = { top, left, width: rect.width }
      }
      this.open = true
    },
    pick(val: any) { this.$emit('update:modelValue', val); this.open = false },
    close() { this.open = false }
  },
  render() {
    const triggerBtn = h('button', {
      class: `flex items-center gap-1.5 rounded px-2 py-1.5 text-[11px] w-full select-none border border-white/10 hover:border-white/20 transition-colors text-on-surface-variant/80 ${this.open ? 'border-white/30 bg-white/5' : ''}`,
      onClick: this.toggle
    }, [
      h('span', { class: 'truncate flex-1 text-left' }, this.label),
      h('span', { class: `material-symbols-outlined text-[14px] transition-transform flex-shrink-0 ${this.open ? 'rotate-180' : ''}`, style: { fontVariationSettings: "'FILL' 0" } }, 'expand_more')
    ])
    const items = (this.options || []).map((opt: any) =>
      h('button', {
        key: opt.value,
        class: `w-full text-left px-3 py-1.5 text-[11px] hover:bg-black/5 flex items-center gap-2 select-none ${String(this.modelValue) === String(opt.value) ? 'text-on-surface font-semibold' : 'text-on-surface-variant/70'}`,
        onMousedown: (e: MouseEvent) => e.preventDefault(),
        onClick: () => this.pick(opt.value)
      }, [
        h('span', { class: `material-symbols-outlined text-[14px] ${String(this.modelValue) === String(opt.value) ? '' : 'invisible'}`, style: { fontVariationSettings: "'FILL' 1" } }, 'check'),
        h('span', null, opt.label)
      ])
    )
    const dropdown = this.open ? h(Teleport, { to: 'body' }, [
      h('div', { class: 'fixed inset-0 z-50', onClick: this.close }),
      h('div', {
        class: 'fixed z-50 bg-white rounded-lg p-1 max-h-48 overflow-y-auto custom-scrollbar shadow-lg',
        style: { top: this.pos.top + 'px', left: this.pos.left + 'px', width: Math.max(this.pos.width, 120) + 'px' },
        onMouseleave: this.close
      }, items)
    ]) : null
    return h('div', { class: 'relative w-full', onClick: (e: MouseEvent) => e.stopPropagation() }, [
      triggerBtn, dropdown
    ])
  }
})

interface StepField {
  id: string; desc: string; action: string
  targetBy: string; targetValue: string; onFailure: string; text: string
  start_x: string; start_y: string; end_x: string; end_y: string
  key: string; duration: string; path: string
  refScreenshot: string; similarity: string
  name: string; value: string; package: string; wait_activity: string; timeout: string; command: string
  direction: string; steps: string; maxSteps: string; clearFirst: string
  _key: string
}

interface SetupField {
  action: string; package: string; wait_activity: string; timeout: string
  key: string; duration: string; name: string; value: string; path: string; _key: string
}

let keyCounter = 0
let skipNextParse = false
let pendingScreenshotIdx = -1
function genKey() { return `k_${++keyCounter}` }

const name = ref("")
const description = ref("")
const tags = ref("")
const module = ref("")
const priority = ref("P2")
const setupSteps = ref<SetupField[]>([])
const steps = ref<StepField[]>([])
const teardownSteps = ref<SetupField[]>([])

function newSetupField(action = 'launch_app'): SetupField {
  return { action, package: '', wait_activity: '', timeout: '', key: 'HOME', duration: '', name: '', value: '', path: '', _key: genKey() }
}

function newStepField(): StepField {
  return { id: '', desc: '', action: 'navigate_to', targetBy: 'resource_id', targetValue: '', onFailure: 'ai_heal', text: '', start_x: '', start_y: '', end_x: '', end_y: '', key: 'HOME', duration: '', path: '', refScreenshot: '', similarity: '0.9', name: '', value: '', package: '', wait_activity: '', timeout: '', command: '', direction: '', steps: '', maxSteps: '', clearFirst: 'true', _key: genKey() }
}

function newTeardownField(action = 'press_key'): SetupField {
  return { action, package: '', wait_activity: '', timeout: '', key: 'HOME', duration: '', name: '', value: '', path: '', _key: genKey() }
}

function buildYaml() {
  const lines: string[] = []
  lines.push('# Test Space Automation Case v1.0')
  lines.push('meta:')
  lines.push(`  id: "TC-${name.value.replace(/[<>:"/\\|?*\s]/g, '_').toLowerCase() || 'untitled'}"`)
  lines.push(`  name: "${name.value}"`)
  lines.push(`  author: ""`)
  lines.push(`  version: "1.0"`)
  const tagItems = tags.value.split(',').map(t => t.trim()).filter(Boolean)
  if (tagItems.length > 0) {
    lines.push('  tags:')
    for (const t of tagItems) lines.push(`    - "${t}"`)
  } else {
    lines.push('  tags: []')
  }
  lines.push(`  priority: "${priority.value}"`)
  lines.push(`  description: "${description.value}"`)
  lines.push('')
  if (setupSteps.value.length > 0) {
    lines.push('setup:')
    for (const s of setupSteps.value) {
      const a = s.action
      if (a === 'launch_app') {
        lines.push(`  - action: launch_app`)
        if (s.package) lines.push(`    package: "${s.package}"`)
        if (s.wait_activity) lines.push(`    wait_activity: "${s.wait_activity}"`)
        if (s.timeout) lines.push(`    timeout: ${s.timeout}`)
      } else if (a === 'press_key') {
        lines.push(`  - action: press_key`)
        lines.push(`    key: ${s.key}`)
      } else if (a === 'wait_for') {
        lines.push(`  - action: wait_for`)
        if (s.duration) lines.push(`    timeout: ${s.duration}`)
      } else if (a === 'set_variable') {
        lines.push(`  - action: set_variable`)
        if (s.name) lines.push(`    name: "${s.name}"`)
        if (s.value) lines.push(`    value: "${s.value}"`)
      } else {
        lines.push(`  - action: ${a}`)
      }
    }
    lines.push('')
  }
  if (steps.value.length > 0) {
    lines.push('steps:')
    for (const s of steps.value) {
      lines.push(`  - id: "${s.id || 'step_auto'}"`)
      if (s.desc) lines.push(`    desc: "${s.desc}"`)
      lines.push(`    action: ${s.action}`)
      if (['navigate_to', 'input_text', 'assert_element', 'assert_visual'].includes(s.action) && s.targetBy && s.targetValue) {
        lines.push('    target:')
        lines.push('      primary:')
        lines.push(`        by: ${s.targetBy}`)
        lines.push(`        value: "${s.targetValue}"`)
      }
      if (s.action === 'navigate_to' && s.maxSteps) lines.push(`    max_steps: ${s.maxSteps}`)
      if (s.action === 'input_text') {
        if (s.text) lines.push(`    text: "${s.text}"`)
        if (s.clearFirst === 'false') lines.push(`    clear_first: false`)
      }
      if (s.action === 'swipe') {
        if (s.direction) lines.push(`    direction: ${s.direction}`)
        if (s.steps) lines.push(`    steps: ${s.steps}`)
        if (s.start_x) lines.push(`    start_x: ${s.start_x}`)
        if (s.start_y) lines.push(`    start_y: ${s.start_y}`)
        if (s.end_x) lines.push(`    end_x: ${s.end_x}`)
        if (s.end_y) lines.push(`    end_y: ${s.end_y}`)
      }
      if (s.action === 'press_key') lines.push(`    key: ${s.key}`)
      if (s.action === 'wait_for' && s.duration) lines.push(`    timeout: ${s.duration}`)
      if (s.action === 'screenshot' && s.path) lines.push(`    path: "${s.path}"`)
      if (s.action === 'set_variable') {
        if (s.name) lines.push(`    name: "${s.name}"`)
        if (s.value) lines.push(`    value: "${s.value}"`)
      }
      if (s.action === 'launch_app') {
        if (s.package) lines.push(`    package: "${s.package}"`)
        if (s.wait_activity) lines.push(`    wait_activity: "${s.wait_activity}"`)
        if (s.timeout) lines.push(`    timeout: ${s.timeout}`)
      }
      if (s.action === 'assert_shell' && s.command) {
        lines.push(`    command: "${s.command}"`)
      }
      if (s.action === 'assert_visual' && s.refScreenshot) lines.push(`    ref_screenshot: "${s.refScreenshot}"`)
      if (s.action === 'assert_visual' && s.similarity) lines.push(`    similarity: ${s.similarity}`)
      if (s.onFailure) lines.push(`    on_failure: "${s.onFailure}"`)
    }
    lines.push('')
  }
  if (teardownSteps.value.length > 0) {
    lines.push('teardown:')
    for (const s of teardownSteps.value) {
      const a = s.action
      if (a === 'press_key') {
        lines.push(`  - action: press_key`)
        lines.push(`    key: ${s.key}`)
      } else if (a === 'wait_for') {
        lines.push(`  - action: wait_for`)
        if (s.duration) lines.push(`    timeout: ${s.duration}`)
      } else if (a === 'screenshot') {
        lines.push(`  - action: screenshot`)
        if (s.path) lines.push(`    path: "${s.path}"`)
      } else {
        lines.push(`  - action: ${a}`)
      }
    }
    lines.push('')
  }
  return lines.join('\n')
}

function updateMeta(field: string, value: string) {
  if (field === 'name') name.value = value
  else if (field === 'description') description.value = value
  else if (field === 'tags') tags.value = value
  else if (field === 'module') module.value = value
  else if (field === 'priority') priority.value = value
  emit(`update:${field}` as any, value)
  rebuildYaml()
}

function rebuildYaml() {
  skipNextParse = true
  emit('update:yaml', buildYaml())
}

function parseYaml(yaml: string) {
  const lines = yaml.split('\n')
  let section = ''
  let inSteps = false
  let currentStep: any = null
  steps.value = []
  setupSteps.value = []
  teardownSteps.value = []
  let metaTags: string[] = []

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const trim = line.trim()
    if (!trim || trim.startsWith('#')) {
      if (trim.startsWith('#') && !trim.startsWith('# Test')) continue
      continue
    }

    if (trim === 'meta:') { section = 'meta'; continue }
    if (trim === 'setup:') { section = 'setup'; inSteps = false; continue }
    if (trim === 'steps:') { section = 'steps'; inSteps = true; continue }
    if (trim === 'teardown:') { section = 'teardown'; inSteps = false; continue }

    if (section === 'meta') {
      const nameMatch = trim.match(/^name:\s*"([^"]*)"/)
      if (nameMatch) { name.value = nameMatch[1]; continue }
      const descMatch = trim.match(/^description:\s*"([^"]*)"/)
      if (descMatch) { description.value = descMatch[1]; continue }
      const priMatch = trim.match(/^priority:\s*"([^"]+)"/)
      if (priMatch) { priority.value = priMatch[1]; continue }
      const tagItemMatch = trim.match(/^-\s*"([^"]+)"/)
      if (tagItemMatch) { metaTags.push(tagItemMatch[1]); continue }
      continue
    }

    const isListItem = trim.startsWith('- ')
    const keyVal = isListItem ? trim.slice(2) : trim

    if (isListItem && !keyVal.includes(':')) {
      if (keyVal.startsWith('"') && keyVal.endsWith('"')) {
        metaTags.push(keyVal.slice(1, -1))
      }
      continue
    }

    if (section === 'setup' || section === 'teardown') {
      if (trim.startsWith('- action:')) {
        if (currentStep) {
          if (section === 'setup') setupSteps.value.push(currentStep)
          else teardownSteps.value.push(currentStep)
        }
        let act = trim.split('action:')[1].trim()
        if (act === 'wait') act = 'wait_for'
        currentStep = newSetupField(act)
        continue
      }
      if (currentStep) {
        if (trim.startsWith('package:')) currentStep.package = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('wait_activity:')) currentStep.wait_activity = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('timeout:')) {
          currentStep.timeout = trim.split(/:\s*/)[1] || ''
          currentStep.duration = currentStep.timeout
        }
        else if (trim.startsWith('key:')) currentStep.key = trim.split(/:\s*/)[1] || 'HOME'
        else if (trim.startsWith('duration:')) currentStep.duration = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('name:')) currentStep.name = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('value:')) currentStep.value = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
      }
      continue
    }

    if (section === 'steps') {
      if (trim.startsWith('- id:') || trim.startsWith('- action:')) {
        if (currentStep) steps.value.push(currentStep)
        currentStep = newStepField()
        if (trim.startsWith('- id:')) currentStep.id = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('- action:')) {
          let a = trim.split('action:')[1].trim()
          if (a === 'wait') a = 'wait_for'
          if (a === 'click') a = 'navigate_to'
          if (a === 'assert_visible') a = 'assert_element'
          currentStep.action = a
        }
        continue
      }
      if (currentStep) {
        if (trim.startsWith('id:')) currentStep.id = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('desc:')) currentStep.desc = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('action:')) {
          let a = trim.split(/:\s*/)[1]?.trim() || 'navigate_to'
          if (a === 'wait') a = 'wait_for'
          if (a === 'click') a = 'navigate_to'
          if (a === 'assert_visible') a = 'assert_element'
          currentStep.action = a
        }
        else if (trim.startsWith('by:')) currentStep.targetBy = trim.split(/:\s*/)[1]?.trim() || 'resource_id'
        else if (trim.startsWith('value:')) {
          if (currentStep.action === 'set_variable') currentStep.value = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
          else currentStep.targetValue = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        }
        else if (trim.startsWith('text:')) currentStep.text = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('name:')) currentStep.name = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('package:')) currentStep.package = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('wait_activity:')) currentStep.wait_activity = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('timeout:')) {
          const tv = trim.split(/:\s*/)[1] || ''
          currentStep.timeout = tv; currentStep.duration = tv
        }
        else if (trim.startsWith('command:')) currentStep.command = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('direction:')) currentStep.direction = trim.split(/:\s*/)[1]?.trim() || ''
        else if (trim.startsWith('steps:')) currentStep.steps = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('max_steps:')) currentStep.maxSteps = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('clear_first:')) currentStep.clearFirst = trim.split(/:\s*/)[1]?.trim().toLowerCase() || 'true'
        else if (trim.startsWith('start_x:')) currentStep.start_x = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('start_y:')) currentStep.start_y = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('end_x:')) currentStep.end_x = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('end_y:')) currentStep.end_y = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('key:')) currentStep.key = trim.split(/:\s*/)[1] || 'HOME'
        else if (trim.startsWith('duration:')) currentStep.duration = trim.split(/:\s*/)[1] || ''
        else if (trim.startsWith('path:')) currentStep.path = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('ref_screenshot:')) currentStep.refScreenshot = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || ''
        else if (trim.startsWith('similarity:')) currentStep.similarity = trim.split(/:\s*/)[1] || '0.9'
        else if (trim.startsWith('on_failure:')) currentStep.onFailure = trim.split(/:"?\s*/)[1]?.replace(/"/g, '') || 'ai_heal'
      }
    }
  }

  if (currentStep) {
    if (section === 'steps') steps.value.push(currentStep)
    else if (section === 'setup') setupSteps.value.push(currentStep)
    else if (section === 'teardown') teardownSteps.value.push(currentStep)
  }

  tags.value = metaTags.join(', ')
}

watch(() => props.yaml, (val) => {
  if (skipNextParse) { skipNextParse = false; return }
  if (val) parseYaml(val)
}, { immediate: true })

watch(() => props.screenshotPath, (val) => {
  if (val && pendingScreenshotIdx >= 0 && pendingScreenshotIdx < steps.value.length) {
    steps.value[pendingScreenshotIdx].refScreenshot = val
    pendingScreenshotIdx = -1
    rebuildYaml()
  }
})

function updateSetupStep(idx: number, field: string, value: string) {
  (setupSteps.value[idx] as any)[field] = value
  rebuildYaml()
}

function removeSetupStep(idx: number) {
  setupSteps.value.splice(idx, 1)
  rebuildYaml()
}

function addSetupStep() {
  setupSteps.value.push(newSetupField())
  rebuildYaml()
}

function moveSetupStep(idx: number, dir: number) {
  const target = idx + dir
  if (target < 0 || target >= setupSteps.value.length) return
  const tmp = setupSteps.value[idx]
  setupSteps.value[idx] = setupSteps.value[target]
  setupSteps.value[target] = tmp
  rebuildYaml()
}

function updateStep(idx: number, field: string, value: string) {
  (steps.value[idx] as any)[field] = value
  rebuildYaml()
}

function removeStep(idx: number) {
  steps.value.splice(idx, 1)
  rebuildYaml()
}

function captureScreenshot(idx: number) {
  pendingScreenshotIdx = idx
  emit('request-screenshot')
}

function addStep() {
  steps.value.push(newStepField())
  rebuildYaml()
}

function moveStep(idx: number, dir: number) {
  const target = idx + dir
  if (target < 0 || target >= steps.value.length) return
  const tmp = steps.value[idx]
  steps.value[idx] = steps.value[target]
  steps.value[target] = tmp
  rebuildYaml()
}

function updateTeardownStep(idx: number, field: string, value: string) {
  (teardownSteps.value[idx] as any)[field] = value
  rebuildYaml()
}

function removeTeardownStep(idx: number) {
  teardownSteps.value.splice(idx, 1)
  rebuildYaml()
}

function addTeardownStep() {
  teardownSteps.value.push(newTeardownField())
  rebuildYaml()
}

function moveTeardownStep(idx: number, dir: number) {
  const target = idx + dir
  if (target < 0 || target >= teardownSteps.value.length) return
  const tmp = teardownSteps.value[idx]
  teardownSteps.value[idx] = teardownSteps.value[target]
  teardownSteps.value[target] = tmp
  rebuildYaml()
}
</script>
