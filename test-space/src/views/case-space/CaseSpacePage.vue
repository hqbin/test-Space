<template>
  <div class="flex flex-col h-full select-none">
    <div class="flex items-center gap-3 mb-8 mt-8">
      <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="showNewDialog = true">
        <span class="material-symbols-outlined text-[20px]">add</span>
        {{ t("case.newFile") }}
      </button>
      <span class="w-px h-8 bg-white/30 mx-1"></span>
      <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="goToFieldRules">
        <span class="material-symbols-outlined text-[20px]">fact_check</span>
        {{ t("case.fieldTemplates") }}
      </button>
    </div>

    <div v-if="store.favoriteFiles.length > 0" class="mb-8">
      <h2 class="font-headline-md text-headline-md text-on-surface font-semibold mb-4 flex items-center gap-2 select-none">
        <span class="material-symbols-outlined text-[20px] text-secondary" style="font-variation-settings: 'FILL' 1">star</span>
        {{ t("case.favorites") }}
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div
          v-for="file in store.favoriteFiles"
          :key="file.path"
          class="glass-panel rounded-2xl p-5 cursor-pointer transition-all duration-250 hover:shadow-lg hover:-translate-y-0.5 glass-hover"
          @click="openRecentFile(file)"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-secondary-fixed/30 flex items-center justify-center">
              <span class="material-symbols-outlined text-secondary text-[22px]" style="font-variation-settings: 'FILL' 1">description</span>
            </div>
            <button class="p-1.5 rounded-lg text-on-surface-variant/40 hover:text-secondary transition-colors select-none" @click.stop="store.toggleFavorite(file.path)">
              <span class="material-symbols-outlined text-[18px] text-secondary" style="font-variation-settings: 'FILL' 1">star</span>
            </button>
          </div>
          <h3 class="font-body-lg text-body-lg text-on-surface font-semibold mb-1 line-clamp-1 select-none">{{ file.name }}</h3>
          <div class="flex items-center gap-3 text-caption text-on-surface-variant/70 mt-2">
            <span class="flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">list_alt</span>
              {{ file.caseCount }} {{ t("case.cases") }}
            </span>
            <span>·</span>
            <span>{{ formatDate(file.lastOpened) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="store.recentFilesList.length > 0">
      <h2 class="font-headline-md text-headline-md text-on-surface font-semibold mb-4 flex items-center gap-2 select-none">
        <span class="material-symbols-outlined text-[20px] text-on-surface-variant/70">history</span>
        {{ t("case.recentFiles") }}
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <div
          v-for="file in store.recentFilesList"
          :key="file.path"
          class="glass-panel rounded-2xl p-5 cursor-pointer transition-all duration-250 hover:shadow-lg hover:-translate-y-0.5 glass-hover"
          @click="openRecentFile(file)"
        >
          <div class="flex items-start justify-between mb-3">
            <div class="w-10 h-10 rounded-xl bg-secondary-fixed/30 flex items-center justify-center">
              <span class="material-symbols-outlined text-secondary text-[22px]" style="font-variation-settings: 'FILL' 1">description</span>
            </div>
            <div class="flex gap-1">
              <button class="p-1.5 rounded-lg text-on-surface-variant/40 hover:text-secondary transition-colors select-none" @click.stop="store.toggleFavorite(file.path)">
                <span
                  class="material-symbols-outlined text-[18px]"
                  :class="store.favorites.includes(file.path) ? 'text-secondary' : 'text-on-surface-variant/30'"
                  :style="{ fontVariationSettings: `'FILL' ${store.favorites.includes(file.path) ? 1 : 0}` }"
                >star</span>
              </button>
              <button class="p-1.5 rounded-lg text-on-surface-variant/40 hover:text-error transition-colors select-none" @click.stop="confirmRemoveRecent(file)">
                <span class="material-symbols-outlined text-[18px]">close</span>
              </button>
            </div>
          </div>
          <h3 class="font-body-lg text-body-lg text-on-surface font-semibold mb-1 line-clamp-1 select-none">{{ file.name }}</h3>
          <div class="flex items-center gap-3 text-caption text-on-surface-variant/70 mt-2">
            <span class="flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">list_alt</span>
              {{ file.caseCount }} {{ t("case.cases") }}
            </span>
            <span>·</span>
            <span>{{ formatDate(file.lastOpened) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="store.recentFilesList.length === 0 && store.favoriteFiles.length === 0" class="flex-1 flex items-center justify-center">
      <div class="text-center">
        <span class="material-symbols-outlined text-7xl text-on-surface-variant/20">description</span>
        <p class="font-headline-md text-headline-md text-on-surface-variant mt-6">{{ t("case.noFiles") }}</p>
        <p class="font-body-md text-body-md text-on-surface-variant/60 mt-2 mb-6">{{ t("case.noFilesDesc") }}</p>
        <div class="flex items-center justify-center gap-3">
          <button class="glass-button px-6 py-3 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="showNewDialog = true">
            <span class="material-symbols-outlined text-[20px]">add</span>
            {{ t("case.createNew") }}
          </button>
        </div>
      </div>
    </div>

    <!-- New Case File Dialog -->
    <Teleport to="body">
      <div v-if="showNewDialog" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm" @click="showNewDialog = false"></div>
        <div class="glass-panel rounded-2xl p-8 w-[440px] relative z-10">
          <div class="flex items-center justify-between mb-6">
            <h3 class="font-headline-md text-headline-md text-on-surface font-semibold select-none">{{ t("case.newDialogTitle") }}</h3>
            <button class="glass-button p-1 rounded select-none" @click="showNewDialog = false">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
          <div class="flex flex-col gap-5">
            <div>
              <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-1.5">{{ t("case.fileName") }} <span class="text-error">*</span></label>
              <input                 v-model="newCaseName"
                class="w-full rounded-xl px-4 py-3 text-body-md text-on-surface bg-white/70 border border-white/60 shadow-sm placeholder:text-on-surface-variant/40 focus:outline-none focus:border-secondary/40 focus:ring-2 focus:ring-secondary/10 transition-all select-text"
                :placeholder="t('case.fileNamePlaceholder')"
                @keydown.enter="confirmNew"
              />
            </div>
            <div class="relative" @click.stop>
              <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-1.5">{{ t("case.fieldTemplate") }}</label>
              <div
                class="w-full rounded-full px-5 py-3 text-body-md text-on-surface bg-glass-surface/15 backdrop-blur-[20px] border border-white/40 flex items-center justify-between cursor-pointer transition-all hover:bg-white/25 hover:border-white/60"
                @click="showRuleDropdown = !showRuleDropdown"
              >
                <span>{{ selectedRuleName }}</span>
                <span class="material-symbols-outlined text-[18px] text-on-surface-variant/50 transition-transform duration-200" :class="showRuleDropdown ? 'rotate-180' : ''">expand_more</span>
              </div>
              <Transition
                enter-active-class="transition duration-150 ease-out"
                enter-from-class="opacity-0 -translate-y-1 scale-95"
                enter-to-class="opacity-100 translate-y-0 scale-100"
                leave-active-class="transition duration-100 ease-in"
                leave-from-class="opacity-100 translate-y-0 scale-100"
                leave-to-class="opacity-0 -translate-y-1 scale-95"
              >
                <div v-if="showRuleDropdown" class="absolute z-50 mt-2 w-full glass-panel rounded-2xl py-2 shadow-lg border border-white/50 max-h-60 overflow-auto">
                  <div
                    class="px-4 py-2.5 rounded-xl mx-1.5 my-0.5 cursor-pointer text-body-md transition-all flex items-center gap-2"
                    :class="newCaseRule === 'default' ? 'bg-white/50 text-on-surface font-medium' : 'text-on-surface-variant hover:bg-white/30'"
                    @click="selectRule('default')"
                  >
                    <span v-if="newCaseRule === 'default'" class="material-symbols-outlined text-[16px] text-secondary">check</span>
                    <span v-else class="w-4"></span>
                    {{ t("case.defaultFields") }}
                  </div>
                  <div
                    v-for="set in customRuleSets"
                    :key="set.id"
                    class="px-4 py-2.5 rounded-xl mx-1.5 my-0.5 cursor-pointer text-body-md transition-all flex items-center gap-2"
                    :class="newCaseRule === set.id ? 'bg-white/50 text-on-surface font-medium' : 'text-on-surface-variant hover:bg-white/30'"
                    @click="selectRule(set.id)"
                  >
                    <span v-if="newCaseRule === set.id" class="material-symbols-outlined text-[16px] text-secondary">check</span>
                    <span v-else class="w-4"></span>
                    {{ set.name }}
                  </div>
                </div>
              </Transition>
            </div>
            <div class="flex justify-end gap-3 mt-2">
              <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md select-none" @click="showNewDialog = false">{{ t("case.cancel") }}</button>
              <button
                class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md flex items-center gap-2 transition-all shadow-sm select-none"
                :disabled="!newCaseName.trim()"
                :class="!newCaseName.trim() ? 'opacity-50 cursor-not-allowed' : ''"
                @click="confirmNew"
              >
                <span class="material-symbols-outlined text-[18px]">edit_note</span>
                {{ t("case.startEditing") }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete Recent File Confirmation -->
    <Teleport to="body">
      <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm" @click="showDeleteConfirm = false"></div>
        <div class="glass-panel rounded-2xl p-8 w-[400px] relative z-10">
          <div class="flex items-center justify-between mb-4">
            <h3 class="font-headline-md text-headline-md text-on-surface font-semibold select-none">{{ t("case.deleteTitle") }}</h3>
            <button class="glass-button p-1 rounded select-none" @click="showDeleteConfirm = false">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
          <p class="font-body-md text-body-md text-on-surface-variant mb-6">{{ t("case.deleteDesc") }}</p>
          <div class="flex justify-end gap-3">
            <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md select-none" @click="showDeleteConfirm = false">{{ t("case.deleteCancel") }}</button>
            <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md bg-red-500/20 hover:bg-red-500/30 text-red-400 select-none" @click="confirmDeleteRecent">{{ t("case.deleteConfirm") }}</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCaseFileStore } from '@/stores/caseFileStore'
import { useFilePersistence } from '@/composables/useFilePersistence'
import { useTestCaseStore } from '@/composables/useTestCaseStore'
import { useI18n } from '@/composables/useI18n'
import type { CaseFile } from '@/types'

const router = useRouter()
const store = useCaseFileStore()
const { readFile, pickOpenPath } = useFilePersistence()
const { fieldRuleSets } = useTestCaseStore()
const { t } = useI18n()

onMounted(() => {
  store.initStore()
})

const showNewDialog = ref(false)
const showRuleDropdown = ref(false)
const newCaseName = ref('')
const newCaseRule = ref('default')
const showDeleteConfirm = ref(false)
const pendingDeleteFile = ref<{ path: string } | null>(null)

const customRuleSets = computed(() => {
  return fieldRuleSets.value.filter(s => s.id !== 'default')
})

const selectedRuleName = computed(() => {
  if (!newCaseRule.value) return t('case.defaultFields')
  const set = fieldRuleSets.value.find(s => s.id === newCaseRule.value)
  return set?.name || t('case.defaultFields')
})

function selectRule(id: string) {
  newCaseRule.value = id
  showRuleDropdown.value = false
}

function goToFieldRules() {
  router.push('/case-space/field-rules')
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch { return iso }
}

function confirmNew() {
  const name = newCaseName.value.trim()
  if (!name) return
  showNewDialog.value = false
  const id = store.createFile(name)
  if (newCaseRule.value) {
    const set = fieldRuleSets.value.find(s => s.id === newCaseRule.value)
    if (set) {
      const file = store.getFileById(id)
      if (file) {
        file.customFields = set.rules.map(r => {
          let key = r.key
          let type = r.type as 'textarea' | 'select' | 'text'
          if (key === 'name') key = 'title'
          if (key === 'level') key = 'priority'
          return { key, label: r.labelCn || r.label, type, options: type === 'select' ? r.options : undefined }
        })
      }
    }
  }
  newCaseName.value = ''
  newCaseRule.value = 'default'
  router.push('/case-space/editor')
}

async function openFile() {
  const path = await pickOpenPath()
  if (!path) return
  await openFileByPath(path)
}

async function openRecentFile(file: { path: string }) {
  await openFileByPath(file.path)
}

function confirmRemoveRecent(file: { path: string }) {
  pendingDeleteFile.value = file
  showDeleteConfirm.value = true
}

async function confirmDeleteRecent() {
  if (pendingDeleteFile.value) {
    await store.removeFromRecent(pendingDeleteFile.value.path)
  }
  showDeleteConfirm.value = false
  pendingDeleteFile.value = null
}

async function openFileByPath(path: string) {
  if (path.startsWith('db://')) {
    const fileId = path.slice(5)
    const fileData = await store.loadFileFromDb(fileId)
    if (!fileData) {
      await store.removeFromRecent(path)
      return
    }
    store.addFileToSession(fileData, path)
    router.push('/case-space/editor')
    return
  }
  const content = await readFile(path)
  if (!content) {
    await store.removeFromRecent(path)
    return
  }
  const file: CaseFile = {
    id: content.id || Date.now().toString(36) + Math.random().toString(36).slice(2, 8),
    name: content.name || path.split(/[/\\]/).pop()?.replace(/\.\w+$/, '') || 'Untitled',
    version: '1.0',
    cases: content.cases || [],
    createdAt: content.createdAt || new Date().toISOString(),
    updatedAt: content.updatedAt || new Date().toISOString(),
    tags: content.tags || [],
    customFields: content.customFields || [],
  }
  store.addFileToSession(file, path)
  router.push('/case-space/editor')
}
</script>
