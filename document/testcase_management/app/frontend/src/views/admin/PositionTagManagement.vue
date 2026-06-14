<template>
  <div class="position-tag-container table-layout">
    <el-card class="table-card table-layout" shadow="never">
      <div class="table-header">
        <div class="header-left">
          <el-button 
            type="primary" 
            :icon="Plus" 
            @click="handleCreate"
          >
            {{ $t('positionTag.createTag') }}
          </el-button>
        </div>
        <div class="header-right">
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('positionTag.searchPlaceholder')"
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
        border
        :header-cell-style="{ background: '#f0f1fb', color: '#606266', fontWeight: '600' }"
      >
        <el-table-column prop="name" :label="$t('positionTag.name')" width="200" />
        <el-table-column prop="description" :label="$t('common.description')" width="300" :show-overflow-tooltip="{ showAfter: 500 }" />
        <el-table-column prop="created_at" :label="$t('common.createdAt')" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.operation')" width="240" align="center" fixed="right">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="default" 
              :icon="Edit" 
              @click="handleEdit(scope.row)"
            >
              {{ $t('common.edit') }}
            </el-button>
            <el-button 
              v-if="!scope.row.is_system"
              type="danger" 
              size="default" 
              :icon="Delete" 
              @click="handleDelete(scope.row)"
            >
              {{ $t('common.delete') }}
            </el-button>
            <el-tooltip 
              v-else
              :content="$t('positionTag.systemDefault')" 
              placement="top"
             :show-after="500">
              <el-button 
                type="danger" 
                size="default" 
                :icon="Delete" 
                disabled
              >
                {{ $t('common.delete') }}
              </el-button>
            </el-tooltip>
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

    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="600px"
      :close-on-click-modal="false"
      :show-close="true"
      @closed="handleDialogClosed"
    >
      <el-form :model="form" ref="formRef" label-width="100px" label-position="top" :style="{ marginBottom: '0' }">
        <el-form-item :label="$t('positionTag.name')" required :style="{ marginBottom: '16px' }">
          <el-input v-model="form.name" :placeholder="$t('positionTag.inputName')" maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item :label="$t('common.description')" :style="{ marginBottom: '20px' }">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="2"
            :placeholder="$t('positionTag.inputDescription')"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="$t('positionTag.contentViewPermission')" :style="{ marginBottom: '20px' }">
          <el-card shadow="never" style="margin-bottom: 15px;">
            <template #header>
              <div class="card-header">
                <span>{{ $t('positionTag.testcase') }}</span>
              </div>
            </template>
            <el-radio-group v-model="form.contentPermissions.testcase" size="large">
              <el-radio-button label="all">{{ $t('positionTag.allVisible') }}</el-radio-button>
              <el-radio-button label="project">{{ $t('positionTag.projectVisible') }}</el-radio-button>
              <el-radio-button label="personal">{{ $t('positionTag.personalVisible') }}</el-radio-button>
            </el-radio-group>
          </el-card>
          <el-card shadow="never" style="margin-bottom: 15px;">
            <template #header>
              <div class="card-header">
                <span>{{ $t('positionTag.report') }}</span>
              </div>
            </template>
            <el-radio-group v-model="form.contentPermissions.report" size="large">
              <el-radio-button label="all">{{ $t('positionTag.allVisible') }}</el-radio-button>
              <el-radio-button label="project">{{ $t('positionTag.projectVisible') }}</el-radio-button>
              <el-radio-button label="personal">{{ $t('positionTag.personalVisible') }}</el-radio-button>
            </el-radio-group>
          </el-card>
          <el-card shadow="never" style="margin-bottom: 15px;">
            <template #header>
              <div class="card-header">
                <span>{{ $t('positionTag.testplan') }}</span>
              </div>
            </template>
            <el-radio-group v-model="form.contentPermissions.testplan" size="large">
              <el-radio-button label="all">{{ $t('positionTag.allVisible') }}</el-radio-button>
              <el-radio-button label="project">{{ $t('positionTag.projectVisible') }}</el-radio-button>
              <el-radio-button label="personal">{{ $t('positionTag.personalVisible') }}</el-radio-button>
            </el-radio-group>
          </el-card>
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <span>{{ $t('positionTag.notification') }}</span>
              </div>
            </template>
            <el-radio-group v-model="form.contentPermissions.notification" size="large">
              <el-radio-button label="all">{{ $t('positionTag.allVisible') }}</el-radio-button>
              <el-radio-button label="project">{{ $t('positionTag.projectVisible') }}</el-radio-button>
              <el-radio-button label="personal">{{ $t('positionTag.personalVisible') }}</el-radio-button>
            </el-radio-group>
          </el-card>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { positionTagApi } from '../../api/positionTag'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete, Search } from '@element-plus/icons-vue'
