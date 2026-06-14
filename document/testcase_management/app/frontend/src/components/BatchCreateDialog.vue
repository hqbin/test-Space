<template>
  <el-dialog
    v-model="visible"
    title="批量新建用例"
    width="98vw"
    :close-on-click-modal="false"
    @opened="handleOpened"
    @closed="handleClosed"
    top="1vh"
    class="batch-dialog"
  >
    <div class="batch-table-wrapper">
      <div class="native-table-scroll">
        <table class="native-table">
          <colgroup>
            <col style="width: 40px" />
            <col style="width: 150px" />
            <col style="width: 200px" />
            <col style="width: 120px" />
            <col style="width: 200px" />
            <col style="width: 220px" />
            <col style="width: 280px" />
            <col style="width: 280px" />
            <col style="width: 100px" />
            <col style="width: 200px" />
            <col style="width: 70px" />
          </colgroup>
          <thead>
            <tr>
              <th>#</th>
              <th>用例库</th>
              <th>所属模块</th>
              <th>类型</th>
              <th>用例标题</th>
              <th>前置条件</th>
              <th>操作步骤</th>
              <th>预期结果</th>
              <th>用例等级</th>
              <th>备注</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="index">
              <td class="cell-center">{{ index + 1 }}</td>
              <td>
                <el-select
                  v-model="row.primary_project_id"
                  placeholder="选用例库"
                  size="small"
                  filterable
                  style="width: 100%"
                  @change="handleProjectChange(index)"
                >
                  <el-option
                    v-for="p in projectList"
                    :key="p.id"
                    :label="p.name"
                    :value="p.id"
                  />
                </el-select>
              </td>
              <td>
                <el-tree-select
                  v-model="row.module"
                  :data="getModuleTree(row.primary_project_id)"
                  :props="{ label: 'label', value: 'value', children: 'children' }"
                  placeholder="选模块"
                  filterable
                  check-strictly
                  :render-after-expand="false"
                  size="small"
                  style="width: 100%"
                  :disabled="!row.primary_project_id"
                />
              </td>
              <td>
                <el-select v-model="row.case_type" size="small" style="width: 100%">
                  <el-option label="功能测试" value="COMMON" />
                  <el-option label="性能测试" value="PERFORMANCE" />
                  <el-option label="安全测试" value="SECURITY" />
                  <el-option label="接口测试" value="INTERFACE" />
                  <el-option label="安装部署" value="INSTALL" />
                  <el-option label="配置相关" value="CONFIG" />
                  <el-option label="兼容性测试" value="COMPATIBILITY" />
                  <el-option label="其他" value="OTHER" />
                </el-select>
              </td>
              <td>
                <el-input
                  v-model="row.name"
                  placeholder="请输入"
                  size="small"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 6 }"
                />
              </td>
              <td>
                <el-input
                  v-model="row.precondition"
                  placeholder="请输入"
                  size="small"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 6 }"
                />
              </td>
              <td>
                <el-input
                  v-model="row.steps_text"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 8 }"
                  placeholder="有序号（1. 2. 3.）则按序号分多步，否则整体为一步"
                  size="small"
                />
              </td>
              <td>
                <el-input
                  v-model="row.expected_text"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 8 }"
                  placeholder="有序号（1. 2. 3.）则按序号分多步，否则整体为一步"
                  size="small"
                />
              </td>
              <td>
                <el-select v-model="row.level" size="small" style="width: 100%">
                  <el-option label="L1" value="L1" />
                  <el-option label="L2" value="L2" />
                  <el-option label="L3" value="L3" />
                  <el-option label="L4" value="L4" />
                </el-select>
              </td>
              <td>
                <el-input
                  v-model="row.remarks"
                  placeholder="请输入"
                  size="small"
                  type="textarea"
                  :autosize="{ minRows: 1, maxRows: 6 }"
                />
              </td>
              <td class="cell-center">
                <div style="display: flex; gap: 4px; justify-content: center;">
                  <el-button
                    :icon="CopyDocument"
                    size="small"
                    link
                    @click="copyRow(index)"
                    title="复制此行"
                  />
                  <el-button
                    v-if="rows.length > 1"
                    :icon="Delete"
                    size="small"
                    link
                    type="danger"
                    @click="deleteRow(index)"
                    title="删除此行"
                  />
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div class="add-row-bar">
      <el-button :icon="Plus" circle @click="addRow" />
    </div>
    <template #footer>
      <el-button @click="handleCancel" :disabled="submitting">取消</el-button>
      <el-button type="primary" @click="handleConfirm" :loading="submitting">确认新建</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Plus, CopyDocument, Delete } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getModuleTree as fetchModuleTree } from '../api/module'
