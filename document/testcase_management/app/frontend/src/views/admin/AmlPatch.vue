<template>
  <div class="aml-patch-container">
    <div class="toolbar">
      <div class="header-actions">
        <el-button v-if="hasButton('amlPatch', 'create')" type="primary" @click="handleCreate">
          <el-icon><Plus /></el-icon>
          {{ $t('amlPatch.create') }}
        </el-button>
        <el-button @click="handleExport">
          <el-icon><Upload /></el-icon>
          导出
        </el-button>
        <el-button v-if="isSuperAdmin || isAdmin" type="warning" :loading="syncing" @click="handleSync">
          <el-icon><Refresh /></el-icon>
          {{ $t('amlPatch.sync') }}
        </el-button>
      </div>
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          :placeholder="$t('amlPatch.searchPlaceholder')"
          clearable
          @keyup.enter="handleSearch"
          class="search-input"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="projectFilter" :placeholder="$t('amlPatch.projectPlaceholder')" clearable class="project-select">
            <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.name" />
            <div class="add-project-btn" @click="handleAddProject">
              <el-icon><Plus /></el-icon>
              添加项目
            </div>
          </el-select>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>
    </div>

    <div class="table-container" ref="tableContainerRef">
      <el-table
        ref="tableRef"
        :data="tableData"
        v-loading="loading"
        :cell-style="tableCellStyle"
        border
        style="width: 100%"
        height="100%"
        header-fixed
        @row-click="handleRowClick"
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="project" :label="$t('amlPatch.project')" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.project }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="feature_branch" :label="$t('amlPatch.featureBranch')" min-width="150">
          <template #default="{ row }">
            <el-tooltip :content="row.feature_branch" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.feature_branch }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="corresponding_directory" :label="$t('amlPatch.correspondingDirectory')" min-width="150">
          <template #default="{ row }">
            <el-tooltip :content="row.corresponding_directory" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.corresponding_directory }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="commit_record" :label="$t('amlPatch.commitRecord')" min-width="250">
          <template #default="{ row }">
            <el-tooltip placement="top" :show-after="500">
              <template #content><pre class="tooltip-pre">{{ row.commit_record }}</pre></template>
              <div class="cell-ellipsis-single">{{ row.commit_record }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('amlPatch.zmindNumber')" min-width="180">
          <template #default="{ row }">
            <div v-if="!row.zmind_numbers || row.zmind_numbers.length === 0">-</div>
            <el-tooltip v-else :content="row.zmind_numbers.join(', ')" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.zmind_numbers.join(', ') }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="amlogic_jira" :label="$t('amlPatch.amlogicJira')" min-width="140">
          <template #default="{ row }">
            <el-tooltip :content="row.amlogic_jira" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.amlogic_jira }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="patch_provider" :label="$t('amlPatch.patchProvider')" min-width="160">
          <template #default="{ row }">
            <el-tooltip :content="row.patch_provider" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.patch_provider }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column :label="$t('amlPatch.isOdmExclusive')" width="120">
          <template #default="{ row }">
            <el-tag :type="row.is_odm_exclusive === '是' ? 'success' : 'danger'">
              {{ row.is_odm_exclusive || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="aml_sri_result" :label="$t('amlPatch.amlSriResult')" min-width="180">
          <template #default="{ row }">
            <el-tooltip :content="row.aml_sri_result" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.aml_sri_result }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="patch_solution" :label="$t('amlPatch.patchSolution')" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.patch_solution" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.patch_solution }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="root_cause" :label="$t('amlPatch.rootCause')" min-width="180">
          <template #default="{ row }">
            <el-tooltip :content="row.root_cause" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.root_cause }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="impact_scope" :label="$t('amlPatch.impactScope')" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.impact_scope" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.impact_scope }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="zeasn_merge_record" :label="$t('amlPatch.zeasnMergeRecord')" min-width="180">
          <template #default="{ row }">
            <el-tooltip :content="row.zeasn_merge_record" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.zeasn_merge_record }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="remarks" :label="$t('amlPatch.remarks')" min-width="180">
          <template #default="{ row }">
            <el-tooltip :content="row.remarks" placement="top" :show-after="500">
              <div class="cell-ellipsis-single">{{ row.remarks }}</div>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" :label="$t('common.updatedAt')" width="180">
          <template #default="{ row }">
            {{ row.updated_at || row.created_at || '-' }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button v-if="hasButton('amlPatch', 'edit')" type="primary" link @click.stop="handleEdit(row)">
              <el-icon><Edit /></el-icon>
            </el-button>
            <el-button v-if="hasButton('amlPatch', 'delete')" type="danger" link @click.stop="handleDelete(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? $t('amlPatch.edit') : $t('amlPatch.create')"
      width="90%"
      class="aml-patch-detail-dialog"
      @close="handleDialogClose"
    >
      <div class="form-content" v-if="dialogVisible">
        <el-descriptions :column="2" border>
          <el-descriptions-item>
            <template #label>项目<span class="required">*</span></template>
            <el-select v-model="formData.project" :placeholder="$t('amlPatch.projectPlaceholder')" style="width: 100%">
              <el-option v-for="p in projectList" :key="p.id" :label="p.name" :value="p.name" />
            </el-select>
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>代码分支<span class="required">*</span></template>
            <el-input v-model="formData.feature_branch" :placeholder="$t('amlPatch.featureBranchPlaceholder')" />
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>该ODM专属<span class="required">*</span></template>
            <el-radio-group v-model="formData.is_odm_exclusive">
              <el-radio value="是">{{ $t('amlPatch.yes') }}</el-radio>
              <el-radio value="否">{{ $t('amlPatch.no') }}</el-radio>
            </el-radio-group>
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label><span style="white-space: pre-wrap;">Aml SRI自测结果（仅针对单case）</span><span class="required">*</span></template>
            <el-radio-group v-model="formData.aml_sri_result">
              <el-radio value="Pass">Pass</el-radio>
              <el-radio value="Failed">Failed</el-radio>
              <el-radio value="无法测试">无法测试</el-radio>
              <el-radio value="未测试">未测试</el-radio>
            </el-radio-group>
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>Zmind号<span class="required">*</span></template>
            <el-input v-model="formData.zmind_numbers" type="textarea" :rows="3" placeholder="多个Zmind号用英文逗号或中文逗号分隔" maxlength="1000" />
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>代码路径<span class="required">*</span></template>
            <el-input v-model="formData.corresponding_directory" type="textarea" :rows="3" :placeholder="$t('amlPatch.correspondingDirectoryPlaceholder')" />
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>Amlogic Jira<span class="required">*</span></template>
            <el-input v-model="formData.amlogic_jira" :placeholder="$t('amlPatch.amlogicJiraPlaceholder')" />
          </el-descriptions-item>
          <el-descriptions-item>
            <template #label>patch提供人<span class="required">*</span></template>
            <el-input v-model="formData.patch_provider" :placeholder="$t('amlPatch.patchProviderPlaceholder')" />
          </el-descriptions-item>
          <el-descriptions-item :span="2">
            <template #label>commit message<span class="required">*</span></template>
            <el-input v-model="formData.commit_record" type="textarea" :rows="3" :placeholder="$t('amlPatch.commitRecordPlaceholder') + '（必须带上 Change-Id）'" />
          </el-descriptions-item>
          <el-descriptions-item :span="2">
            <template #label>Root Cause<span class="required">*</span></template>
            <el-input v-model="formData.root_cause" type="textarea" :rows="3" :placeholder="$t('amlPatch.rootCausePlaceholder')" maxlength="5000" show-word-limit />
          </el-descriptions-item>
          <el-descriptions-item :span="2">
            <template #label>解决方案<span class="required">*</span></template>
            <el-input v-model="formData.patch_solution" type="textarea" :rows="3" :placeholder="$t('amlPatch.patchSolutionPlaceholder')" maxlength="5000" show-word-limit />
          </el-descriptions-item>
          <el-descriptions-item :span="2">
            <template #label>推荐测试范围<span class="required">*</span></template>
            <el-input v-model="formData.impact_scope" type="textarea" :rows="3" :placeholder="$t('amlPatch.impactScopePlaceholder')" maxlength="5000" show-word-limit />
          </el-descriptions-item>
          <el-descriptions-item :span="2">
            <template #label>Zeasn合入记录</template>
            <el-input v-model="formData.zeasn_merge_record" type="textarea" :rows="3" :placeholder="$t('amlPatch.zeasnMergeRecordPlaceholder')" maxlength="5000" show-word-limit />
          </el-descriptions-item>
          <el-descriptions-item :span="2">
            <template #label>备注</template>
            <el-input v-model="formData.remarks" type="textarea" :rows="3" :placeholder="$t('amlPatch.remarksPlaceholder')" maxlength="5000" show-word-limit />
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog
      v-model="detailVisible"
      title="Patch详情"
      width="90%"
      class="aml-patch-detail-dialog"
    >
      <div class="detail-content" v-if="detailData">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="序号">{{ detailData.id }}</el-descriptions-item>
          <el-descriptions-item label="项目">
            <el-tag>{{ detailData.project }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="代码分支">{{ detailData.feature_branch || '-' }}</el-descriptions-item>
<el-descriptions-item label="该ODM专属">
            <el-tag :type="detailData.is_odm_exclusive === '是' ? 'success' : 'danger'">{{ detailData.is_odm_exclusive || '-' }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item><template #label><span style="white-space: pre-wrap;">Aml SRI自测结果（仅针对单case）</span></template>{{ detailData.aml_sri_result || '-' }}</el-descriptions-item>
          <el-descriptions-item label="patch提供人">{{ detailData.patch_provider || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Zmind号">
            <span v-if="!detailData.zmind_numbers || detailData.zmind_numbers.length === 0">-</span>
            <template v-else>
              <div class="detail-zmind-list">
                <template v-for="(num, idx) in detailData.zmind_numbers" :key="idx">
                  <a :href="`https://zmind.whaletv.com/issues/${num}`" target="_blank" class="zmind-link">{{ num }}</a><span v-if="idx < detailData.zmind_numbers.length - 1" class="zmind-separator">, </span>
                </template>
              </div>
            </template>
          </el-descriptions-item>
          <el-descriptions-item label="代码路径">{{ detailData.corresponding_directory || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Amlogic Jira">{{ detailData.amlogic_jira || '-' }}</el-descriptions-item>
          <el-descriptions-item label="更新时间">{{ detailData.updated_at || detailData.created_at || '-' }}</el-descriptions-item>
          <el-descriptions-item label="commit message" :span="2">
            <div class="copy-field commit-message-field">
              <pre class="commit-message-pre" v-html="renderCommitMessage(detailData.commit_record)"></pre>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="Root Cause" :span="2">
            <div class="copy-field">
              <span>{{ detailData.root_cause || '-' }}</span>
              <el-tooltip content="复制" placement="top" :show-after="500">
                <el-button type="primary" link @click="() => copyToClipboard(detailData?.root_cause)" class="copy-btn">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="解决方案" :span="2">
            <div class="copy-field">
              <span>{{ detailData.patch_solution || '-' }}</span>
              <el-tooltip content="复制" placement="top" :show-after="500">
                <el-button type="primary" link @click="() => copyToClipboard(detailData?.patch_solution)" class="copy-btn">
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </el-descriptions-item>
          <el-descriptions-item label="推荐测试范围" :span="2">{{ detailData.impact_scope || '-' }}</el-descriptions-item>
          <el-descriptions-item label="Zeasn合入记录" :span="2">{{ detailData.zeasn_merge_record || '-' }}</el-descriptions-item>
          <el-descriptions-item label="备注" :span="2">{{ detailData.remarks || '-' }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="detailVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox, ElTooltip } from 'element-plus'
import { Plus, Search, Edit, Delete, Download, Upload, CopyDocument, Refresh } from '@element-plus/icons-vue'
import { useUserRole } from '../../composables/useUserRole'
import { debounce } from 'lodash-es'

const { t } = useI18n()
const { hasButton, isSuperAdmin, isAdmin } = useUserRole()

const tableContainerRef = ref(null)
const tableRef = ref(null)

const loading = ref(false)
const syncing = ref(false)
const submitLoading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const searchQuery = ref('')
const projectFilter = ref('')
const projectList = ref([])

const fetchProjects = async () => {
  try {
    const response = await fetch('/api/aml-patch/projects', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    if (response.ok) {
      const result = await response.json()
      projectList.value = result.data || []
    }
  } catch (error) {
    console.error('Failed to fetch projects:', error)
  }
}

const handleAddProject = async () => {
  const { value: projectName } = await ElMessageBox.prompt('请输入项目名称', '添加项目', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    inputPattern: /.+/,
    inputErrorMessage: '项目名称不能为空'
  })
  if (projectName) {
    try {
      const response = await fetch('/api/aml-patch/projects', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ name: projectName })
      })
      if (response.ok) {
        ElMessage.success(t('common.saveSuccess'))
        fetchProjects()
      } else {
        const error = await response.json()
        ElMessage.error(error.detail || '添加失败')
      }
    } catch (error) {
      ElMessage.error('添加失败')
    }
  }
}

const dialogVisible = ref(false)
const detailVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const detailData = ref(null)
const formRef = ref(null)

const formData = reactive({
  project: '',
  feature_branch: '',
  corresponding_directory: '',
  commit_record: '',
  zmind_numbers: '',
  amlogic_jira: '',
  patch_provider: '',
  is_odm_exclusive: '',
  root_cause: '',
  patch_solution: '',
  impact_scope: '',
  aml_sri_result: '',
  zeasn_merge_record: '',
  remarks: ''
})

const formRules = {
  project: [{ required: true, message: '请选择项目', trigger: 'change' }],
  feature_branch: [{ required: true, message: '请输入代码分支', trigger: 'blur' }],
  corresponding_directory: [{ required: true, message: '请输入代码路径', trigger: 'blur' }],
  commit_record: [{ required: true, message: '请输入commit message', trigger: 'blur' }],
  amlogic_jira: [{ required: true, message: '请输入Amlogic Jira', trigger: 'blur' }],
  patch_provider: [{ required: true, message: '请输入patch提供人', trigger: 'blur' }],
  is_odm_exclusive: [{ required: true, message: '请选择是否该ODM专属', trigger: 'change' }],
  patch_solution: [{ required: true, message: '请输入解决方案', trigger: 'blur' }],
  root_cause: [{ required: true, message: '请输入Root Cause', trigger: 'blur' }],
  impact_scope: [{ required: true, message: '请输入推荐测试范围', trigger: 'blur' }],
  aml_sri_result: [{ required: true, message: '请输入Aml SRI自测结果（仅针对单case）', trigger: 'blur' }]
}

const tableCellStyle = ({ row, column }) => {
  return {
    padding: '8px 12px',
    lineHeight: '1.6'
  }
}

const fetchData = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: currentPage.value,
      page_size: pageSize.value
    })
    if (projectFilter.value) {
      params.append('project', projectFilter.value)
    }
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    
    const response = await fetch(`/api/aml-patch?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to fetch data')
    }
    
    const result = await response.json()
    tableData.value = result.data || []
    total.value = result.total || 0
  } catch (error) {
    ElMessage.error(error.message || '加载数据失败')
  } finally {
    loading.value = false
  }
}

const debouncedSearch = debounce(() => {
  currentPage.value = 1
  fetchData()
}, 500)

const debouncedProjectFilter = debounce(() => {
  currentPage.value = 1
  fetchData()
}, 500)

watch(searchQuery, () => {
  debouncedSearch()
})

watch(projectFilter, () => {
  debouncedProjectFilter()
})

const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

const handleExport = async () => {
  try {
    const params = new URLSearchParams()
    if (projectFilter.value) {
      params.append('project', projectFilter.value)
    }
    if (searchQuery.value) {
      params.append('search', searchQuery.value)
    }
    
    const response = await fetch(`/api/aml-patch/export?${params}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('导出失败')
    }
    
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `aml_patch_${new Date().toISOString().slice(0, 10)}.csv`
    document.body.appendChild(a)
    a.click()
    window.URL.revokeObjectURL(url)
    document.body.removeChild(a)
    ElMessage.success(t('common.exportSuccess'))
  } catch (error) {
    ElMessage.error(t('common.exportFailed'))
  }
}

const handleSync = async () => {
  try {
    await ElMessageBox.confirm(t('amlPatch.syncConfirm'), t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
  } catch {
    return
  }
  syncing.value = true
  try {
    const response = await fetch('/api/aml-patch/sync', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''

    }
    ElMessage.success(t('amlPatch.syncSuccess'))
    fetchData()
  } catch (error) {
    ElMessage.error(t('amlPatch.syncFailed'))
  } finally {
    syncing.value = false
  }
}

const handlePageChange = (page) => {
  currentPage.value = page
  fetchData()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  fetchData()
}

const handleRowClick = (row) => {
  detailData.value = row
  detailVisible.value = true
}

const renderCommitMessage = (commitRecord) => {
  if (!commitRecord) return '-'
  // Escape HTML special chars first
  const escaped = commitRecord
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  // Replace Change-Id value with a clickable link (in-place, same line)
  return escaped.replace(
    /(Change-Id:\s*)(I[0-9a-fA-F]+)/gi,
    (_, prefix, id) =>
      `${prefix}<a href="https://whale-gerrit.zeasn.com/q/${id}" target="_blank" class="change-id-link">${id}</a>`
  )
}

const copyToClipboard = (text) => {
  if (!text) {
    ElMessage.warning('没有内容可复制')
    return
  }
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).then(() => {
      ElMessage.success(t('common.copySuccess'))
    }).catch(() => {
      fallbackCopy(text)
    })
  } else {
    fallbackCopy(text)
  }
}

