<template>
  <div class="execution-detail-container">
    <!-- 头部 -->
    <div class="detail-header">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ $t('common.back') }}
      </el-button>
      <h2 style="margin: 0 0 0 20px;">{{ planDetail.name }} - {{ $t('execution.title') }}</h2>
    </div>

    <!-- 主内容区域：左侧用例列表 + 右侧用例详情 -->
    <div class="detail-content">
      <!-- 统计卡片 - 横向显示在顶部 -->
      <div class="stats-section-top">
        <div class="stats-cards-horizontal">
          <div class="automation-filter-wrapper">
            <el-select
              v-model="automationFilter"
              @change="handleAutomationFilterChange"
              class="automation-select"
            >
              <el-option :label="$t('execution.automationAll')" value="" />
              <el-option :label="$t('execution.automationManual')" value="manual" />
              <el-option :label="$t('execution.automationAuto')" value="auto" />
            </el-select>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === null }"
            @click="filterByStatus(null)"
          >
            <span class="stat-label-small">{{ $t('execution.totalCases') }}</span>
            <span class="stat-value-small">{{ statistics.total }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'PENDING' }"
            @click="filterByStatus('PENDING')"
          >
            <span class="stat-label-small">{{ $t('execution.notExecuted') }}</span>
            <span class="stat-value-small" style="color: #909399;">{{ statistics.pending }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'EXECUTED' }"
            @click="filterByStatus('EXECUTED')"
          >
            <span class="stat-label-small">{{ $t('execution.executed') }}</span>
            <span class="stat-value-small" style="color: #409eff;">{{ statistics.executed }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'PASS' }"
            @click="filterByStatus('PASS')"
          >
            <span class="stat-label-small">PASS</span>
            <span class="stat-value-small" style="color: #67c23a;">{{ statistics.passed }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'FAIL' }"
            @click="filterByStatus('FAIL')"
          >
            <span class="stat-label-small">FAIL</span>
            <span class="stat-value-small" style="color: #f56c6c;">{{ statistics.failed }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'BLOCK' }"
            @click="filterByStatus('BLOCK')"
          >
            <span class="stat-label-small">BLOCK</span>
            <span class="stat-value-small" style="color: #e6a23c;">{{ statistics.blocked }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'NA' }"
            @click="filterByStatus('NA')"
          >
            <span class="stat-label-small">NA</span>
            <span class="stat-value-small" style="color: #909399;">{{ statistics.na }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'NT' }"
            @click="filterByStatus('NT')"
          >
            <span class="stat-label-small">NT</span>
            <span class="stat-value-small" style="color: #909399;">{{ statistics.nt }}</span>
          </div>
          <div 
            class="stat-card-small"
            :class="{ 'active': statusFilter === 'ONGOING' }"
            @click="filterByStatus('ONGOING')"
          >
            <span class="stat-label-small">Ongoing</span>
            <span class="stat-value-small" style="color: #1a73e8;">{{ statistics.ongoing }}</span>
          </div>

        </div>
      </div>

      <!-- 内容区域包装器 -->
      <div class="content-wrapper">
        <!-- 左侧：模块选择和用例列表 -->
        <div class="left-sidebar">
        <!-- 模块选择下拉框 -->
        <div class="module-selector">
          <el-tree-select
            v-model="selectedModule"
            :data="moduleTreeOptions"
            :placeholder="$t('execution.selectModule')"
            @change="handleModuleChange"
            style="width: 100%;"
            :render-after-expand="false"
            check-strictly
            :default-expand-all="false"
          />
        </div>

        <!-- 用例列表 -->
        <div class="testcase-list" @scroll="handleTestcaseListScroll" ref="testcaseListRef">
          <div
            v-for="testcase in visibleTestcases"
            :key="testcase.id"
            class="testcase-item"
            :class="{ active: currentTestcaseId === testcase.id }"
            @click="selectTestcase(testcase.id)"
          >
            <div class="testcase-title">{{ testcase.name }}</div>
            <div class="testcase-meta">
              <el-tag 
                v-if="testcase.execution_status === 'PENDING'" 
                type="info" 
                size="small"
              >
                {{ $t('execution.statusPending') }}
              </el-tag>
              <el-tag 
                v-else-if="testcase.execution_status === 'PASS'" 
                type="success" 
                size="small"
              >
                PASS
              </el-tag>
              <el-tag 
                v-else-if="testcase.execution_status === 'FAIL'" 
                type="danger" 
                size="small"
              >
                FAIL
              </el-tag>
              <el-tag 
                v-else-if="testcase.execution_status === 'BLOCK'" 
                type="warning" 
                size="small"
              >
                BLOCK
              </el-tag>
              <el-tag 
                v-else-if="testcase.execution_status === 'NA'" 
                type="info" 
                size="small"
              >
                NA
              </el-tag>
              <el-tag 
                v-else-if="testcase.execution_status === 'NT'" 
                type="info" 
                size="small"
              >
                NT
              </el-tag>
              <el-tag 
                v-else-if="testcase.execution_status === 'ONGOING'" 
                size="small"
                style="background-color: #e8f0fe; color: #1a73e8; border-color: #c6dafc;"
              >
                Ongoing
              </el-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：用例详情和执行 -->
      <div class="right-content" v-if="currentTestcaseId">
        <div class="content-scroll">
          <!-- 加载状态 -->
          <div v-if="!testcaseDetail.id" class="loading-state">
            <el-skeleton :rows="10" animated />
          </div>
          
          <!-- 标签页 -->
          <div v-if="testcaseDetail.id" class="detail-tabs-wrapper">
            <div class="detail-tabs-actions">
              <el-input
                v-model="caseSearchKeyword"
                placeholder="搜索用例编号或关键字（含执行备注）"
                clearable
                class="detail-search-input"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button
                type="warning"
                @click="feedbackDialogVisible = true"
              >
                {{ $t('execution.caseFeedback') }}
              </el-button>
            </div>
          <el-tabs v-model="activeTab" class="detail-tabs" v-if="testcaseDetail.id">
            <!-- 用例信息标签页 -->
            <el-tab-pane :label="$t('execution.caseInfo')" name="info">
              <el-card shadow="never" class="info-card">
                <template #header>
                  <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 600; font-size: 16px;">{{ $t('execution.caseInfo') }}</span>
                  </div>
                </template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item :label="$t('execution.caseNumber')">{{ testcaseDetail.case_number }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.caseTitle')">{{ testcaseDetail.name }}</el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.belongModule')">
                    {{ testcaseDetail.module }}{{ testcaseDetail.sub_module ? ' / ' + testcaseDetail.sub_module : '' }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('testcase.level')">
                    <el-tag :type="getLevelType(testcaseDetail.level)">{{ testcaseDetail.level }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.precondition')">
                    {{ testcaseDetail.precondition || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.testSteps')">
                    <div v-for="(step, index) in parseSteps(testcaseDetail.steps)" :key="index" style="margin-bottom: 8px; white-space: pre-line;">
                      <span style="color: #8b9aee; font-weight: 500;">{{ index + 1 }}.</span> {{ step }}
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.expectedResult')">
                    <div v-for="(result, index) in parseExpected(testcaseDetail.expected_result)" :key="index" style="margin-bottom: 8px; white-space: pre-line;">
                      <span style="color: #8b9aee; font-weight: 500;">{{ index + 1 }}.</span> {{ result }}
                    </div>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.caseRemarks')">
                    {{ testcaseDetail.remarks || '-' }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.linkedPR')">
                    <div v-if="zmindLinks && zmindLinks.length > 0">
                      <span 
                        v-for="(link, index) in zmindLinks" 
                        :key="link.id"
                        style="margin-right: 12px;"
                      >
                        <a 
                          :href="`https://zmind.whaletv.com/issues/${link.zmind_issue_id}`" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          style="color: #409EFF; text-decoration: underline;"
                        >
                          {{ link.zmind_issue_id }}
                        </a>
                        <el-tag 
                          v-if="link.test_plan_id === parseInt(planId)" 
                          type="success" 
                          size="small"
                          style="margin-left: 4px;"
                        >
                          {{ $t('testcase.currentPlan') }}
                        </el-tag>
                        <span v-if="index < zmindLinks.length - 1">,</span>
                      </span>
                    </div>
                    <span v-else>-</span>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('execution.attachment')">
                    <div v-loading="caseAttachmentsLoading" style="min-height: 24px;">
                      <span v-if="!caseAttachmentsLoading && caseAttachments.length === 0" style="color: #909399;">-</span>
                      <div v-else class="inline-attachments">
                        <div 
                          v-for="att in caseAttachments" 
                          :key="att.id" 
                          class="inline-attachment-item"
                        >
                          <el-icon :size="16" :color="getFileIconColor(att.file_name)" style="flex-shrink: 0;">
                            <Document />
                          </el-icon>
                          <span class="inline-att-name" :title="att.file_name">{{ att.file_name }}</span>
                          <span class="inline-att-size">{{ formatFileSize(att.file_size) }}</span>
                          <el-button 
                            v-if="isPreviewable(att.file_name)"
                            type="primary" 
                            size="small" 
                            link
                            @click="handlePreviewCaseAttachment(att)"
                          >
                            {{ $t('execution.preview') }}
                          </el-button>
                          <el-button 
                            type="primary" 
                            size="small" 
                            link
                            @click="handleDownloadCaseAttachment(att)"
                          >
                            {{ $t('execution.download') }}
                          </el-button>
                        </div>
                      </div>
                    </div>
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <!-- 执行表单 -->
              <el-card shadow="never" class="execution-card">
                <template #header>
                  <span style="font-weight: 600; font-size: 16px;">{{ $t('execution.executeTest') }}</span>
                </template>
                <el-form :model="executionForm" label-width="100px">
                  <el-form-item :label="$t('execution.executeResult')" required>
                    <el-radio-group v-model="executionForm.result">
                      <el-radio value="PASS">
                        <el-tag type="success">PASS</el-tag>
                      </el-radio>
                      <el-radio value="FAIL">
                        <el-tag type="danger">FAIL</el-tag>
                      </el-radio>
                      <el-radio value="BLOCK">
                        <el-tag type="warning">BLOCK</el-tag>
                      </el-radio>
                      <el-radio value="NA">
                        <el-tag type="info">NA</el-tag>
                      </el-radio>
                      <el-radio value="NT">
                        <el-tag type="info">NT</el-tag>
                      </el-radio>
                      <el-radio value="ONGOING">
                        <el-tag style="background-color: #e8f0fe; color: #1a73e8; border-color: #c6dafc;">Ongoing</el-tag>
                      </el-radio>
                    </el-radio-group>
                  </el-form-item>
                  <div style="display: flex; gap: 16px;">
                    <el-form-item :label="$t('execution.executeRemark')" style="flex: 1;">
                      <el-input
                        v-model="executionForm.remark"
                        type="textarea"
                        :rows="4"
                        :placeholder="$t('execution.inputRemark')"
                      />
                    </el-form-item>
                    <el-form-item :label="$t('execution.versionInfo')" style="flex: 1;">
                      <el-input
                        v-model="executionForm.version_info"
                        type="textarea"
                        :rows="4"
                        :placeholder="$t('execution.inputVersionInfo')"
                      />
                    </el-form-item>
                  </div>
                  <el-form-item>
                    <el-button type="primary" @click="submitExecution" :loading="submitting">
                      {{ $t('execution.submitResult') }}
                    </el-button>
                    <el-button 
                      @click="goToPrevious" 
                      :disabled="!hasPrevious"
                      style="margin-left: 12px;"
                    >
                      <el-icon><ArrowLeft /></el-icon>
                      {{ $t('execution.previousCase') }}
                    </el-button>
                    <el-button 
                      @click="goToNext" 
                      :disabled="!hasNext"
                    >
                      {{ $t('execution.nextCase') }}
                      <el-icon><ArrowRight /></el-icon>
                    </el-button>
                    <el-button 
                      type="warning" 
                      @click="openPRDialog"
                      style="margin-left: 12px;"
                    >
                      {{ $t('execution.submitPR') }}
                    </el-button>
                  </el-form-item>
                </el-form>
              </el-card>
            </el-tab-pane>

            <!-- 执行历史标签页 -->
            <el-tab-pane :label="$t('execution.executionHistory')" name="history">
              <el-card shadow="never" class="history-card">
                <template #header>
                  <span style="font-weight: 600; font-size: 16px;">{{ $t('execution.executionHistory') }}</span>
                </template>
                <el-timeline>
                  <el-timeline-item
                    v-for="item in executionHistory"
                    :key="item.id"
                    :timestamp="formatDateTime(item.executed_at)"
                    placement="top"
                  >
                    <el-card>
                      <!-- FAIL和BLOCK显示完整信息 -->
                      <template v-if="item.result === 'FAIL' || item.result === 'BLOCK'">
                        <div style="margin-bottom: 12px;">
                          <el-tag v-if="item.result === 'FAIL'" type="danger" size="large">FAIL</el-tag>
                          <el-tag v-else-if="item.result === 'BLOCK'" type="warning" size="large">BLOCK</el-tag>
                        </div>
                        
                        <el-descriptions :column="1" border size="small">
                          <el-descriptions-item :label="$t('executionDetail.testPlanLabel')">{{ item.test_plan_name || $t('execution.unknownPlan') }}</el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.caseNumberLabel')">{{ item.testcase_number || '-' }}</el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.caseTitleLabel')">{{ item.testcase_name || '-' }}</el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.moduleLabelLabel')">
                            {{ item.testcase_module || '-' }}{{ item.testcase_sub_module ? ' / ' + item.testcase_sub_module : '' }}
                          </el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.caseLevelLabel')">
                            <el-tag v-if="item.testcase_level" :type="getLevelType(item.testcase_level)" size="small">{{ item.testcase_level }}</el-tag>
                            <span v-else>-</span>
                          </el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.executorLabel')">{{ item.executor_name || $t('execution.unknownPlan') }}</el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.executionTimeLabel')">{{ formatDateTime(item.executed_at) }}</el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.linkedPRLabel')">
                            <div v-if="item.pr_links_snapshot && item.pr_links_snapshot.length > 0">
                              <span 
                                v-for="(link, index) in item.pr_links_snapshot" 
                                :key="index"
                                style="margin-right: 12px;"
                              >
                                <a 
                                  :href="`https://zmind.whaletv.com/issues/${link.zmind_issue_id}`" 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  style="color: #409EFF; text-decoration: underline;"
                                >
                                  {{ link.zmind_issue_id }}
                                </a>
                                <el-tag 
                                  v-if="link.test_plan_id === parseInt(planId)" 
                                  type="success" 
                                  size="small"
                                  style="margin-left: 4px;"
                                >
                                  {{ $t('testcase.currentPlan') }}
                                </el-tag>
                                <span v-if="index < item.pr_links_snapshot.length - 1">,</span>
                              </span>
                            </div>
                            <span v-else>-</span>
                          </el-descriptions-item>
                          <el-descriptions-item :label="$t('executionDetail.remarkLabelLabel')">
                            <div style="white-space: pre-wrap; color: #606266;" v-html="renderRemarkWithPR(item.remarks) || '-'"></div>
                          </el-descriptions-item>
                          <el-descriptions-item :label="$t('execution.versionInfo')">
                            {{ item.version_info || '-' }}
                          </el-descriptions-item>
                        </el-descriptions>
                      </template>
                      
                      <!-- 其他结果显示简化信息 -->
                      <template v-else>
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                          <div>
                            <el-tag v-if="item.result === 'PASS'" type="success">PASS</el-tag>
                            <el-tag v-else-if="item.result === 'NA'" type="info">NA</el-tag>
                            <el-tag v-else-if="item.result === 'NT'" type="info">NT</el-tag>
                          </div>
                          <span style="color: #909399; font-size: 14px;">{{ $t('executionDetail.executorLabel') }}：{{ item.executor_name || $t('execution.unknownPlan') }}</span>
                        </div>
                        <div style="color: #606266; margin-bottom: 8px;">
                          {{ $t('executionDetail.testPlanLabel') }}：{{ item.test_plan_name || $t('execution.unknownPlan') }}
                        </div>
                        <div v-if="item.remarks" style="color: #606266; white-space: pre-wrap;" v-html="$t('execution.remarkLabel') + '：' + renderRemarkWithPR(item.remarks)">
                        </div>
                        <div style="color: #909399; font-size: 13px; margin-top: 4px;">
                          {{ $t('execution.versionInfo') }}：{{ item.version_info || '-' }}
                        </div>
                      </template>
                    </el-card>
                  </el-timeline-item>
                </el-timeline>
              </el-card>
            </el-tab-pane>
          </el-tabs>
          </div>
        </div>
      </div>

      <!-- 右侧空状态 -->
      <div class="right-content empty-state" v-else>
        <el-empty :description="$t('testcase.selectCaseFromLeft')" />
      </div>
      </div><!-- 关闭 content-wrapper -->
    </div><!-- 关闭 detail-content -->

    <!-- 附件预览对话框 -->
    <el-dialog
      v-model="casePreviewDialogVisible"
      :title="casePreviewFileName"
      width="80%"
      top="5vh"
      append-to-body
      destroy-on-close
    >
      <div class="preview-container">
        <img 
          v-if="casePreviewType === 'image'" 
          :src="casePreviewUrl" 
          style="max-width: 100%; max-height: 70vh; display: block; margin: 0 auto;"
          :alt="casePreviewFileName"
        />
        <iframe 
          v-else-if="casePreviewType === 'pdf'" 
          :src="casePreviewUrl" 
          style="width: 100%; height: 70vh; border: none;"
        />
        <div v-else-if="casePreviewType === 'text'" style="max-height: 70vh; overflow: auto;">
          <pre style="white-space: pre-wrap; word-break: break-all; padding: 16px; background: #f5f7fa; border-radius: 4px; font-size: 13px;">{{ casePreviewTextContent }}</pre>
        </div>
        <div v-else style="text-align: center; padding: 40px; color: #909399;">
          {{ $t('execution.previewNotSupported') }}
        </div>
      </div>
    </el-dialog>

    <!-- Zmind项目选择对话框 -->
    <el-dialog
      v-model="projectDialogVisible"
      :title="$t('execution.selectZmindProject')"
      width="600px"
      :close-on-click-modal="false"
      append-to-body
    >
      <div v-loading="projectLoading">
        <!-- 显示当前选择的项目 -->
        <el-alert
          v-if="selectedZmindProject && selectedZmindProjectName"
          :title="`${$t('execution.currentSelection')}: ${selectedZmindProjectName}`"
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        />
        
        <el-form label-width="100px">
          <el-form-item :label="$t('execution.zmindProject')" required>
            <el-select 
              v-model="selectedZmindProject" 
              :placeholder="$t('execution.selectProject')" 
              style="width: 100%;"
              filterable
              :filter-method="filterZmindProjects"
              popper-class="zmind-project-dropdown"
            >
              <el-option
                v-for="project in filteredZmindProjects"
                :key="project.id"
                :label="project.name"
                :value="project.id"
              />
            </el-select>
          </el-form-item>
        </el-form>
        <div style="color: #909399; font-size: 14px; margin-top: 10px;">
          {{ $t('execution.projectSelectTip') }}
        </div>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="projectDialogVisible = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="confirmProjectSelection">
            {{ $t('common.confirm') }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- PR提交对话框 -->
    <el-dialog
      v-model="prDialogVisible"
      :title="$t('execution.submitToZmind')"
      width="1200px"
      :close-on-click-modal="false"
      append-to-body
      @opened="initDialogDragDrop"
      @closed="cleanupDialogDragDrop"
    >
      <el-form 
        :model="prForm" 
        label-width="120px" 
        v-loading="prFormLoading"
        ref="prFormRef"
        @drop.prevent="handleDialogDrop"
        @dragover.prevent="handleDialogDragOver"
        @dragenter.prevent="handleDialogDragEnter"
        @dragleave.prevent="handleDialogDragLeave"
        :class="{ 'drag-over': isDraggingOverDialog }"
        :data-drop-text="$t('executionDetail.dropFilesToUpload')"
      >
        <!-- 显示当前选择的项目 -->
        <el-form-item :label="$t('execution.currentProject')">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="flex: 1; color: #606266;">{{ selectedZmindProjectName }}</span>
            <el-button type="primary" @click="reSelectProject">
              {{ $t('execution.reSelectProject') }}
            </el-button>
          </div>
        </el-form-item>
        
        <el-form-item :label="$t('execution.prTitle')" required>
          <el-input
            v-model="prForm.subject"
            :placeholder="$t('execution.inputPrTitle')"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>
        
        <el-form-item :label="$t('execution.prDescription')" required>
          <el-input
            v-model="prForm.description"
            type="textarea"
            :rows="18"
            :placeholder="$t('execution.inputPrDescription')"
          />
        </el-form-item>
        
        <!-- 两列布局 -->
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('execution.prPriority')" required>
              <el-select v-model="prForm.priority_id" :placeholder="$t('execution.selectPriority')" style="width: 100%;">
                <el-option
                  v-for="item in priorities"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item :label="$t('execution.assignTo')">
              <el-select v-model="prForm.assigned_to_id" :placeholder="$t('execution.selectAssignee')" style="width: 100%;" clearable filterable :filter-method="filterMembers">
                <el-option
                  v-for="item in filteredMembers"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('execution.category')" :required="isFieldRequired('Category')">
              <el-select v-model="prForm.category_id" :placeholder="$t('execution.selectCategory')" style="width: 100%;" clearable filterable :filter-method="filterCategories">
                <el-option
                  v-for="item in filteredCategories"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item :label="$t('execution.targetVersion')" :required="isFieldRequired('Fixed Version')">
              <el-select v-model="prForm.fixed_version_id" :placeholder="$t('execution.selectVersion')" style="width: 100%;" clearable filterable>
                <el-option
                  v-for="item in versions"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('execution.severity')" :required="isFieldRequired('Severity')">
              <el-select v-model="prForm.severity" :placeholder="$t('execution.selectSeverity')" style="width: 100%;">
                <el-option
                  v-for="item in severities"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item label="Phase" :required="isFieldRequired('Phase')">
              <el-select v-model="prForm.phase" :placeholder="$t('execution.selectPhase')" style="width: 100%;" clearable>
                <el-option
                  v-for="item in phases"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Side Effect" :required="isFieldRequired('Side Effect')">
              <el-select v-model="prForm.side_effect" :placeholder="$t('execution.selectSideEffect')" style="width: 100%;">
                <el-option
                  v-for="item in sideEffects"
                  :key="item.id"
                  :label="item.name"
                  :value="item.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="12">
            <el-form-item :label="$t('execution.planCompletionDate')">
              <el-date-picker
                v-model="prForm.due_date"
                type="date"
                :placeholder="$t('execution.selectDate')"
                format="YYYY/MM/DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="Issue Version" :required="isFieldRequired('Issue Version')">
              <el-input
                v-model="prForm.issue_version"
                :placeholder="$t('execution.inputIssueVersion')"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="TeVaMat ID">
              <el-input
                v-model="prForm.tevama_id"
                placeholder="TeVaMat ID"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item :label="$t('execution.attachment')">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            :file-list="fileList"
            :show-file-list="true"
            multiple
            action="#"
            :limit="10"
            :on-exceed="handleExceed"
            :disabled="fileLoading"
          >
            <el-button type="primary" :loading="fileLoading">
              {{ fileLoading ? $t('execution.processing') : $t('execution.selectFile') }}
            </el-button>
            <template #tip>
              <div style="color: #909399; font-size: 12px; margin-top: 8px;">
                {{ $t('execution.maxFileSize') }}
              </div>
            </template>
          </el-upload>
          
          <!-- 上传进度 -->
          <div v-if="uploadProgress.show" style="margin-top: 12px;">
            <el-progress 
              :percentage="uploadProgress.percent" 
              :status="uploadProgress.status"
            >
              <template #default="{ percentage }">
                <span style="font-size: 12px;">{{ uploadProgress.text }} {{ percentage }}%</span>
              </template>
            </el-progress>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="prDialogVisible = false">{{ $t('common.cancel') }}</el-button>
          <el-button type="primary" @click="submitPR" :loading="prSubmitting">
            {{ $t('common.submit') }}
          </el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 连接Zmind蒙版（支持取消） -->
    <Teleport to="body">
      <div v-if="zmindConnecting" class="zmind-connecting-overlay">
        <div class="zmind-connecting-box">
          <el-icon class="zmind-connecting-spinner"><Loading /></el-icon>
          <p class="zmind-connecting-text">{{ $t('executionDetail.connectingZmind') }}</p>
          <button class="zmind-cancel-btn" @click="cancelZmindConnect">
            {{ $t('executionDetail.cancelConnect') }}
          </button>
        </div>
      </div>
    </Teleport>

    <!-- 用例问题反馈对话框 -->
    <el-dialog
      v-model="feedbackDialogVisible"
      :title="$t('execution.caseFeedback')"
      width="500px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form>
        <el-form-item required>
          <el-input
            v-model="feedbackContent"
            type="textarea"
            :rows="6"
            :placeholder="$t('execution.feedbackPlaceholder')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="feedbackDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="submitFeedback" :loading="feedbackSubmitting">
          {{ $t('common.submit') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行冲突确认对话框 -->
    <el-dialog
      v-model="conflictDialogVisible"
      :title="$t('execution.conflictTitle')"
      width="450px"
      :close-on-click-modal="false"
      append-to-body
    >
      <div class="conflict-info">
        <p>{{ $t('execution.conflictMessage') }}</p>
        <el-descriptions :column="1" border style="margin-top: 16px;">
          <el-descriptions-item :label="$t('execution.executor')">
            {{ conflictData.executor }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('execution.executedAt')">
            {{ conflictData.executed_at }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('execution.result')">
            {{ conflictData.result }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('execution.remarks')" v-if="conflictData.remarks">
            {{ conflictData.remarks }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
      <template #footer>
        <el-button @click="conflictDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="warning" @click="handleConflictConfirm" :loading="submitting">
          {{ $t('execution.forceSubmit') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, ArrowRight, Search, Loading } from '@element-plus/icons-vue'
import { getTestCaseDetail, submitTestCaseFeedback } from '@/api/testcase'
import { createExecution, getExecutions, getLatestExecutionRemark, getLatestVersionInfo } from '@/api/execution'
import { getTestPlanDetail } from '@/api/testplan'
import { getPriorities, getSeverities, getVersions, createZmindIssue, getZmindProjects, getTestPlanZmindProject, updateTestPlanZmindProject, getProjectFields, getPhases, getSideEffects, getProjectRequiredFields, clearZmindProjectCache, isZmindPRCacheReady } from '@/api/zmind'
import { getAttachments, downloadAttachment, getAttachmentPreviewUrl } from '@/api/testcaseAttachment'
import { Document } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { renderRemarkWithPR } from '@/composables/useRemarkPR'

const { t } = useI18n()
const router = useRouter()
const route = useRoute()

const planId = route.params.planId
// 确保 testcaseId 是数字类型
const currentTestcaseId = ref(parseInt(route.params.testcaseId))

const planDetail = ref({})
const testcaseDetail = ref({ id: null })
const executionHistory = ref([])
const zmindLinks = ref([])
const submitting = ref(false)

// 左侧用例列表虚拟滚动
const testcaseListRef = ref(null)
const visibleCount = ref(100)  // 初始显示100条

// 可见用例列表（截取前N条，滚动到底部时加载更多）
const visibleTestcases = computed(() => {
  return filteredTestcases.value.slice(0, visibleCount.value)
})

// 滚动加载更多
const handleTestcaseListScroll = (e) => {
  const el = e.target
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
    if (visibleCount.value < filteredTestcases.value.length) {
      visibleCount.value = Math.min(visibleCount.value + 100, filteredTestcases.value.length)
    }
  }
}

// 用例附件相关
const caseAttachments = ref([])
const caseAttachmentsLoading = ref(false)
// 附件预览相关
const casePreviewDialogVisible = ref(false)
const casePreviewUrl = ref('')
const casePreviewFileName = ref('')
const casePreviewType = ref('')  // 'image' | 'pdf' | 'text' | 'other'
const casePreviewTextContent = ref('')

// 标签页
const activeTab = ref('info')

// 用例问题反馈
const feedbackDialogVisible = ref(false)
const feedbackContent = ref('')
const feedbackSubmitting = ref(false)

// 执行冲突检测
const conflictDialogVisible = ref(false)
const conflictData = ref({
  executor: '',
  executed_at: '',
  result: '',
  remarks: ''
})

const showConflictDialog = (data) => {
  conflictData.value = data
  conflictDialogVisible.value = true
}

const handleConflictConfirm = async () => {
  conflictDialogVisible.value = false
  submitting.value = true
  try {
    const res = await createExecution({
      test_plan_id: planId,
      test_case_id: currentTestcaseId.value,
      result: executionForm.result,
      remarks: executionForm.remark,
      version_info: executionForm.version_info,
      force: true
    })

    if (res.code === 409) {
      ElMessage.warning('该用例已被其他人再次执行，无法覆盖')
      submitting.value = false
      return
    }

    ElMessage.success(t('executionDetail.submitSuccess'))

    const currentIdx = filteredTestcases.value.findIndex(tc => tc.id === currentTestcaseId.value)
    const nextTestcaseId = (currentIdx >= 0 && currentIdx < filteredTestcases.value.length - 1)
      ? filteredTestcases.value[currentIdx + 1].id
      : null

    const currentTc = allTestcases.value.find(tc => tc.id === currentTestcaseId.value)
    if (currentTc) {
      currentTc.execution_status = executionForm.result
    }

    resetForm()

    if (nextTestcaseId) {
      await selectTestcase(nextTestcaseId)
    } else {
      loadExecutionHistory(currentTestcaseId.value)
    }
  } catch (error) {
    ElMessage.error(t('executionDetail.submitFailed'))
  } finally {
    submitting.value = false
  }
}

const submitFeedback = async () => {
  if (!feedbackContent.value.trim()) {
    ElMessage.warning(t('execution.feedbackRequired'))
    return
  }
  feedbackSubmitting.value = true
  try {
    await submitTestCaseFeedback(currentTestcaseId.value, { content: feedbackContent.value.trim() })
    ElMessage.success(t('execution.feedbackSuccess'))
    feedbackDialogVisible.value = false
    feedbackContent.value = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('common.failed'))
  } finally {
    feedbackSubmitting.value = false
  }
}

// 模块和用例列表
// 从URL参数中读取筛选状态，兼容 module 和 subModule 的格式
const getInitialModule = () => {
  const module = route.query.module || ''
  const subModule = route.query.subModule || ''
  if (module && subModule) {
    return `path:${module}/${subModule}`
  }
  // 如果 module 包含 /，说明是子模块路径，添加 path: 前缀
  if (module.includes('/')) {
    return `path:${module}`
  }
  return module
}
const selectedModule = ref(getInitialModule())
const allTestcases = ref([])
const statusFilter = ref(route.query.statusFilter || null)
const automationFilter = ref(route.query.automationFilter || '')
const caseSearchKeyword = ref('')

// 统计数据 - 根据当前筛选条件计算
const statistics = computed(() => {
  // 获取当前模块筛选后的用例
  let testcases = allTestcases.value
  
  // 根据自动化类型筛选
  if (automationFilter.value === 'auto') {
    testcases = testcases.filter(tc => tc.automation?.toUpperCase() === 'Y')
  } else if (automationFilter.value === 'manual') {
    testcases = testcases.filter(tc => tc.automation?.toUpperCase() !== 'Y')
  }
  
  if (selectedModule.value) {
    if (selectedModule.value.startsWith('path:')) {
      // 选择了子模块，格式为 "path:完整路径"
      const fullPath = selectedModule.value.substring(5)
      testcases = testcases.filter(tc => {
        const modulePath = tc.module || '未分类'
        return modulePath === fullPath || modulePath.startsWith(fullPath + '/')
      })
    } else {
      // 只选了主模块：匹配该主模块及其所有子模块
      testcases = testcases.filter(tc => {
        const modulePath = tc.module || '未分类'
        const mainModule = modulePath.split('/')[0].trim()
        return mainModule === selectedModule.value
      })
    }
  }
  
  // 统计各种状态
  let executed = 0
  let passed = 0
  let failed = 0
  let blocked = 0
  let na = 0
  let nt = 0
  let assist = 0
  let ongoing = 0
  
  testcases.forEach(tc => {
    if (tc.execution_status === 'ONGOING') {
      ongoing++
    } else if (tc.execution_status && tc.execution_status !== 'PENDING' && tc.execution_status !== 'ONGOING') {
      executed++
      if (tc.execution_status === 'PASS') passed++
      else if (tc.execution_status === 'FAIL') failed++
      else if (tc.execution_status === 'BLOCK') blocked++
      else if (tc.execution_status === 'NA') na++
      else if (tc.execution_status === 'NT') nt++
      else if ((tc.execution_status || '').trim() === '协测') assist++
    }
  })
  
  const pending = ongoing + (testcases.length - executed - ongoing)
  
  return { total: testcases.length, executed, passed, failed, blocked, na, nt, assist, ongoing, pending }
})

// 从测试计划用例中动态提取模块树（支持任意深度）
const moduleTreeOptions = computed(() => {
  const options = [{ value: '', label: t('executionDetail.allModules'), children: [] }]
  
  // 构建多级树
  const root = { children: new Map() }
  allTestcases.value.forEach(tc => {
    const raw = tc.module || '未分类'
    const parts = raw.split('/').map(p => p.trim()).filter(Boolean)
    if (parts.length === 0) parts.push('未分类')
    
    let current = root
    let pathSoFar = ''
    for (const part of parts) {
      pathSoFar = pathSoFar ? pathSoFar + '/' + part : part
      if (!current.children.has(part)) {
        current.children.set(part, { name: part, path: pathSoFar, children: new Map() })
      }
      current = current.children.get(part)
    }
  })
  
  // 递归转换为 el-cascader 格式
  // 主模块 value = 模块名（选中时匹配主模块及所有子模块）
  // 子模块 value = "path:完整路径"（选中时精确匹配）
  const toOptions = (map, isRoot) => {
    return Array.from(map.values())
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
      .map(node => {
        const opt = {
          value: isRoot ? node.name : `path:${node.path}`,
          label: node.name,
          children: node.children.size > 0 ? toOptions(node.children, false) : []
        }
        return opt
      })
  }
  
  options.push(...toOptions(root.children, true))
  return options
})

const executionForm = reactive({
  result: 'PASS',
  remark: '',
  version_info: ''
})

// Zmind项目选择对话框
const projectDialogVisible = ref(false)
const projectLoading = ref(false)
const selectedZmindProject = ref('')
const selectedZmindProjectName = ref('') // 保存项目名称用于显示
const zmindProjects = ref([])
const filteredZmindProjects = ref([])
// 内存缓存：当前页面生命周期内只请求一次 testplan zmind-project
const cachedZmindProjectId = ref(null) // null=未查询, ''=查询过但未绑定, 其他=已绑定的项目ID

// 自定义搜索：去掉全角空格缩进后匹配
const filterZmindProjects = (query) => {
  if (!query) {
    filteredZmindProjects.value = zmindProjects.value
  } else {
    const keyword = query.toLowerCase()
    filteredZmindProjects.value = zmindProjects.value.filter(p => 
      p.name.replace(/\u3000/g, '').toLowerCase().includes(keyword)
    )
  }
}

// PR提交对话框
const prDialogVisible = ref(false)
const prFormLoading = ref(false)
const prSubmitting = ref(false)
const zmindConnecting = ref(false)          // 控制连接Zmind蒙版
const zmindConnectController = ref(null)    // 用于取消连接Zmind的请求
const prForm = reactive({
  subject: '',
  description: '',
  tracker_id: 1,  // 固定为PR类型
  priority_id: 2,
  severity: 'Minor',
  issue_version: '',  // 手动输入
  tevama_id: '',  // TeVaMat ID（自动填入用例编号）
  project_id: '',
  assigned_to_id: null,  // 指派人
  category_id: null,  // 类别
  fixed_version_id: null,  // 目标版本
  phase: null,  // Phase
  side_effect: 'NO',  // Side Effect（字段ID: 5）
  due_date: null  // 计划完成日期
})

// PR选项数据
const priorities = ref([])
const severities = ref([])
const members = ref([])  // 项目成员
const categories = ref([])  // 项目类别
const versions = ref([])  // 项目版本
const phases = ref([])  // Phase选项
const sideEffects = ref([])  // Side Effect选项
const requiredFields = ref([])  // 必填字段列表

// 指派人和类别的模糊搜索
const memberFilterQuery = ref('')
const categoryFilterQuery = ref('')
const filteredMembers = computed(() => {
  if (!memberFilterQuery.value) return members.value
  const q = memberFilterQuery.value.toLowerCase()
  return members.value.filter(m => m.name.toLowerCase().includes(q))
})
const filteredCategories = computed(() => {
  if (!categoryFilterQuery.value) return categories.value
  const q = categoryFilterQuery.value.toLowerCase()
  return categories.value.filter(c => c.name.toLowerCase().includes(q))
})
function filterMembers(query) {
  memberFilterQuery.value = query
}
function filterCategories(query) {
  categoryFilterQuery.value = query
}

// 文件上传
const uploadRef = ref(null)
const fileList = ref([])
const fileLoading = ref(false)  // 文件选择加载状态
const uploadProgress = ref({
  show: false,
  percent: 0,
  text: '',
  status: ''
})

// 处理文件变化
const handleFileChange = (file, files) => {
  console.log('File selected:', file.name)
  
  // 显示加载状态
  fileLoading.value = true
  
  // 模拟文件处理延迟，给用户视觉反馈
  setTimeout(() => {
    fileList.value = files
    fileLoading.value = false
    // 立即显示文件列表，提供即时反馈
    ElMessage.success(t('executionDetail.fileAdded', { name: file.name }))
  }, 300)
}

// 处理文件移除
const handleFileRemove = (file, files) => {
  console.log('File removed:', file.name)
  fileList.value = files
  ElMessage.info(t('executionDetail.fileRemoved', { name: file.name }))
}

// 处理文件数量超限
const handleExceed = (files, fileList) => {
  ElMessage.warning(t('executionDetail.maxFilesExceed', { count: fileList.length }))
}

// 对话框拖拽状态
const isDraggingOverDialog = ref(false)
const prFormRef = ref(null)
let dragCounter = 0  // 用于跟踪拖拽进入/离开次数

// 初始化对话框拖拽功能
const initDialogDragDrop = () => {
  // 对话框打开时初始化
  dragCounter = 0
  isDraggingOverDialog.value = false
  console.log('对话框拖拽功能已启用')
  
  // 将对话框内容滚动到顶部
  nextTick(() => {
    const dialogBody = document.querySelector('.el-dialog__body')
    if (dialogBody) {
      dialogBody.scrollTop = 0
    }
    
    // 同时重置描述框的滚动位置
    const descriptionTextarea = document.querySelector('.el-dialog__body textarea')
    if (descriptionTextarea) {
      descriptionTextarea.scrollTop = 0
    }
  })
}

// 清理对话框拖拽功能
const cleanupDialogDragDrop = () => {
  isDraggingOverDialog.value = false
  dragCounter = 0
}

// 处理对话框拖拽悬停
const handleDialogDragOver = (e) => {
  e.preventDefault()
  e.stopPropagation()
  isDraggingOverDialog.value = true
}

// 处理对话框拖拽进入
const handleDialogDragEnter = (e) => {
  e.preventDefault()
  e.stopPropagation()
  dragCounter++
  isDraggingOverDialog.value = true
}

// 处理对话框拖拽离开
const handleDialogDragLeave = (e) => {
  e.preventDefault()
  e.stopPropagation()
  dragCounter--
  
  // 只有当计数器为0时才真正离开
  if (dragCounter === 0) {
    isDraggingOverDialog.value = false
  }
}

// 处理对话框文件拖放
const handleDialogDrop = (e) => {
  e.preventDefault()
  e.stopPropagation()
  isDraggingOverDialog.value = false
  dragCounter = 0
  
  const files = Array.from(e.dataTransfer.files)
  
  if (files.length === 0) {
    return
  }
  
  // 检查文件数量限制
  const totalFiles = fileList.value.length + files.length
  if (totalFiles > 10) {
    ElMessage.warning(t('executionDetail.maxFilesExceedDrag', { count: fileList.value.length }))
    return
  }
  
  // 检查单个文件大小（500MB = 524288000 bytes）
  const maxSize = 524288000
  const oversizedFiles = files.filter(file => file.size > maxSize)
  if (oversizedFiles.length > 0) {
    ElMessage.warning(t('executionDetail.fileSizeExceed', { name: oversizedFiles[0].name }))
    return
  }
  
  // 显示加载状态
  fileLoading.value = true
  
  // 添加文件到列表
  setTimeout(() => {
    files.forEach(file => {
      const fileObj = {
        name: file.name,
        size: file.size,
        raw: file,
        status: 'ready',
        uid: Date.now() + Math.random()
      }
      fileList.value.push(fileObj)
    })
    
    fileLoading.value = false
    ElMessage.success(t('executionDetail.filesAdded', { count: files.length }))
  }, 300)
}

// 加载Zmind关联链接
const loadZmindLinks = async (testcaseId) => {
  try {
    console.log('Loading zmind links for testcase:', testcaseId)
    const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}/testcases/${testcaseId}/zmind-links`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    const data = await res.json()
    console.log('Zmind links response:', data)
    if (data.code === 200) {
      zmindLinks.value = data.data || []
      console.log('Zmind links loaded:', zmindLinks.value)
    }
  } catch (error) {
    console.error('加载Zmind链接失败:', error)
  }
}

// 加载用例附件
const loadCaseAttachments = async (testcaseId) => {
  caseAttachmentsLoading.value = true
  try {
    const res = await getAttachments(testcaseId)
    if (res.code === 200) {
      caseAttachments.value = res.data || []
    }
  } catch (error) {
    console.error('加载附件失败:', error)
  } finally {
    caseAttachmentsLoading.value = false
  }
}

// 判断文件是否可预览
const isPreviewable = (fileName) => {
  if (!fileName) return false
  const ext = fileName.split('.').pop().toLowerCase()
  const previewableExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg', 'pdf', 'txt', 'log', 'json', 'xml', 'csv', 'md', 'html', 'css', 'js', 'ts', 'jsx', 'tsx', 'py', 'bat', 'sh', 'cmd', 'ps1', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'env', 'vue', 'java', 'c', 'cpp', 'h', 'go', 'rs', 'rb', 'php', 'sql', 'dockerfile', 'gitignore', 'editorconfig']
  return previewableExts.includes(ext)
}

// 获取文件图标颜色
const getFileIconColor = (fileName) => {
  if (!fileName) return '#909399'
  const ext = fileName.split('.').pop().toLowerCase()
  const colorMap = {
    jpg: '#67C23A', jpeg: '#67C23A', png: '#67C23A', gif: '#67C23A', bmp: '#67C23A', webp: '#67C23A', svg: '#67C23A',
    pdf: '#F56C6C',
    doc: '#409EFF', docx: '#409EFF',
    xls: '#67C23A', xlsx: '#67C23A',
    zip: '#E6A23C', rar: '#E6A23C', '7z': '#E6A23C',
    txt: '#909399', log: '#909399', json: '#E6A23C', xml: '#E6A23C',
  }
  return colorMap[ext] || '#909399'
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 预览附件
const handlePreviewCaseAttachment = async (att) => {
  const ext = att.file_name.split('.').pop().toLowerCase()
  casePreviewFileName.value = att.file_name
  casePreviewTextContent.value = ''
  
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  const textExts = ['txt', 'log', 'json', 'xml', 'csv', 'md', 'html', 'css', 'js', 'ts', 'jsx', 'tsx', 'py', 'bat', 'sh', 'cmd', 'ps1', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'env', 'vue', 'java', 'c', 'cpp', 'h', 'go', 'rs', 'rb', 'php', 'sql', 'dockerfile', 'gitignore', 'editorconfig']
  
  if (imageExts.includes(ext)) {
    casePreviewType.value = 'image'
    casePreviewUrl.value = getAttachmentPreviewUrl(att.id)
    casePreviewDialogVisible.value = true
  } else if (ext === 'pdf') {
    casePreviewType.value = 'pdf'
    casePreviewUrl.value = getAttachmentPreviewUrl(att.id)
    casePreviewDialogVisible.value = true
  } else if (textExts.includes(ext)) {
    casePreviewType.value = 'text'
    try {
      const response = await downloadAttachment(att.id)
      // response.data 是 Blob（因为 responseType: 'blob'）
      const blob = response.data instanceof Blob
        ? response.data
        : new Blob([response.data])
      const text = await blob.text()
      casePreviewTextContent.value = text
      casePreviewDialogVisible.value = true
    } catch (error) {
      ElMessage.error('预览失败')
    }
  } else {
    casePreviewType.value = 'other'
    casePreviewDialogVisible.value = true
  }
}

// 下载附件
const handleDownloadCaseAttachment = async (attachment) => {
  try {
    const response = await downloadAttachment(attachment.id)
    // response 是完整的 axios response 对象（responseType: 'blob'），
    // 实际文件数据在 response.data
    const blob = response.data instanceof Blob
      ? response.data
      : new Blob([response.data], { type: attachment.file_type || 'application/octet-stream' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', attachment.file_name)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

const naturalSort = (a, b) => {
  if (!a && !b) return 0
  if (!a) return -1
  if (!b) return 1
  
  const numA = parseInt(a.replace(/\D/g, '')) || 0
  const numB = parseInt(b.replace(/\D/g, '')) || 0
  
  if (numA !== numB) return numA - numB
  return a.localeCompare(b, 'zh-CN')
}

// 过滤后的用例列表
const filteredTestcases = computed(() => {
  let filtered = allTestcases.value
  
  // 按自动化类型筛选
  if (automationFilter.value === 'auto') {
    filtered = filtered.filter(tc => tc.automation?.toUpperCase() === 'Y')
  } else if (automationFilter.value === 'manual') {
    filtered = filtered.filter(tc => tc.automation?.toUpperCase() !== 'Y')
  }
  
  // 按模块筛选
  if (selectedModule.value) {
    if (selectedModule.value.startsWith('path:')) {
      const fullPath = selectedModule.value.substring(5)
      filtered = filtered.filter(tc => {
        const modulePath = tc.module || '未分类'
        return modulePath === fullPath || modulePath.startsWith(fullPath + '/')
      })
    } else {
      // 只选了主模块：匹配该主模块及其所有子模块
      filtered = filtered.filter(tc => {
        const modulePath = tc.module || '未分类'
        const mainModule = modulePath.split('/')[0].trim()
        return mainModule === selectedModule.value
      })
    }
  }
  
  // 按关键词搜索（用例编号、标题、前置条件、操作步骤、预期结果）
  if (caseSearchKeyword.value && caseSearchKeyword.value.trim()) {
    // 按空格拆分关键词，每个词独立匹配（AND 逻辑），支持多词组合搜索
    const keywords = caseSearchKeyword.value.trim().toLowerCase().split(/\s+/).filter(k => k)
    filtered = filtered.filter(tc => {
      const searchText = [
        tc.case_number,
        tc.name,
        tc.precondition,
        tc.steps,
        tc.expected_result,
        tc.execution_remark  // 执行备注
      ].filter(Boolean).join(' ').toLowerCase()
      return keywords.every(kw => searchText.includes(kw))
    })
  }
  
  // 按执行状态筛选
  if (statusFilter.value) {
    if (statusFilter.value === 'EXECUTED') {
      filtered = filtered.filter(tc => tc.execution_status && tc.execution_status !== 'PENDING' && tc.execution_status !== 'ONGOING')
    } else if (statusFilter.value === 'PENDING') {
      filtered = filtered.filter(tc => !tc.execution_status || tc.execution_status === 'PENDING' || tc.execution_status === 'ONGOING')
    } else {
      filtered = filtered.filter(tc => tc.execution_status === statusFilter.value)
    }
  }
  
  // 排序：未执行的在前，已执行的在后（ONGOING视为未执行）
  // 总用例/未执行：按编号排序；其他：按最新更新排序
  const pending = []
  const executed = []
  filtered.forEach(tc => {
    if (tc.execution_status === 'PENDING' || tc.execution_status === 'ONGOING') {
      pending.push(tc)
    } else {
      executed.push(tc)
    }
  })
  
  const sortByNumber = (arr) => {
    return [...arr].sort((a, b) => {
      const aModule = a.module || '未分类'
      const bModule = b.module || '未分类'
      
      if (!selectedModule.value) {
        if (aModule !== bModule) {
          return aModule.localeCompare(bModule, 'zh-CN')
        }
      }
      return naturalSort(a.case_number, b.case_number)
    })
  }
  
  const sortByTime = (arr) => {
    return [...arr].sort((a, b) => {
      const timeA = new Date(a.executed_at || 0).getTime()
      const timeB = new Date(b.executed_at || 0).getTime()
      if (timeA === timeB) return 0
      return timeB - timeA
    })
  }
  
  const isAllCases = !statusFilter.value || statusFilter.value === 'EXECUTED'
  const isPending = statusFilter.value === 'PENDING'
  const needModuleSort = !statusFilter.value || isPending
  
  if (isAllCases) {
    return [...sortByNumber(pending), ...sortByTime(executed)]
  }
  
  if (needModuleSort) {
    return sortByNumber(filtered)
  } else {
    return sortByTime(filtered)
  }
})


// 按状态筛选
const filterByStatus = (status) => {
  statusFilter.value = status
  visibleCount.value = 100  // 重置可见数量
}

// 按自动化类型筛选
const handleAutomationFilterChange = () => {
  visibleCount.value = 100  // 重置可见数量
  // 切换类型后重新定位到第一个用例
  if (filteredTestcases.value.length > 0) {
    selectTestcase(filteredTestcases.value[0].id)
  }
}

// 当前用例在列表中的索引
const currentIndex = computed(() => {
  return filteredTestcases.value.findIndex(tc => tc.id === currentTestcaseId.value)
})

// 是否有上一个
const hasPrevious = computed(() => {
  return currentIndex.value > 0
})

// 是否有下一个
const hasNext = computed(() => {
  return currentIndex.value < filteredTestcases.value.length - 1
})

// 加载测试计划详情
const loadPlanDetail = async () => {
  try {
    const res = await getTestPlanDetail(planId, { all_cases: true })
    if (res.code === 200) {
      planDetail.value = res.data
      // 填充用例列表
      allTestcases.value = res.data.all_test_cases || res.data.test_cases || []
      // 如果有测试用例，且当前没有选中用例，默认选择第一个
      if (allTestcases.value.length > 0 && !currentTestcaseId.value) {
        currentTestcaseId.value = allTestcases.value[0].id
        await loadTestCaseDetail(currentTestcaseId.value)
      }
    }
  } catch (error) {
    ElMessage.error(t('testplan.loadPlanFailed'))
  }
}

// 加载用例详情
const loadTestCaseDetail = async (testcaseId) => {
  try {
    console.log('Loading testcase detail for:', testcaseId)
    
    // 查找当前用例的执行状态
    const currentTestcase = allTestcases.value.find(tc => tc.id === testcaseId)
    
    // 根据执行状态设置表单默认值
    if (currentTestcase && currentTestcase.execution_status && currentTestcase.execution_status !== 'PENDING') {
      executionForm.result = currentTestcase.execution_status
    } else {
      executionForm.result = 'PASS'
    }
    
    // 清空备注（会在后面的loadLatestExecutionRemark中重新加载）
    executionForm.remark = ''
    
    zmindLinks.value = []
    
    const res = await getTestCaseDetail(testcaseId)
    
    if (res.code === 200) {
      // 直接替换整个对象，避免Object.assign残留旧数据
      testcaseDetail.value = res.data
      
      // 加载Zmind关联链接
      loadZmindLinks(testcaseId)
      
      // 加载用例附件
      loadCaseAttachments(testcaseId)
      
      // 加载执行历史
      loadExecutionHistory(testcaseId)
      
      // 加载最新的执行备注
      await loadLatestExecutionRemark(testcaseId)
      
      // 强制设置激活标签页为用例信息
      activeTab.value = 'info'
    } else {
      ElMessage.error(t('executionDetail.loadCaseDetailFailed') + ': ' + (res.message || ''))
    }
  } catch (error) {
    console.error('Network error:', error)
    ElMessage.error(t('executionDetail.loadCaseDetailNetworkError'))
  }
}

// 加载最新的执行备注
const loadLatestExecutionRemark = async (testcaseId) => {
  try {
    console.log('Loading latest execution remark for testcase:', testcaseId, 'in plan:', planId)
    const res = await getLatestExecutionRemark(planId, testcaseId)
    console.log('Latest execution remark response:', res)
    
    if (res.code === 200 && res.data) {
      // 只有当备注不为空且不是空字符串时才填充
      const remarks = res.data.remarks
      if (remarks && remarks.trim() !== '') {
        executionForm.remark = remarks
        console.log('Loaded remark:', remarks)
      } else {
        // 确保清空备注框
        executionForm.remark = ''
        console.log('No remark found, cleared remark field')
      }
    }
  } catch (error) {
    console.error('加载执行备注失败:', error)
    // 不显示错误消息，因为这不是关键功能
  }
}

// 加载执行历史
const loadExecutionHistory = async (testcaseId) => {
  try {
    console.log('Loading execution history for testcase:', testcaseId)
    const res = await getExecutions({
      // 不限制test_plan_id，显示该用例在所有测试计划中的执行历史
      test_case_id: testcaseId,
      page: 1,
      size: 100  // 获取最近100条执行历史
    })
    console.log('Execution history response:', res)
    if (res.code === 200) {
      executionHistory.value = res.data.records || []
      console.log('Execution history loaded:', executionHistory.value)
    }
  } catch (error) {
    console.error('加载执行历史失败:', error)
  }
}

// 选择用例
const selectTestcase = async (testcaseId) => {
  currentTestcaseId.value = testcaseId
  
  // 确保选中的用例在可见范围内
  const idx = filteredTestcases.value.findIndex(tc => tc.id === testcaseId)
  if (idx >= 0 && idx >= visibleCount.value) {
    visibleCount.value = idx + 50  // 扩展到该用例之后
  }
  
  try {
    // 加载用例详情（会自动清空并重新加载备注）
    await loadTestCaseDetail(testcaseId)
    
    // 滚动到选中的用例
    await nextTick()
    scrollToSelectedTestcase()
  } catch (error) {
    console.error('Failed to select testcase:', error)
    ElMessage.error(t('executionDetail.selectCaseFailed'))
  }
}

// 滚动到选中的用例
const scrollToSelectedTestcase = () => {
  const testcaseList = document.querySelector('.testcase-list')
  const activeItem = document.querySelector('.testcase-item.active')
  
  if (testcaseList && activeItem) {
    const listRect = testcaseList.getBoundingClientRect()
    const itemRect = activeItem.getBoundingClientRect()
    
    // 计算用例项相对于列表容器的位置
    const itemTop = activeItem.offsetTop
    const itemHeight = activeItem.offsetHeight
    const listScrollTop = testcaseList.scrollTop
    const listHeight = testcaseList.clientHeight
    
    // 如果用例不在可见区域，滚动到合适的位置
    // 让选中的用例显示在列表中间位置
    const targetScrollTop = itemTop - (listHeight / 2) + (itemHeight / 2)
    
    testcaseList.scrollTo({
      top: Math.max(0, targetScrollTop),
      behavior: 'smooth'
    })
  }
}

// 模块变化
const handleModuleChange = () => {
  visibleCount.value = 100  // 重置可见数量
  // 模块变化后，如果当前用例不在筛选结果中，选择第一个用例
  if (filteredTestcases.value.length > 0) {
    const currentInFiltered = filteredTestcases.value.find(tc => tc.id === currentTestcaseId.value)
    if (!currentInFiltered) {
      selectTestcase(filteredTestcases.value[0].id)
    }
  }
}

// 上一个用例
const goToPrevious = () => {
  if (hasPrevious.value) {
    const prevTestcase = filteredTestcases.value[currentIndex.value - 1]
    selectTestcase(prevTestcase.id)
  }
}

// 下一个用例
const goToNext = () => {
  if (hasNext.value) {
    const nextTestcase = filteredTestcases.value[currentIndex.value + 1]
    selectTestcase(nextTestcase.id)
  }
}

// 提交执行结果
const submitExecution = async (force = false) => {
  if (!executionForm.result) {
    ElMessage.warning(t('executionDetail.selectResult'))
    return
  }

  // 非PASS/ONGOING结果必须填写备注
  if (executionForm.result !== 'PASS' && executionForm.result !== 'ONGOING' && (!executionForm.remark || executionForm.remark.trim() === '')) {
    ElMessage.warning(t('executionDetail.inputRemark'))
    return
  }

  submitting.value = true
  try {
    const res = await createExecution({
      test_plan_id: planId,
      test_case_id: currentTestcaseId.value,
      result: executionForm.result,
      remarks: executionForm.remark,
      version_info: executionForm.version_info,
      force
    })

    // 409 冲突：显示冲突确认弹窗
    if (res.code === 409) {
      submitting.value = false
      showConflictDialog(res.data)
      return
    }

    ElMessage.success(t('executionDetail.submitSuccess'))

    // 在更新状态前，先记住当前位置的下一个用例ID（排序还没变化）
    const currentIdx = filteredTestcases.value.findIndex(tc => tc.id === currentTestcaseId.value)
    const nextTestcaseId = (currentIdx >= 0 && currentIdx < filteredTestcases.value.length - 1)
      ? filteredTestcases.value[currentIdx + 1].id
      : null

    // 本地更新当前用例的执行状态，避免重新加载全部数据
    const currentTc = allTestcases.value.find(tc => tc.id === currentTestcaseId.value)
    if (currentTc) {
      currentTc.execution_status = executionForm.result
      currentTc.executed_at = new Date().toISOString()
    }

    // 重置表单
    resetForm()

    // 跳到提交前记住的下一个用例
    if (nextTestcaseId) {
      await selectTestcase(nextTestcaseId)
    } else {
      // 已经是最后一个用例，刷新当前用例的执行历史
      loadExecutionHistory(currentTestcaseId.value)
    }
  } catch (error) {
    ElMessage.error(t('executionDetail.submitFailed'))
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  executionForm.result = 'PASS'
  executionForm.remark = ''
  // version_info 不清空，保留给下一个用例自动填充
}

// 返回
const goBack = () => {
  // 构建返回URL，保留所有查询参数
  const query = {}
  
  // 保留筛选状态
  if (route.query.statusFilter) {
    query.statusFilter = route.query.statusFilter
  }
  if (automationFilter.value) {
    query.automationFilter = automationFilter.value
  }
  if (route.query.module) {
    query.module = route.query.module
  }
  if (route.query.subModule) {
    query.subModule = route.query.subModule
  }
  // 保留页码
  if (route.query.page) {
    query.page = route.query.page
  }
  
  router.push({
    path: `/testplans/${planId}/execution`,
    query
  })
}

// 解析步骤
const parseSteps = (stepsText) => {
  if (!stepsText) return []
  
  if (Array.isArray(stepsText)) {
    return stepsText.map(item => {
      let text = ''
      if (typeof item === 'object' && item !== null) {
        text = String(item.step || '').trim()
      } else {
        text = String(item).trim()
      }
      
      // 移除序号前缀（排除小数点：. 后不能紧跟数字）
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
        text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      }
      return text.trim()
    }).filter(text => text)
  }
  
  const textStr = String(stepsText).trim()
  if (!textStr) return []
  
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = ''
        if (typeof item === 'object' && item !== null) {
          text = String(item.step || '').trim()
        } else {
          text = String(item).trim()
        }
        
        // 移除序号前缀（排除小数点：. 后不能紧跟数字）
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
          text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        return text.trim()
      }).filter(text => text)
    }
  } catch (e) {
    // JSON解析失败，按纯文本处理
  }
  
  // 纯文本处理：有序号（>=2行）按序号拆，无序号整体1条保留换行
  const lines = textStr.split('\n')
  // 序号行：数字+标点开头，. 后不能紧跟数字（排除小数如 177.5）
  const numberedLines = lines.filter(l => /^\s*\d+\s*(?:[。、]|\.)(?!\d)/.test(l.trim()))
  if (numberedLines.length >= 2) {
    const items = []
    let current = null
    for (const line of lines) {
      const stripped = line.trim()
      if (/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/.test(stripped)) {
        if (current !== null) items.push(current.trim())
        current = stripped.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
      } else if (current !== null) {
        current += '\n' + line
      }
    }
    if (current !== null) items.push(current.trim())
    return items.filter(t => t)
  }
  // 整体1条，但去掉可能存在的序号前缀（排除小数点）
  const stripped2 = textStr.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
  return stripped2 ? [stripped2] : []
}

// 解析预期结果
const parseExpected = (expectedText) => {
  if (!expectedText) return []
  
  if (Array.isArray(expectedText)) {
    return expectedText.map(item => {
      let text = ''
      if (typeof item === 'object' && item !== null) {
        text = String(item.expected || '').trim()
      } else {
        text = String(item).trim()
      }
      
      // 移除序号前缀（排除小数点：. 后不能紧跟数字）
      while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
        text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      }
      return text.trim()
    }).filter(text => text)
  }
  
  const textStr = String(expectedText).trim()
  if (!textStr) return []
  
  try {
    const parsed = JSON.parse(textStr)
    if (Array.isArray(parsed)) {
      return parsed.map(item => {
        let text = ''
        if (typeof item === 'object' && item !== null) {
          text = String(item.expected || '').trim()
        } else {
          text = String(item).trim()
        }
        
        // 移除序号前缀（排除小数点：. 后不能紧跟数字）
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(text)) {
          text = text.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        return text.trim()
      }).filter(text => text)
    }
  } catch (e) {
    // JSON解析失败，按纯文本处理
  }
  
  // 纯文本处理：有序号（>=2行）按序号拆，无序号整体1条保留换行
  const lines = textStr.split('\n')
  // 序号行：数字+标点开头，. 后不能紧跟数字（排除小数如 177.5）
  const numberedLines = lines.filter(l => /^\s*\d+\s*(?:[。、]|\.)(?!\d)/.test(l.trim()))
  if (numberedLines.length >= 2) {
    const items = []
    let current = null
    for (const line of lines) {
      const stripped = line.trim()
      if (/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/.test(stripped)) {
        if (current !== null) items.push(current.trim())
        current = stripped.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
      } else if (current !== null) {
        current += '\n' + line
      }
    }
    if (current !== null) items.push(current.trim())
    return items.filter(t => t)
  }
  // 整体1条，但去掉可能存在的序号前缀（排除小数点）
  const stripped2 = textStr.replace(/^\s*\d+\s*(?:[。、]|\.)(?!\d)\s*/, '')
  return stripped2 ? [stripped2] : []
}

// 获取等级类型
const getLevelType = (level) => {
  const typeMap = {
    L1: 'danger',
    L2: 'warning',
    L3: 'success',
    L4: 'info'
  }
  return typeMap[level] || 'info'
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 打开PR对话框
const openPRDialog = async () => {
  // 显示自定义连接蒙版（支持取消）
  zmindConnecting.value = true
  zmindConnectController.value = new AbortController()
  const signal = zmindConnectController.value.signal
  
  try {
    // 检查测试计划是否已选择Zmind项目（内存缓存，页面内只请求一次）
    let zmindProjectId = cachedZmindProjectId.value
    if (zmindProjectId === null) {
      const res = await getTestPlanZmindProject(planId, signal)
      if (signal.aborted) return
      zmindProjectId = (res.code === 200 && res.data.zmind_project_id) ? res.data.zmind_project_id : ''
      cachedZmindProjectId.value = zmindProjectId
    }

    if (zmindProjectId) {
      // 已选择项目，直接打开PR表单
      selectedZmindProject.value = zmindProjectId

      // 获取项目名称用于显示（getZmindProjects 会命中 localStorage 缓存，几乎无延迟）
      const projectsRes = await getZmindProjects(signal)
      if (signal.aborted) return

      if (projectsRes.code === 200) {
        const project = projectsRes.data.find(p => p.id === selectedZmindProject.value)
        if (project) {
          selectedZmindProjectName.value = project.name
        }
      }

      await openPRForm()
    } else {
      // 未选择项目，打开项目选择对话框
      await openProjectDialog(signal)
    }
  } catch (error) {
    if (error?.name === 'AbortError' || error?.code === 'ERR_CANCELED') {
      return
    }
    console.error('Failed to check Zmind project:', error)
    ElMessage.error(t('executionDetail.checkZmindFailed'))
  } finally {
    zmindConnecting.value = false
    zmindConnectController.value = null
  }
}

// 取消连接Zmind
const cancelZmindConnect = () => {
  if (zmindConnectController.value) {
    zmindConnectController.value.abort()
  }
  zmindConnecting.value = false
}

// 打开项目选择对话框
const openProjectDialog = async () => {
  projectDialogVisible.value = true
  projectLoading.value = true
  
  try {
    // 重新选择项目时强制刷新，确保拿到最新的 Zmind 项目列表
    const res = await getZmindProjects(null, true)
    if (res.code === 200) {
      // 直接使用后端返回的扁平列表,已经包含了层级缩进
      zmindProjects.value = res.data
      filteredZmindProjects.value = res.data
      if (zmindProjects.value.length === 0) {
        ElMessage.warning(t('executionDetail.noZmindProjects'))
        projectDialogVisible.value = false
      } else {
        // 如果已有选择的项目,获取项目名称用于显示
        if (selectedZmindProject.value) {
          const project = zmindProjects.value.find(p => p.id === selectedZmindProject.value)
          if (project) {
            selectedZmindProjectName.value = project.name
          }
        }
      }
    } else {
      ElMessage.error(res.message || t('executionDetail.getProjectListFailed'))
      projectDialogVisible.value = false
    }
  } catch (error) {
    console.error('Failed to get project list:', error)
    if (error.response?.status === 400) {
      ElMessage.error(t('executionDetail.configZmindFirst'))
    } else {
      ElMessage.error(t('executionDetail.getProjectListFailed'))
    }
    projectDialogVisible.value = false
  } finally {
    projectLoading.value = false
  }
}

// 确认选择项目
const confirmProjectSelection = async () => {
  if (!selectedZmindProject.value) {
    ElMessage.warning(t('executionDetail.selectZmindProject'))
    return
  }
  
  try {
    // 保存项目名称
    const selectedProject = zmindProjects.value.find(p => p.id === selectedZmindProject.value)
    if (selectedProject) {
      selectedZmindProjectName.value = selectedProject.name
    }
    
    // 保存项目选择到测试计划
    const res = await updateTestPlanZmindProject(planId, {
      zmind_project_id: selectedZmindProject.value
    })
    
    if (res.code === 200) {
      projectDialogVisible.value = false
      ElMessage.success(t('executionDetail.projectSaved'))
      // 更新内存缓存，下次打开 PR 对话框不再请求 testplan zmind-project
      cachedZmindProjectId.value = selectedZmindProject.value
      // 选择了新项目，清除该项目的字段缓存，确保下次重新获取
      clearZmindProjectCache(selectedZmindProject.value)
      // 打开PR表单
      openPRForm()
    } else {
      ElMessage.error(res.message || t('executionDetail.saveProjectFailed'))
    }
  } catch (error) {
    console.error('Failed to save project selection:', error)
    ElMessage.error(t('executionDetail.saveProjectFailed'))
  }
}

// 重新选择项目
const reSelectProject = async () => {
  // 关闭PR对话框
  prDialogVisible.value = false
  // 打开项目选择对话框
  await openProjectDialog()
}

// 打开PR表单
const openPRForm = async () => {
  // 重置表单
  const tc = testcaseDetail.value
  
  // 标题格式：【主模块名称】用例标题
  prForm.subject = `【${tc.module || ''}】${tc.name}`
  
  prForm.description = generatePRDescription()
  prForm.tracker_id = 1  // 固定为PR类型
  prForm.priority_id = 2
  prForm.severity = 'Minor'
  prForm.issue_version = ''  // 清空，让用户手动输入
  prForm.tevama_id = tc.case_number || ''  // 自动填入当前用例编号
  prForm.project_id = selectedZmindProject.value
  prForm.assigned_to_id = null
  prForm.category_id = null
  prForm.fixed_version_id = null
  prForm.phase = null
  prForm.side_effect = 'NO'
  prForm.due_date = null
  fileList.value = []
  
  prDialogVisible.value = true
  
  // 加载下拉选项
  await loadPROptions()
}

// 生成PR描述
const generatePRDescription = () => {
  const tc = testcaseDetail.value
  
  // 尝试从localStorage获取该测试计划的上次填写的Tested Environment
  const cacheKey = `pr_tested_env_plan_${planId}`
  const cachedTestedEnv = localStorage.getItem(cacheKey) || ''
  
  let description = '【Tested Environment】\n'
  if (cachedTestedEnv) {
    description += `${cachedTestedEnv}\n\n`
  } else {
    description += '\n'
  }
  
  // 【Initial Situation】下面填写前置条件
  description += '【Initial Situation】\n'
  if (tc.precondition && tc.precondition.trim()) {
    description += `${tc.precondition}\n\n`
  } else {
    description += '\n'
  }
  
  description += '【Operation Steps】\n\n'
  
  // 添加操作步骤
  const steps = parseSteps(tc.steps)
  steps.forEach((step, index) => {
    description += `  [Step${index + 1}] ${step}\n\n`
  })
  
  // 额外追加 3 个空步骤供用户填写
  for (let i = 1; i <= 3; i++) {
    description += `  [Step${steps.length + i}] \n\n`
  }
  
  description += '【Actual Result】\n\n'
  
  // 添加预期结果
  const expected = parseExpected(tc.expected_result)
  if (expected.length > 0) {
    description += '【Expect Result】\n'
    expected.forEach((result, index) => {
      description += `  ${index + 1}. ${result}\n`
    })
    description += '\n'
  }
  
  description += '【Frequency Details】\n \n'
  description += '【Recovery Method】\n\n'
  
  return description
}

// 从描述中提取【Tested Environment】的内容并保存
const saveTestedEnvironment = (description) => {
  try {
    // 使用正则表达式提取【Tested Environment】和【Initial Situation】之间的内容
    const regex = /【Tested Environment】\n([\s\S]*?)\n【Initial Situation】/
    const match = description.match(regex)
    
    if (match && match[1]) {
      const testedEnv = match[1].trim()
      if (testedEnv) {
        const cacheKey = `pr_tested_env_plan_${planId}`
        localStorage.setItem(cacheKey, testedEnv)
        console.log('已保存Tested Environment:', testedEnv)
      }
    }
  } catch (error) {
    console.error('保存Tested Environment失败:', error)
  }
}

// 加载PR选项
const loadPROptions = async () => {
  // 全部命中缓存时跳过 loading，避免闪烁
  if (!isZmindPRCacheReady(selectedZmindProject.value)) {
    prFormLoading.value = true
  }
  try {
    // Zmind 服务器有请求频率限制，并发请求会触发 403
    // 必须串行调用，避免短时间内发出大量请求
    const prioritiesRes = await getPriorities()
    if (prioritiesRes?.code === 200) {
      priorities.value = prioritiesRes.data
    }

    const severitiesRes = await getSeverities()
    if (severitiesRes?.code === 200) {
      severities.value = severitiesRes.data
    }

    const projectFieldsRes = await getProjectFields(selectedZmindProject.value)
    if (projectFieldsRes?.code === 200) {
      const fields = projectFieldsRes.data
      members.value = fields.members || []
      versions.value = fields.versions || []
      categories.value = fields.categories || []
    }

    const phasesRes = await getPhases()
    if (phasesRes?.code === 200) {
      phases.value = phasesRes.data
    }

    const sideEffectsRes = await getSideEffects()
    if (sideEffectsRes?.code === 200) {
      sideEffects.value = sideEffectsRes.data
    }

    const requiredFieldsRes = await getProjectRequiredFields(selectedZmindProject.value, 1)
    if (requiredFieldsRes?.code === 200) {
      requiredFields.value = requiredFieldsRes.data.required_fields || []
    }
  } catch (error) {
    console.error('Failed to load PR options:', error)
    ElMessage.error(t('executionDetail.loadPrOptionsFailed'))
  } finally {
    prFormLoading.value = false
  }
}

// 检查字段是否必填
const isFieldRequired = (fieldName) => {
  return requiredFields.value.includes(fieldName)
}

// 提交PR
const submitPR = async () => {
  // 验证必填字段
  if (!prForm.subject || !prForm.subject.trim()) {
    ElMessage.warning(t('executionDetail.inputPrTitle'))
    return
  }
  if (!prForm.description || !prForm.description.trim()) {
    ElMessage.warning(t('executionDetail.inputPrDescription'))
    return
  }
  if (!prForm.priority_id) {
    ElMessage.warning(t('executionDetail.selectPriority'))
    return
  }
  
  // 动态验证必填字段
  if (isFieldRequired('Severity') && !prForm.severity) {
    ElMessage.warning(t('executionDetail.selectSeverityRequired'))
    return
  }
  if (isFieldRequired('Issue Version') && (!prForm.issue_version || !prForm.issue_version.trim())) {
    ElMessage.warning(t('executionDetail.inputIssueVersionRequired'))
    return
  }
  if (isFieldRequired('Phase') && !prForm.phase) {
    ElMessage.warning(t('executionDetail.selectPhaseRequired'))
    return
  }
  if (isFieldRequired('Category') && !prForm.category_id) {
    ElMessage.warning(t('executionDetail.selectCategoryRequired'))
    return
  }
  if (isFieldRequired('Fixed Version') && !prForm.fixed_version_id) {
    ElMessage.warning(t('executionDetail.selectVersionRequired'))
    return
  }
  
  prSubmitting.value = true
  let issueId = null
  
  try {
    // 第一步：创建Issue
    const res = await createZmindIssue({
      subject: prForm.subject,
      description: prForm.description,
      tracker_id: prForm.tracker_id,
      priority_id: prForm.priority_id,
      severity: prForm.severity,
      issue_version: prForm.issue_version,
      tevama_id: prForm.tevama_id || undefined,
      project_id: prForm.project_id,
      testcase_id: currentTestcaseId.value,
      assigned_to_id: prForm.assigned_to_id,
      category_id: prForm.category_id,
      fixed_version_id: prForm.fixed_version_id,
      phase: prForm.phase,
      side_effect: prForm.side_effect,
      due_date: prForm.due_date
    })
    
    if (res.code === 200) {
      issueId = res.data.id
      
      if (!issueId) {
        ElMessage.error('PR创建返回异常：未获取到Issue ID')
        prSubmitting.value = false
        return
      }
      
      // 第二步：如果有附件，上传附件
      if (fileList.value && fileList.value.length > 0) {
        uploadProgress.value.show = true
        uploadProgress.value.percent = 0
        uploadProgress.value.text = t('executionDetail.uploadingAttachment')
        uploadProgress.value.status = ''
        
        try {
          const totalFiles = fileList.value.length
          let uploadedFiles = 0
          
          for (const fileItem of fileList.value) {
            // 上传每个文件到Redmine
            const formData = new FormData()
            formData.append('file', fileItem.raw)
            
            // 使用XMLHttpRequest支持上传进度
            await new Promise((resolve, reject) => {
              const xhr = new XMLHttpRequest()
              xhr.open('POST', `${import.meta.env.VITE_API_BASE_URL}/zmind/issues/${issueId}/attachments`)
              xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
              xhr.timeout = 300000  // 5分钟超时
              
              xhr.upload.onprogress = (e) => {
                if (e.lengthComputable) {
                  // 当前文件进度 + 已完成文件进度
                  const fileProgress = e.loaded / e.total
                  const overallProgress = (uploadedFiles + fileProgress) / totalFiles * 100
                  uploadProgress.value.percent = Math.round(overallProgress)
                }
              }
              
              xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                  resolve()
                } else {
                  let errorMsg = `上传失败: HTTP ${xhr.status}`
                  try {
                    const response = JSON.parse(xhr.responseText)
                    if (response.detail) errorMsg += ` - ${response.detail}`
                  } catch {}
                  console.error('附件上传失败:', xhr.status, xhr.responseText)
                  reject(new Error(errorMsg))
                }
              }
              xhr.onerror = () => {
                console.error('附件上传网络错误:', xhr.status, xhr.responseText)
                reject(new Error('网络错误'))
              }
              xhr.send(formData)
            })
            
            uploadedFiles++
            uploadProgress.value.percent = Math.round((uploadedFiles / totalFiles) * 100)
          }
          
          uploadProgress.value.status = 'success'
          uploadProgress.value.text = t('executionDetail.attachmentUploadComplete')
          
          // 2秒后隐藏进度条
          setTimeout(() => {
            uploadProgress.value.show = false
            uploadProgress.value.percent = 0
          }, 2000)
        } catch (uploadError) {
          console.error('附件上传失败:', uploadError)
          uploadProgress.value.status = 'exception'
          uploadProgress.value.text = t('executionDetail.attachmentUploadFailed')
          ElMessage.warning(t('executionDetail.prCreatedButAttachmentFailed'))
          
          // 3秒后隐藏进度条
          setTimeout(() => {
            uploadProgress.value.show = false
            uploadProgress.value.percent = 0
          }, 3000)
        }
      }
      
      ElMessage.success(t('executionDetail.prSubmitSuccess'))
      
      // 保存【Tested Environment】到localStorage，供下次使用
      saveTestedEnvironment(prForm.description)
      
      // 创建测试用例与PR的关联
      try {
        await fetch(`${import.meta.env.VITE_API_BASE_URL}/testcases/${currentTestcaseId.value}/zmind-links`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            test_case_id: currentTestcaseId.value,
            zmind_issue_id: String(issueId),
            zmind_issue_subject: prForm.subject,
            zmind_issue_status: 'New',
            zmind_issue_severity: prForm.severity,
            test_plan_id: parseInt(planId)  // 添加测试计划ID
          })
        })
        console.log('PR关联已创建')
      } catch (linkError) {
        console.error('创建PR关联失败:', linkError)
      }
      
      // 自动在执行备注中添加PR ID
      const prText = `PR ${issueId}`
      const currentRemark = executionForm.remark || ''
      if (!currentRemark.includes(prText)) {
        if (currentRemark.trim()) {
          executionForm.remark = `${currentRemark}\n${prText}`
        } else {
          executionForm.remark = prText
        }
      }
      
      prDialogVisible.value = false
      
      // 显示Issue链接
      ElMessage({
        message: `${t('executionDetail.prCreatedViewIssue')}<br><a href="${res.data.url}" target="_blank" style="color: #409EFF; text-decoration: underline;">${t('executionDetail.viewIssueLink')} #${res.data.id}</a>`,
        type: 'success',
        duration: 5000,
        showClose: true,
        dangerouslyUseHTMLString: true
      })
      
      // 重新加载Zmind链接
      await loadZmindLinks(currentTestcaseId.value)
    } else {
      ElMessage.error(res.message || t('executionDetail.prSubmitFailed'))
    }
  } catch (error) {
    console.error('Failed to submit PR:', error)
    ElMessage.error(t('executionDetail.prSubmitFailed'))
  } finally {
    prSubmitting.value = false
  }
}

onMounted(async () => {
  // 并行加载计划详情和版本信息
  const [, versionRes] = await Promise.allSettled([
    loadPlanDetail(),
    getLatestVersionInfo(planId).catch(() => null)
  ])
  
  // 自动填充版本信息
  if (versionRes.status === 'fulfilled' && versionRes.value?.code === 200 && versionRes.value.data.version_info) {
    executionForm.version_info = versionRes.value.data.version_info
  }
  
  // 确保在loadPlanDetail完成后再处理用例选择
  if (currentTestcaseId.value) {
    // 检查当前用例ID是否在测试计划中
    const testcaseExists = allTestcases.value.some(tc => tc.id === currentTestcaseId.value)
    if (testcaseExists) {
      await loadTestCaseDetail(currentTestcaseId.value)
      // 滚动到选中的用例
      await nextTick()
      scrollToSelectedTestcase()
    } else if (allTestcases.value.length > 0) {
      // 如果当前用例不在测试计划中，选择第一个用例
      currentTestcaseId.value = allTestcases.value[0].id
      await loadTestCaseDetail(currentTestcaseId.value)
    }
  } else if (allTestcases.value.length > 0) {
    // 默认选择第一个用例
    currentTestcaseId.value = allTestcases.value[0].id
    await loadTestCaseDetail(currentTestcaseId.value)
  }
})
</script>

<style scoped>
/* ==================== */
/* TestCaseExecutionDetail - Demo Theme */
/* ==================== */

.execution-detail-container {
  padding: 24px;
  min-height: 100%;
  background: var(--demo-bg, #f8fafc);
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
  flex-shrink: 0;
}

.detail-header h2 {
  color: var(--demo-text-primary, #0f172a);
  font-weight: 600;
}

/* 主内容区域 - Demo风格 */
.detail-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  margin-top: 20px;
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 16px;
  overflow: visible;
  min-height: 0;
  background: var(--demo-bg-card, #ffffff);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 统计区域 - 顶部横向 - Demo风格 */
.stats-section-top {
  padding: 16px 20px;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
  background-color: rgba(248, 250, 252, 0.5);
  flex-shrink: 0;
}

.stats-cards-horizontal {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  align-items: center;
  flex-wrap: wrap;
}

.detail-tabs-wrapper {
  position: relative;
}

.detail-tabs-actions {
  position: absolute;
  right: 0;
  top: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
  box-sizing: border-box;
}

.detail-tabs-actions :deep(.el-input__wrapper) {
  height: 32px;
  box-sizing: border-box;
}

.detail-tabs-actions :deep(.el-button) {
  height: 32px;
  box-sizing: border-box;
}

.detail-search-input {
  width: 220px;
}

.detail-search-input :deep(.el-input__wrapper) {
  height: 32px;
  box-sizing: border-box;
}

.detail-tabs :deep(.el-tabs__header) {
  margin-bottom: 20px;
  padding-right: 340px;
}

.stat-card-small {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--demo-bg-card, #ffffff);
  border-radius: 8px;
  min-width: 110px;
  cursor: pointer;
  transition: all 0.15s;
  flex-shrink: 0;
  border: 1px solid var(--demo-border, #e2e8f0);
}

.stat-card-small:hover {
  background: var(--demo-border-light, #f1f5f9);
  border-color: var(--demo-border, #e2e8f0);
}

.stat-card-small.active {
  background: var(--demo-primary-light, #eef2ff);
  border-color: var(--demo-primary, #4f46e5);
}

.stat-card-small.active .stat-label-small,
.stat-card-small.active .stat-value-small {
  color: var(--demo-primary, #4f46e5) !important;
}

.stat-card-small:last-child {
  cursor: default;
}

.stat-card-small:last-child:hover {
  background: var(--demo-bg-card, #ffffff);
  transform: none;
  box-shadow: none;
}

.stat-label-small {
  font-size: 13px;
  color: var(--demo-text-muted, #64748b);
  white-space: nowrap;
  font-weight: 500;
}

.stat-value-small {
  font-size: 15px;
  font-weight: 700;
  color: var(--demo-text-primary, #0f172a);
}

/* 内容区域包装器 - 左右布局，sticky 固定 */
.content-wrapper {
  display: flex;
  position: sticky;
  top: 0;
  height: calc(100vh - 64px);
  min-height: 0;
  overflow: hidden;
  border-radius: 0 0 16px 16px;
}

/* 左侧边栏 - 固定高度，独立滚动 */
.left-sidebar {
  width: 280px;
  border-right: 1px solid var(--demo-border, #e2e8f0);
  background-color: var(--demo-bg-card, #ffffff);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  height: 100%;
}

/* 模块选择器 - Demo风格 */
.module-selector {
  padding: 16px;
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
  background-color: rgba(248, 250, 252, 0.5);
  flex-shrink: 0;
}

/* 用例列表 - Demo风格 */
.testcase-list {
  flex: 1;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 8px 0;
}

.testcase-item {
  padding: 12px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
  transition: all 0.15s;
}

.testcase-item:hover {
  background-color: var(--demo-bg, #f8fafc);
}

.testcase-item.active {
  background-color: var(--demo-primary-light, #eef2ff);
  border-left: 3px solid var(--demo-primary, #4f46e5);
}

.testcase-title {
  font-size: 14px;
  color: var(--demo-text-primary, #0f172a);
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.5;
}

.testcase-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 右侧内容 - Demo风格 */
.right-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  background-color: var(--demo-bg, #f8fafc);
  min-width: 0;
  height: 100%;
  overflow: hidden;
}

.content-scroll {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 卡片样式 - Demo风格 */
.info-card,
.execution-card,
.history-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid var(--demo-border, #e2e8f0);
}

.info-card :deep(.el-card__header),
.execution-card :deep(.el-card__header),
.history-card :deep(.el-card__header) {
  background: rgba(248, 250, 252, 0.5);
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
  padding: 16px 20px;
}

.info-card :deep(.el-card__body),
.execution-card :deep(.el-card__body),
.history-card :deep(.el-card__body) {
  padding: 20px;
}

.info-card:last-child,
.execution-card:last-child,
.history-card:last-child {
  margin-bottom: 0;
}

/* 滚动条样式 - Demo风格 */
.testcase-list::-webkit-scrollbar,
.content-scroll::-webkit-scrollbar {
  width: 8px;
}

.testcase-list::-webkit-scrollbar-track,
.content-scroll::-webkit-scrollbar-track {
  background: var(--demo-border-light, #f1f5f9);
}

.testcase-list::-webkit-scrollbar-thumb,
.content-scroll::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.testcase-list::-webkit-scrollbar-thumb:hover,
.content-scroll::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Zmind Loading 自定义样式 */
:deep(.zmind-loading) {
  .el-loading-spinner {
    top: 50%;
    margin-top: -21px;
  }
  
  .el-loading-spinner .circular {
    width: 50px;
    height: 50px;
  }
  
  .el-loading-text {
    font-size: 16px;
    color: #fff;
    margin-top: 10px;
  }
}

/* 连接Zmind自定义蒙版 */
.zmind-connecting-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  z-index: 3000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zmind-connecting-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.zmind-connecting-spinner {
  font-size: 48px;
  color: #fff;
  animation: zmind-spin 1s linear infinite;
}

@keyframes zmind-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.zmind-connecting-text {
  font-size: 16px;
  color: #fff;
  margin: 0;
}

.zmind-cancel-btn {
  padding: 8px 24px;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.5);
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
  backdrop-filter: blur(4px);
}

.zmind-cancel-btn:hover {
  background: rgba(99, 102, 241, 0.6);
  border-color: #6366f1;
}

/* 对话框拖拽上传样式 - Demo风格 */
.drag-over {
  position: relative;
}

.drag-over::before {
  content: attr(data-drop-text);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(79, 70, 229, 0.1);
  border: 3px dashed var(--demo-primary, #4f46e5);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--demo-primary, #4f46e5);
  font-weight: 600;
  z-index: 9999;
  pointer-events: none;
}

/* 上传列表样式 - Demo风格 */
:deep(.el-upload-list) {
  margin-top: 10px;
}

:deep(.el-upload-list__item) {
  transition: all 0.15s;
  border-radius: 8px;
  padding: 8px 10px;
}

:deep(.el-upload-list__item:hover) {
  background-color: var(--demo-bg, #f8fafc);
}

/* 标签页样式 - Demo风格 */

.detail-tabs :deep(.el-tabs__item) {
  color: var(--demo-text-muted, #64748b);
  font-weight: 500;
}

.detail-tabs :deep(.el-tabs__item.is-active) {
  color: var(--demo-primary, #4f46e5);
}

.detail-tabs :deep(.el-tabs__active-bar) {
  background-color: var(--demo-primary, #4f46e5);
}

/* 描述列表样式 - Demo风格 */
:deep(.el-descriptions__label) {
  color: var(--demo-text-muted, #64748b);
  font-weight: 500;
  width: 120px;
  min-width: 120px;
  max-width: 120px;
}

:deep(.el-descriptions__content) {
  color: var(--demo-text-primary, #0f172a);
}

/* 时间线样式 - Demo风格 */
:deep(.el-timeline-item__node) {
  background-color: var(--demo-primary, #4f46e5);
}

:deep(.el-timeline-item__tail) {
  border-left-color: var(--demo-border, #e2e8f0);
}

:deep(.el-timeline-item__timestamp) {
  color: var(--demo-text-muted, #64748b);
}

/* Demo风格按钮样式 */
:deep(.el-button--primary:not(.is-link)) {
  background: var(--demo-primary, #4f46e5) !important;
  border-color: var(--demo-primary, #4f46e5) !important;
  color: #fff !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
}

:deep(.el-button--primary:not(.is-link):hover) {
  background: var(--demo-primary-hover, #4338ca) !important;
  border-color: var(--demo-primary-hover, #4338ca) !important;
}

:deep(.el-button--primary.is-link) {
  background: transparent !important;
  border: none !important;
  color: var(--demo-primary, #4f46e5) !important;
  padding: 2px 4px !important;
}

:deep(.el-button--primary.is-link:hover) {
  color: var(--demo-primary-hover, #4338ca) !important;
  opacity: 0.85;
}

:deep(.el-button--default) {
  border-radius: 8px !important;
  border-color: var(--demo-border, #e2e8f0) !important;
  color: var(--demo-text-secondary, #475569) !important;
}

:deep(.el-button--default:hover) {
  border-color: var(--demo-primary, #4f46e5) !important;
  color: var(--demo-primary, #4f46e5) !important;
  background: var(--demo-primary-light, #eef2ff) !important;
}

:deep(.el-button--warning) {
  background: #f59e0b !important;
  border-color: #f59e0b !important;
  border-radius: 8px !important;
}

:deep(.el-button--warning:hover) {
  background: #d97706 !important;
  border-color: #d97706 !important;
}

/* Radio按钮样式 - Demo风格 */
:deep(.el-radio__input.is-checked .el-radio__inner) {
  background: var(--demo-primary, #4f46e5);
  border-color: var(--demo-primary, #4f46e5);
}

:deep(.el-radio__input.is-checked + .el-radio__label) {
  color: var(--demo-primary, #4f46e5);
}

/* 附件内联样式 */
.inline-attachments {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.inline-attachment-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.inline-attachment-item:hover {
  background: #f0f5ff;
  border-color: #d9e4ff;
}

.inline-att-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 240px;
}

.inline-att-size {
  font-size: 12px;
  color: #909399;
  flex-shrink: 0;
  margin-right: 4px;
}

.preview-container {
  min-height: 200px;
}

.automation-filter-wrapper {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.automation-select {
  width: 130px;
}

.automation-select :deep(.el-input__wrapper) {
  padding: 6px 12px;
  border-radius: 8px;
  background: var(--demo-bg-card, #ffffff);
  box-shadow: none;
  border: 1px solid var(--demo-border, #e2e8f0);
  height: auto;
  line-height: 1.5;
}

.automation-select :deep(.el-input__wrapper:hover) {
  background: var(--demo-border-light, #f1f5f9);
  border-color: var(--demo-border, #e2e8f0);
}

.automation-select :deep(.el-input__inner) {
  font-size: 13px;
  color: var(--text-200, #475569);
  font-weight: 500;
}
</style>

<style>
/* Zmind项目下拉列表加宽，避免项目名被截断 */
.zmind-project-dropdown {
  min-width: 700px !important;
  width: auto !important;
}
.zmind-project-dropdown .el-select-dropdown__item {
  white-space: nowrap;
  overflow: visible;
}

/* 模块树选择器下拉面板样式 */
.el-tree-select__popper .el-tree-node__content:hover {
  background-color: #f1f5f9;
}
.el-tree-select__popper .el-tree-node.is-current > .el-tree-node__content {
  background-color: #eef2ff;
  color: #4f46e5;
  font-weight: 500;
}
.el-tree-select__popper .el-tree-node.is-current > .el-tree-node__content:hover {
  background-color: #e0e7ff;
}
</style>
