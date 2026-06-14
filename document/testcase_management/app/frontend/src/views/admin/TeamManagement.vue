<template>
  <div class="team-management">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">项目组管理</span>
          <el-button type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新建项目组
          </el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchText"
          placeholder="搜索项目组名称或描述"
          clearable
          style="width: 300px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          搜索
        </el-button>
      </div>

      <!-- 表格 -->
      <div class="table-wrapper">
        <el-table
          ref="tableRef"
          :data="tableData"
          style="width: 100%"
          border
          v-loading="loading"
          height="600px"
        >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="name" label="项目组名称" min-width="150" />
        <el-table-column prop="description" label="描述" min-width="200" :show-overflow-tooltip="{ showAfter: 500 }" />
        <el-table-column prop="member_count" label="成员数量" width="100" align="center">
          <template #default="{ row }">
            <el-tag type="info">{{ row.member_count }} 人</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="120" align="center">
          <template #default="{ row }">
            <span v-if="row.leader_name">{{ row.leader_name }}</span>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column label="授权用例库" width="220" align="center">
          <template #default="{ row }">
            <div v-if="row.projectNames && row.projectNames.length > 0" class="project-tags-wrapper">
              <el-tag 
                type="warning"
                size="small"
                effect="plain"
                class="project-tag"
              >
                {{ row.projectNames[0] }}
              </el-tag>
              <el-tag 
                v-if="row.projectNames.length > 1"
                type="warning"
                size="small"
                effect="plain"
                class="project-tag-more"
              >
                +{{ row.projectNames.length - 1 }}
              </el-tag>
              <el-tooltip 
                v-if="row.projectNames.length > 1"
                effect="dark" 
                placement="top"
               :show-after="500">
                <template #content>
                  <div v-for="(name, idx) in row.projectNames" :key="idx">
                    {{ name }}
                  </div>
                </template>
                <span class="tooltip-trigger"></span>
              </el-tooltip>
            </div>
            <span v-else style="color: #909399;">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100" align="center">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button link type="success" @click="handleAssignProjects(row)">
              <el-icon><Folder /></el-icon>
              授权
            </el-button>
            <el-button link type="primary" @click="handleViewMembers(row)">
              <el-icon><User /></el-icon>
              成员
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      :width="isEdit ? '500px' : '700px'"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="项目组名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目组名称" />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目组描述"
          />
        </el-form-item>
        <el-form-item label="负责人">
          <el-select
            v-model="form.leaderId"
            placeholder="请选择项目组负责人"
            style="width: 100%"
            filterable
            clearable
          >
            <el-option
              v-for="user in allUsers"
              :key="user.id"
              :label="user.username"
          <el-tree
            ref="projectTreeRef"
            :data="allProjects"
            :props="{
              label: 'name',
              children: 'children'
            }"
            show-checkbox
            node-key="id"
            :default-checked-keys="form.projectIds"
            :render-after-expand="false"
            style="width: 100%; border: 1px solid #dcdfe6; border-radius: 4px; padding: 10px; max-height: 300px; overflow-y: auto;"
            class="project-tree"
          >
            <template #default="{ data }">
              <span style="display: flex; align-items: center; gap: 6px; width: 100%;">
                <el-icon v-if="data.project_type === 'GROUP'" color="#409EFF"><Folder /></el-icon>
                <el-icon v-else-if="data.project_type === 'CATEGORY'" color="#67C23A"><Folder /></el-icon>
                <el-icon v-else color="#E6A23C"><Folder /></el-icon>
                <span style="flex: 1;">{{ data.name }}</span>
                <el-tag v-if="data.project_type" size="small" :type="getProjectTypeTag(data.project_type)" effect="plain" style="text-align: center; min-width: 60px;">
                  {{ getProjectTypeLabel(data.project_type) }}
                </el-tag>
              </span>
            </template>
          </el-tree>
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            提示：勾选项目或分类会自动勾选其下所有产品线，只有产品线会被授权
          </div>
        </el-form-item>
        <el-form-item v-if="!isEdit" label="选择成员">
          <el-select
            v-model="form.userIds"
            multiple
            placeholder="请选择项目组成员"
            style="width: 100%"
            filterable
          >
            <el-option
              v-for="user in allUsers"
              :key="user.id"
              :label="user.username"
              :value="user.id"
            />
          </el-select>
          <div style="margin-top: 8px; font-size: 12px; color: #909399;">
            提示：可以搜索用户名
          </div>
        </el-form-item>
        <el-form-item v-if="isEdit" label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">启用</el-radio>
            <el-radio :label="0">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 成员列表对话框 -->
    <el-dialog
      v-model="membersDialogVisible"
      title="项目组成员"
      width="700px"
    >
      <div style="margin-bottom: 16px;">
        <el-button type="primary" @click="handleAddMembers">
          <el-icon><Plus /></el-icon>
          添加成员
        </el-button>
      </div>
      <el-table :data="members" v-loading="loadingMembers">
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" min-width="200" />
        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleRemoveMember(row)">
              <el-icon><Delete /></el-icon>
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="membersDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="addMembersDialogVisible"
      title="添加成员"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-select
        v-model="selectedUserIds"
        multiple
        placeholder="请选择要添加的成员"
        style="width: 100%"
        filterable
      >
        <el-option
          v-for="user in availableUsers"
          :key="user.id"
          :label="user.username"
          :value="user.id"
        />
      </el-select>
      <div style="margin-top: 8px; font-size: 12px; color: #909399;">
        提示：可以搜索用户名
      </div>
      <template #footer>
        <el-button @click="addMembersDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleAddMembersSubmit" :loading="addingMembers">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 授权用例库对话框 -->
    <el-dialog
      v-model="projectsDialogVisible"
      title="授权用例库"
      width="600px"
      :close-on-click-modal="false"
    >
      <div style="margin-bottom: 16px; color: #606266;">
        为项目组授权用例库后，该项目组的所有成员将自动获得这些用例库的访问权限
      </div>
      <el-tree
        ref="projectTreeRefDialog"
        :data="allProjects"
        :props="{
          label: 'name',
          children: 'children'
        }"
        show-checkbox
        node-key="id"
        :default-checked-keys="selectedProjectIds"
        style="border: 1px solid #dcdfe6; border-radius: 4px; padding: 10px; max-height: 400px; overflow-y: auto;"
      >
        <template #default="{ data }">
          <span style="display: flex; align-items: center; gap: 6px;">
            <el-icon v-if="data.project_type === 'GROUP'" color="#409EFF"><Folder /></el-icon>
            <el-icon v-else-if="data.project_type === 'CATEGORY'" color="#67C23A"><Folder /></el-icon>
            <el-icon v-else color="#E6A23C"><Folder /></el-icon>
            <span>{{ data.name }}</span>
            <el-tag v-if="data.project_type" size="small" :type="getProjectTypeTag(data.project_type)" effect="plain">
              {{ getProjectTypeLabel(data.project_type) }}
            </el-tag>
          </span>
        </template>
      </el-tree>
      <div style="margin-top: 8px; font-size: 12px; color: #909399;">
        提示：勾选项目或分类会自动勾选其下所有产品线，只有产品线会被授权
      </div>
      <template #footer>
        <el-button @click="projectsDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleProjectsSubmit" :loading="submittingProjects">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, User, Folder } from '@element-plus/icons-vue'
