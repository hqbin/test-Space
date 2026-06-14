<template>
  <div class="module-management-page">
    <!-- 左侧模块树 -->
    <div class="module-tree-column">
      <!-- 搜索和操作按钮 -->
      <div class="tree-header">
        <div class="search-box">
          <el-button class="back-btn" :icon="ArrowLeft" circle @click="goBack" />
          <el-icon class="search-icon"><Search /></el-icon>
          <input 
            v-model="searchKeyword" 
            type="text" 
            placeholder="Find module..."
            class="search-input"
          />
        </div>
        <div class="view-toggle" v-if="canAddModule">
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'hierarchy' }"
            @click="handleAddModule"
          >
            {{ t('module.addMainModule') }}
          </button>
          <button 
            class="toggle-btn" 
            :class="{ active: viewMode === 'list' }"
            @click="handleAddSubModuleFromTree"
          >
            {{ t('module.addSubModule') }}
          </button>
        </div>
      </div>

      <!-- 模块树列表 -->
      <div class="tree-content" v-loading="loading">
        <div class="module-list">
          <!-- 扁平化渲染所有层级模块 -->
          <template v-for="item in flatModuleList" :key="item.module.id">
            <!-- 主模块（depth === 0） -->
            <div 
              v-if="item.depth === 0"
              class="module-item main-module"
              :class="{ 
                active: selectedModuleId === item.module.id,
                expanded: isExpanded(item.module.id),
                'drag-over': dragOverIndex === item.index && dragOverParentId === null
              }"
              :data-module-id="item.module.id"
              @click="handleModuleClick(item.module)"
              @dragover="handleDragOver($event, item.index)"
              @dragleave="handleDragLeave"
              @drop="handleDrop($event, item.module, null, item.index)"
            >
              <span 
                v-if="canSortModule"
                class="drag-handle"
                draggable="true"
                @dragstart="handleDragStart($event, item.module, 'main', item.index)"
                @dragend="handleDragEnd($event)"
                @click.stop
              >
                <span class="drag-dots">
                  <span></span><span></span>
                  <span></span><span></span>
                  <span></span><span></span>
                </span>
              </span>
              <span 
                class="expand-icon"
                @click.stop="toggleExpand(item.module.id)"
                v-if="item.module.children && item.module.children.length > 0"
              >
                <el-icon v-if="isExpanded(item.module.id)"><ArrowDown /></el-icon>
                <el-icon v-else><ArrowRight /></el-icon>
              </span>
              <el-icon class="module-icon folder"><Folder /></el-icon>
              <span class="module-name">{{ item.module.name }}</span>
            </div>

            <!-- 子模块（depth >= 1） -->
            <div 
              v-else
              class="module-item sub-module"
              :class="{ 
                active: selectedModuleId === item.module.id,
                'drag-over': dragOverIndex === item.index && dragOverParentId === (item.parent && item.parent.id)
              }"
              :style="{ paddingLeft: (8 + item.depth * 20) + 'px' }"
              :data-module-id="item.module.id"
              @click.stop="handleSubModuleClick(item.module, item.parent)"
              @dragover="handleDragOver($event, item.index, item.parent && item.parent.id)"
              @dragleave="handleDragLeave"
              @drop="handleDrop($event, item.parent, item.module, item.index, item.parent && item.parent.id)"
            >
              <span 
                v-if="canSortModule"
                class="drag-handle"
                draggable="true"
                @dragstart="handleDragStart($event, item.module, 'sub', item.index, item.parent && item.parent.id)"
                @dragend="handleDragEnd($event)"
                @click.stop
              >
                <span class="drag-dots">
                  <span></span><span></span>
                  <span></span><span></span>
                  <span></span><span></span>
                </span>
              </span>
              <span 
                v-if="item.module.children && item.module.children.length > 0"
                class="expand-icon"
                @click.stop="toggleExpand(item.module.id)"
              >
                <el-icon v-if="isExpanded(item.module.id)"><ArrowDown /></el-icon>
                <el-icon v-else><ArrowRight /></el-icon>
              </span>
              <el-icon class="module-icon doc"><Document /></el-icon>
              <span class="module-name">{{ item.module.name }}</span>
            </div>
          </template>

          <el-empty 
            v-if="!loading && filteredModuleTree.length === 0" 
            description="暂无模块" 
            :image-size="60"
          />
        </div>
      </div>
    </div>

    <!-- 右侧详情区域 -->
    <div class="detail-column" v-if="selectedModule">
      <div class="detail-card">
        <div class="card-inner">
            <!-- 标题区域 -->
            <h1 class="module-title">{{ projectName }}</h1>

            <!-- 元数据行 -->
            <div class="meta-row">
              <nav class="breadcrumb">
                <template v-for="(crumb, index) in breadcrumbPath" :key="index">
                  <span 
                    class="crumb" 
                    :class="{ clickable: index < breadcrumbPath.length - 1, active: index === breadcrumbPath.length - 1 }"
                    @click="navigateToCrumb(index)"
                  >
                    {{ crumb.name }}
                  </span>
                  <el-icon v-if="index < breadcrumbPath.length - 1" class="crumb-separator"><ArrowRight /></el-icon>
                </template>
              </nav>
              <span class="meta-divider"></span>
              <div class="meta-tags">
                <span class="status-tag stable">{{ selectedModule.inheritedTag || selectedModule.tag || 'NO TAG' }}</span>
                <span class="status-tag cases">{{ selectedModule.count || 0 }} {{ t('module.cases') }}</span>
              </div>
            </div>

            <!-- 当前模块 -->
            <div class="current-module-section">
              <div class="section-label">{{ t('module.currentModule') }}</div>
              <div class="current-position">
                <div class="position-left">
                  <span class="position-tag">{{ selectedModule.name }}</span>
                </div>
                <div class="position-actions">
                  <button v-if="canEditModule" class="icon-btn" @click="handleEditModule(selectedModule)" :title="t('common.edit')">
                    <el-icon><Edit /></el-icon>
                  </button>
                  <button v-if="canDeleteModule" class="icon-btn danger" @click="handleDeleteModule(selectedModule)" :title="t('common.delete')">
                    <el-icon><Delete /></el-icon>
                  </button>
                </div>
              </div>
            </div>

              <!-- 需求文档 -->
              <div class="requirement-section">
                <div class="section-label">{{ t('module.requirementDoc') }}</div>
                <div class="requirement-links">
                  <template v-for="(link, index) in requirementLinks" :key="index">
                    <div class="requirement-link-row" v-if="editingLinkIndex !== index">
                      <a :href="link" target="_blank" class="requirement-link">
                        <el-icon><Link /></el-icon>
                        <span class="link-text">{{ link }}</span>
                      </a>
                      <div class="link-actions" v-if="canManageRequirementLink">
                        <button class="link-action-btn" @click="startEditLink(index, link)" title="编辑">
                          <el-icon><Edit /></el-icon>
                        </button>
                        <button class="link-action-btn danger" @click="deleteLink(index)" title="删除">
                          <el-icon><Delete /></el-icon>
                        </button>
                      </div>
                    </div>
                    <div class="link-edit-row" v-else>
                      <el-input v-model="editingLinkValue" placeholder="请输入链接地址" size="small" />
                      <button class="icon-btn small success" @click="saveLink(index)">
                        <el-icon><Check /></el-icon>
                      </button>
                      <button class="icon-btn small" @click="cancelEditLink">
                        <el-icon><Close /></el-icon>
                      </button>
                    </div>
                  </template>
                  
                  <!-- 新增链接 -->
                  <div class="link-edit-row" v-if="editingLinkIndex === '__new__'">
                    <el-input v-model="editingLinkValue" placeholder="请输入新链接地址" size="small" />
                    <button class="icon-btn small success" @click="saveNewLink">
                      <el-icon><Check /></el-icon>
                    </button>
                    <button class="icon-btn small" @click="cancelEditLink">
                      <el-icon><Close /></el-icon>
                    </button>
                  </div>
                  
                  <button class="add-link-btn" v-if="editingLinkIndex === null && canManageRequirementLink" @click="addNewLink">
                    <el-icon><Plus /></el-icon>
                    <span>{{ t('module.addRequirementLink') }}</span>
                  </button>
                </div>
              </div>

            <!-- RD Owner（仅主模块显示） -->
            <div class="rd-owner-section" v-if="!selectedModule.parent_id">
              <span class="section-label" style="margin-bottom: 0; margin-right: 8px;">RD Owner：</span>
              <span class="rd-owner-value" :style="{ whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }">
                {{ selectedModule.rd_owner || '-' }}
              </span>
            </div>

            <!-- 分割线 -->
            <div class="section-divider"></div>

            <!-- Execution Views -->
            <div class="execution-views">
              <div class="section-label">{{ t('module.executionViews') }}</div>
              <div class="view-cards">
                <div 
                  class="view-card" 
                  :class="{ 'view-card-active': activeView === 'pr' }"
                  @click="activeView = 'pr'"
                >
                  <div class="card-icon">
                    <el-icon :size="20"><Connection /></el-icon>
                  </div>
                  <div class="card-content">
                    <h3 class="card-title">{{ t('module.prKanban') }}</h3>
                  </div>
                  <el-icon class="card-arrow"><ArrowRight /></el-icon>
                </div>
                <div 
                  class="view-card" 
                  :class="{ 'view-card-active': activeView === 'allPr' }"
                  @click="activeView = 'allPr'"
                >
                  <div class="card-icon">
                    <el-icon :size="20"><Grid /></el-icon>
                  </div>
                  <div class="card-content">
                    <h3 class="card-title">{{ t('module.allModulePR') }}</h3>
                  </div>
                  <el-icon class="card-arrow"><ArrowRight /></el-icon>
                </div>
              </div>
            </div>
          </div>

        <!-- 分割线 -->
        <div class="card-divider"></div>

        <!-- 右侧内容区：根据视图切换 -->
        <div class="detail-right-section">
            <!-- 当前模块PR视图 -->
            <div v-if="activeView === 'pr'" class="pr-list-section" v-loading="prLinksLoading">
              <div class="section-header">
                <div class="section-label">{{ t('module.prKanban') }} ({{ modulePRLinks.length }})</div>
              </div>
              <el-table 
                :data="paginatedPRLinks" 
                style="width: 100%;" 
                :empty-text="'暂无关联PR'"
                stripe
                size="small"
                :header-cell-style="{ background: '#f9fafb', color: '#374151', fontWeight: 600, fontSize: '12px' }"
              >
                <el-table-column label="PR ID" width="100">
                  <template #default="{ row }">
                    <a :href="getPRLink(row.zmind_issue_id)" target="_blank" class="pr-id-link" @click.stop>#{{ row.zmind_issue_id }}</a>
                  </template>
                </el-table-column>
                <el-table-column label="标题" min-width="160" :show-overflow-tooltip="{ showAfter: 500 }">
                  <template #default="{ row }">
                    <span>{{ row.zmind_issue_subject }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="140" align="center">
                  <template #default="{ row }">
                    <span class="pr-status-dot" :class="getPRStatusClass(row.zmind_issue_status)"></span>
                    <span class="pr-status-text">{{ row.zmind_issue_status || '未知' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="严重程度" width="90" align="center">
                  <template #default="{ row }">
                    <span v-if="row.zmind_issue_severity" class="pr-severity">{{ row.zmind_issue_severity }}</span>
                    <span v-else class="pr-severity">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="关联用例" width="130" :show-overflow-tooltip="{ showAfter: 500 }">
                  <template #default="{ row }">
                    <a class="pr-case-link" @click.stop="navigateToCase(row.test_case_id)">{{ row.case_number }}</a>
                  </template>
                </el-table-column>
              </el-table>
              <div class="pr-pagination" v-if="modulePRLinks.length > prPageSize">
                <el-pagination
                  v-model:current-page="prCurrentPage"
                  :page-size="prPageSize"
                  :total="modulePRLinks.length"
                  layout="total, prev, pager, next"
                  small
                />
              </div>
            </div>

            <!-- 所有模块PR视图 -->
            <div v-else-if="activeView === 'allPr'" class="pr-list-section" v-loading="allPrLinksLoading">
              <div class="section-header">
                <div class="section-label">{{ t('module.allModulePR') }} ({{ allPrLinks.length }})</div>
              </div>
              <el-table 
                :data="paginatedAllPrLinks" 
                style="width: 100%;" 
                :empty-text="'暂无关联PR'"
                stripe
                size="small"
                :header-cell-style="{ background: '#f9fafb', color: '#374151', fontWeight: 600, fontSize: '12px' }"
              >
                <el-table-column label="PR ID" width="100">
                  <template #default="{ row }">
                    <a :href="getPRLink(row.zmind_issue_id)" target="_blank" class="pr-id-link" @click.stop>#{{ row.zmind_issue_id }}</a>
                  </template>
                </el-table-column>
                <el-table-column label="标题" min-width="160" :show-overflow-tooltip="{ showAfter: 500 }">
                  <template #default="{ row }">
                    <span>{{ row.zmind_issue_subject }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="状态" width="140" align="center">
                  <template #default="{ row }">
                    <span class="pr-status-dot" :class="getPRStatusClass(row.zmind_issue_status)"></span>
                    <span class="pr-status-text">{{ row.zmind_issue_status || '未知' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="严重程度" width="90" align="center">
                  <template #default="{ row }">
                    <span v-if="row.zmind_issue_severity" class="pr-severity">{{ row.zmind_issue_severity }}</span>
                    <span v-else class="pr-severity">-</span>
                  </template>
                </el-table-column>
                <el-table-column label="所属模块" width="150" :show-overflow-tooltip="{ showAfter: 500 }">
                  <template #default="{ row }">
                    <span>{{ row.case_module || '-' }}</span>
                  </template>
                </el-table-column>
                <el-table-column label="关联用例" width="130" :show-overflow-tooltip="{ showAfter: 500 }">
                  <template #default="{ row }">
                    <a class="pr-case-link" @click.stop="navigateToCase(row.test_case_id)">{{ row.case_number }}</a>
                  </template>
                </el-table-column>
              </el-table>
              <div class="pr-pagination" v-if="allPrLinks.length > prPageSize">
                <el-pagination
                  v-model:current-page="allPrCurrentPage"
                  :page-size="prPageSize"
                  :total="allPrLinks.length"
                  layout="total, prev, pager, next"
                  small
                />
              </div>
            </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div class="detail-column empty-detail" v-else>
      <div class="empty-state">
        <el-icon :size="100" color="#d1d5db"><Folder /></el-icon>
        <h2>选择模块查看详情</h2>
        <p>从左侧模块树中选择一个模块查看详情</p>
      </div>
    </div>

    <!-- 模块编辑对话框 -->
    <el-dialog 
      v-model="moduleEditVisible" 
      :title="moduleEditTitle" 
      width="500px"
      :close-on-click-modal="false"
      class="module-edit-dialog"
    >
      <el-form :model="moduleForm" label-width="120px">
        <el-form-item :label="t('module.moduleName')" required>
          <el-input 
            v-model="moduleForm.name" 
            :placeholder="t('module.namePlaceholder')"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="Tag" v-if="!moduleForm.parentId">
          <el-input 
            v-model="moduleForm.tag" 
            :placeholder="(moduleForm.id && !canEditModuleTag) ? '' : t('module.tagPlaceholder')"
            :maxlength="50"
            :disabled="!!moduleForm.id && !canEditModuleTag"
            :show-word-limit="!moduleForm.id || canEditModuleTag"
          />
          <div class="form-tip" v-if="!moduleForm.id">
            {{ t('module.tagTip') }}
          </div>
        </el-form-item>
        <el-form-item :label="t('module.requirementDoc')">
          <div class="form-links-edit">
            <div 
              v-for="(link, index) in moduleForm.requirementLinks" 
              :key="index"
              class="form-link-item"
            >
              <div class="form-link-input-wrapper">
                <el-icon class="form-link-icon"><Link /></el-icon>
                <el-input 
                  v-model="moduleForm.requirementLinks[index]" 
                  :placeholder="t('module.linkPlaceholder')"
                  maxlength="500"
                />
              </div>
              <button class="link-action-btn danger" @click="removeFormLink(index)" :title="t('common.delete')">
                <el-icon><Delete /></el-icon>
              </button>
            </div>
            <button class="add-link-btn" @click="addFormLink">
              <el-icon><Plus /></el-icon>
              <span>{{ t('module.addRequirementLink') }}</span>
            </button>
          </div>
        </el-form-item>
        <el-form-item label="RD Owner" v-if="!moduleForm.parentId">
          <el-input 
            v-model="moduleForm.rdOwner" 
            placeholder="请输入RD负责人（非必填）"
            maxlength="200"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="moduleEditVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveModule" :loading="moduleSaving">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
defineOptions({ name: 'ProjectModuleManagement' })

import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Search, ArrowLeft, ArrowRight, ArrowDown, DArrowRight,
  Folder, Document, Plus, Edit, Delete, Link, Open, Grid, Connection, Check, Close
} from '@element-plus/icons-vue'
import { getModuleTree, createModule, updateModule, deleteModule, sortModules, getModulePRLinks, getProjectAllPRLinks } from '@/api/module'
import { getProjects } from '@/api/project'
import { eventBus } from '../../utils/eventBus'
import { useUserRole } from '@/composables/useUserRole'

const route = useRoute()
const router = useRouter()
const { hasButton, isSuperAdmin } = useUserRole()
const { t } = useI18n()

const projectId = computed(() => {
  const pid = route.params.projectId
  return pid ? Number(pid) : null
})
const projectName = ref('')
const loading = ref(false)
const moduleTree = ref([])
const searchKeyword = ref('')
const viewMode = ref('hierarchy')
const expandedModules = ref([])
const selectedModuleId = ref(null)
const selectedModule = ref(null)
const currentParentModule = ref(null)
const dragOverIndex = ref(-1)
const dragOverParentId = ref(null)
const draggedModule = ref(null)
const draggedType = ref(null)
const moduleEditVisible = ref(false)
const moduleEditTitle = ref('')
const moduleSaving = ref(false)
const activeView = ref('pr')
const modulePRLinks = ref([])
const prLinksLoading = ref(false)
const prCurrentPage = ref(1)
const prPageSize = 15
const allPrLinks = ref([])
const allPrLinksLoading = ref(false)
const allPrCurrentPage = ref(1)

const paginatedPRLinks = computed(() => {
  const start = (prCurrentPage.value - 1) * prPageSize
  return modulePRLinks.value.slice(start, start + prPageSize)
})

const paginatedAllPrLinks = computed(() => {
  const start = (allPrCurrentPage.value - 1) * prPageSize
  return allPrLinks.value.slice(start, start + prPageSize)
})

const getPRLink = (issueId) => {
  return `https://zmind.whaletv.com/issues/${issueId}`
}

const getPRStatusClass = (status) => {
  if (!status) return 'dot-other'
  const s = status.toLowerCase()
  const closedStatuses = ['closed', 'suspended', 'pending', 'device issue', 'app issue']
  if (closedStatuses.includes(s)) return 'dot-closed'
  if (s === 'confirmed' || s === 'confirm') return 'dot-confirmed'
  return 'dot-other'
}

const navigateToCase = (testCaseId) => {
  if (!testCaseId) return
  // Save current module selection in sessionStorage for restoration on return
  if (selectedModuleId.value) {
    sessionStorage.setItem('moduleManagement_selectedModuleId', String(selectedModuleId.value))
  }
  router.push(`/testcases/${testCaseId}/detail`)
}
const moduleForm = reactive({
  id: null,
  name: '',
  tag: '',
  parentId: null,
  parentName: '',
  requirementLinks: [],
  rdOwner: ''
})

const requirementLinks = computed(() => {
  if (!selectedModule.value) return []
  const link = selectedModule.value.requirement_link
  if (!link) return []
  return link.split(',').filter(l => l.trim())
})

const editingLinkIndex = ref(null)
const editingLinkValue = ref('')

const startEditLink = (index, currentValue) => {
  editingLinkIndex.value = index
  editingLinkValue.value = currentValue
}

const cancelEditLink = () => {
  editingLinkIndex.value = null
  editingLinkValue.value = ''
}

const saveLink = async (index) => {
  const links = [...requirementLinks.value]
  links[index] = editingLinkValue.value.trim()
  
  try {
    await updateModule(selectedModule.value.id, {
      requirement_link: links.join(',')
    })
    ElMessage.success('链接更新成功')
    // 刷新整个模块树以保持数据同步
    await loadData()
    // 重新选中当前模块
    const updatedModule = findModuleById(selectedModule.value.id)
    if (updatedModule) {
      selectedModule.value = updatedModule
    }
    cancelEditLink()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  }
}

const addNewLink = () => {
  editingLinkIndex.value = '__new__'
  editingLinkValue.value = ''
}

const saveNewLink = async () => {
  if (!editingLinkValue.value.trim()) {
    ElMessage.warning('请输入链接地址')
    return
  }
  
  const links = [...requirementLinks.value, editingLinkValue.value.trim()]
  
  try {
    await updateModule(selectedModule.value.id, {
      requirement_link: links.join(',')
    })
    ElMessage.success('链接添加成功')
    await loadData()
    const updatedModule = findModuleById(selectedModule.value.id)
    if (updatedModule) {
      selectedModule.value = updatedModule
    }
    cancelEditLink()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  }
}

const deleteLink = async (index) => {
  try {
    await ElMessageBox.confirm('确定要删除此链接吗？', '确认删除', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }
  
  const links = [...requirementLinks.value]
  links.splice(index, 1)
  
  try {
    await updateModule(selectedModule.value.id, {
      requirement_link: links.join(',') || ''
    })
    ElMessage.success('链接删除成功')
    await loadData()
    const updatedModule = findModuleById(selectedModule.value.id)
    if (updatedModule) {
      selectedModule.value = updatedModule
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const canEditModuleTag = computed(() => isSuperAdmin.value || hasButton('projects', 'editModuleTag'))
const canAddModule = computed(() => isSuperAdmin.value || hasButton('projects', 'addModule'))
const canEditModule = computed(() => isSuperAdmin.value || hasButton('projects', 'editModule'))
const canDeleteModule = computed(() => isSuperAdmin.value || hasButton('projects', 'deleteModule'))
const canSortModule = computed(() => isSuperAdmin.value || hasButton('projects', 'sortModule'))
const canManageRequirementLink = computed(() => isSuperAdmin.value || hasButton('projects', 'manageRequirementLink'))

const isExpanded = (moduleId) => {
  return moduleId && expandedModules.value.includes(moduleId)
}

const toggleExpand = (moduleId) => {
  if (isExpanded(moduleId)) {
    expandedModules.value = expandedModules.value.filter(id => id !== moduleId)
  } else {
    expandedModules.value.push(moduleId)
  }
}

const handleDragOver = (event, index, parentId = null) => {
  event.preventDefault()
  dragOverIndex.value = index
  dragOverParentId.value = parentId
  event.dataTransfer.dropEffect = 'move'
}

const handleDragLeave = () => {
  dragOverIndex.value = -1
  dragOverParentId.value = null
}

const handleDragStart = (event, module, type, index, parentId = null) => {
  draggedModule.value = module
  draggedType.value = type
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', module.id)
  event.target.closest('.module-item, .module-item-content')?.classList.add('dragging')
}

const handleDragEnd = (event) => {
  event.target.closest('.module-item, .module-item-content')?.classList.remove('dragging')
  dragOverIndex.value = -1
  dragOverParentId.value = null
  if (!draggedModule.value) return
  draggedModule.value = null
  draggedType.value = null
}

const handleDrop = async (event, targetModule, targetSubModule = null, index, parentId = null) => {
  event.target.classList.remove('dragging')
  dragOverIndex.value = -1
  dragOverParentId.value = null
  
  if (!draggedModule.value) return
  
  const draggedItem = draggedModule.value
  
  if (draggedType.value === 'main') {
    // 主模块排序
    const currentOrder = [...moduleTree.value]
    const fromIndex = currentOrder.findIndex(m => m.id === draggedItem.id)
    const toIndex = index
    
    if (fromIndex !== -1 && toIndex !== -1 && fromIndex !== toIndex) {
      const [removed] = currentOrder.splice(fromIndex, 1)
      currentOrder.splice(toIndex, 0, removed)
      
      const moduleOrders = currentOrder.map((m, i) => ({
        id: m.id,
        sort_order: i
      }))
      
      try {
        await sortModules(moduleOrders)
        ElMessage.success('排序更新成功')
        await loadData()
        eventBus.emit('modules-changed')
      } catch (error) {
        ElMessage.error('排序更新失败')
      }
    }
  } else if (draggedType.value === 'sub') {
    // 子模块排序 - 同一父模块下重新排序
    const draggedParentId = draggedItem.parent_id
    
    if (parentId && draggedParentId === parentId) {
      // 同一父模块下的子模块排序
      const parentModule = findModuleById(parentId)
      if (parentModule && parentModule.children) {
        const children = [...parentModule.children]
        const fromIdx = children.findIndex(m => m.id === draggedItem.id)
        const toIdx = children.findIndex(m => m.id === (targetSubModule ? targetSubModule.id : targetModule.id))
        
        if (fromIdx !== -1 && toIdx !== -1 && fromIdx !== toIdx) {
          const [removed] = children.splice(fromIdx, 1)
          children.splice(toIdx, 0, removed)
          
          const moduleOrders = children.map((m, i) => ({
            id: m.id,
            sort_order: i
          }))
          
          try {
            await sortModules(moduleOrders)
            ElMessage.success('排序更新成功')
            await loadData()
            eventBus.emit('modules-changed')
          } catch (error) {
            ElMessage.error('排序更新失败')
          }
        }
      }
    } else if (parentId && draggedParentId !== parentId) {
      // 跨父模块移动
      try {
        await updateModule(draggedItem.id, { 
          parent_id: parentId
        })
        ElMessage.success('移动成功')
        await loadData()
        eventBus.emit('modules-changed')
      } catch (error) {
        console.error('Move failed:', error)
        ElMessage.error(error.response?.data?.detail || '移动失败')
      }
    }
  }
  
  draggedModule.value = null
  draggedType.value = null
}

const breadcrumbPath = computed(() => {
  if (!selectedModule.value) return []
  const path = []
  let current = selectedModule.value
  while (current.parent) {
    path.unshift({ id: current.parent.id, name: current.parent.name })
    current = current.parent
  }
  path.push({ id: selectedModule.value.id, name: selectedModule.value.name })
  return path
})

const filteredModuleTree = computed(() => {
  if (!searchKeyword.value) return moduleTree.value
  const keyword = searchKeyword.value.toLowerCase()
  
  // 递归过滤：保留匹配的节点及其祖先路径
  const filterTree = (nodes) => {
    return nodes.reduce((acc, node) => {
      const nameMatch = node.name.toLowerCase().includes(keyword)
      const filteredChildren = node.children ? filterTree(node.children) : []
      if (nameMatch || filteredChildren.length > 0) {
        acc.push({ ...node, children: filteredChildren })
      }
      return acc
    }, [])
  }
  return filterTree(moduleTree.value)
})

// 将树形模块扁平化为列表（根据展开状态），支持任意深度
const flatModuleList = computed(() => {
  const result = []
  const flatten = (nodes, depth, parent) => {
    nodes.forEach((node, index) => {
      result.push({ module: node, depth, parent, index })
      if (node.children && node.children.length > 0 && isExpanded(node.id)) {
        flatten(node.children, depth + 1, node)
      }
    })
  }
  flatten(filteredModuleTree.value, 0, null)
  return result
})

// 搜索时自动展开匹配的父模块并定位到第一个匹配项
watch(searchKeyword, (keyword) => {
  if (!keyword) return
  const kw = keyword.toLowerCase()
  
  // 收集所有包含匹配子节点的父模块ID
  const idsToExpand = []
  let firstMatchId = null
  
  const walkTree = (nodes, parentIds = []) => {
    for (const node of nodes) {
      const match = node.name.toLowerCase().includes(kw)
      if (match && !firstMatchId) {
        firstMatchId = node.id
        idsToExpand.push(...parentIds)
      }
      if (node.children && node.children.length > 0) {
        walkTree(node.children, [...parentIds, node.id])
      }
    }
  }
  walkTree(moduleTree.value)
  
  // 展开所有需要展开的父模块
  for (const id of idsToExpand) {
    if (!expandedModules.value.includes(id)) {
      expandedModules.value.push(id)
    }
  }
  
  // 滚动到第一个匹配项
  if (firstMatchId) {
    nextTick(() => {
      const el = document.querySelector(`.module-item[data-module-id="${firstMatchId}"]`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    })
  }
})

const goBack = () => router.push('/projects')
const goToProject = () => router.push('/projects')

const navigateToCrumb = (index) => {
  if (index < breadcrumbPath.value.length - 1) {
    const targetModule = breadcrumbPath.value[index]
    const module = findModuleById(targetModule.id)
    if (module) handleModuleClick(module)
  }
}

const findModuleById = (id) => {
  const findInTree = (modules) => {
    for (const m of modules) {
      if (m.id === id) return m
      if (m.children) {
        const found = findInTree(m.children)
        if (found) return found
      }
    }
    return null
  }
  return findInTree(moduleTree.value)
}

const loadProjectInfo = async () => {
  try {
    const res = await getProjects({ id: Number(projectId.value), page: 1, size: 1 })
    if (res.data?.records?.length > 0) {
      projectName.value = res.data.records[0].name
      // 存储项目名称供数据埋点使用
      sessionStorage.setItem(`project_name_${projectId.value}`, res.data.records[0].name)
    }
  } catch (error) {
    console.error('获取项目信息失败:', error)
  }
}

const buildParentChain = (modules, parent = null, parentTag = null) => {
  for (const module of modules) {
    module.parent = parent
    module.inheritedTag = parentTag || module.tag || ''
    if (module.children && module.children.length > 0) {
      buildParentChain(module.children, module, module.inheritedTag)
    }
  }
}

const loadData = async () => {
  const pid = projectId.value
  if (!pid) return
  
  loading.value = true
  try {
    // 加载项目信息
    const projectRes = await getProjects({ id: pid, page: 1, size: 1 })
    if (projectRes.data?.records?.length > 0) {
      projectName.value = projectRes.data.records[0].name
    }
    
    // 加载模块树
    const moduleRes = await getModuleTree(pid)
    moduleTree.value = moduleRes.data || []
    buildParentChain(moduleTree.value)
    
    // 恢复选中状态
    // 先尝试从 sessionStorage 恢复（从用例详情页返回时）
    if (!selectedModuleId.value) {
      const savedId = sessionStorage.getItem('moduleManagement_selectedModuleId')
      if (savedId) {
        selectedModuleId.value = Number(savedId)
        sessionStorage.removeItem('moduleManagement_selectedModuleId')
      }
    }
    
    if (selectedModuleId.value) {
      const currentModule = findModuleById(selectedModuleId.value)
      if (currentModule) {
        selectedModule.value = currentModule
        // 确保父模块展开
        if (currentModule.parent_id && !expandedModules.value.includes(currentModule.parent_id)) {
          expandedModules.value.push(currentModule.parent_id)
        }
      } else {
        // 之前选中的模块已不存在，选第一个
        selectedModuleId.value = moduleTree.value.length > 0 ? moduleTree.value[0].id : null
        selectedModule.value = moduleTree.value.length > 0 ? moduleTree.value[0] : null
      }
    } else if (moduleTree.value.length > 0) {
      selectedModuleId.value = moduleTree.value[0].id
      selectedModule.value = moduleTree.value[0]
    }
  } catch (error) {
    console.error('加载数据失败:', error)
    ElMessage.error('加载数据失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

const handleModuleClick = (module) => {
  selectedModuleId.value = module.id
  selectedModule.value = module
  currentParentModule.value = null
}

const handleSubModuleClick = (subModule, parentModule) => {
  subModule.parent = parentModule
  selectedModuleId.value = subModule.id
  selectedModule.value = subModule
  currentParentModule.value = parentModule
}

const handleAddModule = () => {
  cancelEditLink()
  moduleForm.id = null
  moduleForm.name = ''
  moduleForm.tag = ''
  moduleForm.parentId = null
  moduleForm.parentName = ''
  moduleForm.requirementLinks = ['']
  moduleEditTitle.value = t('module.addModule')
  moduleEditVisible.value = true
}

const handleAddSubModuleFromTree = () => {
  if (selectedModuleId.value && selectedModule.value) {
    handleAddSubModule(selectedModule.value)
  } else {
    ElMessage.warning('请先选择一个模块')
  }
}

const handleAddSubModule = (parentModule) => {
  cancelEditLink()
  moduleForm.id = null
  moduleForm.name = ''
  moduleForm.tag = ''
  moduleForm.parentId = parentModule.id
  moduleForm.parentName = parentModule.name
  moduleForm.requirementLinks = ['']
  moduleEditTitle.value = t('module.addSubModule')
  moduleEditVisible.value = true
}

const handleEditSubModule = (subModule, parentModule) => {
  cancelEditLink()
  moduleForm.id = subModule.id
  moduleForm.name = subModule.name
  moduleForm.tag = subModule.tag || ''
  moduleForm.parentId = subModule.parent_id
  moduleForm.parentName = parentModule.name
  const link = subModule.requirement_link || ''
  moduleForm.requirementLinks = link ? link.split(',').filter(l => l.trim()) : ['']
  moduleEditTitle.value = t('module.editSubModule')
  moduleEditVisible.value = true
}

const handleEditModule = (module) => {
  cancelEditLink()
  moduleForm.id = module.id
  moduleForm.name = module.name
  moduleForm.tag = module.tag || ''
  moduleForm.parentId = module.parent_id
  moduleForm.parentName = module.parent?.name || ''
  const link = module.requirement_link || ''
  moduleForm.requirementLinks = link ? link.split(',').filter(l => l.trim()) : ['']
  moduleForm.rdOwner = module.rd_owner || ''
  moduleEditTitle.value = t('module.editModule')
  moduleEditVisible.value = true
}

const addFormLink = () => {
  moduleForm.requirementLinks.push('')
}

const removeFormLink = (index) => {
  moduleForm.requirementLinks.splice(index, 1)
}

const handleDeleteModule = async (module) => {
  if (!module.id) return ElMessage.warning('多项目模式下无法删除')

  const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
  const isSuperAdmin = currentUser.username === 'admin' || currentUser.username === 'super'
  
  // 超管删除带子模块的主模块：整个模块树（含子模块和用例）一起删除
  if (isSuperAdmin && module.children?.length > 0) {
    try {
      await ElMessageBox.confirm(
        `确定要删除模块"${module.name}"及其所有子模块吗？\n\n这将同时删除该模块下的所有用例，且不可恢复！`,
        '超级管理员删除确认',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      await deleteModule(module.id)
      ElMessage.success('删除成功（含子模块及用例）')
      await loadData()
      eventBus.emit('modules-changed')
      
      if (selectedModuleId.value === module.id) {
        selectedModuleId.value = null
        selectedModule.value = null
      }
    } catch (error) {
      if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || '删除失败')
    }
    return
  }
  
  // 原有逻辑
  if (module.count > 0) return ElMessage.warning('该模块下有用例，无法删除')
  if (module.children?.length > 0) return ElMessage.warning('该模块下有子模块，无法删除')
  
  try {
    await ElMessageBox.confirm(`确定要删除模块"${module.name}"吗？`, '删除确认', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await deleteModule(module.id)
    ElMessage.success('删除成功')
    await loadData()
    eventBus.emit('modules-changed')
    
    if (selectedModuleId.value === module.id) {
      selectedModuleId.value = null
      selectedModule.value = null
    }
  } catch (error) {
    if (error !== 'cancel') ElMessage.error(error.response?.data?.detail || '删除失败')
  }
}

const handleSaveModule = async () => {
  if (!moduleForm.name?.trim()) return ElMessage.warning('请输入模块名称')
  if (!projectId.value) return ElMessage.error('用例库ID无效')
  
  const links = moduleForm.requirementLinks.filter(l => l.trim()).join(',')
  
  moduleSaving.value = true
  try {
    if (moduleForm.id) {
      const updateData = { name: moduleForm.name.trim() }
      if (canEditModuleTag.value && !moduleForm.parentId) updateData.tag = moduleForm.tag || null
      updateData.requirement_link = links || ''
      if (!moduleForm.parentId) updateData.rd_owner = moduleForm.rdOwner || null
      await updateModule(moduleForm.id, updateData)
      ElMessage.success('更新成功')
    } else {
      const createData = {
        project_id: Number(projectId.value),
        name: moduleForm.name.trim(),
        parent_id: moduleForm.parentId ? Number(moduleForm.parentId) : null
      }
      if (!moduleForm.parentId) {
        createData.tag = moduleForm.tag || null
        createData.rd_owner = moduleForm.rdOwner || null
      }
      createData.requirement_link = links || ''
      await createModule(createData)
      ElMessage.success('创建成功')
    }
    moduleEditVisible.value = false
    
    await loadData()
    eventBus.emit('modules-changed')
    
    if (moduleForm.id) {
      const updatedModule = findModuleById(moduleForm.id)
      if (updatedModule) {
        selectedModule.value = updatedModule
        selectedModuleId.value = moduleForm.id
      }
    } else if (moduleForm.parentId) {
      const parentModule = findModuleById(moduleForm.parentId)
      if (parentModule) {
        selectedModule.value = parentModule
        selectedModuleId.value = moduleForm.parentId
      }
    }
  } catch (error) {
    console.error('模块操作失败:', error)
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    moduleSaving.value = false
  }
}

onMounted(() => {
  loadData()
})

const loadModulePRLinks = async () => {
  if (!selectedModule.value?.id) {
    modulePRLinks.value = []
    return
  }
  prLinksLoading.value = true
  try {
    const res = await getModulePRLinks(selectedModule.value.id)
    modulePRLinks.value = res.data || []
  } catch (error) {
    console.error('加载PR列表失败:', error)
    modulePRLinks.value = []
  } finally {
    prLinksLoading.value = false
  }
}

const loadAllPrLinks = async () => {
  if (!projectId.value) {
    allPrLinks.value = []
    return
  }
  allPrLinksLoading.value = true
  try {
    const res = await getProjectAllPRLinks(projectId.value)
    allPrLinks.value = res.data || []
  } catch (error) {
    console.error('加载所有模块PR失败:', error)
    allPrLinks.value = []
  } finally {
    allPrLinksLoading.value = false
  }
}

watch(() => route.params.projectId, (newVal) => {
  if (newVal) {
    projectName.value = ''
    selectedModuleId.value = null
    selectedModule.value = null
    expandedModules.value = []
    loadData()
  }
})

watch([() => selectedModule.value?.id, activeView], ([moduleId, view]) => {
  prCurrentPage.value = 1
  allPrCurrentPage.value = 1
  if (moduleId && view === 'pr') {
    loadModulePRLinks()
  } else if (view === 'allPr') {
    loadAllPrLinks()
  } else {
    modulePRLinks.value = []
  }
})
</script>

<style scoped>
.module-management-page {
  display: flex;
  background: #f8f9fa;
  padding: 0;
  margin: -24px;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.module-tree-column {
  width: 280px;
  min-width: 280px;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  margin: 12px 0 12px 12px;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.tree-header {
  padding: 16px;
  border-bottom: 1px solid #f3f4f5;
}

.search-box {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.back-btn {
  flex-shrink: 0;
}

.search-icon {
  position: absolute;
  left: 74px;
  top: 50%;
  transform: translateY(-50%);
  color: #9ca3af;
  font-size: 16px;
  z-index: 1;
  pointer-events: none;
}

.search-input {
  width: 100%;
  padding: 12px 16px 12px 48px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  font-size: 14px;
  outline: none;
  background: #f9fafb;
  transition: all 0.2s;
}

.search-input:focus {
  border-color: #6366f1;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

.view-toggle {
  display: flex;
  gap: 10px;
}

.toggle-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
  background: #f9fafb;
  color: #6366f1;
}

.toggle-btn:hover {
  background: #eef2ff;
}

.toggle-btn.active {
  background: #6366f1;
  color: #fff;
}

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.module-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.module-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.module-item:hover {
  background: #f9fafb;
}

.module-item.active {
  background: #eef2ff;
}

.module-item.dragging {
  opacity: 0.5;
  background: #f3f4f6;
}

.module-item.drag-over {
  border-top: 2px solid #6366f1;
  margin-top: -2px;
}

.module-item.main-module {
  font-weight: 500;
}

.module-item.sub-module {
  /* padding-left controlled by inline style for dynamic depth */
}

.module-item.sub-module.child-module {
  /* padding-left controlled by inline style for dynamic depth */
}

.sub-module-list {
  border-left: 2px solid #e5e7eb;
  margin-left: 32px;
  padding-left: 0;
}

.sub-module-wrapper {
  display: flex;
  flex-direction: column;
}

.sub-module-wrapper .module-item-content {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  width: 100%;
}

.sub-module-wrapper .module-item-content:hover {
  background: #f9fafb;
}

.drag-handle {
  color: #cbd5e1;
  cursor: grab;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
}

.drag-handle:active {
  cursor: grabbing;
}

.drag-handle:hover .drag-dots span {
  background: #64748b;
}

.drag-dots {
  display: grid;
  grid-template-columns: repeat(2, 3px);
  grid-template-rows: repeat(3, 3px);
  gap: 2px;
}

.drag-dots span {
  width: 3px;
  height: 3px;
  background: #cbd5e1;
  border-radius: 50%;
  transition: background 0.2s;
}

.module-item.main-module .drag-handle {
  margin-top: -4px;
}

.module-item.main-module .drag-dots {
  gap: 3px;
}

.module-item.main-module .drag-dots span {
  width: 4px;
  height: 4px;
}

.expand-icon {
  color: #9ca3af;
  font-size: 16px;
  cursor: pointer;
}

.expand-icon-placeholder {
  width: 16px;
  height: 16px;
}

.sub-arrow {
  color: #9ca3af;
  font-size: 14px;
}

.module-icon {
  font-size: 20px;
}

.module-icon.folder,
.module-icon.doc {
  color: #6366f1;
}

.module-name {
  flex: 1;
  font-size: 14px;
  color: #111827;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.module-item.active .module-name {
  color: #6366f1;
}

.module-count-badge {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  background: #f3f4f6;
  padding: 4px 10px;
  border-radius: 6px;
}

.tree-footer {
  padding: 16px 20px;
  border-top: 1px solid #f3f4f5;
}

.add-main-module-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 14px;
  border: 2px dashed #d1d5db;
  border-radius: 10px;
  background: transparent;
  color: #6b7280;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
  cursor: pointer;
  transition: all 0.2s;
}

.add-main-module-btn:hover {
  border-color: #6366f1;
  color: #6366f1;
  background: #fafafa;
}

.detail-column {
  flex: 1;
  padding: 12px;
  overflow: hidden;
}

.detail-card {
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  display: flex;
  height: 100%;
}

.detail-card .card-inner {
  padding: 24px;
  overflow-y: auto;
  width: 340px;
  min-width: 340px;
  flex-shrink: 0;
}

.card-divider {
  width: 1px;
  background: #e5e7eb;
  flex-shrink: 0;
}

.detail-right-section {
  flex: 1;
  min-width: 0;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.detail-content {
  max-width: 900px;
  margin: 0 auto;
}

.module-title {
  font-family: 'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
  margin: 0 0 16px 0;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
  flex-wrap: wrap;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.crumb {
  color: #6b7280;
  cursor: pointer;
}

.crumb.clickable:hover {
  color: #6366f1;
  text-decoration: underline;
}

.crumb.active {
  color: #111827;
}

.crumb-separator {
  color: #d1d5db;
  font-size: 12px;
}

.meta-divider {
  width: 1px;
  height: 20px;
  background: #d1d5db;
}

.meta-tags {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 6px 14px;
  border-radius: 20px;
}

.status-tag.stable {
  background: #d1fae5;
  color: #059669;
}

.status-tag.cases {
  background: #eef2ff;
  color: #6366f1;
}

.actions-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
}

.action-btn .el-icon {
  font-size: 18px;
}

.requirement-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

.requirement-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.4);
}

.requirement-btn .btn-text {
  max-width: 200px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.requirement-btn .external-icon {
  opacity: 0.7;
}

.edit-btn {
  background: #fff;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.edit-btn:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.add-link-btn {
  background: #fff;
  color: #6366f1;
  border: 1px solid #e5e7eb;
}

.add-link-btn:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.15);
}

.add-sub-btn {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  border: none;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

.add-sub-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.4);
}

.action-btn.danger {
  background: #fff;
  color: #dc2626;
  border: 1px solid #fecaca;
}

.action-btn.danger:hover {
  border-color: #dc2626;
  background: #fef2f2;
}

.current-module-section {
  margin-bottom: 20px;
}

.current-position {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  background: linear-gradient(135deg, #f8fafc, #f1f5f9);
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.current-position .position-left {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.current-position .position-tag {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  background: linear-gradient(135deg, #3366ff, #4f46e5);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  border-radius: 16px;
}

.current-position .position-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #fff;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.icon-btn:hover {
  background: #f1f5f9;
  color: #3366ff;
}

.icon-btn.danger:hover {
  color: #dc2626;
  background: #fef2f2;
}

.icon-btn.success {
  color: #16a34a;
}

.icon-btn.success:hover {
  background: #dcfce7;
}

.icon-btn.small {
  width: 24px;
  height: 24px;
  font-size: 12px;
}

.icon-btn .el-icon {
  font-size: 14px;
}

.requirement-section {
  margin-bottom: 24px;
}

.requirement-links {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.requirement-link-row {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.requirement-link-row .requirement-link {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  color: #3366ff;
  text-decoration: none;
  font-size: 13px;
  word-break: break-all;
  transition: all 0.2s;
}

.requirement-link-row .requirement-link:hover {
  background: #eff6ff;
  border-color: #3366ff;
}

.requirement-link-row .requirement-link .link-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

.link-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: #94a3b8;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.link-actions {
  display: flex;
  align-items: center;
  gap: 4px;
}

.link-action-btn:hover {
  background: #e2e8f0;
  color: #3366ff;
}

.link-action-btn.danger:hover {
  background: #fef2f2;
  color: #dc2626;
}

.link-edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.link-edit-row .el-input {
  flex: 1;
}

.add-link-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: #fff;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  color: #64748b;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.add-link-btn:hover {
  border-color: #3366ff;
  color: #3366ff;
  background: #eff6ff;
}

.form-links-edit {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.form-link-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.form-link-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 10px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  transition: all 0.2s;
  height: 32px;
}

.form-link-input-wrapper:focus-within {
  background: #fff;
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

.form-link-input-wrapper .form-link-icon {
  color: #6366f1;
  font-size: 14px;
  flex-shrink: 0;
}

.form-link-input-wrapper .el-input {
  flex: 1;
}

.form-link-input-wrapper .el-input :deep(.el-input__wrapper) {
  box-shadow: none !important;
  padding: 0;
  background: transparent;
  height: 30px;
}

.form-link-item .el-input {
  flex: 1;
}

.requirement-link:hover {
  background: #e0e7ff;
}

.requirement-link .external-icon {
  margin-left: auto;
  flex-shrink: 0;
}

.section-divider {
  height: 1px;
  background: #e5e7eb;
  margin-bottom: 24px;
}

.rd-owner-section {
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
}

.rd-owner-value {
  font-size: 14px;
  color: #374151;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.execution-views {
  margin-bottom: 24px;
}

.section-label {
  font-size: 12px;
  font-weight: 600;
  color: #6b7280;
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header .section-label {
  margin-bottom: 0;
}

.action-btn.add-sub-btn.small {
  padding: 8px 16px;
  font-size: 11px;
}

.action-btn.add-sub-btn.small .el-icon {
  font-size: 14px;
}

.view-cards {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.view-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  border: 1px solid #e5e7eb;
}

.view-card:hover {
  border-color: #c7d2fe;
  background: #fafafe;
}

.view-card-active {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
}

.view-card-active:hover {
  background: linear-gradient(135deg, #6366f1, #4f46e5);
  border-color: transparent;
  box-shadow: 0 12px 32px rgba(99, 102, 241, 0.4);
}

.card-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: #f3f4f6;
  color: #6b7280;
}

.view-card-active .card-icon {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  margin: 0;
}

.card-arrow {
  font-size: 18px;
  opacity: 0.4;
  transition: all 0.2s;
  color: #9ca3af;
}

.view-card-active .card-arrow {
  color: #fff;
  opacity: 0.7;
}

.view-card:hover .card-arrow {
  opacity: 1;
  transform: translateX(4px);
}

.sub-modules-section {
  background: #fff;
  border-radius: 16px;
  height: 100%;
}

.sub-modules-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.sub-module-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 20px;
  background: #f9fafb;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.sub-module-row:hover {
  background: #f3f4f6;
}

.sub-info {
  display: flex;
  align-items: center;
  gap: 14px;
}

.sub-icon {
  color: #6366f1;
  font-size: 22px;
}

.sub-name {
  font-size: 15px;
  font-weight: 600;
  color: #111827;
}

.sub-requirement-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  color: #6366f1;
  text-decoration: none;
  border-radius: 4px;
  transition: all 0.2s;
}

.sub-requirement-link:hover {
  background: #eef2ff;
}

.sub-count {
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  background: #e5e7eb;
  padding: 4px 10px;
  border-radius: 6px;
}

.sub-actions {
  display: flex;
  gap: 10px;
}

.sub-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  color: #6366f1;
  border: 1px solid #e5e7eb;
}

.sub-action-btn:hover {
  background: #eef2ff;
  border-color: #6366f1;
}

.sub-action-btn.danger {
  color: #ef4444;
}

.sub-action-btn.danger:hover {
  background: #fef2f2;
  border-color: #ef4444;
}

.empty-submodules {
  text-align: center;
  padding: 40px;
  color: #9ca3af;
}

.empty-submodules p {
  margin: 0;
}

.empty-detail {
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.empty-state {
  text-align: center;
}

.empty-state h2 {
  font-size: 24px;
  font-weight: 700;
  color: #374151;
  margin: 24px 0 12px;
}

.empty-state p {
  font-size: 15px;
  color: #9ca3af;
  margin: 0;
}

.form-tip {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

.module-edit-dialog .el-dialog__header {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  padding: 20px 24px;
  margin: 0;
  border-radius: 8px 8px 0 0;
}

.module-edit-dialog .el-dialog__title {
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.module-edit-dialog .el-dialog__headerbtn .el-dialog__close {
  color: #fff;
}

.module-edit-dialog .el-dialog__body {
  padding: 24px;
}

.module-edit-dialog .el-form-item__label {
  font-weight: 500;
  color: #374151;
}

.module-edit-dialog .el-input__wrapper {
  border-radius: 8px;
}

.module-edit-dialog .el-input__wrapper:focus-within {
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.module-edit-dialog .el-dialog__footer {
  padding: 16px 24px 24px;
  border-top: 1px solid #f0f0f0;
}

.module-edit-dialog .el-button {
  border-radius: 8px;
  padding: 10px 20px;
}

.module-edit-dialog .el-button--primary {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  border: none;
}

.module-edit-dialog .el-button--primary:hover {
  background: linear-gradient(135deg, #5558e3 0%, #4338ca 100%);
}

/* PR列表样式 */
.pr-list-section {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.pr-list-section .el-table {
  flex: 1;
}

.pr-id-link {
  font-size: 13px;
  font-weight: 600;
  color: #6366f1;
  text-decoration: none;
  cursor: pointer;
}

.pr-id-link:hover {
  text-decoration: underline;
  color: #4f46e5;
}

.pr-status-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
  margin-right: 6px;
  vertical-align: middle;
}

.pr-status-dot.dot-closed { background: #9ca3af; }
.pr-status-dot.dot-confirmed { background: #22c55e; }
.pr-status-dot.dot-other { background: #f59e0b; }

.pr-status-text {
  font-size: 12px;
  color: #374151;
  vertical-align: middle;
}

.pr-severity {
  font-size: 12px;
  color: #6b7280;
}

.pr-case {
  font-size: 12px;
  color: #6366f1;
  font-weight: 500;
}

.pr-case-link {
  font-size: 12px;
  color: #6366f1;
  font-weight: 500;
  cursor: pointer;
  text-decoration: none;
}

.pr-case-link:hover {
  text-decoration: underline;
  color: #4f46e5;
}

.pr-pagination {
  display: flex;
  justify-content: flex-end;
  padding: 12px 0 0;
}

/* 响应式适配 */
@media (max-width: 1440px) {
  .module-tree-column {
    width: 260px;
    min-width: 260px;
  }
}

@media (max-width: 1200px) {
  .module-tree-column {
    width: 240px;
    min-width: 240px;
  }
  .detail-card {
    flex-direction: column;
  }
  .detail-card .card-inner {
    width: auto;
    min-width: 0;
  }
  .card-divider {
    width: auto;
    height: 1px;
  }
  .detail-column {
    padding: 8px;
  }
}

@media (max-width: 1024px) {
  .module-management-page {
    flex-direction: column;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }
  .module-tree-column {
    width: auto;
    min-width: auto;
    max-height: 300px;
    margin: 8px 8px 0 8px;
  }
  .detail-column {
    flex: 1;
    padding: 8px;
  }
  .detail-card {
    flex-direction: column;
  }
  .card-divider {
    width: auto;
    height: 1px;
  }
  .view-cards {
    flex-direction: row;
  }
  .view-card {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .module-management-page {
    height: auto;
  }
  .module-tree-column {
    max-height: 250px;
    margin: 6px;
  }
  .tree-header {
    padding: 12px;
  }
  .view-toggle {
    flex-direction: column;
    gap: 6px;
  }
  .detail-column {
    padding: 6px;
  }
  .detail-card .card-inner {
    padding: 16px;
  }
  .detail-right-section {
    padding: 16px;
  }
  .module-title {
    font-size: 18px;
  }
  .meta-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 16px;
  }
  .meta-divider {
    display: none;
  }
  .current-position {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .view-cards {
    flex-direction: column;
  }
}
</style>