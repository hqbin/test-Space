<template>
  <div class="field-mapping-step">
    <!-- V1.3: 表头行选择 -->
    <div class="header-row-selector" v-if="showHeaderRowSelector">
      <el-alert
        type="info"
        :closable="false"
        show-icon
        style="margin-bottom: 16px"
      >
        <template #title>
          <div class="header-row-alert">
            <span>当前表头行：第 {{ currentHeaderRow }} 行</span>
            <el-select
              v-model="currentHeaderRow"
              size="small"
              style="width: 120px; margin-left: 12px"
              @change="handleHeaderRowChange"
            >
              <el-option
                v-for="row in availableHeaderRows"
                :key="row"
                :label="`第 ${row} 行`"
                :value="row"
              />
            </el-select>
            <span class="header-tip">如果表头识别不正确，请手动选择</span>
          </div>
        </template>
      </el-alert>
    </div>

    <el-alert
      title="字段映射"
      type="warning"
      description="文件表头与模板字段不完全匹配，请确认以下映射关系"
      show-icon
      :closable="false"
      style="margin-bottom: 20px"
    />

    <el-table :data="mappingData" border>
      <el-table-column prop="fileColumn" label="文件列" width="200">
        <template #default="{ row }">
          <span>{{ row.fileColumn }}</span>
        </template>
      </el-table-column>
      <el-table-column label="" width="60" align="center">
        <template #default>
          <el-icon><Right /></el-icon>
        </template>
      </el-table-column>
      <el-table-column label="模板字段" width="250">
        <template #default="{ row }">
          <el-select
            v-model="row.templateField"
            placeholder="选择字段"
            clearable
            style="width: 100%"
          >
            <el-option
              v-for="field in availableFields(row)"
              :key="field.name"
              :label="field.name + (field.required ? ' *' : '')"
              :value="field.name"
            />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="必填" width="80" align="center">
        <template #default="{ row }">
          <el-tag v-if="isRequired(row.templateField)" type="danger" size="small">必填</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="unmapped-warning" v-if="unmappedRequired.length > 0">
      <el-alert
        title="以下必填字段未映射"
        type="error"
        :description="unmappedRequired.join(', ')"
        show-icon
        :closable="false"
      />
    </div>

    <div class="actions">
      <el-button @click="$emit('back')">返回</el-button>
      <el-button
        type="primary"
        :loading="loading"
        :disabled="unmappedRequired.length > 0"
        @click="handleConfirm"
      >
        确认映射
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Right } from '@element-plus/icons-vue'

const props = defineProps({
  headers: {
    type: Array,
    default: () => []
  },
  fieldMapping: {
    type: Object,
    default: () => ({})
  },
  templateFields: {
    type: Array,
    default: () => []
  },
  loading: Boolean,
  // V1.3: 表头行相关
  headerRow: {
    type: Number,
    default: 1
  },
  availableRows: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['confirm', 'back', 'header-row-change'])

// V1.3: 表头行选择
const currentHeaderRow = ref(props.headerRow)
const showHeaderRowSelector = computed(() => props.availableRows > 1)
const availableHeaderRows = computed(() => {
  return Array.from({ length: props.availableRows }, (_, i) => i + 1)
})

// 监听props变化
watch(() => props.headerRow, (newVal) => {
  currentHeaderRow.value = newVal
})

// V1.3: 表头行变更
const handleHeaderRowChange = (newRow) => {
  emit('header-row-change', newRow)
}

// 映射数据
const mappingData = ref([])

// 初始化映射数据
watch(() => [props.headers, props.fieldMapping], () => {
  mappingData.value = props.headers.map(header => ({
    fileColumn: header,
    templateField: props.fieldMapping[header] || null
  }))
}, { immediate: true })

// 获取可用字段（排除已选择的）
const availableFields = (currentRow) => {
  const usedFields = mappingData.value
    .filter(r => r !== currentRow && r.templateField)
    .map(r => r.templateField)
  
  return props.templateFields.filter(f => 
    !usedFields.includes(f.name) || f.name === currentRow.templateField
  )
}

// 检查字段是否必填
const isRequired = (fieldName) => {
  if (!fieldName) return false
  const field = props.templateFields.find(f => f.name === fieldName)
  return field?.required || false
}

// 未映射的必填字段
const unmappedRequired = computed(() => {
  const mappedFields = mappingData.value
    .filter(r => r.templateField)
    .map(r => r.templateField)
  
  return props.templateFields
    .filter(f => f.required && !mappedFields.includes(f.name))
    .map(f => f.name)
})

// 确认映射
const handleConfirm = () => {
  const mapping = {}
  mappingData.value.forEach(row => {
    if (row.templateField) {
      mapping[row.fileColumn] = row.templateField
    }
  })
  emit('confirm', mapping)
}
</script>

<style scoped>
.field-mapping-step {
  padding: 20px;
}

.header-row-selector {
  margin-bottom: 8px;
}

.header-row-alert {
  display: flex;
  align-items: center;
}

.header-tip {
  margin-left: 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.unmapped-warning {
  margin-top: 20px;
}

.actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: 30px;
}
</style>
