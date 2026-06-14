<template>
  <div class="dingtalk-bot-content">
    <!-- 工具栏 -->
    <div class="table-header">
      <div class="header-left">
        <div class="action-buttons">
          <el-button v-if="hasButton('notificationManagement', 'createDingtalkBot')" type="primary" @click="handleCreate">
            <el-icon><Plus /></el-icon>
            新增机器人
          </el-button>
        </div>
      </div>
      <div class="header-right">
        <el-select v-model="filterTeamId" placeholder="按项目组筛选" clearable style="width: 160px" @change="handleSearch">
          <el-option v-for="team in allTeams" :key="team.id" :label="team.name" :value="team.id" />
        </el-select>
        <el-select v-model="filterActive" placeholder="启用状态" clearable style="width: 120px" @change="handleSearch">
          <el-option label="已启用" :value="true" />
          <el-option label="已禁用" :value="false" />
        </el-select>
        <el-input v-model="searchText" placeholder="搜索机器人名称" clearable style="width: 220px" size="large" @clear="handleSearch" @keyup.enter="handleSearch">
          <template #suffix>
            <el-icon class="el-input__icon" style="cursor: pointer;" @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 表格 -->
    <div class="table-wrapper">
      <div class="table-container" ref="tableContainerRef">
        <el-table ref="tableRef" :data="tableData" style="width: 100%" :height="tableHeight"
          :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }">
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="机器人名称" min-width="160" />
          <el-table-column prop="team_name" label="项目组" width="140" />
          <el-table-column label="通知类型" min-width="200">
            <template #default="{ row }">
              <el-tag v-for="t in row.notification_types" :key="t" :type="getTypeTagColor(t)" size="small" style="margin-right: 4px;">
                {{ getTypeLabel(t) }}
              </el-tag>
              <span v-if="!row.notification_types?.length" style="color: #94a3b8;">未配置</span>
            </template>
          </el-table-column>
          <el-table-column prop="security_type" label="安全方式" width="100" align="center">
            <template #default="{ row }">
              <el-tag :type="row.security_type === 'sign' ? 'warning' : 'info'" size="small">
                {{ row.security_type === 'sign' ? '加签' : '关键词' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="is_active" label="状态" width="90" align="center">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="handleToggle(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="170">
            <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="success" @click="handleTest(row)" :loading="row._testing">
                <el-icon><Connection /></el-icon>
              </el-button>
              <el-button v-if="hasButton('notificationManagement', 'editDingtalkBot')" link type="primary" @click="handleEdit(row)">
                <el-icon><Edit /></el-icon>
              </el-button>
              <el-button v-if="hasButton('notificationManagement', 'deleteDingtalkBot')" link type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon>
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[10, 20, 50, 100]" :total="total" layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange" @current-change="handleCurrentChange" />
    </div>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="650px" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item label="机器人名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入机器人名称" />
        </el-form-item>
        <el-form-item label="Webhook URL" prop="webhook_url">
          <el-input v-model="form.webhook_url" :placeholder="isEdit ? '留空则不修改' : 'https://oapi.dingtalk.com/robot/send?access_token=...'" />
        </el-form-item>
        <el-form-item label="安全方式" prop="security_type">
          <el-radio-group v-model="form.security_type">
            <el-radio value="keyword">自定义关键词</el-radio>
            <el-radio value="sign">加签</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="form.security_type === 'sign' ? 'Secret' : '关键词'" prop="security_value">
          <el-input v-model="form.security_value" :placeholder="isEdit ? '留空则不修改' : (form.security_type === 'sign' ? '请输入加签Secret' : '请输入自定义关键词')" :type="form.security_type === 'sign' ? 'password' : 'text'" show-password />
        </el-form-item>
        <el-form-item label="项目组" prop="team_id">
          <el-select v-model="form.team_id" placeholder="请选择项目组" style="width: 100%" filterable>
            <el-option v-for="team in allTeams" :key="team.id" :label="team.name" :value="team.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="通知类型" prop="notification_types">
          <el-checkbox-group v-model="form.notification_types">
            <el-checkbox value="testcase">测试用例</el-checkbox>
            <el-checkbox value="testplan">测试计划</el-checkbox>
            <el-checkbox value="execution">测试执行</el-checkbox>
            <el-checkbox value="report">测试报告</el-checkbox>
            <el-checkbox value="system">系统通知</el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, Connection } from '@element-plus/icons-vue'
import { getDingtalkBots, createDingtalkBot, updateDingtalkBot, deleteDingtalkBot, toggleDingtalkBot, testDingtalkBot } from '@/api/dingtalkBot'
import { getTeams } from '@/api/team'
import { useTableHeight } from '@/composables/useTableHeight'
import { useUserRole } from '../../composables/useUserRole'

const { hasButton } = useUserRole()
const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()

const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const searchText = ref('')
const filterTeamId = ref(null)
const filterActive = ref(null)
const allTeams = ref([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const isEdit = ref(false)
const submitting = ref(false)
const formRef = ref(null)

const form = reactive({
  id: null,
  name: '',
  webhook_url: '',
  security_type: 'keyword',
  security_value: '',
  team_id: null,
  notification_types: [],
  is_active: true
})

const rules = {
  name: [{ required: true, message: '请输入机器人名称', trigger: 'blur' }],
  webhook_url: [
    { validator: (rule, value, callback) => { if (!isEdit.value && !value) { callback(new Error('请输入Webhook URL')) } else if (value && !/^https:\/\/oapi\.dingtalk\.com\/robot\/send/.test(value)) { callback(new Error('URL必须以 https://oapi.dingtalk.com/robot/send 开头')) } else { callback() } }, trigger: 'blur' }
  ],
  security_type: [{ required: true, message: '请选择安全方式', trigger: 'change' }],
  security_value: [
    { validator: (rule, value, callback) => { if (!isEdit.value && !value) { callback(new Error('请输入安全设置值')) } else { callback() } }, trigger: 'blur' }
  ],
  team_id: [{ required: true, message: '请选择项目组', trigger: 'change' }]
}

const getTypeTagColor = (type) => {
  const map = { testcase: 'primary', testplan: 'success', execution: 'warning', report: 'danger', system: 'info' }
  return map[type] || 'info'
}

const getTypeLabel = (type) => {
  const map = { testcase: '测试用例', testplan: '测试计划', execution: '测试执行', report: '测试报告', system: '系统通知' }
  return map[type] || type
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const loadData = async () => {
  try {
    const params = { page: currentPage.value, size: pageSize.value }
    if (searchText.value) params.search = searchText.value
    if (filterTeamId.value != null) params.team_id = filterTeamId.value
    if (filterActive.value != null) params.is_active = filterActive.value
    const response = await getDingtalkBots(params)
    tableData.value = response.data.records
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载钉钉机器人列表失败')
  }
}

const loadTeams = async () => {
  try {
    const response = await getTeams({ page: 1, size: 1000 })
    allTeams.value = response.data?.records || response.data || []
  } catch (error) {
    console.error('加载项目组列表失败:', error)
  }
}

const handleSearch = () => { currentPage.value = 1; loadData() }
const handleSizeChange = () => { currentPage.value = 1; loadData() }
const handleCurrentChange = () => { loadData() }

const handleCreate = () => {
  isEdit.value = false
  dialogTitle.value = '新增钉钉机器人'
  Object.assign(form, { id: null, name: '', webhook_url: '', security_type: 'keyword', security_value: '', team_id: null, notification_types: [], is_active: true })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  isEdit.value = true
  dialogTitle.value = '编辑钉钉机器人'
  Object.assign(form, {
    id: row.id, name: row.name, webhook_url: '', security_type: row.security_type,
    security_value: '', team_id: row.team_id, notification_types: row.notification_types || [], is_active: row.is_active
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    submitting.value = true
    try {
      const data = {
        name: form.name, webhook_url: form.webhook_url, security_type: form.security_type,
        security_value: form.security_value, team_id: form.team_id,
        notification_types: form.notification_types, is_active: form.is_active
      }
      if (isEdit.value) {
        // 编辑时，如果URL和secret为空则不更新
        const updateData = { ...data }
        if (!updateData.webhook_url) delete updateData.webhook_url
        if (!updateData.security_value) delete updateData.security_value
        await updateDingtalkBot(form.id, updateData)
        ElMessage.success('更新成功')
      } else {
        await createDingtalkBot(data)
        ElMessage.success('创建成功')
      }
      dialogVisible.value = false
      loadData()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    } finally {
      submitting.value = false
    }
  })
}

const handleToggle = async (row) => {
  try {
    await toggleDingtalkBot(row.id)
    ElMessage.success(row.is_active ? '已启用' : '已禁用')
  } catch (error) {
    row.is_active = !row.is_active
    ElMessage.error('状态切换失败')
  }
}

const handleTest = async (row) => {
  row._testing = true
  try {
    await testDingtalkBot(row.id)
    ElMessage.success('测试消息发送成功，请检查钉钉群')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '测试发送失败')
  } finally {
    row._testing = false
  }
}

const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除机器人「${row.name}」吗？`, '警告', {
    confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning'
  }).then(async () => {
    await deleteDingtalkBot(row.id)
    ElMessage.success('删除成功')
    loadData()
  }).catch(() => {})
}

onMounted(() => { loadData(); loadTeams(); bindTableHeight() })
onBeforeUnmount(() => { unbindTableHeight() })
</script>

<style scoped>
.dingtalk-bot-content { display: flex; flex-direction: column; height: 100%; }
.table-header { padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #e2e8f0; flex-shrink: 0; background-color: rgba(248, 250, 252, 0.5); gap: 12px; }
.header-left { display: flex; gap: 12px; align-items: center; flex-shrink: 0; }
.header-right { display: flex; gap: 12px; align-items: center; flex-shrink: 0; margin-left: auto; }
.header-right :deep(.el-input__wrapper) { height: 40px !important; min-height: 40px !important; padding: 1px 11px !important; box-sizing: border-box !important; display: flex !important; align-items: center !important; }
.header-right :deep(.el-input__inner) { height: 38px !important; line-height: 38px !important; }
.action-buttons { display: flex; gap: 8px; align-items: center; }
.action-buttons .el-button { border-radius: 8px !important; font-weight: 500 !important; height: 40px !important; padding: 0 18px !important; font-size: 14px !important; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important; }
.action-buttons .el-button--primary { background: #4f46e5 !important; border: none !important; }
.action-buttons .el-button--primary:hover { background: #4338ca !important; }
.table-wrapper { flex: 1; display: flex; flex-direction: column; min-height: 0; width: 100%; overflow: hidden; }
.table-wrapper .table-container { flex: 1; min-height: 0; overflow: hidden; }
.table-wrapper :deep(.el-table) { width: 100%; position: relative; }
.table-wrapper :deep(.el-table td.el-table__cell), .table-wrapper :deep(.el-table th.el-table__cell) { height: 48px !important; padding: 0 12px !important; }
.table-wrapper :deep(.el-table td.el-table__cell .cell), .table-wrapper :deep(.el-table th.el-table__cell .cell) { line-height: 48px; padding: 0; }
.table-wrapper :deep(.el-table__body-wrapper) { overflow-y: auto !important; overflow-x: auto !important; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar { height: 8px; width: 8px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track { background: #f1f5f9; }
.table-wrapper :deep(.el-table__header-wrapper) { overflow: hidden !important; position: relative; z-index: 10 !important; }

.table-wrapper :deep(.el-table__row:hover > td) { background: #f8fafc !important; }
.pagination-container { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; background: #fff; flex-shrink: 0; border-top: 1px solid #e2e8f0; min-height: 56px; }
.pagination-container :deep(.el-pager li) { background: transparent; font-weight: 500; border-radius: 6px; min-width: 32px; height: 32px; }
.pagination-container :deep(.el-pager li.is-active) { background: #eef2ff; color: #4f46e5; font-weight: 600; }
.pagination-container :deep(.el-pager li:hover:not(.is-active)) { background: #f1f5f9; }
.pagination-container :deep(.el-pagination__total) { font-size: 14px; color: #64748b; }
:deep(.el-button) { border-radius: 8px; font-weight: 500; transition: all 0.15s; }
:deep(.el-button:hover) { transform: none; box-shadow: none; }
:deep(.el-button--primary) { background: #4f46e5; border: none; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05); }
:deep(.el-button--primary:hover) { background: #4338ca; }
:deep(.el-button--danger) { background: #ef4444; border: none; }
:deep(.el-button--danger:hover) { background: #dc2626; }
:deep(.el-switch) { --el-switch-on-color: #4f46e5; --el-switch-off-color: #cbd5e1; }
:deep(.el-dialog) { border-radius: 16px; overflow: hidden; }
:deep(.el-dialog__header) { padding: 20px 24px 16px; border-bottom: 1px solid #e2e8f0; margin-right: 0; }
:deep(.el-dialog__title) { font-size: 18px; font-weight: 600; color: #0f172a; }
:deep(.el-dialog__body) { padding: 24px; }
:deep(.el-dialog__footer) { padding: 16px 24px; border-top: 1px solid #e2e8f0; }
:deep(.el-form-item__label) { font-weight: 500; color: #334155; font-size: 14px; }
:deep(.el-input__wrapper), :deep(.el-select) { border-radius: 8px; }
</style>
