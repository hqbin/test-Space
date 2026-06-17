<template>
  <div class="flex flex-col h-full select-none">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <button class="glass-button p-2 rounded-xl select-none" @click="goBack">
          <span class="material-symbols-outlined text-[20px]">arrow_back</span>
        </button>

      </div>
      <button class="glass-button px-5 py-2.5 rounded-full font-label-md text-label-md flex items-center gap-2 transition-all shadow-sm select-none" @click="showCreateDialog = true">
        <span class="material-symbols-outlined text-[18px]">add</span>
        New Rule Set
      </button>
    </div>

    <!-- Rule set editing -->
    <div v-if="editingSetId" class="flex-1 flex flex-col">
      <div class="flex items-center gap-3 mb-5">
        <button class="glass-button p-2 rounded-xl select-none" @click="editingSetId = ''">
          <span class="material-symbols-outlined text-[20px]">arrow_back</span>
        </button>
        <div class="flex-1">
          <input v-model="editingSetName" class="font-headline-md text-headline-md text-on-surface font-semibold bg-transparent border-b-2 border-transparent focus:border-secondary/40 focus:outline-none px-1 -ml-1 w-64 select-text" />
        </div>
        <span class="font-caption text-caption text-on-surface-variant/60">{{ editingRules.filter(r => r.visible).length }} visible fields</span>
      </div>

      <div class="glass-panel rounded-2xl overflow-hidden flex-1 flex flex-col">
        <div class="overflow-x-auto flex-1">
          <table class="w-full text-left">
            <thead>
              <tr class="font-label-md text-label-md text-on-surface-variant border-b border-glass-border-dark bg-white/5">
                <th class="py-3 px-4 font-medium w-8">#</th>
                <th class="py-3 px-2 font-medium">Field Name</th>
                <th class="py-3 px-2 font-medium w-28">Type</th>
                <th class="py-3 px-2 font-medium">Options</th>
                <th class="py-3 px-2 font-medium w-20 text-center">Visible</th>
                <th class="py-3 px-2 font-medium w-20 text-center">Required</th>
                <th class="py-3 px-2 font-medium w-12"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(rule, idx) in editingRules" :key="rule.key" class="border-b border-glass-border-dark/30 hover:bg-white/10 transition-colors" draggable="true" @dragstart="onDragStart(idx, $event)" @dragover.prevent="onDragOver(idx, $event)" @drop.prevent="onDrop(idx)" @dragleave="onDragLeave($event)" @dragend="onDragEnd" :class="{ 'opacity-50': dragIdx === idx, 'bg-white/20': dragOverIdx === idx }">
                <td class="py-2 px-4">
                  <span class="w-6 h-6 rounded-full bg-secondary-fixed/30 text-on-secondary-fixed-variant flex items-center justify-center text-[11px] font-bold select-none cursor-grab" @mousedown.stop>{{ idx + 1 }}</span>
                </td>
                <td class="py-2 px-2">
                  <input v-model="rule.labelCn" class="bg-white/50 border border-outline-variant/40 rounded-lg px-2.5 py-1.5 text-body-md text-on-surface text-[13px] focus:outline-none focus:border-secondary/40 w-full min-w-[120px] select-text" placeholder="Field title" @input="onLabelChange(rule)" />
                </td>
                <td class="py-2 px-2">
                  <select v-model="rule.type" class="bg-white/50 border border-outline-variant/40 rounded-lg px-2.5 py-1.5 text-body-md text-on-surface text-[13px] focus:outline-none focus:border-secondary/40 w-full appearance-none cursor-pointer" @change="onTypeChange(rule)">
                    <option value="textarea">textarea</option>
                    <option value="select">select</option>
                  </select>
                </td>
                <td class="py-2 px-2">
                  <input v-if="rule.type === 'select'" v-model="rule.optionsStr" class="bg-white/50 border border-outline-variant/40 rounded-lg px-2.5 py-1.5 text-body-md text-on-surface text-[13px] font-mono focus:outline-none focus:border-secondary/40 w-full select-text" placeholder="comma,separated,values" @input="syncOptions(rule)" />
                  <span v-else class="font-caption text-caption text-on-surface-variant/50 px-1">—</span>
                </td>
                <td class="py-2 px-2 text-center">
                  <button class="w-10 h-6 rounded-full transition-all relative select-none" :class="rule.visible ? 'bg-secondary-fixed' : 'bg-surface-variant/50'" @click="rule.visible = !rule.visible">
                    <span class="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-all" :class="rule.visible ? 'left-[18px]' : 'left-0.5'"></span>
                  </button>
                </td>
                <td class="py-2 px-2 text-center">
                  <button class="w-10 h-6 rounded-full transition-all relative select-none" :class="rule.required ? 'bg-secondary-fixed' : 'bg-surface-variant/50'" @click="rule.required = !rule.required">
                    <span class="absolute top-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-all" :class="rule.required ? 'left-[18px]' : 'left-0.5'"></span>
                  </button>
                </td>
                <td class="py-2 px-2">
                  <button class="glass-button p-1 rounded text-on-surface-variant/30 hover:bg-error/10 hover:text-error transition-all select-none" @click="removeField(idx)" title="Remove field">
                    <span class="material-symbols-outlined text-[16px]">remove_circle</span>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="flex items-center gap-3 px-4 py-3 border-t border-glass-border-dark/30">
          <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1.5 select-none" @click="addNewField">
            <span class="material-symbols-outlined text-[16px]">add</span>
            Add Field
          </button>
          <span class="font-caption text-caption text-on-surface-variant/40">{{ editingRules.length }} fields</span>
        </div>
      </div>

      <div class="flex justify-end gap-3 mt-5">
        <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md select-none" @click="cancelEditing">Cancel</button>
        <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="saveRuleSet">
          <span class="material-symbols-outlined text-[18px]">save</span>
          Save Changes
        </button>
      </div>
    </div>

    <!-- Rule set cards grid -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      <div v-for="set in fieldRuleSets" :key="set.id" class="rule-card glass-panel glass-hover rounded-2xl p-5 transition-all duration-250 cursor-pointer" @click="editRuleSet(set.id)">
        <div class="flex items-start justify-between mb-3">
          <div class="w-10 h-10 rounded-xl bg-secondary-fixed/30 flex items-center justify-center">
            <span class="material-symbols-outlined text-secondary text-[22px]" style="font-variation-settings: 'FILL' 1">fact_check</span>
          </div>
          <div v-if="set.id !== 'default'" class="flex gap-1" @click.stop>
            <button class="glass-button p-1.5 rounded-lg text-on-surface-variant/40 select-none" @click="confirmDeleteSet(set)" title="Delete">
              <span class="material-symbols-outlined text-[18px]">delete</span>
            </button>
          </div>
        </div>
        <h3 class="font-body-lg text-body-lg text-on-surface font-semibold mb-1 select-none">{{ set.name }}</h3>
        <div class="flex items-center gap-3 text-caption text-on-surface-variant/70">
          <span>{{ set.rules.filter(r => r.visible).length }} visible / {{ set.rules.length }} total</span>
          <span>·</span>
          <span>{{ new Date(set.createdAt).toLocaleDateString() }}</span>
        </div>
        <div class="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-glass-border-dark/40">
          <span v-for="r in set.rules.filter(r => r.visible).slice(0, 5)" :key="r.key" class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-white/50 text-on-surface-variant">{{ r.labelCn || r.label }}</span>
          <span v-if="set.rules.filter(r => r.visible).length > 5" class="px-2 py-0.5 rounded-full text-[10px] font-medium bg-white/30 text-on-surface-variant/60">+{{ set.rules.filter(r => r.visible).length - 5 }}</span>
        </div>
      </div>

      <div class="rule-card glass-panel glass-hover rounded-2xl p-5 flex items-center justify-center min-h-[200px] border-2 border-dashed border-outline-variant/30 cursor-pointer" @click="showCreateDialog = true">
        <div class="text-center">
          <span class="material-symbols-outlined text-4xl text-on-surface-variant/30">add</span>
          <p class="font-body-md text-body-md text-on-surface-variant/60 mt-2">Create Rule Set</p>
        </div>
      </div>
    </div>

    <!-- Create dialog -->
    <Teleport to="body">
      <div v-if="showCreateDialog" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm" @click="showCreateDialog = false"></div>
        <div class="glass-panel rounded-2xl p-8 w-[400px] relative z-10">
          <div class="flex items-center justify-between mb-6">
            <h3 class="font-headline-md text-headline-md text-on-surface font-semibold select-none">New Rule Set</h3>
            <button class="glass-button p-1 rounded select-none" @click="showCreateDialog = false">
              <span class="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
          <div>
            <label class="block font-label-md text-caption text-on-surface uppercase tracking-wider mb-1.5">Rule Set Name <span class="text-error">*</span></label>
            <input v-model="newSetName" class="w-full bg-white border border-outline-variant/50 rounded-xl px-4 py-3 text-body-md text-on-surface focus:ring-2 focus:ring-secondary/30 focus:border-secondary transition-all select-text" placeholder="e.g. API Testing Rules" @keydown.enter="createRuleSet" />
          </div>
          <div class="flex justify-end gap-3 mt-8">
            <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md select-none" @click="showCreateDialog = false">Cancel</button>
            <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" :disabled="!newSetName.trim()" :class="!newSetName.trim() ? 'opacity-50 cursor-not-allowed' : ''" @click="createRuleSet">
              <span class="material-symbols-outlined text-[18px]">add</span>
              Create
            </button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Delete confirmation -->
    <Teleport to="body">
      <div v-if="deleteTarget" class="fixed inset-0 z-50 flex items-center justify-center">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm" @click="deleteTarget = null"></div>
        <div class="glass-panel rounded-2xl p-8 w-[380px] relative z-10">
          <div class="flex items-center gap-3 mb-4">
            <span class="w-10 h-10 rounded-full bg-error/15 flex items-center justify-center">
              <span class="material-symbols-outlined text-error">warning</span>
            </span>
            <div>
              <h3 class="font-headline-md text-headline-md text-on-surface font-semibold select-none">Delete Rule Set</h3>
              <p class="font-body-md text-body-md text-on-surface-variant/70 mt-0.5">This action cannot be undone.</p>
            </div>
          </div>
          <p class="font-body-md text-body-md text-on-surface mb-6">Are you sure you want to delete <strong>{{ deleteTarget.name }}</strong>?</p>
          <div class="flex justify-end gap-3">
            <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md select-none" @click="deleteTarget = null">Cancel</button>
            <button class="glass-button px-6 py-2.5 rounded-full font-label-md text-label-md bg-error/10 text-error flex items-center gap-2 select-none" @click="doDeleteSet">
              <span class="material-symbols-outlined text-[18px]">delete</span>
              Delete
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useTestCaseStore, type FieldRuleSet, type FieldRule } from '@/composables/useTestCaseStore'

