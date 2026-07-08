<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center" @click.self="emit('close')">
      <div class="absolute inset-0 bg-black/30 backdrop-blur-sm"></div>
      <div class="glass-panel rounded-[2rem] p-6 w-full max-w-3xl relative z-10 bg-white/60 flex flex-col max-h-[80vh]">
        <div class="flex justify-between items-center mb-4 shrink-0">
          <h3 class="font-label-md text-label-md text-on-surface font-semibold flex items-center gap-1.5 select-none">
            <span class="material-symbols-outlined text-[16px]">history</span>
            {{ t('auto.viewVersions') }}
          </h3>
          <button class="glass-button p-1 rounded select-none" @click="emit('close')">
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </div>

        <div class="flex flex-col min-h-0 flex-1">
          <div v-if="loading" class="flex items-center justify-center py-12 text-on-surface-variant/40">
            <span class="material-symbols-outlined text-3xl animate-spin">refresh</span>
          </div>

          <div v-else-if="versions.length === 0" class="flex items-center justify-center py-12 text-on-surface-variant/40 text-[13px]">
            {{ t('auto.noVersions') }}
          </div>

          <template v-else>
            <div class="flex gap-4 min-h-0 flex-1">
              <div class="w-56 shrink-0 overflow-y-auto custom-scrollbar space-y-1 pr-1">
                <button
                  v-for="v in versions"
                  :key="v.id"
                  class="w-full text-left px-3 py-2 rounded-xl text-[12px] transition-colors border"
                  :class="selectedVersion?.id === v.id ? 'glass-active font-semibold' : 'glass-hover border-transparent'"
                  @click="selectVersion(v)"
                >
                  <div class="font-medium truncate">{{ v.version }}</div>
                  <div class="text-[11px] text-on-surface-variant/60 mt-0.5">{{ formatDate(v.saved_at) }}</div>
                </button>
              </div>

              <div class="flex-1 flex flex-col min-h-0">
                <div v-if="!selectedVersion" class="flex-1 flex items-center justify-center text-on-surface-variant/40 text-[13px]">
                  {{ t('auto.selectVersion') }}
                </div>

                <template v-else>
                  <div class="flex items-center justify-between mb-2 shrink-0">
                    <span class="text-[12px] text-on-surface-variant/70">
                      {{ t('auto.diffCurrent') }} ← {{ selectedVersion.version }}
                    </span>
                    <button
                      class="glass-button px-3 py-1.5 rounded-full text-[11px] flex items-center gap-1 select-none"
                      @click="emit('restore', selectedVersion.id, selectedVersion.yaml_content)"
                    >
                      <span class="material-symbols-outlined text-[13px]">restore</span>
                      {{ t('auto.restoreVersion') }}
                    </button>
                  </div>

                  <div class="flex-1 overflow-y-auto custom-scrollbar rounded-2xl bg-[#0d0d1a] border border-white/10 font-mono text-[13px] leading-[21px]">
                    <div v-for="(line, idx) in diffLines" :key="idx"
                      class="px-4 whitespace-pre-wrap"
                      :class="line.type === 'added' ? 'bg-green-500/15 text-green-300' : line.type === 'removed' ? 'bg-red-500/15 text-red-300' : 'text-[#e4e5e7]'"
                    >
                      <span class="select-none mr-3 text-on-surface-variant/30 text-[11px]">{{ line.type === 'added' ? '+' : line.type === 'removed' ? '-' : ' ' }}</span>
                      {{ line.text }}
                    </div>
                  </div>
                </template>
              </div>
            </div>
          </template>
        </div>

        <div class="flex justify-end gap-2 pt-4 border-t border-outline-variant/30 mt-4 shrink-0">
          <button class="glass-button px-4 py-2 rounded-lg font-label-md text-label-md select-none" @click="emit('close')">
            {{ t('auto.close') }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import * as db from '@/services/database'
import type { AutoCaseVersion } from '@/types'
import { useI18n } from '@/composables/useI18n'

const props = defineProps<{
  caseId: string
  currentContent: string
}>()

const emit = defineEmits<{
  close: []
  restore: [versionId: string, yamlContent: string]
}>()

const { t } = useI18n()

const loading = ref(true)
const versions = ref<AutoCaseVersion[]>([])
const selectedVersion = ref<AutoCaseVersion | null>(null)

interface DiffLine {
  text: string
  type: 'same' | 'added' | 'removed'
}

const diffLines = computed<DiffLine[]>(() => {
  if (!selectedVersion.value) return []
  return computeDiff(props.currentContent, selectedVersion.value.yaml_content)
})

function computeDiff(oldText: string, newText: string): DiffLine[] {
  const oldLines = oldText.split('\n')
  const newLines = newText.split('\n')
  const result: DiffLine[] = []

  const maxLen = Math.max(oldLines.length, newLines.length)
  for (let i = 0; i < maxLen; i++) {
    if (i < oldLines.length && i < newLines.length) {
      if (oldLines[i] === newLines[i]) {
        result.push({ text: oldLines[i], type: 'same' })
      } else {
        result.push({ text: oldLines[i], type: 'removed' })
        result.push({ text: newLines[i], type: 'added' })
      }
    } else if (i < oldLines.length) {
      result.push({ text: oldLines[i], type: 'removed' })
    } else {
      result.push({ text: newLines[i], type: 'added' })
    }
  }

  return result
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString()
  } catch {
    return iso
  }
}

function selectVersion(v: AutoCaseVersion) {
  selectedVersion.value = v
}

onMounted(async () => {
  try {
    versions.value = await db.loadAutoCaseVersions(props.caseId)
    if (versions.value.length > 0) {
      selectedVersion.value = versions.value[0]
    }
  } catch (e) {
    console.error('[VersionHistory] Failed to load versions:', e)
  } finally {
    loading.value = false
  }
})
</script>
