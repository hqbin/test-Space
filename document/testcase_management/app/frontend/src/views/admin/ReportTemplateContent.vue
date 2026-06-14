<template>
  <div class="report-template-content">
    <div class="content-header">
      <div class="header-left">
        <el-button type="primary" :icon="Plus" @click="handleCreate" :disabled="!currentTeamId">
          {{ $t('reportTemplate.createTemplate') }}
        </el-button>
      </div>
    </div>

    <div class="table-wrapper">
      <el-table :data="templates" style="width: 100%" border v-loading="loading"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px' }">
        <el-table-column prop="name" :label="$t('reportTemplate.name')" min-width="150" align="center">
          <template #default="scope">
            <el-tooltip :content="scope.row.name" placement="top" :teleported="true" :show-after="500">
              <span class="cell-text">{{ scope.row.name }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('reportTemplate.description')" min-width="180" align="center">
          <template #default="scope">
            <el-tooltip :content="scope.row.description || '-'" placement="top" :teleported="true" :show-after="500">
              <span class="cell-text">{{ scope.row.description || '-' }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('reportTemplate.fieldConfig')" width="120" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ (row.selected_fields || []).length }} 个字段</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="$t('reportTemplate.criteriaConfig')" width="140" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ (row.criteria_config?.rules || []).length }} 条规则</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_default" :label="$t('reportTemplate.isDefault')" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_default" type="success" size="small">默认</el-tag>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_by_name" :label="$t('reportTemplate.creator')" width="120" align="center">
          <template #default="scope">
            <el-tooltip :content="scope.row.created_by_name || '-'" placement="top" :teleported="true" :show-after="500">
              <span class="cell-text">{{ scope.row.created_by_name || '-' }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" :label="$t('reportTemplate.updatedAt')" width="180" align="center">
          <template #default="scope">
            <el-tooltip :content="formatDate(scope.row.updated_at)" placement="top" :teleported="true" :show-after="500">
              <span class="cell-text">{{ formatDate(scope.row.updated_at) }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="240" align="center" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">{{ $t('common.edit') }}</el-button>
            <el-button link type="success" :icon="Star" @click="handleSetDefault(row)" :disabled="row.is_default">
              {{ $t('reportTemplate.setDefault') }}
            </el-button>
            <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-empty v-if="!currentTeamId" description="请先选择项目组" />

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('reportTemplate.editTemplate') : $t('reportTemplate.createTemplate')"
      width="860px" :close-on-click-modal="false" destroy-on-close class="report-tpl-dialog">
      <el-form :model="form" label-position="top">
        <el-row :gutter="16">
          <el-col :span="16">
            <el-form-item :label="$t('reportTemplate.name')" required>
              <el-input v-model="form.name" :placeholder="$t('reportTemplate.inputName')" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item :label="$t('reportTemplate.description')">
              <el-input v-model="form.description" :placeholder="$t('reportTemplate.inputDescription')" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 字段配置 -->
        <div class="section-block">
          <div class="section-title">
            <svg viewBox="0 0 20 20" fill="currentColor" class="section-icon"><path fill-rule="evenodd" d="M3 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 4a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/></svg>
            {{ $t('reportTemplate.fieldConfig') }}
          </div>
          <div class="field-grid">
            <div v-for="field in allFields" :key="field.key"
              class="field-chip" :class="{ active: form.selected_fields.includes(field.key) }"
              @click="toggleField(field.key)">
              {{ field.label }}
            </div>
          </div>
        </div>

        <!-- 测试标准 -->
        <div class="section-block">
          <div class="section-title">
            <svg viewBox="0 0 20 20" fill="currentColor" class="section-icon"><path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd"/></svg>
            {{ $t('reportTemplate.criteriaConfig') }}
            <span class="section-hint">{{ $t('reportTemplate.criteriaConfigHint') }}</span>
          </div>

          <div class="rule-cards">
            <div v-for="(rule, index) in form.criteria_config.rules" :key="index" class="rule-card">
              <div class="rule-card-header">
                <el-select v-model="rule.metric" size="small" @change="onMetricChange(rule)" class="metric-select">
                  <el-option label="Testcase Pass Rate" value="testcase_pass_rate" />
                  <el-option label="Open PR Count" value="open_pr_count" />
                  <el-option label="PR Closure Rate" value="pr_closure_rate" />
                </el-select>
                <el-button size="small" type="danger" text :icon="Close" circle @click="removeRule(index)" class="rule-remove-btn" />
              </div>

              <!-- testcase_pass_rate -->
              <div v-if="rule.metric === 'testcase_pass_rate'" class="rule-card-body">
                <div class="inline-rule">
                  <span class="rule-text">Pass Rate</span>
                  <el-select v-model="rule.operator" size="small" style="width: 68px">
                    <el-option label=">=" value=">=" />
                    <el-option label=">" value=">" />
                  </el-select>
                  <el-input-number v-model="rule.value" :min="0" :max="100" :step="1" :precision="0" size="small" style="width: 100px" controls-position="right" />
                  <span class="rule-unit">%</span>
                </div>
              </div>

              <!-- open_pr_count -->
              <div v-if="rule.metric === 'open_pr_count'" class="rule-card-body">
                <div v-for="(sub, si) in rule.sub_rules" :key="si" class="inline-rule">
                  <span class="rule-text" :class="'level-' + sub.level.toLowerCase()">{{ sub.level }}</span>
                  <el-select v-model="sub.operator" size="small" style="width: 68px">
                    <el-option label="=" value="=" />
                    <el-option label="<=" value="<=" />
                    <el-option label="<" value="<" />
                  </el-select>
                  <el-input-number v-model="sub.value" :min="0" :step="1" :precision="0" size="small" style="width: 100px" controls-position="right" />
                </div>
              </div>

              <!-- pr_closure_rate -->
              <div v-if="rule.metric === 'pr_closure_rate'" class="rule-card-body">
                <div v-for="(sub, si) in rule.sub_rules" :key="si" class="inline-rule">
                  <span class="rule-text" :class="'level-' + sub.level.toLowerCase()">{{ sub.level }}</span>
                  <el-select v-model="sub.operator" size="small" style="width: 68px">
                    <el-option label=">=" value=">=" />
                    <el-option label=">" value=">" />
                    <el-option label="=" value="=" />
                  </el-select>
                  <el-input-number v-model="sub.value" :min="0" :max="100" :step="1" :precision="0" size="small" style="width: 100px" controls-position="right" />
                  <span class="rule-unit">%</span>
                </div>
              </div>
            </div>

            <div class="add-rule-btn" @click="addRule">
              <el-icon><Plus /></el-icon>
              <span>添加规则</span>
            </div>
          </div>

          <!-- 标准预览 -->
          <div class="criteria-preview" v-if="form.criteria_config.rules.length">
            <svg viewBox="0 0 20 20" fill="currentColor" class="preview-icon"><path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/></svg>
            <span>{{ criteriaPreviewText }}</span>
          </div>
        </div>

        <!-- 结论模板 -->
        <div class="section-block">
          <div class="section-title">
            <svg viewBox="0 0 20 20" fill="currentColor" class="section-icon"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clip-rule="evenodd"/></svg>
            {{ $t('reportTemplate.conclusionRule') }}
            <span class="section-hint">{{ $t('reportTemplate.conclusionRuleHint') }}</span>
          </div>
          <el-row :gutter="16">
            <el-col :span="12">
              <div class="conclusion-box pass">
                <div class="conclusion-label">
                  <span class="conclusion-dot pass"></span>{{ $t('reportTemplate.conclusionPass') }}
                </div>
                <el-input v-model="form.criteria_config.conclusion_pass" type="textarea" :rows="2"
                  :placeholder="$t('reportTemplate.inputConclusionPass')" resize="none" />
              </div>
            </el-col>
            <el-col :span="12">
              <div class="conclusion-box fail">
                <div class="conclusion-label">
                  <span class="conclusion-dot fail"></span>{{ $t('reportTemplate.conclusionFail') }}
                </div>
                <el-input v-model="form.criteria_config.conclusion_fail" type="textarea" :rows="2"
                  :placeholder="$t('reportTemplate.inputConclusionFail')" resize="none" />
              </div>
            </el-col>
          </el-row>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Star, Delete, Close } from '@element-plus/icons-vue'
import { getReportTemplates, createReportTemplate, updateReportTemplate, deleteReportTemplate, setDefaultReportTemplate } from '../../api/reportTemplate'
import { useTeam } from '@/composables/useTeam'

const { t } = useI18n()
const { currentTeam } = useTeam()
const currentTeamId = computed(() => currentTeam.value?.id || null)

const loading = ref(false)
const submitting = ref(false)
const templates = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)

const defaultOpenPrSubRules = () => [
  { level: 'Blocker', operator: '=', value: 0 },
  { level: 'Critical', operator: '=', value: 0 },
  { level: 'Major', operator: '<=', value: 5 }
]

const defaultClosureRateSubRules = () => [
  { level: 'Blocker', operator: '>=', value: 100 },
  { level: 'Critical', operator: '>=', value: 98 },
  { level: 'Major', operator: '>=', value: 90 }
]

const defaultCriteriaConfig = () => ({
  rules: [
    { metric: 'testcase_pass_rate', operator: '>=', value: 95 }
  ],
  conclusion_pass: 'Therefore, the test results meet the product release standards.',
  conclusion_fail: 'Therefore, the test results fail to meet the product release criteria.'
})

const form = ref({
  name: '',
  description: '',
  selected_fields: ['test_cycle', 'testers', 'reviewer_name', 'test_conclusion', 'release_criteria', 'remark', 'test_results', 'test_cases'],
  criteria_config: defaultCriteriaConfig()
})

const allFields = computed(() => [
  { key: 'test_cycle', label: t('reportTemplate.fields.test_cycle') },
  { key: 'testers', label: t('reportTemplate.fields.testers') },
  { key: 'reviewer_name', label: t('reportTemplate.fields.reviewer_name') },
  { key: 'test_conclusion', label: t('reportTemplate.fields.test_conclusion') },
  { key: 'release_criteria', label: t('reportTemplate.fields.release_criteria') },
  { key: 'remark', label: t('reportTemplate.fields.remark') },
  { key: 'test_results', label: t('reportTemplate.fields.test_results') },
  { key: 'test_cases', label: t('reportTemplate.fields.test_cases') },
  { key: 'zmind_stats', label: t('reportTemplate.fields.zmind_stats') },
  { key: 'issue_list', label: t('reportTemplate.fields.issue_list') }
])

const toggleField = (key) => {
  const idx = form.value.selected_fields.indexOf(key)
  if (idx >= 0) form.value.selected_fields.splice(idx, 1)
  else form.value.selected_fields.push(key)
}

const onMetricChange = (rule) => {
  if (rule.metric === 'testcase_pass_rate') {
    rule.operator = '>='; rule.value = 95; delete rule.sub_rules
  } else if (rule.metric === 'open_pr_count') {
    rule.sub_rules = defaultOpenPrSubRules(); delete rule.operator; delete rule.value
  } else if (rule.metric === 'pr_closure_rate') {
    rule.sub_rules = defaultClosureRateSubRules(); delete rule.operator; delete rule.value
  }
}

const addRule = () => {
  form.value.criteria_config.rules.push({ metric: 'testcase_pass_rate', operator: '>=', value: 95 })
}

const removeRule = (index) => {
  form.value.criteria_config.rules.splice(index, 1)
}

const criteriaPreviewText = computed(() => {
  const rules = form.value.criteria_config.rules || []
  if (!rules.length) return '未配置测试标准'
  const parts = rules.map(r => {
    if (r.metric === 'testcase_pass_rate') return `Testcase pass rate ${r.operator || '>='}${r.value || 95}%`
    if (r.metric === 'open_pr_count' && r.sub_rules) return `Open PR: ${r.sub_rules.map(s => `${s.level}${s.operator}${s.value}`).join(', ')}`
    if (r.metric === 'pr_closure_rate' && r.sub_rules) return `PR closure rate: ${r.sub_rules.map(s => `${s.level}${s.operator}${s.value}%`).join(', ')}`
    return ''
  }).filter(Boolean)
  return parts.join('  &  ')
})

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadTemplates = async () => {
  if (!currentTeamId.value) { templates.value = []; return }
  loading.value = true
  try { const res = await getReportTemplates(currentTeamId.value); templates.value = res.data || [] }
  catch (e) { ElMessage.error('加载模板失败') }
  finally { loading.value = false }
}

const handleCreate = () => {
  isEdit.value = false; editId.value = null
  form.value = {
    name: '', description: '',
    selected_fields: ['test_cycle', 'testers', 'reviewer_name', 'test_conclusion', 'release_criteria', 'remark', 'test_results', 'test_cases'],
    criteria_config: defaultCriteriaConfig()
  }
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true; editId.value = row.id
  const config = row.criteria_config || {}
  let rules = config.rules || []
  if (!rules.length && config.pass_rate_threshold) {
    rules = [{ metric: 'testcase_pass_rate', operator: '>=', value: config.pass_rate_threshold }]
  }
  form.value = {
    name: row.name, description: row.description || '',
    selected_fields: [...(row.selected_fields || [])],
    criteria_config: {
      rules,
      conclusion_pass: config.conclusion_pass || 'Therefore, the test results meet the product release standards.',
      conclusion_fail: config.conclusion_fail || 'Therefore, the test results fail to meet the product release criteria.'
    }
  }
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.value.name.trim()) { ElMessage.warning(t('reportTemplate.inputName')); return }
  submitting.value = true
  try {
    const payload = { name: form.value.name, description: form.value.description, selected_fields: form.value.selected_fields, criteria_config: form.value.criteria_config }
    if (isEdit.value) { await updateReportTemplate(editId.value, payload); ElMessage.success(t('reportTemplate.updateSuccess')) }
    else { await createReportTemplate(currentTeamId.value, payload); ElMessage.success(t('reportTemplate.createSuccess')) }
    dialogVisible.value = false; loadTemplates()
  } catch (e) { ElMessage.error(t('common.failed')) }
  finally { submitting.value = false }
}

const handleSetDefault = async (row) => {
  try { await setDefaultReportTemplate(row.id); ElMessage.success(t('reportTemplate.setDefaultSuccess')); loadTemplates() }
  catch (e) { ElMessage.error(t('common.failed')) }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('reportTemplate.deleteConfirm'), t('common.tip'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await deleteReportTemplate(row.id); ElMessage.success(t('reportTemplate.deleteSuccess')); loadTemplates()
  } catch (e) { if (e !== 'cancel') ElMessage.error(t('common.failed')) }
}

onMounted(() => { if (currentTeamId.value) loadTemplates() })
watch(() => currentTeam.value?.id, () => { loadTemplates() })
</script>

<style scoped>
.report-template-content { padding: 20px; height: 100%; overflow-y: auto; }
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.header-left { display: flex; align-items: center; }
.table-wrapper { margin-top: 8px; }

/* Section blocks */
.section-block {
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #fafbfc;
  border-radius: 10px;
  border: 1px solid #eef1f6;
}
.section-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 14px;
}
.section-icon { width: 16px; height: 16px; color: #6366f1; flex-shrink: 0; }
.section-hint { font-weight: 400; font-size: 12px; color: #94a3b8; margin-left: 8px; }

/* Field chips */
.field-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.field-chip {
  display: inline-flex;
  align-items: center;
  padding: 8px 20px;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
  white-space: nowrap;
  font-size: 13px;
  color: #64748b;
}
.field-chip:hover { border-color: #a5b4fc; background: #f5f3ff; }
.field-chip.active { border-color: #6366f1; background: #eef2ff; color: #4338ca; font-weight: 500; }

/* Rule cards */
.rule-cards { display: flex; flex-direction: column; gap: 10px; }
.rule-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  overflow: hidden;
  transition: box-shadow 0.15s ease;
}
.rule-card:hover { box-shadow: 0 2px 8px rgba(99, 102, 241, 0.08); }
.rule-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  background: #f8fafc;
  border-bottom: 1px solid #f1f5f9;
}
.metric-select { width: 200px; }
.rule-remove-btn { color: #ef4444; opacity: 0.5; }
.rule-remove-btn:hover { opacity: 1; }
.rule-card-body { padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; }
.inline-rule {
  display: flex;
  align-items: center;
  gap: 8px;
}
.rule-text {
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  min-width: 72px;
}
.rule-unit { font-size: 12px; color: #94a3b8; }

/* Level colors */
.level-blocker { color: #dc2626; }
.level-critical { color: #ea580c; }
.level-major { color: #d97706; }

/* Add rule button */
.add-rule-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px;
  border: 1px dashed #cbd5e1;
  border-radius: 10px;
  color: #6366f1;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.add-rule-btn:hover { border-color: #6366f1; background: #f5f3ff; }

/* Criteria preview */
.criteria-preview {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 14px;
  background: #f0fdf4;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
  font-size: 12px;
  color: #475569;
  line-height: 1.6;
}
.preview-icon { width: 16px; height: 16px; color: #22c55e; flex-shrink: 0; margin-top: 1px; }

/* Conclusion boxes */
.conclusion-box {
  border-radius: 8px;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
}
.conclusion-box.pass { background: #f0fdf4; border-color: #bbf7d0; }
.conclusion-box.fail { background: #fef2f2; border-color: #fecaca; }
.conclusion-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 8px;
}
.conclusion-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.conclusion-dot.pass { background: #22c55e; }
.conclusion-dot.fail { background: #ef4444; }
.conclusion-box :deep(.el-textarea__inner) {
  background: transparent;
  border: none;
  box-shadow: none;
  padding: 0;
  font-size: 12px;
  color: #64748b;
}

:deep(.el-divider__text) { font-weight: 600; color: #475569; font-size: 14px; }

.cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}
</style>