const fallbackCopy = (text) => {
  const textArea = document.createElement('textarea')
  textArea.value = text
  textArea.style.position = 'fixed'
  textArea.style.left = '-9999px'
  document.body.appendChild(textArea)
  textArea.select()
  try {
    document.execCommand('copy')
    ElMessage.success(t('common.copySuccess'))
  } catch (err) {
    ElMessage.error(t('common.copyFailed'))
  }
  document.body.removeChild(textArea)
}

const handleCreate = () => {
  isEdit.value = false
  editingId.value = null
  resetForm()
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  editingId.value = row.id
  formData.project = row.project || ''
  formData.feature_branch = row.feature_branch || ''
  formData.corresponding_directory = row.corresponding_directory || ''
  formData.commit_record = row.commit_record || ''
  formData.zmind_numbers = row.zmind_numbers && row.zmind_numbers.length > 0 ? row.zmind_numbers.join(', ') : ''
  formData.amlogic_jira = row.amlogic_jira || ''
  formData.patch_provider = row.patch_provider || ''
  formData.is_odm_exclusive = row.is_odm_exclusive || ''
  formData.root_cause = row.root_cause || ''
  formData.patch_solution = row.patch_solution || ''
  formData.impact_scope = row.impact_scope || ''
  formData.aml_sri_result = row.aml_sri_result || ''
  formData.zeasn_merge_record = row.zeasn_merge_record || ''
  formData.remarks = row.remarks || ''
  dialogVisible.value = true
}