const router = useRouter()

function goBack() {
  router.push('/case-space')
}

const {
  fieldRuleSets, addRuleSet, updateRuleSet, deleteRuleSet, getRuleSet,
} = useTestCaseStore()

const editingSetId = ref('')
const editingSetName = ref('')
const showCreateDialog = ref(false)
const newSetName = ref('')
const deleteTarget = ref<FieldRuleSet | null>(null)
const fieldKeyGenCounter = ref(0)
const dragIdx = ref<number | null>(null)
const dragOverIdx = ref<number | null>(null)

const currentSet = computed(() => getRuleSet(editingSetId.value))
const editingRules = computed({
  get: () => {
    const s = getRuleSet(editingSetId.value)
    return s ? s.rules : []
  },
  set: () => {},
})

function editRuleSet(id: string) {
  const s = getRuleSet(id)
  if (s) {
    s.rules.forEach(r => {
      if (r.type === 'select' && r.options && !r.optionsStr) {
        r.optionsStr = r.options.join(', ')
      }
      if (!r.key) r.key = slugify(r.labelCn || r.label) + '_' + Date.now().toString(36).slice(-4)
      r.label = r.labelCn || r.label
    })
    editingSetId.value = id
    editingSetName.value = s.name
  }
}

function cancelEditing() {
  editingSetId.value = ''
  editingSetName.value = ''
  fieldKeyGenCounter.value = 0
}

