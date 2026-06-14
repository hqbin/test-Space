<template>
  <div class="organization-page">
    <el-card class="table-card" shadow="never">
      <div class="table-header">
        <div class="header-left">
          <div class="action-buttons">
            <el-button 
              v-if="hasButton('organization', 'create')"
              type="primary" 
              :icon="Plus" 
              @click="handleCreateDepartment"
            >
              {{ $t('organization.createOrg') }}
            </el-button>
          </div>
        </div>
        <div class="header-right">
          <el-input
            v-model="departmentSearch"
            :placeholder="$t('organization.searchPlaceholder')"
            clearable
            style="width: 250px;"
            size="large"
            @input="handleDepartmentSearch"
            @clear="handleDepartmentSearch"
          >
            <template #suffix>
              <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleDepartmentSearch">
                <Search />
              </el-icon>
            </template>
          </el-input>
        </div>
      </div>
      
      <div class="organization-content">
        <!-- 组织列表 -->
        <div class="department-section">
          <h3 class="section-title">{{ $t('organization.title') }}</h3>
          <div class="table-wrapper">
            <div class="table-container" ref="departmentTableContainerRef">
              <el-table 
                ref="departmentTableRef"
                :data="departments" 
                style="width: 100%"
                :height="departmentTableHeight"
                :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
              >
                <el-table-column prop="name" :label="$t('organization.orgName')" min-width="200" />
                <el-table-column prop="description" :label="$t('common.description')" min-width="300" :show-overflow-tooltip="{ showAfter: 500 }" />
                <el-table-column :label="$t('organization.manager')" min-width="200">
                  <template #default="scope">
                    {{ scope.row.manager_names?.join(', ') || '-' }}
                  </template>
                </el-table-column>
                <el-table-column :label="$t('organization.relatedTeams')" min-width="200">
                  <template #default="scope">
                    {{ scope.row.project_group_names?.join(', ') || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" :label="$t('common.createdAt')" min-width="180">
                  <template #default="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.operation')" min-width="350" align="center" fixed="right">
                  <template #default="scope">
                    <el-button v-if="hasButton('organization', 'edit')" type="primary" size="default" @click="handleEditDepartment(scope.row)">{{ $t('common.edit') }}</el-button>
                    <el-button v-if="hasButton('organization', 'manageTeams')" type="info" size="default" @click="showProjectGroups(scope.row)">{{ $t('organization.teamManagement') }}</el-button>
                    <el-button v-if="hasButton('organization', 'manageMembers')" type="warning" size="default" @click="showDepartmentMembers(scope.row)">{{ $t('organization.memberManagement') }}</el-button>
                    <el-button v-if="hasButton('organization', 'delete')" type="danger" size="default" @click="handleDeleteDepartment(scope.row)">{{ $t('common.delete') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
        
        <!-- 项目组列表 -->
        <div v-if="selectedDepartment && !showMembersSection" class="project-group-section">
          <div class="section-header">
            <div class="section-header-left">
              <h3 class="section-title-inline">{{ selectedDepartment.name }} - {{ $t('organization.teamManagement') }}</h3>
              <div class="action-buttons">
                <el-button type="primary" :icon="Plus" @click="handleCreateProjectGroup">
                  {{ $t('organization.createTeam') }}
                </el-button>
              </div>
            </div>
            <div class="section-header-right">
              <el-input
                v-model="projectGroupSearch"
                :placeholder="$t('organization.searchTeamPlaceholder')"
                clearable
                style="width: 250px;"
                size="large"
                @input="handleProjectGroupSearch"
                @clear="handleProjectGroupSearch"
              >
                <template #suffix>
                  <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleProjectGroupSearch">
                    <Search />
                  </el-icon>
                </template>
              </el-input>
            </div>
          </div>
          <div class="table-wrapper">
            <div class="table-container" ref="projectGroupTableContainerRef">
              <el-table 
                ref="projectGroupTableRef"
                :data="projectGroups" 
                style="width: 100%"
                :height="projectGroupTableHeight"
                v-loading="loadingProjectGroups"
                :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
              >
                <el-table-column prop="id" label="ID" width="80" />
                <el-table-column prop="name" :label="$t('organization.teamName')" min-width="150" />
                <el-table-column prop="description" :label="$t('common.description')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
                <el-table-column :label="$t('organization.teamLeader')" min-width="180">
                  <template #default="{ row }">
                    {{ row.leader_names?.join('、') || row.leader_name || '-' }}
                  </template>
                </el-table-column>
                <el-table-column prop="member_count" :label="$t('organization.memberCount')" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag type="info">{{ row.member_count || 0 }} {{ $t('organization.personUnit') }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column :label="$t('organization.authorizeProjects')" width="220" align="center">
                  <template #default="{ row }">
                    <div v-if="row.projectNames && row.projectNames.length > 0" class="project-tags-wrapper">
                      <el-tag type="warning" size="small" effect="plain" class="project-tag">{{ row.projectNames[0] }}</el-tag>
                      <el-tag v-if="row.projectNames.length > 1" type="warning" size="small" effect="plain" class="project-tag-more">+{{ row.projectNames.length - 1 }}</el-tag>
                      <el-tooltip v-if="row.projectNames.length > 1" effect="dark" placement="top" :show-after="500">
                        <template #content>
                          <div v-for="(name, idx) in row.projectNames" :key="idx">{{ name }}</div>
                        </template>
                        <span class="tooltip-trigger"></span>
                      </el-tooltip>
                    </div>
                    <span v-else style="color: #909399;">-</span>
                  </template>
                </el-table-column>
                <el-table-column prop="status" :label="$t('common.status')" width="100" align="center">
                  <template #default="{ row }">
                    <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}</el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="created_at" :label="$t('common.createdAt')" width="180">
                  <template #default="scope">
                    {{ formatDate(scope.row.created_at) }}
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.operation')" width="280">
                  <template #default="{ row }">
                    <el-button link type="primary" @click="handleEditProjectGroup(row)"><el-icon><Edit /></el-icon>{{ $t('common.edit') }}</el-button>
                    <el-button link type="primary" @click="handleAssignProjects(row)"><el-icon><Folder /></el-icon>{{ $t('organization.authorize') }}</el-button>
                    <el-button link type="primary" @click="handleViewMembers(row)"><el-icon><User /></el-icon>{{ $t('organization.memberManagement') }}</el-button>
                    <el-button link type="danger" @click="handleDeleteProjectGroup(row)"><el-icon><Delete /></el-icon>{{ $t('common.delete') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
        
        <!-- 组织成员列表 -->
        <div v-if="selectedDepartment && showMembersSection" class="department-members-section">
          <h3 class="section-title">
            {{ selectedDepartment.name }} - {{ $t('organization.memberManagement') }}
            <el-button type="primary" :icon="Plus" @click="showAddMemberDialog" style="margin-left: 20px">{{ $t('organization.addMember') }}</el-button>
          </h3>
          <div class="table-wrapper">
            <div class="table-container" ref="membersTableContainerRef">
              <el-table 
                ref="membersTableRef"
                :data="departmentMembers" 
                style="width: 100%"
                :height="membersTableHeight"
                :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
              >
                <el-table-column prop="username" :label="$t('user.username')" min-width="150" />
                <el-table-column prop="email" :label="$t('user.email')" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
                <el-table-column :label="$t('common.operation')" min-width="150" align="center">
                  <template #default="scope">
                    <el-button type="danger" size="default" @click="removeDepartmentMember(scope.row)">{{ $t('organization.removeMember') }}</el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 组织编辑对话框 -->
    <el-dialog v-model="departmentDialogVisible" :title="departmentDialogTitle" width="600px" :close-on-click-modal="false">
      <el-form :model="departmentForm" ref="departmentFormRef" label-width="100px" label-position="top">
        <el-form-item :label="$t('organization.orgName')" required>
          <el-input v-model="departmentForm.name" :placeholder="$t('organization.inputOrgName')" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item :label="$t('organization.manager')" required>
          <el-select 
            v-model="departmentForm.manager_ids" 
            multiple 
            :placeholder="$t('organization.selectManager')" 
            style="width: 100%" 
            filterable 
            remote 
            :remote-method="handleManagerSearch"
            @focus="loadUsers"
          >
            <el-option v-for="user in users" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('common.description')">
          <el-input v-model="departmentForm.description" type="textarea" :rows="2" :placeholder="$t('organization.inputDescription')" maxlength="255" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="departmentDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmitDepartment" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
    
    <!-- 添加组织成员对话框 -->
    <el-dialog v-model="addMemberDialogVisible" :title="$t('organization.addMember')" width="600px" :close-on-click-modal="false">
      <el-form :model="addMemberForm" ref="addMemberFormRef" label-width="100px" label-position="top">
        <el-form-item :label="$t('organization.selectUser')" required>
          <el-select v-model="addMemberForm.user_ids" multiple :placeholder="$t('organization.selectMember')" filterable remote :remote-method="remoteSearchUsers" :loading="searchLoading">
            <el-option v-for="user in availableUsers" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addMemberDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddMembers" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 项目组创建/编辑对话框 -->
    <el-dialog v-model="projectGroupDialogVisible" :title="projectGroupDialogTitle" :width="isEditProjectGroup ? '500px' : '700px'" :close-on-click-modal="false">
      <el-form ref="projectGroupFormRef" :model="projectGroupForm" :rules="projectGroupRules" label-width="120px">
        <el-form-item :label="$t('organization.teamName')" prop="name">
          <el-input v-model="projectGroupForm.name" :placeholder="$t('organization.inputTeamName')" />
        </el-form-item>
        <el-form-item :label="$t('common.description')" prop="description">
          <el-input v-model="projectGroupForm.description" type="textarea" :rows="4" :placeholder="$t('organization.inputDescription')" />
        </el-form-item>
        <el-form-item :label="$t('organization.teamLeader')" prop="leader_ids" required>
          <el-select 
            v-model="projectGroupForm.leader_ids" 
            multiple 
            :placeholder="$t('organization.selectTeamLeader')" 
            style="width: 100%" 
            filterable 
            remote 
            :remote-method="handleLeaderSearch"
            :loading="leaderSearchLoading"
            collapse-tags 
            collapse-tags-tooltip
            @focus="loadDepartmentMembersForProjectGroup"
          >
            <el-option v-for="user in leaderOptions" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="!isEditProjectGroup" :label="$t('organization.authorizeProjects')">
          <el-select
            v-model="projectGroupForm.projectIds"
            multiple
            :placeholder="$t('organization.selectProjects')"
            style="width: 100%"
            filterable
            collapse-tags
            collapse-tags-tooltip
          >
            <el-option
              v-for="project in allProjects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">{{ $t('organization.selectedProjects', { count: projectGroupForm.projectIds.length }) }}</div>
        </el-form-item>
        <el-form-item v-if="!isEditProjectGroup" :label="$t('organization.addMember')">
          <el-select 
            v-model="projectGroupForm.userIds" 
            multiple 
            :placeholder="$t('organization.selectMember')" 
            style="width: 100%" 
            filterable
            remote
            :remote-method="handleMemberSearch"
            :loading="memberSearchLoading"
            @focus="loadDepartmentMembersForProjectGroup"
          >
            <el-option v-for="user in allUsers" :key="user.id" :label="user.username" :value="user.id" />
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">{{ $t('organization.selectMemberTip') }}</div>
        </el-form-item>
        <el-form-item v-if="isEditProjectGroup" :label="$t('common.status')" prop="status">
          <el-radio-group v-model="projectGroupForm.status">
            <el-radio :label="1">{{ $t('common.enabled') }}</el-radio>
            <el-radio :label="0">{{ $t('common.disabled') }}</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="projectGroupDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmitProjectGroup" :loading="submittingProjectGroup">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 项目组成员列表对话框 -->
    <el-dialog v-model="pgMembersDialogVisible" :title="$t('organization.teamMembers')" width="700px">
      <div style="margin-bottom: 16px;">
        <el-button type="primary" @click="handleAddPgMembers"><el-icon><Plus /></el-icon>{{ $t('organization.addMember') }}</el-button>
      </div>
      <el-table :data="pgMembers" v-loading="loadingPgMembers">
        <el-table-column prop="username" :label="$t('user.username')" width="150" />
        <el-table-column prop="email" :label="$t('user.email')" min-width="200" />
        <el-table-column :label="$t('common.operation')" width="100" align="center">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleRemovePgMember(row)"><el-icon><Delete /></el-icon>{{ $t('organization.removeMember') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="pgMembersDialogVisible = false">{{ $t('organization.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加项目组成员对话框 -->
    <el-dialog v-model="addPgMembersDialogVisible" :title="$t('organization.addMember')" width="500px" :close-on-click-modal="false">
      <el-select 
        v-model="selectedPgUserIds" 
        multiple 
        :placeholder="$t('organization.selectMemberRequired')" 
        style="width: 100%" 
        filterable
        remote
        :remote-method="handlePgMemberSearch"
        :loading="pgMemberSearchLoading"
        @focus="loadAvailablePgUsers"
      >
        <el-option v-for="user in availablePgUsers" :key="user.id" :label="user.username" :value="user.id" />
      </el-select>
      <div style="margin-top: 8px; font-size: 12px; color: #909399;">{{ $t('organization.selectMemberTip') }}</div>
      <template #footer>
        <el-button @click="addPgMembersDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleAddPgMembersSubmit" :loading="addingPgMembers">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 授权用例库对话框 -->
    <el-dialog v-model="projectsDialogVisible" :title="$t('organization.authorizeProjects')" width="600px" :close-on-click-modal="false">
      <div style="margin-bottom: 16px; color: #606266;">{{ $t('organization.authDescription') }}</div>
      <el-select
        v-model="selectedProjectIds"
        multiple
        :placeholder="$t('organization.selectProjects')"
        style="width: 100%"
        filterable
        collapse-tags
        collapse-tags-tooltip
      >
        <el-option
          v-for="project in allProjects"
          :key="project.id"
          :label="project.name"
          :value="project.id"
        />
      </el-select>
      <div style="margin-top: 8px; font-size: 12px; color: #909399;">{{ $t('organization.selectedProjects', { count: selectedProjectIds.length }) }}</div>
      <template #footer>
        <el-button @click="projectsDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleProjectsSubmit" :loading="submittingProjects">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>


<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { organizationApi } from '../../api/organization'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, User, Folder, Search } from '@element-plus/icons-vue'
import { useTableHeight } from '../../composables/useTableHeight'
import { useLoadingStore } from '../../stores/loading'
import { useUserRole } from '../../composables/useUserRole'
import { getTeams, createTeam, updateTeam, deleteTeam, getTeamMembers, assignProjectsToTeam, getTeamProjects } from '@/api/team'
import { getProjects } from '@/api/project'
import { getUsers } from '@/api/user'
import { assignTeams, removeMember } from '@/api/userTeam'
import { eventBus } from '@/utils/eventBus'

const loadingStore = useLoadingStore()
const { hasButton } = useUserRole()
const { t } = useI18n()

// 组织表格高度
const { tableContainerRef: departmentTableContainerRef, tableHeight: departmentTableHeight, bindTableHeight: bindDepartmentTableHeight } = useTableHeight()
const departmentTableRef = ref(null)

// 项目组表格高度
const { tableContainerRef: projectGroupTableContainerRef, tableHeight: projectGroupTableHeight, bindTableHeight: bindProjectGroupTableHeight } = useTableHeight()
const projectGroupTableRef = ref(null)

// 成员表格高度
const { tableContainerRef: membersTableContainerRef, tableHeight: membersTableHeight, bindTableHeight: bindMembersTableHeight } = useTableHeight()
const membersTableRef = ref(null)

// 数据
const departments = ref([])
const projectGroups = ref([])
const users = ref([])
const selectedDepartment = ref(null)
const submitting = ref(false)
const loadingProjectGroups = ref(false)
const departmentSearch = ref('')

// 组织成员管理
const showMembersSection = ref(false)
const departmentMembers = ref([])
const addMemberDialogVisible = ref(false)
const addMemberForm = reactive({ user_ids: [] })
const addMemberFormRef = ref(null)
const availableUsers = ref([])
const searchLoading = ref(false)

// 组织对话框
const departmentDialogVisible = ref(false)
const departmentDialogTitle = ref('')
const departmentFormRef = ref(null)
const departmentForm = reactive({
  id: null,
  name: '',
  description: '',
  manager_ids: []
})

// 项目组相关
const projectGroupDialogVisible = ref(false)
const projectGroupDialogTitle = ref(t('organization.createTeam'))
const isEditProjectGroup = ref(false)
const submittingProjectGroup = ref(false)
const projectGroupFormRef = ref(null)
const allProjects = ref([])
const allUsers = ref([])
const projectGroupSearch = ref('')

// 搜索相关状态
const leaderSearchLoading = ref(false)
const memberSearchLoading = ref(false)
const pgMemberSearchLoading = ref(false)
const projectGroupForm = reactive({
  id: null,
  name: '',
  description: '',
  status: 1,
  leader_ids: [],
  projectIds: [],
  userIds: []
})
const projectGroupRules = {
  name: [
    { required: true, message: () => t('organization.teamNameRequired'), trigger: 'blur' },
    { min: 2, max: 100, message: () => t('organization.teamNameLength'), trigger: 'blur' }
  ],
  leader_ids: [
    { required: true, type: 'array', min: 1, message: () => t('organization.selectTeamLeader'), trigger: 'change' }
  ]
}

// 项目组成员管理
const pgMembersDialogVisible = ref(false)
const pgMembers = ref([])
const loadingPgMembers = ref(false)
const currentTeamForMembers = ref(null)
const addPgMembersDialogVisible = ref(false)
const selectedPgUserIds = ref([])
const availablePgUsers = ref([])
const addingPgMembers = ref(false)

// 授权用例库
const projectsDialogVisible = ref(false)
const selectedProjectIds = ref([])
const currentTeamId = ref(null)
const submittingProjects = ref(false)
const leaderOptions = ref([])

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// ========== 组织管理 ==========
const loadDepartments = async (search = '') => {
  loadingStore.showLoading()
  try {
    const params = search ? { search } : {}
    const res = await organizationApi.getDepartments(params)
    let departmentData = []
    if (res.data && res.data.records) {
      departmentData = res.data.records
    } else if (Array.isArray(res.data)) {
      departmentData = res.data
    }
    departments.value = departmentData.map(dept => ({
      ...dept,
      project_group_ids: Array.isArray(dept.project_group_ids) ? dept.project_group_ids : [],
      manager_ids: Array.isArray(dept.manager_ids) ? dept.manager_ids : []
    }))
  } catch (error) {
    console.error('Load departments error:', error)
    departments.value = []
    ElMessage.error(t('organization.loadFailed'))
  } finally {
    loadingStore.hideLoading()
  }
}

const handleDepartmentSearch = () => {
  loadDepartments(departmentSearch.value)
}

const loadUsers = async (search = '') => {
  try {
    const { getUserList } = await import('../../api/user')
    const params = search ? { search } : {}
    const res = await getUserList(params)
    users.value = res.data?.records || []
  } catch (error) {
    console.error('Load users error:', error)
    users.value = []
  }
}

// 组织负责人远程搜索
const handleManagerSearch = async (query) => {
  if (!query || !query.trim()) {
    await loadUsers()
    return
  }
  await loadUsers(query.trim())
}

const handleCreateDepartment = () => {
  departmentForm.id = null
  departmentForm.name = ''
  departmentForm.description = ''
  departmentForm.manager_ids = []
  departmentDialogTitle.value = t('organization.createOrg')
  departmentDialogVisible.value = true
  loadUsers()
}

const handleEditDepartment = (row) => {
  departmentForm.id = row.id
  departmentForm.name = row.name
  departmentForm.description = row.description
  departmentForm.manager_ids = Array.isArray(row.manager_ids) ? row.manager_ids : []
  departmentDialogTitle.value = t('organization.editOrg')
  departmentDialogVisible.value = true
  loadUsers()
}

const handleSubmitDepartment = async () => {
  if (!departmentForm.name || !departmentForm.name.trim()) {
    ElMessage.warning(t('organization.inputOrgName'))
    return
  }
  if (!departmentForm.manager_ids || departmentForm.manager_ids.length === 0) {
    ElMessage.warning(t('organization.managerRequired'))
    return
  }
  submitting.value = true
  try {
    const payload = {
      name: departmentForm.name,
      description: departmentForm.description,
      manager_ids: departmentForm.manager_ids
    }
    if (departmentForm.id) {
      await organizationApi.updateDepartment(departmentForm.id, payload)
      ElMessage.success(t('organization.updateSuccess'))
    } else {
      await organizationApi.createDepartment(payload)
      ElMessage.success(t('organization.createSuccess'))
    }
    departmentDialogVisible.value = false
    loadDepartments()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('organization.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const handleDeleteDepartment = async (row) => {
  try {
    await ElMessageBox.confirm(t('organization.deleteConfirm'), t('common.deleteConfirmTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await organizationApi.deleteDepartment(row.id)
    ElMessage.success(t('organization.deleteSuccess'))
    loadDepartments()
    if (selectedDepartment.value?.id === row.id) {
      selectedDepartment.value = null
      projectGroups.value = []
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || t('common.failed'))
    }
  }
}

// ========== 项目组管理 ==========
const showProjectGroups = async (department) => {
  selectedDepartment.value = department
  showMembersSection.value = false
  projectGroupSearch.value = ''
  await loadProjectGroupsForDepartment(department.id)
}

const loadProjectGroupsForDepartment = async (departmentId, search = '') => {
  loadingProjectGroups.value = true
  try {
    const params = { page: 1, size: 1000, department_id: departmentId }
    if (search && search.trim()) {
      params.search = search.trim()
    }
    const res = await getTeams(params)
    projectGroups.value = res.data?.records || []
  } catch (error) {
    console.error('Load project groups error:', error)
    projectGroups.value = []
    ElMessage.error(t('organization.loadProjectGroupsFailed'))
  } finally {
    loadingProjectGroups.value = false
  }
}

const handleProjectGroupSearch = () => {
  if (selectedDepartment.value) {
    loadProjectGroupsForDepartment(selectedDepartment.value.id, projectGroupSearch.value)
  }
}

const loadProjects = async () => {
  try {
    const response = await getProjects({ page: 1, size: 1000 })
    allProjects.value = response.data?.records || []
  } catch (error) {
    console.error('Load projects error:', error)
  }
}

// 项目组负责人远程搜索
const handleLeaderSearch = async (query) => {
  if (!selectedDepartment.value?.id) return
  if (!query || !query.trim()) {
    await loadDepartmentMembersForProjectGroup()
    return
  }
  leaderSearchLoading.value = true
  try {
    const res = await organizationApi.getDepartmentMembers(selectedDepartment.value.id, query.trim())
    leaderOptions.value = res.data || []
  } catch (error) {
    console.error('Search leaders failed:', error)
  } finally {
    leaderSearchLoading.value = false
  }
}

// 项目组成员远程搜索（创建项目组时）
const handleMemberSearch = async (query) => {
  if (!selectedDepartment.value?.id) return
  if (!query || !query.trim()) {
    await loadDepartmentMembersForProjectGroup()
    return
  }
  memberSearchLoading.value = true
  try {
    const res = await organizationApi.getDepartmentMembers(selectedDepartment.value.id, query.trim())
    allUsers.value = res.data || []
  } catch (error) {
    console.error('Search members failed:', error)
  } finally {
    memberSearchLoading.value = false
  }
}

// 项目组成员远程搜索（添加成员对话框）
const handlePgMemberSearch = async (query) => {
  if (!selectedDepartment.value?.id) return
  if (!query || !query.trim()) {
    await loadAvailablePgUsers()
    return
  }
  pgMemberSearchLoading.value = true
  try {
    const res = await organizationApi.getDepartmentMembers(selectedDepartment.value.id, query.trim())
    const currentMemberIds = pgMembers.value.map(m => m.id)
    availablePgUsers.value = (res.data || []).filter(u => !currentMemberIds.includes(u.id))
  } catch (error) {
    console.error('Search project group members failed:', error)
  } finally {
    pgMemberSearchLoading.value = false
  }
}

// 加载项目组成员列表（用于搜索）
const loadDepartmentMembersForProjectGroup = async () => {
  if (!selectedDepartment.value?.id) return
  try {
    const res = await organizationApi.getDepartmentMembers(selectedDepartment.value.id)
    allUsers.value = res.data || []
    leaderOptions.value = res.data || []
  } catch (error) {
    console.error('Load department members error:', error)
    allUsers.value = []
    leaderOptions.value = []
  }
}

// 加载可用项目组成员（排除已添加的）
const loadAvailablePgUsers = async () => {
  if (!selectedDepartment.value?.id) return
  try {
    const res = await organizationApi.getDepartmentMembers(selectedDepartment.value.id)
    const deptMembers = res.data || []
    const currentMemberIds = pgMembers.value.map(m => m.id)
    availablePgUsers.value = deptMembers.filter(u => !currentMemberIds.includes(u.id))
  } catch (error) {
    console.error('Load department members error:', error)
    availablePgUsers.value = []
  }
}

const handleCreateProjectGroup = async () => {
  isEditProjectGroup.value = false
  projectGroupDialogTitle.value = t('organization.createTeam')
  projectGroupForm.id = null
  projectGroupForm.name = ''
  projectGroupForm.description = ''
  projectGroupForm.status = 1
  projectGroupForm.leader_ids = []
  projectGroupForm.projectIds = []
  projectGroupForm.userIds = []
  await loadProjects()
  // 加载当前组织下的成员（用于选择负责人和成员）
  await loadDepartmentMembersForProjectGroup()
  projectGroupDialogVisible.value = true
}

const handleEditProjectGroup = async (row) => {
  isEditProjectGroup.value = true
  projectGroupDialogTitle.value = t('organization.editTeam')
  projectGroupForm.id = row.id
  projectGroupForm.name = row.name
  projectGroupForm.description = row.description
  projectGroupForm.status = row.status
  projectGroupForm.leader_ids = Array.isArray(row.leader_ids) ? [...row.leader_ids] : []
  projectGroupForm.projectIds = []
  projectGroupForm.userIds = []
  // 加载当前组织下的成员作为组长候选
  await loadDepartmentMembersForProjectGroup()
  projectGroupDialogVisible.value = true
}

const handleSubmitProjectGroup = async () => {
  if (!projectGroupFormRef.value) return
  await projectGroupFormRef.value.validate(async (valid) => {
    if (valid) {
      submittingProjectGroup.value = true
      try {
        if (isEditProjectGroup.value) {
          await updateTeam(projectGroupForm.id, {
            name: projectGroupForm.name,
            description: projectGroupForm.description,
            status: projectGroupForm.status,
            leader_ids: projectGroupForm.leader_ids || []
          })
          ElMessage.success(t('organization.updateSuccess'))
        } else {
          const res = await createTeam({
            name: projectGroupForm.name,
            description: projectGroupForm.description,
            department_id: selectedDepartment.value.id,
            leader_ids: projectGroupForm.leader_ids || []
          })
          const teamId = res.data.id
          
          // 直接使用选中的项目ID
          if (projectGroupForm.projectIds && projectGroupForm.projectIds.length > 0) {
            await assignProjectsToTeam({ team_id: teamId, project_ids: projectGroupForm.projectIds })
          }
          
          if (projectGroupForm.userIds && projectGroupForm.userIds.length > 0) {
            for (const userId of projectGroupForm.userIds) {
              await assignTeams({ user_id: userId, team_ids: [teamId] })
            }
          }
          
          ElMessage.success(t('organization.createSuccess'))
        }
        projectGroupDialogVisible.value = false
        loadProjectGroupsForDepartment(selectedDepartment.value.id)
        loadDepartments()
        eventBus.emit('teams-changed')
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || t('organization.operationFailed'))
      } finally {
        submittingProjectGroup.value = false
      }
    }
  })
}

const handleDeleteProjectGroup = (row) => {
  ElMessageBox.confirm(t('organization.confirmDeleteTeam', { name: row.name }), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await deleteTeam(row.id)
      ElMessage.success(t('organization.deleteSuccess'))
      loadProjectGroupsForDepartment(selectedDepartment.value.id)
      loadDepartments()
      eventBus.emit('teams-changed')
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || t('common.failed'))
    }
  }).catch(() => {})
}

// 项目组成员管理
const handleViewMembers = async (row) => {
  currentTeamForMembers.value = row
  pgMembersDialogVisible.value = true
  loadingPgMembers.value = true
  try {
    const response = await getTeamMembers(row.id)
    pgMembers.value = response.data
  } catch (error) {
    ElMessage.error(t('organization.loadMembersFailed'))
  } finally {
    loadingPgMembers.value = false
  }
}

const handleAddPgMembers = async () => {
  // 加载当前组织下的成员（用于选择成员）- 会通过 @focus 触发
  await loadAvailablePgUsers()
  selectedPgUserIds.value = []
  addPgMembersDialogVisible.value = true
}

const handleAddPgMembersSubmit = async () => {
  if (!selectedPgUserIds.value || selectedPgUserIds.value.length === 0) {
    ElMessage.warning(t('organization.selectMemberRequired'))
    return
  }
  addingPgMembers.value = true
  try {
    for (const userId of selectedPgUserIds.value) {
      await assignTeams({ user_id: userId, team_ids: [currentTeamForMembers.value.id] })
    }
    ElMessage.success(t('organization.addMemberSuccess'))
    addPgMembersDialogVisible.value = false
    const response = await getTeamMembers(currentTeamForMembers.value.id)
    pgMembers.value = response.data
    loadProjectGroupsForDepartment(selectedDepartment.value.id)
    eventBus.emit('teams-changed')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('organization.operationFailed'))
  } finally {
    addingPgMembers.value = false
  }
}

const handleRemovePgMember = (row) => {
  ElMessageBox.confirm(t('organization.removeMemberConfirm'), t('common.tip'), {
    confirmButtonText: t('common.confirm'),
    cancelButtonText: t('common.cancel'),
    type: 'warning'
  }).then(async () => {
    try {
      await removeMember({ user_id: row.id, team_id: currentTeamForMembers.value.id })
      ElMessage.success(t('organization.removeMemberSuccess'))
      const response = await getTeamMembers(currentTeamForMembers.value.id)
      pgMembers.value = response.data
      loadProjectGroupsForDepartment(selectedDepartment.value.id)
      eventBus.emit('teams-changed')
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || t('organization.removeMemberFailed'))
    }
  }).catch(() => {})
}

// 授权用例库
const handleAssignProjects = async (row) => {
  currentTeamId.value = row.id
  await loadProjects()
  projectsDialogVisible.value = true
  try {
    const response = await getTeamProjects(row.id)
    selectedProjectIds.value = response.data.map(p => p.id)
  } catch (error) {
    ElMessage.error(t('organization.loadFailed'))
  }
}

const handleProjectsSubmit = async () => {
  submittingProjects.value = true
  try {
    await assignProjectsToTeam({ team_id: currentTeamId.value, project_ids: selectedProjectIds.value })
    ElMessage.success(t('organization.authSuccess'))
    projectsDialogVisible.value = false
    loadProjectGroupsForDepartment(selectedDepartment.value.id)
    eventBus.emit('teams-changed')
    eventBus.emit('projects-changed')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('organization.operationFailed'))
  } finally {
    submittingProjects.value = false
  }
}

// ========== 组织成员管理 ==========
const showDepartmentMembers = (department) => {
  selectedDepartment.value = department
  showMembersSection.value = true
  loadDepartmentMembers(department.id)
}

const loadDepartmentMembers = async (departmentId) => {
  loadingStore.showLoading()
  try {
    const res = await organizationApi.getDepartmentMembers(departmentId)
    departmentMembers.value = res.data || []
  } catch (error) {
    console.error('Load department members error:', error)
    departmentMembers.value = []
    ElMessage.error(t('organization.loadMembersFailed'))
  } finally {
    loadingStore.hideLoading()
  }
}

const showAddMemberDialog = async () => {
  addMemberForm.user_ids = []
  // 加载可添加的用户（排除已在组织中的）
  await loadAvailableUsers('')
  addMemberDialogVisible.value = true
}

const loadAvailableUsers = async (search) => {
  searchLoading.value = true
  try {
    const res = await organizationApi.getAvailableUsersForDepartment(selectedDepartment.value.id, search)
    availableUsers.value = res.data || []
  } catch (error) {
    console.error('Load available users error:', error)
    availableUsers.value = []
  } finally {
    searchLoading.value = false
  }
}

const remoteSearchUsers = async (query) => {
  await loadAvailableUsers(query)
}

const handleAddMembers = async () => {
  if (!addMemberForm.user_ids || addMemberForm.user_ids.length === 0) {
    ElMessage.warning(t('organization.selectMemberRequired'))
    return
  }
  submitting.value = true
  try {
    await organizationApi.addDepartmentMembers(selectedDepartment.value.id, addMemberForm.user_ids)
    ElMessage.success(t('organization.addMemberSuccess'))
    addMemberDialogVisible.value = false
    loadDepartmentMembers(selectedDepartment.value.id)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('organization.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const removeDepartmentMember = async (user) => {
  try {
    await ElMessageBox.confirm(t('organization.removeMemberConfirm'), t('common.tip'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await organizationApi.removeDepartmentMember(selectedDepartment.value.id, user.id)
    ElMessage.success(t('organization.removeMemberSuccess'))
    loadDepartmentMembers(selectedDepartment.value.id)
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || t('organization.removeMemberFailed'))
    }
  }
}

onMounted(async () => {
  bindDepartmentTableHeight()
  bindProjectGroupTableHeight()
  bindMembersTableHeight()
  // 并行加载部门和用户数据
  await Promise.all([loadDepartments(), loadUsers()])
})
</script>

<style scoped>
/* ==================== */
/* 页面布局 - 统一设计系统 */
/* ==================== */
.organization-page {
  height: 100%;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px;
}

.organization-page::-webkit-scrollbar { width: 8px; }
.organization-page::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.organization-page::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.organization-page::-webkit-scrollbar-track { background: #f1f5f9; }

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

.header-left { display: flex; gap: 12px; align-items: center; flex-shrink: 0; }
.header-right { display: flex; gap: 12px; align-items: center; flex-shrink: 0; margin-left: auto; }

.header-right :deep(.el-input__wrapper) {
  height: 40px !important; min-height: 40px !important;
  padding: 1px 11px !important; box-sizing: border-box !important;
  display: flex !important; align-items: center !important;
}
.header-right :deep(.el-input__inner) { height: 38px !important; line-height: 38px !important; }

.action-buttons { display: flex; gap: 8px; align-items: center; }
.action-buttons .el-button {
  border-radius: 8px !important; font-weight: 500 !important;
  height: 40px !important; padding: 0 18px !important;
  font-size: 14px !important; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}
.action-buttons .el-button--primary { background: #4f46e5 !important; border: none !important; }
.action-buttons .el-button--primary:hover { background: #4338ca !important; }

/* ==================== */
/* 内容区域 */
/* ==================== */
.organization-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 0 20px 20px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  margin: 20px 0 12px 0;
  color: #0f172a;
  display: flex;
  align-items: center;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 20px 0 12px 0;
}

.section-header-left { display: flex; align-items: center; gap: 15px; }
.section-header-right { display: flex; align-items: center; gap: 10px; }

.section-header-right :deep(.el-input__wrapper) {
  height: 40px !important; min-height: 40px !important;
  padding: 1px 11px !important; box-sizing: border-box !important;
  display: flex !important; align-items: center !important;
}
.section-header-right :deep(.el-input__inner) { height: 38px !important; line-height: 38px !important; }

.section-title-inline {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.department-section,
.project-group-section,
.department-members-section {
  margin-bottom: 24px;
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
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.table-wrapper .table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper :deep(.el-table) { width: 100%; position: relative; }

.table-wrapper :deep(.el-table td.el-table__cell),
.table-wrapper :deep(.el-table th.el-table__cell) {
  height: 48px !important; padding: 0 12px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell .cell),
.table-wrapper :deep(.el-table th.el-table__cell .cell) {
  line-height: 48px; padding: 0;
}

.table-wrapper :deep(.el-table__body-wrapper) { overflow-y: auto !important; overflow-x: auto !important; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar { height: 8px; width: 8px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track { background: #f1f5f9; }

.table-wrapper :deep(.el-table__header-wrapper) { overflow: hidden !important; position: relative; z-index: 10 !important; }
.table-wrapper :deep(.el-table__body-wrapper) { position: relative; z-index: 5 !important; }



/* 行悬停 */
.table-wrapper :deep(.el-table__row:hover > td) { background: #f8fafc !important; }

/* ==================== */
/* 按钮 */
/* ==================== */
:deep(.el-button) { border-radius: 8px; font-weight: 500; transition: all 0.15s; }
:deep(.el-button:hover) { transform: none; box-shadow: none; }
:deep(.el-button--primary) { background: #4f46e5; border: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
:deep(.el-button--primary:hover) { background: #4338ca; box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); }
:deep(.el-button--danger) { background: #ef4444; border: none; }
:deep(.el-button--danger:hover) { background: #dc2626; }
:deep(.el-button--info) { background: #64748b; border: none; }
:deep(.el-button--info:hover) { background: #475569; }
:deep(.el-button--warning) { background: #f59e0b; border: none; }
:deep(.el-button--warning:hover) { background: #d97706; }
:deep(.el-button--success) { background: #10b981; border: none; }
:deep(.el-button--success:hover) { background: #059669; }

/* ==================== */
/* 对话框 */
/* ==================== */
:deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
:deep(.el-dialog__header) { padding: 20px 24px 16px; border-bottom: 1px solid #e2e8f0; margin-right: 0; }
:deep(.el-dialog__title) { font-size: 18px; font-weight: 600; color: #0f172a; }
:deep(.el-dialog__body) { padding: 24px; }
:deep(.el-dialog__footer) { padding: 16px 24px; border-top: 1px solid #e2e8f0; }
:deep(.el-form-item__label) { font-weight: 500; color: #334155; font-size: 14px; }
:deep(.el-input__wrapper), :deep(.el-select) { border-radius: 8px; }

/* ==================== */
/* 用例库标签 */
/* ==================== */
.project-tags-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  position: relative;
  max-width: 100%;
}

.project-tag { margin: 0 !important; max-width: 180px; overflow: visible; white-space: nowrap; }
.project-tag-more { margin: 0 !important; cursor: pointer; }
.tooltip-trigger { position: absolute; top: 0; left: 0; right: 0; bottom: 0; cursor: pointer; }
</style>
