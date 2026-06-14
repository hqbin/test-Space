<template>
  <div class="suite-container">
    <div class="table-header">
      <div class="header-left">
        <el-button v-if="hasButton('testplans', 'suiteCreate')" type="primary" :icon="Plus" @click="handleCreate">
          {{ $t('suite.createSuite') }}
        </el-button>
      </div>
      <div class="header-right">
        <el-input
          v-model="searchKeyword"
          :placeholder="$t('suite.searchPlaceholder')"
          style="width: 250px;"
          clearable
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <div class="table-wrapper">
      <el-table :data="tableData" style="width: 100%" v-loading="loading"
        :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px' }">
        <el-table-column prop="name" :label="$t('suite.name')" min-width="150" :show-overflow-tooltip="{ showAfter: 500 }">
          <template #default="scope">
            <span class="clickable-name" @click="handleViewSuite(scope.row)">{{ scope.row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" :label="$t('suite.description')" min-width="150" :show-overflow-tooltip="{ showAfter: 500 }">
          <template #default="scope">
            <span class="clickable-cell" @click="handleViewSuite(scope.row)">{{ scope.row.description || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="case_count" :label="$t('suite.caseCount')" width="120" align="center">
          <template #default="scope">
            <span class="clickable-cell" @click="handleViewSuite(scope.row)">
              <el-tag type="info" size="small">{{ scope.row.case_count }}</el-tag>
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_name" :label="$t('suite.creator')" width="140" align="center" />
        <el-table-column prop="updated_at" :label="$t('suite.updatedAt')" width="180" align="center">
          <template #default="scope">{{ formatDate(scope.row.updated_at) }}</template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="260" align="center" fixed="right">
          <template #default="scope">
            <el-button v-if="hasButton('testplans', 'suiteEdit')" link type="primary" :icon="Edit" @click="handleEdit(scope.row)">{{ $t('common.edit') }}</el-button>
            <el-button v-if="hasButton('testplans', 'suiteExport')" link type="success" :icon="Download" @click="handleExport(scope.row)">{{ $t('suite.exportExcel') }}</el-button>
            <el-button v-if="hasButton('testplans', 'suiteDelete')" link type="danger" :icon="Delete" @click="handleDelete(scope.row)">{{ $t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination-container">
      <el-pagination v-model:current-page="page" v-model:page-size="size" :total="total"
        :page-sizes="[10, 20, 50]" layout="total, sizes, prev, pager, next, jumper"
        @current-change="loadData" @size-change="loadData" />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? $t('suite.editSuite') : $t('suite.createSuite')"
      width="800px" :close-on-click-modal="false">
      <el-form :model="form" label-width="100px" label-position="top">
        <el-form-item :label="$t('suite.name')" required>
          <el-input v-model="form.name" :placeholder="$t('suite.inputName')" />
        </el-form-item>
        <el-form-item :label="$t('suite.description')">
          <el-input v-model="form.description" type="textarea" :rows="3" :placeholder="$t('suite.inputDescription')" />
        </el-form-item>
        <el-form-item :label="$t('testplan.testCases')">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-button type="primary" :icon="Plus" @click="openTestCaseSelector">
              {{ $t('testplan.selectTestCases') }}
            </el-button>
            <span style="color: #64748b;">
              {{ $t('testplan.selectedCases', { count: form.testCaseIds.length }) }}
            </span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 测试用例选择器对话框 -->
    <el-dialog v-model="selectorVisible" :title="$t('testplan.selectTestCasesTitle')"
      width="95%" top="3vh" :close-on-click-modal="false" append-to-body class="testcase-selector-dialog">
      <div class="testcase-select-container">
        <div class="module-sidebar">
          <div class="project-filter-section">
            <div class="section-header"><span>{{ $t('testcase.caseLibrary') }}</span></div>
            <div class="project-filter-content">
              <ProjectSelector v-model="selectedProjectIdList" :project-list="teamProjectList" @change="handleProjectChange" />
            </div>
          </div>
          <el-divider style="margin: 12px 0;" />
          <div class="module-header"><span>{{ $t('testcase.moduleBelongs') }}</span></div>
          <div class="module-list">
            <div class="module-item" :class="{ active: filterModule === '' }" @click="filterModule = ''; filterSubModule = ''; loadSelectorData()">
              <span class="module-name">{{ $t('common.all') }}</span>
            </div>
            <div v-for="item in flatModuleTree" :key="item.path" class="module-item"
              :class="{ 'main-module': item.depth === 0, 'sub-module': item.depth > 0, active: filterModule === item.path }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}">
              <el-icon v-if="item.children && item.children.length > 0" class="expand-icon" @click.stop="toggleModuleExpand(item.path)">
                <ArrowRight v-if="!item.expanded" /><ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="filterModule = item.path; filterSubModule = ''; loadSelectorData()">
                <span class="module-name">{{ item.name }}<span v-if="item.tag" style="color: #409eff; margin-left: 2px;">({{ item.tag }})</span></span>
              </div>
            </div>
          </div>
        </div>
        <div class="testcase-content">
          <div class="testcase-filter">
            <el-input v-model="selectorKeyword" :placeholder="$t('testcase.searchPlaceholder')" clearable
              style="width: 300px; margin-right: 10px" @keyup.enter="loadSelectorData">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="loadSelectorData"><el-icon><Search /></el-icon>{{ $t('common.search') }}</el-button>
            <el-select v-model="filterLevel" multiple clearable :placeholder="$t('testcase.level')" style="width: 200px; margin-left: 10px" @change="loadSelectorData">
              <el-option label="L1" value="L1" />
              <el-option label="L2" value="L2" />
              <el-option label="L3" value="L3" />
              <el-option label="L4" value="L4" />
            </el-select>
            <el-button @click="selectAllCases" :disabled="selectorData.length === 0" :loading="selectingAll" style="margin-left: 10px">{{ $t('testplan.selectAll') }}</el-button>
            <div style="flex: 1"></div>
            <el-button type="primary" :disabled="tempSelectedTestCases.length === 0" @click="confirmSelection">
              {{ $t('testplan.confirmSelection') }} ({{ tempSelectedTestCases.length }})
            </el-button>
          </div>
          <div class="table-wrapper">
            <el-table ref="selectorTableRef" :data="selectorData" style="width: 100%" height="100%" border
              v-loading="loadingSelectorData" @selection-change="handleSelectionChange"
              :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }">
              <el-table-column type="selection" width="50" align="center" />
              <el-table-column prop="case_number" :label="$t('testcase.caseNumber')" width="230" align="center" :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope"><el-tag type="info" size="small">{{ scope.row.case_number }}</el-tag></template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('testcase.name')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
              <el-table-column prop="module" :label="$t('testcase.moduleBelongs')" width="140" align="center" :show-overflow-tooltip="{ showAfter: 500 }" />
              <el-table-column prop="level" :label="$t('testcase.level')" width="100" align="center" />
              <el-table-column prop="status" :label="$t('common.status')" width="120" align="center">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">{{ $t('testcase.statusReviewed') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">{{ $t('testcase.statusPendingReview') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">{{ $t('testcase.statusReviewRejected') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
          <el-pagination v-model:current-page="selectorPage" v-model:page-size="selectorSize" :total="selectorTotal"
            :page-sizes="[10, 20, 50, 100]" layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadSelectorData" @current-change="loadSelectorData" style="margin-top: 16px; justify-content: flex-end; flex-shrink: 0" />
        </div>
      </div>
    </el-dialog>

    <!-- 查看套件关联用例对话框 -->
    <el-dialog v-model="viewVisible" :title="`${viewData.name || ''} - 关联用例`"
      width="95%" top="3vh" :close-on-click-modal="false" class="testcase-selector-dialog"
      @closed="handleViewDialogClosed">
      <div class="testcase-select-container" v-loading="viewLoading">
        <!-- 左侧模块树 -->
        <div class="module-sidebar">
          <div class="module-header"><span>{{ $t('testcase.moduleBelongs') }}</span></div>
          <div class="module-list">
            <div class="module-item" :class="{ active: viewFilter.module === '' }" @click="handleViewModuleClick('')">
              <span class="module-name">{{ $t('common.all') }}</span>
            </div>
            <div v-for="item in flatViewModuleTree" :key="item.path" class="module-item"
              :class="{ 'main-module': item.depth === 0, 'sub-module': item.depth > 0, active: viewFilter.module === item.path }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}">
              <el-icon v-if="item.children && item.children.length > 0" class="expand-icon" @click.stop="toggleViewModuleExpand(item.path)">
                <ArrowRight v-if="!item.expanded" /><ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="handleViewModuleClick(item.path)">
                <span class="module-name">{{ item.name }}</span>
              </div>
            </div>
          </div>
        </div>
        <!-- 右侧用例列表 -->
        <div class="testcase-content">
          <div class="testcase-filter">
            <el-input v-model="viewSearchKeyword" :placeholder="$t('testcase.searchPlaceholder')" clearable
              style="width: 300px; margin-right: 10px" @keyup.enter="filterViewCases">
              <template #prefix><el-icon><Search /></el-icon></template>
            </el-input>
            <el-button type="primary" @click="filterViewCases"><el-icon><Search /></el-icon>{{ $t('common.search') }}</el-button>
            <div style="flex: 1"></div>
            <el-button type="primary" @click="showAddCaseFromView">
              <el-icon><Plus /></el-icon>添加用例
            </el-button>
          </div>
          <div class="table-wrapper">
            <el-table :data="pagedViewCases" style="width: 100%" height="100%" border
              :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }">
              <el-table-column :label="$t('common.operation')" width="60" align="center">
                <template #default="{ row }">
                  <el-icon class="remove-icon" @click="handleUnlinkCase(row)" title="取消关联" style="cursor: pointer; color: #f56c6c; font-size: 18px;">
                    <CircleClose />
                  </el-icon>
                </template>
              </el-table-column>
              <el-table-column prop="case_number" :label="$t('testcase.caseNumber')" width="230" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('testcase.name')" min-width="200" align="left" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope"><div class="single-line-ellipsis">{{ scope.row.name }}</div></template>
              </el-table-column>
              <el-table-column prop="module" :label="$t('testcase.moduleBelongs')" width="140" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }" />
              <el-table-column prop="steps" :label="$t('testcase.steps')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip placement="top" popper-class="steps-tooltip" effect="dark" :show-after="500" raw-content>
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div v-for="(step, i) in parseSteps(scope.row.steps)" :key="i" style="display: flex; padding: 6px 0; line-height: 1.6;">
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ i + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ step }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">{{ parseSteps(scope.row.steps).map((s, i) => `${i + 1}. ${s}`).join(' ') || '-' }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column :label="$t('testcase.expectedResult')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip placement="top" popper-class="steps-tooltip" effect="dark" :show-after="500" raw-content>
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div v-for="(r, i) in parseExpected(scope.row.expected_result)" :key="i" style="display: flex; padding: 6px 0; line-height: 1.6;">
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ i + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ r }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">{{ parseExpected(scope.row.expected_result).map((r, i) => `${i + 1}. ${r}`).join(' ') || '-' }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="level" :label="$t('testcase.level')" width="140" align="center" resizable />
              <el-table-column prop="status" :label="$t('common.status')" width="140" align="center" resizable>
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">{{ $t('testcase.statusReviewed') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">{{ $t('testcase.statusPendingReview') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">{{ $t('testcase.statusReviewRejected') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column :label="$t('testcase.creator')" width="120" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">{{ scope.row.creator_name || '-' }}</template>
              </el-table-column>
            </el-table>
          </div>
          <el-pagination
            v-model:current-page="viewPage" v-model:page-size="viewPageSize"
            :page-sizes="[10, 20, 50, 100]" :total="filteredViewCases.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="viewPage = 1" @current-change="() => {}"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="viewVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { getTestSuites, createTestSuite, getTestSuiteDetail, updateTestSuite, deleteTestSuite, unlinkTestSuiteCase, exportSuiteExcel } from '../../api/testSuite'
import { getTestCases, getAllTestCaseIds } from '../../api/testcase'
import { getModuleTree } from '../../api/module'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, ArrowRight, ArrowDown, CircleClose, Download } from '@element-plus/icons-vue'
import { useTeam } from '../../composables/useTeam'
import { useUserRole } from '../../composables/useUserRole'
import { useProjectPreference } from '../../composables/useProjectPreference'
import ProjectSelector from '../../components/ProjectSelector.vue'

const { t } = useI18n()
const { currentTeam, teamProjects } = useTeam()
const { hasButton } = useUserRole()
const { selectedProjectIdList, applyPreference, updateSelection } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0
    ? selectedProjectIdList.value
    : teamProjectList.value.map(p => p.id)
})

const tableData = ref([])
const loading = ref(false)
const page = ref(1)
const size = ref(20)
const total = ref(0)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const submitting = ref(false)

const form = reactive({ name: '', description: '', testCaseIds: [] })

// 用例选择器 - 与 TestPlanList 完全一致的模式
const selectorVisible = ref(false)
const selectorData = ref([])
const loadingSelectorData = ref(false)
const selectorKeyword = ref('')
const selectorPage = ref(1)
const selectorSize = ref(20)
const selectorTotal = ref(0)
const tempSelectedTestCases = ref([])  // 存储完整对象，不只是ID
const isRestoringSelection = ref(false)  // 防止恢复选中时触发 selection-change
const selectingAll = ref(false)
const selectorTableRef = ref(null)
const moduleTree = ref([])
let _moduleTreeVer = 0
let _selectorVer = 0
const filterModule = ref('')
const filterSubModule = ref('')
const filterLevel = ref([])

const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const handleSearch = () => { page.value = 1; loadData() }

const loadData = async () => {
  if (!currentTeam.value?.id) return
  loading.value = true
  try {
    const res = await getTestSuites({ team_id: currentTeam.value.id, keyword: searchKeyword.value || undefined, page: page.value, size: size.value })
    if (res.data) { tableData.value = res.data.records || []; total.value = res.data.total || 0 }
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const handleCreate = () => {
  isEdit.value = false; editId.value = null
  form.name = ''; form.description = ''; form.testCaseIds = []
  dialogVisible.value = true
}

const handleEdit = async (row) => {
  isEdit.value = true; editId.value = row.id
  try {
    const res = await getTestSuiteDetail(row.id)
    if (res.data) {
      form.name = res.data.name; form.description = res.data.description || ''
      form.testCaseIds = res.data.test_case_ids || []
    }
    dialogVisible.value = true
  } catch (e) { ElMessage.error(t('common.failed')) }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('suite.deleteConfirm'), t('common.tip'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await deleteTestSuite(row.id)
    ElMessage.success(t('suite.deleteSuccess'))
    loadData()
  } catch (e) { if (e !== 'cancel') ElMessage.error(t('common.failed')) }
}

const exportingId = ref(null)
const handleExport = async (row) => {
  if (row.case_count === 0) {
    ElMessage.warning(t('suite.exportEmpty'))
    return
  }
  exportingId.value = row.id
  try {
    await exportSuiteExcel(row.id, row.name)
    ElMessage.success(t('suite.exportSuccess'))
  } catch (e) {
    console.error(e)
    ElMessage.error(t('common.failed'))
  } finally {
    exportingId.value = null
  }
}

const handleSubmit = async () => {
  if (!form.name.trim()) { ElMessage.warning(t('suite.inputName')); return }
  submitting.value = true
  try {
    const payload = { name: form.name, description: form.description, team_id: currentTeam.value?.id, test_case_ids: form.testCaseIds }
    if (isEdit.value) {
      await updateTestSuite(editId.value, payload)
      ElMessage.success(t('suite.updateSuccess'))
    } else {
      await createTestSuite(payload)
      ElMessage.success(t('suite.createSuccess'))
    }
    dialogVisible.value = false; loadData()
  } catch (e) { ElMessage.error(t('common.failed')) }
  finally { submitting.value = false }
}

// ========== 用例选择器逻辑（与 TestPlanList 完全一致） ==========

const openTestCaseSelector = async () => {
  selectorKeyword.value = ''
  filterModule.value = ''
  filterSubModule.value = ''
  filterLevel.value = []
  selectorPage.value = 1
  selectorSize.value = 20
  selectorVisible.value = true

  // 如果已有已选用例（编辑模式），用 all-ids 接口恢复勾选状态（不受100条限制）
  if (form.testCaseIds.length > 0) {
    // 直接用 id 构造轻量对象，loadSelectorData 会根据 id 恢复表格勾选
    const selectedIdSet = new Set(form.testCaseIds)
    tempSelectedTestCases.value = form.testCaseIds.map(id => ({ id }))
  } else {
    tempSelectedTestCases.value = []
  }

  loadModuleTree()
  loadSelectorData()
}

const loadModuleTree = async () => {
  const projectParam = currentProjectIds.value.join(',')
  if (!projectParam) return
  const ver = ++_moduleTreeVer
  try {
    const res = await getModuleTree(projectParam)
    if (ver !== _moduleTreeVer) return
    const addExpanded = (nodes) => nodes.map(n => ({
      ...n, expanded: false,
      children: n.children ? addExpanded(n.children) : []
    }))
    moduleTree.value = addExpanded(res.data || [])
  } catch (e) { console.error(e) }
}

const flatModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (node.expanded && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(moduleTree.value, 0)
  return result
})

const toggleModuleExpand = (path) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === path) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(moduleTree.value)
}

const loadSelectorData = async () => {
  const ver = ++_selectorVer
  loadingSelectorData.value = true
  try {
    const params = {
      page: selectorPage.value,
      size: selectorSize.value,
      keyword: selectorKeyword.value || undefined,
      module: (filterSubModule.value ? `${filterModule.value}/${filterSubModule.value}` : filterModule.value) || undefined,
      status_in: 'REVIEWED,PENDING,REJECTED'
    }
    if (filterLevel.value.length > 0) {
      params.level_in = filterLevel.value.join(',')
    }
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    const res = await getTestCases(params)
    if (ver !== _selectorVer) return
    if (res.data) {
      // 设置标志位，防止 selection-change 清空已选
      isRestoringSelection.value = true
      selectorData.value = res.data.records || res.data.items || []
      selectorTotal.value = res.data.total || 0
    }
    // 恢复之前的选择状态
    await nextTick()
    // 先清除所有选中状态，防止 row-key 复用导致残留勾选
    if (selectorTableRef.value) {
      selectorTableRef.value.clearSelection()
    }
    if (selectorTableRef.value && tempSelectedTestCases.value.length > 0) {
      const selectedIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
      selectorData.value.forEach(row => {
        const shouldSelect = selectedIds.has(row.id)
        selectorTableRef.value.toggleRowSelection(row, shouldSelect)
      })
    }
    await nextTick()
    isRestoringSelection.value = false
  } catch (e) { console.error(e) }
  finally { loadingSelectorData.value = false }
}

const handleSelectionChange = (selection) => {
  // 恢复选中状态期间跳过，避免清空已选
  if (isRestoringSelection.value) return

  // 获取当前页面的所有用例ID
  const currentPageIds = new Set(selectorData.value.map(tc => tc.id))

  // 移除当前页面的所有用例（无论是否选中）
  const otherPagesSelected = tempSelectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))

  // 添加当前页面新选中的用例
  tempSelectedTestCases.value = [...otherPagesSelected, ...selection]
}

