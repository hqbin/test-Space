<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="700px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item :label="$t('execution.testCase')">
        <span>{{ testcase?.name }}</span>
      </el-form-item>
      
      <el-form-item :label="$t('execution.result')" prop="result">
        <el-radio-group v-model="formData.result">
          <el-radio value="PASS">PASS</el-radio>
          <el-radio value="FAIL">FAIL</el-radio>
          <el-radio value="NA">NA</el-radio>
          <el-radio value="NT">NT</el-radio>
          <el-radio value="BLOCK">BLOCK</el-radio>
          <el-radio :value="$t('execution.toBeConfirmed')">{{ $t('execution.toBeConfirmed') }}</el-radio>
        </el-radio-group>
      </el-form-item>
      
      <el-form-item :label="$t('execution.actualResult')" prop="actual_result">
        <el-input
          v-model="formData.actual_result"
          type="textarea"
          :rows="4"
          :placeholder="$t('execution.inputActualResult')"
        />
      </el-form-item>
      
      <el-form-item
        v-if="formData.result === 'FAIL'"
        :label="$t('execution.failureReason')"
        prop="failure_reason"
      >
        <el-input
          v-model="formData.failure_reason"
          type="textarea"
          :rows="4"
          :placeholder="$t('execution.inputFailureReason')"
        />
      </el-form-item>
      
      <el-form-item :label="$t('execution.remarks')" prop="remarks">
        <el-input
          v-model="formData.remarks"
          type="textarea"
          :rows="3"
          :placeholder="$t('execution.inputRemarks')"
        />
      </el-form-item>
      
      <el-form-item :label="$t('attachment.attachment')">
        <AttachmentUpload
          v-if="executionId"
          :execution-id="executionId"
          @success="handleAttachmentSuccess"
        />
        <el-text v-else type="info" size="small">
          {{ $t('execution.saveBeforeUpload') }}
        </el-text>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="handleClose">{{ $t('common.cancel') }}</el-button>
      <el-button
        type="primary"
        :loading="submitting"
        @click="handleSubmit"
      >
        {{ $t('common.save') }}
      </el-button>
      <el-button
        v-if="formData.result === 'FAIL' && executionId"
        type="warning"
        @click="handleCreateZmindIssue"
      >
        {{ $t('execution.createZmindIssue') }}
      </el-button>
    </template>
    
    <!-- Zmind问题单对话框 -->
    <ZmindIssueDialog
      v-model="zmindDialogVisible"
      :execution-id="executionId"
      :testcase-name="testcase?.name"
      @success="handleZmindSuccess"
    />
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import { useExecution } from '@/composables/useExecution'
import AttachmentUpload from './AttachmentUpload.vue'
import ZmindIssueDialog from './ZmindIssueDialog.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  testplanId: {
    type: Number,
    required: true
  },
  testcase: {
    type: Object,
    default: null
  },
  presetResult: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(props.modelValue)
const formRef = ref(null)
const executionId = ref(null)
const zmindDialogVisible = ref(false)

const { submitting, executeTestcase, validateExecutionData } = useExecution()

const formData = reactive({
  result: '',
  actual_result: '',
  failure_reason: '',
  remarks: ''
})

const rules = {
  result: [
    { required: true, message: t('execution.selectResult'), trigger: 'change' }
  ],
  failure_reason: [
    {
      validator: (rule, value, callback) => {
        if (formData.result === 'FAIL' && !value) {
          callback(new Error(t('execution.failureReasonRequired')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const dialogTitle = computed(() => {
  return executionId.value ? t('execution.editResult') : t('execution.executeTestCase')
})

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    if (props.presetResult) {
      formData.result = props.presetResult
    }
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
  if (!val) {
    resetForm()
  }
})

const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    const data = {
      test_plan_id: props.testplanId,
      test_case_id: props.testcase.id,
      result: formData.result,
      actual_result: formData.actual_result,
      failure_reason: formData.failure_reason,
      remarks: formData.remarks
    }
    
    if (!validateExecutionData(data)) {
      return
    }
    
    const result = await executeTestcase(data)
    if (result) {
      executionId.value = result.id
      emit('success', result)
      
      if (formData.result === 'FAIL') {
        ElMessage.success({
          message: t('execution.resultSavedCreateIssue'),
          duration: 3000
        })
      } else {
        handleClose()
      }
    }
  } catch (error) {
    console.error('Form validation failed:', error)
  }
}

const handleAttachmentSuccess = () => {
  ElMessage.success(t('attachment.uploadSuccess'))
}

const handleCreateZmindIssue = () => {
  if (!executionId.value) {
    ElMessage.warning(t('execution.saveResultFirst'))
    return
  }
  zmindDialogVisible.value = true
}

const handleZmindSuccess = (result) => {
  ElMessage.success(t('execution.zmindIssueCreated'))
  handleClose()
}

const resetForm = () => {
  formRef.value?.resetFields()
  executionId.value = null
  formData.result = ''
  formData.actual_result = ''
  formData.failure_reason = ''
  formData.remarks = ''
}

const handleClose = () => {
  visible.value = false
}
</script>

<style scoped>
.el-form-item {
  margin-bottom: 20px;
}
</style>
