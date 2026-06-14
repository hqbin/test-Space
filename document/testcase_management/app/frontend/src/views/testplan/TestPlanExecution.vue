<template>
  <div>
    <div class="execution-container">
      <!-- 头部：返回按钮和标题 -->
      <div class="execution-header">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          {{ $t('common.back') }}
        </el-button>
        <h2 style="margin: 0 0 0 20px;">{{ planDetail.name }} - {{ $t('execution.title') }}</h2>
      </div>

      <!-- 统计卡片和完成按钮 - 固定区域 -->
      <div class="stats-submit-wrapper" :class="{ 'is-fixed': isStatsFixed }" ref="statsWrapperRef">
        <div class="stats-submit-container">
          <!-- 进度统计 -->
          <div class="stats-cards">
            <div class="automation-filter-wrapper">
              <el-select
                v-model="automationFilter"
                @change="handleAutomationFilterChange"
                class="automation-select"
              >
                <el-option label="全部类型" value="" />
                <el-option label="人工测试" value="manual" />
                <el-option label="自动化测试" value="auto" />
              </el-select>
            </div>
            <div 
              class="stat-card" 
              :class="{ 'active': statusFilter === null }"
              @click="filterByStatus(null)"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('dashboard.totalCases') }}</span>
              <span class="stat-value">{{ statistics.total || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'PENDING' }"
              @click="filterByStatus('PENDING')"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('execution.notExecuted') }}</span>
              <span class="stat-value" style="color: var(--text-200);">{{ statistics.pending || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'EXECUTED' }"
              @click="filterByStatus('EXECUTED')"
              style="cursor: pointer;"
            >
              <span class="stat-label">{{ $t('execution.executed') }}</span>
              <span class="stat-value" style="color: var(--primary-100);">{{ statistics.executed || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'PASS' }"
              @click="filterByStatus('PASS')"
              style="cursor: pointer;"
            >
              <span class="stat-label">PASS</span>
              <span class="stat-value" style="color: var(--primary-100);">{{ statistics.passed || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'FAIL' }"
              @click="filterByStatus('FAIL')"
              style="cursor: pointer;"
            >
              <span class="stat-label">FAIL</span>
              <span class="stat-value" style="color: var(--accent-100);">{{ statistics.failed || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'BLOCK' }"
              @click="filterByStatus('BLOCK')"
              style="cursor: pointer;"
            >
              <span class="stat-label">BLOCK</span>
              <span class="stat-value" style="color: var(--primary-200);">{{ statistics.blocked || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'NA' }"
              @click="filterByStatus('NA')"
              style="cursor: pointer;"
            >
              <span class="stat-label">NA</span>
              <span class="stat-value" style="color: var(--text-200);">{{ statistics.na || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'NT' }"
              @click="filterByStatus('NT')"
              style="cursor: pointer;"
            >
              <span class="stat-label">NT</span>
              <span class="stat-value" style="color: var(--text-200);">{{ statistics.nt || 0 }}</span>
            </div>
            <div 
              class="stat-card"
              :class="{ 'active': statusFilter === 'ONGOING' }"
              @click="filterByStatus('ONGOING')"
              style="cursor: pointer;"
            >
              <span class="stat-label">Ongoing</span>
              <span class="stat-value" style="color: #1a73e8;">{{ statistics.ongoing || 0 }}</span>
            </div>
          </div>
          
          <!-- 完成按钮 -->
          <div class="submit-action">
            <!-- 添加用例按钮（创建人/管理员） -->
            <el-button
              v-if="canEdit && planDetail.status !== 'COMPLETED'"
              type="primary"
              size="default"
              @click="openAddTestCaseDialog"
            >
              <el-icon><Plus /></el-icon>
              {{ $t('testplan.addCases') }}
            </el-button>
            <!-- 提交审核按钮（执行人） -->
            <template v-if="isExecutor && (planDetail.status === 'IN_PROGRESS' || planDetail.status === 'REJECTED')">
              <el-button
                type="primary"
                size="default"
                @click="submitForReview"
                :disabled="!canComplete"
                style="position: relative; z-index: 10;"
              >
                <el-icon><Check /></el-icon>
                {{ planDetail.status === 'REJECTED' ? t('execution.resubmitReview') : t('execution.submitReview') }}
              </el-button>
              <div v-if="!canComplete" class="submit-tip">
                {{ $t('execution.remainingCases', { count: allTestcases.length - allExecutedCount }) }}
              </div>
            </template>
          </div>
        </div>
      </div>
      
      <!-- 占位元素,当统计卡片固定时保持布局 -->
      <div v-if="isStatsFixed" class="stats-placeholder"></div>

      <!-- 审核不通过原因提示 -->
      <el-alert
        v-if="planDetail.status === 'REJECTED' && planDetail.reject_reason"
        type="warning"
        :closable="false"
        show-icon
        style="margin-bottom: 12px;"
      >
        <template #title>
          <span style="font-weight: 600;">{{ t('execution.rejectReasonTitle') }}</span>
        </template>
        <div style="margin-top: 4px; white-space: pre-wrap; word-break: break-word;">{{ planDetail.reject_reason }}</div>
        <div v-if="planDetail.rejected_by" style="margin-top: 6px; color: #909399; font-size: 12px;">
          —— {{ planDetail.rejected_by }}{{ planDetail.rejected_at ? '，' + formatRejectTime(planDetail.rejected_at) : '' }}
        </div>
      </el-alert>

      <!-- 批量操作栏（创建人/管理员可见） -->
      <div class="batch-actions" v-if="canEdit && planDetail.status !== 'COMPLETED' && selectedTestCases.length > 0">
        <span style="margin-right: 10px;">{{ $t('testcase.selected') }} {{ selectedTestCases.length }} {{ $t('testcase.itemsUnit') }}</span>
        <el-button
          @click="selectAllInCurrentModule"
          :disabled="moduleFilteredTestcases.length === 0"
        >
          <el-icon><Select /></el-icon>
          全选当前模块
        </el-button>
        <el-button
          type="primary"
          :disabled="removableSelected.length === 0"
          @click="batchUnlinkTestCases"
          :loading="unlinking"
        >
          <el-icon><CircleClose /></el-icon>
          取消关联<template v-if="removableSelected.length > 0">（{{ removableSelected.length }}）</template>
        </el-button>
        <el-button @click="clearSelection">
          取消操作
        </el-button>
      </div>

      <!-- 主内容区域：左侧模块树 + 右侧用例列表 -->
      <div class="execution-content">
        <!-- 左侧模块树 -->
        <div class="module-sidebar">
          <div class="module-header">
            <span>{{ $t('testcase.moduleBelongs') }}</span>
          </div>
          <div class="module-list">
            <div 
              class="module-item" 
              :class="{ active: moduleFilter.module === '' }"
              @click="handleModuleClick('')"
            >
              <span class="module-name">{{ $t('common.all') }}</span>
            </div>
            <div 
              v-for="item in flatModuleTree" 
              :key="item.path"
              class="module-item"
              :class="{ 
                'main-module': item.depth === 0,
                'sub-module': item.depth > 0,
                active: moduleFilter.module === item.path
              }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}"
            >
              <el-icon 
                v-if="item.children && item.children.length > 0"
                class="expand-icon"
                @click.stop="toggleModule(item.path)"
              >
                <ArrowRight v-if="!expandedModules.has(item.path)" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="handleModuleClick(item.path)">
                <span class="module-name">{{ item.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧用例列表 -->
        <div class="testcase-content">
          <div class="table-wrapper">
            <div class="table-container" ref="tableContainerRef">
              <el-table
                ref="tableRef"
                :data="testcaseList"
                style="width: 100%"
                border
                :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }"
                :cell-style="{ padding: '8px 12px' }"
                @selection-change="handleSelectionChange"
                row-key="id"
                :height="tableHeight"
              >
            <el-table-column v-if="isExecutor" type="selection" width="50" align="center" :selectable="isSelectable" />
            <el-table-column prop="case_number" :label="$t('testcase.caseNumber')" width="280" align="center">
              <template #default="{ row }">
                <el-tooltip :content="row.case_number" placement="top" :teleported="true" :show-after="500">
                  <el-tag type="info" size="small" class="ellipsis-tag">{{ row.case_number }}</el-tag>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="module" :label="$t('testcase.moduleBelongs')" width="180" align="center">
              <template #default="{ row }">
                <el-tooltip
                  :content="row.module + (row.sub_module ? ' / ' + row.sub_module : '')"
                  placement="top"
                  effect="dark"
                  :show-after="500"
                  :teleported="true"
                >
                  <span class="single-line-ellipsis">{{ row.module }}{{ row.sub_module ? ' / ' + row.sub_module : '' }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="name" :label="$t('testcase.name')" min-width="200" align="center">
              <template #default="{ row }">
                <el-tooltip
                  :content="row.name"
                  placement="top"
                  effect="dark"
                  :show-after="500"
                  :disabled="!row.name"
                  :teleported="true"
                >
                  <div class="single-line-ellipsis">
                    {{ row.name }}
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column :label="$t('execution.result')" width="120" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.execution_status === 'PENDING'" type="info" size="small">{{ $t('execution.notExecuted') }}</el-tag>
                <el-tag v-else-if="row.execution_status === 'PASS'" type="success" size="small">PASS</el-tag>
                <el-tag v-else-if="row.execution_status === 'FAIL'" type="danger" size="small">FAIL</el-tag>
                <el-tag v-else-if="row.execution_status === 'BLOCK'" type="warning" size="small">BLOCK</el-tag>
                <el-tag v-else-if="row.execution_status === 'NA'" type="info" size="small">NA</el-tag>
                <el-tag v-else-if="row.execution_status === 'NT'" type="info" size="small">NT</el-tag>
                <el-tag v-else-if="row.execution_status === 'ONGOING'" size="small" style="background-color: #e8f0fe; color: #1a73e8; border-color: #c6dafc;">Ongoing</el-tag>
                <span v-else>-</span>
              </template>
            </el-table-column>
            <el-table-column label="执行人" width="100" align="center">
              <template #default="{ row }">
                <el-tooltip v-if="row.execution_executor" :content="row.execution_executor" placement="top" :show-after="500" :teleported="true">
                  <span class="executor-cell">{{ row.execution_executor }}</span>
                </el-tooltip>
                <span v-else style="color: #c0c4cc;">-</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('common.operation')" width="100" align="center" fixed="right" v-if="isExecutor">
              <template #default="{ row }">
                <el-button 
                  type="primary" 
                  size="small"
                  @click="goToExecutionDetail(row.id)"
                >
                  {{ $t('execution.title') }}
                </el-button>
              </template>
            </el-table-column>
            <el-table-column :label="$t('execution.remarks')" min-width="200" align="center">
              <template #default="{ row }">
                <el-tooltip
                  v-if="row.execution_remark"
                  placement="top"
                  effect="dark"
                  :show-after="500"
                  popper-class="remark-tooltip"
                  :teleported="true"
                >
                  <template #content>
                    <div style="max-width: 400px; white-space: pre-wrap; word-break: break-word;" v-html="renderRemarkWithPR(row.execution_remark)"></div>
                  </template>
                  <div class="single-line-ellipsis" v-html="renderRemarkWithPR(row.execution_remark)"></div>
                </el-tooltip>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
            </div>

          <!-- 分页器 -->
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="pagination.page"
              v-model:page-size="pagination.size"
              :page-sizes="[10, 20, 50, 100]"
              :total="pagination.total"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="async () => { await applyFilter(); await nextTick(); scrollToTop(); }"
              @current-change="async () => { await applyFilter(); await nextTick(); scrollToTop(); }"
              background
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 批量执行对话框 -->
    <el-dialog
      v-model="batchDialogVisible"
      :title="$t('execution.batchExecute')"
      width="500px"
    >
      <el-form :model="batchForm" label-width="100px">
        <el-form-item :label="$t('execution.executeResult')">
          <el-tag :type="getResultType(batchForm.result)">{{ getResultText(batchForm.result) }}</el-tag>
        </el-form-item>
        <el-form-item :label="$t('execution.executeRemark')">
          <el-input
            v-model="batchForm.remark"
            type="textarea"
            :rows="4"
            :placeholder="$t('execution.inputRemark')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="confirmBatchExecute">{{ $t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 添加用例对话框 -->
    <el-dialog
      v-model="addTestCaseDialogVisible"
      :title="$t('testplan.linkCases')"
      width="95%"
      top="3vh"
      append-to-body
      :close-on-click-modal="false"
    >
      <div class="testcase-select-container">
        <!-- 左侧模块树 -->
        <div class="module-sidebar-add">
          <!-- 用例库选择器 -->
          <div class="project-filter-section">
            <div class="section-header">
              <span>{{ $t('testcase.caseLibrary') }}</span>
            </div>
            <div class="project-filter-content">
              <ProjectSelector
                v-model="selectedProjectIdList"
                :project-list="teamProjectList"
                @change="handleProjectSelectorChange"
              />
            </div>
          </div>

          <el-divider style="margin: 12px 0;" />

          <div class="module-header-add">
            <span>{{ $t('testplan.module') }}</span>
          </div>
          <div class="module-list-add">
            <div
              class="module-item-add"
              :class="{ active: addTestcaseFilter.module === '' }"
              @click="handleAddModuleClick('')"
            >
              <span class="module-name-add">{{ $t('testplan.allModules') }}</span>
            </div>
            <div
              v-for="item in flatAddModuleTree"
              :key="item.path"
              class="module-item-add"
              :class="{
                'main-module-add': item.depth === 0,
                'sub-module-add': item.depth > 0,
                active: addTestcaseFilter.module === item.path
              }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}"
            >
              <el-icon
                v-if="item.children && item.children.length > 0"
                class="expand-icon-add"
                @click.stop="toggleAddModule(item.path)"
              >
                <ArrowRight v-if="!item.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content-add" @click="handleAddModuleClick(item.path)">
                <span class="module-name-add">{{ item.name }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧用例列表 -->
        <div class="testcase-content-add">
          <div class="testcase-filter-add">
            <el-input
              v-model="addSearchKeyword"
              :placeholder="$t('testplan.searchCaseName')"
              clearable
              style="width: 300px; margin-right: 10px"
              @keyup.enter="handleAddTestcaseSearch"
              @clear="handleAddTestcaseSearch"
            >
              <template #prefix>
                <el-icon><Select /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="handleAddTestcaseSearch">
              搜索
            </el-button>

            <el-button
              @click="selectAllAvailableInModule"
              :disabled="availableTestCases.length === 0"
              style="margin-left: 10px"
              :loading="selectingAllAvailable"
            >
              {{ $t('testplan.selectCurrentModule') }}
            </el-button>

            <div style="flex: 1"></div>

            <el-button
              type="primary"
              :disabled="addSelectedTestCases.length === 0"
              @click="confirmAddTestCases"
              :loading="adding"
            >
              {{ $t('testplan.linkCasesCount', { count: addSelectedTestCases.length }) }}
            </el-button>
          </div>

          <div class="add-table-wrapper">
            <el-table
              ref="addTestcaseTableRef"
              :data="availableTestCases"
              style="width: 100%"
              :height="addDialogTableHeight"
              border
              :header-cell-style="{ background: '#f0f1fb', color: 'var(--text-200)', fontWeight: '600' }"
              v-loading="addTestcaseLoading"
              :element-loading-text="$t('testplan.loading')"
              @selection-change="handleAddTestCaseSelectionChange"
            >
              <el-table-column type="selection" width="50" align="center" />
              <el-table-column prop="case_number" :label="$t('testplan.caseNumber')" width="230" align="center" :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('testplan.caseTitle')" min-width="200" align="left" :show-overflow-tooltip="{ showAfter: 500 }" />
              <el-table-column prop="precondition" :label="$t('testcase.precondition')" min-width="180" align="left" :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <div class="single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="steps" :label="$t('testcase.steps')" min-width="220" align="left">
                <template #default="scope">
                  <el-tooltip
                    placement="top"
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    :teleported="true"
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div
                          v-for="(step, idx) in parseSteps(scope.row.steps)"
                          :key="idx"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ idx + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ step }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseSteps(scope.row.steps).map((s, i) => `${i + 1}. ${s}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="expected_result" :label="$t('testcase.expectedResult')" min-width="220" align="left">
                <template #default="scope">
                  <el-tooltip
                    placement="top"
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    :teleported="true"
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div
                          v-for="(r, idx) in parseExpected(scope.row.expected_result)"
                          :key="idx"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ idx + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ r }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseExpected(scope.row.expected_result).map((s, i) => `${i + 1}. ${s}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="status" label="状态" width="120" align="center">
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">已评审</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">待评审</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">评审未通过</el-tag>
                  <el-tag v-else-if="scope.row.status === 'DEPRECATED'" type="info" size="small">废弃</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="level" label="用例等级" width="100" align="center" />
              <el-table-column label="创建人" width="120" align="center" :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  {{ scope.row.creator_name || '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>

          <el-pagination
            v-model:current-page="addTestcasePagination.page"
            v-model:page-size="addTestcasePagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="addTestcasePagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadAvailableTestCases"
            @current-change="loadAvailableTestCases"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
    </el-dialog>

    <!-- 测试报告信息填写对话框 -->
    <el-dialog
      v-model="reportInfoDialogVisible"
      :title="$t('execution.reportInfo')"
      width="800px"
      append-to-body
      :close-on-click-modal="false"
    >
      <el-form :model="reportInfoForm" label-width="120px" :rules="reportInfoRules" ref="reportInfoFormRef">
        <el-form-item :label="$t('execution.projectNameLabel')" prop="projectName">
          <el-input
            v-model="reportInfoForm.projectName"
            :placeholder="$t('execution.inputProjectName')"
          />
        </el-form-item>
        <el-form-item :label="$t('execution.verifyEnv')" prop="verifyEnv">
          <el-input
            v-model="reportInfoForm.verifyEnv"
            type="textarea"
            :rows="6"
            :placeholder="$t('execution.inputVerifyEnv')"
          />
        </el-form-item>
        <el-form-item :label="$t('execution.releaseNote')" prop="releaseNote">
          <el-input
            v-model="reportInfoForm.releaseNote"
            type="textarea"
            :rows="6"
            :placeholder="$t('execution.inputReleaseNote')"
          />
        </el-form-item>
        <el-form-item :label="t('execution.reportTemplate')">
          <el-select
            v-model="reportInfoForm.reportTemplateId"
            :placeholder="reportTemplates.length > 0 ? t('execution.selectReportTemplate') : t('execution.noReportTemplate')"
            clearable
            :disabled="reportTemplates.length === 0"
            style="width: 100%;"
          >
            <el-option
              v-for="tpl in reportTemplates"
              :key="tpl.id"
              :label="tpl.name + (tpl.is_default ? t('execution.defaultTemplate') : '')"
              :value="tpl.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('execution.riskAssessment')">
          <el-input
            v-model="reportInfoForm.riskAssessment"
            type="textarea"
            :rows="6"
            :placeholder="$t('execution.riskAssessmentPlaceholder')"
          />
        </el-form-item>
        <el-form-item label="备注 Remark">
          <el-input
            v-model="reportInfoForm.reportRemark"
            type="textarea"
            :rows="3"
            placeholder="选填，如有备注请填写"
          />
        </el-form-item>
        <el-form-item :label="$t('execution.zmindAttachment')" v-if="showZmindUpload" :required="zmindFileRequired">
          <div style="width: 100%;">
            <!-- 模式切换 -->
            <div style="margin-bottom: 8px;">
              <el-radio-group v-model="prInputMode" size="small">
                <el-radio-button :value="false">CSV文件上传</el-radio-button>
                <el-radio-button :value="true">PR号查询</el-radio-button>
              </el-radio-group>
            </div>

            <!-- CSV上传模式 -->
            <template v-if="!prInputMode">
              <el-upload
                ref="zmindUploadRef"
                :auto-upload="false"
                :limit="1"
                accept=".csv"
                :on-change="handleZmindFileChange"
                :on-remove="handleZmindFileRemove"
              >
                <el-button type="primary">
                  <el-icon><Upload /></el-icon>
                  {{ $t('execution.selectCsvFile') }}
                </el-button>
                <template #tip>
                  <div class="el-upload__tip">
                    {{ zmindFileRequired ? t('execution.csvTipRequired') : $t('execution.csvTip') }}
                  </div>
                </template>
              </el-upload>
            </template>

            <!-- PR号输入模式 -->
            <template v-else>
              <div style="display: flex; gap: 8px; align-items: flex-start;">
                <el-input
                  v-model="prNumberInput"
                  type="textarea"
                  :rows="2"
                  placeholder="输入PR号，多个用逗号分隔，如：330891,327631,330791"
                  style="flex: 1;"
                  :disabled="fetchingPrData"
                />
                <el-button
                  type="primary"
                  @click="handleFetchPrData"
                  :loading="fetchingPrData"
                  :disabled="!prNumberInput.trim()"
                >
                  查询
                </el-button>
                <el-button
                  v-if="prFetchResult"
                  @click="clearPrData"
                >
                  清除
                </el-button>
              </div>
              <!-- 查询结果提示 -->
              <div v-if="prFetchResult" style="margin-top: 8px;">
                <el-alert
                  :title="`已查询到 ${prFetchResult.total_found} 个PR（共 ${prFetchResult.total_requested} 个）`"
                  :type="prFetchResult.errors && prFetchResult.errors.length > 0 ? 'warning' : 'success'"
                  :closable="false"
                  show-icon
                >
                  <template v-if="prFetchResult.errors && prFetchResult.errors.length > 0">
                    <div style="font-size: 12px; color: #e6a23c; margin-top: 4px;">
                      <div v-for="(err, idx) in prFetchResult.errors" :key="idx">{{ err }}</div>
                    </div>
                  </template>
                </el-alert>
              </div>
              <div class="el-upload__tip" style="margin-top: 4px;">
                通过PR号自动从Zmind查询Issue数据，生成PR统计和Issue列表
              </div>
            </template>
          </div>
        </el-form-item>
        <el-form-item label="MpList附件">
          <el-upload
            ref="mplistUploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.xls,.csv"
            :on-change="handleMplistFileChange"
            :on-remove="handleMplistFileRemove"
          >
            <el-button type="primary">
              <el-icon><Upload /></el-icon>
              选择MpList文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 .xlsx/.xls/.csv 格式，非必填
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="reportInfoDialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button @click="handleSaveReportDraft">{{ $t('common.save') }}</el-button>
        <el-button type="primary" @click="generateReportPreview" :loading="submittingReportInfo">
          生成报告
        </el-button>
      </template>
    </el-dialog>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, onBeforeUnmount, nextTick, watch } from 'vue'
import { useScrollToTop } from '@/composables/useScrollToTop'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Select, CloseBold, Check, Lock, MoreFilled, CircleClose, ArrowRight, ArrowDown, Upload, View, Plus } from '@element-plus/icons-vue'
import { getTestPlanDetail, submitTestPlanForReview, previewTestPlanReport, previewTestPlanReportWithData, addTestCasesToPlan, removeTestCaseFromPlan, batchRemoveTestCasesFromPlan } from '@/api/testplan'
import { getReportTemplates } from '@/api/reportTemplate'
import { getModuleTree } from '@/api/module'
import { getTestCases, getAllTestCaseIds } from '@/api/testcase'
import { createExecution, batchExecute } from '@/api/execution'
import { fetchIssuesByPrNumbers } from '@/api/zmind'
import { useLoadingStore } from '../../stores/loading'
import { useUserRole } from '../../composables/useUserRole'
import { useTeam } from '../../composables/useTeam'
import { getUserRoleInTeam, getTeamProjects } from '../../api/team'
import { getProjects } from '../../api/project'
import { useProjectPreference } from '../../composables/useProjectPreference'
import ProjectSelector from '../../components/ProjectSelector.vue'

const router = useRouter()
const route = useRoute()
const { t } = useI18n()
const loadingStore = useLoadingStore()
const { isSuperAdmin, isAdmin } = useUserRole()
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()
const currentUserRole = ref('member')

// 用例库选择相关（添加用例对话框用，完全复刻详情页实现）
const { selectedProjectIdList, applyPreference, updateSelection } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0
    ? selectedProjectIdList.value
    : teamProjectList.value.map(p => p.id)
})

// 处理用例库选择器变化
let _projectChangeTimer = null
const handleProjectSelectorChange = (ids) => {
  updateSelection(ids)
  addTestcaseFilter.module = ''
  addTestcaseFilter.subModule = ''
  addTestcasePagination.page = 1
  clearTimeout(_projectChangeTimer)
  _projectChangeTimer = setTimeout(() => {
    loadAddModuleTree()
    loadAvailableTestCases()
  }, 300)
}

const planId = route.params.id
const loading = ref(false)
const planDetail = ref({})
const testcaseList = ref([])
const selectedTestCases = ref([])
const tableRef = ref(null)

// 统计数据 - 根据选择的模块计算（基于allTestcases）
const statistics = computed(() => {
  // 获取当前模块筛选后的用例
  let testcases = allTestcases.value
  
  // 根据自动化类型筛选
  if (automationFilter.value === 'auto') {
    testcases = testcases.filter(tc => tc.automation?.toUpperCase() === 'Y')
  } else if (automationFilter.value === 'manual') {
    testcases = testcases.filter(tc => tc.automation?.toUpperCase() !== 'Y')
  }
  
  // 根据模块筛选（路径前缀匹配）
  if (moduleFilter.module) {
    const filterPath = moduleFilter.module
    testcases = testcases.filter(tc => {
      const raw = tc.module || '未分类'
      return raw === filterPath || raw.startsWith(filterPath + '/')
    })
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
const tableContainerRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)
const tableHeight = ref(undefined)

const pagination = reactive({
  page: parseInt(route.query.page) || 1,
  size: 20,
  total: 0
})

// 批量操作相关
const batchDialogVisible = ref(false)
const batchForm = reactive({
  result: '',
  remark: ''
})

// 测试报告信息填写相关
const reportInfoDialogVisible = ref(false)
const reportInfoFormRef = ref(null)
const submittingReportInfo = ref(false)
const reportInfoForm = reactive({
  projectName: '',
  verifyEnv: '',
  releaseNote: '',
  riskAssessment: '',
  reportRemark: '',
  zmindFile: null,
  mplistFile: null,
  reportTemplateId: null
})
const reportTemplates = ref([])

// 当前选中的模板对象
const selectedTemplate = computed(() => {
  if (!reportInfoForm.reportTemplateId) return null
  return reportTemplates.value.find(t => t.id === reportInfoForm.reportTemplateId) || null
})

// 选中模板是否包含 zmind_stats 或 issue_list
const zmindFileRequired = computed(() => {
  const tpl = selectedTemplate.value
  if (!tpl || !tpl.selected_fields) return false
  return tpl.selected_fields.includes('zmind_stats') || tpl.selected_fields.includes('issue_list')
})

// 是否显示 Zmind 上传：没选模板时显示（可选上传），选了模板且包含zmind字段时显示（必传），选了模板但不包含时隐藏
const showZmindUpload = computed(() => {
  const tpl = selectedTemplate.value
  if (!tpl) return true  // 没选模板，显示（可选）
  if (!tpl.selected_fields) return true
  return tpl.selected_fields.includes('zmind_stats') || tpl.selected_fields.includes('issue_list')
})

// 根据模板的 criteria_config.rules 推导 include_pr_closed
// 有 pr_closure_rate 规则 → 需要统计 PR closed (include_pr_closed=1)
// 只有 open_pr_count 规则 → 不需要 (include_pr_closed=0)
// 都没有 → 默认0
const templateIncludePrClosed = computed(() => {
  const tpl = selectedTemplate.value
  if (!tpl || !tpl.criteria_config || !tpl.criteria_config.rules) return 0
  const hasClosureRate = tpl.criteria_config.rules.some(r => r.metric === 'pr_closure_rate')
  return hasClosureRate ? 1 : 0
})
const reportInfoRules = {
  projectName: [{ required: true, message: t('execution.inputProjectName'), trigger: 'blur' }],
  verifyEnv: [{ required: true, message: t('execution.inputVerifyEnv'), trigger: 'blur' }],
  releaseNote: [{ required: true, message: t('execution.inputReleaseNote'), trigger: 'blur' }]
}

// 模块相关
const moduleTree = ref([])
const moduleFilter = reactive({
  module: '',
  subModule: ''
})

// 新增：状态筛选和固定相关
const isStatsFixed = ref(false)
const statsWrapperRef = ref(null)
const statusFilter = ref(null)
const automationFilter = ref(route.query.automationFilter || '')
const allTestcases = ref([])  // 保存所有用例数据

// 过滤后的模块树 - 直接从用例数据构建，不依赖模块API
const filteredModuleTree = computed(() => {
  if (!allTestcases.value || allTestcases.value.length === 0) {
    return []
  }
  
  // 从用例的 module 字段（路径格式如 "主模块/子模块/子子模块"）构建多级树
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
  
  // 递归转换 Map 为数组
  const toArray = (map) => {
    return Array.from(map.values())
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'))
      .map(node => ({
        name: node.name,
        path: node.path,
        expanded: false,
        children: node.children.size > 0 ? toArray(node.children) : []
      }))
  }
  
  return toArray(root.children)
})

// 判断当前用户是否是执行人（管理员、项目组负责人、组织负责人或执行人）
const isExecutor = computed(() => {
  if (isSuperAdmin.value || isAdmin.value) return true
  if (currentUserRole.value === 'leader' || currentUserRole.value === 'org_manager') return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  const executors = planDetail.value.executors || []
  return executors.some(e => e.id === currentUserId)
})

// 权限：是否可以编辑（添加/取消关联用例）— 仅创建人或管理员
const canEdit = computed(() => {
  if (isAdmin.value || isSuperAdmin.value) return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return planDetail.value.created_by === currentUserId
})

// 选中的可取消关联用例（仅未执行 / NT / ONGOING 可以取消）
const removableSelected = computed(() => {
  return selectedTestCases.value.filter(tc =>
    !tc.execution_status ||
    tc.execution_status === 'PENDING' ||
    tc.execution_status === 'NT' ||
    tc.execution_status === 'ONGOING'
  )
})

// ===== 添加用例对话框相关 =====
const addTestCaseDialogVisible = ref(false)
const adding = ref(false)
const availableTestCases = ref([])
const addSelectedTestCases = ref([])
const addSearchKeyword = ref('')
const addTestcaseLoading = ref(false)
const addTestcaseTableRef = ref(null)
const selectingAllAvailable = ref(false)
const addTestcaseFilter = reactive({ module: '', subModule: '' })
const addTestcasePagination = reactive({ page: 1, size: 20, total: 0 })
const addDialogTableHeight = ref('calc(100vh - 350px)')
const addModuleTree = ref([])
const isRestoringAddSelection = ref(false)

// 对话框内模块树扁平化
const flatAddModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (node.expanded && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(addModuleTree.value, 0)
  return result
})

const loadAddModuleTree = async () => {
  if (currentProjectIds.value.length === 0) return
  try {
    const projectParam = currentProjectIds.value.join(',')
    const res = await getModuleTree(projectParam)
    if (res.code === 200) {
      const addExpanded = (nodes) => nodes.map(n => ({
        ...n,
        expanded: false,
        children: n.children ? addExpanded(n.children) : []
      }))
      addModuleTree.value = addExpanded(res.data || [])
    }
  } catch (error) {
    console.error('加载模块树失败', error)
  }
}

const toggleAddModule = (modulePath) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === modulePath) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(addModuleTree.value)
}

const handleAddModuleClick = (modulePath) => {
  addTestcaseFilter.module = modulePath
  addTestcaseFilter.subModule = ''
  addTestcasePagination.page = 1
  loadAvailableTestCases()
}

// 搜索用例（重置到第一页）
const handleAddTestcaseSearch = () => {
  addTestcasePagination.page = 1
  loadAvailableTestCases()
}

// 打开添加用例对话框（完全复刻详情页实现）
const openAddTestCaseDialog = async () => {
  addTestCaseDialogVisible.value = true
  addSearchKeyword.value = ''
  addTestcaseFilter.module = ''
  addTestcaseFilter.subModule = ''
  addTestcasePagination.page = 1
  addSelectedTestCases.value = []

  // 加载当前计划所属团队的用例库
  // 重要：必须用 planDetail.team_id（计划实际归属），不能用全局 currentTeam
  // 否则 admin 账号查看其他团队的计划时，会加载错团队的用例库
  const planTeamId = planDetail.value.team_id
  if (planTeamId) {
    // 如果全局 currentTeam 刚好就是本计划团队，复用已加载的数据
    if (currentTeam.value?.id === planTeamId && teamProjects.value.length > 0) {
      // noop - 已加载
    } else {
      // 否则直接按计划 team_id 拉取（不修改全局 currentTeam，避免影响其他页面）
      try {
        const res = await getTeamProjects(planTeamId)
        teamProjects.value = res.data || []
      } catch (e) {
        console.error('加载用例库列表失败:', e)
      }
    }
  } else if (currentTeam.value && teamProjects.value.length === 0) {
    // 兜底：如果计划没 team_id（后端未更新/旧数据），回退到当前 team
    await loadTeamProjects()
  }

  // 关键补丁：计划可能关联了多个用例库的用例（跨用例库）
  // 如果计划涉及的用例库不在 team_projects 里，补齐它们
  const planCaseProjectIds = planDetail.value.test_case_project_ids || []
  if (planCaseProjectIds.length > 0) {
    const existingIds = new Set(teamProjects.value.map(p => p.id))
    const missingIds = planCaseProjectIds.filter(id => !existingIds.has(id))
    if (missingIds.length > 0) {
      try {
        const res = await getProjects({ page: 1, size: 1000 })
        const allProjects = res.data?.records || []
        const idToProject = new Map(allProjects.map(p => [p.id, p]))
        const missing = missingIds
          .map(id => idToProject.get(id))
          .filter(Boolean)
          .map(p => ({ id: p.id, name: p.name }))
        if (missing.length > 0) {
          teamProjects.value = [...teamProjects.value, ...missing]
        }
      } catch (e) {
        // 若拉不到具体 name，兜底用 ID 占位，保证用例库 ID 能参与筛选
        const missing = missingIds.map(id => ({ id, name: `用例库 #${id}` }))
        teamProjects.value = [...teamProjects.value, ...missing]
      }
    }
  }

  // 应用用户偏好（默认选中全部用例库）
  if (teamProjectList.value.length > 0) {
    applyPreference(teamProjectList.value)
  }

  // 等待 Vue 渲染完成
  await nextTick()

  // 兜底：如果还是没拿到用例库，用 project_id 构造一个
  if (currentProjectIds.value.length === 0 && planDetail.value.project_id) {
    teamProjects.value = [{
      id: planDetail.value.project_id,
      name: planDetail.value.project_name || '当前用例库'
    }]
    applyPreference(teamProjectList.value)
    await nextTick()
  }

  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('无法获取用例库信息，请联系管理员')
    return
  }

  // 加载模块树
  await loadAddModuleTree()

  // 加载用例列表
  await loadAvailableTestCases()
}

// 加载可添加的测试用例（完全复刻详情页实现）
const loadAvailableTestCases = async () => {
  if (currentProjectIds.value.length === 0) {
    return
  }

  addTestcaseLoading.value = true
  try {
    const params = {
      page: addTestcasePagination.page,
      size: addTestcasePagination.size,
      project_ids: currentProjectIds.value.join(','),
      keyword: addSearchKeyword.value || undefined,
      module: (addTestcaseFilter.subModule ? `${addTestcaseFilter.module}/${addTestcaseFilter.subModule}` : addTestcaseFilter.module) || undefined,
      status_in: 'REVIEWED,PENDING,REJECTED',
      exclude_testplan_id: planId
    }

    const res = await getTestCases(params)
    if (res.code === 200) {
      availableTestCases.value = res.data.records
      addTestcasePagination.total = res.data.total

      // 恢复之前选中的用例
      await nextTick()
      isRestoringAddSelection.value = true
      if (addTestcaseTableRef.value) {
        addTestcaseTableRef.value.clearSelection()
      }
      if (addTestcaseTableRef.value && addSelectedTestCases.value.length > 0) {
        availableTestCases.value.forEach(row => {
          if (addSelectedTestCases.value.some(selected => selected.id === row.id)) {
            addTestcaseTableRef.value.toggleRowSelection(row, true)
          }
        })
      }
      await nextTick()
      isRestoringAddSelection.value = false
    }
  } catch (error) {
    ElMessage.error('加载用例列表失败')
  } finally {
    addTestcaseLoading.value = false
  }
}

const handleAddTestCaseSelectionChange = (selection) => {
  if (isRestoringAddSelection.value) return
  const currentPageIds = new Set(availableTestCases.value.map(tc => tc.id))
  const otherPagesSelected = addSelectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))
  addSelectedTestCases.value = [...otherPagesSelected, ...selection]
}