const selectAllCases = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('请先选择用例库')
    return
  }

  selectingAll.value = true
  try {
    // 使用 all-ids 接口，不受后端100条分页限制
    const params = {
      keyword: selectorKeyword.value || undefined,
      module: (filterSubModule.value ? `${filterModule.value}/${filterSubModule.value}` : filterModule.value) || undefined,
      status_in: 'REVIEWED,PENDING,REJECTED'
    }
    if (filterLevel.value.length > 0) {
      params.level_in = filterLevel.value.join(',')
    }
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }

    const res = await getAllTestCaseIds(params)
    if (res.code === 200) {
      const allRecords = res.data.records || []

      // 直接替换临时选择列表为所有用例（去重）
      const existingIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
      // all-ids 返回轻量对象，只需 id/status/case_number/primary_project_id
      const newRecords = allRecords.filter(tc => !existingIds.has(tc.id))
      tempSelectedTestCases.value = [...tempSelectedTestCases.value, ...newRecords]

      // 同步表格的选中状态
      await nextTick()
      if (selectorTableRef.value) {
        isRestoringSelection.value = true
        const selectedIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
        selectorData.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          selectorTableRef.value.toggleRowSelection(row, shouldSelect)
        })
        await nextTick()
        isRestoringSelection.value = false
      }

      ElMessage.success(t('testplan.selectedCases', { count: allRecords.length }))
    }
  } catch (error) {
    console.error('全选失败:', error)
    ElMessage.error('全选失败')
  } finally {
    selectingAll.value = false
  }
}

