<template>
  <div class="user-page">
    <!-- 表格卡片 -->
    <el-card class="table-card" shadow="never">
      <div class="table-header">
        <div class="header-left">
          <div class="action-buttons">
            <el-button 
              v-if="hasButton('users', 'create')"
              type="primary" 
              :icon="Plus" 
              @click="handleCreate"
            >
              {{ $t('user.createUser') }}
            </el-button>
            <el-button 
              v-if="hasButton('users', 'create')"
              :icon="Upload"
              @click="importDialogVisible = true"
            >
              批量导入
            </el-button>
            <el-badge :value="pendingUsers.length" :hidden="pendingUsers.length === 0" :max="99">
              <el-button @click="pendingDialogVisible = true">
                待审核注册
              </el-button>
            </el-badge>
          </div>
        </div>
        <div class="header-right">
          <el-select
            v-model="filterRoleId"
            placeholder="筛选角色"
            size="large"
            style="width: 180px;"
            clearable
            @change="handleSearch"
          >
            <el-option v-for="role in allRoles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('user.searchPlaceholder')"
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
            @row-click="handleRowClick"
            row-key="id"
          >
            <el-table-column prop="username" :label="$t('user.username')" min-width="140" align="center">
              <template #default="scope">
                <el-tooltip :content="scope.row.username" placement="top" :teleported="true" :show-after="500">
                  <span class="cell-text">{{ scope.row.username }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="email" :label="$t('user.email')" min-width="200" align="center">
              <template #default="scope">
                <el-tooltip :content="scope.row.email" placement="top" :teleported="true" :show-after="500">
                  <span class="cell-text">{{ scope.row.email }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column :label="$t('user.department')" min-width="150" align="center">
              <template #default="scope">
                <div v-if="scope.row.departmentNames && scope.row.departmentNames.length > 0" class="tag-cell">
                  <el-tag type="primary" size="small" class="cell-tag">{{ scope.row.departmentNames[0] }}</el-tag>
                  <el-tooltip v-if="scope.row.departmentNames.length > 1" effect="dark" placement="top" :show-after="500">
                    <template #content>
                      <div v-for="(name, idx) in scope.row.departmentNames" :key="idx">{{ name }}</div>
                    </template>
                    <el-tag type="primary" size="small" class="cell-tag-more">+{{ scope.row.departmentNames.length - 1 }}</el-tag>
                  </el-tooltip>
                </div>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('user.team')" min-width="150" align="center">
              <template #default="scope">
                <div v-if="scope.row.teamNames && scope.row.teamNames.length > 0" class="tag-cell">
                  <el-tag type="info" size="small" class="cell-tag">{{ scope.row.teamNames[0] }}</el-tag>
                  <el-tooltip v-if="scope.row.teamNames.length > 1" effect="dark" placement="top" :show-after="500">
                    <template #content>
                      <div v-for="(name, idx) in scope.row.teamNames" :key="idx">{{ name }}</div>
                    </template>
                    <el-tag type="info" size="small" class="cell-tag-more">+{{ scope.row.teamNames.length - 1 }}</el-tag>
                  </el-tooltip>
                </div>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('user.role')" min-width="140" align="center">
              <template #default="scope">
                <el-tag :type="getRoleTagType(scope.row.roleId)" effect="light" size="small">
                  {{ getRoleName(scope.row.roleId) || $t('user.unassigned') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('user.dataPermission')" min-width="120" align="center">
              <template #default="scope">
                <el-tag type="info" effect="light" size="small">
                  {{ getPositionTagName(scope.row.position_tag_id) || '-' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="status" :label="$t('common.status')" min-width="100" align="center">
              <template #default="scope">
                <el-tag 
                  :type="scope.row.status === 1 ? 'success' : 'info'" 
                  effect="light"
                  size="small"
                  :style="{ cursor: isSuperAdmin(scope.row.username) ? 'not-allowed' : 'pointer' }"
                  @click.stop="!isSuperAdmin(scope.row.username) && handleStatusChange(scope.row)"
                >
                  {{ scope.row.status === 1 ? $t('common.enabled') : $t('common.disabled') }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.operation')" width="240" align="center" fixed="right">
              <template #default="scope">
                <el-button 
                  v-if="hasButton('users', 'edit')"
                  type="primary" 
                  size="default" 
                  :icon="Edit"
                  @click.stop="handleEdit(scope.row)"
                >
                  {{ $t('common.edit') }}
                </el-button>
                <template v-if="!isSuperAdmin(scope.row.username)">
                  <el-button 
                    v-if="hasButton('users', 'delete')"
                    type="danger" 
                    size="default" 
                    :icon="Delete"
                    @click.stop="handleDelete(scope.row)"
                  >
                    {{ $t('common.delete') }}
                  </el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>

      <div class="pagination-container">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="size"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="async () => { await loadData(); await nextTick(); scrollToTop(); }"
          @size-change="async () => { await loadData(); await nextTick(); scrollToTop(); }"
        />
      </div>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="600px"
      :close-on-click-modal="false"
      :show-close="true"
      @open="handleDialogOpen"
      @closed="handleDialogClosed"
    >
      <el-form :model="form" ref="formRef" label-width="100px" label-position="top" autocomplete="off">
        <el-form-item :label="$t('user.username')" required>
          <el-input v-model="form.username" :disabled="!!form.id" :placeholder="$t('user.inputUsername')" autocomplete="off" />
        </el-form-item>
        <el-form-item :label="$t('user.email')" required>
          <el-input v-model="form.email" :placeholder="$t('user.inputEmail')" autocomplete="off" />
          <div v-if="!form.id" class="form-tip">初始密码为邮箱地址，用户首次登录需修改密码</div>
        </el-form-item>
        <el-form-item :label="$t('user.fullName')">
          <el-input v-model="form.full_name" :placeholder="$t('user.inputFullName')" autocomplete="off" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="用于钉钉通知@提醒" autocomplete="off" />
        </el-form-item>
        <el-form-item v-if="form.id" :label="$t('user.resetPassword')">
          <div>
            <el-button @click="handleResetPassword" :loading="resettingPassword">{{ $t('user.resetPassword') }}</el-button>
            <el-button type="warning" @click="handleUnlockUser" :loading="unlocking">解锁账户</el-button>
            <div class="form-tip">重置后将生成随机强密码，请妥善保管</div>
          </div>
        </el-form-item>
        <el-form-item :label="$t('user.role')" required>
          <el-select v-model="form.roleId" :placeholder="$t('user.selectRole')" style="width: 100%">
            <el-option v-for="role in allRoles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.dataPermission')" required>
          <el-select v-model="form.position_tag_id" :placeholder="$t('user.selectDataPermission')" style="width: 100%">
            <el-option v-for="tag in allPositionTags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.department')">
          <el-select v-model="form.departmentIds" multiple :placeholder="$t('organization.selectDepartment')" style="width: 100%" filterable @change="handleDepartmentChange">
            <el-option v-for="dept in allDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.team')">
          <el-select v-model="form.teamIds" multiple :placeholder="$t('organization.selectTeam')" style="width: 100%" filterable>
            <el-option v-for="team in filteredTeams" :key="team.id" :label="team.name" :value="team.id" />
          </el-select>
          <div v-if="form.departmentIds.length > 0 && filteredTeams.length === 0" class="form-tip">所选组织下暂无项目组</div>
          <div v-if="form.departmentIds.length === 0" class="form-tip">选择组织后可筛选对应项目组，也可直接选择所有项目组</div>
        </el-form-item>
        <el-form-item :label="$t('user.userStatus')">
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
        <el-button type="primary" @click="handleSubmit" :loading="submitting">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 待审核注册用户对话框 -->
    <el-dialog v-model="pendingDialogVisible" :title="$t('user.pendingRegistration')" width="1100px" top="8vh">
      <div style="max-height: 60vh; overflow: hidden; display: flex; flex-direction: column;">
        <el-table :data="paginatedPendingUsers" border style="width: 100%; flex: 1;" :empty-text="$t('common.empty')">
          <el-table-column prop="username" :label="$t('user.username')" width="130" />
          <el-table-column prop="email" :label="$t('user.email')" min-width="180" :show-overflow-tooltip="{ showAfter: 500 }" />
          <el-table-column prop="full_name" :label="$t('user.fullName')" width="120">
            <template #default="{ row }">{{ row.full_name || '-' }}</template>
          </el-table-column>
          <el-table-column prop="phone" :label="$t('user.phone')" width="130">
            <template #default="{ row }">{{ row.phone || '-' }}</template>
          </el-table-column>
          <el-table-column prop="created_at" :label="$t('user.applyTime')" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column :label="$t('common.operation')" width="140" align="center">
            <template #default="{ row }">
              <el-button type="primary" size="small" link @click="openApproveDialog(row)">{{ $t('user.approve') }}</el-button>
              <el-button type="danger" size="small" link @click="handleReject(row)">{{ $t('user.reject') }}</el-button>
            </template>
          </el-table-column>
        </el-table>
        <div style="display: flex; justify-content: flex-end; padding-top: 12px;" v-if="pendingUsers.length > pendingPageSize">
          <el-pagination
            v-model:current-page="pendingPage"
            :page-size="pendingPageSize"
            :total="pendingUsers.length"
            layout="total, prev, pager, next"
            small
          />
        </div>
      </div>
    </el-dialog>

    <!-- 审核授权对话框 -->
    <el-dialog v-model="approveDialogVisible" :title="$t('user.approveWithConfig')" width="600px" :close-on-click-modal="false" append-to-body>
      <div style="margin-bottom: 16px; color: #64748b; font-size: 13px;">
        {{ $t('user.user') }}:<span style="color: #0f172a; font-weight: 600;">{{ approveTarget?.username }}</span>（{{ approveTarget?.email }}）
        <br/><!-- 下所搜权为可选不填则审核通过后由管理员后续分配 -->
      </div>
      <el-form label-width="100px" label-position="top">
        <el-form-item :label="$t('user.role')">
          <el-select v-model="approveForm.role_id" :placeholder="$t('user.selectRoleOptional')" style="width: 100%" clearable>
            <el-option v-for="role in allRoles" :key="role.id" :label="role.name" :value="role.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.dataPermission')">
          <el-select v-model="approveForm.position_tag_id" :placeholder="$t('user.selectDataPermissionOptional')" style="width: 100%" clearable>
            <el-option v-for="tag in allPositionTags" :key="tag.id" :label="tag.name" :value="tag.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.department')">
          <el-select v-model="approveForm.department_ids" multiple :placeholder="$t('user.selectDepartmentOptional')" style="width: 100%" filterable clearable @change="handleApproveDeptChange">
            <el-option v-for="dept in allDepartments" :key="dept.id" :label="dept.name" :value="dept.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('user.team')">
          <el-select v-model="approveForm.team_ids" multiple :placeholder="$t('user.selectTeamOptional')" style="width: 100%" filterable clearable>
            <el-option v-for="team in approveFilteredTeams" :key="team.id" :label="team.name" :value="team.id" />
          </el-select>
          <div v-if="approveForm.department_ids.length > 0 && approveFilteredTeams.length === 0" class="form-tip">{{ $t('user.noTeamInDept') }}</div>
          <div v-if="approveForm.department_ids.length === 0" class="form-tip">{{ $t('user.selectDeptFirst') }}</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="approveDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleApprove" :loading="approving">{{ $t('user.confirmApprove') }}</el-button>
      </template>
    </el-dialog>

    <!-- 批量导入对话框 -->
    <el-dialog v-model="importDialogVisible" :title="$t('user.batchImport')" width="500px" :close-on-click-modal="false" append-to-body class="import-user-dialog">
      <div class="import-tip-info">
        <div class="import-tip-header">
          <el-icon><InfoFilled /></el-icon>
          <span>{{ $t('user.importTip') }}</span>
        </div>
        <ul class="import-tip-content">
          <li>{{ $t('user.usernameEmailRequired') }}</li>
          <li>{{ $t('user.othersOptional') }}</li>
          <li>{{ $t('user.autoMatch') }}</li>
          <li>{{ $t('user.skipExist') }}</li>
        </ul>
      </div>
      
      <el-divider content-position="left">
        <span style="font-size: 13px; color: #64748b;">{{ $t('user.importFile') }}</span>
      </el-divider>
      
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :limit="1"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="fileList"
        accept=".xlsx,.xls"
        class="import-upload"
      >
        <el-button type="primary">
          <el-icon><Upload /></el-icon>
          选择Excel文件
        </el-button>
        <template #tip>
          <div class="el-upload__tip">支持 .xlsx, .xls 格式，仅能上传一个文件</div>
        </template>
      </el-upload>
      
      <el-progress 
        v-if="importing && importProgress.total > 0"
        :percentage="Math.round((importProgress.processed / importProgress.total) * 100)"
        :status="importProgress.status === 'error' ? 'exception' : undefined"
        :stroke-width="8"
        class="import-progress"
      >
        <span style="font-size: 12px;">{{ importProgress.message || `已处理 ${importProgress.processed}/${importProgress.total} 条` }}</span>
      </el-progress>
      
      <div class="import-template-link">
        <el-button type="primary" link @click="handleDownloadTemplate">
          <el-icon><Download /></el-icon>
          下载导入模板
        </el-button>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="importDialogVisible = false" :disabled="importing">取消</el-button>
          <el-button type="primary" @click="handleImport" :loading="importing" :disabled="!selectedFile">开始导入</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { getUsers, createUser, updateUser, deleteUser, toggleUserStatus, resetUserPassword, unlockUser, getPendingUsers, approveUser, rejectUser, downloadUserTemplate, importUsers } from '../../api/user'
import { getRoles, getUserRoles, assignRoles } from '../../api/role'
import { getTeams } from '../../api/team'
import { assignTeams } from '../../api/userTeam'
import { positionTagApi } from '../../api/positionTag'
import { organizationApi } from '../../api/organization'
import { ElMessage, ElMessageBox } from 'element-plus'
import { User, Plus, Edit, Delete, Search, Upload, Download, InfoFilled } from '@element-plus/icons-vue'
import { useUserRole } from '../../composables/useUserRole'
import { usePagination } from '../../composables/usePagination'
import { useTableHeight } from '../../composables/useTableHeight'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'

const { t } = useI18n()
const { hasButton } = useUserRole()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()

const tableData = ref([])
const allRoles = ref([])
const allTeams = ref([])
const allPositionTags = ref([])
const allDepartments = ref([])
const { page, size, total } = usePagination('userManagement', 10)
const searchKeyword = ref('')
const filterRoleId = ref(null)
const dialogVisible = ref(false)
const dialogTitle = computed(() => form.id ? t('user.editUser') : t('user.createUser'))
const submitting = ref(false)
const resettingPassword = ref(false)
const unlocking = ref(false)
const formRef = ref(null)
const form = reactive({
  id: null, username: '', email: '', full_name: '', phone: '', password: '',
  roleId: null, teamIds: [], departmentIds: [],
  position_tag_id: null, status: 1
})

const pendingUsers = ref([])
const pendingDialogVisible = ref(false)
const pendingPage = ref(1)
const pendingPageSize = 10

const paginatedPendingUsers = computed(() => {
  const start = (pendingPage.value - 1) * pendingPageSize
  return pendingUsers.value.slice(start, start + pendingPageSize)
})

const approveDialogVisible = ref(false)
const approveTarget = ref(null)
const approving = ref(false)
const approveForm = reactive({
  role_id: null,
  position_tag_id: null,
  department_ids: [],
  team_ids: []
})

const approveFilteredTeams = computed(() => {
  if (!approveForm.department_ids || approveForm.department_ids.length === 0) {
    return allTeams.value.filter(t => t.status === 1)
  }
  return allTeams.value.filter(t => t.status === 1 && approveForm.department_ids.includes(t.department_id))
})

const handleApproveDeptChange = () => {
  if (approveForm.department_ids.length > 0) {
    const validIds = approveFilteredTeams.value.map(t => t.id)
    approveForm.team_ids = approveForm.team_ids.filter(id => validIds.includes(id))
  }
}

const openApproveDialog = (row) => {
  approveTarget.value = row
  approveForm.role_id = null
  approveForm.position_tag_id = null
  approveForm.department_ids = []
  approveForm.team_ids = []
  approveDialogVisible.value = true
}

const SUPER_ADMINS = ['admin', 'super']
const isSuperAdmin = (username) => SUPER_ADMINS.includes(username)

const loadRoles = async () => {
  try { const res = await getRoles({ page: 1, size: 1000 }); allRoles.value = res.data.records } catch {}
}
const loadTeams = async () => {
  try { const res = await getTeams({ page: 1, size: 1000 }); allTeams.value = res.data.records } catch {}
}
const loadDepartments = async () => {
  try { const res = await organizationApi.getDepartments({ page: 1, size: 1000 }); allDepartments.value = res.data.records } catch {}
}
const loadPositionTags = async () => {
  try { const res = await positionTagApi.getPositionTags({ page: 1, size: 1000 }); allPositionTags.value = Array.isArray(res.data?.records) ? res.data.records : [] } catch { allPositionTags.value = [] }
}

const getPositionTagName = (tagId) => {
  if (!Array.isArray(allPositionTags.value)) return ''
  const tag = allPositionTags.value.find(t => t.id === tagId)
  return tag ? tag.name : ''
}

// 根据选中的组织过滤项目组
const filteredTeams = computed(() => {
  if (!form.departmentIds || form.departmentIds.length === 0) {
    // 没选组织时显示所有启用的项目组
    return allTeams.value.filter(t => t.status === 1)
  }
  // 只显示所选组织下的项目组
  return allTeams.value.filter(t => t.status === 1 && form.departmentIds.includes(t.department_id))
})

// 组织变更时，移除不属于所选组织的项目组
const handleDepartmentChange = () => {
  if (form.departmentIds.length > 0) {
    const validTeamIds = filteredTeams.value.map(t => t.id)
    form.teamIds = form.teamIds.filter(id => validTeamIds.includes(id))
  }
}

const handleSearch = () => { page.value = 1; loadData() }

const loadData = async () => {
  loadingStore.showLoading()
  try {
    const params = { page: page.value, size: size.value }
    if (searchKeyword.value && searchKeyword.value.trim()) params.search = searchKeyword.value.trim()
    if (filterRoleId.value) params.role_id = filterRoleId.value
    const res = await getUsers(params)
    tableData.value = res.data.records
    total.value = res.data.total
  } catch { ElMessage.error(t('user.loadFailed')) } finally { loadingStore.hideLoading() }
}

const getRoleName = (roleId) => {
  const role = allRoles.value.find(r => r.id === roleId)
  return role ? role.name : ''
}

const getRoleTagType = (roleId) => {
  const name = getRoleName(roleId)
  if (name.includes('管理员') || name.includes('Admin')) return 'danger'
  if (name.includes('经理') || name.includes('Manager')) return 'primary'
  if (name.includes('组长') || name.includes('Leader')) return 'warning'
  if (name.includes('工程师') || name.includes('Engineer')) return 'success'
  if (name.includes('RD') || name.includes('开发') || name.includes('PM') || name.includes('产品')) return 'info'
  return 'default'
}

const handleResetPassword = async () => {
  if (!form.id || !form.email) { ElMessage.warning(t('user.resetPasswordMissing')); return }
  try {
    await ElMessageBox.confirm(t('user.resetPasswordConfirm', { username: form.username }), t('user.resetPassword'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    resettingPassword.value = true
    const res = await resetUserPassword(form.id)
    const newPwd = res.data?.new_password
    if (newPwd) {
      await ElMessageBox.alert(
        `新密码：${newPwd}\n\n请复制后告知用户，此密码仅显示一次。`,
        '密码已重置',
        { confirmButtonText: '我已复制', type: 'success', dangerouslyUseHTMLString: false }
      )
    } else {
      ElMessage.success(t('user.resetPasswordSuccess'))
    }
  } catch (e) { if (e !== 'cancel') ElMessage.error(t('user.resetPasswordFailed')) } finally { resettingPassword.value = false }
}

const handleUnlockUser = async () => {
  if (!form.id) return
  try {
    await ElMessageBox.confirm(`确定要解锁用户 ${form.username} 的登录锁定吗？`, '解锁账户', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' })
    unlocking.value = true
    const res = await unlockUser(form.id)
    ElMessage.success(res.message || '账户已解锁')
  } catch (e) { if (e !== 'cancel') ElMessage.error('解锁失败') } finally { unlocking.value = false }
}

const handleCreate = () => {
  form.id = null; form.username = ''; form.email = ''; form.full_name = ''; form.phone = ''; form.password = ''
  form.roleId = null; form.teamIds = []; form.departmentIds = []
  form.position_tag_id = null; form.status = 1
  dialogVisible.value = true
  setTimeout(() => { if (formRef.value) formRef.value.clearValidate() }, 0)
}

const handleDialogOpen = () => {
  if (!form.id) { form.username = ''; form.password = ''; form.full_name = ''; form.email = ''; form.phone = '' }
}

const handleEdit = async (row) => {
  form.id = row.id; form.username = row.username; form.full_name = row.full_name
  form.email = row.email; form.phone = row.phone || ''; form.roleId = row.roleId
  form.teamIds = row.teamIds || []; form.departmentIds = row.departmentIds || []
  form.position_tag_id = row.position_tag_id; form.status = row.status
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.username || !form.username.trim()) { ElMessage.warning(t('user.inputUsername')); return }
  if (!form.email || !form.email.trim()) { ElMessage.warning(t('user.inputEmail')); return }
  if (!form.roleId) { ElMessage.warning(t('user.roleRequired')); return }
  if (!form.position_tag_id) { ElMessage.warning(t('user.dataPermissionRequired')); return }
  submitting.value = true
  try {
    const userData = { username: form.username, full_name: form.full_name, email: form.email, phone: form.phone || null, status: form.status, position_tag_id: form.position_tag_id }
    if (!form.id) userData.password = form.email
    let userId
    if (form.id) { await updateUser(form.id, userData); userId = form.id; ElMessage.success(t('user.updateSuccess')) }
    else { const res = await createUser(userData); userId = res.data.id; ElMessage.success(t('user.createSuccess')) }
    // 保存角色
    if (form.roleId) await assignRoles(userId, [form.roleId])
    // 保存组织
    await organizationApi.assignUserDepartments(userId, form.departmentIds || [])
    // 保存项目组
    await assignTeams({ user_id: userId, team_ids: form.teamIds || [] })
    dialogVisible.value = false; loadData()
    eventBus.emit('users-changed')
  } catch (e) { ElMessage.error(e.response?.data?.detail || t('common.operation') + t('common.failed')) } finally { submitting.value = false }
}

const handleStatusChange = async (row) => {
  const newStatus = row.status === 1 ? 0 : 1
  const statusText = newStatus === 1 ? t('common.enabled') : t('common.disabled')
  try {
    await ElMessageBox.confirm(t('user.statusToggleConfirm', { action: statusText }), t('user.statusToggle'), { confirmButtonText: t('common.confirm'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await toggleUserStatus(row.id); row.status = newStatus
    ElMessage.success(t('user.statusUpdateSuccess', { action: statusText }))
  } catch (e) { if (e !== 'cancel') ElMessage.error(t('user.statusToggle') + t('common.failed')) }
}

const handleDialogClosed = () => { if (document.activeElement instanceof HTMLElement) document.activeElement.blur() }

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('user.deleteConfirm'), t('user.deleteTitle'), { confirmButtonText: t('common.confirm') + t('common.delete'), cancelButtonText: t('common.cancel'), type: 'warning' })
    await deleteUser(row.id); ElMessage.success(t('user.deleteSuccess')); loadData()
    eventBus.emit('users-changed')
  } catch (e) { if (e !== 'cancel') ElMessage.error(t('common.delete') + t('common.failed')) }
}

const handleRowClick = (row) => { /* 预留行点击 */ }

const loadPendingUsers = async () => {
  try {
    const res = await getPendingUsers()
    pendingUsers.value = res.data || []
  } catch { pendingUsers.value = [] }
}

const handleApprove = async () => {
  if (!approveTarget.value) return
  approving.value = true
  try {
    const data = {}
    if (approveForm.role_id) data.role_id = approveForm.role_id
    if (approveForm.position_tag_id) data.position_tag_id = approveForm.position_tag_id
    if (approveForm.department_ids.length > 0) data.department_ids = approveForm.department_ids
    if (approveForm.team_ids.length > 0) data.team_ids = approveForm.team_ids
    await approveUser(approveTarget.value.id, data)
    ElMessage.success(`已通过用户 ${approveTarget.value.username} 的注册申请`)
    approveDialogVisible.value = false
    loadPendingUsers()
    loadData()
    eventBus.emit('users-changed')
  } catch { ElMessage.error('审核操作失败') } finally { approving.value = false }
}

const handleReject = async (row) => {
  try {
    await ElMessageBox.confirm(`确定拒绝用户 ${row.username} 的注册申请？拒绝后将删除该申请。`, '拒绝注册', { confirmButtonText: '确定拒绝', cancelButtonText: '取消', type: 'warning' })
    await rejectUser(row.id)
    ElMessage.success('已拒绝')
    loadPendingUsers()
  } catch (e) { if (e !== 'cancel') ElMessage.error('操作失败') }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  const pad = (n) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
}

const importDialogVisible = ref(false)
const selectedFile = ref(null)
const fileList = ref([])
const importing = ref(false)
const importProgress = ref({ total: 0, processed: 0, status: '', message: '' })

const handleDownloadTemplate = async () => {
  try {
    const res = await downloadUserTemplate()
    const blob = res.data
    const link = document.createElement('a')
    link.href = window.URL.createObjectURL(blob)
    link.download = 'user_import_template.xlsx'
    link.click()
    window.URL.revokeObjectURL(link.href)
  } catch (e) { ElMessage.error('模板下载失败') }
}

const handleFileChange = (file) => {
  selectedFile.value = file.raw
  fileList.value = [file]
}

const handleFileRemove = () => {
  selectedFile.value = null
  fileList.value = []
}

const handleImport = async () => {
  if (!selectedFile.value) { ElMessage.warning('请选择要导入的文件'); return }
  importing.value = true
  importProgress.value = { total: 0, processed: 0, status: 'processing', message: '正在提交...' }
  
  const formData = new FormData()
  formData.append('file', selectedFile.value)
  
  try {
    const result = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          importProgress.value = {
            ...importProgress.value,
            processed: Math.round(e.loaded),
            total: e.total,
            message: '正在上传...'
          }
        }
      }
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch {
            reject(new Error('服务器响应解析失败'))
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText)
            reject(new Error(err.detail || err.message || '导入失败'))
          } catch {
            reject(new Error(`导入失败 (${xhr.status})`))
          }
        }
      }
      
      xhr.onerror = () => reject(new Error('网络连接失败'))
      xhr.ontimeout = () => reject(new Error('请求超时'))
      xhr.timeout = 300000  // 5分钟上传超时
      
      xhr.open('POST', '/api/users/batch-import')
      xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
      xhr.send(formData)
    })
    
    const taskId = result?.data?.task_id
    if (taskId) {
      await pollImportProgress(taskId)
    } else {
      ElMessage.success(result.message || '导入成功')
      importDialogVisible.value = false
      selectedFile.value = null
      fileList.value = []
      loadData()
      eventBus.emit('users-changed')
    }
  } catch (e) {
    ElMessage.error(e.message || '导入失败')
  } finally {
    importing.value = false
  }
}

// 轮询导入进度
const pollImportProgress = (taskId) => {
  return new Promise((resolve, reject) => {
    const token = localStorage.getItem('token')
    const poll = () => {
      fetch(`/api/users/batch-import/progress/${taskId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(res => {
          const data = res.data || res
          importProgress.value = data
          
          if (data.status === 'completed' || data.status === 'done') {
            importing.value = false
            ElMessage.success(data.message || '导入成功')
            importDialogVisible.value = false
            selectedFile.value = null
            fileList.value = []
            loadData()
            eventBus.emit('users-changed')
            resolve(data)
          } else if (data.status === 'error') {
            importing.value = false
            ElMessage.error(data.message || '导入失败')
            resolve(data)
          } else if (data.status === 'not_found') {
            importing.value = false
            ElMessage.error('导入任务不存在')
            resolve({ status: 'error', message: '导入任务不存在' })
          } else {
            setTimeout(poll, 1000)
          }
        })
        .catch(err => {
          console.error('轮询进度失败:', err)
          setTimeout(poll, 3000)
        })
    }
    poll()
  })
}

onMounted(async () => {
  await Promise.all([loadRoles(), loadTeams(), loadPositionTags(), loadDepartments()])
  loadData(); loadPendingUsers(); bindTableHeight()
})
onBeforeUnmount(() => { 
  unbindTableHeight() 
})
</script>

<style scoped>
/* ==================== */
/* 页面布局 - 与用例管理一致 */
/* ==================== */
.user-page {
  height: 100%;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  padding: 24px;
}

.user-page::-webkit-scrollbar { width: 8px; }
.user-page::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.user-page::-webkit-scrollbar-thumb:hover { background: #94a3b8; }
.user-page::-webkit-scrollbar-track { background: #f1f5f9; }

/* ==================== */
/* 表格卡片 - Demo风格 */
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

.header-right :deep(.el-select) {
  height: 40px !important;
}

.header-right :deep(.el-select .el-select__wrapper) {
  height: 40px !important;
  min-height: 40px !important;
  box-sizing: border-box !important;
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

/* 表格单元格高度 */
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

/* 表格滚动 */
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



.cell-text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

/* ==================== */
/* 表格单元格内容样式 */
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

/* ==================== */
/* 分页 - Demo风格 */
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
/* 按钮 - Demo风格 */
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
/* 对话框 - Demo风格 */
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

/* 斑马纹 */
.table-wrapper :deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #fafbfc;
}

/* 导入对话框样式 */
.import-tips {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.import-tip-title {
  font-weight: 600;
  color: #0369a1;
  margin-bottom: 8px;
}

.import-tip-list {
  margin: 0;
  padding-left: 20px;
  color: #075985;
  font-size: 13px;
}

.import-tip-list li {
  margin-bottom: 4px;
}

.import-actions {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 8px;
}

.import-tip-info {
  background: var(--demo-primary-light, rgba(79, 70, 229, 0.08));
  border: 1px solid var(--demo-border-light, #e2e8f0);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
}

.import-tip-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--primary-color, #409eff);
  margin-bottom: 12px;
  font-size: 14px;
}

.import-tip-header .el-icon {
  font-size: 16px;
}

.import-tip-content {
  margin: 0;
  padding-left: 24px;
  color: var(--text-regular, #606266);
  font-size: 13px;
  line-height: 1.8;
}

.import-tip-content li {
  margin-bottom: 2px;
}

.import-tip-content strong {
  color: #dc2626;
}

.import-upload {
  width: 100%;
}

.import-upload :deep(.el-upload-list) {
  margin-top: 12px;
}

.import-upload :deep(.el-upload__tip) {
  margin-top: 8px;
  color: #94a3b8;
  font-size: 12px;
}

.import-overwrite {
  margin: 16px 0;
}

.import-template-link {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

.import-user-dialog :deep(.el-dialog__body) {
  padding: 20px 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
