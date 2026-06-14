import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { CaseFile, CaseItem, RecentFileInfo, FileTab, CustomFieldDef } from '@/types'
import * as db from '@/services/database'

function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 8)
}

function createDefaultCase(order: number): CaseItem {
  return {
    id: genId(),
    module: '',
    title: '',
    precondition: '',
    steps: '',
    expected: '',
    priority: '',
    tags: [],
    assignee: '',
    remarks: '',
  }
}

function createNewFile(name: string): CaseFile {
  return {
    id: genId(),
    name,
    version: '1.0',
    cases: [createDefaultCase(1)],
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    tags: [],
    customFields: [],
  }
}

export const useCaseFileStore = defineStore('caseFile', () => {
  const fileMap = ref<Record<string, CaseFile>>({})
  const fileOrder = ref<string[]>([])
  const activeFileId = ref<string | null>(null)
  const recentFiles = ref<RecentFileInfo[]>([])
  const favorites = ref<string[]>([])
  const filePathMap = ref<Record<string, string>>({})
  const loaded = ref(false)

  async function initStore() {
    if (loaded.value) return
    try {
      const [recent, favs] = await Promise.all([db.getRecentFiles(), db.getFavorites()])
      recentFiles.value = recent.map((r: any) => ({
        path: r.path,
        name: r.name,
        caseCount: r.case_count,
        lastOpened: r.last_opened,
        isFavorite: favs.includes(r.path),
        isPinned: false,
      }))
      favorites.value = favs
      const lastActive = await db.getSetting('lastActiveFileId')
      if (lastActive && fileMap.value[lastActive]) {
        activeFileId.value = lastActive
      }
    } catch (e) {
      console.warn('DB init failed, using defaults', e)
    }
    loaded.value = true
  }

  const activeFile = computed(() => {
    if (!activeFileId.value) return null
    return fileMap.value[activeFileId.value] ?? null
  })

  const openTabs = computed<FileTab[]>(() => {
    return fileOrder.value.map(id => ({
      fileId: id,
      fileName: fileMap.value[id]?.name ?? 'Untitled',
      isDirty: true,
      path: filePathMap.value[id] ?? null,
    }))
  })

  const favoriteFiles = computed(() => {
    return recentFiles.value.filter(r => favorites.value.includes(r.path))
  })

  const recentFilesList = computed(() => {
    return recentFiles.value.slice(0, 20)
  })

  async function saveFileToDb(fileId: string) {
    const f = fileMap.value[fileId]
    if (!f) return
    try {
      await db.saveCaseFile({
        id: fileId,
        name: f.name,
        data: { ...f },
        tags: f.tags,
        customFields: f.customFields,
        ruleSetId: (f as any).ruleSetId,
        createdAt: f.createdAt,
        updatedAt: f.updatedAt,
      })
    } catch (e) {
      console.warn('Save to DB failed', e)
    }
  }

  async function loadFileFromDb(fileId: string): Promise<CaseFile | null> {
    try {
      const row = await db.loadCaseFile(fileId)
      if (row) return JSON.parse(row.data) as CaseFile
    } catch {}
    return null
  }

  function createFile(name: string): string {
    const file = createNewFile(name)
    fileMap.value[file.id] = file
    if (!fileOrder.value.includes(file.id)) {
      fileOrder.value.push(file.id)
    }
    activeFileId.value = file.id
    saveFileToDb(file.id)
    return file.id
  }

  async function addFileToSession(file: CaseFile, path?: string) {
    fileMap.value[file.id] = file
    if (!fileOrder.value.includes(file.id)) {
      fileOrder.value.push(file.id)
    }
    if (path) {
      filePathMap.value[file.id] = path
    }
    activeFileId.value = file.id
    await saveFileToDb(file.id)
    if (path) {
      await addToRecent(file.id, file.name, file.cases.length, path)
    }
  }

  function closeFile(fileId: string) {
    const idx = fileOrder.value.indexOf(fileId)
    if (idx < 0) return
    fileOrder.value.splice(idx, 1)
    delete fileMap.value[fileId]
    delete filePathMap.value[fileId]
    if (activeFileId.value === fileId) {
      activeFileId.value = fileOrder.value.length > 0 ? fileOrder.value[0] : null
    }
  }

  function setActiveFile(fileId: string) {
    if (fileMap.value[fileId]) {
      activeFileId.value = fileId
      db.setSetting('lastActiveFileId', fileId)
    }
  }

  function reorderTabs(from: number, to: number) {
    const item = fileOrder.value.splice(from, 1)[0]
    fileOrder.value.splice(to, 0, item)
  }

  function addCase() {
    const f = activeFile.value
    if (!f) return
    const c = createDefaultCase(f.cases.length + 1)
    if (f.customFields?.some(cf => cf.key === 'case_number')) {
      ;(c as any).case_number = String(f.cases.length + 1)
    }
    f.cases.push(c)
    f.updatedAt = new Date().toISOString()
  }

  function addCaseAt(idx: number) {
    const f = activeFile.value
    if (!f) return
    const c = createDefaultCase(f.cases.length + 1)
    if (f.customFields?.some(cf => cf.key === 'case_number')) {
      ;(c as any).case_number = String(f.cases.length + 1)
    }
    f.cases.splice(idx, 0, c)
    f.updatedAt = new Date().toISOString()
  }

  function updateCase(caseId: string, data: Partial<CaseItem>) {
    const f = activeFile.value
    if (!f) return
    const c = f.cases.find(c => c.id === caseId)
    if (c) {
      Object.assign(c, data)
      f.updatedAt = new Date().toISOString()
    }
  }

  function updateCaseField(caseId: string, field: string, value: any) {
    const f = activeFile.value
    if (!f) return
    const c = f.cases.find(c => c.id === caseId)
    if (c) {
      ;(c as any)[field] = value
      f.updatedAt = new Date().toISOString()
    }
  }

  function deleteCase(caseId: string) {
    const f = activeFile.value
    if (!f) return
    f.cases = f.cases.filter(c => c.id !== caseId)
    f.updatedAt = new Date().toISOString()
  }

  function duplicateCase(caseId: string) {
    const f = activeFile.value
    if (!f) return
    const c = f.cases.find(c => c.id === caseId)
    if (c) {
      const dup: CaseItem = JSON.parse(JSON.stringify(c))
      dup.id = genId()
      f.cases.splice(f.cases.indexOf(c) + 1, 0, dup)
      f.updatedAt = new Date().toISOString()
    }
  }

  function moveCase(from: number, to: number) {
    const f = activeFile.value
    if (!f) return
    const item = f.cases.splice(from, 1)[0]
    f.cases.splice(to, 0, item)
    f.updatedAt = new Date().toISOString()
  }

  function batchUpdateCases(ids: string[], field: string, value: any) {
    const f = activeFile.value
    if (!f) return
    ids.forEach(id => {
      const c = f.cases.find(c => c.id === id)
      if (c) (c as any)[field] = value
    })
    f.updatedAt = new Date().toISOString()
  }

  function addCustomField(def: CustomFieldDef) {
    const f = activeFile.value
    if (!f) return
    if (!f.customFields) f.customFields = []
    if (!f.customFields.find(c => c.key === def.key)) {
      f.customFields.push(def)
    }
  }

  function removeCustomField(key: string) {
    const f = activeFile.value
    if (!f) return
    if (f.customFields) {
      f.customFields = f.customFields.filter(c => c.key !== key)
      f.cases.forEach(c => { delete c[key] })
    }
  }

  function updateCustomField(key: string, data: Partial<CustomFieldDef>) {
    const f = activeFile.value
    if (!f) return
    const def = f.customFields?.find(c => c.key === key)
    if (def) Object.assign(def, data)
  }

  async function addToRecent(fileId: string, name: string, caseCount: number, path: string) {
    try {
      await db.addRecentFile(path, name, caseCount)
    } catch {}
    const list = recentFiles.value.filter(r => r.path !== path)
    list.unshift({
      path,
      name,
      caseCount,
      lastOpened: new Date().toISOString(),
      isFavorite: favorites.value.includes(path),
      isPinned: false,
    })
    if (list.length > 50) list.length = 50
    recentFiles.value = list
  }

  async function removeFromRecent(path: string) {
    try { await db.removeRecentFile(path) } catch {}
    recentFiles.value = recentFiles.value.filter(r => r.path !== path)
  }

  async function toggleFavorite(path: string) {
    let isFav = false
    try { isFav = await db.toggleFavorite(path) } catch {}
    const idx = favorites.value.indexOf(path)
    if (isFav) {
      if (idx < 0) favorites.value.push(path)
    } else {
      if (idx >= 0) favorites.value.splice(idx, 1)
    }
    const recent = recentFiles.value.find(r => r.path === path)
    if (recent) recent.isFavorite = favorites.value.includes(path)
  }

  function fileDataForSave(): { file: CaseFile; path?: string } | null {
    const f = activeFile.value
    if (!f) return null
    return {
      file: JSON.parse(JSON.stringify(f)),
      path: activeFileId.value ? filePathMap.value[activeFileId.value] : undefined,
    }
  }

  function setFilePath(fileId: string, path: string) {
    filePathMap.value[fileId] = path
  }

  function clearSession() {
    fileMap.value = {}
    fileOrder.value = []
    activeFileId.value = null
    filePathMap.value = {}
  }

  function getFileById(id: string): CaseFile | undefined {
    return fileMap.value[id]
  }

  function markSaved(fileId: string) {
    const f = fileMap.value[fileId]
    if (f) {
      f.updatedAt = new Date().toISOString()
    }
  }

  return {
    fileMap,
    fileOrder,
    activeFileId,
    activeFile,
    openTabs,
    recentFiles,
    recentFilesList,
    favoriteFiles,
    favorites,
    filePathMap,
    loaded,
    initStore,
    createFile,
    addFileToSession,
    closeFile,
    setActiveFile,
    reorderTabs,
    addCase,
    addCaseAt,
    updateCase,
    updateCaseField,
    deleteCase,
    duplicateCase,
    moveCase,
    batchUpdateCases,
    addCustomField,
    removeCustomField,
    updateCustomField,
    addToRecent,
    removeFromRecent,
    toggleFavorite,
    fileDataForSave,
    setFilePath,
    clearSession,
    getFileById,
    saveFileToDb,
    loadFileFromDb,
    markSaved,
  }
})