const handleDelete = (row) => {
  ElMessageBox.confirm(
    t('amlPatch.deleteConfirm'),
    t('common.warning'),
    {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    }
  ).then(async () => {
    try {
      const response = await fetch(`/api/aml-patch/${row.id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to delete')
      }
      
      ElMessage.success(t('amlPatch.deleteSuccess'))
      fetchData()
    } catch (error) {
      ElMessage.error(error.message || '删除失败')
    }
  }).catch(() => {})
}

const resetForm = () => {
  formData.project = ''
  formData.feature_branch = ''
  formData.corresponding_directory = ''
  formData.commit_record = ''
  formData.zmind_numbers = ''
  formData.amlogic_jira = ''
  formData.patch_provider = ''
  formData.is_odm_exclusive = ''
  formData.root_cause = ''
  formData.patch_solution = ''
  formData.impact_scope = ''
  formData.aml_sri_result = ''
  formData.zeasn_merge_record = ''
  formData.remarks = ''
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  resetForm()
}

const handleSubmit = async () => {
  const requiredFields = [
    { key: 'project', label: '项目' },
    { key: 'feature_branch', label: '代码分支' },
    { key: 'corresponding_directory', label: '代码路径' },
    { key: 'commit_record', label: 'commit message' },
    { key: 'amlogic_jira', label: 'Amlogic Jira' },
    { key: 'patch_provider', label: 'patch提供人' },
    { key: 'is_odm_exclusive', label: '该ODM专属' },
    { key: 'patch_solution', label: '解决方案' },
    { key: 'root_cause', label: 'Root Cause' },
    { key: 'impact_scope', label: '推荐测试范围' },
    { key: 'aml_sri_result', label: 'Aml SRI自测结果（仅针对单case）' },
    { key: 'zmind_numbers', label: 'Zmind号', customCheck: () => (formData.zmind_numbers || '').trim() !== '' }
  ]
  
  const missing = requiredFields.filter(f => {
    if (f.customCheck) return !f.customCheck()
    return !formData[f.key]
  })
  if (missing.length > 0) {
    ElMessage.error(`请填写以下必填字段：${missing.map(f => f.label).join('、')}`)
    return
  }
  
  submitLoading.value = true
    
    const zmindStr = formData.zmind_numbers || ''
    const zmindNumbers = zmindStr.split(/[,，]/).map(n => n.trim()).filter(n => n !== '')
    
    const payload = {
      project: formData.project,
      feature_branch: formData.feature_branch || null,
      corresponding_directory: formData.corresponding_directory || null,
      commit_record: formData.commit_record || null,
      zmind_numbers: zmindNumbers,
      amlogic_jira: formData.amlogic_jira || null,
      patch_provider: formData.patch_provider || null,
      is_odm_exclusive: formData.is_odm_exclusive || null,
      root_cause: formData.root_cause || null,
      patch_solution: formData.patch_solution || null,
      impact_scope: formData.impact_scope || null,
      aml_sri_result: formData.aml_sri_result || null,
      zeasn_merge_record: formData.zeasn_merge_record || null,
      remarks: formData.remarks || null
    }
    
    const url = isEdit.value ? `/api/aml-patch/${editingId.value}` : '/api/aml-patch'
    const method = isEdit.value ? 'PUT' : 'POST'

    try {
    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })
    
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to save')
    }
    
    ElMessage.success(isEdit.value ? t('amlPatch.updateSuccess') : t('amlPatch.createSuccess'))
    dialogVisible.value = false
    fetchData()
  } catch (error) {
    console.error('Submit error:', error)
    ElMessage.error(error.message || '保存失败')
  } finally {
    submitLoading.value = false
  }
}

onMounted(() => {
  fetchData()
  fetchProjects()
})
</script>

<style scoped>
.aml-patch-container {
  padding: 24px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  flex-shrink: 0;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-input {
  width: 200px;
}

.search-input :deep(.el-input__wrapper) {
  height: 32px;
  line-height: 32px;
}

.project-select {
  width: 150px;
}

.project-select :deep(.el-select__wrapper) {
  height: 32px;
}

.add-project-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  cursor: pointer;
  color: #409eff;
  border-top: 1px solid #eee;
}

.add-project-btn:hover {
  background-color: #f5f7fa;
}

.table-container {
  flex: 1;
  overflow: auto;
}

.table-container .el-table__body-wrapper::-webkit-scrollbar {
  height: 12px;
}

.table-container .el-table__body-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 6px;
}

.table-container .el-table__body-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 6px;
}

.multi-line-cell {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.cell-ellipsis-single {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: normal;
  line-height: 1.5;
}

/* Keep old class for any remaining references */
.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  word-break: normal;
  line-height: 1.5;
}

/* 强制覆盖global.css */
.aml-patch-container .cell-ellipsis-single,
.aml-patch-container .cell-ellipsis {
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  word-break: normal !important;
  line-height: 1.5 !important;
  height: auto !important;
  display: block !important;
}

.zmind-tags {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.zmind-span {
  display: block;
}

.zmind-link {
  color: #409EFF;
  text-decoration: none;
}

.zmind-link:hover {
  text-decoration: underline;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  flex-shrink: 0;
}

.zmind-inputs {
  width: 100%;
}

.form-grid {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-row {
  display: flex;
  gap: 20px;
}

.form-row.full {
  flex-direction: column;
}

.form-col {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.form-col > label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-col .required {
  color: #f56c6c;
  margin-left: 4px;
}

.form-item > label {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
  margin-bottom: 6px;
}

.form-item .required {
  color: #f56c6c;
}

.form-item :deep(.el-form-item) {
  margin-bottom: 0;
}

.form-item :deep(.el-form-item__content) {
  margin-left: 0 !important;
}

.form-item .el-input__wrapper,
.form-item .el-select__wrapper,
.form-item .el-textarea__inner {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.form-item .el-input__wrapper:hover,
.form-item .el-select__wrapper:hover,
.form-item .el-textarea__inner:hover {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.form-item .el-input__wrapper.is-focus,
.form-item .el-select__wrapper.is-focus,
.form-item .el-textarea__inner:focus {
  box-shadow: 0 0 0 1px #409eff inset;
}
</style>

<style>
.aml-patch-detail-dialog .el-dialog__body {
  max-height: 70vh;
  overflow-y: auto;
}

.aml-patch-detail-dialog {
  max-width: 1200px;
}

.aml-patch-detail-dialog .el-descriptions__label {
  width: 150px !important;
  min-width: 150px !important;
  flex-shrink: 0 !important;
}

.aml-patch-detail-dialog .el-descriptions__cell {
  min-width: 200px;
}

.form-content :deep(.el-descriptions__cell) {
  padding: 12px 15px;
}

.form-content :deep(.el-input),
.form-content :deep(.el-textarea__inner),
.form-content :deep(.el-select__wrapper) {
  width: 100%;
}

.form-content :deep(.el-radio-group) {
  display: flex;
  gap: 20px;
}

.form-content :deep(.el-descriptions-item__label) {
  display: flex;
  align-items: center;
}

.form-content .required {
  color: #f56c6c;
  margin-right: 4px;
}

.zmind-inputs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.zmind-input-row {
  display: flex;
  gap: 8px;
  align-items: center;
  width: calc(25% - 4px);
}

.zmind-input-row .el-input {
  flex: 1;
  min-width: 100px;
}

.form-content .required {
  color: #f56c6c;
  margin-right: 4px;
}
</style>

<style>
/* 表格容器 */
.aml-patch-container .table-container {
  flex: 1;
  overflow: auto;
}

.aml-patch-container .el-table {
  width: 100%;
  table-layout: auto;
}

/* 表格头部样式 - 覆盖global.css */
.aml-patch-container .el-table th.el-table__cell .cell {
  background: #f8fafc !important;
  color: #64748b !important;
  font-weight: 500 !important;
  white-space: normal !important;
  overflow: visible !important;
  text-overflow: unset !important;
  padding: 8px 12px;
  height: auto !important;
}

/* 单元格内容 - 让tooltip正常工作 */
.aml-patch-container .el-table td.el-table__cell .cell {
  white-space: normal !important;
  overflow: hidden !important;
  line-height: 1.5 !important;
  padding: 8px 12px;
  height: auto !important;
  display: block !important;
}

/* 确保tooltip不被遮挡 */
.aml-patch-container .el-tooltip__popper {
  z-index: 10000 !important;
}

.zmind-link {
  color: #409eff;
  text-decoration: none;
  margin-right: 8px;
}

.zmind-link:hover {
  text-decoration: underline;
}

.tooltip-pre {
  margin: 0;
  font-family: inherit;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-word;
  max-width: 400px;
  line-height: 1.5;
}

.change-id-link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.change-id-link:hover {
  text-decoration: underline;
}

.detail-zmind-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.copy-field {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.commit-message-field {
  flex-direction: column;
  gap: 6px;
}

.commit-message-pre {
  margin: 0;
  font-family: inherit;
  font-size: 13px;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
  color: inherit;
}

.change-id-link {
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.change-id-link:hover {
  text-decoration: underline;
}


.copy-btn {
  flex-shrink: 0;
}
</style>