function saveRuleSet() {
  const s = getRuleSet(editingSetId.value)
  if (s) {
    const clean = s.rules.map(r => {
      const { optionsStr, ...rest } = r
      return r.type === 'select'
        ? { ...rest, options: r.options && r.options.length > 0 ? r.options : [''] }
        : { ...rest, options: undefined }
    })
    updateRuleSet(s.id, { name: editingSetName.value, rules: clean })
  }
  editingSetId.value = ''
  editingSetName.value = ''
  fieldKeyGenCounter.value = 0
}

function genFieldKey(): string {
  fieldKeyGenCounter.value++
  return 'f_' + Date.now().toString(36) + fieldKeyGenCounter.value
}

function slugify(text: string): string {
  return text.toLowerCase().replace(/[^\w\u4e00-\u9fff]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '') || 'field'
}

function onLabelChange(rule: FieldRule) {
  if (!rule.key || rule.key.startsWith('f_')) {
    rule.key = slugify(rule.labelCn) + '_' + Date.now().toString(36).slice(-4)
  }
  rule.label = rule.labelCn
}

function addNewField() {
  const s = getRuleSet(editingSetId.value)
  if (!s) return
  const label = 'New Field'
  const key = genFieldKey()
  const newField: FieldRule = {
    key,
    label,
    labelCn: label,
    visible: true,
    required: false,
    type: 'textarea',
    optionsStr: '',
  }
  s.rules.push(newField)
}

