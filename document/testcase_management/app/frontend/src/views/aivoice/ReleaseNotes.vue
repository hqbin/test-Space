<template>
  <div class="release-notes">
    <div class="toolbar">
      <el-button type="primary" @click="showCreate = true"><el-icon><Plus /></el-icon>新建发版说明</el-button>
      <div class="search-bar">
        <el-input v-model="filters.keyword" placeholder="搜索版本/分支/提交人..." clearable style="width:240px" @keyup.enter="loadData" />
        <el-select v-model="filters.changeType" placeholder="变更类型" clearable style="width:130px">
          <el-option v-for="t in changeTypes" :key="t" :label="t" :value="t" />
        </el-select>
        <el-select v-model="filters.severity" placeholder="严重程度" clearable style="width:120px">
          <el-option v-for="s in severities" :key="s" :label="s" :value="s" />
        </el-select>
        <el-button @click="loadData"><el-icon><Search /></el-icon>搜索</el-button>
      </div>
    </div>

    <el-table :data="tableData" v-loading="loading" border stripe row-key="id" default-expand-all :tree-props="{ children: 'children' }">
      <el-table-column prop="version" label="版本号" width="140" />
      <el-table-column prop="author" label="提交人" width="100" />
      <el-table-column prop="changeType" label="类型" width="80">
        <template #default="{ row }"><el-tag size="small">{{ row.changeType }}</el-tag></template>
      </el-table-column>
      <el-table-column prop="severity" label="严重程度" width="80">
        <template #default="{ row }">
          <el-tag :type="sevType(row.severity)" size="small">{{ row.severity }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="branch" label="分支" width="120" show-overflow-tooltip />
      <el-table-column prop="changeDescription" label="变更描述" min-width="250" show-overflow-tooltip />
      <el-table-column prop="rdSmokeStatus" label="冒烟状态" width="100">
        <template #default="{ row }">
          <el-tag :type="smokeType(row.rdSmokeStatus)" size="small">{{ row.rdSmokeStatus }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="createdAt" label="创建时间" width="160">
        <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button size="small" text @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" text type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination v-if="total > 0" :current-page="page" :page-size="pageSize" :total="total" layout="total, prev, pager, next" @current-change="onPageChange" class="pagination" />

    <el-dialog v-model="showCreate" :title="editing ? '编辑发版说明' : '新建发版说明'" width="700px">
      <el-form :model="form" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="版本号" required>
              <el-input v-model="form.version" placeholder="如 v1.2.3" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="父版本">
              <el-select v-model="form.parentVersion" clearable filterable placeholder="选择父版本" style="width:100%">
                <el-option v-for="pv in parentVersions" :key="pv.version" :label="pv.version" :value="pv.version" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="提交人" required>
              <el-input v-model="form.author" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分支">
              <el-input v-model="form.branch" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="变更描述" required>
          <el-input v-model="form.changeDescription" type="textarea" :rows="3" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="变更类型">
              <el-select v-model="form.changeType" style="width:100%">
                <el-option v-for="t in changeTypes" :key="t" :label="t" :value="t" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="严重程度">
              <el-select v-model="form.severity" style="width:100%">
                <el-option v-for="s in severities" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="冒烟状态">
              <el-select v-model="form.rdSmokeStatus" style="width:100%">
                <el-option v-for="s in smokeStatuses" :key="s" :label="s" :value="s" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="commit">
          <el-input v-model="form.commitHash" placeholder="commit hash" style="width:200px" />
          <el-input v-model="form.commitMessage" placeholder="commit message" style="width:300px;margin-left:8px" />
        </el-form-item>
        <el-form-item label="影响模块">
          <el-select v-model="form.affectedModules" multiple filterable allow-create default-first-option style="width:100%">
            <el-option v-for="t in impactTags" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="回归风险">
          <el-input v-model="form.regressionRisk" type="textarea" :rows="2" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getReleaseNotes, createReleaseNote, updateReleaseNote, deleteReleaseNote, getParentVersions, getImpactTags } from '@/api/aivoice'

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const filters = ref({ keyword: '', changeType: '', severity: '' })
const showCreate = ref(false)
const editing = ref(null)
const saving = ref(false)
const parentVersions = ref([])
const impactTags = ref([])
const emptyForm = () => ({ version: '', parentVersion: '', author: '', branch: '', changeDescription: '', changeType: '功能', severity: '中', rdSmokeStatus: '未测试', commitHash: '', commitMessage: '', affectedModules: [], regressionRisk: '' })
const form = ref(emptyForm())

const changeTypes = ['功能', '修复', '优化', '重构', '配置', '文档', '其他']
const severities = ['高', '中', '低']
const smokeStatuses = ['未测试', '通过', '失败', '阻塞']
const sevType = (s) => ({ '高': 'danger', '中': 'warning', '低': 'info' }[s] || 'info')
const smokeType = (s) => ({ '通过': 'success', '失败': 'danger', '阻塞': 'warning', '未测试': 'info' }[s] || 'info')
const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : ''

const loadData = async () => {
  loading.value = true
  try {
    const res = await getReleaseNotes({ ...filters.value, page: page.value, pageSize: pageSize.value, workspaceId: 'AI Voice' })
    tableData.value = res.data?.data || []
    total.value = res.data?.total || 0
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

const loadParentVersions = async () => {
  try {
    const res = await getParentVersions({ workspaceId: 'AI Voice' })
    parentVersions.value = res.data || []
  } catch (e) { console.error(e) }
}

const loadImpactTags = async () => {
  try {
    const res = await getImpactTags({ workspaceId: 'AI Voice' })
    impactTags.value = res.data || []
  } catch (e) { console.error(e) }
}

const onPageChange = (p) => { page.value = p; loadData() }

const handleEdit = (row) => {
  editing.value = row.id
  form.value = {
    version: row.version || '',
    parentVersion: row.parentVersion || '',
    author: row.author || '',
    branch: row.branch || '',
    changeDescription: row.changeDescription || '',
    changeType: row.changeType || '功能',
    severity: row.severity || '中',
    rdSmokeStatus: row.rdSmokeStatus || '未测试',
    commitHash: row.commitHash || '',
    commitMessage: row.commitMessage || '',
    affectedModules: Array.isArray(row.affectedModules) ? row.affectedModules : [],
    regressionRisk: row.regressionRisk || '',
  }
  showCreate.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除版本 ${row.version} 的发版说明？`)
    await deleteReleaseNote(row.id)
    ElMessage.success('删除成功')
    await loadData()
  } catch (e) { /* cancelled */ }
}

const handleSave = async () => {
  saving.value = true
  try {
    if (editing.value) {
      await updateReleaseNote(editing.value, form.value)
    } else {
      await createReleaseNote({ ...form.value, workspaceId: 'AI Voice' })
    }
    ElMessage.success(editing.value ? '更新成功' : '创建成功')
    showCreate.value = false
    editing.value = null
    form.value = emptyForm()
    await loadData()
  } catch (e) { ElMessage.error('操作失败') }
  finally { saving.value = false }
}

onMounted(() => { loadData(); loadParentVersions(); loadImpactTags() })
</script>

<style scoped>
.release-notes { padding: 20px; }
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; align-items: center; }
.search-bar { display: flex; gap: 8px; align-items: center; margin-left: auto; }
.pagination { margin-top: 16px; justify-content: flex-end; }
</style>