const confirmSelection = async () => {
  // 检查是否有待评审或评审未通过的用例
  const pendingTestCases = tempSelectedTestCases.value.filter(tc => tc.status === 'PENDING')
  const rejectedTestCases = tempSelectedTestCases.value.filter(tc => tc.status === 'REJECTED')

  if (pendingTestCases.length > 0 || rejectedTestCases.length > 0) {
    let message = ''
    if (pendingTestCases.length > 0 && rejectedTestCases.length > 0) {
      message = `存在 ${pendingTestCases.length} 个待评审用例和 ${rejectedTestCases.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    } else if (pendingTestCases.length > 0) {
      message = `存在 ${pendingTestCases.length} 个待评审用例，需要先完成评审后再进行关联。`
    } else {
      message = `存在 ${rejectedTestCases.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    }

    try {
      await ElMessageBox.confirm(
        message,
        t('common.tip'),
        {
          confirmButtonText: t('common.understood'),
          showCancelButton: false,
          type: 'warning'
        }
      )
    } catch (error) {
      // 用户点击了确定或关闭
    }
    return
  }

  // 直接替换为当前选中的用例ID
  form.testCaseIds = tempSelectedTestCases.value.map(tc => tc.id)

  selectorVisible.value = false
  tempSelectedTestCases.value = []
  ElMessage.success(t('testplan.casesLinked', { count: form.testCaseIds.length }))
}

// 防抖，防止快速切换导致数据错乱
let _projectChangeTimer = null
const handleProjectChange = (ids) => {
  updateSelection(ids)
  filterModule.value = ''
  filterSubModule.value = ''
  filterLevel.value = []
  selectorPage.value = 1
  clearTimeout(_projectChangeTimer)
  _projectChangeTimer = setTimeout(() => {
    loadModuleTree()
    loadSelectorData()
  }, 300)
}

// ========== 查看套件详情 ==========
const viewVisible = ref(false)
const viewData = ref({})
const viewLoading = ref(false)
const viewSearchKeyword = ref('')
const viewModuleTree = ref([])
const viewFilter = reactive({ module: '', subModule: '' })
const viewPage = ref(1)
const viewPageSize = ref(20)
const allViewCases = ref([])

const filteredViewCases = computed(() => {
  let filtered = allViewCases.value
  if (viewFilter.module) {
    const filterPath = viewFilter.module
    filtered = filtered.filter(tc => {
      const raw = tc.module || '未分类'
      return raw === filterPath || raw.startsWith(filterPath + '/')
    })
  }
  if (viewSearchKeyword.value) {
    const kw = viewSearchKeyword.value.toLowerCase()
    filtered = filtered.filter(tc =>
      tc.case_number?.toLowerCase().includes(kw) ||
      tc.name?.toLowerCase().includes(kw)
    )
  }
  return filtered
})

const pagedViewCases = computed(() => {
  const start = (viewPage.value - 1) * viewPageSize.value
  return filteredViewCases.value.slice(start, start + viewPageSize.value)
})

const handleViewSuite = async (row) => {
  viewVisible.value = true
  viewLoading.value = true
  viewSearchKeyword.value = ''
  viewFilter.module = ''
  viewFilter.subModule = ''
  viewPage.value = 1
  viewData.value = { name: row.name, description: row.description }
  allViewCases.value = []
  try {
    const res = await getTestSuiteDetail(row.id)
    if (res.data) {
      viewData.value = res.data
      allViewCases.value = res.data.test_cases || []
      // 构建模块树
      buildViewModuleTree(allViewCases.value)
    }
  } catch (e) {
    ElMessage.error(t('common.failed'))
  } finally {
    viewLoading.value = false
  }
}

const buildViewModuleTree = (cases) => {
  const root = { children: new Map() }
  cases.forEach(tc => {
    const raw = tc.module || '未分类'
    const parts = raw.split('/').map(p => p.trim()).filter(Boolean)
    if (parts.length === 0) parts.push('未分类')
    let current = root
    let pathSoFar = ''
    for (const part of parts) {
      pathSoFar = pathSoFar ? pathSoFar + '/' + part : part
      if (!current.children.has(part)) {
        current.children.set(part, { name: part, path: pathSoFar, children: new Map(), expanded: false })
      }
      current = current.children.get(part)
    }
  })
  const toArray = (map) => Array.from(map.values()).map(n => ({
    name: n.name, path: n.path, expanded: false,
    children: n.children.size > 0 ? toArray(n.children) : []
  }))
  viewModuleTree.value = toArray(root.children)
}

const flatViewModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (node.expanded && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(viewModuleTree.value, 0)
  return result
})