import { batchCreateTestCases } from '../api/testcase'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  projectList: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'success', 'closed'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const submitting = ref(false)
const moduleTreeCache = ref({})

const createEmptyRow = () => ({
  primary_project_id: null,
  module: '',
  case_type: 'COMMON',
  name: '',
  precondition: '',
  steps_text: '',
  expected_text: '',
  level: 'L3',
  remarks: ''
})

const rows = ref([createEmptyRow()])

const buildFormTreeData = (nodes, parentPath = '') => {
  return nodes.map(node => {
    const path = parentPath ? `${parentPath}/${node.name}` : node.name
    const item = {
      label: node.name,
      value: path,
      children: []
    }
    if (node.children && node.children.length > 0) {
      item.children = buildFormTreeData(node.children, path)
    }
    return item
  })
}

const getModuleTree = (projectId) => {
  if (!projectId) return []
  if (moduleTreeCache.value[projectId]) {
    return moduleTreeCache.value[projectId]
  }
  loadModuleTree(projectId)
  return []
}

const loadModuleTree = async (projectId) => {
  if (!projectId) return
  try {
    const res = await fetchModuleTree(projectId)
    moduleTreeCache.value[projectId] = buildFormTreeData(res.data || [])
  } catch {
    moduleTreeCache.value[projectId] = []
  }
}

const handleProjectChange = (index) => {
  const row = rows.value[index]
  row.module = ''
  if (row.primary_project_id) {
    loadModuleTree(row.primary_project_id)
  }
}

const addRow = () => {
  const last = rows.value[rows.value.length - 1]
  const newRow = createEmptyRow()
  if (last) {
    newRow.primary_project_id = last.primary_project_id
    newRow.module = last.module
    newRow.case_type = last.case_type
    // 预加载该项目的模块树（如已缓存则跳过）
    if (last.primary_project_id && !moduleTreeCache.value[last.primary_project_id]) {
      loadModuleTree(last.primary_project_id)
    }
  }
  rows.value.push(newRow)
}

const copyRow = (index) => {
  const source = rows.value[index]
  rows.value.push({ ...source })
}

const deleteRow = (index) => {
  rows.value.splice(index, 1)
}

// 与后端 excel.py split_steps_by_number 一致的步骤解析逻辑：
// - 有序号（至少2行以 1. 2. 1、等开头）→ 按序号分隔，续行合并到上一条
// - 无序号 → 整体作为1条，保留内部换行
const splitStepsByNumber = (text) => {
  if (!text) return []
  const lines = text.split('\n')
  const numberedLines = lines.filter(l => /^\s*\d+\s*(?:[。、]|\.)(?!\d)/.test(l.trim()))
  if (numberedLines.length >= 2) {
    const items = []
    let current = null
    for (const line of lines) {
      const stripped = line.trim()
      if (/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/.test(stripped)) {
        if (current !== null) items.push(current.trim())
        current = stripped.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
      } else if (current !== null) {
        current += '\n' + line
      }
    }
    if (current !== null) items.push(current.trim())
    return items.filter(i => i)
  }
  const stripped = text.trim()
  return stripped ? [stripped] : []
}

const handleOpened = () => {
  // 对话框打开时的额外处理
}

const handleCancel = async () => {
  try {
    await ElMessageBox.confirm('确认取消？已填写的数据将丢失', '提示', {
      confirmButtonText: '确认取消',
      cancelButtonText: '继续编辑',
      type: 'warning'
    })
    visible.value = false
  } catch {
    // 用户点了取消，不做操作
  }
}