function removeField(idx: number) {
  const s = getRuleSet(editingSetId.value)
  if (!s || s.rules.length <= 1) return
  s.rules.splice(idx, 1)
}

function onTypeChange(rule: FieldRule) {
  if (rule.type !== 'select') {
    rule.options = undefined
    rule.optionsStr = ''
  } else {
    rule.options = rule.optionsStr ? rule.optionsStr.split(',').map(s => s.trim()).filter(Boolean) : []
  }
}

function syncOptions(rule: FieldRule) {
  rule.options = rule.optionsStr ? rule.optionsStr.split(',').map(s => s.trim()).filter(Boolean) : []
}

function onDragStart(idx: number, event: DragEvent) {
  dragIdx.value = idx
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', String(idx))
  }
}

function onDragOver(idx: number, event: DragEvent) {
  if (dragIdx.value !== null && dragIdx.value !== idx) {
    dragOverIdx.value = idx
  }
}

function onDrop(idx: number) {
  if (dragIdx.value !== null && dragIdx.value !== idx) {
    const s = getRuleSet(editingSetId.value)
    if (s) {
      const [moved] = s.rules.splice(dragIdx.value, 1)
      s.rules.splice(idx, 0, moved)
    }
  }
  dragIdx.value = null
  dragOverIdx.value = null
}

function onDragLeave(event: DragEvent) {
  const target = event.currentTarget as HTMLElement
  const related = event.relatedTarget as HTMLElement
  if (!target.contains(related)) {
    dragOverIdx.value = null
  }
}

function onDragEnd() {
  dragIdx.value = null
  dragOverIdx.value = null
}

function createRuleSet() {
  const name = newSetName.value.trim()
  if (!name) return
  addRuleSet(name)
  showCreateDialog.value = false
  newSetName.value = ''
}

function confirmDeleteSet(set: FieldRuleSet) {
  deleteTarget.value = set
}

function doDeleteSet() {
  if (deleteTarget.value) {
    deleteRuleSet(deleteTarget.value.id)
    deleteTarget.value = null
  }
}
</script>

<style scoped>
.rule-card {
  backdrop-filter: blur(16px);
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(255, 255, 255, 0.5);
}
.rule-card:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: rgba(100, 120, 255, 0.15);
}
</style>
