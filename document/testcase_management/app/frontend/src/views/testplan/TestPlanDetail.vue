<template>
  <div class="plan-detail-container">
      <!-- 头部 -->
      <div class="detail-header">
        <el-button @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          {{ $t('common.back') }}
        </el-button>
        <h2 style="margin: 0 0 0 20px;">{{ planDetail.name }}</h2>
        <div style="flex: 1"></div>
        <el-button 
          type="primary" 
          @click="showEditDialog" 
          v-if="canEdit && planDetail.status !== 'COMPLETED'"
        >
          <el-icon><Edit /></el-icon>
          {{ $t('common.edit') }}
        </el-button>
      </div>

      <!-- 基本信息 -->
      <div class="info-section">
        <div class="section-title">{{ $t('testplan.basicInfo') }}</div>
        <div class="info-grid">
          <div class="info-item">
            <span class="info-label">{{ $t('testplan.planId') }}:</span>
            <span class="info-value">
              {{ planDetail.id }}
              <el-tooltip :content="$t('testplan.copyPlanIdTip')" placement="top" :show-after="500">
                <el-button 
                  link 
                  size="small" 
                  @click="copyPlanId"
                  style="margin-left: 4px; padding: 0;"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </el-tooltip>
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('testplan.planStatus') }}:</span>
            <el-tag v-if="planDetail.status === 'PENDING'" type="info">{{ $t('testplan.statusNotStarted') }}</el-tag>
            <el-tag v-else-if="planDetail.status === 'IN_PROGRESS'" type="warning">{{ $t('testplan.statusInProgress') }}</el-tag>
            <el-tag v-else-if="planDetail.status === 'COMPLETED'" type="success">{{ $t('testplan.statusCompleted') }}</el-tag>
            <el-tag v-else-if="planDetail.status === 'CANCELLED'" type="info">{{ $t('testplan.statusCancelled') }}</el-tag>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('testplan.planName') }}:</span>
            <span class="info-value">{{ planDetail.name }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('testplan.executors') }}:</span>
            <span class="info-value">{{ planDetail.executor_names?.join(', ') || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('testplan.reviewer') }}:</span>
            <span class="info-value">{{ planDetail.reviewer_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('testcase.creator') }}:</span>
            <span class="info-value">{{ planDetail.creator_name || '-' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('common.createdAt') }}:</span>
            <span class="info-value">{{ formatDateTime(planDetail.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('common.updatedAt') }}:</span>
            <span class="info-value">{{ formatDateTime(planDetail.updated_at) }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">{{ $t('testplan.executionPeriod') }}:</span>
            <span class="info-value">
              <span v-if="planDetail.start_time && planDetail.end_time">
                {{ formatDateOnly(planDetail.start_time) }} {{ $t('common.to') }} {{ formatDateOnly(planDetail.end_time) }}
              </span>
              <span v-else>-</span>
            </span>
          </div>
          <div class="info-item full-width">
            <span class="info-label">描述：</span>
            <span class="info-value">{{ planDetail.description || '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 执行统计 -->
      <div class="stats-section">
        <div class="section-title-row">
          <span class="section-title">执行统计</span>
          <el-tooltip content="查看执行总览" placement="top" :show-after="500">
            <button class="overview-entry-btn" @click="openExecutionOverview">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/></svg>
              <span>执行总览</span>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
            </button>
          </el-tooltip>
        </div>
        <div class="stats-cards">
          <div class="stat-card">
            <span class="stat-label">总用例数</span>
            <span class="stat-value">{{ planDetail.total_testcases }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">总进度</span>
            <span class="stat-value" :style="{ color: getAllProgressColor() }">{{ allProgress.executed_pct }}%</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">通过率</span>
            <span class="stat-value" :style="{ color: getPassRateColor() }">
              {{ passRate }}%
            </span>
          </div>
          <div class="stat-card">
            <span class="stat-label">未执行</span>
            <span class="stat-value" style="color: #909399;">{{ (planDetail.total_testcases || 0) - (statistics.executed || 0) }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">已执行</span>
            <span class="stat-value" style="color: var(--primary-100);">{{ statistics.executed || 0 }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">PASS</span>
            <span class="stat-value" style="color: #67c23a;">{{ statistics.passed || 0 }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">FAIL</span>
            <span class="stat-value" style="color: var(--accent-100);">{{ statistics.failed || 0 }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">BLOCK</span>
            <span class="stat-value" style="color: #e6a23c;">{{ statistics.blocked || 0 }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">NA</span>
            <span class="stat-value" style="color: #909399;">{{ statistics.na || 0 }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-label">NT</span>
            <span class="stat-value" style="color: #909399;">{{ statistics.nt || 0 }}</span>
          </div>
        </div>
      </div>

      <!-- 模块执行进度 -->
      <div class="stats-section" v-if="moduleProgressList.length > 0">
        <div class="section-title">模块执行进度</div>
        <div class="module-progress-grid">
          <!-- 整体进度卡片 -->
          <div class="module-progress-item">
            <div class="module-progress-header">
              <span class="module-progress-name">All</span>
              <span class="module-progress-pct" :style="{ color: getAllProgressColor() }">
                {{ $t('testplan.progress') }}：{{ allProgress.executed_pct }}%
              </span>
            </div>
            <div class="module-progress-bar-bg">
              <div 
                class="module-progress-bar-fill"
                :style="{ width: allProgress.executed_pct + '%', background: getAllBarGradient() }"
              ></div>
            </div>
            <div class="module-progress-detail">
              <span>{{ allProgress.executed }}/{{ allProgress.total }}</span>
              <span>{{ $t('testplan.passRate') }}：{{ allProgress.pass_rate }}%</span>
            </div>
          </div>
          <div 
            v-for="mod in moduleProgressList" 
            :key="mod.name" 
            class="module-progress-item"
          >
            <div class="module-progress-header">
              <span class="module-progress-name">{{ mod.name }}</span>
              <span class="module-progress-pct" :style="{ color: getModuleProgressColor(mod.executed_pct) }">
                {{ $t('testplan.progress') }}：{{ mod.executed_pct }}%
              </span>
            </div>
            <div class="module-progress-bar-bg">
              <div 
                class="module-progress-bar-fill"
                :style="{ width: mod.executed_pct + '%', background: getModuleBarGradient(mod) }"
              ></div>
            </div>
            <div class="module-progress-detail">
              <span>{{ mod.executed }}/{{ mod.total }}</span>
              <span>{{ $t('testplan.passRate') }}：{{ mod.pass_rate }}%</span>
            </div>
            <div class="module-progress-rd-owner" v-if="mod.rd_owner">
              <span>RD Owner：{{ mod.rd_owner }}</span>
            </div>
          </div>
        </div>
      </div>

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
            <span>{{ $t('testplan.module') }}</span>
          </div>
          <div class="module-list">
            <div 
              class="module-item" 
              :class="{ active: testcaseFilter.module === '' }"
              @click="handleModuleClick('')"
            >
              <span class="module-name">{{ $t('testplan.allModules') }}</span>
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
                @click.stop="toggleModule(item.path)"
              >
                <ArrowRight v-if="!item.expanded" />
                <ArrowDown v-else />
              </el-icon>
              <div class="module-content" @click="handleModuleClick(item.path)">
                <span class="module-name">{{ item.name }}<span v-if="item.tag" style="color: #409eff; margin-left: 2px;">({{ item.tag }})</span></span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 右侧用例列表 -->
        <div class="testcase-content">
          <div class="testcase-filter">
            <el-input
              v-model="testcaseSearchKeyword"
              :placeholder="$t('testplan.searchCaseName')"
              clearable
              style="width: 300px; margin-right: 10px"
              @keyup.enter="handleTestcaseSearch"
              @clear="handleTestcaseSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
            <el-button type="primary" @click="handleTestcaseSearch">
              <el-icon><Search /></el-icon>
              {{ $t('common.search') }}
            </el-button>
            
            <el-button 
              @click="selectAllCurrentModule"
              :disabled="availableTestCases.length === 0"
              style="margin-left: 10px"
              :loading="selectingAll"
            >
              {{ $t('testplan.selectCurrentModule') }}
            </el-button>
            
            <div style="flex: 1"></div>
            
            <el-button 
              type="primary" 
              :disabled="selectedTestCases.length === 0"
              @click="confirmAddTestCases"
            >
              {{ $t('testplan.linkCasesCount', { count: selectedTestCases.length }) }}
            </el-button>
          </div>
          
          <div class="table-wrapper">
            <el-table
              ref="testcaseTableRef"
              :data="availableTestCases"
              style="width: 100%"
              :height="dialogTableHeight"
              border
              :header-cell-style="{ background: '#f0f1fb', color: 'var(--text-200)', fontWeight: '600' }"
              v-loading="testcaseLoading"
              :element-loading-text="$t('testplan.loading')"
              @selection-change="handleTestCaseSelectionChange"
            >
              <el-table-column type="selection" width="50" align="center" />
              <el-table-column prop="case_number" :label="$t('testplan.caseNumber')" width="230" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              <el-table-column prop="name" :label="$t('testplan.caseTitle')" min-width="200" align="left" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <div class="single-line-ellipsis">{{ scope.row.name }}</div>
                </template>
              </el-table-column>
              <el-table-column prop="precondition" :label="$t('testcase.precondition')" min-width="200" align="left" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  <div class="single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
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
                          <span style="color: #8b9aee; font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
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
                          <span style="color: #8b9aee; font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
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
              <el-table-column prop="status" label="状态" width="140" align="center" resizable>
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" type="success" size="small">已评审</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" type="warning" size="small">待评审</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" type="danger" size="small">评审未通过</el-tag>
                  <el-tag v-else-if="scope.row.status === 'DEPRECATED'" type="info" size="small">废弃</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              <el-table-column prop="level" label="用例等级" width="140" align="center" resizable />
              <el-table-column label="创建人" width="120" align="center" resizable :show-overflow-tooltip="{ showAfter: 500 }">
                <template #default="scope">
                  {{ scope.row.creator_name || '-' }}
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-pagination
            v-model:current-page="testcasePagination.page"
            v-model:page-size="testcasePagination.size"
            :page-sizes="[10, 20, 50, 100]"
            :total="testcasePagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="() => { loadAvailableTestCases(); scrollToTop(); }"
            @current-change="() => { loadAvailableTestCases(); scrollToTop(); }"
            style="margin-top: 20px; justify-content: flex-end"
          />
        </div>
      </div>
    </el-dialog>

    <!-- 编辑测试计划对话框 -->
  <el-dialog
    v-model="editDialogVisible"
    title="编辑测试计划"
    width="700px"
  >
    <el-form
      ref="editFormRef"
      :model="editForm"
      label-width="100px"
    >
      <el-form-item label="计划名称" prop="name" :rules="[{ required: true, message: '请输入计划名称', trigger: 'blur' }]">
        <el-input v-model="editForm.name" placeholder="请输入计划名称" />
      </el-form-item>
      
      <el-form-item label="描述">
        <el-input
          v-model="editForm.description"
          type="textarea"
          :rows="3"
          placeholder="请对该测试计划进行描述"
        />
      </el-form-item>
      
      <el-form-item label="执行人" prop="executor_ids">
        <el-select
          ref="executorSelectRef"
          v-model="editForm.executor_ids"
          multiple
          placeholder="请选择执行人"
          style="width: 100%"
          filterable
          remote
          :remote-method="handleExecutorSearch"
          :loading="executorSearchLoading"
          :disabled="!canEditExecutors"
          @focus="loadProjectMembers"
          @change="handleExecutorChange"
        >
          <el-option
            v-for="member in projectMembers"
            :key="member.id"
            :label="member.username"
            :value="member.id"
          />
        </el-select>
        <div v-if="!canEditExecutors" style="margin-top: 4px; color: #909399; font-size: 12px;">
          仅项目组负责人或组织负责人可编辑执行人
        </div>
      </el-form-item>

      <el-form-item label="审核人" prop="reviewer_id">
        <el-select
          v-model="editForm.reviewer_id"
          placeholder="请选择审核人"
          style="width: 100%"
          filterable
        >
          <el-option
            v-for="member in availableReviewers"
            :key="member.id"
            :label="member.username"
            :value="member.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="执行周期">
        <el-date-picker
          v-model="executionTimeRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          style="width: 100%"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="submitEdit" :loading="submitting">保存</el-button>
    </template>
  </el-dialog>
  <!-- ===== 执行总览 Drawer ===== -->
  <el-drawer
    v-model="overviewVisible"
    direction="rtl"
    size="100%"
    :with-header="false"
    :modal="true"
    :append-to-body="true"
    class="execution-overview-drawer"
    @open="onOverviewOpen"
  >
    <div class="ov-root">
      <!-- 顶部导航栏 -->
      <div class="ov-navbar">
        <div class="ov-navbar-left">
          <button class="ov-back-btn" @click="overviewVisible = false">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
          </button>
          <div class="ov-plan-title">
            <span class="ov-plan-label">执行总览</span>
            <span class="ov-plan-name">{{ planDetail.name }}</span>
          </div>
        </div>
        <div class="ov-navbar-right">
          <!-- 状态标签 -->
          <span class="ov-status-badge" :class="'ov-status-' + (planDetail.status || 'PENDING').toLowerCase()">
            {{ { PENDING: '未开始', IN_PROGRESS: '进行中', COMPLETED: '已完成', CANCELLED: '已取消' }[planDetail.status] || planDetail.status }}
          </span>
          <!-- 搜索框 -->
          <div class="ov-search-wrap">
            <svg class="ov-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
            <input
              v-model="ovSearch"
              class="ov-search-input"
              placeholder="搜索用例名称 / 编号..."
              @input="onOvSearch"
            />
            <button v-if="ovSearch" class="ov-search-clear" @click="ovSearch=''; onOvSearch()">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            </button>
          </div>
          <!-- 视图切换 -->
          <div class="ov-view-toggle">
            <button :class="['ov-view-btn', ovViewMode === 'table' && 'active']" @click="ovViewMode='table'" title="表格视图">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
            </button>
            <button :class="['ov-view-btn', ovViewMode === 'card' && 'active']" @click="ovViewMode='card'" title="卡片视图">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>
            </button>
          </div>
          <!-- 导出按钮 -->
          <button class="ov-export-btn" v-if="planDetail.status === 'COMPLETED'" @click="exportReport">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            导出报告
          </button>
        </div>
      </div>

      <!-- 主体内容 -->
      <div class="ov-body">
        <!-- 左侧：统计面板 -->
        <div class="ov-sidebar">
          <!-- 整体进度环 -->
          <div class="ov-progress-ring-card">
            <div class="ov-ring-wrap">
              <svg class="ov-ring-svg" viewBox="0 0 120 120">
                <!-- 背景灰圈（未执行部分兜底） -->
                <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" stroke-width="12"/>
                <!-- 多段色环：PASS / FAIL / BLOCK / NA / NT 依次绘制 -->
                <circle
                  v-for="seg in ovRingSegments"
                  :key="seg.key"
                  cx="60" cy="60" r="50" fill="none"
                  :stroke="seg.color"
                  stroke-width="12"
                  :stroke-dasharray="`${seg.len} 314.159`"
                  :stroke-dashoffset="seg.offset"
                  transform="rotate(-90 60 60)"
                  style="transition: stroke-dasharray 0.5s ease, stroke-dashoffset 0.5s ease"
                />
              </svg>
              <div class="ov-ring-center">
                <span class="ov-ring-pct">{{ allProgress.executed_pct }}%</span>
                <span class="ov-ring-label">执行进度</span>
              </div>
            </div>
            <div class="ov-ring-stats">
              <div class="ov-ring-stat-item">
                <span class="ov-ring-stat-val">{{ allProgress.total }}</span>
                <span class="ov-ring-stat-key">总用例</span>
              </div>
              <div class="ov-ring-stat-item">
                <span class="ov-ring-stat-val" style="color:#4f46e5">{{ allProgress.executed }}</span>
                <span class="ov-ring-stat-key">已执行</span>
              </div>
              <div class="ov-ring-stat-item">
                <span class="ov-ring-stat-val" style="color:#22c55e">{{ passRate }}%</span>
                <span class="ov-ring-stat-key">通过率</span>
              </div>
            </div>
          </div>

          <!-- 状态分布 -->
          <div class="ov-status-dist">
            <div class="ov-sidebar-title">状态分布</div>
            <div class="ov-status-bars">
              <div
                v-for="s in ovStatusList"
                :key="s.key"
                class="ov-status-bar-item"
                :class="{ 'ov-status-active': ovStatusFilter === s.key }"
                @click="ovToggleStatus(s.key)"
              >
                <div class="ov-status-bar-header">
                  <span class="ov-status-dot" :style="{ background: s.color }"></span>
                  <span class="ov-status-bar-label">{{ s.label }}</span>
                  <span class="ov-status-bar-count" :style="{ color: s.color }">{{ s.count }}</span>
                </div>
                <div class="ov-status-bar-track">
                  <div
                    class="ov-status-bar-fill"
                    :style="{ width: ovStatusBarWidth(s.count) + '%', background: s.color }"
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <!-- 模块进度 -->
          <div class="ov-module-progress" v-if="moduleProgressList.length > 0">
            <div class="ov-sidebar-title">模块进度</div>
            <div class="ov-module-list">
              <div
                v-for="mod in moduleProgressList"
                :key="mod.name"
                class="ov-module-item"
                :class="{ 'ov-module-active': ovModuleFilter === mod.name }"
                @click="ovToggleModule(mod.name)"
              >
                <div class="ov-module-header">
                  <span class="ov-module-name" :title="mod.name">{{ mod.name }}</span>
                  <span class="ov-module-pct" :style="{ color: getModuleProgressColor(mod.executed_pct) }">进度 {{ mod.executed_pct }}%</span>
                </div>
                <div class="ov-module-bar-track">
                  <div class="ov-module-bar-fill" :style="{ width: mod.executed_pct + '%', background: getModuleBarGradient(mod) }"></div>
                </div>
                <div class="ov-module-detail">
                  <span>{{ mod.executed }}/{{ mod.total }}</span>
                  <span style="color:#67c23a">通过率 {{ mod.pass_rate }}%</span>
                </div>
                <div class="ov-module-rd" v-if="mod.rd_owner" :title="'RD Owner：' + mod.rd_owner">
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  <span>RD：{{ mod.rd_owner }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧：用例列表 -->
        <div class="ov-main">
          <!-- 筛选条 -->
          <div class="ov-filter-bar">
            <div class="ov-filter-chips">
              <button
                v-for="s in [{ key: null, label: '全部', color: '#64748b' }, ...ovStatusList]"
                :key="s.key"
                class="ov-chip"
                :class="{ 'ov-chip-active': ovStatusFilter === s.key }"
                :style="ovStatusFilter === s.key ? { background: s.color + '18', color: s.color, borderColor: s.color } : {}"
                @click="ovToggleStatus(s.key)"
              >
                <span v-if="s.key" class="ov-chip-dot" :style="{ background: s.color }"></span>
                {{ s.label }}
                <span class="ov-chip-count">{{ s.key ? s.count : ovStatusBarBase }}</span>
              </button>
            </div>
            <div class="ov-filter-right">
              <span class="ov-result-count">
                显示 <strong>{{ ovFilteredList.length }}</strong> 条
                <template v-if="ovModuleFilter"> · {{ ovModuleFilter }}</template>
              </span>
              <button v-if="ovStatusFilter || ovModuleFilter || ovSearch" class="ov-clear-filter" @click="ovClearFilters">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                清除筛选
              </button>
            </div>
          </div>

          <!-- 表格视图 -->
          <div v-if="ovViewMode === 'table'" class="ov-table-wrap" v-loading="ovLoading">
            <table class="ov-table">
              <colgroup>
                <col style="width:120px" />
                <col style="width:140px" />
                <col style="width:180px" />
                <col style="width:200px" />
                <col style="width:200px" />
                <col style="width:56px" />
                <col style="width:76px" />
                <col style="width:80px" />
                <col style="width:150px" />
              </colgroup>
              <thead>
                <tr>
                  <th class="ov-th">用例编号</th>
                  <th class="ov-th">模块</th>
                  <th class="ov-th">用例标题</th>
                  <th class="ov-th">操作步骤</th>
                  <th class="ov-th">预期结果</th>
                  <th class="ov-th ov-th-center">等级</th>
                  <th class="ov-th ov-th-center">执行结果</th>
                  <th class="ov-th ov-th-center">执行人</th>
                  <th class="ov-th ov-th-center">执行备注</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="(row, idx) in ovPagedList"
                  :key="row.id"
                  class="ov-tr"
                  :class="'ov-row-' + (row.execution_status || 'PENDING').toLowerCase()"
                >
                  <td class="ov-td">
                    <span class="ov-case-num">{{ row.case_number || '-' }}</span>
                  </td>
                  <td class="ov-td">
                    <span class="ov-module-tag">{{ row.module }}{{ row.sub_module ? ' / ' + row.sub_module : '' }}</span>
                  </td>
                  <td class="ov-td">
                    <span class="ov-cell-wrap">{{ row.name || '-' }}</span>
                  </td>
                  <td class="ov-td">
                    <div class="ov-steps-list">
                      <div
                        v-for="(step, si) in parseSteps(row.steps)"
                        :key="si"
                        class="ov-step-item"
                      >
                        <span class="ov-step-num">{{ si + 1 }}.</span>
                        <span class="ov-step-text">{{ step }}</span>
                      </div>
                      <span v-if="!parseSteps(row.steps).length" class="ov-cell-muted">-</span>
                    </div>
                  </td>
                  <td class="ov-td">
                    <div class="ov-steps-list">
                      <div
                        v-for="(res, ri) in parseExpected(row.expected_result)"
                        :key="ri"
                        class="ov-step-item"
                      >
                        <span class="ov-step-num">{{ ri + 1 }}.</span>
                        <span class="ov-step-text">{{ res }}</span>
                      </div>
                      <span v-if="!parseExpected(row.expected_result).length" class="ov-cell-muted">-</span>
                    </div>
                  </td>
                  <td class="ov-td ov-td-center">
                    <span class="ov-level-badge" :class="'ov-level-' + (row.level || '').toLowerCase()">{{ row.level || '-' }}</span>
                  </td>
                  <td class="ov-td ov-td-center">
                    <span class="ov-exec-badge" :class="'ov-exec-' + (row.execution_status || 'PENDING').toLowerCase()">
                      {{ { PENDING: '未执行', PASS: 'PASS', FAIL: 'FAIL', BLOCK: 'BLOCK', NA: 'NA', NT: 'NT' }[row.execution_status] || '未执行' }}
                    </span>
                  </td>
                  <td class="ov-td ov-td-center">
                    <span class="ov-cell-wrap ov-executor">{{ row.execution_executor || '-' }}</span>
                  </td>
                  <td class="ov-td ov-td-center">
                    <span class="ov-cell-wrap ov-remark-text" v-if="row.execution_remark" v-html="renderRemarkWithPR(row.execution_remark)"></span>
                    <span v-else class="ov-cell-muted">-</span>
                  </td>
                </tr>
                <tr v-if="ovPagedList.length === 0">
                  <td colspan="9" class="ov-empty">
                    <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                    <span>暂无匹配的用例</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 卡片视图 -->
          <div v-else class="ov-card-grid" v-loading="ovLoading">
            <div
              v-for="(row, idx) in ovPagedList"
              :key="row.id"
              class="ov-case-card"
              :class="'ov-card-' + (row.execution_status || 'PENDING').toLowerCase()"
            >
              <div class="ov-card-header">
                <span class="ov-card-num" :title="row.case_number">{{ row.case_number }}</span>
                <span class="ov-exec-badge" :class="'ov-exec-' + (row.execution_status || 'PENDING').toLowerCase()">
                  {{ { PENDING: '未执行', PASS: 'PASS', FAIL: 'FAIL', BLOCK: 'BLOCK', NA: 'NA', NT: 'NT' }[row.execution_status] || '未执行' }}
                </span>
              </div>
              <div class="ov-card-name" :title="row.name">{{ row.name }}</div>
              <div class="ov-card-meta">
                <span class="ov-module-tag">{{ row.module }}{{ row.sub_module ? ' / ' + row.sub_module : '' }}</span>
                <span class="ov-level-badge" :class="'ov-level-' + (row.level || '').toLowerCase()">{{ row.level || '-' }}</span>
              </div>
              <div class="ov-card-remark" v-if="row.execution_remark" v-html="renderRemarkWithPR(row.execution_remark)"></div>
            </div>
            <div v-if="ovPagedList.length === 0" class="ov-empty-card">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <span>暂无匹配的用例</span>
            </div>
          </div>

          <!-- 分页 -->
          <div class="ov-pagination">
            <span class="ov-page-info">第 {{ ovPage }} / {{ ovTotalPages }} 页，共 {{ ovFilteredList.length }} 条</span>
            <div class="ov-page-btns">
              <button class="ov-page-btn" :disabled="ovPage <= 1" @click="ovPage = 1">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="11 17 6 12 11 7"/><polyline points="18 17 13 12 18 7"/></svg>
              </button>
              <button class="ov-page-btn" :disabled="ovPage <= 1" @click="ovPage--">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
              </button>
              <button
                v-for="p in ovPageNumbers"
                :key="p"
                class="ov-page-num"
                :class="{ active: p === ovPage, ellipsis: p === '...' }"
                :disabled="p === '...'"
                @click="p !== '...' && (ovPage = p)"
              >{{ p }}</button>
              <button class="ov-page-btn" :disabled="ovPage >= ovTotalPages" @click="ovPage++">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>
              </button>
              <button class="ov-page-btn" :disabled="ovPage >= ovTotalPages" @click="ovPage = ovTotalPages">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="13 17 18 12 13 7"/><polyline points="6 17 11 12 6 7"/></svg>
              </button>
            </div>
            <div class="ov-page-size-wrap">
              <span>每页</span>
              <select class="ov-page-size-select" v-model="ovPageSize" @change="ovPage=1">
                <option :value="20">20</option>
                <option :value="50">50</option>
                <option :value="100">100</option>
                <option :value="200">200</option>
              </select>
              <span>条</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </el-drawer>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, computed, nextTick, watch } from 'vue'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Plus, CircleClose, Search, ArrowRight, ArrowDown, Edit, CopyDocument, Loading } from '@element-plus/icons-vue'
import { getTestPlanDetail, addTestCasesToPlan, removeTestCaseFromPlan, updateTestPlan } from '@/api/testplan'
import { getTestCases, getAllTestCaseIds } from '@/api/testcase'
import { getModuleTree } from '@/api/module'
import { getUsers } from '@/api/user'
import { getAvailableMembersForSelection, getUserRoleInTeam } from '@/api/team'
import { useUserRole } from '@/composables/useUserRole'
import { useTeam } from '@/composables/useTeam'
import ProjectSelector from '../../components/ProjectSelector.vue'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'
import { useProjectPreference } from '../../composables/useProjectPreference'
import { renderRemarkWithPR } from '../../composables/useRemarkPR'

const router = useRouter()
const route = useRoute()
const { isAdmin } = useUserRole()
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()
const loadingStore = useLoadingStore()

// 用例库选择相关
const { selectedProjectIdList, applyPreference, updateSelection, resetPreference } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])

// 计算当前选中的用例库ID列表
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0 
    ? selectedProjectIdList.value 
    : teamProjectList.value.map(p => p.id)
})

// 处理用例库选择器变化（防抖，防止快速切换导致数据错乱）
let _projectChangeTimer = null
const handleProjectSelectorChange = (ids) => {
  updateSelection(ids)
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  clearTimeout(_projectChangeTimer)
  _projectChangeTimer = setTimeout(() => {
    loadModuleTree()
    loadAvailableTestCases()
  }, 300)
}

const planId = route.params.id
const loading = ref(false)
const removing = ref(false)  // 防止重复移除
const planDetail = ref({})
const testcaseList = ref([])
const allTestcases = ref([])  // 保存所有用例数据（用于统计）
const searchKeyword = ref('')
const statusFilter = ref(null)

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 表格容器引用
const tableWrapperRef = ref(null)
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef)

const handleTestCasesPageChange = async (page, size) => {
  pagination.page = page
  if (size) pagination.size = size
  await loadPlanDetail()
  await nextTick()
  scrollToTop()
}

// 处理表格滚动同步
const handleTableScroll = (event) => {
  if (!tableWrapperRef.value) return
  
  const scrollLeft = event.target.scrollLeft
  
  // 同步表头和表体的滚动位置
  const headerWrapper = tableWrapperRef.value.querySelector('.el-table__header-wrapper')
  const bodyWrapper = tableWrapperRef.value.querySelector('.el-table__body-wrapper')
  
  if (headerWrapper) {
    headerWrapper.scrollLeft = scrollLeft
  }
  
  if (bodyWrapper) {
    bodyWrapper.scrollLeft = scrollLeft
  }
}

// 对话框中表格的高度
const dialogTableHeight = ref('calc(100vh - 350px)')

// 统计数据 - 直接使用后端返回数据
const statistics = computed(() => {
  return planDetail.value.statistics || { executed: 0, passed: 0, failed: 0, blocked: 0, na: 0, nt: 0 }
})

// 编辑相关
const editDialogVisible = ref(false)
const editFormRef = ref(null)
const editForm = reactive({
  name: '',
  description: '',
  executor_ids: [],
  reviewer_id: null,
  start_time: null,
  end_time: null,
  project_id: null
})
const executionTimeRange = ref(null)
const projectMembers = ref([])
const availableReviewers = ref([])
const executorSearchLoading = ref(false)
const executorSelectRef = ref(null)
const editUserRole = ref('')
const submitting = ref(false)

// 编辑时是否可以修改执行人（仅负责人/组织负责人/超级管理员）
const canEditExecutors = computed(() => {
  return isAdmin.value || editUserRole.value === 'org_manager' || editUserRole.value === 'leader'
})

// 添加用例相关
const addTestCaseDialogVisible = ref(false)
const availableTestCases = ref([])
const selectedTestCases = ref([])
const isRestoringSelection = ref(false)
const testcaseSearchKeyword = ref('')
const testcaseLoading = ref(false)
const testcaseTableRef = ref(null)
const moduleTree = ref([])
let _moduleTreeVer = 0
let _selectorVer = 0
const selectingAll = ref(false)
const testcaseFilter = reactive({
  module: '',
  subModule: ''
})
const testcasePagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

// 权限控制
const canEdit = computed(() => {
  if (isAdmin.value) return true
  const currentUserId = JSON.parse(localStorage.getItem('user')).id
  return planDetail.value.created_by === currentUserId
})

// 通过率
const passRate = computed(() => {
  // 使用后端返回的全部用例数，而不是当前页的用例数
  const total = planDetail.value.total_testcases || 0
  const passed = statistics.value.passed || 0
  const na = statistics.value.na || 0
  const assist = statistics.value.assist || 0
  const validTestcases = total - na - assist
  if (validTestcases === 0) return '0.00'
  return ((passed / validTestcases) * 100).toFixed(2)
})

// 整体进度 - 直接使用后端返回数据
const allProgress = computed(() => {
  const total = planDetail.value.total_testcases || 0
  const executed = planDetail.value.statistics?.executed || 0
  const passed = planDetail.value.statistics?.passed || 0
  const executed_pct = planDetail.value.executed_pct || '0.00'
  const pass_rate = planDetail.value.pass_rate || '0.00'
  return { total, executed, passed, executed_pct, pass_rate }
})

// 整体进度颜色
const getAllProgressColor = () => {
  const r = parseFloat(allProgress.value.executed_pct)
  if (r >= 100) return '#67c23a'
  if (r >= 50) return 'var(--demo-primary, #4f46e5)'
  if (r > 0) return '#e6a23c'
  return '#c0c4cc'
}

// 整体进度条渐变
const getAllBarGradient = () => {
  const { total, executed, passed, na } = allProgress.value
  if (executed === 0) return '#c0c4cc'
  
  const passPct = (passed / total) * 100
  const executedNotPass = executed - passed
  const executedNotPassPct = (executedNotPass / total) * 100
  const notExecutedPct = ((total - executed) / total) * 100
  
  if (passed === 0 && executed > 0) return '#f56c6c'
  if (passed > 0 && executed === passed) return '#67c23a'
  
  const stops = []
  let pos = 0
  if (passPct > 0) {
    stops.push(`#67c23a ${pos}%`, `#67c23a ${pos + passPct}%`)
    pos += passPct
  }
  if (executedNotPassPct > 0) {
    stops.push(`#f56c6c ${pos}%`, `#f56c6c ${pos + executedNotPassPct}%`)
    pos += executedNotPassPct
  }
  if (notExecutedPct > 0) {
    stops.push(`#e5e7eb ${pos}%`, `#e5e7eb ${pos + notExecutedPct}%`)
  }
  return `linear-gradient(to right, ${stops.join(', ')})`
}

// 通过率颜色
const getPassRateColor = () => {
  const rate = passRate.value
  if (rate >= 90) return '#67c23a'
  if (rate >= 70) return '#e6a23c'
  return 'var(--accent-100)'
}

// 主模块的 RD Owner 映射
const mainModuleRdOwnerMap = ref({})

// 加载主模块的 RD Owner
const loadMainModuleRdOwners = async () => {
  if (currentProjectIds.value.length === 0) return
  try {
    const projectParam = currentProjectIds.value.join(',')
    const res = await getModuleTree(projectParam)
    if (res.code === 200) {
      const map = {}
      const extractRdOwner = (nodes) => {
        for (const node of nodes) {
          if (node.rd_owner) {
            map[node.name] = node.rd_owner
          }
          if (node.children && node.children.length > 0) {
            extractRdOwner(node.children)
          }
        }
      }
      extractRdOwner(res.data || [])
      mainModuleRdOwnerMap.value = map
    }
  } catch (error) {
    console.error('加载模块RD Owner失败', error)
  }
}

// 模块执行进度 - 直接使用后端返回数据
const moduleProgressList = computed(() => {
  return planDetail.value.module_stats || []
})

// 模块进度颜色（基于执行进度）
const getModuleProgressColor = (executedPct) => {
  const r = parseFloat(executedPct)
  if (r >= 100) return '#67c23a'
  if (r >= 50) return 'var(--demo-primary, #4f46e5)'
  if (r > 0) return '#e6a23c'
  return '#c0c4cc'
}

// 模块进度条渐变（绿色=PASS，红色=FAIL，橙色=BLOCK，灰色=其他已执行）
const getModuleBarGradient = (mod) => {
  if (mod.executed === 0) return '#c0c4cc'
  const passPct = (mod.passed / mod.total) * 100
  const failPct = (mod.failed / mod.total) * 100
  const blockPct = (mod.blocked / mod.total) * 100
  const otherPct = ((mod.executed - mod.passed - mod.failed - mod.blocked) / mod.total) * 100
  
  // 如果只有一种状态，直接返回纯色
  if (mod.failed === 0 && mod.blocked === 0 && otherPct === 0) return '#67c23a'
  if (mod.passed === 0 && mod.blocked === 0 && otherPct === 0) return '#f56c6c'
  
  // 多种状态用渐变
  const stops = []
  let pos = 0
  if (passPct > 0) {
    stops.push(`#67c23a ${pos}%`, `#67c23a ${pos + passPct}%`)
    pos += passPct
  }
  if (failPct > 0) {
    stops.push(`#f56c6c ${pos}%`, `#f56c6c ${pos + failPct}%`)
    pos += failPct
  }
  if (blockPct > 0) {
    stops.push(`#e6a23c ${pos}%`, `#e6a23c ${pos + blockPct}%`)
    pos += blockPct
  }
  if (otherPct > 0) {
    stops.push(`#909399 ${pos}%`, `#909399 ${pos + otherPct}%`)
  }
  return `linear-gradient(to right, ${stops.join(', ')})`
}

// 用例列表 - 直接使用后端返回的分页数据
const filteredTestcaseList = computed(() => {
  return allTestcases.value
})

// 筛选状态（点击统计卡片时）
const filterByStatus = (status) => {
  statusFilter.value = status
  pagination.page = 1
  loadPlanDetail()
}

// 搜索处理
const handleSearch = () => {
  pagination.page = 1
  loadPlanDetail()
}

// 加载测试计划详情（支持分页、搜索、筛选）
const loadPlanDetail = async (params = {}, isInitial = false) => {
  testcaseLoading.value = true
  try {
    const queryParams = {
      page: pagination.page,
      size: pagination.size,
      ...params
    }
    if (searchKeyword.value) {
      queryParams.keyword = searchKeyword.value
    }
    if (statusFilter.value) {
      queryParams.status = statusFilter.value
    }
    const res = await getTestPlanDetail(planId, queryParams)
    if (res.code === 200) {
      planDetail.value = res.data
      allTestcases.value = res.data.test_cases || []
      pagination.total = res.data.pagination?.total || 0

      if (res.data.all_statistics) {
        planDetail.value.statistics = res.data.all_statistics
      }

      // 存储计划名称供数据埋点使用
      if (res.data.name) {
        sessionStorage.setItem(`plan_name_${planId}`, res.data.name)
      }
    }
  } catch (error) {
    ElMessage.error('加载测试计划详情失败')
  } finally {
    testcaseLoading.value = false
    if (isInitial) {
      loadingStore.hideLoading()
    }
  }
}

// 加载测试用例列表（直接使用已加载数据）
const loadTestCases = () => {
  testcaseLoading.value = true
  setTimeout(() => {
    allTestcases.value = planDetail.value.test_cases || []
    setTimeout(() => {
      testcaseLoading.value = false
    }, 100)
  }, 50)
}

// 继续执行
const continueExecution = () => {
  router.push(`/testplans/${planId}/execution`)
}

// 导出报告
const exportReport = () => {
  ElMessage.info('导出报告功能开发中...')
}

// 返回
const goBack = () => {
  if (route.query.from === 'task-overview') {
    router.back()
  } else {
    router.push('/testplans')
  }
}

// 复制计划ID
const copyPlanId = () => {
  const id = String(planDetail.value.id)
  const textarea = document.createElement('textarea')
  textarea.value = id
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  document.execCommand('copy')
  document.body.removeChild(textarea)
  ElMessage.success('计划ID已复制到剪贴板')
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

// 格式化日期（只显示年月日）
const formatDateOnly = (date) => {
  if (!date) return '-'
  // 如果是字符串且包含空格，提取日期部分
  if (typeof date === 'string' && date.includes(' ')) {
    return date.split(' ')[0]
  }
  // 如果是日期对象或其他格式，格式化为 YYYY-MM-DD
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 显示添加用例对话框
const showAddTestCaseDialog = async () => {
  addTestCaseDialogVisible.value = true
  testcaseSearchKeyword.value = ''
  testcaseFilter.module = ''
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  selectedTestCases.value = []
  
  // 确保 teamProjects 已加载
  if (teamProjects.value.length === 0 && currentTeam.value) {
    await loadTeamProjects()
  }
  
  // 等待 Vue 渲染完成
  await nextTick()
  
  // 加载模块树
  await loadModuleTree()
  
  // 加载用例列表
  await loadAvailableTestCases()
}

// 加载模块树
const loadModuleTree = async () => {
  if (currentProjectIds.value.length === 0) return
  
  const ver = ++_moduleTreeVer
  try {
    const projectParam = currentProjectIds.value.join(',')
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

// 扁平化模块树
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

// 加载可用的测试用例
const loadAvailableTestCases = async () => {
  if (currentProjectIds.value.length === 0) {
    return
  }
  
  const ver = ++_selectorVer
  testcaseLoading.value = true
  try {
    const params = {
      page: testcasePagination.page,
      size: testcasePagination.size,
      project_ids: currentProjectIds.value.join(','),
      keyword: testcaseSearchKeyword.value || undefined,
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      status_in: 'REVIEWED,PENDING,REJECTED',  // 显示已评审、待评审和评审未通过状态的用例
      exclude_testplan_id: planId  // 排除当前测试计划中的用例
    }
    
    const res = await getTestCases(params)
    if (ver !== _selectorVer) return
    
    if (res.code === 200) {
      availableTestCases.value = res.data.records
      testcasePagination.total = res.data.total
      
      // 恢复之前选中的用例
      await nextTick()
      // 先清除所有选中状态，防止 row-key 复用导致残留勾选
      isRestoringSelection.value = true
      if (testcaseTableRef.value) {
        testcaseTableRef.value.clearSelection()
      }
      if (testcaseTableRef.value && selectedTestCases.value.length > 0) {
        availableTestCases.value.forEach(row => {
          if (selectedTestCases.value.some(selected => selected.id === row.id)) {
            testcaseTableRef.value.toggleRowSelection(row, true)
          }
        })
      }
      await nextTick()
      isRestoringSelection.value = false
    }
  } catch (error) {
    ElMessage.error('加载用例列表失败')
  } finally {
    testcaseLoading.value = false
  }
}

// 切换模块展开/收起
const toggleModule = (modulePath) => {
  const findAndToggle = (nodes) => {
    for (const n of nodes) {
      if (n.path === modulePath) { n.expanded = !n.expanded; return true }
      if (n.children && findAndToggle(n.children)) return true
    }
    return false
  }
  findAndToggle(moduleTree.value)
}

// 处理模块点击
const handleModuleClick = (modulePath) => {
  testcaseFilter.module = modulePath
  testcaseFilter.subModule = ''
  testcasePagination.page = 1
  loadAvailableTestCases()
}

// 搜索用例（重置到第一页）
const handleTestcaseSearch = () => {
  testcasePagination.page = 1
  loadAvailableTestCases()
}

// 处理用例选择变化
const handleTestCaseSelectionChange = (selection) => {
  // 恢复选中状态期间跳过，避免清空已选
  if (isRestoringSelection.value) return
  
  // 获取当前页面的所有用例ID
  const currentPageIds = new Set(availableTestCases.value.map(tc => tc.id))
  
  // 移除当前页面的所有用例（无论是否选中）
  const otherPagesSelected = selectedTestCases.value.filter(tc => !currentPageIds.has(tc.id))
  
  // 添加当前页面新选中的用例
  selectedTestCases.value = [...otherPagesSelected, ...selection]
}

// 全选当前模块
const selectAllCurrentModule = async () => {
  if (currentProjectIds.value.length === 0) {
    ElMessage.warning('请先选择用例库')
    return
  }
  
  selectingAll.value = true
  try {
    const params = {
      project_ids: currentProjectIds.value.join(','),
      keyword: testcaseSearchKeyword.value || undefined,
      module: (testcaseFilter.subModule ? `${testcaseFilter.module}/${testcaseFilter.subModule}` : testcaseFilter.module) || undefined,
      status_in: 'REVIEWED,PENDING,REJECTED',  // 显示已评审、待评审和评审未通过状态的用例
      exclude_testplan_id: planId  // 排除当前测试计划中的用例
    }
    
    const res = await getAllTestCaseIds(params)
    if (res.code === 200) {
      const allTestCases = res.data.records
      
      // 直接替换选择列表为所有用例（去重）
      const existingIds = new Set(selectedTestCases.value.map(tc => tc.id))
      const newTestCases = allTestCases.filter(tc => !existingIds.has(tc.id))
      selectedTestCases.value = [...selectedTestCases.value, ...newTestCases]
      
      // 使用nextTick确保DOM更新后再同步表格选中状态
      await nextTick()
      
      // 同步表格的选中状态
      if (testcaseTableRef.value) {
        const selectedIds = new Set(selectedTestCases.value.map(tc => tc.id))
        availableTestCases.value.forEach(row => {
          const shouldSelect = selectedIds.has(row.id)
          testcaseTableRef.value.toggleRowSelection(row, shouldSelect)
        })
      }
      
      ElMessage.success(`已选择 ${allTestCases.length} 条用例`)
    }
  } catch (error) {
    console.error('全选失败:', error)
    ElMessage.error('全选失败')
  } finally {
    selectingAll.value = false
  }
}

// 确认添加用例
const confirmAddTestCases = async () => {
  if (selectedTestCases.value.length === 0) {
    ElMessage.warning('请先选择用例')
    return
  }
  
  // 检查是否存在待评审或评审未通过的用例
  const pendingTestCases = selectedTestCases.value.filter(tc => tc.status === 'PENDING')
  const rejectedTestCases = selectedTestCases.value.filter(tc => tc.status === 'REJECTED')
  
  if (pendingTestCases.length > 0 || rejectedTestCases.length > 0) {
    let message = ''
    if (pendingTestCases.length > 0 && rejectedTestCases.length > 0) {
      message = `选择的用例中有 ${pendingTestCases.length} 个待评审用例和 ${rejectedTestCases.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    } else if (pendingTestCases.length > 0) {
      message = `选择的用例中有 ${pendingTestCases.length} 个待评审用例，需要先完成评审后再进行关联。`
    } else {
      message = `选择的用例中有 ${rejectedTestCases.length} 个评审未通过用例，需要先完成评审后再进行关联。`
    }
    
    ElMessageBox.alert(
      message,
      '提示',
      {
        confirmButtonText: '我知道了',
        type: 'warning'
      }
    )
    return
  }
  
  try {
    const testcaseIds = selectedTestCases.value.map(tc => tc.id)
    const res = await addTestCasesToPlan(planId, { testcase_ids: testcaseIds })
    if (res.code === 200) {
      ElMessage.success(`成功添加 ${res.data.added} 个用例`)
      addTestCaseDialogVisible.value = false
      await loadPlanDetail()
    }
  } catch (error) {
    ElMessage.error('添加用例失败')
  }
}

// 移除用例
const removeTestCase = async (row) => {
  if (removing.value) return
  removing.value = true
  try {
    await ElMessageBox.confirm(
      `确定要从测试计划中移除用例"${row.case_number}"吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    await removeTestCaseFromPlan(planId, row.id)
    ElMessage.success('移除成功')
    await loadPlanDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('移除失败')
    }
  } finally {
    removing.value = false
  }
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
        return text
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

const loadProjectMembers = async () => {
  const teamId = currentTeam.value?.id
  if (!teamId) return
  try {
    const executorRes = await getAvailableMembersForSelection(teamId, 'executor')
    if (executorRes.code === 200) {
      projectMembers.value = executorRes.data
    }
  } catch (error) {
    console.error('加载执行人列表失败', error)
  }
}

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
      projectMembers.value = res.data
    }
  } catch (error) {
    console.error('搜索执行人失败', error)
  } finally {
    executorSearchLoading.value = false
  }
}

// 选中后清空搜索框
const handleExecutorChange = () => clearSelectSearch(executorSelectRef)

// 显示编辑对话框
const showEditDialog = async () => {
  const teamId = currentTeam.value?.id
  
  // 加载当前用户在项目组中的角色
  if (teamId) {
    try {
      const roleRes = await getUserRoleInTeam(teamId)
      if (roleRes.code === 200) {
        editUserRole.value = roleRes.data.role
      }
    } catch (error) {
      console.error('加载用户角色失败', error)
    }
    
    // 加载执行人列表
    try {
      const executorRes = await getAvailableMembersForSelection(teamId, 'executor')
      if (executorRes.code === 200) {
        projectMembers.value = executorRes.data
      }
    } catch (error) {
      console.error('加载执行人列表失败', error)
    }
    
    // 加载审核人列表
    try {
      const reviewerRes = await getAvailableMembersForSelection(teamId, 'reviewer')
      if (reviewerRes.code === 200) {
        availableReviewers.value = reviewerRes.data
      }
    } catch (error) {
      console.error('加载审核人列表失败', error)
    }
  } else {
    // 回退：加载所有用户
    try {
      const res = await getUsers({ page: 1, size: 1000 })
      if (res.code === 200) {
        projectMembers.value = res.data.records
        availableReviewers.value = res.data.records
      }
    } catch (error) {
      console.error('加载项目成员失败', error)
    }
  }
  
  // 填充表单
  editForm.name = planDetail.value.name
  editForm.description = planDetail.value.description
  editForm.executor_ids = planDetail.value.executor_ids || []
  editForm.reviewer_id = planDetail.value.reviewer_id || null
  editForm.start_time = planDetail.value.start_time
  editForm.end_time = planDetail.value.end_time
  editForm.project_id = planDetail.value.project_id
  
  if (planDetail.value.start_time && planDetail.value.end_time) {
    executionTimeRange.value = [planDetail.value.start_time, planDetail.value.end_time]
  } else {
    executionTimeRange.value = null
  }
  
  editDialogVisible.value = true
}

// 提交编辑
const submitEdit = async () => {
  if (!editFormRef.value) return
  
  await editFormRef.value.validate(async (valid) => {
    if (!valid) return
    
    submitting.value = true
    try {
      // 处理时间范围 - 转换为 YYYY-MM-DD 格式
      if (executionTimeRange.value && executionTimeRange.value.length === 2) {
        // 如果是ISO格式（包含T），提取日期部分
        editForm.start_time = executionTimeRange.value[0].includes('T') 
          ? executionTimeRange.value[0].split('T')[0] 
          : executionTimeRange.value[0]
        editForm.end_time = executionTimeRange.value[1].includes('T') 
          ? executionTimeRange.value[1].split('T')[0] 
          : executionTimeRange.value[1]
      } else {
        editForm.start_time = null
        editForm.end_time = null
      }
      
      await updateTestPlan(planId, editForm)
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      await loadPlanDetail()
      eventBus.emit('testplans-changed')
    } catch (error) {
      ElMessage.error('更新失败')
    } finally {
      submitting.value = false
    }
  })
}

// 格式化日期
const formatDate = (dateTime) => {
  if (!dateTime) return '-'
  return new Date(dateTime).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 状态类型
const getStatusType = (status) => {
  const typeMap = {
    PENDING: 'info',
    IN_PROGRESS: 'warning',
    COMPLETED: 'success',
    CANCELLED: 'info'
  }
  return typeMap[status] || 'info'
}

// 状态文本
const getStatusText = (status) => {
  const textMap = {
    PENDING: '未开始',
    IN_PROGRESS: '进行中',
    COMPLETED: '已完成',
    CANCELLED: '已取消'
  }
  return textMap[status] || status
}

// 监听用例库列表变化，自动应用偏好
watch(teamProjectList, (list) => {
  if (list && list.length > 0) {
    applyPreference(list)
  }
})

// ===== 执行总览 Drawer =====
const overviewVisible = ref(false)
const ovSearch = ref('')
const ovStatusFilter = ref(null)
const ovModuleFilter = ref(null)
const ovViewMode = ref('table')
const ovPage = ref(1)
const ovPageSize = ref(50)
const ovLoading = ref(false)
const ovAllList = ref([])       // 全量数据（独立于详情页分页）
const ovDataLoaded = ref(false) // 是否已加载过全量数据

// 打开总览
const openExecutionOverview = () => {
  overviewVisible.value = true
}

const onOverviewOpen = async () => {
  if (!ovDataLoaded.value) {
    await loadOvAllData()
  }
}

const loadOvAllData = async () => {
  ovLoading.value = true
  try {
    // 用 all_cases=true 获取全量用例，取 all_test_cases 字段（与统计口径一致）
    const res = await getTestPlanDetail(planId, { all_cases: true })
    if (res.code === 200) {
      // all_test_cases 是基于全部用例的完整列表，与 statistics 统计口径完全一致
      ovAllList.value = res.data.all_test_cases || res.data.test_cases || []
      ovDataLoaded.value = true
    }
  } catch (e) {
    console.error('加载总览数据失败', e)
  } finally {
    ovLoading.value = false
  }
}

// 搜索防抖
let _ovSearchTimer = null
const onOvSearch = () => {
  clearTimeout(_ovSearchTimer)
  _ovSearchTimer = setTimeout(() => { ovPage.value = 1 }, 200)
}

const ovToggleStatus = (key) => {
  ovStatusFilter.value = ovStatusFilter.value === key ? null : key
  ovPage.value = 1
}

const ovToggleModule = (name) => {
  ovModuleFilter.value = ovModuleFilter.value === name ? null : name
  ovPage.value = 1
}

const ovClearFilters = () => {
  ovStatusFilter.value = null
  ovModuleFilter.value = null
  ovSearch.value = ''
  ovPage.value = 1
}

// 状态列表配置 — count 基于"除状态筛选外的其他筛选条件"统计，跟随模块/搜索联动
const ovStatusList = computed(() => {
  // 先应用模块筛选和搜索，再统计各状态数量（状态筛选本身不影响状态卡片数字）
  let list = ovAllList.value
  if (ovModuleFilter.value) {
    // 后端模块统计用 module.split('/')[0] 作为主模块名，前端筛选保持一致
    list = list.filter(r => (r.module || '未分类').split('/')[0].trim() === ovModuleFilter.value)
  }
  if (ovSearch.value.trim()) {
    const kw = ovSearch.value.trim().toLowerCase()
    list = list.filter(r =>
      (r.name && r.name.toLowerCase().includes(kw)) ||
      (r.case_number && r.case_number.toLowerCase().includes(kw))
    )
  }
  // 未执行：PENDING / ONGOING / 无执行记录（与后端 statistics 口径一致）
  const pendingCount = list.filter(r => !r.execution_status || r.execution_status === 'PENDING' || r.execution_status === 'ONGOING').length
  const passCount    = list.filter(r => r.execution_status === 'PASS').length
  const failCount    = list.filter(r => r.execution_status === 'FAIL').length
  const blockCount   = list.filter(r => r.execution_status === 'BLOCK').length
  const naCount      = list.filter(r => r.execution_status === 'NA').length
  const ntCount      = list.filter(r => r.execution_status === 'NT').length
  return [
    { key: 'PENDING', label: '未执行', color: '#94a3b8', count: pendingCount },
    { key: 'PASS',    label: 'PASS',   color: '#22c55e', count: passCount    },
    { key: 'FAIL',    label: 'FAIL',   color: '#ef4444', count: failCount    },
    { key: 'BLOCK',   label: 'BLOCK',  color: '#f59e0b', count: blockCount   },
    { key: 'NA',      label: 'NA',     color: '#a78bfa', count: naCount      },
    { key: 'NT',      label: 'NT',     color: '#64748b', count: ntCount      },
  ]
})

// 状态分布的"总基数"（排除状态筛选后的条数，用于计算状态占比）
const ovStatusBarBase = computed(() => {
  return ovStatusList.value.reduce((sum, s) => sum + s.count, 0)
})

const ovStatusBarWidth = (count) => {
  const base = ovStatusBarBase.value || 1
  return Math.round((count / base) * 100)
}

// 进度环颜色（保留用于 sidebar 其他地方）
const ovExecutedPct = computed(() => parseFloat(allProgress.value.executed_pct) || 0)
const ovPassPct = computed(() => {
  const total = planDetail.value.total_testcases || 1
  return Math.round(((statistics.value.passed || 0) / total) * 100)
})
const ovRingColor = computed(() => {
  const p = ovExecutedPct.value
  if (p >= 100) return '#22c55e'
  if (p >= 50) return '#4f46e5'
  if (p > 0) return '#f59e0b'
  return '#e2e8f0'
})

// 多段进度环：按 PASS / FAIL / BLOCK / NA / NT 五段依次绘制
// 圆周长 = 2πr = 2 * π * 50 ≈ 314.159
const OV_RING_CIRC = 314.159
const ovRingSegments = computed(() => {
  const total = planDetail.value.total_testcases || 0
  if (total === 0) return []
  const stats = statistics.value
  const data = [
    { key: 'PASS',  count: stats.passed  || 0, color: '#22c55e' },
    { key: 'FAIL',  count: stats.failed  || 0, color: '#ef4444' },
    { key: 'BLOCK', count: stats.blocked || 0, color: '#f59e0b' },
    { key: 'NA',    count: stats.na      || 0, color: '#a78bfa' },
    { key: 'NT',    count: stats.nt      || 0, color: '#64748b' },
  ]
  const segs = []
  let cumulative = 0
  for (const d of data) {
    if (d.count <= 0) continue
    const len = (d.count / total) * OV_RING_CIRC
    // stroke-dashoffset 用于定位段起点：初始-78.54(=314.159/4) 使 0° 在正上方(配合rotate(-90))
    // 这里用负偏移累加每段起点
    segs.push({
      key: d.key,
      color: d.color,
      len: len,
      offset: -cumulative
    })
    cumulative += len
  }
  return segs
})

// 过滤后的列表（使用全量数据）
const ovFilteredList = computed(() => {
  let list = [...ovAllList.value]
  if (ovStatusFilter.value) {
    if (ovStatusFilter.value === 'PENDING') {
      // 未执行 = PENDING / ONGOING / 无执行记录（与后端 statistics 及状态卡片口径一致）
      list = list.filter(r => !r.execution_status || r.execution_status === 'PENDING' || r.execution_status === 'ONGOING')
    } else {
      list = list.filter(r => r.execution_status === ovStatusFilter.value)
    }
  }
  if (ovModuleFilter.value) {
    // 与 moduleProgressList 的主模块分组保持一致（后端按 module.split('/')[0] 聚合）
    list = list.filter(r => (r.module || '未分类').split('/')[0].trim() === ovModuleFilter.value)
  }
  if (ovSearch.value.trim()) {
    const kw = ovSearch.value.trim().toLowerCase()
    list = list.filter(r =>
      (r.name && r.name.toLowerCase().includes(kw)) ||
      (r.case_number && r.case_number.toLowerCase().includes(kw))
    )
  }
  return list
})

const ovTotalPages = computed(() => Math.max(1, Math.ceil(ovFilteredList.value.length / ovPageSize.value)))

const ovPagedList = computed(() => {
  const start = (ovPage.value - 1) * ovPageSize.value
  return ovFilteredList.value.slice(start, start + ovPageSize.value)
})

// 页码列表（带省略号）
const ovPageNumbers = computed(() => {
  const total = ovTotalPages.value
  const cur = ovPage.value
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = []
  if (cur <= 4) {
    pages.push(1, 2, 3, 4, 5, '...', total)
  } else if (cur >= total - 3) {
    pages.push(1, '...', total - 4, total - 3, total - 2, total - 1, total)
  } else {
    pages.push(1, '...', cur - 1, cur, cur + 1, '...', total)
  }
  return pages
})

// 当过滤条件变化时重置页码
watch([ovStatusFilter, ovModuleFilter], () => { ovPage.value = 1 })

// 打开总览时加载数据
watch(overviewVisible, (v) => {
  if (v) {
    ovPage.value = 1
    if (!ovDataLoaded.value) {
      loadOvAllData()
    }
  }
})

onMounted(async () => {
  // 首次加载，确保全局 loading 显示（从列表页跳转时已触发，这里兜底）
  loadingStore.showLoading('加载测试计划详情...')
  await loadPlanDetail({}, true)
  
  // 添加滚动事件监听器
  if (tableWrapperRef.value) {
    tableWrapperRef.value.addEventListener('scroll', handleTableScroll)
  }
})

onUnmounted(() => {
  // 移除滚动事件监听器
  if (tableWrapperRef.value) {
    tableWrapperRef.value.removeEventListener('scroll', handleTableScroll)
  }
})
</script>

<style scoped>
/* ==================== */
/* TestPlanDetail - Demo Theme */
/* ==================== */

.plan-detail-container {
  padding: 24px;
  min-height: 100%;
  background: var(--demo-bg, #f8fafc);
}

.detail-header {
  display: flex;
  align-items: center;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
  margin-bottom: 24px;
}

/* 基本信息区域 - Demo风格 */
.info-section {
  background: var(--demo-bg-card, #ffffff);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 16px;
  padding: 24px;
  margin-top: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--demo-text-primary, #0f172a);
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}

/* 执行统计标题行（标题 + 入口按钮） */
.section-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}
.section-title-row .section-title {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
  flex-shrink: 0;
}

/* 执行总览入口按钮 */
.overview-entry-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 1.5px solid var(--demo-primary, #4f46e5);
  border-radius: 8px;
  background: var(--demo-primary-light, #eef2ff);
  color: var(--demo-primary, #4f46e5);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.18s;
  white-space: nowrap;
  line-height: 1;
}
.overview-entry-btn:hover {
  background: var(--demo-primary, #4f46e5);
  color: #fff;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.25);
  transform: translateY(-1px);
}
.overview-entry-btn:active {
  transform: translateY(0);
  box-shadow: none;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.info-item {
  display: flex;
  align-items: flex-start;
}

.info-item.full-width {
  grid-column: 1 / -1;
}

.info-label {
  color: var(--demo-text-muted, #64748b);
  font-size: 14px;
  min-width: 100px;
  flex-shrink: 0;
  font-weight: 500;
}

.info-value {
  color: var(--demo-text-primary, #0f172a);
  font-size: 14px;
  flex: 1;
}

/* 执行统计区域 - Demo风格 */
.stats-section {
  background: var(--demo-bg-card, #ffffff);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 16px;
  padding: 20px 24px;
  margin-top: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.stats-cards {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: var(--demo-bg, #f8fafc);
  border-radius: 8px;
  min-width: 100px;
  transition: all 0.15s;
  border: 1px solid transparent;
}

.stat-card.clickable {
  cursor: pointer;
}

.stat-card.clickable:hover {
  background: var(--demo-border-light, #f1f5f9);
  border-color: var(--demo-border, #e2e8f0);
}

.stat-card.active {
  background: var(--demo-primary-light, #eef2ff);
  border: 1px solid var(--demo-primary, #4f46e5);
}

.stat-card:hover {
  background: var(--demo-border-light, #f1f5f9);
}

.stat-label {
  font-size: 13px;
  color: var(--demo-text-muted, #64748b);
  white-space: nowrap;
  font-weight: 500;
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  color: var(--demo-text-primary, #0f172a);
}

/* 模块执行进度 */
.module-progress-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  margin-top: 12px;
}

.module-progress-item {
  padding: 14px 16px;
  background: var(--demo-bg, #f8fafc);
  border-radius: 10px;
  border: 1px solid var(--demo-border-light, #f1f5f9);
  transition: all 0.15s;
}

.module-progress-item:hover {
  border-color: var(--demo-border, #e2e8f0);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.module-progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.module-progress-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--demo-text-primary, #0f172a);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 12px;
}

.module-progress-pct {
  font-size: 16px;
  font-weight: 700;
  flex-shrink: 0;
}

.module-progress-bar-bg {
  height: 6px;
  background: var(--demo-border-light, #e2e8f0);
  border-radius: 3px;
  overflow: hidden;
}

.module-progress-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.4s ease;
  min-width: 0;
}

.module-progress-detail {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-size: 12px;
  color: var(--demo-text-muted, #64748b);
}

.module-progress-rd-owner {
  margin-top: 4px;
  font-size: 12px;
  color: #409eff;
}

.testcase-list-section {
  margin-top: 20px;
  position: relative;
  background: var(--demo-bg-card, #ffffff);
  border: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 16px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: var(--demo-bg, #f8fafc);
  border-radius: 8px;
}

.action-buttons {
  display: flex;
  gap: 10px;
}

/* 列表头部样式 - Demo风格 */
.list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0;
  padding: 16px 20px;
  background: rgba(248, 250, 252, 0.5);
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
}

/* 工具栏 */
.sticky-toolbar {
  background: rgba(248, 250, 252, 0.5);
  padding: 16px 20px;
  margin-bottom: 0 !important;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
}

/* 移除图标样式 */
.remove-icon {
  font-size: 20px;
  color: #ef4444;
  cursor: pointer;
  transition: all 0.15s;
}

.remove-icon:hover {
  color: #dc2626;
  transform: scale(1.1);
}

.remove-icon.is-loading {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 用例选择对话框样式 - Demo风格 */
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
  display: flex;
  flex-direction: column;
  overflow: visible;
  position: relative;
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

.testcase-filter {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
  flex-shrink: 0;
}



/* 表格容器 - Demo风格 */
.table-container {
  width: 100%;
  position: relative;
  margin-bottom: 0;
  margin-top: 0;
  overflow-x: auto;
  min-height: 400px;
  background: var(--demo-bg-card, #ffffff);
  scroll-behavior: smooth;
}

/* 确保表格表头和表体对齐 */
.table-container :deep(.el-table) {
  width: 100%;
}

.table-container :deep(.el-table__header-wrapper) {
  background-color: #f8fafc;
}

/* 表格表头固定 - Demo风格 */
.sticky-header-table {
  position: relative;
  min-width: 1000px;
}

.sticky-header-table :deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 100;
  background: var(--demo-bg-card, #ffffff) !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow-x: hidden;
  border-bottom: 1px solid var(--demo-border, #e2e8f0);
}

.sticky-header-table :deep(.el-table__header-wrapper th) {
  background: #f8fafc !important;
  color: var(--demo-text-muted, #64748b) !important;
  font-weight: 500 !important;
  font-size: 12px !important;
  text-transform: uppercase !important;
  letter-spacing: 0.05em !important;
  position: sticky;
  top: 0;
  z-index: 101;
  white-space: nowrap;
  border-right: 1px solid var(--demo-border-light, #f1f5f9);
}

/* 表格内容区域 */
.sticky-header-table :deep(.el-table__body-wrapper) {
  overflow-y: auto;
  overflow-x: hidden;
  max-height: calc(100vh - 220px);
}

/* 表格行悬停效果 - Demo风格 */
.sticky-header-table :deep(.el-table__row:hover > td) {
  background: #f8fafc !important;
}

/* 固定列不透明背景 */
.sticky-header-table :deep(.el-table td.el-table__cell) {
  background: #fff;
}

/* 调整滚动条样式 - Demo风格 */
.table-container::-webkit-scrollbar,
.sticky-header-table :deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
  height: 8px;
}

.table-container::-webkit-scrollbar-track,
.sticky-header-table :deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: var(--demo-border-light, #f1f5f9);
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb,
.sticky-header-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-container::-webkit-scrollbar-thumb:hover,
.sticky-header-table :deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: #94a3b8;
}

/* 为Firefox浏览器添加滚动条样式 */
.table-container,
.sticky-header-table :deep(.el-table__body-wrapper) {
  scrollbar-width: thin;
  scrollbar-color: #cbd5e1 var(--demo-border-light, #f1f5f9);
}

/* 表格单元格样式 - Demo风格 */
.sticky-header-table :deep(.el-table__cell) {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-right: 1px solid var(--demo-border-light, #f1f5f9);
  transition: all 0.15s ease;
  color: var(--demo-text-primary, #0f172a);
}

/* 确保表头和表体的列宽对齐 */
.sticky-header-table :deep(.el-table__header),
.sticky-header-table :deep(.el-table__body) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 增强表格的整体感 */
.sticky-header-table :deep(.el-table) {
  border: none;
  width: 100%;
}

/* 确保表格底部边框完整 */
.sticky-header-table :deep(.el-table__row:last-child td) {
  border-bottom: 1px solid var(--demo-border-light, #f1f5f9);
}

/* 确保表头和表体的滚动条同步 */
.table-container :deep(.el-table__body-wrapper) {
  overflow-x: auto !important;
  overflow-y: auto !important;
}

/* 确保表头列宽和表体列宽一致 */
.table-container :deep(.el-table__header),
.table-container :deep(.el-table__body) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 确保表头和表体的单元格宽度一致 */
.table-container :deep(.el-table__header-wrapper .el-table__header),
.table-container :deep(.el-table__body-wrapper .el-table__body) {
  width: 100% !important;
}

/* 移除可能影响对齐的边距和内边距 */
.table-container :deep(.el-table__header-wrapper),
.table-container :deep(.el-table__body-wrapper) {
  margin: 0 !important;
  padding: 0 !important;
}

/* 设置表格单元格高度 */
.table-container :deep(.el-table td.el-table__cell),
.table-container :deep(.el-table th.el-table__cell) {
  height: 48px !important;
  padding: 0 12px !important;
}

.table-container :deep(.el-table td.el-table__cell .cell),
.table-container :deep(.el-table th.el-table__cell .cell) {
  line-height: 48px;
  padding: 0;
}

/* 确保单元格内容不溢出 */
.table-container :deep(.el-table__cell) {
  overflow: hidden;
}

/* 对话框中的表格容器 */
.testcase-content .table-container {
  flex: 1;
  width: 100%;
  position: relative;
  overflow: hidden;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
}

/* 确保表格表头固定 - Demo风格 */
.table-wrapper :deep(.el-table__header-wrapper) {
  background-color: #f8fafc;
  position: sticky;
  top: 0;
  z-index: 10;
}

/* 确保表头和表体的滚动条同步 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-x: auto !important;
  overflow-y: auto !important;
  max-height: calc(100vh - 350px);
}

/* 确保表头列宽和表体列宽一致 */
.table-wrapper :deep(.el-table__header),
.table-wrapper :deep(.el-table__body) {
  width: 100% !important;
  table-layout: fixed !important;
}

/* 确保表头和表体的单元格宽度一致 */
.table-wrapper :deep(.el-table__header-wrapper .el-table__header),
.table-wrapper :deep(.el-table__body-wrapper .el-table__body) {
  width: 100% !important;
}

/* 移除可能影响对齐的边距和内边距 */
.table-wrapper :deep(.el-table__header-wrapper),
.table-wrapper :deep(.el-table__body-wrapper) {
  margin: 0 !important;
  padding: 0 !important;
}

/* 分页器 - Demo风格 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--demo-bg-card, #ffffff);
  border-top: 1px solid var(--demo-border, #e2e8f0);
  border-radius: 0 0 16px 16px;
}

/* 分页器按钮样式 - Demo风格 */
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
  font-weight: 600;
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

/* Tooltip 样式 */
.steps-tooltip {
  max-width: 600px !important;
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
}

:deep(.el-button--success:hover) {
  background: #059669 !important;
  border-color: #059669 !important;
}

/* 表格内操作按钮样式 - Demo风格 */
:deep(.el-table .el-button.is-link) {
  padding: 4px 8px;
  font-size: 13px;
  font-weight: 500;
}

:deep(.el-table .el-button--primary.is-link) {
  color: var(--demo-primary, #4f46e5) !important;
}

:deep(.el-table .el-button--primary.is-link:hover) {
  color: var(--demo-primary-hover, #4338ca) !important;
  background: var(--demo-primary-light, #eef2ff) !important;
  border-radius: 4px;
}

/* ===== 执行总览入口按钮 ===== */
.overview-btn {
  display: inline-flex;
  align-items: center;
  margin-right: 10px;
  border-radius: 8px !important;
  border-color: var(--demo-primary, #4f46e5) !important;
  color: var(--demo-primary, #4f46e5) !important;
  font-weight: 500 !important;
  transition: all 0.2s !important;
}
.overview-btn:hover {
  background: var(--demo-primary-light, #eef2ff) !important;
}

/* ===== 执行总览 Drawer 全局覆盖 ===== */
:global(.execution-overview-drawer .el-drawer__body) {
  padding: 0 !important;
  overflow: hidden !important;
  height: 100vh !important;
}
:global(.execution-overview-drawer) {
  box-shadow: none !important;
}

/* ===== 总览根容器 ===== */
.ov-root {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  overflow: hidden;
}

/* ===== 顶部导航栏 ===== */
.ov-navbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  height: 56px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  z-index: 10;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.ov-navbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}
.ov-back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  color: #475569;
  transition: all 0.15s;
  flex-shrink: 0;
}
.ov-back-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
  color: #0f172a;
}
.ov-plan-title {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.ov-plan-label {
  font-size: 11px;
  color: #94a3b8;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  line-height: 1;
}
.ov-plan-name {
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 400px;
  line-height: 1.4;
}
.ov-navbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.ov-status-badge {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
}
.ov-status-pending   { background: #f1f5f9; color: #64748b; }
.ov-status-in_progress { background: #fef3c7; color: #d97706; }
.ov-status-completed { background: #dcfce7; color: #16a34a; }
.ov-status-cancelled { background: #f1f5f9; color: #94a3b8; }

.ov-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.ov-search-icon {
  position: absolute;
  left: 10px;
  color: #94a3b8;
  pointer-events: none;
}
.ov-search-input {
  width: 220px;
  height: 34px;
  padding: 0 32px 0 32px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  color: #0f172a;
  background: #f8fafc;
  outline: none;
  transition: all 0.15s;
}
.ov-search-input:focus {
  border-color: #4f46e5;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(79,70,229,0.08);
}
.ov-search-input::placeholder { color: #94a3b8; }
.ov-search-clear {
  position: absolute;
  right: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  border: none;
  background: #cbd5e1;
  border-radius: 50%;
  cursor: pointer;
  color: #fff;
  transition: background 0.15s;
}
.ov-search-clear:hover { background: #94a3b8; }

.ov-view-toggle {
  display: flex;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.ov-view-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border: none;
  background: #fff;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.15s;
}
.ov-view-btn:hover { background: #f1f5f9; color: #475569; }
.ov-view-btn.active { background: #eef2ff; color: #4f46e5; }
.ov-view-btn + .ov-view-btn { border-left: 1px solid #e2e8f0; }

.ov-export-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0 14px;
  height: 34px;
  border: 1px solid #10b981;
  border-radius: 8px;
  background: #fff;
  color: #10b981;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
}
.ov-export-btn:hover { background: #f0fdf4; }

/* ===== 主体布局 ===== */
.ov-body {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* ===== 左侧统计面板 ===== */
.ov-sidebar {
  width: 240px;
  flex-shrink: 0;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.ov-sidebar::-webkit-scrollbar { width: 4px; }
.ov-sidebar::-webkit-scrollbar-thumb { background: #e2e8f0; border-radius: 2px; }

.ov-sidebar-title {
  font-size: 11px;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 16px 16px 8px;
}

/* 进度环卡片 */
.ov-progress-ring-card {
  padding: 20px 16px 16px;
  border-bottom: 1px solid #f1f5f9;
}
.ov-ring-wrap {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 16px;
}
.ov-ring-svg {
  width: 120px;
  height: 120px;
}
.ov-ring-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
}
.ov-ring-pct {
  display: block;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
}
.ov-ring-label {
  display: block;
  font-size: 11px;
  color: #94a3b8;
  margin-top: 2px;
}
.ov-ring-stats {
  display: flex;
  justify-content: space-around;
}
.ov-ring-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.ov-ring-stat-val {
  font-size: 18px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
}
.ov-ring-stat-key {
  font-size: 11px;
  color: #94a3b8;
  white-space: nowrap;
}

/* 状态分布 */
.ov-status-dist {
  border-bottom: 1px solid #f1f5f9;
  padding-bottom: 12px;
}
.ov-status-bars {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.ov-status-bar-item {
  padding: 6px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.ov-status-bar-item:hover { background: #f8fafc; }
.ov-status-active { background: #f8fafc !important; border-color: #e2e8f0 !important; }
.ov-status-bar-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.ov-status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ov-status-bar-label {
  font-size: 12px;
  color: #475569;
  font-weight: 500;
  flex: 1;
}
.ov-status-bar-count {
  font-size: 13px;
  font-weight: 700;
}
.ov-status-bar-track {
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
}
.ov-status-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
  opacity: 0.8;
}

/* 模块进度 */
.ov-module-progress {
  flex: 1;
  padding-bottom: 16px;
}
.ov-module-list {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.ov-module-item {
  padding: 8px 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  border: 1px solid transparent;
}
.ov-module-item:hover { background: #f8fafc; }
.ov-module-active { background: #eef2ff !important; border-color: #c7d2fe !important; }
.ov-module-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.ov-module-name {
  font-size: 12px;
  font-weight: 500;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}
.ov-module-pct {
  font-size: 12px;
  font-weight: 700;
  flex-shrink: 0;
}
.ov-module-bar-track {
  height: 4px;
  background: #f1f5f9;
  border-radius: 2px;
  overflow: hidden;
  margin-bottom: 4px;
}
.ov-module-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}
.ov-module-detail {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: #94a3b8;
}
.ov-module-rd {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  padding-top: 4px;
  border-top: 1px dashed #e2e8f0;
  font-size: 11px;
  color: #4f46e5;
  overflow: hidden;
}
.ov-module-rd svg {
  flex-shrink: 0;
  color: #818cf8;
}
.ov-module-rd span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}

/* ===== 右侧主内容 ===== */
.ov-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

/* 筛选条 */
.ov-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}
.ov-filter-chips {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.ov-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  background: #fff;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.ov-chip:hover { background: #f8fafc; border-color: #cbd5e1; }
.ov-chip-active { font-weight: 600; }
.ov-chip-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.ov-chip-count {
  background: #f1f5f9;
  color: #64748b;
  border-radius: 10px;
  padding: 0 5px;
  font-size: 11px;
  font-weight: 600;
  min-width: 18px;
  text-align: center;
}
.ov-chip-active .ov-chip-count {
  background: rgba(255,255,255,0.3);
  color: inherit;
}
.ov-filter-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.ov-result-count {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
}
.ov-result-count strong { color: #475569; }
.ov-clear-filter {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid #fca5a5;
  border-radius: 6px;
  background: #fff;
  color: #ef4444;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}
.ov-clear-filter:hover { background: #fef2f2; }

/* ===== 表格视图 ===== */
.ov-table-wrap {
  flex: 1;
  overflow: auto;
  min-height: 0;
}
.ov-table-wrap::-webkit-scrollbar { width: 6px; height: 6px; }
.ov-table-wrap::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
.ov-table-wrap::-webkit-scrollbar-track { background: #f8fafc; }

.ov-table {
  width: 100%;
  min-width: 1200px;
  border-collapse: collapse;
  font-size: 12px;
  table-layout: fixed;
}
.ov-th {
  position: sticky;
  top: 0;
  z-index: 5;
  background: #f8fafc;
  padding: 9px 8px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e2e8f0;
  white-space: nowrap;
  user-select: none;
  vertical-align: middle;
}
.ov-th-idx    { width: 44px; text-align: center; }
.ov-th-center { text-align: center; }

.ov-tr {
  border-bottom: 1px solid #d1d5db;
  transition: background 0.1s;
}
.ov-tr:hover { background: #f8fafc; }
.ov-row-fail    { border-left: 3px solid #fca5a5; }
.ov-row-block   { border-left: 3px solid #fcd34d; }
.ov-row-pass    { border-left: 3px solid #86efac; }
.ov-row-pending { border-left: 3px solid transparent; }
.ov-row-na, .ov-row-nt { border-left: 3px solid #e2e8f0; }

.ov-td {
  padding: 8px 8px;
  vertical-align: top;
  color: #0f172a;
  word-break: break-word;
  line-height: 1.5;
  overflow: hidden;
}
.ov-td-idx    { text-align: center; color: #94a3b8; font-size: 11px; vertical-align: middle; }
.ov-td-center { text-align: center; vertical-align: middle; }

/* 单元格内容样式 */
.ov-case-num {
  display: inline-block;
  font-size: 11px;
  color: #374151;
  font-weight: 600;
  font-family: 'SF Mono', 'Fira Code', monospace;
  word-break: keep-all;
  white-space: nowrap;
  line-height: 1.4;
}
.ov-module-tag {
  display: inline-block;
  font-size: 11px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 4px;
  word-break: keep-all;
  white-space: nowrap;
}
.ov-cell-wrap {
  display: block;
  font-size: 12px;
  color: #0f172a;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
}
.ov-cell-muted {
  color: #94a3b8;
  font-size: 12px;
}
.ov-executor {
  font-size: 12px;
  color: #475569;
  text-align: center;
}
.ov-remark-text {
  display: block;
  font-size: 12px;
  color: #475569;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.5;
  text-align: center;
}

/* 步骤列表 */
.ov-steps-list {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.ov-step-item {
  display: flex;
  gap: 4px;
  align-items: flex-start;
  line-height: 1.5;
}
.ov-step-num {
  flex-shrink: 0;
  font-size: 11px;
  color: #4f46e5;
  font-weight: 600;
  min-width: 18px;
  padding-top: 1px;
}
.ov-step-text {
  font-size: 12px;
  color: #0f172a;
  word-break: break-word;
  white-space: pre-line;
  flex: 1;
}

.ov-level-badge {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
}
.ov-level-p0 { background: #fef2f2; color: #dc2626; }
.ov-level-p1 { background: #fff7ed; color: #ea580c; }
.ov-level-p2 { background: #fefce8; color: #ca8a04; }
.ov-level-p3 { background: #f0fdf4; color: #16a34a; }
.ov-level-   { background: #f1f5f9; color: #94a3b8; }

.ov-exec-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  white-space: nowrap;
}
.ov-exec-pending { background: #f1f5f9; color: #64748b; }
.ov-exec-pass    { background: #dcfce7; color: #16a34a; }
.ov-exec-fail    { background: #fef2f2; color: #dc2626; }
.ov-exec-block   { background: #fef3c7; color: #d97706; }
.ov-exec-na      { background: #f5f3ff; color: #7c3aed; }
.ov-exec-nt      { background: #f1f5f9; color: #475569; }

.ov-empty {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
  font-size: 14px;
}
.ov-empty svg { display: block; margin: 0 auto 12px; }

/* ===== 卡片视图 ===== */
.ov-card-grid {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 10px;
  align-content: start;
}
.ov-card-grid::-webkit-scrollbar { width: 6px; }
.ov-card-grid::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }

.ov-case-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  transition: all 0.15s;
  border-left-width: 3px;
}
.ov-case-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); transform: translateY(-1px); }
.ov-card-pass    { border-left-color: #22c55e; }
.ov-card-fail    { border-left-color: #ef4444; }
.ov-card-block   { border-left-color: #f59e0b; }
.ov-card-pending { border-left-color: #e2e8f0; }
.ov-card-na, .ov-card-nt { border-left-color: #a78bfa; }

.ov-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.ov-card-num {
  font-size: 11px;
  color: #4f46e5;
  font-weight: 500;
  font-family: 'SF Mono', 'Fira Code', monospace;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  margin-right: 8px;
}
.ov-card-name {
  font-size: 13px;
  font-weight: 500;
  color: #0f172a;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ov-card-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.ov-card-remark {
  margin-top: 8px;
  font-size: 11px;
  color: #64748b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
}
.ov-empty-card {
  grid-column: 1 / -1;
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
  font-size: 14px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

/* ===== 分页 ===== */
.ov-pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  flex-shrink: 0;
  gap: 12px;
  flex-wrap: wrap;
}
.ov-page-info {
  font-size: 12px;
  color: #94a3b8;
  white-space: nowrap;
}
.ov-page-btns {
  display: flex;
  align-items: center;
  gap: 3px;
}
.ov-page-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  color: #475569;
  transition: all 0.15s;
}
.ov-page-btn:hover:not(:disabled) { background: #f1f5f9; border-color: #cbd5e1; }
.ov-page-btn:disabled { opacity: 0.4; cursor: not-allowed; }
.ov-page-num {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 30px;
  height: 30px;
  padding: 0 4px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: #475569;
  transition: all 0.15s;
}
.ov-page-num:hover:not(.ellipsis):not(.active) { background: #f1f5f9; }
.ov-page-num.active { background: #4f46e5; border-color: #4f46e5; color: #fff; font-weight: 600; }
.ov-page-num.ellipsis { cursor: default; border-color: transparent; background: transparent; }
.ov-page-size-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  white-space: nowrap;
}
.ov-page-size-select {
  height: 30px;
  padding: 0 6px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: #fff;
  font-size: 12px;
  color: #475569;
  cursor: pointer;
  outline: none;
}
.ov-page-size-select:focus { border-color: #4f46e5; }

/* ===== 低分辨率适配（笔记本 ≤1440px） ===== */
@media (max-width: 1440px) {
  .ov-sidebar { width: 210px; }
  .ov-ring-wrap { width: 100px; height: 100px; }
  .ov-ring-svg  { width: 100px; height: 100px; }
  .ov-ring-pct  { font-size: 18px; }
  .ov-ring-stat-val { font-size: 15px; }
  .ov-ring-stat-key { font-size: 10px; }
  .ov-navbar { height: 50px; padding: 0 14px; }
  .ov-plan-name { font-size: 13px; max-width: 280px; }
  .ov-search-input { width: 180px; font-size: 12px; }
  .ov-filter-bar { padding: 8px 12px; }
  .ov-chip { padding: 3px 8px; font-size: 11px; }
  .ov-th { padding: 7px 8px; font-size: 10px; }
  .ov-td { padding: 6px 8px; }
  .ov-step-text { font-size: 11px; }
  .ov-cell-wrap { font-size: 11px; }
  .ov-case-num  { font-size: 10px; }
  .ov-module-tag { font-size: 10px; }
  .ov-pagination { padding: 8px 12px; }
  .ov-page-info { font-size: 11px; }
  .ov-page-num, .ov-page-btn { width: 26px; height: 26px; font-size: 11px; }
}

@media (max-width: 1280px) {
  .ov-sidebar { width: 190px; }
  .ov-ring-wrap { width: 88px; height: 88px; }
  .ov-ring-svg  { width: 88px; height: 88px; }
  .ov-ring-pct  { font-size: 16px; }
  .ov-ring-stats { gap: 0; }
  .ov-ring-stat-val { font-size: 13px; }
  .ov-plan-name { max-width: 220px; font-size: 13px; }
  .ov-search-input { width: 150px; }
  .ov-status-bar-label { font-size: 11px; }
  .ov-status-bar-count { font-size: 12px; }
  .ov-module-name { font-size: 11px; }
  .ov-module-pct  { font-size: 11px; }
  .ov-module-detail { font-size: 10px; }
  .ov-sidebar-title { font-size: 10px; padding: 12px 12px 6px; }
  .ov-progress-ring-card { padding: 14px 12px 12px; }
  .ov-status-bars { padding: 0 8px; }
  .ov-module-list { padding: 0 8px; }
}

/* 超小屏（1024px 以下）隐藏左侧面板，改为顶部 chip 筛选 */
@media (max-width: 1024px) {
  .ov-sidebar { display: none; }
  .ov-body { flex-direction: column; }
  .ov-main { overflow: hidden; }
  .ov-filter-bar { flex-wrap: wrap; gap: 6px; }
  .ov-filter-chips { flex-wrap: wrap; }
}

</style>