const toggleViewModuleExpand = (path) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === path) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(viewModuleTree.value)
}

const handleViewModuleClick = (modulePath) => {
  viewFilter.module = modulePath
  viewFilter.subModule = ''
  viewPage.value = 1
}

const filterViewCases = () => {
  viewPage.value = 1
}

const handleUnlinkCase = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要取消关联用例 ${row.case_number} 吗？`,
      t('common.tip'),
      { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' }
    )
    await unlinkTestSuiteCase(viewData.value.id, row.id)
    ElMessage.success('取消关联成功')
    // 从本地列表移除
    allViewCases.value = allViewCases.value.filter(tc => tc.id !== row.id)
    viewData.value.case_count = allViewCases.value.length
    buildViewModuleTree(allViewCases.value)
    // 同步刷新列表页的用例数
    loadData()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('取消关联失败')
  }
}

const showAddCaseFromView = () => {
  // 关闭查看对话框，打开用例选择器（编辑模式）
  viewVisible.value = false
  isEdit.value = true
  editId.value = viewData.value.id
  form.name = viewData.value.name
  form.description = viewData.value.description || ''
  form.testCaseIds = allViewCases.value.map(tc => tc.id)
  // 不打开编辑对话框，直接打开选择器
  dialogVisible.value = true
  nextTick(() => {
    openTestCaseSelector()
  })
}

const handleViewDialogClosed = () => {
  viewSearchKeyword.value = ''
  viewFilter.module = ''
  viewFilter.subModule = ''
  viewPage.value = 1
}

// ========== 解析步骤/预期结果（与 TestPlanList 一致） ==========
const parseSteps = (stepsText) => {
  if (!stepsText) return []
  if (Array.isArray(stepsText)) {
    return stepsText.map(item => {
      let text = typeof item === 'object' && item !== null ? String(item.step || '').trim() : String(item).trim()
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      return text.trim()
    }).filter(t => t)
  }
  const textStr = String(stepsText).trim()
  if (!textStr) return []
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = typeof item === 'object' && item !== null ? String(item.step || '').trim() : String(item).trim()
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        return text.trim()
      }).filter(t => t)
    }
  } catch (e) {}
  // 纯文本处理：有序号（>=2行）按序号拆，无序号整体1条保留换行
  const lines = textStr.split('\n')
  // 序号行：数字+标点开头，. 后不能紧跟数字（排除小数如 177.5）
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
    return items.filter(t => t)
  }
  // 整体1条，但去掉可能存在的序号前缀（排除小数点）
  const stripped2 = textStr.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
  return stripped2 ? [stripped2] : []
}

const parseExpected = (expectedText) => {
  if (!expectedText) return []
  if (Array.isArray(expectedText)) {
    return expectedText.map(item => {
      let text = typeof item === 'object' && item !== null ? String(item.expected || '').trim() : String(item).trim()
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      return text.trim()
    }).filter(t => t)
  }
  const textStr = String(expectedText).trim()
  if (!textStr) return []
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = typeof item === 'object' && item !== null ? String(item.expected || '').trim() : String(item).trim()
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        return text.trim()
      }).filter(t => t)
    }
  } catch (e) {}
  // 纯文本处理：有序号（>=2行）按序号拆，无序号整体1条保留换行
  const lines = textStr.split('\n')
  // 序号行：数字+标点开头，. 后不能紧跟数字（排除小数如 177.5）
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
    return items.filter(t => t)
  }
  // 整体1条，但去掉可能存在的序号前缀（排除小数点）
  const stripped2 = textStr.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
  return stripped2 ? [stripped2] : []
}

watch(() => currentTeam.value?.id, () => { loadData() })
onMounted(() => { loadData() })
</script>

<style scoped>
.suite-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
}

/* 分页 */
.pagination-container {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  min-height: 56px;
}

.pagination-container :deep(.el-pager li) { background: transparent; font-weight: 500; border-radius: 6px; min-width: 32px; height: 32px; }
.pagination-container :deep(.el-pager li.is-active) { background: #eef2ff; color: #4f46e5; font-weight: 600; }
.pagination-container :deep(.el-pager li:hover:not(.is-active)) { background: #f1f5f9; }
.pagination-container :deep(.el-pagination__total) { font-size: 14px; color: #64748b; }

/* ==================== */
/* 用例选择器样式 - 与 TestPlanList 完全一致 */
/* ==================== */
.testcase-selector-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.testcase-select-container {
  display: flex;
  height: calc(100vh - 200px);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: visible;
}

.module-sidebar {
  width: 220px;
  border-right: 1px solid #e2e8f0;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  overflow: visible;
}

.project-filter-section {
  padding: 12px 14px;
  background: rgba(248, 250, 252, 0.5);
  overflow: visible;
  position: relative;
  z-index: 100;
  border-bottom: 1px solid #f1f5f9;
}

.section-header {
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.project-filter-content {
  padding: 0;
  overflow: visible;
  position: relative;
}

.module-header {
  padding: 12px 16px;
  border-bottom: 1px solid #f1f5f9;
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: rgba(248, 250, 252, 0.5);
}

.module-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.module-group {
  margin-bottom: 0;
}

.module-item {
  padding: 8px 12px;
  margin: 2px 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: #475569;
  transition: all 0.15s;
  user-select: none;
  border-radius: 6px;
}

.module-item:hover {
  background-color: #f8fafc;
}

.module-item.active {
  background-color: #eef2ff;
  color: #4338ca;
  font-weight: 500;
}

.module-item .expand-icon {
  margin-right: 6px;
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}

.module-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}

.module-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-module-list {
  background-color: rgba(248, 250, 252, 0.5);
}

.sub-module {
  padding-left: 40px;
  font-size: 13px;
}

.testcase-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  background-color: #ffffff;
}

.testcase-content .testcase-filter {
  margin-bottom: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.testcase-filter {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

/* 选择器内表格容器 */
.testcase-content .table-wrapper {
  flex: 1;
  width: 100%;
  overflow: visible;
  position: relative;
  min-height: 0;
  max-height: calc(100vh - 320px);
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.testcase-content .table-wrapper :deep(.el-table) {
  width: 100%;
  height: 100%;
  position: relative;
}

/* 表头样式 */
.testcase-content .table-wrapper :deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
  color: #64748b !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* 单元格高度 */
.testcase-content .table-wrapper :deep(.el-table td.el-table__cell),
.testcase-content .table-wrapper :deep(.el-table th.el-table__cell) {
  height: 48px !important;
  padding: 0 12px !important;
}

.testcase-content .table-wrapper :deep(.el-table td.el-table__cell .cell),
.testcase-content .table-wrapper :deep(.el-table th.el-table__cell .cell) {
  line-height: 48px;
  padding: 0;
}

/* 表格滚动 */
.testcase-content .table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

.testcase-content .table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden !important;
  position: relative;
  z-index: 10 !important;
}

.testcase-content .table-wrapper :deep(.el-table__body-wrapper) {
  position: relative;
  z-index: 5 !important;
}

/* 表头和表体使用固定布局确保对齐 */
.testcase-content .table-wrapper :deep(.el-table__header) {
  table-layout: fixed !important;
  width: 100% !important;
}

.testcase-content .table-wrapper :deep(.el-table__body) {
  table-layout: fixed !important;
  width: 100% !important;
}

/* 确保单元格内容居中对齐 */
.testcase-content .table-wrapper :deep(.el-table td.el-table__cell) {
  text-align: center !important;
  vertical-align: middle !important;
}

.testcase-content .table-wrapper :deep(.el-table .el-table__cell .cell) {
  padding-left: 0 !important;
  padding-right: 0 !important;
  text-align: center !important;
}

/* 滚动条样式 */
.testcase-content .table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.testcase-content .table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.testcase-content .table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
}

/* 多选框样式 - 与 TestPlanList 一致 */
:deep(.el-table .el-checkbox) {
  transform: scale(1.3);
}

:deep(.el-table .el-checkbox__inner) {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

:deep(.el-table .el-checkbox__inner::after) {
  width: 4px;
  height: 8px;
  border-width: 2px;
}

/* 多选框列不影响其他列对齐 */
:deep(.el-table .el-table-column--selection .cell) {
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 对话框样式 */
:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e2e8f0;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  border-radius: 8px;
}

/* 按钮样式 */
:deep(.el-button--primary) {
  background: #4f46e5;
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--primary:hover) {
  background: #4338ca;
}

/* 可点击的套件名称样式 */
.clickable-name {
  color: var(--demo-primary, #4f46e5);
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.clickable-name:hover {
  color: var(--demo-primary-hover, #4338ca);
  text-decoration: underline;
}

.clickable-cell {
  cursor: pointer;
  transition: color 0.2s;
}

.clickable-cell:hover {
  color: var(--demo-primary, #4f46e5);
}

/* 单行省略 */
.single-line-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 移除图标 */
.remove-icon {
  cursor: pointer;
  color: #f56c6c;
  font-size: 18px;
  transition: all 0.2s;
}

.remove-icon:hover {
  color: #f23c3c;
  transform: scale(1.2);
}
</style>
