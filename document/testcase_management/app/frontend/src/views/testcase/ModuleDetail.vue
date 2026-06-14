<template>
  <div class="module-detail-page">
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack" class="back-btn">
          返回
        </el-button>
        <h2 class="page-title">{{ moduleInfo.name }}</h2>
        <el-tag v-if="moduleInfo.tag" type="primary" size="default" class="module-tag">
          {{ moduleInfo.tag }}
        </el-tag>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Edit" @click="handleEditModule">
          编辑主模块
        </el-button>
        <el-button type="primary" :icon="Plus" @click="handleAddSubModule">
          新增子模块
        </el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="info-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="card-title">模块信息</span>
            </div>
          </template>
          <div class="info-content">
            <div class="info-item">
              <span class="info-label">模块名称：</span>
              <span class="info-value">{{ moduleInfo.name }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">Tag：</span>
              <span class="info-value">{{ moduleInfo.tag || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">用例数量：</span>
              <span class="info-value">{{ moduleInfo.count || 0 }} 个</span>
            </div>
            <div class="info-item">
              <span class="info-label">原始需求链接：</span>
              <span class="info-value">
                <a 
                  v-if="moduleInfo.requirement_link" 
                  :href="moduleInfo.requirement_link" 
                  target="_blank" 
                  class="requirement-link"
                >
                  <el-icon><Link /></el-icon>
                  {{ moduleInfo.requirement_link }}
                </a>
                <span v-else class="no-link">未设置</span>
              </span>
            </div>
            <div class="info-item" v-if="!moduleInfo.parent_id">
              <span class="info-label">RD Owner：</span>
              <span class="info-value">{{ moduleInfo.rd_owner || '-' }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="sub-module-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">子模块管理</span>
          <span class="card-count">({{ subModules.length }} 个)</span>
        </div>
      </template>
      <div class="sub-module-list" v-loading="loading">
        <el-table :data="subModules" style="width: 100%" v-if="subModules.length > 0">
          <el-table-column prop="name" label="子模块名称" min-width="200">
            <template #default="scope">
              <div class="sub-module-name">
                <el-icon><Document /></el-icon>
                {{ scope.row.name }}
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="count" label="用例数量" width="120" align="center">
            <template #default="scope">
              <span class="count-badge">{{ scope.row.count || 0 }}</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" align="center">
            <template #default="scope">
              <el-button type="primary" :icon="Edit" size="small" link @click="handleEditSubModule(scope.row)">
                编辑
              </el-button>
              <el-button type="danger" :icon="Delete" size="small" link @click="handleDeleteSubModule(scope.row)">
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!loading && subModules.length === 0" description="暂无子模块，请添加子模块" />
      </div>
    </el-card>

    <!-- 主模块编辑对话框 -->
    <el-dialog 
      v-model="mainModuleEditVisible" 
      title="编辑主模块" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="moduleForm" label-width="120px">
        <el-form-item label="模块名称" required>
          <el-input 
            v-model="moduleForm.name" 
            placeholder="请输入模块名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="Tag">
          <el-input 
            v-model="moduleForm.tag" 
            :placeholder="canEditModuleTag ? '用于用例编号生成，如：CO' : ''"
            :maxlength="50"
            :disabled="!!moduleForm.id && !canEditModuleTag"
            :show-word-limit="canEditModuleTag"
          />
          <div style="color: #e6a23c; font-size: 12px; margin-top: 4px;" v-if="canEditModuleTag">
            Tag创建后不可修改
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;" v-else>
            Tag创建后不可修改
          </div>
        </el-form-item>
        <el-form-item label="原始需求链接">
          <el-input 
            v-model="moduleForm.requirementLink" 
            placeholder="请输入原始需求链接"
            maxlength="500"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;">
            用于关联原始需求文档，支持URL格式
          </div>
        </el-form-item>
        <el-form-item label="RD Owner">
          <el-input 
            v-model="moduleForm.rdOwner" 
            placeholder="请输入RD负责人（非必填）"
            maxlength="200"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="mainModuleEditVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveMainModule" :loading="moduleSaving">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 子模块编辑对话框 -->
    <el-dialog 
      v-model="subModuleEditVisible" 
      :title="subModuleEditTitle" 
      width="450px"
      :close-on-click-modal="false"
    >
      <el-form :model="subModuleForm" label-width="100px">
        <el-form-item label="子模块名称" required>
          <el-input 
            v-model="subModuleForm.name" 
            placeholder="请输入子模块名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="subModuleEditVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveSubModule" :loading="moduleSaving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, Edit, Delete, Document, Link } from '@element-plus/icons-vue'
import { getModuleTree, createModule, updateModule, deleteModule } from '@/api/module'

const route = useRoute()
const router = useRouter()

const projectId = computed(() => route.params.projectId)
const moduleId = computed(() => route.params.moduleId)

const loading = ref(false)
const moduleInfo = ref({})
const subModules = ref([])
const moduleTree = ref([])

const mainModuleEditVisible = ref(false)
const subModuleEditVisible = ref(false)
const subModuleEditTitle = ref('')
const moduleSaving = ref(false)

const canEditModuleTag = ref(true)

const moduleForm = reactive({
  id: null,
  name: '',
  tag: '',
  requirementLink: '',
  rdOwner: ''
})

const subModuleForm = reactive({
  id: null,
  name: ''
})

const goBack = () => {
  router.push(`/projects/${projectId.value}/modules`)
}

const loadModuleData = async () => {
  loading.value = true
  try {
    const res = await getModuleTree(projectId.value)
    moduleTree.value = res.data || []

    const mainModule = moduleTree.value.find(m => m.id === parseInt(moduleId.value))
    if (mainModule) {
      moduleInfo.value = mainModule
      subModules.value = mainModule.children || []
      // 存储模块名称供数据埋点使用
      sessionStorage.setItem(`module_name_${moduleId.value}`, mainModule.name)
    } else {
      ElMessage.error('模块不存在')
      goBack()
    }
  } catch (error) {
    console.error('加载模块数据失败:', error)
    ElMessage.error('加载模块数据失败')
  } finally {
    loading.value = false
  }
}

const handleEditModule = () => {
  moduleForm.id = moduleInfo.value.id
  moduleForm.name = moduleInfo.value.name
  moduleForm.tag = moduleInfo.value.tag || ''
  moduleForm.requirementLink = moduleInfo.value.requirement_link || ''
  moduleForm.rdOwner = moduleInfo.value.rd_owner || ''
  mainModuleEditVisible.value = true
}

const handleSaveMainModule = async () => {
  if (!moduleForm.name || !moduleForm.name.trim()) {
    ElMessage.warning('请输入模块名称')
    return
  }
  
  moduleSaving.value = true
  
  try {
    const updateData = {
      name: moduleForm.name.trim()
    }
    
    if (canEditModuleTag.value) {
      updateData.tag = moduleForm.tag || null
    }
    
    updateData.requirement_link = moduleForm.requirementLink || null
    updateData.rd_owner = moduleForm.rdOwner || null
    
    await updateModule(moduleForm.id, updateData)
    ElMessage.success('更新成功')
    
    mainModuleEditVisible.value = false
    await loadModuleData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    moduleSaving.value = false
  }
}

const handleAddSubModule = () => {
  subModuleForm.id = null
  subModuleForm.name = ''
  subModuleEditTitle.value = '新增子模块'
  subModuleEditVisible.value = true
}

const handleEditSubModule = (subModule) => {
  subModuleForm.id = subModule.id
  subModuleForm.name = subModule.name
  subModuleEditTitle.value = '编辑子模块'
  subModuleEditVisible.value = true
}

const handleSaveSubModule = async () => {
  if (!subModuleForm.name || !subModuleForm.name.trim()) {
    ElMessage.warning('请输入子模块名称')
    return
  }
  
  moduleSaving.value = true
  
  try {
    if (subModuleForm.id) {
      await updateModule(subModuleForm.id, {
        name: subModuleForm.name.trim()
      })
      ElMessage.success('更新成功')
    } else {
      await createModule({
        project_id: projectId.value,
        name: subModuleForm.name.trim(),
        parent_id: moduleId.value
      })
      ElMessage.success('创建成功')
    }
    
    subModuleEditVisible.value = false
    await loadModuleData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    moduleSaving.value = false
  }
}

const handleDeleteSubModule = async (subModule) => {
  if (subModule.count > 0) {
    ElMessage.warning('该子模块下有用例，无法删除')
    return
  }
  
  try {
    await ElMessageBox.confirm(
      `确定要删除子模块"${subModule.name}"吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteModule(subModule.id)
    ElMessage.success('删除成功')
    
    await loadModuleData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadModuleData()
})
</script>

<style scoped>
.module-detail-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-btn {
  padding: 8px 12px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.module-tag {
  margin-left: 8px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.card-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.card-count {
  color: #909399;
  font-size: 14px;
}

.info-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.info-label {
  min-width: 100px;
  color: #909399;
  font-size: 14px;
}

.info-value {
  color: #303133;
  font-size: 14px;
  word-break: break-all;
}

.requirement-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: #409eff;
  text-decoration: none;
  word-break: break-all;
}

.requirement-link:hover {
  text-decoration: underline;
}

.no-link {
  color: #c0c4cc;
}

.sub-module-card {
  margin-top: 0;
}

.sub-module-list {
  min-height: 200px;
}

.sub-module-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.count-badge {
  display: inline-block;
  padding: 2px 8px;
  background: #f0f7ff;
  color: #409eff;
  border-radius: 4px;
  font-size: 13px;
}
</style>
