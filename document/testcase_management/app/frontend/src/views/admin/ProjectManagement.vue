<template>
  <div class="project-page">
    <el-card class="table-card" shadow="never">
      <div class="table-header">
        <div class="header-left">
          <div class="action-buttons">
            <el-button 
              v-if="hasButton('projects', 'create')"
              type="primary" 
              :icon="Plus" 
              @click="handleCreate"
            >
              {{ $t('project.createProject') }}
            </el-button>
            <el-button 
              :icon="Document" 
              @click="openNamingRuleDialog"
            >
              命名规则
            </el-button>
          </div>
        </div>
        <div class="header-right">
          <el-select
            v-model="filterTeamId"
            :placeholder="$t('project.filterByTeam')"
            clearable
            size="large"
            style="width: 180px;"
            @change="handleFilterChange"
          >
            <el-option
              v-for="team in userTeams"
              :key="team.id"
              :label="team.name"
              :value="team.id"
            />
          </el-select>
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('project.searchPlaceholder')"
            size="large"
            style="width: 250px;"
            clearable
            @clear="handleSearch"
            @keyup.enter="handleSearch"
          >
            <template #suffix>
              <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleSearch">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <div class="table-wrapper">
        <div class="table-container" ref="tableContainerRef">
          <el-table 
            ref="tableRef"
            :data="tableData" 
            style="width: 100%"
            :height="tableHeight"
            :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
          >
            <el-table-column prop="name" :label="$t('project.name')" min-width="150" align="center">
              <template #default="scope">
                <el-tooltip :content="scope.row.name + (scope.row.tag ? ' (' + scope.row.tag + ')' : '')" placement="top" :teleported="true" :show-after="500">
                  <div class="project-name-cell" @click="handleProjectNameClick(scope.row)">
                    <span class="project-name">{{ scope.row.name }}</span>
                    <span v-if="scope.row.tag" class="project-tag">({{ scope.row.tag }})</span>
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column :label="$t('project.authorizedTeams')" min-width="180">
              <template #default="scope">
                <div v-if="scope.row.authorized_teams && scope.row.authorized_teams.length > 0" class="tag-cell">
                  <el-tag type="info" size="small" class="cell-tag">{{ scope.row.authorized_teams[0].name }}</el-tag>
                  <el-tooltip v-if="scope.row.authorized_teams.length > 1" effect="dark" placement="top" :show-after="500">
                    <template #content>
                      <div v-for="(team, idx) in scope.row.authorized_teams" :key="idx">{{ team.name }}</div>
                    </template>
                    <el-tag type="info" size="small" class="cell-tag-more">+{{ scope.row.authorized_teams.length - 1 }}</el-tag>
                  </el-tooltip>
                </div>
                <span v-else class="text-muted">{{ $t('project.unauthorized') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="creator_name" :label="$t('project.creator')" min-width="120" align="center">
              <template #default="scope">
                <el-tooltip :content="scope.row.creator_name || '-'" placement="top" :teleported="true" :show-after="500">
                  <span class="creator-name">{{ scope.row.creator_name || '-' }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="status" :label="$t('common.status')" min-width="100" align="center">
              <template #default="scope">
                <el-tag 
                  :type="scope.row.status === 1 ? 'success' : 'info'" 
                  effect="light"
                  size="small"
                  style="cursor: pointer;"
                  @click="handleStatusChange(scope.row)"
                >
                  {{ scope.row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" :label="$t('common.createdAt')" min-width="160" align="center">
              <template #default="scope">
                <el-tooltip :content="formatDate(scope.row.created_at)" placement="top" :teleported="true" :show-after="500">
                  <span class="created-at">{{ formatDate(scope.row.created_at) }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="description" :label="$t('common.description')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
            <el-table-column :label="$t('common.operation')" width="240" align="center" fixed="right">
              <template #default="scope">
                <el-button 
                  v-if="hasButton('projects', 'edit')"
                  type="primary" 
                  size="default" 
                  :icon="Edit"
                  @click="handleEdit(scope.row)"
                >
                  {{ $t('common.edit') }}
                </el-button>
                <el-button 
                  v-if="hasButton('projects', 'delete')"
                  type="danger" 
                  size="default" 
                  :icon="Delete"
                  @click="handleDelete(scope.row)"
                >
                  {{ $t('common.delete') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="600px"
      :close-on-click-modal="false"
      :show-close="true"
      @closed="handleDialogClosed"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px" label-position="top">
        <el-form-item :label="$t('project.name')" prop="name" required>
          <el-input 
            v-model="form.name" 
            :placeholder="$t('project.inputName')"
            maxlength="100"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="Tag" :required="!form.id || canEditTag" :rules="tagRules">
          <el-input 
            v-model="form.tag" 
            :placeholder="form.id && !canEditTag ? '' : '用于用例编号生成，如：OS'"
            :maxlength="50"
            :disabled="!!form.id && !canEditTag"
            :show-word-limit="!form.id || canEditTag"
          />
          <div class="form-tip" v-if="!form.id">
            用于用例编号生成，格式：{用例库Tag}+{模块Tag}+{序号}，建议使用简洁的英文缩写
            <br>
            <span style="color: #e6a23c;">注意：Tag创建后不可修改，请谨慎填写</span>
          </div>
          <div class="form-tip" v-else-if="canEditTag" style="color: #e6a23c;">Tag创建后不可修改</div>
          <div class="form-tip" v-else style="color: #909399;">Tag创建后不可修改</div>
        </el-form-item>
        <el-form-item :label="$t('project.authorizeTeam')" prop="team_ids" required>
          <el-select
            v-model="form.team_ids"
            multiple
            :placeholder="$t('project.selectTeam')"
            style="width: 100%"
            filterable
            collapse-tags
            collapse-tags-tooltip
            value-key="id"
          >
            <el-option
              v-for="team in allTeams"
              :key="team.id"
              :label="team.name"
              :value="team.id"
            />
          </el-select>
          <div class="form-tip">{{ $t('project.selectedTeamCount', { count: Array.isArray(form.team_ids) ? form.team_ids.length : 0 }) }}</div>
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="4"
            :placeholder="$t('project.inputDescription')"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('project.projectStatus')">
          <el-switch
            v-model="form.status"
            :active-value="1"
            :inactive-value="0"
            :active-text="$t('common.enabled')"
            :inactive-text="$t('common.disabled')"
            inline-prompt
            style="--el-switch-on-color: #4f46e5; --el-switch-off-color: #cbd5e1"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 命名规则对话框 -->
    <el-dialog
      v-model="namingRuleVisible"
      title="用例编号命名规则"
      width="900px"
      top="5vh"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <div class="naming-rule-content" v-loading="namingRuleLoading">
        <!-- 格式说明 -->
        <div class="rule-section">
          <div class="rule-section-title">命名格式</div>
          <div v-if="!namingRuleEditing" class="rule-format-box">
            <pre class="rule-format-text">{{ namingRuleData.format_description }}</pre>
          </div>
          <el-input
            v-else
            v-model="namingRuleData.format_description"
            type="textarea"
            :rows="3"
            placeholder="输入命名格式说明"
          />
        </div>

        <!-- 用例库代号表 -->
        <div class="rule-section">
          <div class="rule-section-title">
            用例库代号
            <span class="rule-count">{{ filteredProjectCodes.length }} / {{ namingRuleData.project_codes?.length || 0 }} 项</span>
          </div>
          <el-input
            v-model="projectCodeSearch"
            placeholder="搜索用例库名称或代号"
            clearable
            size="small"
            style="margin-bottom: 8px; width: 300px;"
            :prefix-icon="Search"
          />
          <el-table :data="filteredProjectCodes" border size="small" class="rule-table">
            <el-table-column prop="name" label="用例库" min-width="200">
              <template #default="{ row }">
                <el-input v-if="namingRuleEditing" v-model="row.name" size="small" />
                <span v-else>{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="code" label="代号" width="150">
              <template #default="{ row }">
                <el-input v-if="namingRuleEditing" v-model="row.code" size="small" />
                <span v-else>{{ row.code }}</span>
              </template>
            </el-table-column>
            <el-table-column v-if="namingRuleEditing" label="" width="60" align="center">
              <template #default="{ row }">
                <el-button type="danger" link size="small" @click="removeProjectCode(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button v-if="namingRuleEditing" size="small" @click="namingRuleData.project_codes.push({ name: '', code: '' })" style="margin-top: 8px;">
            <el-icon><Plus /></el-icon> 添加用例库
          </el-button>
        </div>

        <!-- 模块代号表 -->
        <div class="rule-section">
          <div class="rule-section-title">
            父模块代号
            <span class="rule-count">{{ filteredModuleCodes.length }} / {{ namingRuleData.module_codes?.length || 0 }} 项</span>
          </div>
          <el-input
            v-model="moduleCodeSearch"
            placeholder="搜索模块名称或代号"
            clearable
            size="small"
            style="margin-bottom: 8px; width: 300px;"
            :prefix-icon="Search"
          />
          <el-table :data="filteredModuleCodes" border size="small" class="rule-table" max-height="400">
            <el-table-column prop="name" label="父模块" min-width="160">
              <template #default="{ row }">
                <el-input v-if="namingRuleEditing" v-model="row.name" size="small" />
                <span v-else>{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="code" label="代号" width="120">
              <template #default="{ row }">
                <el-input v-if="namingRuleEditing" v-model="row.code" size="small" />
                <span v-else>{{ row.code }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="logic" label="命名逻辑" min-width="280">
              <template #default="{ row }">
                <el-input v-if="namingRuleEditing" v-model="row.logic" size="small" />
                <span v-else class="logic-text">{{ row.logic }}</span>
              </template>
            </el-table-column>
            <el-table-column v-if="namingRuleEditing" label="" width="60" align="center">
              <template #default="{ row }">
                <el-button type="danger" link size="small" @click="removeModuleCode(row)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button v-if="namingRuleEditing" size="small" @click="namingRuleData.module_codes.push({ name: '', code: '', logic: '' })" style="margin-top: 8px;">
            <el-icon><Plus /></el-icon> 添加模块
          </el-button>
        </div>
      </div>

      <template #footer>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span v-if="namingRuleUpdatedAt" style="color: #909399; font-size: 12px;">
            最后更新：{{ formatDate(namingRuleUpdatedAt) }}
          </span>
          <span v-else></span>
          <div>
            <template v-if="namingRuleEditing">
              <el-button @click="cancelNamingRuleEdit">取消</el-button>
              <el-button type="primary" @click="saveNamingRule" :loading="namingRuleSaving">保存</el-button>
            </template>
            <template v-else>
              <el-button v-if="canEditNamingRule" type="primary" @click="namingRuleEditing = true">
                <el-icon><Edit /></el-icon> 编辑
              </el-button>
              <el-button @click="namingRuleVisible = false">关闭</el-button>
            </template>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { getProjects, createProject, updateProject, deleteProject, toggleProjectStatus, getUserAccessibleTeams, updateProjectTeams } from '../../api/project'
import { getNamingRule, updateNamingRule } from '../../api/namingRule'
import { getTeams } from '../../api/team'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder, Plus, Edit, Delete, Clock, User, Search, Document } from '@element-plus/icons-vue'
import { useUserRole } from '../../composables/useUserRole'
import { useTableHeight } from '../../composables/useTableHeight'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'

const { t } = useI18n()
const router = useRouter()
const { hasButton, isSuperAdmin } = useUserRole()
const canEditTag = computed(() => isSuperAdmin.value || hasButton('projects', 'editTag'))
const canEditNamingRule = computed(() => isSuperAdmin.value || hasButton('projects', 'editNamingRule'))
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef, null)
const loadingStore = useLoadingStore()

const tableData = ref([])
const userTeams = ref([])
const allTeams = ref([])
const filterTeamId = ref(null)
const page = ref(1)
const size = ref(10)
const total = ref(0)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogTitle = computed(() => form.id ? t('project.editProject') : t('project.createProject'))
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null, name: '', tag: '', description: '', status: 1, team_ids: []
})

const rules = computed(() => {
  const baseRules = {
    name: [
      { required: true, message: t('project.inputName'), trigger: 'blur' },
      { min: 1, max: 100, message: t('project.inputName'), trigger: 'blur' }
    ],
    team_ids: [
      { required: true, type: 'array', message: t('project.teamRequired'), trigger: 'change' }
    ]
  }
  // 新建时tag必填，编辑时不需要验证（因为只读）
  if (!form.id) {
    baseRules.tag = [{ required: true, message: '用例库Tag不能为空，用于生成用例编号', trigger: 'blur' }]
  }
  return baseRules
})

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const handleSearch = () => { page.value = 1; loadData() }
const handleFilterChange = () => { page.value = 1; loadData() }

const loadData = async () => {
  loadingStore.showLoading()
  try {
    const params = { page: page.value, size: size.value, keyword: searchKeyword.value || undefined, team_id: filterTeamId.value || undefined }
    const res = await getProjects(params)
    tableData.value = res.data.records || []; total.value = res.data.total || 0
  } catch { ElMessage.error(t('common.failed')) } finally { loadingStore.hideLoading() }
}

const handleSizeChange = async () => { page.value = 1; await loadData(); await nextTick(); scrollToTop() }
const handlePageChange = async () => { await loadData(); await nextTick(); scrollToTop() }

const handleCreate = () => {
  form.id = null; form.name = ''; form.tag = ''; form.description = ''; form.status = 1; form.team_ids = []
  dialogVisible.value = true
  if (formRef.value) formRef.value.clearValidate()
}

const handleProjectNameClick = (row) => {
  sessionStorage.setItem(`project_name_${row.id}`, row.name)
  router.push(`/projects/${row.id}/modules`)
}

const handleEdit = async (row) => {
  form.id = row.id; form.name = row.name; form.tag = row.tag || ''; form.description = row.description; form.status = row.status
  form.team_ids = row.authorized_teams ? row.authorized_teams.map(t => t.id) : []
  dialogVisible.value = true
  if (formRef.value) formRef.value.clearValidate()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!form.team_ids || form.team_ids.length === 0) { ElMessage.warning(t('project.teamRequired')); return }
    submitting.value = true
    try {
      const projectData = { name: form.name, tag: form.tag || null, description: form.description, status: form.status }
      let projectId
      if (form.id) {
        await updateProject(form.id, projectData); projectId = form.id
        await updateProjectTeams(projectId, form.team_ids)
        ElMessage.success(t('project.updateSuccess'))
      } else {
        const response = await createProject(projectData); projectId = response.data.id
        await updateProjectTeams(projectId, form.team_ids)
        ElMessage.success(t('project.createSuccess'))
      }
      dialogVisible.value = false; await loadData()
      eventBus.emit('projects-changed')
    } catch (error) { ElMessage.error(error.response?.data?.detail || t('common.failed')) } finally { submitting.value = false }
  })
}

const handleStatusChange = async (row) => {
  const newStatus = row.status === 1 ? 0 : 1
  const statusText = newStatus === 1 ? t('common.enabled') : t('common.disabled')
  try {
    await ElMessageBox.confirm(t('project.statusToggleConfirm', { action: statusText }), t('user.statusToggle'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await toggleProjectStatus(row.id)
    ElMessage.success(t('project.statusUpdateSuccess', { action: statusText })); await loadData()
    eventBus.emit('projects-changed')
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('common.failed')) }
}

const handleDialogClosed = () => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur() }

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('project.deleteConfirm'), t('user.deleteTitle'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await deleteProject(row.id); ElMessage.success(t('project.deleteSuccess')); loadData()
    eventBus.emit('projects-changed')
  } catch (error) { if (error !== 'cancel') ElMessage.error(t('common.failed')) }
}

watch(() => form.team_ids, (newVal) => { if (!Array.isArray(newVal)) form.team_ids = [] }, { deep: true })

const loadUserTeams = async () => {
  try { const response = await getUserAccessibleTeams(); userTeams.value = response.data || [] } catch {}
}
const loadAllTeams = async () => {
  try { const response = await getTeams({ page: 1, size: 1000 }); allTeams.value = response.data.records || [] } catch {}
}

onMounted(() => { loadData(); loadUserTeams(); loadAllTeams(); bindTableHeight() })
onBeforeUnmount(() => { unbindTableHeight() })

// ==================== 命名规则 ====================
const namingRuleVisible = ref(false)
const namingRuleLoading = ref(false)
const namingRuleEditing = ref(false)
const namingRuleSaving = ref(false)
const namingRuleData = ref({})
const namingRuleBackup = ref(null)
const namingRuleUpdatedAt = ref(null)
const projectCodeSearch = ref('')
const moduleCodeSearch = ref('')

const filteredProjectCodes = computed(() => {
  const list = namingRuleData.value.project_codes || []
  const kw = projectCodeSearch.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter(item =>
    (item.name || '').toLowerCase().includes(kw) ||
    (item.code || '').toLowerCase().includes(kw)
  )
})

const filteredModuleCodes = computed(() => {
  const list = namingRuleData.value.module_codes || []
  const kw = moduleCodeSearch.value.trim().toLowerCase()
  if (!kw) return list
  return list.filter(item =>
    (item.name || '').toLowerCase().includes(kw) ||
    (item.code || '').toLowerCase().includes(kw)
  )
})

const removeProjectCode = (row) => {
  const idx = namingRuleData.value.project_codes.indexOf(row)
  if (idx >= 0) namingRuleData.value.project_codes.splice(idx, 1)
}

const removeModuleCode = (row) => {
  const idx = namingRuleData.value.module_codes.indexOf(row)
  if (idx >= 0) namingRuleData.value.module_codes.splice(idx, 1)
}

const openNamingRuleDialog = async () => {
  namingRuleVisible.value = true
  namingRuleEditing.value = false
  namingRuleLoading.value = true
  projectCodeSearch.value = ''
  moduleCodeSearch.value = ''
  try {
    const res = await getNamingRule()
    if (res.code === 200) {
      namingRuleData.value = res.data
      namingRuleUpdatedAt.value = res.updated_at
    }
  } catch (e) {
    ElMessage.error('加载命名规则失败')
  } finally {
    namingRuleLoading.value = false
  }
}

const cancelNamingRuleEdit = () => {
  if (namingRuleBackup.value) {
    namingRuleData.value = JSON.parse(namingRuleBackup.value)
  }
  namingRuleEditing.value = false
  namingRuleBackup.value = null
}

// 进入编辑时备份
watch(() => namingRuleEditing.value, (val) => {
  if (val) {
    namingRuleBackup.value = JSON.stringify(namingRuleData.value)
  }
})

const saveNamingRule = async () => {
  namingRuleSaving.value = true
  try {
    const res = await updateNamingRule(namingRuleData.value)
    if (res.code === 200) {
      ElMessage.success('命名规则已保存')
      namingRuleEditing.value = false
      namingRuleBackup.value = null
      namingRuleUpdatedAt.value = new Date().toISOString()
    }
  } catch (e) {
    if (e.response?.status === 403) {
      ElMessage.error('没有编辑命名规则的权限')
    } else {
      ElMessage.error('保存失败')
    }
  } finally {
    namingRuleSaving.value = false
  }
}
</script>

<style scoped>
/* ==================== */
/* 页面布局 - 统一设计规范 */
/* ==================== */
.project-page {
  height: 100%;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px;
}

.project-page::-webkit-scrollbar { width: 8px; }
.project-page::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.project-page::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.project-page::-webkit-scrollbar-track { background: #f1f5f9; }

/* ==================== */
/* 表格卡片 */
/* ==================== */
.table-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: #fff;
}

.table-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  flex: 1;
  min-height: 0;
}

/* ==================== */
/* 工具栏 */
/* ==================== */
.table-header {
  padding: 16px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  background-color: rgba(248, 250, 252, 0.5);
  border-radius: 16px 16px 0 0;
  gap: 12px;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-shrink: 0;
  margin-left: auto;
}

.header-right :deep(.el-input__wrapper) {
  height: 40px !important;
  min-height: 40px !important;
  padding: 1px 11px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
}

.header-right :deep(.el-input__inner) {
  height: 38px !important;
  line-height: 38px !important;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button {
  border-radius: 8px !important;
  font-weight: 500 !important;
  height: 40px !important;
  padding: 0 18px !important;
  font-size: 14px !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.action-buttons .el-button--primary {
  background: #4f46e5 !important;
  border: none !important;
}

.action-buttons .el-button--primary:hover {
  background: #4338ca !important;
}

/* ==================== */
/* 表格容器 */
/* ==================== */
.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  overflow: hidden;
}

.table-wrapper .table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
  position: relative;
}

.table-wrapper :deep(.el-table td.el-table__cell),
.table-wrapper :deep(.el-table th.el-table__cell) {
  height: 48px !important;
  padding: 0 12px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell .cell),
.table-wrapper :deep(.el-table th.el-table__cell .cell) {
  line-height: 48px;
  padding: 0;
}

.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden !important;
  position: relative;
  z-index: 10 !important;
}

.table-wrapper :deep(.el-table__body-wrapper) {
  position: relative;
  z-index: 5 !important;
}



/* ==================== */
/* 单元格内容样式 */
/* ==================== */
.tag-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cell-tag {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-tag-more {
  cursor: pointer;
}

.text-muted {
  color: #94a3b8;
}

.project-name-cell {
  display: block;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.creator-name {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.created-at {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

.project-name-cell:hover .project-name {
  color: #409eff !important;
  text-decoration: underline;
}

.project-name {
  font-weight: 500;
  color: #0f172a;
  transition: color 0.2s;
}

.project-tag {
  color: #409eff;
}

/* ==================== */
/* 分页 */
/* ==================== */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  flex-shrink: 0;
  border-top: 1px solid #e2e8f0;
  border-radius: 0 0 16px 16px;
  min-height: 56px;
}

.pagination-container :deep(.el-pager li) {
  background: transparent;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
}

.pagination-container :deep(.el-pager li.is-active) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 600;
}

.pagination-container :deep(.el-pager li:hover:not(.is-active)) {
  background: #f1f5f9;
}

.pagination-container :deep(.el-pagination__total) {
  font-size: 14px;
  color: #64748b;
}

/* ==================== */
/* 按钮 */
/* ==================== */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s;
}

:deep(.el-button:hover) {
  transform: none;
  box-shadow: none;
}

:deep(.el-button--primary) {
  background: #4f46e5;
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--primary:hover) {
  background: #4338ca;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

:deep(.el-button--danger) {
  background: #ef4444;
  border: none;
}

:deep(.el-button--danger:hover) {
  background: #dc2626;
}

/* ==================== */
/* 对话框 */
/* ==================== */
:deep(.el-dialog) {
  border-radius: 16px;
  overflow: hidden;
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e2e8f0;
  margin-right: 0;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-dialog__footer) {
  padding: 16px 24px;
  border-top: 1px solid #e2e8f0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #334155;
  font-size: 14px;
}

:deep(.el-input__wrapper),
:deep(.el-select) {
  border-radius: 8px;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #94a3b8;
}

/* ==================== */
/* 行悬停效果 */
/* ==================== */
.table-wrapper :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 固定列不透明背景 */
.table-wrapper :deep(.el-table td.el-table__cell) {
  background: #fff;
}

.table-wrapper :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #fafbfc;
}

/* ==================== 命名规则对话框 ==================== */
.naming-rule-content {
  max-height: 65vh;
  overflow-y: auto;
  padding: 0 4px;
}

.rule-section {
  margin-bottom: 24px;
}

.rule-section-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.rule-count {
  font-size: 12px;
  font-weight: 400;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 10px;
}

.rule-format-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 16px;
}

.rule-format-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: #334155;
  white-space: pre-wrap;
  font-family: inherit;
}

.rule-table {
  border-radius: 8px;
  overflow: hidden;
}

.logic-text {
  color: #64748b;
  font-size: 13px;
}
</style>