import { useTableHeight } from '../../composables/useTableHeight'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { usePagination } from '../../composables/usePagination'
import { useLoadingStore } from '../../stores/loading'

const { t } = useI18n()

const { tableContainerRef, tableHeight, bindTableHeight, unbindTableHeight } = useTableHeight()
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const loadingStore = useLoadingStore()
const tableData = ref([])
const { page, size, total } = usePagination('positionTagManagement', 10)
const searchKeyword = ref('')
const dialogVisible = ref(false)
const dialogTitle = computed(() => form.id ? t('positionTag.editTag') : t('positionTag.createTag'))
const submitting = ref(false)
const formRef = ref(null)
const form = reactive({
  id: null,
  name: '',
  description: '',
  contentPermissions: {
    testcase: 'all',
    report: 'all',
    testplan: 'all',
    notification: 'all'
  }
})

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const loadData = async () => {
  loadingStore.showLoading()
  try {
    const res = await positionTagApi.getPositionTags()
    
    if (res.data && res.data.records) {
      tableData.value = res.data.records
      total.value = res.data.total || 0
    } else if (Array.isArray(res.data)) {
      tableData.value = res.data
      total.value = res.data.length
    } else {
      tableData.value = []
      total.value = 0
    }
  } catch (error) {
    console.error('Load data error:', error)
    tableData.value = []
    total.value = 0
    ElMessage.error(t('organization.loadFailed') + ': ' + (error.message || ''))
  } finally {
    loadingStore.hideLoading()
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const handleCreate = () => {
  form.id = null
  form.name = ''
  form.description = ''
  dialogVisible.value = true
}

const handleEdit = (row) => {
  form.id = row.id
  form.name = row.name
  form.description = row.description
  
  // 转换后端返回的权限配置为前端格式
  if (row.content_permissions && Array.isArray(row.content_permissions)) {
    const permissions = { testcase: 'all', report: 'all', testplan: 'all', notification: 'all' }
    row.content_permissions.forEach(perm => {
      const [key, value] = perm.split(':')
      if (permissions.hasOwnProperty(key)) {
        permissions[key] = value
      }
    })
    form.contentPermissions = permissions
  } else {
    form.contentPermissions = { testcase: 'all', report: 'all', testplan: 'all', notification: 'all' }
  }
  
  dialogVisible.value = true
}

const handleSubmit = async () => {
  if (!form.name || !form.name.trim()) {
    ElMessage.warning(t('positionTag.inputName'))
    return
  }

  submitting.value = true
  try {
    const payload = {
      name: form.name,
      description: form.description,
      content_permissions: Object.entries(form.contentPermissions).map(([key, value]) => `${key}:${value}`),
      notification_permissions: []
    }
    if (form.id) {
      await positionTagApi.updatePositionTag(form.id, payload)
      ElMessage.success(t('positionTag.updateSuccess'))
    } else {
      await positionTagApi.createPositionTag(payload)
      ElMessage.success(t('positionTag.createSuccess'))
    }
    dialogVisible.value = false
    loadData()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('organization.operationFailed'))
  } finally {
    submitting.value = false
  }
}

const handleDialogClosed = () => {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('positionTag.deleteConfirm'), t('common.deleteConfirmTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    await positionTagApi.deletePositionTag(row.id)
    ElMessage.success(t('positionTag.deleteSuccess'))
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || t('common.failed'))
    }
  }
}

onMounted(async () => {
  loadData()
  bindTableHeight()
})
</script>
