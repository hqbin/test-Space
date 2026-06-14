<template>
  <el-dialog
    v-model="visible"
    :title="$t('zmind.createIssue')"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item :label="$t('zmind.issueProject')" prop="project_id">
        <el-select
          v-model="formData.project_id"
          :placeholder="$t('zmind.selectZmindProject')"
          style="width: 100%"
        >
          <el-option
            v-for="project in zmindProjects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item :label="$t('zmind.issueTitle')" prop="title">
        <el-input
          v-model="formData.title"
          :placeholder="$t('zmind.issueTitlePlaceholder')"
        />
      </el-form-item>
      
      <el-form-item :label="$t('zmind.issueDescription')" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="6"
          :placeholder="$t('zmind.issueDescPlaceholder')"
        />
      </el-form-item>
      
      <el-form-item :label="$t('zmind.issueType')" prop="issue_type">
        <el-select v-model="formData.issue_type" style="width: 100%">
          <el-option label="Bug" value="Bug" />
          <el-option label="Feature" value="Feature" />
          <el-option label="Support" value="Support" />
        </el-select>
      </el-form-item>
      
      <el-form-item :label="$t('zmind.issuePriority')" prop="priority">
        <el-select v-model="formData.priority" style="width: 100%">
          <el-option label="High" value="High" />
          <el-option label="Medium" value="Medium" />
          <el-option label="Low" value="Low" />
        </el-select>
      </el-form-item>
      
      <el-form-item :label="$t('zmind.issueAssignee')" prop="assignee">
        <el-input
          v-model="formData.assignee"
          :placeholder="$t('zmind.issueAssigneePlaceholder')"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel') }}</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ $t('common.create') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { useZmind } from '@/composables/useZmind'
import { getZmindProjects } from '@/api/zmind'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  executionId: {
    type: Number,
    required: true
  },
  testcaseName: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const formRef = ref(null)
const zmindProjects = ref([])

const { submitting, createIssue } = useZmind()

const formData = reactive({
  project_id: '',
  title: '',
  description: '',
  issue_type: 'Bug',
  priority: 'Medium',
  assignee: ''
})

const rules = {
  project_id: [
    { required: true, message: '请选择Zmind项目', trigger: 'change' }
  ],
  issue_type: [
    { required: true, message: '请选择问题类型', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ]
}

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    loadZmindProjects()
    // 设置默认标题
    if (props.testcaseName) {
      formData.title = props.testcaseName
    }
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const loadZmindProjects = async () => {
  try {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      const user = JSON.parse(userStr)
      const res = await getZmindProjects({ apiKey: user.zmind_api_key })
      zmindProjects.value = res.data || []
    }
  } catch (error) {
    console.error('加载Zmind项目失败:', error)
  }
}

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    const result = await createIssue(props.executionId, formData)
    if (result) {
      emit('success', result)
      handleClose()
    }
  } catch (error) {
    console.error('表单验证失败:', error)
  }
}

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}
</script>