// 在对话框内全选当前模块的可用用例
const selectAllAvailableInModule = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('请先选择用例库')
    return
  }
  selectingAllAvailable.value = true
  try {
    const params = {
      project_ids: currentProjectIds.value.join(','),
      keyword: addSearchKeyword.value || undefined,
      module: (addTestcaseFilter.subModule ? `${addTestcaseFilter.module}/${addTestcaseFilter.subModule}` : addTestcaseFilter.module) || undefined,
      status_in: 'REVIEWED,PENDING,REJECTED',
      exclude_testplan_id: planId
    }
    const res = await getAllTestCaseIds(params)
    if (res.code === 200) {
      const all = res.data.records
      const existingIds = new Set(addSelectedTestCases.value.map(tc => tc.id))
      const newOnes = all.filter(tc => !existingIds.has(tc.id))
      addSelectedTestCases.value = [...addSelectedTestCases.value, ...newOnes]
      await nextTick()
      if (addTestcaseTableRef.value) {
        const selectedIds = new Set(addSelectedTestCases.value.map(tc => tc.id))
        availableTestCases.value.forEach(row => {
          addTestcaseTableRef.value.toggleRowSelection(row, selectedIds.has(row.id))
        })
      }
      ElMessage.success(`已选择 ${all.length} 条用例`)
    }
  } catch (e) {
    ElMessage.error('全选失败')
  } finally {
    selectingAllAvailable.value = false
  }
}