const handleConfirm = async () => {
  for (let i = 0; i < rows.value.length; i++) {
    const row = rows.value[i]
    if (!row.primary_project_id) {
      ElMessage.warning(`第 ${i + 1} 行：请选用例库`)
      return
    }
    if (!row.module) {
      ElMessage.warning(`第 ${i + 1} 行：请选择所属模块`)
      return
    }
    if (!row.name) {
      ElMessage.warning(`第 ${i + 1} 行：请输入用例标题`)
      return
    }
    if (!row.level) {
      ElMessage.warning(`第 ${i + 1} 行：请选用例等级`)
      return
    }
    const stepsParsed = splitStepsByNumber(row.steps_text)
    const expectedParsed = splitStepsByNumber(row.expected_text)
    if (stepsParsed.length === 0 && expectedParsed.length === 0) {
      ElMessage.warning(`第 ${i + 1} 行：操作步骤和预期结果不能都为空`)
      return
    }
  }

  submitting.value = true
  try {
    const apiData = rows.value.map(row => {
      const stepsItems = splitStepsByNumber(row.steps_text)
      const expectedItems = splitStepsByNumber(row.expected_text)
      const maxLen = Math.max(stepsItems.length, expectedItems.length)
      const steps = []
      for (let i = 0; i < maxLen; i++) {
        const step = stepsItems[i] || ''
        const expected = expectedItems[i] || ''
        if (step || expected) {
          steps.push({ step, expected })
        }
      }
      if (steps.length === 0) {
        steps.push({ step: '', expected: '' })
      }

      const expectedText = steps.map((s, i) => {
        let et = String(s.expected || '').trim()
        et = et.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        return `${i + 1}. ${et}`
      }).join('\n')

      return {
        primary_project_id: row.primary_project_id,
        module: row.module,
        name: row.name,
        case_type: row.case_type,
        precondition: row.precondition || '',
        steps: JSON.stringify(steps),
        expected_result: expectedText,
        level: row.level,
        automation: null,
        tags: null,
        archive_source: '',
        remarks: row.remarks || ''
      }
    })

    const res = await batchCreateTestCases({ testcases: apiData })
    const data = res.data

    if (data.success_count > 0) {
      let msg = `成功创建 ${data.success_count} 条用例`
      if (data.fail_count > 0) {
        msg += `，${data.fail_count} 条失败`
        if (data.errors && data.errors.length > 0) {
          const details = data.errors.slice(0, 5).map(e => `第${e.row}行：${e.message}`).join('；')
          msg += `。失败详情：${details}`
        }
      }
      ElMessage.success(msg)
    } else {
      const errorMsg = data.errors && data.errors.length > 0
        ? data.errors.map(e => `第${e.row}行：${e.message}`).join('；')
        : '创建失败'
      ElMessage.error(errorMsg)
      return
    }

    visible.value = false
    emit('success')
  } catch (error) {
    let errorMsg = '批量创建失败'
    if (error.response?.data?.detail) {
      errorMsg = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMsg = error.response.data.message
    } else if (error.message) {
      errorMsg = error.message
    }
    ElMessage.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

const handleClosed = () => {
  rows.value = [createEmptyRow()]
  moduleTreeCache.value = {}
  emit('closed')
}
</script>

<style scoped>
.batch-table-wrapper {
  margin-bottom: 8px;
}

.native-table-scroll {
  overflow-x: auto;
  width: 100%;
}

/* 原生 table — 行高完全由内容决定，不受 el-table 限制 */
.native-table {
  width: 100%;
  min-width: 1940px;
  border-collapse: collapse;
  table-layout: fixed;
  font-size: 13px;
}

.native-table th,
.native-table td {
  border: 1px solid var(--el-border-color, #dcdfe6);
  padding: 4px 6px;
  vertical-align: top;
  word-break: break-all;
  white-space: pre-wrap;
}

.native-table thead tr {
  background-color: var(--el-fill-color-light, #f5f7fa);
}

.native-table th {
  font-weight: 600;
  color: var(--el-text-color-regular, #606266);
  text-align: center;
  white-space: nowrap;
  padding: 8px 6px;
}

.native-table tbody tr:hover {
  background-color: var(--el-fill-color-lighter, #fafafa);
}

.cell-center {
  text-align: center;
  vertical-align: middle !important;
}

.add-row-bar {
  display: flex;
  justify-content: center;
  padding: 6px 0;
}

/* el-input textarea 撑开单元格高度 */
:deep(.el-textarea__inner) {
  min-height: auto !important;
  font-size: 13px;
  line-height: 1.5;
  resize: none;
}

:deep(.el-input__wrapper) {
  padding: 1px 8px;
}

:deep(.el-select) {
  width: 100%;
}

/* 对话框铺满宽度，body 可滚动 */
.batch-dialog :deep(.el-dialog) {
  margin-top: 1vh !important;
  max-height: calc(100vh - 2vh);
  display: flex;
  flex-direction: column;
}

.batch-dialog :deep(.el-dialog__body) {
  padding: 12px 16px;
  overflow-y: auto;
  flex: 1;
}

.batch-dialog :deep(.el-dialog__footer) {
  flex-shrink: 0;
}
</style>