import { getTeams, createTeam, updateTeam, deleteTeam, getTeamMembers, assignProjectsToTeam, getTeamProjects } from '@/api/team'
import { getProjectTree } from '@/api/project'
import { getUsers } from '@/api/user'
import { assignTeams, removeMember } from '@/api/userTeam'
import { usePagination } from '@/composables/usePagination'
import { useScrollToTop } from '@/composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'

const loading = ref(false)
const tableData = ref([])
const tableRef = ref(null)
const { page: currentPage, size: pageSize, total } = usePagination('teamManagement', 10)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()

const searchText = ref('')
const dialogVisible = ref(false)
const dialogTitle = ref('新建项目组')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)
const projectTreeRef = ref(null)

// 所有项目和用户
const allProjects = ref([])
const allUsers = ref([])

const form = reactive({
  id: null,
  name: '',
  description: '',
  status: 1,
  leaderId: null,
  projectIds: [],
  userIds: []
})

const rules = {
  name: [
    { required: true, message: '请输入项目组名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}

const membersDialogVisible = ref(false)
const members = ref([])
const loadingMembers = ref(false)
const currentTeamForMembers = ref(null)

const addMembersDialogVisible = ref(false)
const selectedUserIds = ref([])
const availableUsers = ref([])
const addingMembers = ref(false)

const projectsDialogVisible = ref(false)
const selectedProjectIds = ref([])
const currentTeamId = ref(null)
const submittingProjects = ref(false)
const projectTreeRefDialog = ref(null)

// 加载数据
const loadData = async () => {
  loadingStore.showLoading()
  loading.value = true
  try {
    const response = await getTeams({
      page: currentPage.value,
      size: pageSize.value,
      search: searchText.value
    })
    tableData.value = response.data.records
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载数据失败')
  } finally {
    loadingStore.hideLoading()
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadData()
}

// 分页
const handleSizeChange = async () => {
  currentPage.value = 1
  await loadData()
  await nextTick()
  scrollToTop()
}

const handleCurrentChange = async () => {
  await loadData()
  await nextTick()
  scrollToTop()
}

// 新建
const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = '新建项目组'
  form.id = null
  form.name = ''
  form.description = ''
  form.status = 1
  form.leaderId = null
  form.projectIds = []
  form.userIds = []
  dialogVisible.value = true
  
  // 清空树形组件选中状态
  setTimeout(() => {
    if (projectTreeRef.value) {
      projectTreeRef.value.setCheckedKeys([])
    }
  }, 100)
}

// 编辑
const handleEdit = async (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑项目组'
  form.id = row.id
  form.name = row.name
  form.description = row.description
  form.status = row.status
  form.leaderId = row.leader_id || null
  form.projectIds = []
  form.userIds = []
  dialogVisible.value = true
  
  // 加载项目组的用例库
  try {
    const projectsRes = await getTeamProjects(row.id)
    if (projectsRes.data) {
      form.projectIds = projectsRes.data.map(p => p.id)
    }
  } catch (error) {
    console.error('加载项目组用例库失败:', error)
  }
  
  // 加载项目组成员
  try {
    const membersRes = await getTeamMembers(row.id)
    if (membersRes.data) {
      form.userIds = membersRes.data.map(m => m.id)
    }
  } catch (error) {
    console.error('加载项目组成员失败:', error)
  }
  
  // 设置树形组件选中状态
  setTimeout(() => {
    if (projectTreeRef.value && form.projectIds.length > 0) {
      projectTreeRef.value.setCheckedKeys(form.projectIds)
    }
  }, 150)
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (valid) {
      submitting.value = true
      try {
        if (isEdit.value) {
          // 编辑模式：只更新基本信息
          await updateTeam(form.id, {
            name: form.name,
            description: form.description,
            status: form.status,
            leader_id: form.leaderId || 0  // 0 表示清除负责人
          })
          ElMessage.success('更新成功')
        } else {
          // 创建模式：创建项目组并授权用例库、分配成员
          const res = await createTeam({
            name: form.name,
            description: form.description,
            leader_id: form.leaderId
          })
          const teamId = res.data.id
          
          // 获取选中的项目ID（只保留叶子节点）
          const checkedKeys = projectTreeRef.value ? projectTreeRef.value.getCheckedKeys() : []
          const halfCheckedKeys = projectTreeRef.value ? projectTreeRef.value.getHalfCheckedKeys() : []
          const allCheckedIds = [...checkedKeys, ...halfCheckedKeys]
          
          // 过滤出叶子节点（产品线）
          const leafNodeIds = []
          const checkIfLeaf = (nodeId) => {
            const findNode = (nodes, id) => {
              for (const node of nodes) {
                if (node.id === id) return node
                if (node.children && node.children.length > 0) {
                  const found = findNode(node.children, id)
                  if (found) return found
                }
              }
              return null
            }
            const node = findNode(allProjects.value, nodeId)
            return node && (!node.children || node.children.length === 0)
          }
          
          for (const id of allCheckedIds) {
            if (checkIfLeaf(id)) {
              leafNodeIds.push(id)
            }
          }
          
          // 授权用例库
          if (leafNodeIds.length > 0) {
            await assignProjectsToTeam({
              team_id: teamId,
              project_ids: leafNodeIds
            })
          }
          
          // 分配成员
          if (form.userIds && form.userIds.length > 0) {
            for (const userId of form.userIds) {
              await assignTeams({
                user_id: userId,
                team_ids: [teamId]
              })
            }
          }
          
          ElMessage.success('创建成功')
        }
        
        dialogVisible.value = false
        loadData()
        eventBus.emit('teams-changed')
      } catch (error) {
        const errorMsg = error.response?.data?.detail || '操作失败'
        ElMessage.error(errorMsg)
      } finally {
        submitting.value = false
      }
    }
  })
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm(
    `确认删除项目组"${row.name}"吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteTeam(row.id)
      ElMessage.success('删除成功')
      loadData()
      eventBus.emit('teams-changed')
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '删除失败'
      ElMessage.error(errorMsg)
    }
  }).catch(() => {})
}

// 查看成员
const handleViewMembers = async (row) => {
  currentTeamForMembers.value = row
  membersDialogVisible.value = true
  loadingMembers.value = true
  try {
    const response = await getTeamMembers(row.id)
    members.value = response.data
  } catch (error) {
    ElMessage.error('加载成员列表失败')
  } finally {
    loadingMembers.value = false
  }
}

// 添加成员
const handleAddMembers = () => {
  // 过滤出不在当前项目组的用户
  const currentMemberIds = members.value.map(m => m.id)
  availableUsers.value = allUsers.value.filter(u => !currentMemberIds.includes(u.id))
  selectedUserIds.value = []
  addMembersDialogVisible.value = true
}

// 提交添加成员
const handleAddMembersSubmit = async () => {
  if (!selectedUserIds.value || selectedUserIds.value.length === 0) {
    ElMessage.warning('请选择要添加的成员')
    return
  }
  
  addingMembers.value = true
  try {
    // 为每个用户添加到项目组
    for (const userId of selectedUserIds.value) {
      await assignTeams({
        user_id: userId,
        team_ids: [currentTeamForMembers.value.id]
      })
    }
    
    ElMessage.success('添加成员成功')
    addMembersDialogVisible.value = false
    
    // 刷新成员列表
    const response = await getTeamMembers(currentTeamForMembers.value.id)
    members.value = response.data
    
    // 刷新主表格数据（更新成员数量）
    loadData()
    eventBus.emit('teams-changed')
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '添加成员失败'
    ElMessage.error(errorMsg)
  } finally {
    addingMembers.value = false
  }
}

// 移除成员
const handleRemoveMember = (row) => {
  ElMessageBox.confirm(
    `确认将"${row.username}"从项目组中移除吗？`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 调用API移除成员
      await removeMember({
        user_id: row.id,
        team_id: currentTeamForMembers.value.id
      })
      
      ElMessage.success('移除成员成功')
      
      // 刷新成员列表
      const response = await getTeamMembers(currentTeamForMembers.value.id)
      members.value = response.data
      
      // 刷新主表格数据（更新成员数量）
      loadData()
      eventBus.emit('teams-changed')
    } catch (error) {
      const errorMsg = error.response?.data?.detail || '移除成员失败'
      ElMessage.error(errorMsg)
    }
  }).catch(() => {})
}

// 格式化日期
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 加载项目树
const loadProjects = async () => {
  try {
    const response = await getProjectTree()
    allProjects.value = response.data || []
  } catch (error) {
    console.error('加载项目树失败:', error)
  }
}

// 加载用户列表
const loadUsers = async () => {
  try {
    const response = await getUsers({ page: 1, size: 1000 })
    allUsers.value = response.data.records || []
  } catch (error) {
    console.error('加载用户列表失败:', error)
  }
}

// 项目类型标签
const getProjectTypeTag = (type) => {
  const tags = {
    'GROUP': 'primary',
    'CATEGORY': 'success',
    'PRODUCT': 'warning'
  }
  return tags[type] || 'info'
}

const getProjectTypeLabel = (type) => {
  const labels = {
    'GROUP': '项目',
    'CATEGORY': '业务线',
    'PRODUCT': '产品线'
  }
  return labels[type] || type
}

// 授权用例库
const handleAssignProjects = async (row) => {
  currentTeamId.value = row.id
  projectsDialogVisible.value = true
  
  // 加载该项目组已授权的用例库
  try {
    const response = await getTeamProjects(row.id)
    selectedProjectIds.value = response.data.map(p => p.id)
    
    // 设置树形组件的选中状态
    setTimeout(() => {
      if (projectTreeRefDialog.value) {
        projectTreeRefDialog.value.setCheckedKeys(selectedProjectIds.value)
      }
    }, 100)
  } catch (error) {
    ElMessage.error('加载用例库列表失败')
  }
}

// 提交授权
const handleProjectsSubmit = async () => {
  if (!projectTreeRefDialog.value) return
  
  // 获取所有选中的节点（包括半选中的父节点）
  const checkedNodes = projectTreeRefDialog.value.getCheckedNodes()
  const halfCheckedNodes = projectTreeRefDialog.value.getHalfCheckedNodes()
  const allNodes = [...checkedNodes, ...halfCheckedNodes]
  
  // 只保留产品线（叶子节点）
  const leafNodeIds = allNodes
    .filter(node => node.project_type === 'PRODUCT' || (!node.children || node.children.length === 0))
    .map(node => node.id)
  
  submittingProjects.value = true
  try {
    await assignProjectsToTeam({
      team_id: currentTeamId.value,
      project_ids: leafNodeIds
    })
    
    ElMessage.success('授权成功')
    projectsDialogVisible.value = false
    
    // 刷新主表格数据（更新授权用例库列）
    loadData()
    eventBus.emit('teams-changed')
    eventBus.emit('projects-changed')
  } catch (error) {
    const errorMsg = error.response?.data?.detail || '授权失败'
    ElMessage.error(errorMsg)
  } finally {
    submittingProjects.value = false
  }
}

onMounted(() => {
  loadData()
  loadProjects()
  loadUsers()
})
</script>

<style scoped>
.team-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.table-wrapper {
  margin: 20px 0;
}

.table-wrapper .el-table {
  width: 100%;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

/* 用例库标签容器 */
.project-tags-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  position: relative;
  max-width: 100%;
}

.project-tag {
  margin: 0 !important;
  max-width: 180px;
  overflow: visible;
  white-space: nowrap;
}

.project-tag-more {
  margin: 0 !important;
  cursor: pointer;
}

.tooltip-trigger {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  cursor: pointer;
}

/* 项目树样式 */
.project-tree :deep(.el-tree-node) {
  margin: 4px 0;
}

.project-tree :deep(.el-tree-node__content) {
  height: 32px;
  line-height: 32px;
}

/* 固定列不透明背景 */
:deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
}
:deep(.el-table td.el-table__cell) {
  background: #fff;
}
:deep(.el-table__row:hover > td.el-table__cell) {
  background: #f8fafc !important;
}
</style>
