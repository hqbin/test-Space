<template>
  <div class="testplan-container">
    <el-card shadow="never">
      <el-tabs v-model="activeTab" @tab-change="handleTabChange">
        <el-tab-pane :label="$t('testplan.title')" name="plans">
    <div class="table-header">
        <div class="header-left">
          <el-button type="primary" :icon="Plus" @click="handleCreate">
            {{ $t('testplan.createPlan') }}
          </el-button>
        </div>
        <div class="header-right">
          <el-select
            v-model="selectedExecutor"
            :placeholder="$t('testplan.executors')"
            clearable
            filterable
            class="header-filter-select"
            style="width: 160px; margin-right: 10px;"
            @change="handleExecutorFilter"
          >
            <el-option
              v-for="name in executorOptions"
              :key="name"
              :label="name"
              :value="name"
            />
          </el-select>
          <el-input
            v-model="searchKeyword"
            :placeholder="$t('testplan.searchPlaceholder')"
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

      <!-- 统计卡片 -->
      <div class="stats-cards">
        <div 
          class="stat-card" 
          :class="{ 'active': statusFilter === null }"
          @click="filterByStatus(null)"
        >
          <div class="stat-label">{{ $t('testplan.totalPlans') }}</div>
          <div class="stat-value">{{ statistics.total }}</div>
        </div>
        <div 
          class="stat-card"
          :class="{ 'active': statusFilter === 'PENDING' }"
          @click="filterByStatus('PENDING')"
        >
          <div class="stat-label">{{ $t('testplan.statusPending') }}</div>
          <div class="stat-value" style="color: var(--text-200);">{{ statistics.pending }}</div>
        </div>
        <div 
          class="stat-card"
          :class="{ 'active': statusFilter === 'IN_PROGRESS' }"
          @click="filterByStatus('IN_PROGRESS')"
        >
          <div class="stat-label">{{ $t('testplan.statusInProgress') }}</div>
          <div class="stat-value" style="color: var(--primary-200);">{{ statistics.inProgress }}</div>
        </div>
        <div 
          class="stat-card"
          :class="{ 'active': statusFilter === 'IN_REVIEW' }"
          @click="filterByStatus('IN_REVIEW')"
        >
          <div class="stat-label">{{ $t('testplan.statusInReview') }}</div>
          <div class="stat-value" style="color: var(--primary-100);">{{ statistics.inReview }}</div>
        </div>
        <div 
          class="stat-card"
          :class="{ 'active': statusFilter === 'REJECTED' }"
          @click="filterByStatus('REJECTED')"
        >
          <div class="stat-label">{{ $t('testplan.statusRejected') }}</div>
          <div class="stat-value" style="color: var(--accent-100);">{{ statistics.rejected }}</div>
        </div>
        <div 
          class="stat-card"
          :class="{ 'active': statusFilter === 'COMPLETED' }"
          @click="filterByStatus('COMPLETED')"
        >
          <div class="stat-label">{{ $t('testplan.statusCompleted') }}</div>
          <div class="stat-value" style="color: var(--primary-100);">{{ statistics.completed }}</div>
        </div>
        <!-- 已取消状态保留但不显示 -->
        <!-- <div 
          class="stat-card"
          :class="{ 'active': statusFilter === 'CANCELLED' }"
          @click="filterByStatus('CANCELLED')"
          style="display: none;"
        >
          <div class="stat-label">已取消</div>
          <div class="stat-value" style="color: #909399;">{{ statistics.cancelled }}</div>
        </div> -->
        <!-- 平均进度保留但不显示 -->
        <!-- <div class="stat-card" style="cursor: default; display: none;">
          <div class="stat-label">平均进度</div>
          <div class="stat-value" :style="{ color: getAverageProgressColor() }">{{ averageProgress }}%</div>
        </div> -->
      </div>
      
      <!-- 测试计划表格 -->
      <div class="plan-table-wrapper" ref="tableWrapper">
        <div class="table-container" ref="tableContainerRef">
        <el-table
          ref="tableRef"
          :data="tableData"
          style="width: 100%"
          :height="tableHeight"
          :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }"
          @header-dragend="handleHeaderDragend"
        >
          <el-table-column :label="$t('testplan.name')" width="250" align="center">
            <template #default="{ row }">
              <el-tooltip :content="row.name" placement="top" :show-after="500" :teleported="false">
                <div class="ellipsis-text clickable-name" @click="handleView(row)">
                  {{ row.name }}
                </div>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testplan.testCases')" width="80" align="center">
            <template #default="{ row }">
              {{ row.total_testcases || 0 }}
            </template>
          </el-table-column>
          <el-table-column :label="$t('testplan.progress')" width="100" align="center">
            <template #default="{ row }">
              <span style="font-size: 14px; font-weight: 500;" :style="{ color: getExecutionProgressColor(row) }">
                {{ row.total_testcases > 0 ? (((row.executed_testcases || 0) / row.total_testcases) * 100).toFixed(2) : '0.00' }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testplan.riskWarning')" width="140" align="center">
            <template #default="{ row }">
              <el-tooltip 
                v-if="getRiskAssessment(row).tooltip"
                :content="getRiskAssessment(row).tooltip" 
                placement="top"
               :show-after="500">
                <el-tag 
                  :type="getRiskAssessment(row).type" 
                  size="small"
                >
                  {{ getRiskAssessment(row).text }}
                </el-tag>
              </el-tooltip>
              <el-tag 
                v-else
                :type="getRiskAssessment(row).type" 
                size="small"
              >
                {{ getRiskAssessment(row).text }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('execution.passRate')" width="100" align="center">
            <template #default="{ row }">
              <span style="font-size: 14px; font-weight: 500;" :style="{ color: getPassRateColor(row) }">
                {{ calculatePassRate(row) }}%
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="$t('common.status')" width="90" align="center">
            <template #default="{ row }">
              <el-tag v-if="row.status === 'PENDING'" type="info" size="small">{{ $t('testplan.statusPending') }}</el-tag>
              <el-tag v-else-if="row.status === 'IN_PROGRESS'" type="warning" size="small">{{ $t('testplan.statusInProgress') }}</el-tag>
              <el-tag v-else-if="row.status === 'IN_REVIEW'" type="primary" size="small">{{ $t('testplan.statusInReview') }}</el-tag>
              <el-tag v-else-if="row.status === 'REJECTED'" type="danger" size="small">{{ $t('testplan.statusRejected') }}</el-tag>
              <el-tag v-else-if="row.status === 'COMPLETED'" type="success" size="small">{{ $t('testplan.statusCompleted') }}</el-tag>
              <el-tag v-else type="info" size="small">{{ $t('testplan.statusCancelled') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('report.name')" width="180" align="center">
            <template #default="{ row }">
              <template v-if="row.report_id && row.report_name">
                <el-tooltip :content="row.report_name" placement="top" :show-after="500">
                  <div class="ellipsis-text clickable-name report-link" @click="goToReport(row.report_id)">
                    {{ row.report_name }}
                  </div>
                </el-tooltip>
              </template>
              <span v-else style="color: #c0c4cc;">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testplan.executors')" width="120" align="center">
            <template #default="{ row }">
              <el-tooltip 
                v-if="row.executor_names && row.executor_names.length > 0"
                :content="row.executor_names.join(', ')" 
                placement="top"
                effect="dark"
                :show-after="500"
              >
                <div style="text-align: center !important; width: 100% !important; cursor: pointer;">
                  {{ row.executor_names.join(', ') }}
                </div>
              </el-tooltip>
              <span v-else style="color: #c0c4cc;">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="$t('testplan.executionPeriod')" width="150" align="center">
            <template #default="{ row }">
              <el-tooltip 
                :content="row.start_time && row.end_time ? `${formatDate(row.start_time)} ~ ${formatDate(row.end_time)}` : '-'" 
                placement="top"
                effect="dark"
                :show-after="500"
              >
                <span style="display: block; text-align: center; width: 100%;">
                  {{ getExecutionDays(row) }}
                </span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.operation')" width="240" align="center" fixed="right">
            <template #default="{ row }">
              <div style="display: flex; align-items: center; justify-content: center; gap: 8px;">
                <el-button
                  v-if="canEditPlan(row)"
                  link
                  type="primary"
                  :loading="editingLoading"
                  @click="handleEdit(row)"
                >
                  {{ $t('common.edit') }}
                </el-button>
                <el-button
                  v-if="(row.status === 'PENDING' || row.status === 'IN_PROGRESS' || row.status === 'REJECTED') && canExecutePlan(row)"
                  link
                  type="primary"
                  @click="handleStartExecution(row)"
                >
                  {{ $t('execution.title') }}
                </el-button>
                <el-button
                  v-if="row.status === 'IN_REVIEW'"
                  link
                  type="warning"
                  @click="handleWithdrawReview(row)"
                >
                  {{ $t('execution.withdrawReview') }}
                </el-button>
                <el-dropdown v-if="(row.status === 'PENDING' && hasButton('testplans', 'delete')) || ((isSuperAdmin || isAdmin) && hasButton('testplans', 'deleteAll'))" trigger="hover" @command="(cmd) => handleDropdownCommand(cmd, row)">
                  <el-button 
                    type="info" 
                    size="small" 
                    link
                    :icon="MoreFilled"
                  />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="delete">
                        <el-icon><Delete /></el-icon>
                        <span>{{ $t('common.delete') }}</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
                <!-- 已完成的测试计划显示导出按钮 -->
                <el-dropdown v-if="row.status === 'COMPLETED' && (hasButton('testplans', 'exportExcel') || hasButton('testplans', 'exportPdf'))" trigger="hover" @command="(cmd) => handleExportCommand(cmd, row)">
                  <el-button 
                    type="primary" 
                    size="small" 
                    link
                    :icon="Download"
                  >
                    {{ $t('common.export') }}
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item v-if="hasButton('testplans', 'exportExcel')" command="excel">
                        <el-icon><Download /></el-icon>
                        <span>{{ $t('report.exportExcel') }}</span>
                      </el-dropdown-item>
                      <el-dropdown-item v-if="hasButton('testplans', 'exportPdf')" command="pdf">
                        <el-icon><Download /></el-icon>
                        <span>{{ $t('report.exportPDF') }}</span>
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
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
          @current-change="handlePageOrSizeChange"
          @size-change="handlePageOrSizeChange"
        />
      </div>

    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="800px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form :model="form" label-width="100px" label-position="top">
        <el-form-item :label="$t('testplan.name')" required>
          <el-input 
            v-model="form.name" 
            :placeholder="$t('testplan.inputName')"
            :prefix-icon="Calendar"
          />
        </el-form-item>
        <el-form-item :label="$t('testplan.description')">
          <el-input 
            v-model="form.description" 
            type="textarea" 
            :rows="4"
            :placeholder="$t('testplan.inputDescription')"
          />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('testplan.startTime')" required>
              <el-date-picker 
                v-model="form.startTime" 
                type="date" 
                :placeholder="$t('testplan.selectStartTime')"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('testplan.endTime')" required>
              <el-date-picker 
                v-model="form.endTime" 
                type="date" 
                :placeholder="$t('testplan.selectEndTime')"
                style="width: 100%"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="$t('suite.title')">
          <el-select
            v-model="form.suiteIds"
            :placeholder="$t('suite.selectSuite')"
            clearable
            filterable
            multiple
            collapse-tags
            collapse-tags-tooltip
            style="width: 100%"
            @change="handleSuiteChange"
          >
            <el-option
              v-for="s in suiteOptions"
              :key="s.id"
              :label="`${s.name}（${s.case_count}个用例）`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('testplan.testCases')">
          <div style="display: flex; align-items: center; gap: 12px;">
            <el-button type="primary" :icon="Plus" @click="openTestCaseSelector">
              {{ $t('testplan.selectTestCases') }}
            </el-button>
            <span style="color: var(--text-200);">
              {{ $t('testplan.selectedCases', { count: form.testCaseIds.length }) }}
            </span>
          </div>
        </el-form-item>
        <el-form-item :label="$t('testplan.executors')" required>
          <el-select 
            ref="executorSelectRef"
            v-model="form.executorIds" 
            :placeholder="$t('testplan.selectExecutors')"
            multiple
            filterable
            remote
            :remote-method="handleExecutorSearch"
            :loading="executorSearchLoading"
            style="width: 100%"
            @focus="loadProjectMembers"
            @change="handleExecutorChange"
          >
            <el-option
              v-for="member in availableExecutors"
              :key="member.id"
              :label="member.username"
              :value="member.id"
            />
          </el-select>
          <div style="margin-top: 8px; color: var(--text-200); font-size: 12px;">
            {{ $t('testplan.executorsSelected', { count: form.executorIds.length }) }}
          </div>
        </el-form-item>
        <el-form-item :label="$t('testplan.reviewer')" required>
          <el-select 
            ref="reviewerSelectRef"
            v-model="form.reviewerId" 
            :placeholder="$t('testplan.selectReviewer')"
            filterable
            remote
            :remote-method="handleReviewerSearch"
            :loading="reviewerSearchLoading"
            style="width: 100%"
            @focus="loadProjectMembers"
            @change="handleReviewerChange"
          >
            <el-option
              v-for="member in availableReviewers"
              :key="member.id"
              :label="member.username"
              :value="member.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('testplan.viewers')">
          <el-select 
            ref="viewerSelectRef"
            v-model="form.viewerIds" 
            :placeholder="$t('testplan.selectViewers')"
            multiple
            filterable
            remote
            :remote-method="handleViewerSearch"
            :loading="viewerSearchLoading"
            style="width: 100%"
            @focus="loadProjectMembers"
            @change="handleViewerChange"
          >
            <el-option
              v-for="member in availableViewers"
              :key="member.id"
              :label="member.username"
              :value="member.id"
            />
          </el-select>
          <div style="margin-top: 8px; color: var(--text-200); font-size: 12px;">
            {{ $t('testplan.viewersSelected', { count: form.viewerIds.length }) }}
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 测试用例选择器对话框 -->
    <el-dialog 
      v-model="testCaseSelectorVisible" 
      :title="$t('testplan.selectTestCasesTitle')" 
      width="95%"
      top="3vh"
      :close-on-click-modal="false"
      append-to-body
      class="testcase-selector-dialog"
    >
      <div class="testcase-select-container">
        <!-- 左侧模块树 -->
        <div class="module-sidebar">
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
          
          <div class="module-header">
            <span>{{ $t('testcase.moduleBelongs') }}</span>
          </div>
          <div class="module-list">
            <div 
              class="module-item" 
              :class="{ active: testcaseFilter.module === '' }"
              @click="handleTestCaseModuleClick('')"
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
                active: testcaseFilter.module === item.path
              }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}"
            >
              <el-icon 
                v-if="item.children && item.children.length > 0"
                class="expand-icon"
                @click.stop="toggleTestCaseModule(item.path)"
              >
                <ArrowRight v-if="!item.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="handleTestCaseModuleClick(item.path)">
                <span class="module-name">{{ item.name }}<span v-if="item.tag" style="color: #409eff; margin-left: 2px;">({{ item.tag }})</span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧用例列表 -->
        <div class="testcase-content">
          <div class="testcase-filter">
            <el-input
              v-model="selectorSearchKeyword"
              :placeholder="selectorRegexMode ? '正则模式：支持 (?=.*A)(?=.*B) 同时包含多词，如 (?=.*卫星)(?=.*信号)' : $t('testcase.searchPlaceholder')"
              clearable
              size="default"
              style="width: 300px; margin-right: 6px; height: 32px;"
              @keyup.enter="loadTestCasesForSelector"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-tooltip :content="selectorRegexMode ? '当前：正则模式（点击切换为普通搜索）' : '当前：普通搜索（点击切换为正则模式）'" placement="top">
              <el-button
                :type="selectorRegexMode ? 'warning' : 'default'"
                @click="selectorRegexMode = !selectorRegexMode"
                style="margin-right: 6px; font-family: monospace; font-weight: bold;"
              >.*</el-button>
            </el-tooltip>
            <el-button type="primary" @click="loadTestCasesForSelector">
              <el-icon><Search /></el-icon>
              {{ $t('common.search') }}
            </el-button>
            
            <el-select v-model="selectorLevelFilter" multiple clearable :placeholder="$t('testcase.level')" style="width: 200px; margin-left: 10px" @change="handleSelectorLevelChange">
              <el-option label="L1" value="L1" />
              <el-option label="L2" value="L2" />
              <el-option label="L3" value="L3" />
              <el-option label="L4" value="L4" />
            </el-select>

            <el-select
              v-model="selectorStatusFilter"
              :placeholder="$t('common.status')"
              style="width: 160px; margin-left: 10px"
              @change="handleSelectorStatusChange"
            >
              <el-option :label="$t('common.all')" value="" />
              <el-option :label="$t('testcase.statusReviewed')" value="REVIEWED" />
              <el-option :label="$t('testcase.statusPendingReview')" value="PENDING" />
            </el-select>

            <el-button 
              @click="selectAllTestCases"
              :disabled="testCases.length === 0"
              style="margin-left: 10px"
              :loading="selectingAll"
            >
              {{ $t('testplan.selectAll') }}
            </el-button>
            
            <div style="flex: 1"></div>
            
            <el-button 
              type="primary" 
              :disabled="tempSelectedTestCases.length === 0"
              @click="confirmTestCaseSelection"
            >
              {{ $t('testplan.confirmSelection') }} ({{ tempSelectedTestCases.length }})
            </el-button>
          </div>
          
          <div class="table-wrapper">
            <el-table
              ref="selectorTable"
              :data="testCases"
              style="width: 100%"
              height="100%"
              border
              :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }"
              v-loading="loadingTestCases"
              element-loading-text="Loading..."
              @selection-change="handleSelectorSelectionChange"
            >
              <el-table-column type="selection" width="50" align="center" />
              <el-table-column prop="case_number" :label="$t('testcase.caseNumber')" width="230" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('testcase.name')" min-width="200" align="left" resizable>
                <template #default="scope">
                  <el-tooltip
                    :content="scope.row.name"
                    placement="top"
                    :show-after="300"
                    popper-class="text-tooltip"
                  >
                    <div class="single-line-ellipsis">{{ scope.row.name }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="precondition" :label="$t('testcase.precondition')" min-width="200" align="left" resizable>
                <template #default="scope">
                  <el-tooltip
                    :content="scope.row.precondition || '-'"
                    placement="top"
                    :show-after="300"
                    popper-class="text-tooltip"
                    :disabled="!scope.row.precondition"
                  >
                    <div class="single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="steps" :label="$t('testcase.steps')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip 
                    placement="top" 
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    raw-content
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div 
                          v-for="(step, stepIndex) in parseSteps(scope.row.steps)" 
                          :key="stepIndex"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
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
              <el-table-column :label="$t('testcase.expectedResult')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip 
                    placement="top" 
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    raw-content
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div 
                          v-for="(result, resultIndex) in parseExpected(scope.row.expected_result)" 
                          :key="resultIndex"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ result }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseExpected(scope.row.expected_result).map((r, i) => `${i + 1}. ${r}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="status" :label="$t('common.status')" width="140" align="center" resizable>
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">{{ $t('testcase.statusReviewed') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">{{ $t('testcase.statusPendingReview') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">{{ $t('testcase.statusReviewRejected') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'DEPRECATED'" type="info" size="small">{{ $t('testcase.statusDeprecated') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="level" :label="$t('testcase.level')" width="140" align="center" resizable />
              <el-table-column :label="$t('testcase.creator')" width="120" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  {{ scope.row.creator_name || '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-pagination
            v-model:current-page="selectorPage"
            v-model:page-size="selectorSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="selectorTotal"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="loadTestCasesForSelector"
            @current-change="loadTestCasesForSelector"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
    </el-dialog>

    <!-- 查看详情对话框 -->
    <el-dialog 
      v-model="viewDialogVisible" 
      :title="$t('testplan.viewDetail')" 
      width="1000px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <div v-loading="viewLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('testplan.name')">
            {{ viewData.name }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testplan.description')">
            {{ viewData.description || '-' }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testplan.startTime')">
            {{ formatDate(viewData.start_time) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testplan.endTime')">
            {{ formatDate(viewData.end_time) }}
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testplan.status')">
            <el-tag v-if="viewData.status === 'PENDING'" type="info" effect="light">
              {{ $t('testplan.statusPending') }}
            </el-tag>
            <el-tag v-else-if="viewData.status === 'IN_PROGRESS'" type="warning" effect="light">
              {{ $t('testplan.statusInProgress') }}
            </el-tag>
            <el-tag v-else-if="viewData.status === 'IN_REVIEW'" type="primary" effect="light">
              {{ $t('testplan.statusInReview') }}
            </el-tag>
            <el-tag v-else-if="viewData.status === 'REJECTED'" type="danger" effect="light">
              {{ $t('testplan.statusRejected') }}
            </el-tag>
            <el-tag v-else-if="viewData.status === 'COMPLETED'" type="success" effect="light">
              {{ $t('testplan.statusCompleted') }}
            </el-tag>
            <el-tag v-else type="info" effect="light">
              {{ $t('testplan.statusCancelled') }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('testplan.testCases')">
            {{ viewData.total_testcases || 0 }} 个用例
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <h4 style="margin-bottom: 12px;">{{ $t('testplan.executors') }} ({{ viewData.executors?.length || 0 }})</h4>

        <div style="margin-bottom: 20px;">
          <el-tag 
            v-for="executor in viewData.executors" 
            :key="executor.id"
            style="margin-right: 8px; margin-bottom: 8px;"
          >
            {{ executor.username }}
          </el-tag>
          <span v-if="!viewData.executors || viewData.executors.length === 0" style="color: var(--text-200);">{{ $t('testplan.noExecutors') }}</span>
        </div>

        <el-divider />

<div style="margin-bottom: 20px;">
          <h4 style="margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
            {{ $t('testplan.testCases') }} ({{ viewData.total_testcases || 0 }})
            <el-button
              type="primary" 
              size="small" 
              :icon="View"
              @click="viewTestCases"
              v-if="viewData.test_cases && viewData.test_cases.length > 0"
            >
              查看测试用例
            </el-button>
          </h4>
          <span v-if="!viewData.test_cases || viewData.test_cases.length === 0" style="color: var(--text-200);">{{ $t('testplan.noTestCases') }}</span>
        </div>
        
        <!-- 评论区 -->
        <el-divider />
        <CommentSection
          v-if="viewData.id"
          entity-type="testplan"
          :entity-id="viewData.id"
        />
      </div>
      <template #footer>
        <el-button @click="viewDialogVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 测试用例列表对话框 -->
    <el-dialog 
      v-model="testCaseListVisible" 
      :title="`测试计划 - ${viewData.name} - 测试用例列表`" 
      width="95%"
      top="3vh"
      :close-on-click-modal="false"
      class="testcase-list-dialog"
      @closed="handleDialogClosed"
    >
      <div class="testcase-select-container">
        <!-- 左侧模块树 -->
        <div class="module-sidebar">
          <div class="module-header">
            <span>{{ $t('testcase.moduleBelongs') }}</span>
          </div>
          <div class="module-list">
            <div 
              class="module-item" 
              :class="{ active: viewTestCaseFilter.module === '' }"
              @click="handleViewTestCaseModuleClick('', '')"
            >
              <span class="module-name">{{ $t('common.all') }}</span>
            </div>
            <div 
              v-for="item in flatViewModuleTree" 
              :key="item.path"
              class="module-item"
              :class="{ 
                'main-module': item.depth === 0,
                'sub-module': item.depth > 0,
                active: item.depth === 0 ? (viewTestCaseFilter.module === item.name && !viewTestCaseFilter.subModule) : (viewTestCaseFilter.subModule === item.name)
              }"
              :style="item.depth > 0 ? { paddingLeft: (12 + item.depth * 16) + 'px' } : {}"
            >
              <el-icon 
                v-if="item.children && item.children.length > 0"
                class="expand-icon"
                @click.stop="toggleViewTestCaseModule(item.path)"
              >
                <ArrowRight v-if="!item.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="item.depth === 0 ? handleViewTestCaseModuleClick(item.name, '') : handleViewTestCaseModuleClick(viewTestCaseFilter.module || item.name, item.name)">
                <span class="module-name">{{ item.name }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧用例列表 -->
        <div class="testcase-content">
          <div class="testcase-filter">
            <el-input
              v-model="viewTestCaseSearchKeyword"
              :placeholder="$t('testcase.searchPlaceholder')"
              clearable
              style="width: 300px; margin-right: 10px"
              @keyup.enter="filterViewTestCases"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="filterViewTestCases">
              <el-icon><Search /></el-icon>
              {{ $t('common.search') }}
            </el-button>
            
            <div style="flex: 1"></div>
            
            <el-button 
              type="primary" 
              @click="showAddTestCaseToViewDialog"
            >
              <el-icon><Plus /></el-icon>
              {{ $t('testcase.createCase') }}
            </el-button>
          </div>
          
          <div class="table-wrapper">
            <el-table
              :data="pagedViewTestCases"
              style="width: 100%"
              height="100%"
              border
              :header-cell-style="{ background: '#e6f5f5', color: 'var(--text-200)', fontWeight: '600' }"
              v-loading="testCaseListLoading"
            >
              <el-table-column :label="$t('common.operation')" width="60" align="center">
                <template #default="{ row }">
                  <el-icon 
                    class="remove-icon"
                    @click="removeTestCaseFromView(row)"
                    title="移除用例"
                  >
                    <CircleClose />
                  </el-icon>
                </template>
              </el-table-column>
              <el-table-column prop="case_number" :label="$t('testcase.caseNumber')" width="230" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('testcase.name')" min-width="200" align="left" resizable>
                <template #default="scope">
                  <el-tooltip
                    :content="scope.row.name"
                    placement="top"
                    :show-after="300"
                    popper-class="text-tooltip"
                  >
                    <div class="single-line-ellipsis">{{ scope.row.name }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="precondition" :label="$t('testcase.precondition')" min-width="200" align="left" resizable>
                <template #default="scope">
                  <el-tooltip
                    :content="scope.row.precondition || '-'"
                    placement="top"
                    :show-after="300"
                    popper-class="text-tooltip"
                    :disabled="!scope.row.precondition"
                  >
                    <div class="single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="steps" :label="$t('testcase.steps')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip 
                    placement="top" 
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    raw-content
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div 
                          v-for="(step, stepIndex) in parseSteps(scope.row.steps)" 
                          :key="stepIndex"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
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
              <el-table-column :label="$t('testcase.expectedResult')" min-width="250" align="left" resizable>
                <template #default="scope">
                  <el-tooltip 
                    placement="top" 
                    popper-class="steps-tooltip"
                    effect="dark"
                    :show-after="500"
                    raw-content
                  >
                    <template #content>
                      <div style="max-width: 500px; padding: 8px 0;">
                        <div 
                          v-for="(result, resultIndex) in parseExpected(scope.row.expected_result)" 
                          :key="resultIndex"
                          style="display: flex; padding: 6px 0; line-height: 1.6;"
                        >
                          <span style="color: var(--primary-100); font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
                          <span style="flex: 1; word-break: break-word;">{{ result }}</span>
                        </div>
                      </div>
                    </template>
                    <div class="single-line-ellipsis">
                      {{ parseExpected(scope.row.expected_result).map((r, i) => `${i + 1}. ${r}`).join(' ') || '-' }}
                    </div>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="status" :label="$t('common.status')" width="140" align="center" resizable>
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">{{ $t('testcase.statusReviewed') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">{{ $t('testcase.statusPendingReview') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">{{ $t('testcase.statusReviewRejected') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'DEPRECATED'" type="info" size="small">{{ $t('testcase.statusDeprecated') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="level" :label="$t('testcase.level')" width="140" align="center" resizable />
              <el-table-column :label="$t('testcase.creator')" width="120" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  {{ scope.row.creator_name || '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-pagination
            v-model:current-page="viewTestCasePage"
            v-model:page-size="viewTestCasePageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="filteredViewTestCases.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleViewTestCasePageSizeChange"
            @current-change="handleViewTestCasePageChange"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="testCaseListVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>
        </el-tab-pane>
        <el-tab-pane v-if="hasButton('testplans', 'taskOverviewTab')" :label="$t('taskOverview.title')" name="taskOverview">
          <TaskOverviewList v-if="activeTab === 'taskOverview'" />
        </el-tab-pane>
        <el-tab-pane v-if="hasButton('testplans', 'suiteTab')" :label="$t('suite.title')" name="suites">
          <TestSuiteList v-if="activeTab === 'suites'" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
defineOptions({ name: 'TestPlanList' })
import { ref, reactive, onMounted, onActivated, onBeforeUnmount, watch, computed, nextTick } from 'vue'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getTestPlans, createTestPlan, getTestPlanDetail, updateTestPlan, deleteTestPlan, startTestPlan, withdrawTestPlanReview } from '../../api/testplan'
import { getTestSuites, getTestSuiteDetail } from '../../api/testSuite'
import { getTestCases, getAllTestCaseIds } from '../../api/testcase'
import { getModuleTree } from '../../api/module'
import { getAvailableMembersForSelection, getUserRoleInTeam } from '../../api/team'
import { useUserRole } from '../../composables/useUserRole'
import { exportReportPdf, exportReportExcel } from '../../api/report'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Calendar, Plus, Clock, View, Search, Edit, Delete, VideoPlay, MoreFilled, ArrowRight, ArrowDown, CircleClose, Download } from '@element-plus/icons-vue'
import { useTeam } from '../../composables/useTeam'
import { usePagination } from '../../composables/usePagination'
import CommentSection from '@/components/CommentSection.vue'
import ProjectSelector from '../../components/ProjectSelector.vue'
import TestSuiteList from './TestSuiteList.vue'
import TaskOverviewList from './TaskOverviewList.vue'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'
import { useProjectPreference } from '../../composables/useProjectPreference'
import { getWorkDaysInRange, getNonWorkingDaysInRange, getElapsedWorkDays } from '../../utils/chineseHoliday'

const router = useRouter()
const loadingStore = useLoadingStore()
const activeTab = ref(sessionStorage.getItem('testplans_activeTab') || 'plans')

const handleTabChange = (tab) => {
  sessionStorage.setItem('testplans_activeTab', tab)
}

const { t } = useI18n()
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()

// 用例库选择相关 - 新版本
const { selectedProjectIdList, applyPreference, updateSelection, resetPreference } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])

// 当前项目组的所有用例库ID（测试计划列表用，不受用例库选择器影响）
const allTeamProjectIds = computed(() => {
  return teamProjectList.value.map(p => p.id)
})

// 计算当前选中的用例库ID列表（用例选择器对话框用）
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0 
    ? selectedProjectIdList.value 
    : teamProjectList.value.map(p => p.id)
})

// 兼容旧代码的 currentProjectId
const currentProjectId = computed(() => {
  if (currentProjectIds.value.length > 0) {
    return currentProjectIds.value[0]
  }
  return null
})

// 处理用例库选择器变化（防抖，防止快速切换导致数据错乱）
let _projectChangeTimer = null
const handleProjectSelectorChange = (ids) => {
  updateSelection(ids)
  selectorLevelFilter.value = []
  selectorStatusFilter.value = ''
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  selectorPage.value = 1
  clearTimeout(_projectChangeTimer)
  _projectChangeTimer = setTimeout(() => {
    loadModuleTree()
    loadTestCasesForSelector()
  }, 300)
}

const tableData = ref([])
const allTableData = ref([]) // 存储所有数据用于统计
const { page, size, total } = usePagination('testPlanList', 10)
const containerLoading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = computed(() => isEdit.value ? t('testplan.editPlan') : t('testplan.createPlan'))
const submitting = ref(false)
const searchKeyword = ref('')
const selectedExecutor = ref('')
const testCases = ref([])
const loadingTestCases = ref(false)
const loadingMembers = ref(false)
const testCaseSelectorVisible = ref(false)
const selectorSearchKeyword = ref('')
const selectorRegexMode = ref(false)
const selectorLevelFilter = ref([])
const selectorStatusFilter = ref('')
const selectorPage = ref(1)
const selectorSize = ref(20)
const selectorTotal = ref(0)
const tempSelectedIds = ref([])
const tempSelectedTestCases = ref([])
const isRestoringSelection = ref(false)
const selectorTable = ref(null)
const viewDialogVisible = ref(false)
const viewLoading = ref(false)
const viewData = ref({})
const suiteOptions = ref([])
// 追踪来自套件的用例ID，用于套件移除时准确撤销
const suiteSourceIds = ref(new Set())
const isEdit = ref(false)
const editId = ref(null)
const editingLoading = ref(false)
const selectingAll = ref(false)
const moduleTree = ref([])
let _moduleTreeVer = 0
let _selectorVer = 0
// 用户角色相关
const { isAdmin, isSuperAdmin, hasButton } = useUserRole()
const currentUserRole = ref('member') // 'member' | 'leader' | 'org_manager' | 'admin'

// 可选成员列表
const availableExecutors = ref([])
const availableViewers = ref([])
const availableReviewers = ref([])

// 搜索功能相关状态
const executorSearchLoading = ref(false)
const viewerSearchLoading = ref(false)
const reviewerSearchLoading = ref(false)

// el-select ref，用于选中后清空搜索输入框
const executorSelectRef = ref(null)
const viewerSelectRef = ref(null)
const reviewerSelectRef = ref(null)

// 通用：选中后清空 el-select 的搜索输入框
const clearSelectSearch = (selectRef) => {
  nextTick(() => {
    const el = selectRef.value?.$el
    if (!el) return
    const input = el.querySelector('.el-select__input') || el.querySelector('.el-input__inner')
    if (input) {
      const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
        window.HTMLInputElement.prototype, 'value'
      ).set
      nativeInputValueSetter.call(input, '')
      input.dispatchEvent(new Event('input', { bubbles: true }))
    }
  })
}

// 所有用户都可以选择其他成员作为执行人
const canSelectOtherMembers = computed(() => {
  return true
})

// 状态筛选
const statusFilter = ref(sessionStorage.getItem('testPlanListStatusFilter') || null)

// 统计数据
const statistics = computed(() => {
  const data = allTableData.value
  let pending = 0
  let inProgress = 0
  let inReview = 0
  let rejected = 0
  let completed = 0
  let cancelled = 0
  
  data.forEach(plan => {
    if (plan.status === 'PENDING') {
      pending++
    } else if (plan.status === 'IN_PROGRESS') {
      inProgress++
    } else if (plan.status === 'IN_REVIEW') {
      inReview++
    } else if (plan.status === 'REJECTED') {
      rejected++
    } else if (plan.status === 'COMPLETED') {
      completed++
    } else if (plan.status === 'CANCELLED') {
      cancelled++
    }
  })
  
  // 总计划数不包含已完成的计划
  const total = pending + inProgress + inReview + rejected
  
  return { total, pending, inProgress, inReview, rejected, completed, cancelled }
})

// 平均进度
const averageProgress = computed(() => {
  const data = allTableData.value
  if (data.length === 0) return 0
  
  let totalProgress = 0
  data.forEach(plan => {
    if (plan.total_testcases > 0) {
      const progress = ((plan.executed_testcases || 0) / plan.total_testcases) * 100
      totalProgress += progress
    }
  })
  
  return Math.round(totalProgress / data.length)
})

// 平均进度颜色
const getAverageProgressColor = () => {
  const progress = averageProgress.value
  if (progress >= 80) return '#67c23a'
  if (progress >= 50) return '#e6a23c'
  return '#f56c6c'
}

// 执行人选项列表（从所有计划中提取去重）
const executorOptions = computed(() => {
  const nameSet = new Set()
  allTableData.value.forEach(plan => {
    if (plan.executor_names && plan.executor_names.length > 0) {
      plan.executor_names.forEach(name => nameSet.add(name))
    }
  })
  return Array.from(nameSet).sort()
})

// 按状态筛选
const filterByStatus = (status) => {
  statusFilter.value = status
  // 保存筛选状态到sessionStorage
  if (status) {
    sessionStorage.setItem('testPlanListStatusFilter', status)
  } else {
    sessionStorage.removeItem('testPlanListStatusFilter')
  }
  page.value = 1
  applyFilter()
}

// 应用筛选
const applyFilter = () => {
  let filtered = [...allTableData.value]
  
  // 按关键词搜索
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(plan =>
      (plan.name && plan.name.toLowerCase().includes(kw)) ||
      (plan.creator_name && plan.creator_name.toLowerCase().includes(kw)) ||
      (plan.executor_names && plan.executor_names.some(n => n.toLowerCase().includes(kw))) ||
      (plan.project_name && plan.project_name.toLowerCase().includes(kw))
    )
  }
  
  // 按执行人筛选
  if (selectedExecutor.value) {
    filtered = filtered.filter(plan =>
      plan.executor_names && plan.executor_names.includes(selectedExecutor.value)
    )
  }
  
  // 按状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(plan => plan.status === statusFilter.value)
  } else {
    // 总计划数筛选：排除已完成的计划
    filtered = filtered.filter(plan => plan.status !== 'COMPLETED')
  }
  
  // 排序逻辑
  if (statusFilter.value) {
    // 单个状态筛选：按更新时间降序（最新的在前）
    filtered.sort((a, b) => {
      const timeA = new Date(a.updated_at || a.created_at).getTime()
      const timeB = new Date(b.updated_at || b.created_at).getTime()
      return timeB - timeA
    })
  } else {
    // 显示所有计划：按状态分组排序（未开始 > 进行中 > 审核中 > 审核不通过 > 已完成），同状态内按更新时间降序
    const statusOrder = {
      'PENDING': 1,
      'IN_PROGRESS': 2,
      'IN_REVIEW': 3,
      'REJECTED': 4,
      'COMPLETED': 5,
      'CANCELLED': 6
    }
    
    filtered.sort((a, b) => {
      // 先按状态排序
      const statusDiff = (statusOrder[a.status] || 999) - (statusOrder[b.status] || 999)
      if (statusDiff !== 0) {
        return statusDiff
      }
      
      // 同状态内按更新时间降序
      const timeA = new Date(a.updated_at || a.created_at).getTime()
      const timeB = new Date(b.updated_at || b.created_at).getTime()
      return timeB - timeA
    })
  }
  
  // 分页
  total.value = filtered.length
  const start = (page.value - 1) * size.value
  const end = start + size.value
  tableData.value = filtered.slice(start, end)
}

// 表格容器引用
const tableWrapper = ref(null)
const tableRef = ref(null)
const tableContainerRef = ref(null)
const tableHeight = ref(400)
const updateTableHeight = () => {
  nextTick(() => {
    if (tableContainerRef.value && tableContainerRef.value.clientHeight > 0) {
      tableHeight.value = tableContainerRef.value.clientHeight
    }
  })
}
let resizeObserver = null
const { scrollToTop } = useScrollToTop(tableRef)

const handlePageOrSizeChange = async () => {
  applyFilter()
  await nextTick()
  scrollToTop()
}

// 处理表格头部拖动事件
const handleHeaderDragend = async () => {
  await nextTick()
  syncTableScroll()
}

// 同步表格滚动
const syncTableScroll = () => {
  if (!tableWrapper.value) return
  
  const headerWrapper = tableWrapper.value.querySelector('.el-table__header-wrapper')
  const bodyWrapper = tableWrapper.value.querySelector('.el-table__body-wrapper')
  
  if (headerWrapper && bodyWrapper) {
    // 同步水平滚动
    bodyWrapper.addEventListener('scroll', () => {
      if (headerWrapper.scrollLeft !== bodyWrapper.scrollLeft) {
        headerWrapper.scrollLeft = bodyWrapper.scrollLeft
      }
    })
    
    headerWrapper.addEventListener('scroll', () => {
      if (bodyWrapper.scrollLeft !== headerWrapper.scrollLeft) {
        bodyWrapper.scrollLeft = headerWrapper.scrollLeft
      }
    })
  }
}

// 处理窗口大小变化
const handleResize = () => {
  // 窗口大小变化时，表格高度会自动重新计算
}

// 初始化事件监听
const initEventListeners = () => {
  nextTick(() => {
    updateTableHeight()
    if (tableContainerRef.value && typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(updateTableHeight)
      resizeObserver.observe(tableContainerRef.value)
    }
    setTimeout(updateTableHeight, 150)
    syncTableScroll()
  })
  window.addEventListener('resize', updateTableHeight)
}

// 清理事件监听
const cleanupEventListeners = () => {
  window.removeEventListener('resize', updateTableHeight)
  if (resizeObserver) resizeObserver.disconnect()
}

// 用例筛选条件
const testcaseFilter = reactive({
  module: '',
  subModule: ''
})

// 测试用例列表相关变量
const testCaseListVisible = ref(false)
const testCaseListLoading = ref(false)
const testCaseList = ref([])
const testCasePage = ref(1)
const testCasePageSize = ref(20)

// 查看用例对话框的模块树和筛选
const viewModuleTree = ref([])
const viewTestCaseFilter = reactive({
  module: '',
  subModule: ''
})
const viewTestCaseSearchKeyword = ref('')
const viewTestCasePage = ref(1)
const viewTestCasePageSize = ref(20)
const filteredViewTestCases = ref([])

// 分页后的查看用例数据
const pagedViewTestCases = computed(() => {
  const start = (viewTestCasePage.value - 1) * viewTestCasePageSize.value
  return filteredViewTestCases.value.slice(start, start + viewTestCasePageSize.value)
})



// Get level type for tag color
const getLevelType = (level) => {
  const typeMap = {
    'L1': 'danger',
    'L2': 'warning',
    'L3': 'primary',
    'L4': 'info'
  }
  return typeMap[level] || 'info'
}

const form = reactive({
  name: '',
  description: '',
  startTime: null,
  endTime: null,
  project_id: currentProjectId,
  testCaseIds: [],
  executorIds: [],
  viewerIds: [],
  reviewerId: null,
  suiteIds: []
})

const handleSearch = () => {
  page.value = 1
  applyFilter()
}

const handleExecutorFilter = () => {
  page.value = 1
  applyFilter()
}

const formatDate = (date) => {
  if (!date) return '-'
  const d = new Date(date)
  return d.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit'
  }).replace(/\//g, '-')
}

// 计算执行周期天数（工作日，排除法定节假日）
const getExecutionDays = (row) => {
  if (!row.start_time || !row.end_time) return '-'
  const workDays = getWorkDaysInRange(row.start_time, row.end_time)
  return `${workDays} ${t('testplan.days')}`
}

const calculatePassRate = (row) => {
  const validTestcases = row.total_testcases - (row.na_testcases || 0)
  if (validTestcases === 0) return '0.00'
  return (((row.passed_testcases || 0) / validTestcases) * 100).toFixed(2)
}

const getPassRateColor = (row) => {
  const validTestcases = row.total_testcases - (row.na_testcases || 0)
  if (validTestcases === 0) return '#909399'
  const passRate = (row.passed_testcases || 0) / validTestcases
  if (passRate >= 0.9) return '#67c23a'
  if (passRate >= 0.7) return '#e6a23c'
  return '#f56c6c'
}

const getExecutionProgressColor = (row) => {
  if (!row.total_testcases || row.total_testcases === 0) return '#909399'
  const progress = (row.executed_testcases || 0) / row.total_testcases
  if (progress >= 0.9) return '#67c23a' // 绿色：90%以上
  if (progress >= 0.5) return '#409eff' // 蓝色：50-90%
  return '#e6a23c' // 橙色：50%以下
}

// 风险评估函数
const getRiskAssessment = (row) => {
  // 如果计划已完成或进入审核阶段（审核中/审核不通过），风险评估都显示已完成
  if (row.status === 'COMPLETED' || row.status === 'IN_REVIEW' || row.status === 'REJECTED') {
    return { type: 'success', text: t('testplan.riskCompleted') }
  }
  
  // 如果计划已取消
  if (row.status === 'CANCELLED') {
    return { type: 'info', text: t('testplan.riskCancelled') }
  }
  
  // 如果没有用例，无法评估
  if (!row.total_testcases || row.total_testcases === 0) {
    return { type: 'info', text: t('testplan.riskNoCases') }
  }
  
  // 如果没有开始时间或结束时间，无法评估
  if (!row.start_time || !row.end_time) {
    return { type: 'info', text: t('testplan.riskNoPeriod') }
  }
  
  const now = new Date()
  now.setHours(0, 0, 0, 0)
  
  const startDate = new Date(row.start_time)
  startDate.setHours(0, 0, 0, 0)
  
  const endDate = new Date(row.end_time)
  endDate.setHours(23, 59, 59, 999)
  
  // 如果当前时间在开始时间之前
  if (now < startDate) {
    if (row.status === 'IN_PROGRESS') {
      const actualProgress = ((row.executed_testcases || 0) / row.total_testcases) * 100
      if (actualProgress >= 100) {
        return { type: 'success', text: t('testplan.riskCompleted') }
      } else if (actualProgress > 0) {
        return { type: 'success', text: t('testplan.progressNormal') }
      } else {
        return { type: 'warning', text: t('testplan.notStartedWarning') }
      }
    }
    return { type: 'info', text: t('testplan.riskNotStarted') }
  }
  
  // totalDays: 总工作日数（排除周末+法定节假日+补班日）
  // elapsedDays: 已过去的工作日数
  const totalDays = getWorkDaysInRange(row.start_time, row.end_time)
  const elapsedDays = Math.max(0, getElapsedWorkDays(row.start_time, now))
  
  // 如果当前时间超过结束时间
  if (now > endDate) {
    const actualProgress = ((row.executed_testcases || 0) / row.total_testcases) * 100
    if (actualProgress >= 100) {
      return { type: 'success', text: t('testplan.riskCompleted') }
    } else {
      const overdueDays = Math.ceil((now - endDate) / (1000 * 60 * 60 * 24))
      return { type: 'danger', text: t('testplan.riskOverdue', { days: overdueDays }) }
    }
  }
  
  // 如果在测试周期内但状态还是未开始，显示预警
  if (row.status === 'PENDING') {
    return { 
      type: 'warning', 
      text: t('testplan.notStartedWarning'),
      tooltip: t('testplan.notStartedWarningTooltip')
    }
  }
  
  const expectedProgress = (elapsedDays / totalDays) * 100
  const actualProgress = ((row.executed_testcases || 0) / row.total_testcases) * 100
  const progressGap = expectedProgress - actualProgress
  
  if (progressGap <= 0) {
    return { type: 'success', text: t('testplan.progressNormal') }
  } else if (progressGap < 5) {
    return { type: 'warning', text: t('testplan.riskSlightDelay') }
  } else if (progressGap < 10) {
    return { type: 'warning', text: t('testplan.riskDelay') }
  } else {
    return { type: 'danger', text: t('testplan.riskSevereDelay') }
  }
}

const loadData = async () => {
  if (allTeamProjectIds.value.length === 0) {
    return
  }
  
  containerLoading.value = true
  loadingStore.showLoading(t('testplan.loadingPlans'))
  try {
    // 加载所有数据用于统计和筛选（使用项目组全部用例库，不受选择器影响）
    const res = await getTestPlans({ 
      project_ids: allTeamProjectIds.value.join(','),
      team_id: currentTeam.value?.id,
      page: 1, 
      size: 10000  // 获取所有数据
    })
    allTableData.value = res.data.records
    
    // 应用筛选和分页
    applyFilter()
  } catch (error) {
    ElMessage.error(t('common.failed'))
  } finally {
    containerLoading.value = false
    loadingStore.hideLoading()
  }
}

const loadTestCases = async () => {
  if (!currentProjectId.value) {
    testCases.value = []
    return
  }
  
  loadingTestCases.value = true
  try {
    const res = await getTestCases({ 
      project_id: currentProjectId.value,
      page: 1, 
      size: 1000 
    })
    testCases.value = res.data.records
  } catch (error) {
    ElMessage.error(t('testplan.loadTestCasesFailed'))
  } finally {
    loadingTestCases.value = false
  }
}

const loadTestCasesForSelector = async () => {
  if (currentProjectIds.value.length === 0) {
    testCases.value = []
    selectorTotal.value = 0
    return
  }
  
  const ver = ++_selectorVer
  loadingTestCases.value = true
  try {
    const params = {
      page: selectorPage.value,
      size: selectorSize.value,
      keyword: selectorSearchKeyword.value
        ? (selectorRegexMode.value ? `regex:${selectorSearchKeyword.value}` : selectorSearchKeyword.value)
        : undefined,
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      status_in: selectorStatusFilter.value ? selectorStatusFilter.value : 'REVIEWED,PENDING'
    }
    
    if (selectorLevelFilter.value.length > 0) {
      params.level_in = selectorLevelFilter.value.join(',')
    }

    // 添加用例库ID参数
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    
    const res = await getTestCases(params)
    if (ver !== _selectorVer) return
    if (res.code === 200) {
      // 过滤掉已经关联的用例
      const existingIds = new Set((testCaseList.value || []).map(tc => tc.id))
      
      // 数据赋值前设置标志位，防止 selection-change 清空已选
      isRestoringSelection.value = true
      testCases.value = res.data.records.filter(tc => !existingIds.has(tc.id))
      selectorTotal.value = res.data.total
      
      // 恢复之前的选择状态
      await nextTick()
      // 先清除所有选中状态，防止 row-key 复用导致残留勾选
      if (selectorTable.value) {
        selectorTable.value.clearSelection()
      }
      if (selectorTable.value && tempSelectedTestCases.value.length > 0) {
        const selectedIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
        testCases.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          selectorTable.value.toggleRowSelection(row, shouldSelect)
        })
      }
      await nextTick()
      isRestoringSelection.value = false
    }
  } catch (error) {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail
    if (status === 400 && detail) {
      ElMessage.error(`正则搜索错误：${detail}`)
    } else if (status === 408) {
      ElMessage.error(detail || '正则搜索超时，请简化正则表达式后重试')
    } else if (detail) {
      ElMessage.error(detail)
    } else {
      ElMessage.error('加载用例列表失败')
    }
  } finally {
    loadingTestCases.value = false
  }
}

const loadProjectMembers = async () => {
  // 获取当前项目组ID
  const teamId = currentTeam.value?.id
  if (!teamId) {
    // 项目组未选择时静默返回，不显示警告
    return
  }
  
  loadingMembers.value = true
  try {
    // 加载执行人列表
    const executorRes = await getAvailableMembersForSelection(teamId, 'executor')
    if (executorRes.code === 200) {
      availableExecutors.value = executorRes.data
    }
    
    // 加载查看人列表
    const viewerRes = await getAvailableMembersForSelection(teamId, 'viewer')
    if (viewerRes.code === 200) {
      availableViewers.value = viewerRes.data
    }
    
    // 加载审核人列表（组织下任何人都可以选择组织下任何人）
    const reviewerRes = await getAvailableMembersForSelection(teamId, 'reviewer')
    if (reviewerRes.code === 200) {
      availableReviewers.value = reviewerRes.data
    }
  } catch (error) {
    ElMessage.error('加载项目成员失败')
  } finally {
    loadingMembers.value = false
  }
}

// 执行人远程搜索
const handleExecutorSearch = async (query) => {
  if (!query || !query.trim()) {
    await loadProjectMembers()
    return
  }
  executorSearchLoading.value = true
  try {
    const teamId = currentTeam.value?.id
    if (!teamId) return
    const res = await getAvailableMembersForSelection(teamId, 'executor', query.trim())
    if (res.code === 200) {
      availableExecutors.value = res.data
    }
  } catch (error) {
    console.error('Search executors failed:', error)
  } finally {
    executorSearchLoading.value = false
  }
}

// 查看人远程搜索
const handleViewerSearch = async (query) => {
  if (!query || !query.trim()) {
    await loadProjectMembers()
    return
  }
  viewerSearchLoading.value = true
  try {
    const teamId = currentTeam.value?.id
    if (!teamId) return
    const res = await getAvailableMembersForSelection(teamId, 'viewer', query.trim())
    if (res.code === 200) {
      availableViewers.value = res.data
    }
  } catch (error) {
    console.error('Search viewers failed:', error)
  } finally {
    viewerSearchLoading.value = false
  }
}

// 审核人远程搜索
const handleReviewerSearch = async (query) => {
  if (!query || !query.trim()) {
    await loadProjectMembers()
    return
  }
  reviewerSearchLoading.value = true
  try {
    const teamId = currentTeam.value?.id
    if (!teamId) return
    const res = await getAvailableMembersForSelection(teamId, 'reviewer', query.trim())
    if (res.code === 200) {
      availableReviewers.value = res.data
    }
  } catch (error) {
    console.error('Search reviewers failed:', error)
  } finally {
    reviewerSearchLoading.value = false
  }
}

// 选中后清空搜索框并刷新列表
const handleExecutorChange = () => clearSelectSearch(executorSelectRef)
const handleViewerChange = () => clearSelectSearch(viewerSelectRef)
const handleReviewerChange = () => clearSelectSearch(reviewerSelectRef)

// 加载当前用户角色
const loadCurrentUserRole = async () => {
  const teamId = currentTeam.value?.id
  if (!teamId) return
  
  try {
    const res = await getUserRoleInTeam(teamId)
    if (res.code === 200) {
      currentUserRole.value = res.data.role
    }
  } catch (error) {
    console.error('加载用户角色失败', error)
    currentUserRole.value = 'member'
  }
}

const openTestCaseSelector = async () => {
  testCaseSelectorVisible.value = true
  selectorSearchKeyword.value = ''
  selectorRegexMode.value = false
  selectorLevelFilter.value = []
  selectorStatusFilter.value = ''
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  selectorPage.value = 1
  selectorSize.value = 20
  // 根据 form.testCaseIds 恢复已选状态，而不是清空
  tempSelectedTestCases.value = form.testCaseIds.map(id => ({ id }))
  
  // 确保 teamProjects 已加载
  if (teamProjects.value.length === 0 && currentTeam.value) {
    await loadTeamProjects()
  }
  
  // 等待 Vue 渲染完成
  await nextTick()
  
  // 加载模块树
  await loadModuleTree()
  
  // 加载用例列表
  await loadTestCasesForSelector()
}

const loadModuleTree = async () => {
  if (currentProjectIds.value.length === 0) return
  
  const ver = ++_moduleTreeVer
  try {
    const projectParam = currentProjectIds.value.join(',')
    if (!projectParam) return
    
    const res = await getModuleTree(projectParam)
    if (ver !== _moduleTreeVer) return
    if (res.code === 200) {
      const addExpanded = (nodes) => nodes.map(n => ({
        ...n,
        expanded: false,
        children: n.children ? addExpanded(n.children) : []
      }))
      moduleTree.value = addExpanded(res.data || [])
    }
  } catch (error) {
    console.error('加载模块树失败', error)
  }
}

// 扁平化模块树（根据展开状态）
const flatModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (node.expanded && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(moduleTree.value, 0)
  return result
})

const toggleTestCaseModule = (modulePath) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === modulePath) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(moduleTree.value)
}

const handleTestCaseModuleClick = (modulePath) => {
  testcaseFilter.module = modulePath
  testcaseFilter.subModule = ''
  selectorPage.value = 1
  loadTestCasesForSelector()
}

const handleSelectorLevelChange = () => {
  selectorPage.value = 1
  loadTestCasesForSelector()
}

const handleSelectorStatusChange = () => {
  selectorPage.value = 1
  loadTestCasesForSelector()
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

const selectAllTestCases = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('请先选择用例库')
    return
  }
  
  selectingAll.value = true
  try {
    // 使用 all-ids 接口，不受后端100条分页限制
    const params = {
      keyword: selectorSearchKeyword.value
        ? (selectorRegexMode.value ? `regex:${selectorSearchKeyword.value}` : selectorSearchKeyword.value)
        : undefined,
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      status_in: selectorStatusFilter.value ? selectorStatusFilter.value : 'REVIEWED,PENDING'
    }
    
    if (selectorLevelFilter.value.length > 0) {
      params.level_in = selectorLevelFilter.value.join(',')
    }

    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    
    const res = await getAllTestCaseIds(params)
    if (res.code === 200) {
      const allRecords = res.data.records || []
      
      // 直接替换临时选择列表为所有用例（去重）
      const existingIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
      const newRecords = allRecords.filter(tc => !existingIds.has(tc.id))
      tempSelectedTestCases.value = [...tempSelectedTestCases.value, ...newRecords]
      
      // 使用nextTick确保DOM更新后再同步表格选中状态
      await nextTick()
      
      // 同步表格的选中状态
      if (selectorTable.value) {
        isRestoringSelection.value = true
        const selectedIds = new Set(tempSelectedTestCases.value.map(tc => tc.id))
        testCases.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          selectorTable.value.toggleRowSelection(row, shouldSelect)
        })
        await nextTick()
        isRestoringSelection.value = false
      }
      
      ElMessage.success(t('testplan.selectedCases', { count: allRecords.length }))
    }
  } catch (error) {
    const msg = error?.response?.data?.detail
    if (msg) {
      ElMessage.error(msg)
    } else {
      console.error('全选失败:', error)
      ElMessage.error('全选失败')
    }
  } finally {
    selectingAll.value = false
  }
}

const handleSelectorSelectionChange = (selection) => {
  // 恢复选中状态期间跳过，避免清空已选
  if (isRestoringSelection.value) return
  
  // 获取当前页面的所有用例ID
  const currentPageIds = new Set(testCases.value.map(tc => tc.id))
  
  // 移除当前页面的所有用例（无论是否选中）
  const otherPagesSelected = tempSelectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))
  
  // 添加当前页面新选中的用例
  tempSelectedTestCases.value = [...otherPagesSelected, ...selection]
}

const confirmTestCaseSelection = async () => {
  // 检查是否有待评审或评审未通过的用例
  const pendingTestCases = tempSelectedTestCases.value.filter(tc => tc.status === 'PENDING')
  const rejectedTestCases = tempSelectedTestCases.value.filter(tc => tc.status === 'REJECTED')
  
  if (pendingTestCases.length > 0 || rejectedTestCases.length > 0) {
    let message = ''
    if (pendingTestCases.length > 0 && rejectedTestCases.length > 0) {
      message = `存在 ${pendingTestCases.length} 个待评审用例和 ${rejectedTestCases.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    } else if (pendingTestCases.length > 0) {
      message = `存在 ${pendingTestCases.length} 个待评审用例，需要先完成评审后再进行关联。`
    } else {
      message = `存在 ${rejectedTestCases.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    }
    
    try {
      await ElMessageBox.confirm(
        message,
        t('common.tip'),
        {
          confirmButtonText: t('common.understood'),
          showCancelButton: false,
          type: 'warning'
        }
      )
    } catch (error) {
      // 用户点击了确定或关闭
    }
    return
  }
  
  // 直接用当前选择替换，支持取消勾选
  const selectedIds = tempSelectedTestCases.value.map(tc => tc.id)
  form.testCaseIds = [...new Set(selectedIds)]
  
  testCaseSelectorVisible.value = false
  tempSelectedTestCases.value = []
  ElMessage.success(t('testplan.casesLinked', { count: form.testCaseIds.length }))
}

const handleCreate = async () => {
  isEdit.value = false
  editId.value = null
  form.name = ''
  form.description = ''
  form.startTime = null
  form.endTime = null
  form.testCaseIds = []
  form.executorIds = []
  form.viewerIds = []
  form.reviewerId = null
  form.suiteIds = []
  suiteSourceIds.value = new Set()
  
  // 加载当前用户角色
  await loadCurrentUserRole()
  
  // 加载项目成员和套件列表
  await loadProjectMembers()
  await loadSuiteOptions()
  
  dialogVisible.value = true
}

// 从测试用例页面跳转过来，预选中指定的用例
const handleCreateWithTestcases = async (testcaseIds) => {
  isEdit.value = false
  editId.value = null
  form.name = ''
  form.description = ''
  form.startTime = null
  form.endTime = null
  form.testCaseIds = testcaseIds
  form.executorIds = []
  form.viewerIds = []
  form.reviewerId = null
  form.suiteIds = []
  suiteSourceIds.value = new Set()
  
  // 加载当前用户角色
  await loadCurrentUserRole()
  
  // 加载项目成员和套件列表
  await loadProjectMembers()
  await loadSuiteOptions()
  
  dialogVisible.value = true
}

const loadSuiteOptions = async () => {
  if (!currentTeam.value?.id) { suiteOptions.value = []; return }
  try {
    const res = await getTestSuites({ team_id: currentTeam.value.id, size: 1000 })
    suiteOptions.value = res.data?.records || []
  } catch (e) { suiteOptions.value = [] }
}

const handleSuiteChange = async (suiteIds) => {
  // 用来跟踪每个套件贡献的用例，以便移除套件时能准确撤销
  // 策略：重新从所有已选套件加载用例，和手动选的用例合并
  if (!suiteIds || suiteIds.length === 0) {
    // 清空所有套件时，只保留手动添加的用例（即不来自任何套件的用例）
    form.testCaseIds = form.testCaseIds.filter(id => !suiteSourceIds.value.has(id))
    suiteSourceIds.value = new Set()
    return
  }
  try {
    // 并发加载所有已选套件的详情
    const results = await Promise.all(suiteIds.map(id => getTestSuiteDetail(id)))
    
    // 检查是否有待评审的用例，收集有效套件的用例
    const rejectedSuiteIds = new Set()
    for (let i = 0; i < results.length; i++) {
      const res = results[i]
      if (res.data?.pending_count > 0) {
        ElMessage.warning(t('suite.pendingReviewWarning', { count: res.data.pending_count }))
        rejectedSuiteIds.add(suiteIds[i])
      }
    }
    // 移除有问题的套件
    if (rejectedSuiteIds.size > 0) {
      form.suiteIds = form.suiteIds.filter(id => !rejectedSuiteIds.has(id))
    }
    
    // 收集有效套件的用例ID（跳过被拒绝的套件）
    const newSuiteIds = new Set()
    for (let i = 0; i < results.length; i++) {
      if (rejectedSuiteIds.has(suiteIds[i])) continue
      if (results[i].data?.test_case_ids) {
        results[i].data.test_case_ids.forEach(id => newSuiteIds.add(id))
      }
    }
    
    // 保留之前手动选择的（不来自套件的）用例，再叠加新套件的用例
    const manualIds = form.testCaseIds.filter(id => !suiteSourceIds.value.has(id))
    suiteSourceIds.value = newSuiteIds
    form.testCaseIds = [...new Set([...manualIds, ...newSuiteIds])]
  } catch (e) { console.error('加载套件详情失败:', e) }
}

const handleSubmit = async () => {
  if (!form.name) {
    ElMessage.warning(t('testplan.inputName'))
    return
  }
  if (!form.startTime) {
    ElMessage.warning(t('testplan.selectStartTime'))
    return
  }
  if (!form.endTime) {
    ElMessage.warning(t('testplan.selectEndTime'))
    return
  }

  if (form.testCaseIds.length === 0) {
    ElMessage.warning(t('testplan.selectTestCasesRequired'))
    return
  }

  if (form.executorIds.length === 0) {
    ElMessage.warning(t('testplan.selectExecutorsRequired'))
    return
  }
  
  if (!form.reviewerId) {
    ElMessage.warning(t('testplan.selectReviewer'))
    return
  }
  
  // 校验：查看人和执行人不能重叠
  if (form.viewerIds.length > 0 && form.executorIds.length > 0) {
    const overlap = form.viewerIds.filter(id => form.executorIds.includes(id))
    if (overlap.length > 0) {
      ElMessage.warning(t('testplan.viewerExecutorOverlap'))
      return
    }
  }

  // 检查是否存在待评审或评审未通过的用例
  const pendingTestCases = testCaseList.value.filter(tc => tc.status === 'PENDING')
  const rejectedTestCases = testCaseList.value.filter(tc => tc.status === 'REJECTED')
  
  if (pendingTestCases.length > 0 || rejectedTestCases.length > 0) {
    let message = ''
    if (pendingTestCases.length > 0 && rejectedTestCases.length > 0) {
      message = t('testplan.pendingAndRejectedCases', { pending: pendingTestCases.length, rejected: rejectedTestCases.length })
    } else if (pendingTestCases.length > 0) {
      message = t('testplan.pendingCasesWarning', { count: pendingTestCases.length })
    } else {
      message = t('testplan.rejectedCasesWarning', { count: rejectedTestCases.length })
    }
    
    ElMessageBox.alert(
      message,
      t('common.tip'),
      {
        confirmButtonText: t('common.understood'),
        type: 'warning'
      }
    )
    return
  }

  submitting.value = true
  try {
    // Convert camelCase to snake_case for backend
    // 日期格式保持为 YYYY-MM-DD，与后端期望的格式一致
    const payload = {
      name: form.name,
      description: form.description,
      start_time: form.startTime,
      end_time: form.endTime,
      project_id: currentProjectId.value,
      team_id: currentTeam.value?.id,
      suite_id: form.suiteIds.length > 0 ? form.suiteIds[0] : null,
      test_case_ids: form.testCaseIds,
      executor_ids: form.executorIds,
      viewer_ids: form.viewerIds,
      reviewer_id: form.reviewerId
    }
    
    if (isEdit.value) {
      await updateTestPlan(editId.value, payload)
      ElMessage.success(t('testplan.updateSuccess'))
    } else {
      await createTestPlan(payload)
      ElMessage.success(t('testplan.createSuccess'))
    }
    
    dialogVisible.value = false
    loadData()
    eventBus.emit('testplans-changed')
  } catch (error) {
    ElMessage.error(t('common.failed'))
  } finally {
    submitting.value = false
  }
}

const handleDialogClosed = () => {
  // 对话框关闭后,移除所有按钮的焦点
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

const handleEdit = async (row) => {
  isEdit.value = true
  editId.value = row.id
  editingLoading.value = true
  
  try {
    // 加载当前用户角色
    await loadCurrentUserRole()
    
    // 加载项目成员和套件列表
    await loadProjectMembers()
    await loadSuiteOptions()
    
    const res = await getTestPlanDetail(row.id, { all_cases: true })
    const data = res.data
    
    form.name = data.name
    form.description = data.description
    form.startTime = data.start_time ? data.start_time.split('T')[0] : null
    form.endTime = data.end_time ? data.end_time.split('T')[0] : null
    form.testCaseIds = data.test_case_ids || []
    form.executorIds = data.executor_ids || []
    form.viewerIds = data.viewer_ids || []
    form.reviewerId = data.reviewer_id || null
    // 兼容旧数据：后端仍存单个 suite_id，编辑时恢复成数组
    form.suiteIds = data.suite_id ? [data.suite_id] : []
    // 编辑时重新获取套件的用例ID，以便后续增删套件能准确区分手动选的用例
    if (data.suite_id) {
      try {
        const suiteRes = await getTestSuiteDetail(data.suite_id)
        suiteSourceIds.value = new Set(suiteRes.data?.test_case_ids || [])
      } catch (e) {
        suiteSourceIds.value = new Set()
      }
    } else {
      suiteSourceIds.value = new Set()
    }
    
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error(t('common.failed'))
  } finally {
    editingLoading.value = false
  }
}

const handleView = async (row) => {
  // 存储计划名称供详情页使用
  sessionStorage.setItem(`plan_name_${row.id}`, row.name)
  // 跳转到测试计划详情页，加全局 loading 提示
  loadingStore.showLoading('加载测试计划详情...')
  router.push(`/testplans/${row.id}`)
}

// 跳转到报告详情页
const goToReport = (reportId) => {
  router.push(`/reports/review/${reportId}`)
}

// 查看测试用例列表
const viewTestCases = async () => {
  testCaseList.value = viewData.value.test_cases || []
  testCaseListVisible.value = true
  
  // 加载模块树
  if (viewData.value.project_id) {
    try {
      const res = await getModuleTree(viewData.value.project_id)
      if (res.code === 200) {
        const addExpanded = (nodes) => nodes.map(n => ({
          ...n,
          expanded: false,
          children: n.children ? addExpanded(n.children) : []
        }))
        viewModuleTree.value = addExpanded(res.data || [])
      }
    } catch (error) {
      console.error('加载模块树失败', error)
    }
  }
  
  // 初始化筛选
  viewTestCaseFilter.module = ''
  viewTestCaseFilter.subModule = ''
  viewTestCaseSearchKeyword.value = ''
  filterViewTestCases()
}

// 显示添加用例到查看对话框
const showAddTestCaseToViewDialog = () => {
  // 关闭查看用例对话框
  testCaseListVisible.value = false
  // 打开添加用例选择器
  testCaseSelectorVisible.value = true
  // 重置选择器状态
  selectorSearchKeyword.value = ''
  selectorRegexMode.value = false
  selectorLevelFilter.value = []
  selectorStatusFilter.value = ''
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  selectorPage.value = 1
  tempSelectedTestCases.value = []
  // 加载用例
  loadTestCasesForSelector()
}

// 从查看对话框移除用例
const removeTestCaseFromView = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('testplan.confirmRemoveCase', { number: row.case_number }),
      t('testplan.confirmRemoveTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    ElMessage.success(t('testplan.removeSuccess'))
    
    // 重新加载测试计划详情
    await handleView({ id: viewData.value.id })
    
    // 重新筛选显示
    filterViewTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('testplan.removeFailed'))
    }
  }
}

// 切换查看用例模块展开/收起
const toggleViewTestCaseModule = (modulePath) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === modulePath) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(viewModuleTree.value)
}

// 扁平化查看用例模块树
const flatViewModuleTree = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({ ...node, depth })
      if (node.expanded && node.children && node.children.length > 0) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(viewModuleTree.value, 0)
  return result
})

// 处理查看用例模块点击
const handleViewTestCaseModuleClick = (module, subModule) => {
  viewTestCaseFilter.module = module
  viewTestCaseFilter.subModule = subModule
  viewTestCasePage.value = 1
  filterViewTestCases()
}

// 筛选查看用例
const filterViewTestCases = () => {
  let filtered = testCaseList.value
  
  // 按模块筛选
  if (viewTestCaseFilter.module) {
    filtered = filtered.filter(tc => {
      if (viewTestCaseFilter.subModule) {
        return tc.module === viewTestCaseFilter.module && tc.sub_module === viewTestCaseFilter.subModule
      } else {
        return tc.module === viewTestCaseFilter.module
      }
    })
  }
  
  // 按关键词筛选
  if (viewTestCaseSearchKeyword.value) {
    const keyword = viewTestCaseSearchKeyword.value.toLowerCase()
    filtered = filtered.filter(tc => 
      tc.case_number?.toLowerCase().includes(keyword) ||
      tc.name?.toLowerCase().includes(keyword)
    )
  }
  
  filteredViewTestCases.value = filtered
}

// 处理查看用例分页大小变化
const handleViewTestCasePageSizeChange = () => {
  viewTestCasePage.value = 1
}

// 处理查看用例页码变化
const handleViewTestCasePageChange = () => {
  // 页码变化时不需要额外操作，分页由el-pagination自动处理
}

// 判断当前用户是否可以编辑该测试计划（管理员、项目组负责人、或创建人，且状态非已完成）
const canEditPlan = (row) => {
  if (row.status === 'COMPLETED') return false
  if (isSuperAdmin.value || isAdmin.value) return true
  if (currentUserRole.value === 'leader' || currentUserRole.value === 'org_manager') return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return row.created_by === currentUserId
}

// 判断当前用户是否可以执行该测试计划（管理员、项目组/组织负责人、或执行人）
const canExecutePlan = (row) => {
  if (isSuperAdmin.value || isAdmin.value) return true
  // 项目组负责人或组织负责人可以执行任何计划
  if (currentUserRole.value === 'leader' || currentUserRole.value === 'org_manager') return true
  const currentUserId = JSON.parse(localStorage.getItem('user') || '{}').id
  return row.executors && row.executors.some(e => e.id === currentUserId)
}

// 处理开始执行操作
const handleStartExecution = async (row) => {
  try {
    // 直接跳转到测试执行页面，不修改状态
    // 用户可以随时进入和退出执行页面，状态由实际执行情况决定
    router.push(`/testplans/${row.id}/execution`)
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 撤回审核
const handleWithdrawReview = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('execution.withdrawReviewConfirm'),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    const res = await withdrawTestPlanReview(row.id)
    if (res.code === 200) {
      ElMessage.success(t('execution.withdrawReviewSuccess'))
      loadData()
      eventBus.emit('testplans-changed')
    }
  } catch (error) {
    if (error !== 'cancel' && error?.toString?.()?.includes?.('cancel') !== true) {
      ElMessage.error(t('execution.operationFailed'))
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(
      t('testplan.deleteConfirm'),
      t('common.warning'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    await deleteTestPlan(row.id)
    ElMessage.success(t('testplan.deleteSuccess'))
    loadData()
    eventBus.emit('testplans-changed')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('common.failed'))
    }
  }
}

const handleDropdownCommand = (command, row) => {
  if (command === 'delete') {
    handleDelete(row)
  }
}

const handleExportCommand = async (command, row) => {
  try {
    // 优先使用列表已返回的报告信息，避免额外请求
    let reportId = row.report_id
    let reportName = row.report_name
    
    if (!reportId) {
      // 兜底：列表未返回报告信息时，查询一次
      const { getReports } = await import('../../api/report')
      const res = await getReports({ test_plan_id: row.id, status: 'APPROVED', page: 1, size: 1 })
      
      if (res.data.records.length === 0) {
        ElMessage.warning('该测试计划没有已审核通过的报告')
        return
      }
      
      const report = res.data.records[0]
      reportId = report.id
      reportName = (report.project_name || report.name || '').replace(/\s*-\s*测试报告$/, '')
    }
    
    if (command === 'excel') {
      await exportReportExcel(reportId, reportName)
      ElMessage.success('Excel导出成功')
    } else if (command === 'pdf') {
      await exportReportPdf(reportId, reportName)
      ElMessage.success('PDF导出成功')
    }
  } catch (error) {
    console.error('导出失败:', error)
    ElMessage.error('导出失败')
  }
}

watch(currentTeam, async () => {
  if (currentTeam.value) {
    // 项目组变化时，重置用例库选择
    resetPreference()
    await loadTeamProjects()
    if (teamProjectList.value.length > 0) {
      applyPreference(teamProjectList.value)
    }
    loadData()
  }
})

// 监听用例库列表变化，自动应用偏好（不重复loadData，由currentTeam watch统一处理）
watch(teamProjectList, (list) => {
  if (list && list.length > 0) {
    applyPreference(list)
  }
})

onMounted(async () => {
  // 刷新页面时 teamProjects 可能还没加载完，需要等待
  if (teamProjectList.value.length === 0 && currentTeam.value) {
    await loadTeamProjects()
    if (teamProjectList.value.length > 0) {
      applyPreference(teamProjectList.value)
    }
  }
  loadCurrentUserRole()
  loadData()
  initEventListeners()
  
  // 检查是否有从测试用例页面传递过来的用例ID
  const routeQuery = router.currentRoute.value.query
  if (routeQuery.action === 'create' && routeQuery.testcase_ids) {
    const testcaseIds = routeQuery.testcase_ids.split(',').map(id => parseInt(id)).filter(id => !isNaN(id))
    if (testcaseIds.length > 0) {
      // 清除路由参数，避免刷新时重复触发
      router.replace({ query: {} })
      // 打开创建对话框并预选中用例
      await handleCreateWithTestcases(testcaseIds)
    }
  }
})

onBeforeUnmount(() => {
  cleanupEventListeners()
})

// keep-alive 缓存后从子页面返回时，只刷新数据，不重复初始化事件监听
onActivated(() => {
  loadData()
})
</script>

<style scoped>
/* ==================== */
/* TestPlanList - Demo Theme */
/* ==================== */

.testplan-container {
  height: 100%;
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
}

.testplan-container :deep(.el-card) {
  height: 100%;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.testplan-container :deep(.el-card__body) {
  height: 100%;
  padding: 0 !important;
}

.testplan-container :deep(.el-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.testplan-container :deep(.el-tabs__header) {
  padding: 0 20px;
  margin-bottom: 0;
  border-bottom: 1px solid #e2e8f0;
}

.testplan-container :deep(.el-tabs__item) {
  font-weight: 500;
  color: #64748b;
  font-size: 14px;
}

.testplan-container :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
}

.testplan-container :deep(.el-tabs__active-bar) {
  background-color: #4f46e5;
}

.testplan-container :deep(.el-tabs__content) {
  flex: 1;
  overflow: hidden;
}

.testplan-container :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px;
  border-bottom: 1px solid #e2e8f0;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

.header-right :deep(.el-select),
.header-right :deep(.el-input) {
  height: 32px;
}

.header-right :deep(.el-select .el-input__wrapper),
.header-right :deep(.el-input__wrapper) {
  height: 32px;
  box-sizing: border-box;
}

/* 统计卡片 - Demo风格 */
.stats-cards {
  display: flex;
  gap: 10px;
  padding: 10px 20px;
  flex-wrap: wrap;
  background: var(--demo-bg-card, #ffffff);
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--demo-bg, #f8fafc);
  border-radius: 6px;
  min-width: 100px;
  transition: all 0.15s;
  cursor: pointer;
  border: 1px solid transparent;
}

.stat-card:hover {
  background: var(--demo-border-light, #f1f5f9);
  border-color: var(--demo-border, #e2e8f0);
}

.stat-card.active {
  border-color: var(--demo-primary, #4f46e5);
  background: var(--demo-primary-light, #eef2ff);
}

.stat-label {
  font-size: 12px;
  color: var(--demo-text-muted, #64748b);
  white-space: nowrap;
  font-weight: 500;
}

.stat-value {
  font-size: 15px;
  font-weight: 700;
  color: var(--demo-text-primary, #0f172a);
}

/* 表格容器 - Demo风格 */
.plan-table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  overflow: hidden;
}

.plan-table-wrapper .table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.plan-table-wrapper :deep(.el-table) {
  width: 100%;
  table-layout: fixed;
}

.plan-table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden;
  position: sticky;
  top: 0;
  z-index: 900;
  background: white;
}

.plan-table-wrapper :deep(.el-table__body-wrapper) {
  overflow: auto;
}

/* Demo风格表头 */
.plan-table-wrapper :deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
  color: var(--demo-text-muted, #64748b) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  padding: 4px 8px !important;
}

/* 表格行悬停效果 - Demo风格 */
.plan-table-wrapper :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

.plan-table-wrapper :deep(.el-table__row:hover) {
  background: #f8fafc !important;
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #f8fafc !important;
}

/* 滚动条样式 - Demo风格 */
.plan-table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.plan-table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.plan-table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.plan-table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: var(--demo-border-light, #f1f5f9);
}

.plan-table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar {
  height: 8px;
}

.plan-table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.plan-table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.plan-table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar-track {
  background: var(--demo-border-light, #f1f5f9);
}

/* Firefox 滚动条样式 */
.plan-table-wrapper :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light, #f1f5f9);
}

.plan-table-wrapper :deep(.el-table__header-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light, #f1f5f9);
}

/* 确保表格内容与表头对齐 */
.plan-table-wrapper :deep(.el-table td.el-table__cell) {
  text-align: center !important;
  vertical-align: middle !important;
  padding: 4px 8px !important;
  color: var(--demo-text-primary, #0f172a);
  background: #fff;
}

.plan-table-wrapper :deep(.el-table__row:hover > td.el-table__cell) {
  background: #f8fafc !important;
}

.plan-table-wrapper :deep(.el-table td.el-table__cell .cell) {
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 100% !important;
  height: 100% !important;
  text-align: center !important;
}

/* 确保表头和表体使用相同的布局和宽度 */
.plan-table-wrapper :deep(.el-table__header) {
  table-layout: fixed;
  width: 100%;
}

.plan-table-wrapper :deep(.el-table__body) {
  table-layout: fixed;
  width: 100%;
}

/* 同步表头和表体的滚动 */
.plan-table-wrapper :deep(.el-table__header-wrapper) {
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.plan-table-wrapper :deep(.el-table__header-wrapper)::-webkit-scrollbar {
  display: none;
}

/* 终极方案：直接覆盖 Element Plus 的 .cell 样式 */
.plan-table-wrapper :deep(.el-table .el-table__cell .cell) {
  padding-left: 0 !important;
  padding-right: 0 !important;
  text-align: center !important;
}

/* 确保所有内容都居中 */
.plan-table-wrapper :deep(.el-table .el-table__cell .cell > *) {
  text-align: center !important;
  margin: 0 auto !important;
}

/* 确保表头和表体一起滚动 */
.plan-table-wrapper {
  overflow-x: auto !important;
}

.plan-table-wrapper :deep(.el-table) {
  overflow: visible !important;
}

.plan-table-wrapper :deep(.el-table__body-wrapper) {
  overflow-x: hidden !important;
  overflow-y: auto !important;
}

.plan-table-wrapper :deep(.el-table__header-wrapper) {
  overflow-x: hidden !important;
}

/* 确保在不同屏幕尺寸下对齐 */
.plan-table-wrapper :deep(.el-table__header),
.plan-table-wrapper :deep(.el-table__body) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 响应式调整 */
@media (max-width: 1440px) {
  .plan-table-wrapper :deep(.el-table th.el-table__cell) {
    padding: 4px 4px !important;
  }
  .plan-table-wrapper :deep(.el-table td.el-table__cell) {
    padding: 4px 4px !important;
  }
  
  .plan-table-wrapper :deep(.el-table th.el-table__cell .cell),
  .plan-table-wrapper :deep(.el-table td.el-table__cell .cell) {
    padding: 0 4px !important;
  }
}

/* 省略号文本样式 */
.ellipsis-text {
  width: 100% !important;
  max-width: 230px !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  text-align: center !important;
  display: inline-block !important;
}

/* 可点击的计划名称样式 - Demo风格 */
.clickable-name {
  color: var(--demo-primary, #4f46e5);
  cursor: pointer;
  transition: all 0.15s;
  display: block;
  width: 100%;
  text-align: center;
  font-weight: 500;
}

.clickable-name:hover {
  color: var(--demo-primary-hover, #4338ca);
  text-decoration: underline;
}

/* 调整操作列按钮间距和对齐 */
.plan-table-wrapper :deep(.el-table td.el-table__cell .cell) {
  gap: 8px !important;
  justify-content: center !important;
  align-items: center !important;
}

.plan-table-wrapper :deep(.el-table td.el-table__cell .cell .el-button) {
  margin-right: 4px !important;
  margin-left: 4px !important;
}

/* 进度条样式优化 */
:deep(.el-progress__text) {
  display: none;
}

:deep(.el-progress-bar) {
  padding-right: 0;
  margin-right: 0;
}

.pagination-container {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  min-height: 56px;
}

/* 分页器按钮样式 */
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

/* 确保表格操作列按钮对齐 */
.plan-table-wrapper :deep(.el-table td.el-table__cell .cell) {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: center;
  align-items: center;
  min-height: 48px;
}

.plan-table-wrapper :deep(.el-table td.el-table__cell .cell .el-button) {
  margin: 0;
  flex-shrink: 0;
}

.plan-table-wrapper :deep(.el-table td.el-table__cell .cell .el-dropdown) {
  flex-shrink: 0;
}

/* 对话框样式 - Demo风格 */
:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: var(--demo-text-primary, #0f172a);
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--demo-text-secondary, #475569);
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  border-radius: 8px;
  border: 1px solid var(--demo-border, #e2e8f0);
  box-shadow: none;
}

:deep(.el-input__wrapper:hover),
:deep(.el-textarea__inner:hover) {
  border-color: #cbd5e1;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-textarea__inner:focus) {
  border-color: var(--demo-primary, #4f46e5);
  box-shadow: 0 0 0 2px rgba(79, 70, 229, 0.1);
}

/* 按钮样式 - Demo风格 */
.el-button {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s;
}

.el-button:hover {
  transform: none;
}

.el-button:active {
  transform: none;
}

:deep(.el-button--primary) {
  background: var(--demo-primary, #4f46e5);
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--primary:hover) {
  background: var(--demo-primary-hover, #4338ca);
}

/* 测试用例选择器样式 - Demo风格 */
.testcase-selector-dialog :deep(.el-dialog__body) {
  padding: 0;
}

/* 用例选择对话框样式 */
.testcase-select-container {
  display: flex;
  height: calc(100vh - 200px);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 8px;
  overflow: visible;
}

.module-sidebar {
  width: 220px;
  border-right: 1px solid var(--demo-border, #e2e8f0);
  background-color: var(--demo-bg-card, #ffffff);
  display: flex;
  flex-direction: column;
  overflow: visible;
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

.module-count {
  font-size: 12px;
  color: var(--demo-text-muted, #64748b);
  background: var(--demo-border-light, #f1f5f9);
  padding: 2px 8px;
  border-radius: 12px;
}

.module-item.active .module-count {
  background: rgba(79, 70, 229, 0.1);
  color: var(--demo-primary, #4f46e5);
}

.sub-module-list {
  background-color: rgba(248, 250, 252, 0.5);
}

.sub-module {
  padding-left: 40px;
  font-size: 13px;
}

.testcase-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
  overflow: hidden;
  background-color: var(--demo-bg-card, #ffffff);
}

.testcase-content .testcase-filter {
  margin-bottom: 16px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
}

.testcase-content .testcase-filter :deep(.el-input__wrapper) {
  height: 32px;
  box-sizing: border-box;
}

.testcase-filter {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

/* 表格容器 - Demo风格 */
.table-wrapper {
  flex: 1;
  width: 100%;
  overflow: visible;
  position: relative;
  min-height: 400px;
  max-height: calc(100vh - 320px);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 8px;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
  height: 100%;
  position: relative;
}

/* Demo风格表头 */
.table-wrapper :deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
  color: var(--demo-text-muted, #64748b) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
}

/* 设置表格单元格高度 */
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

/* 表格内部垂直和水平滚动 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

/* 表头不滚动 */
.table-wrapper :deep(.el-table__header-wrapper) {
  overflow: hidden !important;
  position: relative;
  z-index: 10 !important;
}

/* 确保表体内容正确显示 */
.table-wrapper :deep(.el-table__body-wrapper) {
  position: relative;
  z-index: 5 !important;
}

/* 确保单元格内容不溢出 */
.table-wrapper :deep(.el-table__cell) {
  overflow: hidden;
  position: relative;
  z-index: 1;
}

/* 确保表头和表体宽度一致 */
.table-wrapper :deep(.el-table__header),
.table-wrapper :deep(.el-table__body) {
  width: 100% !important;
}

/* 使用固定布局确保列宽一致 */
.table-wrapper :deep(.el-table__header) {
  table-layout: fixed !important;
}

.table-wrapper :deep(.el-table__body) {
  table-layout: fixed !important;
}

/* Tooltip 样式 */
.steps-tooltip {
  max-width: 600px !important;
}

/* 文本内容 tooltip 样式 */
.text-tooltip {
  max-width: 500px !important;
  word-break: break-word;
  line-height: 1.6;
}

/* 单行省略号样式 */
.single-line-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

/* 标签省略号样式 */
.ellipsis-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

/* 多选框样式优化 */
:deep(.el-table .el-checkbox) {
  transform: scale(1.3);
}

:deep(.el-table .el-checkbox__inner) {
  width: 16px;
  height: 16px;
  border-width: 2px;
}

:deep(.el-table .el-checkbox__inner::after) {
  width: 4px;
  height: 8px;
  border-width: 2px;
}

/* 多选框列不影响其他列对齐 */
:deep(.el-table .el-table-column--selection .cell) {
  padding: 0 !important;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 用例库选择器样式 - Demo风格 */
.project-filter-section {
  padding: 12px 14px;
  background: rgba(248, 250, 252, 0.5);
  overflow: visible;
  position: relative;
  z-index: 100;
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}

.project-filter-section .section-header {
  font-weight: 600;
  font-size: 12px;
  color: var(--demo-text-light, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 10px;
}

.project-filter-content {
  padding: 0;
  overflow: visible;
  position: relative;
}

/* Demo风格操作按钮 - link类型 */
:deep(.el-button.is-link),
:deep(.el-button[link]),
:deep(.el-button--link) {
  background: transparent !important;
  border: none !important;
  padding: 4px 8px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  height: auto !important;
}

:deep(.el-button--primary.is-link),
:deep(.el-button--primary[link]),
:deep(.el-button--primary.el-button--link) {
  color: var(--demo-primary, #4f46e5) !important;
  background: transparent !important;
}

:deep(.el-button--primary.is-link:hover),
:deep(.el-button--primary[link]:hover),
:deep(.el-button--primary.el-button--link:hover) {
  color: var(--demo-primary-hover, #4338ca) !important;
  background: var(--demo-primary-light, #eef2ff) !important;
  border-radius: 4px !important;
}

:deep(.el-button--info.is-link),
:deep(.el-button--info[link]),
:deep(.el-button--info.el-button--link) {
  color: var(--demo-text-muted, #64748b) !important;
  background: transparent !important;
}

:deep(.el-button--info.is-link:hover),
:deep(.el-button--info[link]:hover),
:deep(.el-button--info.el-button--link:hover) {
  color: var(--demo-text-secondary, #475569) !important;
  background: var(--demo-border-light, #f1f5f9) !important;
  border-radius: 4px !important;
}

/* 表格内操作按钮样式 - Demo风格 */
:deep(.el-table .el-button.is-link),
:deep(.el-table .el-button[link]),
:deep(.el-table .el-button--link) {
  padding: 4px 8px !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  background: transparent !important;
  border: none !important;
  height: auto !important;
}

:deep(.el-table .el-button--primary.is-link),
:deep(.el-table .el-button--primary[link]),
:deep(.el-table .el-button--primary.el-button--link) {
  color: var(--demo-primary, #4f46e5) !important;
}

:deep(.el-table .el-button--primary.is-link:hover),
:deep(.el-table .el-button--primary[link]:hover),
:deep(.el-table .el-button--primary.el-button--link:hover) {
  color: var(--demo-primary-hover, #4338ca) !important;
  background: var(--demo-primary-light, #eef2ff) !important;
  border-radius: 4px !important;
}

/* Demo风格状态标签 */
:deep(.el-tag--info) {
  background: var(--demo-bg, #f8fafc) !important;
  color: var(--demo-text-muted, #64748b) !important;
  border-color: var(--demo-border, #e2e8f0) !important;
}

:deep(.el-tag--warning) {
  background: #fffbeb !important;
  color: #b45309 !important;
  border-color: rgba(180, 83, 9, 0.3) !important;
}

:deep(.el-tag--primary) {
  background: var(--demo-primary-light, #eef2ff) !important;
  color: var(--demo-primary, #4f46e5) !important;
  border-color: rgba(79, 70, 229, 0.3) !important;
}

:deep(.el-tag--danger) {
  background: #fef2f2 !important;
  color: #be123c !important;
  border-color: rgba(190, 18, 60, 0.3) !important;
}

:deep(.el-tag--success) {
  background: #ecfdf5 !important;
  color: #047857 !important;
  border-color: rgba(4, 120, 87, 0.3) !important;
}

:deep(.el-tag) {
  border-radius: 6px !important;
  font-weight: 500 !important;
}
</style>
