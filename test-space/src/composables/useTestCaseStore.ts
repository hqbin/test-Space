import { reactive, computed, toRefs } from 'vue'
import * as db from '@/services/database'
import { useI18n } from '@/composables/useI18n'

export interface FieldRule {
  key: string
  label: string
  labelCn: string
  visible: boolean
  required: boolean
  type: 'textarea' | 'select'
  options?: string[]
  optionsStr?: string
}

export interface FieldRuleSet {
  id: string
  name: string
  rules: FieldRule[]
  createdAt: string
}

function makeDefaultFieldRules(t: (key: string) => string): FieldRule[] {
  return [
    { key: 'case_number', label: 'Case #', labelCn: t('case.field.caseNo'), visible: true, required: false, type: 'textarea' },
    { key: 'module', label: 'Module', labelCn: t('case.field.module'), visible: true, required: false, type: 'textarea' },
    { key: 'name', label: 'Title', labelCn: t('case.field.title'), visible: true, required: true, type: 'textarea' },
    { key: 'precondition', label: 'Precondition', labelCn: t('case.field.precondition'), visible: true, required: false, type: 'textarea' },
    { key: 'steps', label: 'Steps', labelCn: t('case.field.steps'), visible: true, required: true, type: 'textarea' },
    { key: 'expected', label: 'Expected', labelCn: t('case.field.expected'), visible: true, required: false, type: 'textarea' },
    { key: 'level', label: 'Level', labelCn: t('case.field.priority'), visible: true, required: true, type: 'select', options: ['L1', 'L2', 'L3', 'L4'] },
    { key: 'automation', label: 'Automation', labelCn: t('case.field.automation'), visible: true, required: false, type: 'select', options: ['N', 'Y'] },
    { key: 'remarks', label: 'Remarks', labelCn: t('case.field.remarks'), visible: true, required: false, type: 'textarea' },
  ]
}

function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
}

const defaultSet: FieldRuleSet = {
  id: 'default',
  name: 'Default Fields',
  rules: [],
  createdAt: new Date().toISOString(),
}

const state = reactive({
  fieldRuleSets: [defaultSet] as FieldRuleSet[],
  activeRuleSetId: 'default' as string,
})

async function loadRuleSetsFromDb() {
  try {
    const sets = await db.loadFieldRuleSets()
    if (sets.length > 0) {
      const mapped = sets.map((s: any) => ({
        id: s.id,
        name: s.name,
        rules: s.rules as FieldRule[],
        createdAt: s.created_at,
      }))
      const hasDefault = mapped.some(s => s.id === 'default')
      if (!hasDefault) mapped.unshift(defaultSet)
      state.fieldRuleSets = mapped
    }
  } catch {}
}

async function saveRuleSetToDb(set: FieldRuleSet) {
  try {
    await db.saveFieldRuleSet({
      id: set.id,
      name: set.name,
      rules: set.rules,
      createdAt: set.createdAt,
    })
  } catch {}
}

loadRuleSetsFromDb()

export function useTestCaseStore() {
  const { t } = useI18n()
  const defaultFieldRules = makeDefaultFieldRules(t)

  const defaultSet = state.fieldRuleSets.find(s => s.id === 'default')
  if (defaultSet && defaultSet.rules.length === 0) {
    defaultSet.rules = defaultFieldRules
  }

  const fieldRuleSets = computed(() => state.fieldRuleSets)
  const activeRuleSetId = computed(() => state.activeRuleSetId)

  const activeFieldRules = computed(() => {
    const set = state.fieldRuleSets.find(s => s.id === state.activeRuleSetId)
    return set ? set.rules : defaultFieldRules
  })

  function setActiveRuleSetId(id: string) {
    state.activeRuleSetId = id
  }

  function addRuleSet(name: string): FieldRuleSet {
    const set: FieldRuleSet = {
      id: 'rs_' + genId(),
      name,
      rules: defaultFieldRules.map(r => ({ ...r })),
      createdAt: new Date().toISOString(),
    }
    state.fieldRuleSets.push(set)
    saveRuleSetToDb(set)
    return set
  }

  function updateRuleSet(id: string, data: { name?: string; rules?: FieldRule[] }) {
    const set = state.fieldRuleSets.find(s => s.id === id)
    if (set) {
      if (data.name !== undefined) set.name = data.name
      if (data.rules !== undefined) set.rules = data.rules
      saveRuleSetToDb(set)
    }
  }

  function deleteRuleSet(id: string) {
    if (id === 'default') return
    state.fieldRuleSets = state.fieldRuleSets.filter(s => s.id !== id)
    if (state.activeRuleSetId === id) state.activeRuleSetId = 'default'
    db.deleteFieldRuleSet(id)
  }

  function getRuleSet(id: string): FieldRuleSet | undefined {
    return state.fieldRuleSets.find(s => s.id === id)
  }

  function addFieldToRuleSet(setId: string, field: FieldRule) {
    const set = state.fieldRuleSets.find(s => s.id === setId)
    if (set) {
      set.rules.push(field)
      saveRuleSetToDb(set)
    }
  }

  function removeFieldFromRuleSet(setId: string, fieldKey: string) {
    const set = state.fieldRuleSets.find(s => s.id === setId)
    if (set) {
      set.rules = set.rules.filter(r => r.key !== fieldKey)
      saveRuleSetToDb(set)
    }
  }

  function updateFieldInRuleSet(setId: string, fieldKey: string, data: Partial<FieldRule>) {
    const set = state.fieldRuleSets.find(s => s.id === setId)
    if (set) {
      const field = set.rules.find(r => r.key === fieldKey)
      if (field) {
        Object.assign(field, data)
        saveRuleSetToDb(set)
      }
    }
  }

  function reorderFieldsInRuleSet(setId: string, fromIndex: number, toIndex: number) {
    const set = state.fieldRuleSets.find(s => s.id === setId)
    if (set) {
      const rules = [...set.rules]
      const [moved] = rules.splice(fromIndex, 1)
      rules.splice(toIndex, 0, moved)
      set.rules = rules
      saveRuleSetToDb(set)
    }
  }

  return {
    fieldRuleSets,
    activeRuleSetId,
    activeFieldRules,
    setActiveRuleSetId,
    addRuleSet,
    updateRuleSet,
    deleteRuleSet,
    getRuleSet,
    addFieldToRuleSet,
    removeFieldFromRuleSet,
    updateFieldInRuleSet,
    reorderFieldsInRuleSet,
  }
}
