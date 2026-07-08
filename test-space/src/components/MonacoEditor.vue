<template>
  <div ref="containerRef" class="w-full h-full min-h-0"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps<{
  modelValue: string
  readOnly?: boolean
  language?: string
  theme?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLDivElement>()
let editor: any = null
let monaco: any = null
let changeSubscription: any = null
let debounceTimer: ReturnType<typeof setTimeout> | null = null

async function initMonaco() {
  const monacoMod = await import('monaco-editor')
  monaco = monacoMod.default || monacoMod

  // Define custom dark theme
  monaco.editor.defineTheme('space-dark', {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'key', foreground: '60a5fa' },
      { token: 'string', foreground: '34d399' },
      { token: 'number', foreground: 'fb923c' },
      { token: 'comment', foreground: '6b7280', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'c084fc' },
      { token: 'type', foreground: 'f59e0b' },
      { token: 'tag', foreground: 'ef4444' },
    ],
    colors: {
      'editor.background': '#0d0d1a',
      'editor.foreground': '#e4e5e7',
      'editor.lineHighlightBackground': '#1a1c2e',
      'editor.selectionBackground': '#264f78',
      'editorCursor.foreground': '#ffffff',
      'editorLineNumber.foreground': '#4a5568',
      'editorLineNumber.activeForeground': '#6b7280',
      'editor.inactiveSelectionBackground': '#264f7840',
    }
  })

  // Register YAML completion provider
  monaco.languages.registerCompletionItemProvider('yaml', {
    provideCompletionItems: (model: any, position: any) => {
      const word = model.getWordUntilPosition(position)
      const range = {
        startLineNumber: position.lineNumber,
        endLineNumber: position.lineNumber,
        startColumn: word.startColumn,
        endColumn: word.endColumn,
      }
      const suggestions: any[] = []

      // Determine context from indentation
      const lineContent = model.getLineContent(position.lineNumber)
      const indent = lineContent.search(/\S/)
      const prevLine = position.lineNumber > 1 ? model.getLineContent(position.lineNumber - 1) : ''

      if (indent <= 0 && !lineContent.trim()) {
        suggestions.push(
          { label: 'meta:', kind: monaco.languages.CompletionItemKind.Property, insertText: 'meta:\n  id: "$1"\n  name: "$2"\n  author: ""\n  version: "1.0"\n  tags:\n    - "$3"\n  priority: "P2"\n  description: ""', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, range, detail: 'YAML metadata' },
          { label: 'setup:', kind: monaco.languages.CompletionItemKind.Property, insertText: 'setup:\n  - action: launch_app\n    package: ""\n    wait_activity: ""\n    timeout: 8000', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, range, detail: 'Setup steps' },
          { label: 'steps:', kind: monaco.languages.CompletionItemKind.Property, insertText: 'steps:\n  - id: "step_01"\n    desc: "$1"\n    action: navigate_to\n    target:\n      primary:\n        by: resource_id\n        value: "$2"\n    on_failure: "ai_heal"', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, range, detail: 'Test steps' },
          { label: 'teardown:', kind: monaco.languages.CompletionItemKind.Property, insertText: 'teardown:\n  - action: press_key\n    key: HOME', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, range, detail: 'Teardown steps' },
          { label: 'variables:', kind: monaco.languages.CompletionItemKind.Property, insertText: 'variables:\n  target_package: ""\n  max_nav_steps: 25', insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet, range, detail: 'Variables' },
        )
      }

      if (lineContent.includes('action:')) {
        const actions = ['launch_app', 'navigate_to', 'press_key', 'press_key_sequence', 'wait_for', 'wait_stable', 'wait_then_assert', 'assert_focused', 'assert_visual', 'assert_element', 'assert_app_foreground', 'assert_shell', 'screenshot', 'input_text', 'swipe', 'set_variable']
        actions.forEach(a => suggestions.push({ label: a, kind: monaco.languages.CompletionItemKind.Keyword, insertText: a, range, detail: 'Action' }))
      }
      if (lineContent.includes('by:')) {
        const bys = ['resource_id', 'content_desc', 'text', 'text_contains', 'visual_match', 'index', 'class_and_index']
        bys.forEach(b => suggestions.push({ label: b, kind: monaco.languages.CompletionItemKind.Value, insertText: b, range, detail: 'Locator strategy' }))
      }
      if (lineContent.includes('on_failure:')) {
        const strategies = ['skip', 'abort', 'retry', 'ai_heal']
        strategies.forEach(s => suggestions.push({ label: s, kind: monaco.languages.CompletionItemKind.Value, insertText: s, range, detail: 'Failure strategy' }))
      }
      if (lineContent.includes('key:')) {
        const keys = ['DPAD_UP', 'DPAD_DOWN', 'DPAD_LEFT', 'DPAD_RIGHT', 'DPAD_CENTER', 'BACK', 'HOME', 'MENU', 'DPAD_CENTER', 'VOLUME_UP', 'VOLUME_DOWN']
        keys.forEach(k => suggestions.push({ label: k, kind: monaco.languages.CompletionItemKind.Keyword, insertText: k, range, detail: 'Keycode' }))
      }

      return { suggestions }
    }
  })

  if (!containerRef.value) return
  editor = monaco.editor.create(containerRef.value, {
    value: props.modelValue || '',
    language: props.language || 'yaml',
    theme: 'space-dark',
    readOnly: props.readOnly || false,
    fontSize: 13,
    fontFamily: "'Consolas', 'Monaco', 'Courier New', monospace",
    lineHeight: 21,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    automaticLayout: true,
    tabSize: 2,
    wordWrap: 'on',
    padding: { top: 12, bottom: 48 },
    renderLineHighlight: 'line',
    cursorWidth: 2,
    smoothScrolling: true,
  })

  changeSubscription = editor.onDidChangeModelContent(() => {
    if (debounceTimer) clearTimeout(debounceTimer)
    debounceTimer = setTimeout(() => {
      emit('update:modelValue', editor.getValue())
    }, 300)
  })
}

onMounted(initMonaco)

onUnmounted(() => {
  if (changeSubscription) changeSubscription.dispose()
  if (editor) editor.dispose()
  if (debounceTimer) clearTimeout(debounceTimer)
})

watch(() => props.modelValue, (nv) => {
  if (editor && nv !== editor.getValue()) {
    editor.setValue(nv)
  }
})

watch(() => props.readOnly, (nv) => {
  if (editor) editor.updateOptions({ readOnly: nv })
})
</script>
