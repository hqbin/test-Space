<template>
  <div class="ai-recommendations">
    <el-card shadow="never" class="main-card">
    <!-- Tab 切换 -->
    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- ===== 新建推荐 Tab ===== -->
      <el-tab-pane :label="t('recommend.newRecommend')" name="create">
        <div class="tab-content">
        <!-- Step 1: 配置区域 -->
        <el-card class="config-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><Setting /></el-icon> {{ t('recommend.config') }}</span>
            </div>
          </template>

          <el-form :model="config" label-width="120px" label-position="top">
            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item :label="t('recommend.selectCaseLib')" required>
                  <el-select
                    v-model="config.projectIds"
                    multiple
                    filterable
                    :placeholder="t('recommend.selectCaseLibPlaceholder')"
                    style="width: 100%"
                    :loading="loadingProjects"
                  >
                    <el-option
                      v-for="p in teamProjects"
                      :key="p.id"
                      :label="p.name"
                      :value="p.id"
                    />
                  </el-select>
                  <div class="form-tip">{{ t('recommend.selectCaseLibTip') }}</div>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="24">
                <el-form-item :label="t('recommend.titleOptional')">
                  <el-input v-model="config.title" :placeholder="t('recommend.titlePlaceholder')" />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item :label="t('recommend.prLink')">
              <div class="pr-input-row">
                <el-input
                  v-model="config.prNumbers"
                  :placeholder="t('recommend.prPlaceholder')"
                  style="flex: 1"
                  @keyup.enter="handleFetchPr"
                />
                <el-button :loading="fetchingPr" @click="handleFetchPr">{{ t('recommend.fetchPr') }}</el-button>
              </div>
              <div v-if="prInfoList.length > 0" class="pr-info-list">
                <div v-for="pr in prInfoList" :key="pr.prNumber" class="pr-info-item">
                  <div class="pr-info-header">
                    <el-tag size="small" type="primary">#{{ pr.prNumber }}</el-tag>
                    <span class="pr-subject">{{ pr.subject }}</span>
                    <el-tag v-if="pr.status" size="small" :type="pr.status === 'Closed' ? 'success' : 'warning'">{{ pr.status }}</el-tag>
                    <el-button size="small" text type="danger" @click="removePr(pr.prNumber)"><el-icon><Close /></el-icon></el-button>
                  </div>
                  <div v-if="pr.rootCause" class="pr-info-field"><label>Root Cause：</label><span>{{ pr.rootCause }}</span></div>
                  <div v-if="pr.solution" class="pr-info-field"><label>Solution：</label><span>{{ pr.solution }}</span></div>
                  <div v-if="pr.error" class="pr-info-field error"><span>{{ pr.error }}</span></div>
                </div>
              </div>
              <div v-if="prInfoList.length === 0" class="form-tip">{{ t('recommend.prTip') }}</div>
            </el-form-item>

            <el-form-item :label="t('recommend.releaseNote')">
              <el-input
                v-model="config.releaseNote"
                type="textarea"
                :rows="8"
                :placeholder="t('recommend.releaseNotePlaceholder')"
              />
              <div class="form-tip">{{ t('recommend.atLeastOne') }}</div>
            </el-form-item>

            <el-form-item>
              <el-tooltip :content="taskRunning ? t('recommend.taskRunningTip') : !canAnalyze ? t('recommend.atLeastOneTip') : ''" :disabled="canAnalyze && !taskRunning" placement="top">
                <el-button
                  type="primary"
                  size="large"
                  :loading="analyzing"
                  :disabled="!canAnalyze || taskRunning"
                  @click="startAnalysis"
                >
                  <el-icon><MagicStick /></el-icon>
                  {{ analyzing ? t('recommend.creating') : taskRunning ? t('recommend.taskRunning') : t('recommend.createAnalysis') }}
                </el-button>
              </el-tooltip>
            </el-form-item>
          </el-form>
        </el-card>

        <!-- AI分析结果 -->
        <el-card v-if="analysisResult" class="analysis-card-inline" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><DataAnalysis /></el-icon> {{ t('recommend.aiImpactAnalysis') }}</span>
              <el-tag type="success" size="small">{{ t('recommend.analysisComplete') }}</el-tag>
            </div>
          </template>

          <el-row :gutter="16">
            <el-col :span="8">
              <div class="analysis-item">
                <div class="analysis-label">{{ t('recommend.affectedModules') }}</div>
                <div class="analysis-value">
                  <el-tag v-for="m in analysisResult.affectedModules" :key="m" size="small" style="margin: 2px">{{ m }}</el-tag>
                </div>
              </div>
            </el-col>
            <el-col :span="4">
              <div class="analysis-item">
                <div class="analysis-label">{{ t('recommend.riskLevel') }}</div>
                <div class="analysis-value">
                  <el-tag :type="riskLevelType(analysisResult.riskLevel)">{{ analysisResult.riskLevel }}</el-tag>
                </div>
              </div>
            </el-col>
            <el-col :span="12">
              <div class="analysis-item">
                <div class="analysis-label">{{ t('recommend.testDirections') }}</div>
                <div class="analysis-value analysis-tags-wrap">
                  <el-tag v-for="d in analysisResult.testDirections" :key="d" size="small" type="info" style="margin: 2px">{{ d }}</el-tag>
                </div>
              </div>
            </el-col>
          </el-row>

          <div v-if="analysisResult.summary" class="analysis-summary">
            <div class="analysis-label">{{ t('recommend.impactSummary') }}</div>
            <div class="analysis-text">{{ analysisResult.summary }}</div>
          </div>
        </el-card>

        <!-- PR 关联详情 -->
        <el-card v-if="analysisResult && !taskRunning && (prInfoList.length > 0 || config.releaseNote || latestAnalysis?.releaseNote)" class="pr-detail-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><Link /></el-icon> {{ t('recommend.prDetailTitle') }}</span>
            </div>
          </template>
          <div v-for="pr in prInfoList" :key="pr.prNumber" class="pr-detail-item">
            <div class="pr-detail-header">
              <el-tag size="small" type="primary">#{{ pr.prNumber }}</el-tag>
              <strong class="pr-detail-subject">{{ pr.subject }}</strong>
              <el-tag v-if="pr.status" size="small" :type="pr.status === 'Closed' ? 'success' : 'warning'">{{ pr.status }}</el-tag>
            </div>
            <div v-if="pr.rootCause" class="pr-detail-field">
              <label>{{ t('recommend.prDetailRootCause') }}：</label><span>{{ pr.rootCause }}</span>
            </div>
            <div v-if="pr.solution" class="pr-detail-field">
              <label>{{ t('recommend.prDetailSolution') }}：</label><span>{{ pr.solution }}</span>
            </div>
          </div>
          <div v-if="config.releaseNote || latestAnalysis?.releaseNote" class="pr-detail-release-note">
            <div class="pr-detail-release-label">{{ t('recommend.prDetailReleaseNote') }}：</div>
            <div class="pr-detail-release-content">{{ config.releaseNote || latestAnalysis?.releaseNote }}</div>
          </div>
        </el-card>

        <!-- 最近24小时分析结果 -->
        <el-card v-if="latestAnalysis && !taskRunning && !analysisResult" class="latest-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><DataAnalysis /></el-icon> 最近分析结果</span>
              <span class="latest-time">{{ formatTime(latestAnalysis.createdAt) }}</span>
            </div>
          </template>
          <el-row :gutter="16">
            <el-col :span="6">
              <div class="latest-stat">
                <div class="latest-stat-value">{{ latestAnalysis.recommendedCount }}</div>
                <div class="latest-stat-label">推荐用例</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="latest-stat">
                <div class="latest-stat-value"><el-tag :type="riskLevelType(latestAnalysis.riskLevel)" size="small">{{ latestAnalysis.riskLevel }}</el-tag></div>
                <div class="latest-stat-label">风险等级</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="latest-stat">
                <div class="latest-stat-value">{{ latestAnalysis.coverageRate }}%</div>
                <div class="latest-stat-label">覆盖率</div>
              </div>
            </el-col>
            <el-col :span="6">
              <div class="latest-stat">
                <el-button size="small" type="primary" link @click="loadLatestDetail">查看详情</el-button>
              </div>
            </el-col>
          </el-row>
          <div v-if="latestAnalysis.summary" class="latest-summary">{{ latestAnalysis.summary }}</div>
        </el-card>

        <!-- 进度显示 -->
        <el-card v-if="taskRunning" class="progress-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="progress-header-text"><el-icon class="spinning"><Loading /></el-icon> AI 分析进行中</span>
            </div>
          </template>
          <div class="progress-content">
            <el-progress :percentage="taskProgress.progress || 0" :stroke-width="20" :text-inside="true" :color="progressColors" />
            <div class="progress-message">
              {{ taskProgress.message || '等待中...' }}
            </div>
          </div>
        </el-card>

        <!-- Step 3: 推荐用例列表 -->
        <el-card v-if="recommendedCases.length > 0" class="result-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><List /></el-icon> {{ t('recommend.recommendCases') }}（{{ filteredCases.length }}/{{ recommendedCases.length }}）</span>
              <div class="header-actions">
                <el-select v-model="filterModule" :placeholder="t('recommend.filterByModule')" clearable size="small" style="width: 140px">
                  <el-option v-for="m in moduleOptions" :key="m" :label="m" :value="m" />
                </el-select>
                <el-select v-model="filterScore" :placeholder="t('recommend.filterByScore')" clearable size="small" style="width: 130px">
                  <el-option label="≥90分" value="90" />
                  <el-option label="≥80分" value="80" />
                  <el-option label="≥70分" value="70" />
                  <el-option label="≥60分" value="60" />
                </el-select>
                <el-button size="small" @click="selectAll">{{ isAllSelected ? t('recommend.cancelSelectAll') : t('recommend.selectAll') }}</el-button>
                <el-button v-if="hasButton('aivoiceRecommendations', 'export')" size="small" @click="handleExport" :loading="exporting"><el-icon><Download /></el-icon>{{ t('recommend.export') }}</el-button>
                <el-button size="small" type="primary" :disabled="selectedCases.length === 0" @click="openCreateSuiteDialog">
                  <el-icon><FolderAdd /></el-icon>{{ t('recommend.createSuite') }}（{{ selectedCases.length }}）
                </el-button>
                <el-button size="small" type="primary" :disabled="selectedCases.length === 0" @click="handleCreatePlan">
                  <el-icon><List /></el-icon>{{ t('recommend.createPlan') }}（{{ selectedCases.length }}）
                </el-button>
              </div>
            </div>
          </template>

          <el-table :data="paginatedCases" border stripe ref="tableRef" row-key="caseId" style="width: 100%">
            <el-table-column width="60" fixed="left">
              <template #default="{ row }">
                <el-checkbox :model-value="selectedIds.has(row.caseId)" @change="toggleRow(row)" />
              </template>
            </el-table-column>
            <el-table-column prop="caseNumber" :label="t('recommend.caseNumber')" width="180">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="row.caseNumber" placement="top-start" :show-after="300">
                  <span class="cell-ellipsis">{{ row.caseNumber }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="title" :label="t('recommend.caseTitle')" min-width="220">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="row.title" placement="top-start" :show-after="300">
                  <span class="cell-ellipsis">{{ row.title }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="module" :label="t('recommend.module')" width="130">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="row.module" placement="top" :show-after="300">
                  <span class="cell-ellipsis">{{ row.module }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="projectName" :label="t('recommend.caseLib')" width="120">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="row.projectName" placement="top" :show-after="300">
                  <span class="cell-ellipsis">{{ row.projectName }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="aiScore" :label="t('recommend.aiScore')" width="120" sortable>
              <template #default="{ row }">
                <el-progress :percentage="row.aiScore" :color="scoreColor(row.aiScore)" :stroke-width="16" :text-inside="true" />
              </template>
            </el-table-column>
            <el-table-column prop="reason" :label="t('recommend.reason')" min-width="180">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="row.reason" placement="top-start" :show-after="300">
                  <span class="cell-ellipsis">
                    <el-tag v-if="row.prLinked" type="danger" size="small" style="margin-right: 4px">PR</el-tag>
                    {{ row.reason }}
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
          </el-table>

          <div class="result-pagination">
            <el-pagination
              v-model:current-page="casePage"
              v-model:page-size="casePageSize"
              :page-sizes="[10, 20, 50, 100]"
              :total="filteredCases.length"
              layout="total, sizes, prev, pager, next"
              small
            />
          </div>
        </el-card>

        <!-- Step 4: 覆盖率分析 -->
        <el-card v-if="coverageResult" class="coverage-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><PieChart /></el-icon> {{ t('recommend.coverageAnalysis') }}</span>
              <el-button
                v-if="false"
                size="small"
                type="warning"
                :loading="generatingSupplement"
                :disabled="supplementGenerated"
                @click="handleGenerateSupplement"
              >
                <el-icon><MagicStick /></el-icon>{{ supplementGenerated ? t('recommend.supplementGenerated') : t('recommend.generateSupplement') }}
              </el-button>
            </div>
          </template>

          <el-row :gutter="20">
            <el-col :span="8">
              <div class="coverage-item">
                <el-progress type="circle" :percentage="coverageResult.coverageRate" :width="120" :color="scoreColor(coverageResult.coverageRate)" />
                <div class="coverage-label">{{ t('recommend.coverageRate') }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="coverage-item left-align">
                <div class="coverage-list-title">{{ t('recommend.uncoveredFeatures') }}</div>
                <ul class="coverage-list">
                  <li v-for="item in coverageResult.uncoveredFeatures" :key="item">{{ item }}</li>
                  <li v-if="!coverageResult.uncoveredFeatures || coverageResult.uncoveredFeatures.length === 0" class="empty">{{ t('recommend.allCovered') }}</li>
                </ul>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="coverage-item left-align">
                <div class="coverage-list-title">{{ t('recommend.riskWarnings') }}</div>
                <ul class="coverage-list risk">
                  <li v-for="item in coverageResult.riskWarnings" :key="item">{{ item }}</li>
                </ul>
              </div>
            </el-col>
          </el-row>
        </el-card>

        <!-- 补充用例生成进度 -->
        <el-card v-if="false" class="progress-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="progress-header-text"><el-icon class="spinning"><Loading /></el-icon> {{ t('recommend.generatingSupplement') }}</span>
            </div>
          </template>
          <div class="progress-content">
            <el-progress :percentage="supplementProgress?.progress || 0" :stroke-width="20" :text-inside="true" :color="progressColors" />
            <div class="progress-message">
              {{ supplementProgress?.message || '准备中...' }}
            </div>
          </div>
        </el-card>

        <!-- Step 5: AI补充用例 -->
        <el-card v-if="false" class="supplement-card" shadow="never">
          <template #header>
            <div class="card-header">
              <span><el-icon><MagicStick /></el-icon> {{ t('recommend.supplementCases') }}（{{ supplementCases.length }}）</span>
              <el-button size="small" @click="handleExport" :loading="exporting"><el-icon><Download /></el-icon>{{ t('recommend.export') }}</el-button>
            </div>
          </template>
          <el-table :data="supplementCases" border stripe size="small">
            <el-table-column prop="module" :label="t('recommend.module')" width="140" show-overflow-tooltip />
            <el-table-column prop="name" :label="t('recommend.caseTitle')" min-width="200" show-overflow-tooltip />
            <el-table-column prop="precondition" :label="t('recommend.precondition')" width="150" show-overflow-tooltip />
            <el-table-column prop="steps" :label="t('recommend.steps')" min-width="200" show-overflow-tooltip />
            <el-table-column prop="expected_result" :label="t('recommend.expectedResult')" min-width="150" show-overflow-tooltip />
          </el-table>
        </el-card>
        </div>
      </el-tab-pane>

      <!-- ===== 历史记录 Tab ===== -->
      <el-tab-pane :label="t('recommend.history')" name="history">
        <div class="tab-content">
        <el-card shadow="never">
          <div class="history-toolbar">
            <el-input
              v-model="historyKeyword"
              :placeholder="t('recommend.searchTitle')"
              clearable
              style="width: 250px"
              @keyup.enter="loadHistory"
            />
            <el-button @click="loadHistory"><el-icon><Search /></el-icon>{{ t('recommend.search') }}</el-button>
          </div>

          <el-table :data="historyList" v-loading="historyLoading" border stripe>
            <el-table-column prop="title" :label="t('recommend.recommendTitle')" min-width="200">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="row.title" placement="top-start" :show-after="300">
                  <span class="cell-ellipsis">{{ row.title }}</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="projectNames" :label="t('recommend.caseLib')" width="150">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" :content="(row.projectNames || []).join('、')" placement="top" :show-after="300">
                  <span>
                    <el-tag v-for="n in (row.projectNames || []).slice(0, 2)" :key="n" size="small" style="margin: 1px">{{ n }}</el-tag>
                    <span v-if="(row.projectNames || []).length > 2" class="more-tag">+{{ row.projectNames.length - 2 }}</span>
                  </span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="riskLevel" :label="t('recommend.risk')" width="70" align="center">
              <template #default="{ row }">
                <el-tag :type="riskLevelType(row.riskLevel)" size="small">{{ row.riskLevel }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="recommendedCount" :label="t('recommend.recommendCount')" width="80" align="center" />
            <el-table-column prop="coverageRate" :label="t('recommend.coverageRate')" width="120" align="center">
              <template #default="{ row }">
                <el-progress :percentage="row.coverageRate" :stroke-width="14" :text-inside="true" :color="scoreColor(row.coverageRate)" />
              </template>
            </el-table-column>
            <el-table-column prop="suiteName" :label="t('recommend.linkedSuite')" width="120">
              <template #default="{ row }">
                <el-tooltip popper-class="ai-recommend-tooltip" v-if="row.suiteName" :content="row.suiteName" placement="top" :show-after="300">
                  <span class="cell-ellipsis">{{ row.suiteName }}</span>
                </el-tooltip>
                <span v-else class="text-muted">{{ t('recommend.notCreated') }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="createdByName" :label="t('recommend.creator')" width="90" />
            <el-table-column prop="createdAt" :label="t('recommend.createTime')" width="160">
              <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
            </el-table-column>
            <el-table-column :label="t('common.operation') || '操作'" width="130" fixed="right">
              <template #default="{ row }">
                <template v-if="isTaskRunning(row.id)">
                  <el-button size="small" text type="warning" @click="handleAbortTask(row)">{{ t('recommend.abortTask') }}</el-button>
                </template>
                <template v-else>
                  <el-button size="small" link @click="viewHistoryDetail(row)">{{ t('recommend.detail') }}</el-button>
                  <el-button size="small" link type="danger" @click="handleDeleteHistory(row)">{{ t('recommend.delete') }}</el-button>
                </template>
              </template>
            </el-table-column>
          </el-table>

          <el-pagination
            v-if="historyTotal > 0"
            :current-page="historyPage"
            :page-size="historyPageSize"
            :total="historyTotal"
            layout="total, prev, pager, next"
            @current-change="p => { historyPage = p; loadHistory() }"
            class="pagination"
          />
        </el-card>
        </div>
      </el-tab-pane>

      <!-- ===== 任务队列 Tab ===== -->
      <el-tab-pane v-if="hasButton('aivoiceRecommendations', 'taskQueue')" :label="`${t('recommend.taskQueue')}${queueList.filter(q => q.status === 'waiting' || q.status === 'running').length > 0 ? ' (' + queueList.filter(q => q.status === 'waiting' || q.status === 'running').length + ')' : ''}`" name="queue">
        <div class="tab-content">
          <el-card shadow="never" v-loading="queueLoading">
            <div class="queue-toolbar">
              <span class="queue-info-text" v-if="queueActiveCount > 0">{{ t('recommend.queueRunning') }}：{{ queueActiveCount }}/{{ MAX_CONCURRENT_TASKS }} | {{ t('recommend.totalWaiting') }}：{{ queueWaitingCount }}</span>
            </div>
              <el-table :data="queueList" border stripe empty-text="">
              <el-table-column type="index" width="50" label="#" />
              <el-table-column prop="title" :label="t('recommend.recommendTitle')" min-width="180">
                <template #default="{ row }">
                  <span>{{ row.title || `AI推荐 #${row.historyId}` }}</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('recommend.risk')" width="90" align="center">
                <template #default="{ row }">
                  <el-tag :type="queueStatusType(row.status)" size="small">{{ t('recommend.' + queueStatusKey(row.status)) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column :label="t('recommend.aiScore')" width="180">
                <template #default="{ row }">
                  <el-progress
                    :percentage="row.progress?.progress || 0"
                    :stroke-width="16"
                    :text-inside="true"
                    :color="row.status === 'failed' || row.status === 'aborted' ? '#f56c6c' : row.status === 'completed' ? '#67c23a' : '#409eff'"
                  />
                </template>
              </el-table-column>
              <el-table-column prop="createdAt" :label="t('recommend.createTime')" width="160">
                <template #default="{ row }">{{ formatTime(row.createdAt) }}</template>
              </el-table-column>
              <el-table-column prop="status" :label="t('recommend.queuePosition')" width="100" align="center">
                <template #default="{ row }">
                  <span v-if="row.status === 'waiting'">{{ queueWaitingItems.indexOf(row) + 1 }}</span>
                  <span v-else-if="row.status === 'running'">-</span>
                  <span v-else class="text-muted">-</span>
                </template>
              </el-table-column>
              <el-table-column :label="t('common.operation')" width="160" fixed="right">
                <template #default="{ row }">
                  <template v-if="row.status === 'waiting' && queueWaitingItems.length >= 2">
                    <el-button size="small" text :disabled="queueWaitingItems.indexOf(row) === 0" @click="moveQueueItem(row, -1)"><el-icon><Top /></el-icon></el-button>
                    <el-button size="small" text :disabled="queueWaitingItems.indexOf(row) === queueWaitingItems.length - 1" @click="moveQueueItem(row, 1)"><el-icon><Bottom /></el-icon></el-button>
                  </template>
                  <template v-if="row.status === 'waiting' || row.status === 'running'">
                    <el-button size="small" text type="warning" @click="handleAbortQueueTask(row)">{{ t('recommend.abortTask') }}</el-button>
                  </template>
                </template>
              </el-table-column>
            </el-table>
            <div v-if="queueList.length === 0" class="queue-empty">{{ t('recommend.queueEmpty') }}</div>
          </el-card>
        </div>
      </el-tab-pane>
    </el-tabs>
    </el-card>

    <!-- 创建测试套件对话框 -->
    <el-dialog v-model="showCreateSuiteDialog" :title="t('recommend.createSuiteTitle')" width="600px" align-center destroy-on-close @closed="suiteUpdateHistoryId = null">
      <el-form :model="suiteForm" label-width="100px" :rules="suiteRules" ref="suiteFormRef">
        <el-form-item :label="t('recommend.suiteName')" prop="name">
          <el-input v-model="suiteForm.name" :placeholder="t('recommend.suiteNamePlaceholder')" />
        </el-form-item>
        <el-form-item :label="t('recommend.team')" prop="teamId">
          <el-select v-model="suiteForm.teamId" filterable :placeholder="t('recommend.teamPlaceholder')" style="width: 100%">
            <el-option v-for="t in teamList" :key="t.id" :label="t.name" :value="t.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('recommend.selectedCases')">
          <el-tag type="info">{{ selectedCases.length }} 条用例</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateSuiteDialog = false">{{ t('recommend.cancel') }}</el-button>
        <el-button type="primary" :loading="creatingSuite" @click="handleCreateSuite">{{ t('recommend.confirmCreate') }}</el-button>
      </template>
    </el-dialog>

    <!-- 创建测试计划对话框 -->
    <el-dialog v-model="showCreatePlanDialog" :title="t('recommend.createPlan')" width="700px" align-center destroy-on-close @closed="handlePlanDialogClosed">
      <el-form :model="planForm" label-width="100px" :rules="planRules" ref="planFormRef">
        <el-form-item :label="t('testplan.name')" prop="name">
          <el-input v-model="planForm.name" :placeholder="t('testplan.inputName')" />
        </el-form-item>
        <el-form-item :label="t('testplan.description')" prop="description">
          <el-input v-model="planForm.description" type="textarea" :rows="3" :placeholder="t('testplan.inputDescription')" />
        </el-form-item>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="t('testplan.startTime')" prop="startTime">
              <el-date-picker v-model="planForm.startTime" type="date" :placeholder="t('testplan.selectStartTime')" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="t('testplan.endTime')" prop="endTime">
              <el-date-picker v-model="planForm.endTime" type="date" :placeholder="t('testplan.selectEndTime')" style="width: 100%" value-format="YYYY-MM-DD" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="t('testplan.executors')" prop="executorIds">
              <el-select
                v-model="planForm.executorIds"
                multiple
                filterable
                remote
                :remote-method="handleExecutorSearch"
                :loading="executorSearchLoading"
                :placeholder="t('testplan.selectExecutors')"
                style="width: 100%"
                @focus="loadPlanMembers"
              >
                <el-option v-for="u in availableExecutors" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="t('testplan.reviewer')" prop="reviewerId">
              <el-select
                v-model="planForm.reviewerId"
                filterable
                remote
                :remote-method="handleReviewerSearch"
                :loading="reviewerSearchLoading"
                :placeholder="t('testplan.selectReviewer')"
                style="width: 100%"
                @focus="loadPlanMembers"
              >
                <el-option v-for="u in availableReviewers" :key="u.id" :label="u.username" :value="u.id" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="t('recommend.selectedCases')">
          <el-tag type="info">{{ planCaseCount }} 条用例</el-tag>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreatePlanDialog = false">{{ t('recommend.cancel') }}</el-button>
        <el-button type="primary" :loading="creatingPlan" @click="handleCreatePlanSubmit">{{ t('common.confirm') }}</el-button>
      </template>
    </el-dialog>

    <!-- 历史详情对话框 -->
    <el-dialog v-model="showHistoryDetail" :title="t('recommend.detail')" width="1200px" align-center>
      <div v-if="historyDetail" class="history-detail">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item :label="t('recommend.recommendTitle')">{{ historyDetail.title }}</el-descriptions-item>
          <el-descriptions-item :label="t('recommend.creator')">{{ historyDetail.createdByName }}</el-descriptions-item>
          <el-descriptions-item :label="t('recommend.caseLib')">
            <el-tag v-for="n in historyDetail.projectNames" :key="n" size="small" style="margin: 2px">{{ n }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('recommend.riskLevel')">
            <el-tag :type="riskLevelType(historyDetail.riskLevel)">{{ historyDetail.riskLevel }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('recommend.affectedModules')" :span="2">
            <el-tag v-for="m in historyDetail.affectedModules" :key="m" size="small" style="margin: 2px">{{ m }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('recommend.testDirections')" :span="2">
            <el-tag v-for="d in historyDetail.testDirections" :key="d" size="small" type="info" style="margin: 2px">{{ d }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="t('recommend.impactSummary')" :span="2">{{ historyDetail.summary }}</el-descriptions-item>
          <el-descriptions-item :label="t('recommend.linkedSuite')">
            <span v-if="historyDetail.suiteName">{{ historyDetail.suiteName }}</span>
            <el-button v-else size="small" type="primary" link @click="createSuiteFromHistory">
              <el-icon><FolderAdd /></el-icon>{{ t('recommend.createSuite') }}
            </el-button>
          </el-descriptions-item>
          <el-descriptions-item :label="t('recommend.createTime')">{{ formatTime(historyDetail.createdAt) }}</el-descriptions-item>
        </el-descriptions>

        <div class="detail-section-title">Release Note</div>
        <div class="detail-release-note">{{ historyDetail.releaseNote }}</div>

        <div class="detail-section-title">
          <span>{{ t('recommend.recommendCases') }}（{{ detailFilteredCases.length }}/{{ (historyDetail.recommendedCases || []).length }}）</span>
          <div class="detail-actions">
            <el-select v-model="detailFilterModule" :placeholder="t('recommend.filterByModule')" clearable size="small" style="width: 130px">
              <el-option v-for="m in detailModuleOptions" :key="m" :label="m" :value="m" />
            </el-select>
            <el-select v-model="detailFilterScore" :placeholder="t('recommend.filterByScore')" clearable size="small" style="width: 120px">
              <el-option label="≥90" value="90" />
              <el-option label="≥80" value="80" />
              <el-option label="≥70" value="70" />
              <el-option label="≥60" value="60" />
            </el-select>
            <el-button size="small" @click="detailSelectAll">{{ detailIsAllSelected ? t('recommend.cancelSelectAll') : t('recommend.selectAll') }}（{{ detailSelectedCases.length }}）</el-button>
<el-button v-if="!historyDetail.suiteName" size="small" type="primary" :disabled="detailSelectedCases.length === 0" @click="createSuiteFromHistorySelection">
  <el-icon><FolderAdd /></el-icon>{{ t('recommend.createSuite') }}（{{ detailSelectedCases.length }}）
</el-button>
<el-button v-if="!historyDetail.suiteName" size="small" type="primary" :disabled="detailSelectedCases.length === 0" @click="handleCreatePlanFromDetail">
  <el-icon><List /></el-icon>{{ t('recommend.createPlan') }}（{{ detailSelectedCases.length }}）
</el-button>
          </div>
        </div>
        <el-table :data="detailPaginatedCases" border stripe size="small" ref="detailTableRef" row-key="caseId">
          <el-table-column width="60">
            <template #default="{ row }">
              <el-checkbox :model-value="detailSelectedIds.has(row.caseId)" @change="toggleDetailRow(row)" />
            </template>
          </el-table-column>
          <el-table-column prop="caseNumber" :label="t('recommend.caseNumber')" width="180">
            <template #default="{ row }">
              <el-tooltip popper-class="ai-recommend-tooltip" :content="row.caseNumber" placement="top-start" :show-after="300">
                <span class="cell-ellipsis">{{ row.caseNumber }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="title" :label="t('recommend.caseTitle')" min-width="200">
            <template #default="{ row }">
              <el-tooltip popper-class="ai-recommend-tooltip" :content="row.title" placement="top-start" :show-after="300">
                <span class="cell-ellipsis">{{ row.title }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="module" :label="t('recommend.module')" width="120">
            <template #default="{ row }">
              <el-tooltip popper-class="ai-recommend-tooltip" :content="row.module" placement="top" :show-after="300">
                <span class="cell-ellipsis">{{ row.module }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="projectName" :label="t('recommend.caseLib')" width="100">
            <template #default="{ row }">
              <el-tooltip popper-class="ai-recommend-tooltip" :content="row.projectName" placement="top" :show-after="300">
                <span class="cell-ellipsis">{{ row.projectName }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column prop="aiScore" :label="t('recommend.aiScore')" width="100">
            <template #default="{ row }">
              <el-progress :percentage="row.aiScore" :color="scoreColor(row.aiScore)" :stroke-width="14" :text-inside="true" />
            </template>
          </el-table-column>
          <el-table-column prop="reason" :label="t('recommend.reason')" min-width="150">
            <template #default="{ row }">
              <el-tooltip popper-class="ai-recommend-tooltip" :content="row.reason" placement="top-start" :show-after="300">
                <span class="cell-ellipsis">{{ row.reason }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
        </el-table>
        <div class="result-pagination">
          <el-pagination
            v-model:current-page="detailPage"
            v-model:page-size="detailPageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="detailFilteredCases.length"
            layout="total, sizes, prev, pager, next"
            small
          />
        </div>

        <template v-if="false">
          <div class="detail-section-title">
            <span>{{ t('recommend.supplementCases') }}（{{ historyDetail.supplementCases.length }}）</span>
          </div>
          <el-table :data="historyDetail.supplementCases" border stripe size="small">
            <el-table-column prop="module" :label="t('recommend.module')" width="140" show-overflow-tooltip />
            <el-table-column prop="name" :label="t('recommend.caseTitle')" min-width="200" show-overflow-tooltip />
            <el-table-column prop="precondition" :label="t('recommend.precondition')" width="150" show-overflow-tooltip />
            <el-table-column prop="steps" :label="t('recommend.steps')" min-width="200" show-overflow-tooltip />
            <el-table-column prop="expected_result" :label="t('recommend.expectedResult')" min-width="150" show-overflow-tooltip />
          </el-table>
        </template>
      </div>
      <div v-else class="detail-loading">
        <el-icon class="spinning" :size="24"><Loading /></el-icon>
        <span>{{ t('common.loading') || 'Loading...' }}</span>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Setting, DataAnalysis, List, MagicStick, FolderAdd, PieChart, Search, Loading, Close, Download, Link, Sort, Top, Bottom } from '@element-plus/icons-vue'
import { createTestSuite } from '@/api/testSuite'
import { createTestPlan } from '@/api/testplan'
import { getTeamMembers, getAvailableMembersForSelection } from '@/api/team'
import { useUserRole } from '@/composables/useUserRole'
import { useTeam } from '@/composables/useTeam'
import { analyzeAndRecommend, getAnalyzeProgress, getRunningTask, abortTask, fetchPrInfo, getLatestAnalysis, getRecommendHistory, getRecommendHistoryDetail, deleteRecommendHistory, updateRecommendHistorySuite, generateSupplementCases, getSupplementProgress, exportRecommendExcel, getQueue, reorderQueue } from '@/api/aivoice'

// ===== Tab状态 =====
const router = useRouter()
const { t } = useI18n()
const { hasButton } = useUserRole()
const activeTab = ref('create')

// ===== 新建推荐 =====
const { currentTeam, teamList, teamProjects, loadingProjects, loadTeamProjects } = useTeam()
const teamMembers = ref([])
const analyzing = ref(false)
const taskRunning = ref(false)
const taskProgress = ref({ status: '', progress: 0, message: '' })
const analysisResult = ref(null)
const recommendedCases = ref([])
const coverageResult = ref(null)
const selectedCases = ref([])
const showCreateSuiteDialog = ref(false)
const creatingSuite = ref(false)
const tableRef = ref(null)
const suiteFormRef = ref(null)
const currentHistoryId = ref(null)
const suiteUpdateHistoryId = ref(null)
let pollTimer = null

// ===== 任务队列 =====
const queueList = ref([])
const queueLoading = ref(false)
const MAX_CONCURRENT_TASKS = 3
let queuePollTimer = null

const queueActiveCount = computed(() => queueList.value.filter(q => q.status === 'running').length)
const queueWaitingCount = computed(() => queueList.value.filter(q => q.status === 'waiting').length)
const queueWaitingItems = computed(() => queueList.value.filter(q => q.status === 'waiting'))

const queueStatusType = (status) => {
  const map = { waiting: 'warning', running: 'primary', completed: 'success', failed: 'danger', aborted: 'info' }
  return map[status] || 'info'
}

const queueStatusKey = (status) => {
  const map = { waiting: 'queueWaiting', running: 'queueRunning', completed: 'queueCompleted', failed: 'queueFailed', aborted: 'queueAborted' }
  return map[status] || 'queueWaiting'
}

const startQueuePolling = () => {
  if (queuePollTimer) clearInterval(queuePollTimer)
  queuePollTimer = setInterval(async () => {
    try {
      const res = await getQueue()
      queueList.value = (res.data || []).map(q => ({
        ...q,
        title: q.progress?.message || '',
        progress: q.progress || { progress: 0, status: q.status, message: '' }
      }))
      // 检测当前用户的排队任务是否已开始执行
      const myTask = queueList.value.find(q => q.historyId === currentHistoryId.value)
      if (myTask && myTask.status === 'running' && !taskRunning.value) {
        taskRunning.value = true
        taskProgress.value = myTask.progress
        startPolling(myTask.historyId)
      }
    } catch (e) {
      console.error('轮询队列失败', e)
    }
  }, 3000)
}

const stopQueuePolling = () => {
  if (queuePollTimer) {
    clearInterval(queuePollTimer)
    queuePollTimer = null
  }
}

const loadQueue = async () => {
  queueLoading.value = true
  try {
    const res = await getQueue()
    queueList.value = (res.data || []).map(q => ({
      ...q,
      title: q.progress?.message || '',
      progress: q.progress || { progress: 0, status: q.status, message: '' }
    }))
  } catch (e) {
    console.error('加载队列失败', e)
  } finally {
    queueLoading.value = false
  }
}

const handleQueueReorder = async () => {
  if (queueWaitingItems.value.length < 2) return
  const ids = queueList.value.map(q => q.historyId)
  try {
    await reorderQueue(ids)
    ElMessage.success(t('recommend.reorderSuccess'))
    await loadQueue()
  } catch (e) {
    ElMessage.error(t('common.requestFailed') || '操作失败')
  }
}

const moveQueueItem = (item, direction) => {
  const idx = queueList.value.findIndex(q => q.historyId === item.historyId)
  if (idx === -1) return
  const targetIdx = idx + direction
  if (targetIdx < 0 || targetIdx >= queueList.value.length) return
  // 交换位置
  const arr = queueList.value
  ;[arr[idx], arr[targetIdx]] = [arr[targetIdx], arr[idx]]
  // 触发响应式更新
  queueList.value = [...arr]
  // 自动保存新顺序
  handleQueueReorder()
}

const handleAbortQueueTask = async (item) => {
  try {
    await ElMessageBox.confirm('确定中止该任务？', '中止任务', { type: 'warning', confirmButtonText: '中止', cancelButtonText: '取消' })
    await abortTask(item.historyId)
    ElMessage.success('任务已中止')
    await loadQueue()
    if (item.status === 'running') {
      // 如果是运行中的任务被中止，更新当前状态
      if (currentHistoryId.value === item.historyId) {
        if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
        taskRunning.value = false
        taskProgress.value = { status: 'aborted', progress: 0, message: '' }
        currentHistoryId.value = null
      }
    }
  } catch (e) {
    // cancelled
  }
}

// 筛选
const filterModule = ref('')
const filterScore = ref('')

// 分页
const casePage = ref(1)
const casePageSize = ref(20)

// 导出
const exporting = ref(false)

// 补充用例
const generatingSupplement = ref(false)
const supplementCases = ref([])
const supplementGenerated = ref(false)
const supplementProgress = ref(null)
let supplementPollTimer = null

// 最近分析
const latestAnalysis = ref(null)

const progressColors = [
  { color: '#909399', percentage: 20 },
  { color: '#e6a23c', percentage: 50 },
  { color: '#1989fa', percentage: 80 },
  { color: '#67c23a', percentage: 100 }
]

const config = ref({
  projectIds: [],
  releaseNote: '',
  title: '',
  prNumbers: ''
})

const prInfoList = ref([])
const fetchingPr = ref(false)

const suiteForm = ref({
  name: '',
  teamId: null,
  reviewers: [],
  executors: [],
  owner: null
})

const suiteRules = {
  name: [{ required: true, message: '请输入套件名称', trigger: 'blur' }],
  teamId: [{ required: true, message: '请选择项目组', trigger: 'change' }]
}

// ===== 创建计划 =====
const showCreatePlanDialog = ref(false)
const creatingPlan = ref(false)
const planFormRef = ref(null)
const planCaseSource = ref('main') // 'main' | 'detail'
const planForm = ref({
  name: '',
  description: '',
  startTime: null,
  endTime: null,
  executorIds: [],
  reviewerId: null
})

const availableExecutors = ref([])
const availableReviewers = ref([])
const executorSearchLoading = ref(false)
const reviewerSearchLoading = ref(false)

const planRules = {
  name: [{ required: true, message: '请输入计划名称', trigger: 'blur' }],
  startTime: [{ required: true, message: '请选择开始时间', trigger: 'change' }],
  endTime: [{ required: true, message: '请选择结束时间', trigger: 'change' }],
  executorIds: [{ required: true, message: '请选择执行人', trigger: 'change' }],
  reviewerId: [{ required: true, message: '请选择审核人', trigger: 'change' }]
}

const planCaseCount = computed(() => {
  return planCaseSource.value === 'detail' ? detailSelectedCases.value.length : selectedCases.value.length
})

// ===== 历史记录 =====
const historyList = ref([])
const historyLoading = ref(false)
const historyTotal = ref(0)
const historyPage = ref(1)
const historyPageSize = ref(15)
const historyKeyword = ref('')
const showHistoryDetail = ref(false)
const historyDetail = ref(null)
const detailTableRef = ref(null)
const detailPage = ref(1)
const detailPageSize = ref(20)
const detailFilterModule = ref('')
const detailFilterScore = ref('')
const detailSelectedCases = ref([])

// ===== 计算属性 =====
const canAnalyze = computed(() => {
  const hasProject = config.value.projectIds.length > 0
  const hasReleaseNote = config.value.releaseNote.trim().length > 0
  const hasPr = prInfoList.value.length > 0
  return hasProject && (hasReleaseNote || hasPr)
})

const isAllSelected = computed(() => {
  return filteredCases.value.length > 0 && selectedCases.value.length === filteredCases.value.length
})

const moduleOptions = computed(() => {
  const modules = new Set(recommendedCases.value.map(c => c.module).filter(Boolean))
  return Array.from(modules).sort()
})

const filteredCases = computed(() => {
  let list = recommendedCases.value
  if (filterModule.value) {
    list = list.filter(c => c.module === filterModule.value)
  }
  if (filterScore.value) {
    const min = parseInt(filterScore.value)
    list = list.filter(c => c.aiScore >= min)
  }
  return list
})

const paginatedCases = computed(() => {
  const start = (casePage.value - 1) * casePageSize.value
  return filteredCases.value.slice(start, start + casePageSize.value)
})

// Detail dialog computed
const detailModuleOptions = computed(() => {
  if (!historyDetail.value) return []
  const modules = new Set((historyDetail.value.recommendedCases || []).map(c => c.module).filter(Boolean))
  return Array.from(modules).sort()
})

const detailFilteredCases = computed(() => {
  if (!historyDetail.value) return []
  let list = historyDetail.value.recommendedCases || []
  if (detailFilterModule.value) {
    list = list.filter(c => c.module === detailFilterModule.value)
  }
  if (detailFilterScore.value) {
    const min = parseInt(detailFilterScore.value)
    list = list.filter(c => c.aiScore >= min)
  }
  return list
})

const detailPaginatedCases = computed(() => {
  const start = (detailPage.value - 1) * detailPageSize.value
  return detailFilteredCases.value.slice(start, start + detailPageSize.value)
})

const detailSelectedIds = computed(() => new Set(detailSelectedCases.value.map(c => c.caseId)))

const detailIsAllSelected = computed(() => {
  return detailFilteredCases.value.length > 0 && detailFilteredCases.value.every(row =>
    detailSelectedIds.value.has(row.caseId)
  )
})

const toggleDetailRow = (row) => {
  const idx = detailSelectedCases.value.findIndex(c => c.caseId === row.caseId)
  if (idx >= 0) {
    detailSelectedCases.value.splice(idx, 1)
  } else {
    detailSelectedCases.value = [...detailSelectedCases.value, row]
  }
}

const detailSelectAll = () => {
  if (detailIsAllSelected.value) {
    detailSelectedCases.value = []
  } else {
    detailSelectedCases.value = [...detailFilteredCases.value]
  }
}

// ===== 工具方法 =====
const riskLevelType = (level) => {
  const map = { '高': 'danger', '中': 'warning', '低': 'success' }
  return map[level] || 'info'
}

const scoreColor = (score) => {
  if (score >= 80) return '#67c23a'
  if (score >= 60) return '#e6a23c'
  return '#f56c6c'
}

const formatTime = (t) => t ? new Date(t).toLocaleString('zh-CN') : ''

const selectedIds = computed(() => new Set(selectedCases.value.map(c => c.caseId)))

const toggleRow = (row) => {
  const idx = selectedCases.value.findIndex(c => c.caseId === row.caseId)
  if (idx >= 0) {
    selectedCases.value.splice(idx, 1)
  } else {
    selectedCases.value = [...selectedCases.value, row]
  }
}

const selectAll = () => {
  if (isAllSelected.value) {
    selectedCases.value = []
  } else {
    selectedCases.value = [...filteredCases.value]
  }
}

// ===== PR 关联 =====
const handleFetchPr = async () => {
  if (!config.value.prNumbers.trim()) {
    ElMessage.warning('请输入PR编号')
    return
  }
  fetchingPr.value = true
  try {
    const res = await fetchPrInfo(config.value.prNumbers.trim())
    const data = res.data || []
    // 过滤掉查询失败的，合并到已有列表（去重）
    const existingIds = new Set(prInfoList.value.map(p => p.prNumber))
    let addedCount = 0
    let failedCount = 0
    for (const pr of data) {
      if (pr.error) {
        failedCount++
        continue
      }
      if (!existingIds.has(pr.prNumber)) {
        prInfoList.value.push(pr)
        addedCount++
      }
    }
    config.value.prNumbers = ''
    if (failedCount > 0 && addedCount === 0) {
      ElMessage.error(`${failedCount} 个PR查询失败，请检查编号是否正确`)
    } else if (failedCount > 0) {
      ElMessage.warning(`已添加 ${addedCount} 个PR，${failedCount} 个查询失败`)
    } else if (addedCount > 0) {
      ElMessage.success(`已添加 ${addedCount} 个PR`)
    } else {
      ElMessage.info('PR已存在，无需重复添加')
    }
  } catch (e) {
    console.error('读取PR失败', e)
  } finally {
    fetchingPr.value = false
  }
}

const removePr = (prNumber) => {
  prInfoList.value = prInfoList.value.filter(p => p.prNumber !== prNumber)
}

// ===== 导出 =====
const handleExport = async () => {
  if (!currentHistoryId.value) {
    ElMessage.warning('请先完成AI分析')
    return
  }
  exporting.value = true
  try {
    const response = await exportRecommendExcel(currentHistoryId.value)
    const blob = new Blob([response.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `AI推荐用例_${currentHistoryId.value}.xlsx`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

// ===== AI补充用例 =====
const startSupplementPolling = (historyId) => {
  if (supplementPollTimer) clearInterval(supplementPollTimer)
  supplementPollTimer = setInterval(async () => {
    try {
      const res = await getSupplementProgress(historyId)
      const data = res?.data
      if (!data) return
      supplementProgress.value = data

      if (data.status === 'completed') {
        clearInterval(supplementPollTimer)
        supplementPollTimer = null
        generatingSupplement.value = false
        // 重新加载结果（用同一个 historyId）
        const detailRes = await getRecommendHistoryDetail(historyId)
        const detailData = detailRes.data
        const cases = (detailData?.supplementCases?.length > 0) ? detailData.supplementCases : []
        supplementCases.value = cases
        if (cases.length > 0) {
          supplementGenerated.value = true
          ElMessage.success(data.message || '补充用例生成完成')
        } else {
          supplementProgress.value = null
          ElMessage.warning('AI 未生成有效的补充用例，可重新尝试')
        }
      } else if (data.status === 'failed') {
        clearInterval(supplementPollTimer)
        supplementPollTimer = null
        generatingSupplement.value = false
        supplementProgress.value = null
        ElMessage.error(data.message || '生成补充用例失败')
      }
    } catch (e) {
      console.error('轮询补充用例进度失败', e)
    }
  }, 2000)
}

const handleGenerateSupplement = async () => {
  if (!coverageResult.value || !coverageResult.value.uncoveredFeatures?.length) return
  generatingSupplement.value = true
  supplementProgress.value = null
  try {
    const res = await generateSupplementCases({
      historyId: currentHistoryId.value,
      uncoveredFeatures: coverageResult.value.uncoveredFeatures
    })
    startSupplementPolling(res.data.historyId)
  } catch (e) {
    const errMsg = e?.response?.data?.detail || e.message || '生成补充用例失败'
    ElMessage.error(errMsg)
    generatingSupplement.value = false
  }
}

// ===== 数据加载 =====
const loadLatestAnalysis = async () => {
  try {
    const res = await getLatestAnalysis()
    const data = res.data
    if (data && teamProjects.value.length > 0) {
      const teamProjectIds = new Set(teamProjects.value.map(p => p.id))
      if (data.projectIds?.some(id => teamProjectIds.has(id))) {
        latestAnalysis.value = data
        return
      }
    }
    latestAnalysis.value = null
  } catch (e) {
    latestAnalysis.value = null
  }
}

const loadLatestDetail = () => {
  if (latestAnalysis.value) {
    currentHistoryId.value = latestAnalysis.value.id
    analysisResult.value = {
      affectedModules: latestAnalysis.value.affectedModules || [],
      riskLevel: latestAnalysis.value.riskLevel,
      testDirections: latestAnalysis.value.testDirections || [],
      summary: latestAnalysis.value.summary || ''
    }
    recommendedCases.value = (latestAnalysis.value.recommendedCases || []).map((c, idx) => ({ ...c, _idx: idx }))
    coverageResult.value = latestAnalysis.value.coverageData || null
    filterModule.value = ''
    filterScore.value = ''
    casePage.value = 1
    selectedCases.value = []
    detailSelectedCases.value = []
    if (latestAnalysis.value.supplementCases?.length > 0) {
      supplementCases.value = latestAnalysis.value.supplementCases
      supplementGenerated.value = true
    }
  }
}

const loadTeamMembers = async () => {
  if (!currentTeam.value) return
  try {
    const res = await getTeamMembers(currentTeam.value.id)
    teamMembers.value = res.data || []
  } catch (e) {
    console.error('加载项目组成员失败', e)
  }
}

// ===== AI 分析（后台任务模式） =====
const startAnalysis = async () => {
  if (!canAnalyze.value) return
  analyzing.value = true
  analysisResult.value = null
  recommendedCases.value = []
  coverageResult.value = null
  selectedCases.value = []
  supplementCases.value = []
  supplementGenerated.value = false
  supplementProgress.value = null
  if (supplementPollTimer) {
    clearInterval(supplementPollTimer)
    supplementPollTimer = null
  }
  currentHistoryId.value = null

  try {
    // 将PR信息拼接到Release Note中供AI分析
    let fullReleaseNote = config.value.releaseNote
    if (prInfoList.value.length > 0) {
      const prContext = prInfoList.value.map(pr => {
        let text = `\n【PR#${pr.prNumber}】${pr.subject}`
        if (pr.rootCause) text += `\nRoot Cause: ${pr.rootCause}`
        if (pr.solution) text += `\nSolution: ${pr.solution}`
        return text
      }).join('\n')
      fullReleaseNote = `${fullReleaseNote}\n\n--- 关联PR信息 ---${prContext}`
    }

    const res = await analyzeAndRecommend({
      projectIds: config.value.projectIds,
      releaseNote: fullReleaseNote,
      title: config.value.title || undefined,
      prNumbers: prInfoList.value.length > 0 ? prInfoList.value.map(p => p.prNumber).join(',') : undefined
    })

    currentHistoryId.value = res.data.historyId

    if (res.data.status === 'waiting') {
      // 加入队列
      taskProgress.value = { status: 'waiting', progress: 0, message: `排队中...` }
      ElMessage.info(t('recommend.enterQueue', { position: res.data.queuePosition }) || `已加入队列，当前排在第 ${res.data.queuePosition} 位`)
      // 更新队列列表
      await loadQueue()
    } else {
      // 立即执行
      taskRunning.value = true
      taskProgress.value = { status: 'running', progress: 0, message: '任务已创建...' }
      startPolling(res.data.historyId)
    }
    // 也轮询队列以同步状态
    if (!queuePollTimer) startQueuePolling()
  } catch (e) {
    console.error('创建分析任务失败', e)
  } finally {
    analyzing.value = false
  }
}

const startPolling = (historyId) => {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const res = await getAnalyzeProgress(historyId)
      const data = res?.data
      if (!data) return
      taskProgress.value = data

      if (data.status === 'completed') {
        clearInterval(pollTimer)
        pollTimer = null
        taskRunning.value = false
        ElMessage.success(data.message || '分析完成')
        // 加载完整结果
        await loadAnalysisResult(historyId)
      } else if (data.status === 'failed') {
        clearInterval(pollTimer)
        pollTimer = null
        taskRunning.value = false
        ElMessage.error(data.message || '分析失败')
      }
    } catch (e) {
      console.error('轮询进度失败', e)
    }
  }, 2000) // 每2秒轮询
}

const loadAnalysisResult = async (historyId) => {
  try {
    const res = await getRecommendHistoryDetail(historyId)
    const data = res.data

    if (data.affectedModules && data.affectedModules.length > 0) {
      analysisResult.value = {
        affectedModules: data.affectedModules,
        riskLevel: data.riskLevel,
        testDirections: data.testDirections || [],
        summary: data.summary || ''
      }
    }

    if (data.recommendedCases && data.recommendedCases.length > 0) {
      recommendedCases.value = data.recommendedCases.map((c, idx) => ({ ...c, _idx: idx }))
    }

    if (data.coverageData) {
      coverageResult.value = data.coverageData
    }

    if (data.supplementCases && data.supplementCases.length > 0) {
      supplementCases.value = data.supplementCases
      supplementGenerated.value = true
    }
  } catch (e) {
    console.error('加载分析结果失败', e)
  }
}

// ===== 创建套件 =====
const openCreateSuiteDialog = () => {
  suiteForm.value.teamId = currentTeam.value?.id || null
  showCreateSuiteDialog.value = true
}

const handleCreateSuite = async () => {
  const valid = await suiteFormRef.value?.validate().catch(() => false)
  if (!valid) return

  creatingSuite.value = true
  try {
    const res = await createTestSuite({
      name: suiteForm.value.name,
      team_id: suiteForm.value.teamId,
      test_case_ids: selectedCases.value.map(c => c.caseId),
      source: 'ai_recommendation'
    })

    // 更新历史记录的套件关联
    const targetHistoryId = suiteUpdateHistoryId.value || currentHistoryId.value
    if (targetHistoryId) {
      try {
        await updateRecommendHistorySuite(targetHistoryId, {
          historyId: targetHistoryId,
          suiteId: res.data?.id || res.data?.data?.id || 0,
          suiteName: suiteForm.value.name
        })
      } catch (e) {
        console.warn('更新历史套件关联失败', e)
      }
    }
    suiteUpdateHistoryId.value = null

    ElMessage.success('测试套件创建成功')
    showCreateSuiteDialog.value = false
    suiteForm.value = { name: '', teamId: null, reviewers: [], executors: [], owner: null }

    // 创建成功后引导
    ElMessageBox.confirm('测试套件创建成功！是否前往测试计划页面查看？', '创建成功', {
      confirmButtonText: '前往查看',
      cancelButtonText: '留在当前',
      type: 'success'
    }).then(() => {
      router.push('/testplans')
    }).catch(() => {})
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '创建套件失败')
  } finally {
    creatingSuite.value = false
  }
}

// ===== 创建计划 =====
let loadedPlanMembersTeamId = null

const loadPlanMembers = async () => {
  if (!currentTeam.value) return
  if (loadedPlanMembersTeamId === currentTeam.value.id) return
  loadedPlanMembersTeamId = currentTeam.value.id
  try {
    const [execRes, reviewRes] = await Promise.all([
      getAvailableMembersForSelection(currentTeam.value.id, 'executor', ''),
      getAvailableMembersForSelection(currentTeam.value.id, 'reviewer', '')
    ])
    availableExecutors.value = execRes.data || []
    availableReviewers.value = reviewRes.data || []
  } catch (e) {
    console.error('加载项目组成员失败', e)
  }
}

const handleExecutorSearch = async (query) => {
  if (!currentTeam.value) return
  executorSearchLoading.value = true
  try {
    const res = await getAvailableMembersForSelection(currentTeam.value.id, 'executor', query)
    availableExecutors.value = res.data || []
  } catch (e) {
    console.error('搜索执行人失败', e)
  } finally {
    executorSearchLoading.value = false
  }
}

const handleReviewerSearch = async (query) => {
  if (!currentTeam.value) return
  reviewerSearchLoading.value = true
  try {
    const res = await getAvailableMembersForSelection(currentTeam.value.id, 'reviewer', query)
    availableReviewers.value = res.data || []
  } catch (e) {
    console.error('搜索审核人失败', e)
  } finally {
    reviewerSearchLoading.value = false
  }
}

const handleCreatePlan = () => {
  if (selectedCases.value.length === 0) return
  planCaseSource.value = 'main'
  planForm.value = { name: '', description: '', startTime: null, endTime: null, executorIds: [], reviewerId: null }
  showCreatePlanDialog.value = true
}

const handleCreatePlanFromDetail = () => {
  if (detailSelectedCases.value.length === 0) return
  planCaseSource.value = 'detail'
  planForm.value = { name: '', description: '', startTime: null, endTime: null, executorIds: [], reviewerId: null }
  showCreatePlanDialog.value = true
}

const handlePlanDialogClosed = () => {
  planFormRef.value?.resetFields()
}

const handleCreatePlanSubmit = async () => {
  const valid = await planFormRef.value?.validate().catch(() => false)
  if (!valid) return

  const testcaseIds = planCaseSource.value === 'detail'
    ? detailSelectedCases.value.map(c => c.caseId)
    : selectedCases.value.map(c => c.caseId)

  const projectId = teamProjects.value?.[0]?.id
  if (!currentTeam.value || !projectId) {
    ElMessage.warning('当前项目组下没有关联的用例库，无法创建计划')
    return
  }

  creatingPlan.value = true
  try {
    await createTestPlan({
      name: planForm.value.name,
      description: planForm.value.description,
      start_time: planForm.value.startTime,
      end_time: planForm.value.endTime,
      project_id: projectId,
      team_id: currentTeam.value.id,
      suite_id: null,
      test_case_ids: testcaseIds,
      executor_ids: planForm.value.executorIds,
      viewer_ids: [],
      reviewer_id: planForm.value.reviewerId
    })
    ElMessage.success('测试计划创建成功')
    showCreatePlanDialog.value = false

    ElMessageBox.confirm('测试计划创建成功！是否前往测试计划页面查看？', '创建成功', {
      confirmButtonText: '前往查看',
      cancelButtonText: '留在当前',
      type: 'success'
    }).then(() => {
      router.push('/testplans')
    }).catch(() => {})
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || '创建计划失败')
  } finally {
    creatingPlan.value = false
  }
}

// ===== 历史记录 =====
const loadHistory = async () => {
  historyLoading.value = true
  try {
    const res = await getRecommendHistory({
      page: historyPage.value,
      pageSize: historyPageSize.value,
      keyword: historyKeyword.value || undefined
    })
    const allData = res.data?.data || []
    const teamProjectIds = new Set(teamProjects.value.map(p => p.id))
    historyList.value = allData.filter(r =>
      r.projectIds?.some(id => teamProjectIds.has(id))
    )
    historyTotal.value = historyList.value.length
  } catch (e) {
    console.error('加载历史记录失败', e)
  } finally {
    historyLoading.value = false
  }
}

const viewHistoryDetail = async (row) => {
  historyDetail.value = null
  detailSelectedCases.value = []
  detailFilterModule.value = ''
  detailFilterScore.value = ''
  detailPage.value = 1
  showHistoryDetail.value = true
  try {
    const res = await getRecommendHistoryDetail(row.id)
    historyDetail.value = res.data
  } catch (e) {
    ElMessage.error(t('recommend.loadFailed'))
    showHistoryDetail.value = false
  }
}

const createSuiteFromHistory = () => {
  if (historyDetail.value) {
    suiteUpdateHistoryId.value = historyDetail.value.id
    selectedCases.value = [...(historyDetail.value.recommendedCases || [])]
    suiteForm.value.teamId = currentTeam.value?.id || null
    showHistoryDetail.value = false
    showCreateSuiteDialog.value = true
  }
}

const createSuiteFromHistorySelection = () => {
  if (historyDetail.value) {
    if (detailSelectedCases.value.length === 0) {
      ElMessage.warning(t('recommend.atLeastOneTip') || '请先勾选用例')
      return
    }
    suiteUpdateHistoryId.value = historyDetail.value.id
    selectedCases.value = [...detailSelectedCases.value]
    suiteForm.value.teamId = currentTeam.value?.id || null
    showHistoryDetail.value = false
    showCreateSuiteDialog.value = true
  }
}

const handleDeleteHistory = async (row) => {
  try {
    await ElMessageBox.confirm(`确定删除推荐记录「${row.title}」？`, '确认删除', { type: 'warning' })
    await deleteRecommendHistory(row.id)
    ElMessage.success('删除成功')
    await loadHistory()
  } catch (e) {
    // cancelled
  }
}

const isTaskRunning = (historyId) => {
  return taskRunning.value && currentHistoryId.value === historyId
}

const handleAbortTask = async (row) => {
  try {
    await ElMessageBox.confirm('确定中止当前AI分析任务？', '中止任务', { type: 'warning', confirmButtonText: '中止', cancelButtonText: '取消' })
    await abortTask(row.id)
    // 停止轮询
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
    taskRunning.value = false
    taskProgress.value = { status: 'aborted', progress: 0, message: '' }
    currentHistoryId.value = null
    ElMessage.success('任务已中止')
    await loadHistory()
  } catch (e) {
    // cancelled
  }
}

// 筛选变化时重置分页
watch([filterModule, filterScore], () => {
  casePage.value = 1
})

// 切换到历史Tab时加载数据
watch(activeTab, (val) => {
  if (val === 'history') {
    loadHistory()
  }
})

// 切换项目组时重置所有状态，刷新当前项目组的数据
watch(currentTeam, async (newTeam, oldTeam) => {
  if (newTeam && newTeam.id !== oldTeam?.id) {
    config.value.projectIds = []
    analysisResult.value = null
    recommendedCases.value = []
    coverageResult.value = null
    selectedCases.value = []
    filterModule.value = ''
    filterScore.value = ''
    casePage.value = 1
    currentHistoryId.value = null
    supplementCases.value = []
    supplementGenerated.value = false
    supplementProgress.value = null
    if (supplementPollTimer) {
      clearInterval(supplementPollTimer)
      supplementPollTimer = null
    }
    latestAnalysis.value = null
    await loadTeamProjects()
    loadTeamMembers()
    await loadHistory()
    const res = await getLatestAnalysis()
    const data = res.data
    if (data && teamProjects.value.length > 0) {
      const teamProjectIds = new Set(teamProjects.value.map(p => p.id))
      if (data.projectIds?.some(id => teamProjectIds.has(id))) {
        latestAnalysis.value = data
        loadLatestDetail()
      }
    }
    // 如果最新记录不属于当前团队，从历史列表中取第一条匹配的完整数据
    if (!latestAnalysis.value && historyList.value.length > 0) {
      try {
        const detailRes = await getRecommendHistoryDetail(historyList.value[0].id)
        latestAnalysis.value = detailRes.data
        if (latestAnalysis.value) {
          loadLatestDetail()
        }
      } catch (e) {
        console.error('加载团队历史详情失败', e)
      }
    }
  }
})

// ===== 生命周期 =====
onMounted(async () => {
  if (currentTeam.value) {
    if (teamProjects.value.length === 0) {
      await loadTeamProjects()
    }
    loadTeamMembers()
  }
  await loadLatestAnalysis()
  if (latestAnalysis.value) {
    loadLatestDetail()
  } else {
    // 如果最新记录不属于当前团队，从历史列表中取第一条匹配的
    await loadHistory()
    if (historyList.value.length > 0) {
      try {
        const detailRes = await getRecommendHistoryDetail(historyList.value[0].id)
        if (detailRes.data) {
          latestAnalysis.value = detailRes.data
          loadLatestDetail()
        }
      } catch (e) {
        console.error('加载默认详情失败', e)
      }
    }
  }
  let historyId = currentHistoryId.value
  const runningHid = await checkRunningTask()
  historyId = runningHid || historyId
  if (historyId) {
    await checkSupplementProgress(historyId)
  }
  // 加载队列
  await loadQueue()
  startQueuePolling()
})

const checkRunningTask = async () => {
  try {
    const res = await getRunningTask()
    const data = res.data
    if (data?.running && data.historyId) {
      currentHistoryId.value = data.historyId
      taskRunning.value = true
      taskProgress.value = data.progress || { status: 'running', progress: 0, message: '任务执行中...' }
      startPolling(data.historyId)
      return data.historyId
    }
  } catch (e) {
    // 忽略
  }
  return null
}

const checkSupplementProgress = async (historyId) => {
  const hid = historyId || currentHistoryId.value
  if (!hid || supplementGenerated.value) return
  try {
    const res = await getSupplementProgress(hid)
    const data = res?.data
    if (!data) return
    if (data.status === 'running') {
      generatingSupplement.value = true
      supplementProgress.value = data
      startSupplementPolling(hid)
    } else if (data.status === 'completed') {
      const detailRes = await getRecommendHistoryDetail(hid)
      const detailData = detailRes?.data
      if (detailData) {
        const cases = (detailData.supplementCases?.length > 0) ? detailData.supplementCases : []
        supplementCases.value = cases
        if (cases.length > 0) {
          supplementGenerated.value = true
        }
      }
    }
  } catch (e) {
    // 忽略
  }
}

onUnmounted(() => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (supplementPollTimer) {
    clearInterval(supplementPollTimer)
    supplementPollTimer = null
  }
  stopQueuePolling()
})
</script>

<style scoped>
.ai-recommendations {
  height: 100%;
  background: #f8fafc;
  padding: 24px;
  overflow-y: auto;
  transition: padding 0.3s ease;
}

@media (min-width: 1920px) {
  .ai-recommendations {
    padding: 28px 32px;
  }
}

@media (max-width: 1440px) {
  .ai-recommendations {
    padding: 16px;
  }
}

.main-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.main-card :deep(.el-card__body) {
  padding: 16px 24px 24px;
}

.main-tabs :deep(.el-tabs__header) {
  padding: 0;
  margin-bottom: 0;
}

.main-tabs :deep(.el-tabs__item) {
  font-weight: 500;
  color: #64748b;
  font-size: 15px;
}

.main-tabs :deep(.el-tabs__item.is-active) {
  color: #4f46e5;
}

.main-tabs :deep(.el-tabs__active-bar) {
  background-color: #4f46e5;
}

.tab-content {
  padding-top: 24px;
}

.config-card,
.analysis-card,
.result-card,
.coverage-card,
.progress-card,
.supplement-card,
.latest-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  transition: box-shadow 0.3s ease;
}

.config-card:hover,
.analysis-card:hover,
.result-card:hover,
.coverage-card:hover,
.supplement-card:hover,
.latest-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

/* 最近分析卡片 */
.latest-card {
  background: #fafbff;
}

.latest-time {
  font-size: 12px;
  color: #909399;
  font-weight: normal;
}

.latest-stat {
  text-align: center;
  padding: 8px 0;
}

.latest-stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 4px;
}

.latest-stat-label {
  font-size: 12px;
  color: #909399;
}

.latest-summary {
  margin-top: 12px;
  padding: 10px 12px;
  background: #f0f2f5;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
}

.progress-header-text {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
  color: #409eff;
}

.spinning {
  animation: spin 1.2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-content {
  padding: 24px 40px;
}

.progress-message {
  margin-top: 16px;
  font-size: 14px;
  color: #606266;
  text-align: center;
}

.progress-eta {
  color: #909399;
  font-size: 12px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-header span {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 15px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* PR关联 */
.pr-input-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.pr-info-list {
  margin-top: 10px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  padding: 8px 12px;
  max-height: 180px;
  min-height: 60px;
  overflow-y: auto;
  background: #fafafa;
}

.pr-info-item {
  padding: 10px 0;
  border-bottom: 1px solid #ebeef5;
}

.pr-info-item:last-child {
  border-bottom: none;
}

.pr-info-header {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 28px;
}

.pr-subject {
  flex: 1;
  font-size: 13px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 28px;
}

.pr-info-field {
  font-size: 12px;
  color: #606266;
  padding: 3px 0 3px 58px;
  line-height: 1.5;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.pr-info-field label {
  color: #909399;
  font-weight: 500;
}

.pr-info-field.error {
  color: #f56c6c;
}

/* 分析结果 */
.analysis-item {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  min-height: 90px;
  margin-bottom: 12px;
}

.analysis-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 10px;
  font-weight: 500;
}

.analysis-value {
  font-size: 14px;
  color: #303133;
}

.analysis-tags-wrap {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  overflow-wrap: break-word;
  word-break: break-word;
}

.analysis-tags-wrap :deep(.el-tag) {
  max-width: 100%;
  white-space: normal;
  height: auto;
  line-height: 1.4;
  padding: 2px 8px;
}

.analysis-summary {
  margin-top: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
}

.analysis-text {
  font-size: 14px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
}

/* 覆盖率 */
.coverage-card :deep(.el-card__body) {
  padding: 24px;
}

.coverage-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 16px;
}

.coverage-item.left-align {
  align-items: flex-start;
}

.coverage-label {
  margin-top: 14px;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.coverage-list-title {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 10px;
}

.coverage-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.coverage-list li {
  padding: 6px 0;
  font-size: 13px;
  color: #606266;
  border-bottom: 1px dashed #ebeef5;
}

.coverage-list li::before {
  content: '•';
  color: #409eff;
  margin-right: 6px;
}

.coverage-list.risk li::before {
  color: #f56c6c;
}

.coverage-list li.empty {
  color: #67c23a;
}

.coverage-list li.empty::before {
  content: '';
}

/* 推荐用例表格 */
.result-card :deep(.el-card__body) {
  padding: 16px 20px 20px;
}

.result-card .header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
  flex-wrap: wrap;
}

.result-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.supplement-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
}

/* AI分析结果 - 配置旁边 */
.config-analysis-row {
  margin-bottom: 20px;
}

.analysis-card-inline {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  transition: box-shadow 0.3s ease;
}

.analysis-card-inline:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.result-card :deep(.el-table) {
  --el-table-border-color: #ebeef5;
}

.result-card :deep(.el-table .el-table__cell) {
  padding: 10px 0;
}

.cell-ellipsis {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 100%;
}

/* 历史记录 */
.history-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}

.pagination {
  margin-top: 16px;
  justify-content: flex-end;
}

.more-tag {
  font-size: 12px;
  color: #909399;
  margin-left: 4px;
}

.text-muted {
  color: #c0c4cc;
  font-size: 13px;
}

/* 历史详情 */
.history-detail {
  max-height: 85vh;
  overflow-y: auto;
  padding-bottom: 20px;
}

.history-detail .el-table {
  min-width: 960px;
}

.detail-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 0;
  gap: 12px;
  color: #909399;
  font-size: 14px;
}

.detail-section-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
  margin: 24px 0 12px;
  padding-bottom: 6px;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.detail-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.detail-release-note {
  background: #f5f7fa;
  padding: 14px;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  line-height: 1.8;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

/* 响应式：高分辨率屏幕 */
@media (min-width: 1920px) {
  .analysis-item {
    padding: 20px;
    min-height: 100px;
  }

  .card-header span {
    font-size: 16px;
  }

  .progress-content {
    padding: 28px 60px;
  }
}

/* 响应式：小屏幕 */
@media (max-width: 1440px) {
  .analysis-item {
    padding: 12px;
    min-height: 70px;
  }

  .header-actions {
    gap: 4px;
  }

  .progress-content {
    padding: 20px 24px;
  }
}

@media (max-width: 1200px) {
  .header-actions {
    flex-wrap: wrap;
  }
}

/* PR 关联详情卡片 */
.pr-detail-card {
  margin-bottom: 20px;
  border-radius: 12px;
  border: 1px solid #ebeef5;
  background: #fafbff;
}

.pr-detail-item {
  padding: 8px 0;
  border-bottom: 1px dashed #ebeef5;
}

.pr-detail-item:last-of-type {
  border-bottom: none;
}

.pr-detail-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.pr-detail-subject {
  font-size: 14px;
  color: #303133;
  flex: 1;
}

.pr-detail-field {
  font-size: 13px;
  color: #606266;
  padding: 2px 0 2px 50px;
  line-height: 1.6;
}

.pr-detail-field label {
  color: #909399;
  font-weight: 500;
}

.pr-detail-release-note {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #ebeef5;
}

.pr-detail-release-label {
  font-size: 13px;
  color: #909399;
  font-weight: 500;
  margin-bottom: 4px;
}

.pr-detail-release-content {
  font-size: 13px;
  color: #606266;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* 任务队列 */
.queue-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.queue-info-text {
  font-size: 13px;
  color: #606266;
}

.queue-empty {
  text-align: center;
  color: #909399;
  padding: 40px 0;
  font-size: 14px;
}
</style>


<style>
/* 全局tooltip样式 - AI用例推荐页面 */
.ai-recommend-tooltip.el-popper {
  max-width: 500px !important;
  word-break: break-word !important;
  white-space: normal !important;
  line-height: 1.6 !important;
  font-size: 13px !important;
}
</style>