// 确认添加用例
const confirmAddTestCases = async () => {
  if (addSelectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择用例')
    return
  }

  // 校验：待评审/评审未通过 不能添加
  const pendingList = addSelectedTestCases.value.filter(tc => tc.status === 'PENDING')
  const rejectedList = addSelectedTestCases.value.filter(tc => tc.status === 'REJECTED')
  if (pendingList.length > 0 || rejectedList.length > 0) {
    let message = ''
    if (pendingList.length > 0 && rejectedList.length > 0) {
      message = `选择的用例中有 ${pendingList.length} 个待评审用例和 ${rejectedList.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    } else if (pendingList.length > 0) {
      message = `选择的用例中有 ${pendingList.length} 个待评审用例，需要先完成评审后再进行关联。`
    } else {
      message = `选择的用例中有 ${rejectedList.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    }
    ElMessageBox.alert(message, '提示', { confirmButtonText: '我知道了', type: 'warning' })
    return
  }

  adding.value = true
  try {
    const ids = addSelectedTestCases.value.map(tc => tc.id)
    const res = await addTestCasesToPlan(planId, { testcase_ids: ids })
    if (res.code === 200) {
      ElMessage.success(`成功添加 ${res.data.added} 个用例`)
      addTestCaseDialogVisible.value = false
      await loadPlanDetail()
      await loadTestCases()
    }
  } catch (e) {
    ElMessage.error('添加用例失败')
  } finally {
    adding.value = false
  }
}

// ===== 批量取消关联 =====
const unlinking = ref(false)

// 当前模块筛选下的用例（用于"全选当前模块"）
const moduleFilteredTestcases = computed(() => {
  let list = allTestcases.value
  if (automationFilter.value === 'auto') {
    list = list.filter(tc => tc.automation?.toUpperCase() === 'Y')
  } else if (automationFilter.value === 'manual') {
    list = list.filter(tc => tc.automation?.toUpperCase() !== 'Y')
  }
  if (moduleFilter.module) {
    const filterPath = moduleFilter.module
    list = list.filter(tc => {
      const raw = tc.module || '未分类'
      return raw === filterPath || raw.startsWith(filterPath + '/')
    })
  }
  return list
})

// 全选当前模块（对已关联用例列表，跨分页持久化）
const selectAllInCurrentModule = async () => {
  const list = moduleFilteredTestcases.value
  if (list.length === 0) {
    ElMessage.warning('当前模块下没有用例')
    return
  }
  // 把当前模块的所有用例（不分页）加入已选集合，去重
  const existingIds = new Set(selectedTestCases.value.map(tc => tc.id))
  const newOnes = list.filter(tc => !existingIds.has(tc.id))
  selectedTestCases.value = [...selectedTestCases.value, ...newOnes]

  // 同步当前可见页的勾选状态（其他页会在切换时自动恢复）
  await nextTick()
  isRestoringSelection.value = true
  if (tableRef.value) {
    const selectedIds = new Set(selectedTestCases.value.map(tc => tc.id))
    testcaseList.value.forEach(row => {
      if (selectedIds.has(row.id)) {
        tableRef.value.toggleRowSelection(row, true)
      }
    })
  }
  await nextTick()
  isRestoringSelection.value = false

  ElMessage.success(`已选中当前模块 ${list.length} 条用例`)
}

// 批量取消关联（使用后端单次事务接口）
const batchUnlinkTestCases = async () => {
  const removable = removableSelected.value
  if (removable.length === 0) {
    ElMessage.warning('没有可取消关联的用例（已执行的用例不能取消）')
    return
  }
  const executedSelected = selectedTestCases.value.length - removable.length
  let confirmMsg = `确定要取消关联选中的 ${removable.length} 个用例吗？`
  if (executedSelected > 0) {
    confirmMsg += `\n（有 ${executedSelected} 个已执行的用例将被跳过）`
  }
  try {
    await ElMessageBox.confirm(confirmMsg, '批量取消关联', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
  } catch {
    return
  }

  unlinking.value = true
  try {
    const ids = removable.map(tc => tc.id)
    let removed = 0
    let skippedExecuted = 0
    try {
      // 优先使用批量接口（单次事务）
      const res = await batchRemoveTestCasesFromPlan(planId, ids)
      if (res.code === 200) {
        removed = res.data?.removed || 0
        skippedExecuted = res.data?.skipped_executed || 0
      } else {
        throw new Error('batch api returned non-200')
      }
    } catch (batchErr) {
      // 降级：后端未部署批量接口时，逐条调用单删接口
      console.warn('批量接口不可用，降级为逐条删除:', batchErr?.message || batchErr)
      for (const id of ids) {
        try {
          await removeTestCaseFromPlan(planId, id)
          removed++
        } catch {
          // 已执行的用例后端会 404 或 400，记为跳过
          skippedExecuted++
        }
      }
    }

    if (skippedExecuted > 0) {
      ElMessage.success(`成功取消关联 ${removed} 个用例，跳过 ${skippedExecuted} 个已执行的用例`)
    } else {
      ElMessage.success(`成功取消关联 ${removed} 个用例`)
    }
    // 清空选中 + 强制刷新数据
    selectedTestCases.value = []
    if (tableRef.value) tableRef.value.clearSelection()
    await loadPlanDetail()
    await loadTestCases(false)
  } catch (e) {
    console.error(e)
    ElMessage.error('批量取消关联失败')
  } finally {
    unlinking.value = false
  }
}

// 清空当前选择（"取消操作"按钮）
const clearSelection = () => {
  selectedTestCases.value = []
  if (tableRef.value) {
    tableRef.value.clearSelection()
  }
}

// 是否可以完成测试 - 基于全部用例计算，不受模块筛选影响
const canComplete = computed(() => {
  // 计算全部用例中已执行的数量（ONGOING不算已执行）
  const allExecuted = allTestcases.value.filter(tc => 
    tc.execution_status && tc.execution_status !== 'PENDING' && tc.execution_status !== 'ONGOING'
  ).length
  return allExecuted === allTestcases.value.length && allTestcases.value.length > 0
})

// 全部用例的已执行数量（用于提示信息）
const allExecutedCount = computed(() => {
  return allTestcases.value.filter(tc => 
    tc.execution_status && tc.execution_status !== 'PENDING' && tc.execution_status !== 'ONGOING'
  ).length
})


// 格式化审核不通过时间
const formatRejectTime = (isoStr) => {
  if (!isoStr) return ''
  try {
    const d = new Date(isoStr)
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch { return isoStr }
}

// 加载测试计划详情
const loadPlanDetail = async () => {
  try {
    const res = await getTestPlanDetail(planId, { all_cases: true })
    if (res.code === 200) {
      planDetail.value = res.data
    }
  } catch (error) {
    ElMessage.error(t('execution.loadPlanFailed'))
  }
}

// 加载测试用例列表 - 使用全部用例数据
const loadTestCases = async (showLoading = true) => {
  if (showLoading) {
    loadingStore.showLoading()
    loading.value = true
  }
try {
    // 使用 all_test_cases（后端返回的完整用例数据）
    const allCases = planDetail.value.all_test_cases
    if (allCases) {
      allTestcases.value = allCases
    } else {
      // 如果 all_test_cases 不存在，使用 test_cases（备用）
      allTestcases.value = planDetail.value.test_cases || []
    }
        
    // 应用筛选（包含排序逻辑）
    applyFilter()
  } catch (error) {
    ElMessage.error(t('execution.loadCasesFailed'))
  } finally {
    if (showLoading) {
      loadingStore.hideLoading()
      loading.value = false
    }
  }
}

// 执行单个用例
const executeTestCase = async (row, result) => {
  try {
    const isRemarkRequired = result === 'NA' || result === 'NT'
    const promptTitle = isRemarkRequired ? t('execution.executeTestRemarkRequired', { result: getResultText(result) }) : t('execution.executeTest')
    const inputPlaceholder = isRemarkRequired ? t('execution.inputRemarkRequired') : t('execution.inputRemark')
    
    await ElMessageBox.prompt(inputPlaceholder, promptTitle, {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      inputType: 'textarea',
      inputValidator: (value) => {
        if (isRemarkRequired && (!value || value.trim() === '')) {
          return t('execution.remarkRequired', { result: getResultText(result) })
        }
        return true
      }
    }).then(async ({ value }) => {
      await createExecution({
        test_plan_id: planId,
        test_case_id: row.id,
        result: result,
        remark: value || ''
      })
      
      ElMessage.success(t('execution.executeSuccess'))
      await loadPlanDetail()
      await loadTestCases()
    })
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('execution.executeFailed'))
    }
  }
}

// 显示批量执行对话框
const showBatchExecuteDialog = (result) => {
  batchForm.result = result
  batchForm.remark = ''
  batchDialogVisible.value = true
}

// 确认批量执行
const confirmBatchExecute = async () => {
  try {
    await batchExecute({
      test_plan_id: planId,
      test_case_ids: selectedTestCases.value.map(tc => tc.id),
      result: batchForm.result
    })
    
    ElMessage.success(t('execution.batchExecuteSuccess', { count: selectedTestCases.value.length }))
    batchDialogVisible.value = false
    selectedTestCases.value = []
    
    await loadPlanDetail()
    await loadTestCases()
  } catch (error) {
    ElMessage.error(t('execution.batchExecuteFailed'))
  }
}

// 报告表单用户偏好 - localStorage key
const getReportPrefKey = () => {
  const userId = JSON.parse(localStorage.getItem('user') || '{}').id || 0
  return `report_form_pref_${userId}`
}

const loadReportFormPref = () => {
  try {
    const saved = localStorage.getItem(getReportPrefKey())
    if (saved) return JSON.parse(saved)
  } catch (e) { /* ignore */ }
  return null
}

const saveReportFormPref = () => {
  try {
    localStorage.setItem(getReportPrefKey(), JSON.stringify({
      projectName: reportInfoForm.projectName,
      verifyEnv: reportInfoForm.verifyEnv,
      releaseNote: reportInfoForm.releaseNote,
      riskAssessment: reportInfoForm.riskAssessment,
      reportRemark: reportInfoForm.reportRemark,
      prNumbers: prNumberInput.value,
      reportTemplateId: reportInfoForm.reportTemplateId
    }))
  } catch (e) { /* ignore */ }
}

// 显示测试报告信息填写对话框
const showReportInfoDialog = async () => {
  // 重置表单，回填用户偏好
  const pref = loadReportFormPref()
  reportInfoForm.projectName = pref?.projectName || planDetail.value.name || ''
  reportInfoForm.verifyEnv = pref?.verifyEnv || ''
  reportInfoForm.releaseNote = pref?.releaseNote || ''
  reportInfoForm.riskAssessment = pref?.riskAssessment || ''
  reportInfoForm.reportRemark = pref?.reportRemark || ''
  reportInfoForm.zmindFile = null
  reportInfoForm.mplistFile = null
  reportInfoForm.reportTemplateId = pref?.reportTemplateId || null
  prInputMode.value = pref?.prNumbers ? true : false
  prNumberInput.value = pref?.prNumbers || ''
  prFetchResult.value = null
  reportTemplates.value = []
  reportInfoDialogVisible.value = true

  // 加载报告模板列表
  if (currentTeam.value?.id) {
    try {
      const res = await getReportTemplates(currentTeam.value.id)
      if (res.code === 200) {
        reportTemplates.value = res.data || []
        // 若已保存的模板仍存在，保持选中；否则回退到默认模板
        const savedTplValid = reportInfoForm.reportTemplateId &&
          reportTemplates.value.some(t => t.id === reportInfoForm.reportTemplateId)
        if (!savedTplValid) {
          const defaultTpl = reportTemplates.value.find(t => t.is_default)
          reportInfoForm.reportTemplateId = defaultTpl ? defaultTpl.id : null
        }
      }
    } catch (e) {
      console.error('Failed to load report templates:', e)
    }
  }
}

// 保存草稿（只保存文本/模板/PR号到本地，不提交审核，不关闭对话框）
const handleSaveReportDraft = () => {
  saveReportFormPref()
  ElMessage.success(t('common.saveSuccess') || '已保存')
}

// Zmind CSV文件选择
const zmindUploadRef = ref(null)
const handleZmindFileChange = (file) => {
  reportInfoForm.zmindFile = file.raw
  // 清除PR查询数据（两种模式互斥）
  prFetchResult.value = null
  prNumberInput.value = ''
}
const handleZmindFileRemove = () => {
  reportInfoForm.zmindFile = null
}
const mplistUploadRef = ref(null)

// PR号输入相关
const prNumberInput = ref('')
const fetchingPrData = ref(false)
const prFetchResult = ref(null)  // { stats, issues, errors }
const prInputMode = ref(false)  // true=PR号输入模式, false=CSV上传模式

const handleFetchPrData = async () => {
  if (!prNumberInput.value.trim()) {
    ElMessage.warning('请输入PR号')
    return
  }
  fetchingPrData.value = true
  prFetchResult.value = null
  try {
    const res = await fetchIssuesByPrNumbers(prNumberInput.value.trim())
    if (res.code === 200) {
      prFetchResult.value = res.data
      const { total_found, total_requested, errors } = res.data
      if (errors && errors.length > 0) {
        ElMessage.warning(`查询完成：${total_found}/${total_requested} 个PR查询成功，${errors.length} 个失败`)
      } else {
        ElMessage.success(`查询完成：${total_found} 个PR`)
      }
    } else {
      ElMessage.error(res.message || '查询失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '查询PR失败')
  } finally {
    fetchingPrData.value = false
  }
}

const clearPrData = () => {
  prNumberInput.value = ''
  prFetchResult.value = null
}

const switchToPrInput = () => {
  prInputMode.value = true
  reportInfoForm.zmindFile = null
  if (zmindUploadRef.value) {
    zmindUploadRef.value.clearFiles()
  }
}

const switchToCsvUpload = () => {
  prInputMode.value = false
  prNumberInput.value = ''
  prFetchResult.value = null
}
const handleMplistFileChange = (file) => {
  reportInfoForm.mplistFile = file.raw
}
const handleMplistFileRemove = () => {
  reportInfoForm.mplistFile = null
}

// 提交测试报告信息
// 生成报告预览（替代原来的直接提交）
const generateReportPreview = async () => {
  if (!reportInfoFormRef.value) return
  
  await reportInfoFormRef.value.validate(async (valid) => {
    if (valid) {
      // 检查模板要求的 Zmind 附件
      if (zmindFileRequired.value && !reportInfoForm.zmindFile && !prFetchResult.value) {
        ElMessage.warning(t('execution.zmindFileRequired'))
        return
      }
      submittingReportInfo.value = true
      try {
        // 使用FormData提交到预览接口
        const formData = new FormData()
        formData.append('project_name', reportInfoForm.projectName)
        formData.append('verify_env', reportInfoForm.verifyEnv)
        formData.append('release_note', reportInfoForm.releaseNote)
        formData.append('risk_assessment', reportInfoForm.riskAssessment || '')
        formData.append('report_remark', reportInfoForm.reportRemark || '')
        formData.append('include_pr_closed', templateIncludePrClosed.value)
        
        if (reportInfoForm.reportTemplateId) {
          formData.append('report_template_id', reportInfoForm.reportTemplateId)
        }
        
        if (reportInfoForm.zmindFile) {
          formData.append('zmind_file', reportInfoForm.zmindFile)
        }
        
        if (prFetchResult.value && prFetchResult.value.issues && prFetchResult.value.issues.length > 0) {
          formData.append('zmind_pr_data', JSON.stringify(prFetchResult.value))
        }
        
        if (reportInfoForm.mplistFile) {
          formData.append('mplist_file', reportInfoForm.mplistFile)
        }
        
        // 调用预览接口获取完整报告数据
        const res = await previewTestPlanReportWithData(planId, formData)
        
        if (res.code === 200) {
          // 保存表单偏好
          saveReportFormPref()
          // 将预览数据存入sessionStorage供预览页面使用
          sessionStorage.setItem('submitPreviewData', JSON.stringify(res.data))
          // 将FormData存到window上，供确认提交时复用（File对象无法序列化到sessionStorage）
          const submitFormData = new FormData()
          submitFormData.append('project_name', reportInfoForm.projectName)
          submitFormData.append('verify_env', reportInfoForm.verifyEnv)
          submitFormData.append('release_note', reportInfoForm.releaseNote)
          submitFormData.append('risk_assessment', reportInfoForm.riskAssessment || '')
          submitFormData.append('report_remark', reportInfoForm.reportRemark || '')
          submitFormData.append('include_pr_closed', templateIncludePrClosed.value)
          if (reportInfoForm.reportTemplateId) {
            submitFormData.append('report_template_id', reportInfoForm.reportTemplateId)
          }
          if (reportInfoForm.zmindFile) {
            submitFormData.append('zmind_file', reportInfoForm.zmindFile)
          }
          if (prFetchResult.value && prFetchResult.value.issues && prFetchResult.value.issues.length > 0) {
            submitFormData.append('zmind_pr_data', JSON.stringify(prFetchResult.value))
          }
          if (reportInfoForm.mplistFile) {
            submitFormData.append('mplist_file', reportInfoForm.mplistFile)
          }
          window.__submitReviewFormData = submitFormData
          window.__submitReviewPlanId = planId
          // 标记从预览返回时需要重新打开对话框
          sessionStorage.setItem('reopenReportDialog', '1')
          // 关闭对话框并跳转到预览页面
          reportInfoDialogVisible.value = false
          router.push(`/testplans/${planId}/submit-preview`)
        } else {
          ElMessage.error(res.message || '生成报告失败')
        }
      } catch (error) {
        ElMessage.error('生成报告失败')
      } finally {
        submittingReportInfo.value = false
      }
    }
  })
}

// 提交审核
const submitForReview = async () => {
  console.log('submitForReview clicked')
  try {
    await ElMessageBox.confirm(
      t('execution.confirmSubmitMsg'),
      t('execution.confirmSubmit'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    // 弹出测试报告信息填写对话框
    showReportInfoDialog()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('execution.operationFailed'))
    }
  }
}

// 跳转到执行详情
const goToExecutionDetail = (testcaseId) => {
  // 构建查询参数，传递当前的筛选状态和页码
  const query = {}
  if (statusFilter.value) {
    query.statusFilter = statusFilter.value
  }
  if (automationFilter.value) {
    query.automationFilter = automationFilter.value
  }
  if (moduleFilter.module) {
    query.module = moduleFilter.module
  }
  // 传递当前页码
  query.page = pagination.page
  
  router.push({
    path: `/testplans/${planId}/testcases/${testcaseId}`,
    query
  })
}

// 加载模块树
const loadModuleTree = async () => {
  if (!planDetail.value.project_id) return
  
  try {
    const res = await getModuleTree(planDetail.value.project_id)
    if (res.code === 200) {
      const addExpanded = (nodes) => nodes.map(n => ({
        ...n,
        expanded: false,
        children: n.children ? addExpanded(n.children) : []
      }))
      moduleTree.value = addExpanded(res.data || [])
    }
  } catch (error) {
    console.error('Load module tree failed:', error)
  }
}

// 扁平化模块树（基于用例数据构建的filteredModuleTree）
const flatModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (expandedModules.value.has(node.path) && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(filteredModuleTree.value, 0)
  return result
})

// 切换模块展开/收起
const expandedModules = ref(new Set())

const toggleModule = (modulePath) => {
  if (expandedModules.value.has(modulePath)) {
    expandedModules.value.delete(modulePath)
  } else {
    expandedModules.value.add(modulePath)
  }
}

// 应用筛选和分页
const applyFilter = () => {
  let filtered = [...allTestcases.value]
  
  // 根据自动化类型筛选
  if (automationFilter.value === 'auto') {
    filtered = filtered.filter(tc => tc.automation?.toUpperCase() === 'Y')
  } else if (automationFilter.value === 'manual') {
    filtered = filtered.filter(tc => tc.automation?.toUpperCase() !== 'Y')
  }
  
  // 根据模块筛选（路径前缀匹配，支持任意层级）
  if (moduleFilter.module) {
    const filterPath = moduleFilter.module
    filtered = filtered.filter(tc => {
      const raw = tc.module || '未分类'
      return raw === filterPath || raw.startsWith(filterPath + '/')
    })
  }
  
  // 根据状态筛选
  if (statusFilter.value === 'PENDING') {
    filtered = filtered.filter(tc => tc.execution_status === 'PENDING' || tc.execution_status === 'ONGOING')
  } else if (statusFilter.value === 'EXECUTED') {
    filtered = filtered.filter(tc => tc.execution_status !== 'PENDING' && tc.execution_status !== 'ONGOING')
  } else if (statusFilter.value) {
    filtered = filtered.filter(tc => tc.execution_status === statusFilter.value)
  }
  
  // 排序
  filtered = sortTestCases(filtered, statusFilter.value, moduleFilter)
  
  // 更新总数
  pagination.total = filtered.length
  
  // 分页
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  testcaseList.value = filtered.slice(start, end)
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

const sortTestCases = (cases, status, moduleFilter) => {
  const isAllCases = !status || status === 'EXECUTED'
  const isPending = status === 'PENDING'
  const needModuleSort = !status || isPending
  
  const pending = []
  const executed = []
  cases.forEach(tc => {
    if (tc.execution_status === 'PENDING' || tc.execution_status === 'ONGOING') {
      pending.push(tc)
    } else {
      executed.push(tc)
    }
  })
  
  const sortByModuleNumber = (arr) => {
    return [...arr].sort((a, b) => {
      const aModule = a.module || '未分类'
      const bModule = b.module || '未分类'
      
      if (moduleFilter && moduleFilter.module) {
        return naturalSort(a.case_number, b.case_number)
      }
      
      if (aModule !== bModule) {
        return aModule.localeCompare(bModule, 'zh-CN')
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
  
  if (isAllCases) {
    return [...sortByModuleNumber(pending), ...sortByTime(executed)]
  }
  
  if (needModuleSort) {
    return sortByModuleNumber(cases)
  } else {
    return sortByTime(cases)
  }
}

// 状态筛选
const filterByStatus = (status) => {
  statusFilter.value = status
  pagination.page = 1
  applyFilter()
}

// 自动化类型筛选
const handleAutomationFilterChange = () => {
  pagination.page = 1
  applyFilter()
}

// 处理模块点击 — 统一用 path 过滤
const handleModuleClick = (modulePath) => {
  moduleFilter.module = modulePath
  moduleFilter.subModule = ''
  pagination.page = 1
  applyFilter()
}

// 返回
const goBack = () => {
  router.push('/testplans')
}

// 选择变化 — 跨分页保留（当前页切换选中时只增删对应 ID，不清空其他页的已选）
const isRestoringSelection = ref(false)
const handleSelectionChange = (selection) => {
  // 恢复选中状态期间跳过，避免把"未显示的已选用例"误删
  if (isRestoringSelection.value) return
  const currentPageIds = new Set(testcaseList.value.map(tc => tc.id))
  // 保留不在当前页的所有已选
  const otherPagesSelected = selectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))
  // 合并当前页最新选中
  selectedTestCases.value = [...otherPagesSelected, ...selection]
}

// 当前页重新渲染后，恢复已选用例的勾选状态（跨分页保持）
const restoreSelectionOnTable = async () => {
  if (!tableRef.value || selectedTestCases.value.length === 0) return
  await nextTick()
  isRestoringSelection.value = true
  try {
    const selectedIds = new Set(selectedTestCases.value.map(tc => tc.id))
    testcaseList.value.forEach(row => {
      if (selectedIds.has(row.id)) {
        tableRef.value.toggleRowSelection(row, true)
      }
    })
  } finally {
    await nextTick()
    isRestoringSelection.value = false
  }
}

// 表格数据变化时恢复勾选
watch(() => testcaseList.value, () => {
  restoreSelectionOnTable()
})

// 是否可选择
const isSelectable = (row) => {
  return row.execution_status === 'PENDING'
}

// 获取结果类型
const getResultType = (result) => {
  const typeMap = {
    PASS: 'success',
    FAIL: 'danger',
    BLOCK: 'warning',
    NA: 'info',
    NT: 'info'
  }
  return typeMap[result] || 'info'
}

// 获取结果文本
const getResultText = (result) => {
  const textMap = {
    PASS: t('execution.statusPassed'),
    FAIL: t('execution.statusFailed'),
    BLOCK: t('execution.blocked'),
    NA: 'NA',
    NT: 'NT'
  }
  return textMap[result] || result
}

// 将备注中的PR号转为可点击链接（匹配 PR 后紧跟恰好6位数字）
const renderRemarkWithPR = (text) => {
  if (!text) return ''
  const escaped = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
  return escaped.replace(/PR\s*[#＃]?\s*(\d{6})(?!\d)/gi, (match, prId) => {
    return `<a href="https://zmind.whaletv.com/issues/${prId}" target="_blank" rel="noopener noreferrer" class="pr-link-inline" onclick="event.stopPropagation()">${match}</a>`
  })
}

// 解析步骤文本
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

// 滚动监听
const handleScroll = () => {
  if (statsWrapperRef.value) {
    const rect = statsWrapperRef.value.getBoundingClientRect()
    isStatsFixed.value = rect.top <= 0
  }
}

// 同步表头和表体的滚动
const syncTableScroll = () => {
  if (tableRef.value) {
    const bodyWrapper = tableRef.value.$el.querySelector('.el-table__body-wrapper')
    const headerWrapper = tableRef.value.$el.querySelector('.el-table__header-wrapper')
    
    if (bodyWrapper && headerWrapper) {
      // 当表体滚动时，同步表头的滚动位置
      bodyWrapper.addEventListener('scroll', (e) => {
        headerWrapper.scrollLeft = e.target.scrollLeft
      })
    }
  }
}

// 更新表格高度以填满可用空间
const updateTableHeight = () => {
  nextTick(() => {
    if (tableContainerRef.value) {
      const height = tableContainerRef.value.clientHeight
      if (height > 0) {
        tableHeight.value = height
      }
    }
  })
}

let resizeObserver = null

// 监听路由查询参数变化，更新分页
watch(() => route.query.page, (newPage) => {
  if (newPage) {
    pagination.page = parseInt(newPage)
    applyFilter()
  }
})

onMounted(async () => {
  loading.value = true
  loadingStore.showLoading()
  try {
    // 加载用户在当前团队中的角色
    if (currentTeam.value?.id) {
      try {
        const roleRes = await getUserRoleInTeam(currentTeam.value.id)
        if (roleRes.code === 200 && roleRes.data?.role) {
          currentUserRole.value = roleRes.data.role
        }
      } catch (e) {
        console.error('Failed to load user role:', e)
      }
    }
    await loadPlanDetail()
    // 模块树和用例列表互不依赖，并行加载
    await Promise.all([loadModuleTree(), loadTestCases(false)])
    
    // 数据就绪后，先计算好表格高度再关闭 loading，避免顿挫感
    await nextTick()
    updateTableHeight()
  } finally {
    loading.value = false
    loadingStore.hideLoading()
  }
  
  // 添加滚动监听
  window.addEventListener('scroll', handleScroll)
  
  // ResizeObserver 持续监听后续尺寸变化
  nextTick(() => {
    if (tableContainerRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => updateTableHeight())
      resizeObserver.observe(tableContainerRef.value)
    }
  })
  window.addEventListener('resize', updateTableHeight)
  
  // 初始化表格滚动同步 — 使用 rAF 代替 setTimeout
  requestAnimationFrame(syncTableScroll)
  
  // 从预览页返回时，自动重新打开报告信息对话框并恢复表单数据
  // 只有当测试计划状态为REJECTED时才自动打开（表示用户从预览页返回修改）
  if (sessionStorage.getItem('reopenReportDialog') === '1' && planDetail.value?.status === 'REJECTED') {
    sessionStorage.removeItem('reopenReportDialog')
    // 从localStorage恢复表单文本字段
    const pref = loadReportFormPref()
    if (pref) {
      reportInfoForm.projectName = pref.projectName || ''
      reportInfoForm.verifyEnv = pref.verifyEnv || ''
      reportInfoForm.releaseNote = pref.releaseNote || ''
      reportInfoForm.riskAssessment = pref.riskAssessment || ''
      reportInfoForm.reportRemark = pref.reportRemark || ''
      prInputMode.value = pref.prNumbers ? true : false
      prNumberInput.value = pref.prNumbers || ''
    }
    // 文件字段无法恢复，保持为null
    reportInfoForm.zmindFile = null
    reportInfoForm.mplistFile = null
    prFetchResult.value = null
    // 加载模板列表并恢复之前选择的模板
    if (currentTeam.value?.id) {
      try {
        const res = await getReportTemplates(currentTeam.value.id)
        if (res.code === 200) {
          reportTemplates.value = res.data || []
          // 恢复之前选择的模板
          if (pref?.reportTemplateId) {
            const exists = reportTemplates.value.find(t => t.id === pref.reportTemplateId)
            if (exists) {
              reportInfoForm.reportTemplateId = pref.reportTemplateId
            }
          }
        }
      } catch (e) { /* ignore */ }
    }
    await nextTick()
    reportInfoDialogVisible.value = true
  }
})

onBeforeUnmount(() => {
  // 移除监听
  window.removeEventListener('scroll', handleScroll)
  window.removeEventListener('resize', updateTableHeight)
  if (resizeObserver) {
    resizeObserver.disconnect()
  }
})
</script>

<style scoped>
/* ==================== */
/* TestPlanExecution - Demo Theme */
/* ==================== */

.execution-container {
  padding: 24px;
  padding-bottom: 0;
  min-height: 100%;
  background: var(--demo-bg, #f8fafc);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.execution-header {
  display: flex;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
  flex-shrink: 0;
}

.execution-header h2 {
  color: var(--demo-text-primary, #0f172a);
  font-weight: 600;
}

/* 统计卡片和提交按钮容器 - Demo风格 */
.stats-submit-wrapper {
  margin-top: 20px;
  transition: all 0.15s;
  flex-shrink: 0;
  background: var(--demo-bg-card, #ffffff);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 12px;
  z-index: 100;
  padding: 20px 24px;
  box-sizing: border-box;
}

.stats-submit-wrapper.is-fixed {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  border-radius: 0;
  margin-top: 0;
}

.stats-placeholder {
  height: 80px;
  flex-shrink: 0;
}

.stats-submit-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  max-width: 100%;
  margin: 0 auto;
}

.stats-cards {
  display: flex;
  gap: 12px;
  flex: 1;
  overflow-x: auto;
  align-items: center;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  background: var(--demo-bg-card, #ffffff);
  border-radius: 8px;
  min-width: 110px;
  transition: all 0.15s;
  flex-shrink: 0;
  border: 1px solid var(--demo-border, #e2e8f0);
}

.stat-card:hover {
  background: var(--demo-border-light, #f1f5f9);
  border-color: var(--demo-border, #e2e8f0);
}

.stat-card.active:not(:first-child) {
  background: var(--demo-primary-light, #eef2ff);
  border: 1px solid var(--demo-primary, #4f46e5);
}

.stat-card.active:not(:first-child) .stat-label,
.stat-card.active:not(:first-child) .stat-value {
  color: var(--demo-primary, #4f46e5) !important;
}

.stat-label {
  font-size: 13px;
  color: var(--demo-text-muted, #64748b);
  white-space: nowrap;
  font-weight: 500;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--demo-text-primary, #0f172a);
}

.submit-action {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.submit-action .el-button--primary {
  color: #ffffff !important;
}

.submit-tip {
  font-size: 12px;
  color: var(--demo-text-muted, #64748b);
  white-space: nowrap;
}

.batch-actions {
  margin-top: 20px;
  padding: 16px 20px;
  background-color: var(--demo-primary-light, #eef2ff);
  border: 1px solid rgba(79, 70, 229, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.batch-actions span {
  color: var(--demo-text-primary, #0f172a);
  font-weight: 500;
}

/* 主内容区域：左侧模块树 + 右侧用例列表 - Demo风格 */
.execution-content {
  display: flex;
  flex: 1;
  margin-top: 20px;
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 16px;
  overflow: hidden;
  min-height: 0;
  background: var(--demo-bg-card, #ffffff);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

/* 左侧模块树 - Demo风格 */
.module-sidebar {
  width: 220px;
  border-right: 1px solid var(--demo-border, #e2e8f0);
  background-color: var(--demo-bg-card, #ffffff);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.module-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
  font-weight: 600;
  font-size: 12px;
  color: var(--demo-text-light, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background-color: rgba(248, 250, 252, 0.5);
  flex-shrink: 0;
}

.module-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.module-group {
  margin-bottom: 0;
}

.module-item {
  padding: 8px 12px;
  margin: 2px 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 14px;
  color: var(--demo-text-secondary, #475569);
  transition: all 0.15s;
  user-select: none;
  border-radius: 6px;
}

.module-item:hover {
  background-color: var(--demo-bg, #f8fafc);
}

.module-item.active {
  background-color: var(--demo-primary-light, #eef2ff);
  color: var(--demo-primary-hover, #4338ca);
  font-weight: 500;
}

.module-item .expand-icon {
  margin-right: 6px;
  font-size: 12px;
  color: var(--demo-text-muted, #64748b);
  flex-shrink: 0;
}

.module-content {
  flex: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  overflow: hidden;
}

.module-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sub-module-list {
  background-color: rgba(248, 250, 252, 0.5);
}

.sub-module {
  padding-left: 40px;
  font-size: 13px;
}

/* 右侧用例列表 - Demo风格 */
.testcase-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  background-color: var(--demo-bg-card, #ffffff);
  min-width: 0;
}

.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding-bottom: 0;
  position: relative;
  min-height: 0;
}

.table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
  height: 100%;
}

/* 表格头部 - Demo风格 */
.table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden;
  position: sticky;
  top: 0;
  z-index: 900;
  background: var(--demo-bg-card, #ffffff);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.table-wrapper :deep(.el-table__header-wrapper th) {
  background: #f8fafc !important;
  color: var(--demo-text-muted, #64748b) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* 表格行悬停效果 - Demo风格 */
.table-wrapper :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 固定列不透明背景 */
.table-wrapper :deep(.el-table td.el-table__cell) {
  background: #fff;
}

/* 表格主体 - 使用动态高度填充可用空间 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow: auto;
}

/* 确保表头和表体的水平滚动同步 */
.table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar {
  display: none;
}

.table-wrapper :deep(.el-table__header-wrapper) {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* 自定义表格容器的滚动条样式 - Demo风格 */
.table-wrapper :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light, #f1f5f9);
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: var(--demo-border-light, #f1f5f9);
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* 分页器 - Demo风格 */
.pagination-container {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 0;
  background: var(--demo-bg-card, #ffffff);
  border-top: 1px solid var(--demo-border, #e2e8f0);
}

.pagination-container :deep(.el-pagination) {
  font-weight: normal;
}

.pagination-container :deep(.el-pagination button),
.pagination-container :deep(.el-pager li) {
  background: transparent !important;
  font-weight: 500;
  border-radius: 6px;
  min-width: 32px;
  height: 32px;
}

.pagination-container :deep(.el-pager li) {
  border-radius: 6px;
  margin: 0 2px;
  transition: all 0.15s;
}

.pagination-container :deep(.el-pager li:hover:not(.is-active)) {
  background: var(--demo-border-light, #f1f5f9) !important;
}

.pagination-container :deep(.el-pager li.is-active) {
  background: var(--demo-primary-light, #eef2ff) !important;
  color: var(--demo-primary, #4f46e5) !important;
  font-weight: 600 !important;
}

.single-line-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
  display: block;
}

.clickable-title:hover {
  text-decoration: underline;
}

/* 多选框样式优化 - Demo风格 */
:deep(.el-table .el-checkbox__inner) {
  width: 18px;
  height: 18px;
  border-width: 2px;
  border-radius: 4px;
  border-color: #cbd5e1;
}

:deep(.el-table .el-checkbox__input.is-checked .el-checkbox__inner) {
  background: var(--demo-primary, #4f46e5);
  border-color: var(--demo-primary, #4f46e5);
}

:deep(.el-table .el-checkbox__inner::after) {
  width: 4px;
  height: 9px;
  left: 5px;
  top: 1px;
  border-width: 2px;
}

/* 多选框列表头和表体统一居中对齐 */
:deep(.el-table th.el-table-column--selection .cell),
:deep(.el-table td.el-table-column--selection .cell) {
  display: flex !important;
  align-items: center;
  justify-content: center;
  padding: 0 !important;
  min-height: unset !important;
  line-height: normal !important;
}

/* Demo风格按钮样式 */
:deep(.el-button--primary) {
  background: var(--demo-primary, #4f46e5) !important;
  border-color: var(--demo-primary, #4f46e5) !important;
  color: #fff !important;
  border-radius: 8px !important;
  font-weight: 500 !important;
}

:deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover, #4338ca) !important;
  border-color: var(--demo-primary-hover, #4338ca) !important;
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

:deep(.el-button--success) {
  background: #10b981 !important;
  border-color: #10b981 !important;
  border-radius: 8px !important;
  color: #fff !important;
}

:deep(.el-button--success:hover) {
  background: #059669 !important;
  border-color: #059669 !important;
}

:deep(.el-button--danger) {
  background: #ef4444 !important;
  border-color: #ef4444 !important;
  border-radius: 8px !important;
  color: #fff !important;
}

:deep(.el-button--danger:hover) {
  background: #dc2626 !important;
  border-color: #dc2626 !important;
}

:deep(.el-button--warning) {
  background: #f59e0b !important;
  border-color: #f59e0b !important;
  border-radius: 8px !important;
  color: #fff !important;
}

:deep(.el-button--warning:hover) {
  background: #d97706 !important;
  border-color: #d97706 !important;
}

/* 表格内操作按钮样式 - Demo风格 */
:deep(.el-table .el-button) {
  border-radius: 6px !important;
  font-weight: 500 !important;
}

:deep(.el-table .el-button--primary) {
  background: var(--demo-primary, #4f46e5) !important;
  border-color: var(--demo-primary, #4f46e5) !important;
  color: #fff !important;
}

:deep(.el-table .el-button--primary:hover) {
  background: var(--demo-primary-hover, #4338ca) !important;
  border-color: var(--demo-primary-hover, #4338ca) !important;
}

/* 标签省略号样式 */
.ellipsis-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
  vertical-align: middle;
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
.executor-cell {
  display: inline-block;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

/* ===== 添加用例对话框样式 ===== */
.testcase-select-container {
  display: flex;
  height: calc(100vh - 200px);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 8px;
  overflow: visible;
}
.module-sidebar-add {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid var(--demo-border, #e2e8f0);
  background: #fff;
  display: flex;
  flex-direction: column;
  overflow: visible;
}
.module-sidebar-add .project-filter-section {
  padding: 12px 14px;
  background: rgba(248, 250, 252, 0.5);
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
  position: relative;
  z-index: 100;
  overflow: visible;
}
.module-sidebar-add .section-header {
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}
.module-sidebar-add .project-filter-content {
  overflow: visible;
  position: relative;
}
.module-header-add {
  padding: 12px 16px;
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(248, 250, 252, 0.5);
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}
.module-list-add {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}
.module-item-add {
  padding: 8px 12px;
  margin: 2px 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #475569;
  transition: all 0.15s;
  user-select: none;
  border-radius: 6px;
}
.module-item-add:hover { background: #f8fafc; }
.module-item-add.active {
  background: #eef2ff;
  color: #4338ca;
  font-weight: 500;
}
.module-item-add .expand-icon-add {
  margin-right: 6px;
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}
.module-content-add {
  flex: 1;
  display: flex;
  align-items: center;
  overflow: hidden;
}
.module-name-add {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.testcase-content-add {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  background: #fff;
}
.testcase-filter-add {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}
.add-table-wrapper {
  flex: 1;
  width: 100%;
  position: relative;
  overflow: hidden;
}
.add-table-wrapper :deep(.el-table__body-wrapper) {
  overflow-x: auto !important;
  overflow-y: auto !important;
}
</style>

<style>
/* 步骤tooltip样式 - 全局样式 */
.steps-tooltip {
  max-width: 600px !important;
}

.steps-tooltip .el-popper__arrow::before {
  background: #303133;
}

/* 强制primary按钮白色文字 - 全局样式 */
.test-plan-execution .el-button--primary,
.test-plan-execution .el-button--primary span,
.submit-action .el-button--primary,
.submit-action .el-button--primary span {
  color: #ffffff !important;
}

.test-plan-execution .el-button--primary .el-icon,
.submit-action .el-button--primary .el-icon {
  color: #ffffff !important;
}

/* PR链接样式 - 必须在非scoped中，v-html动态内容不受scoped限制 */
.pr-link-inline {
  color: #409EFF !important;
  text-decoration: underline !important;
  cursor: pointer !important;
  position: relative;
  z-index: 1;
}
.pr-link-inline:hover {
  color: #66b1ff !important;
}
</style>
