<template>
  <div class="testcase-page">
    <!-- 左侧模块筛选 -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed, resizing: isSidebarResizing }" :style="{ width: sidebarCollapsed ? '0px' : sidebarWidth + 'px' }">
      <!-- 展开/收起按钮 -->
      <div 
        class="collapse-btn" 
        @click="toggleSidebar"
        :title="sidebarCollapsed ? $t('common.expand') : $t('common.collapse')"
      >
        <el-icon>
          <DArrowLeft v-if="!sidebarCollapsed" />
          <DArrowRight v-else />
        </el-icon>
      </div>

      <!-- 拖拽调整宽度手柄 -->
      <div
        v-if="!sidebarCollapsed"
        class="sidebar-resize-handle"
        @mousedown="startSidebarResize"
      ></div>
      
      <!-- 模块列表 -->
      <div v-if="!sidebarCollapsed" class="module-container">
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
        <div class="module-search">
          <el-input
            v-model="moduleSearchKeyword"
            :placeholder="$t('testcase.searchModule')"
            size="small"
            clearable
            :prefix-icon="Search"
          />
        </div>
        <div class="module-list" v-loading="moduleListLoading">
          <div 
            class="module-item" 
            :class="{ active: selectedModulePath === '' }"
            @click="handleModuleClick('')"
          >
            <span class="module-name">{{ $t('common.all') }}</span>
            <span class="module-count">{{ totalCount }}</span>
          </div>
          <template v-for="item in filteredSidebarModules" :key="item.path">
            <div 
              class="module-item"
              :class="{ active: selectedModulePath === item.path }"
              :style="{ paddingLeft: (12 + item.depth * 16) + 'px' }"
            >
              <el-icon 
                v-if="item.hasChildren"
                class="expand-icon"
                @click.stop="toggleModulePath(item.path)"
              >
                <ArrowRight v-if="!expandedModulePaths.has(item.path)" />
                <ArrowDown v-else />
              </el-icon>
              <span v-else class="expand-icon-placeholder"></span>
              <div class="module-content" @click="handleModuleClick(item.path)">
                <el-tooltip 
                  :content="item.name" 
                  placement="top"
                  :show-after="500"
                >
                  <span class="module-name">{{ item.name }}<span v-if="item.tag" style="color: #409eff; margin-left: 2px;">({{ item.tag }})</span></span>
                </el-tooltip>
                <span class="module-count">{{ item.count }}</span>
              </div>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 右侧主内容 -->
    <div class="main-content">


      <!-- 统计条 - 紧凑一行 -->
      <div class="stats-bar" v-if="showStatistics && hasSelectedProjects && statistics.total !== undefined">
        <div class="stats-bar-group">
          <span class="stats-bar-label">{{ $t('testcase.statistics.total') }} {{ statistics.total?.toLocaleString() }}</span>
          <span class="stats-bar-divider"></span>
          <span class="stats-bar-tag blue">L1 {{ statistics.level?.L1 || 0 }}</span>
          <span class="stats-bar-tag blue">L2 {{ statistics.level?.L2 || 0 }}</span>
          <span class="stats-bar-tag blue">L3 {{ statistics.level?.L3 || 0 }}</span>
          <span class="stats-bar-tag blue">L4 {{ statistics.level?.L4 || 0 }}</span>
        </div>
        <span class="stats-bar-sep">|</span>
        <div class="stats-bar-group">
          <span class="stats-bar-tag emerald">{{ $t('testcase.automationCompleted') }} {{ statistics.automation?.completed || 0 }}</span>
          <span class="stats-bar-tag rose">{{ $t('testcase.automationNA') }} {{ statistics.automation?.cannot_automate || 0 }}</span>
          <span class="stats-bar-tag slate">{{ $t('testcase.automationPending') }} {{ statistics.automation?.not_automated || 0 }}</span>
        </div>
        <span class="stats-bar-sep">|</span>
        <div class="stats-bar-group clickable" @click="goToReview">
          <span class="stats-bar-tag amber">用例{{ $t('testcase.statusPendingReview') }} {{ statusStats.pending }}</span>
          <span class="stats-bar-tag rose">{{ $t('testcase.statusReviewRejected') }} {{ statusStats.rejected }}</span>
        </div>
      </div>
      
      <el-card class="table-card" shadow="never">
        <div class="table-header">
          <div class="header-left">
            <!-- 批量操作按钮（选中项时显示） -->
            <div v-if="selectedRows.length > 0" class="batch-actions">
              <span class="selected-count">{{ $t('testcase.selected') }}({{ selectedRows.length }})</span>
              <el-button 
                v-if="hasButton('testcases', 'batchEdit')"
                type="primary"
                size="default"
                @click="showBatchEditDialog"
              >
                {{ $t('common.edit') }}
              </el-button>
              <el-button 
                v-if="hasButton('testcases', 'batchExport')"
                size="default"
                @click="handleBatchExport"
              >
                {{ $t('common.export') }}
              </el-button>
              <el-button 
                size="default"
                @click="handleSelectAll"
              >
                {{ $t('testcase.selectAll') }}
              </el-button>
              <el-button 
                v-if="hasButton('testcases', 'createPlan')"
                size="default"
                @click="handleCreatePlan"
              >
                创建计划
              </el-button>
              <el-button 
                v-if="hasButton('testcases', 'batchDelete')"
                type="danger"
                size="default"
                @click="handleBatchDelete"
              >
                {{ $t('common.delete') }}
              </el-button>
            </div>
            
            <!-- 常规操作按钮 -->
            <template v-else>
              <div class="action-buttons">
                <el-button 
                  v-if="hasButton('testcases', 'create')"
                  type="primary"
                  :icon="Plus" 
                  @click="handleCreate"
                >
                  {{ $t('common.create') }}
                </el-button>
                <el-button
                  v-if="hasButton('testcases', 'create')"
                  type="primary"
                  :icon="List"
                  @click="handleBatchCreate"
                >
                  批量新建
                </el-button>
                <el-button 
                  v-if="hasButton('testcases', 'import')"
                  type="primary"
                  :icon="Download"
                  @click="showImportDialog"
                >
                  {{ $t('common.import') }}
                </el-button>
              </div>
            </template>
          </div>
          
          <!-- 统计显示按钮 -->
          <div class="header-stats">
            <el-button 
              type="primary"
              :icon="showStatistics ? Hide : View"
              @click="toggleStatistics"
              :title="showStatistics ? $t('common.hideStats') : $t('common.showStats')"
            >
              {{ $t('common.statistics') }}
            </el-button>
          </div>
          
          <div class="header-right">
            <!-- 列设置按钮 -->
            <el-popover
              v-model:visible="columnSettingsVisible"
              placement="bottom-end"
              :width="220"
              trigger="click"
            >
              <template #reference>
                <el-button 
                  :icon="Setting" 
                  circle
                  :title="$t('testcase.columnSettingsBtn')"
                  style="width: 32px; height: 32px;"
                />
              </template>
              <div class="column-settings">
                <div class="settings-title">{{ $t('testcase.columnSettings') }}</div>
                <div class="column-list">
                  <div 
                    v-for="(column, index) in columnOrder" 
                    :key="column.key"
                    class="column-item"
                    :class="{ dragging: draggedIndex === index }"
                    draggable="true"
                    @dragstart="handleDragStart(index)"
                    @dragover.prevent
                    @dragenter="handleDragEnter(index)"
                    @drop="handleDrop(index)"
                    @dragend="handleDragEnd"
                  >
                    <el-icon class="drag-handle"><Rank /></el-icon>
                    <el-checkbox 
                      :model-value="visibleColumns[column.key]"
                      @change="(val) => handleColumnVisibilityChange(column.key, val)"
                    >
                      {{ column.label }}
                    </el-checkbox>
                  </div>
                </div>
              </div>
            </el-popover>
            
            <!-- 用例类型筛选 -->
            <el-select 
              v-model="selectedCaseType" 
              :placeholder="$t('testcase.allTypes')" 
              clearable
              @change="handleCaseTypeChange"
              style="width: 140px;"
            >
              <el-option :label="$t('testcase.allTypes')" value="" />
              <el-option :label="$t('testcase.typeFunctional')" value="COMMON" />
              <el-option :label="$t('testcase.typePerformance')" value="PERFORMANCE" />
              <el-option :label="$t('testcase.typeSecurity')" value="SECURITY" />
              <el-option :label="$t('testcase.typeInterface')" value="INTERFACE" />
              <el-option :label="$t('testcase.typeInstall')" value="INSTALL" />
              <el-option :label="$t('testcase.typeConfig')" value="CONFIG" />
              <el-option :label="$t('testcase.typeCompatibility')" value="COMPATIBILITY" />
              <el-option :label="$t('testcase.typeOther')" value="OTHER" />
            </el-select>

            <!-- 用户反馈筛选 -->
            <el-select
              v-model="hasFeedbackFilter"
              placeholder="用户反馈"
              clearable
              @change="handleHasFeedbackChange"
              style="width: 140px;"
            >
              <el-option label="全部" :value="null" />
              <el-option label="有反馈" :value="true" />
              <el-option label="无反馈" :value="false" />
            </el-select>
            
            <el-input
              v-model="searchKeyword"
              :placeholder="regexMode ? '正则模式：支持 (?=.*A)(?=.*B) 同时包含多词，如 (?=.*卫星)(?=.*信号)' : $t('testcase.searchPlaceholder')"
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
            <el-tooltip :content="regexMode ? '当前：正则模式（点击切换为普通搜索）' : '当前：普通搜索（点击切换为正则模式）'" placement="top">
              <el-button
                :type="regexMode ? 'warning' : 'default'"
                @click="regexMode = !regexMode; searchKeyword && handleSearch()"
                style="margin-left: 6px; font-family: monospace; font-weight: bold;"
              >.*</el-button>
            </el-tooltip>
          </div>
        </div>
        
        <div class="table-wrapper">
          <div class="table-container" ref="tableContainerRef">
          <el-table 
            ref="tableRef"
            :data="tableData" 
            v-loading="loading"
            :class="{ 'hide-empty': loading || !dataReady }"
            style="width: 100%"
            :height="tableHeight"
            :header-cell-style="{ background: '#f8fafc', color: '#64748b', fontWeight: '500', fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.05em' }"
            :tooltip-options="{ placement: 'top', appendTo: 'body' }"
            @sort-change="handleSortChange"
            @selection-change="handleSelectionChange"
            @row-click="handleRowClick"
            row-key="id"
            :row-class-name="getRowClassName"
          >
            <!-- 拖拽列 -->
            <el-table-column 
                label="排序" 
              width="60" 
              align="center"
            >
              <template #default="scope">
                <div
                  class="drag-handle-wrapper"
                  draggable="true"
                  @dragstart="handleRowDragStart($event, scope.$index, scope.row)"
                  @dragend="handleRowDragEnd"
                >
                  <el-icon class="drag-handle">
                    <Rank />
                  </el-icon>
                </div>
              </template>
            </el-table-column>
            
            <!-- 多选列 -->
            <el-table-column 
              type="selection" 
              width="50" 
              align="center"
            />
            
            <!-- 动态渲染列 -->
            <template v-for="column in orderedVisibleColumns" :key="column.key">
              <!-- 用例编号 -->
              <el-table-column 
                v-if="column.key === 'case_number'"
                prop="case_number" 
                :label="$t('testcase.caseNumber')" 
                width="230" 
                align="center"
                resizable
                sortable="custom"
                :show-overflow-tooltip="{ showAfter: 500 }"
              >
                <template #default="scope">
                  <el-tooltip :content="scope.row.case_number" placement="top" :show-after="500">
                    <el-tag type="info" size="small" class="ellipsis-tag">{{ scope.row.case_number }}</el-tag>
                  </el-tooltip>
                </template>
              </el-table-column>
              
              <!-- 用例标题 -->
              <el-table-column 
                v-else-if="column.key === 'name'"
                prop="name" 
                :label="$t('testcase.name')" 
                min-width="200" 
                align="left"
                resizable
                sortable="custom"
                :show-overflow-tooltip="{ showAfter: 500 }"
              >
                <template #default="scope">
                  <div class="case-name clickable-title" @click="handleViewDetail(scope.row)">
                    <el-icon color="#6366f1"><Document /></el-icon>
                    <span class="ellipsis-text">{{ scope.row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              
              <!-- 前置条件 -->
              <el-table-column 
                v-else-if="column.key === 'precondition'"
                prop="precondition" 
                :label="$t('testcase.precondition')" 
                min-width="200" 
                align="left"
                resizable
                :show-overflow-tooltip="{ showAfter: 500 }"
              >
                <template #default="scope">
                  <div class="text-content single-line-ellipsis">{{ scope.row.precondition || '-' }}</div>
                </template>
              </el-table-column>
              
              <!-- 操作步骤 -->
              <el-table-column 
                v-else-if="column.key === 'steps'"
                prop="steps" 
                :label="$t('testcase.steps')" 
                min-width="250" 
                align="left"
                resizable
              >
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
                          <span style="color: #6366f1; font-weight: 500; min-width: 30px;">{{ stepIndex + 1 }}.</span>
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
              
              <!-- 预期结果 -->
              <el-table-column 
                v-else-if="column.key === 'expected_result'"
                prop="expected_result" 
                :label="$t('testcase.expectedResult')" 
                min-width="250" 
                align="left"
                resizable
              >
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
                          <span style="color: #6366f1; font-weight: 500; min-width: 30px;">{{ resultIndex + 1 }}.</span>
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
              
              <!-- 状态 -->
              <el-table-column 
                v-else-if="column.key === 'status'"
                prop="status" 
                :label="$t('common.status')" 
                width="160" 
                align="center"
                resizable
              >
                <template #header>
                  <div class="filter-header">
                    <span>{{ $t('common.status') }}</span>
                    <el-dropdown trigger="click" @command="handleStatusFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedStatus }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedStatus">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item command="REVIEWED" :active="selectedStatus === 'REVIEWED'">{{ $t('testcase.statusReviewed') }}</el-dropdown-item>
                          <el-dropdown-item command="PENDING" :active="selectedStatus === 'PENDING'">{{ $t('testcase.statusPendingReview') }}</el-dropdown-item>
                          <el-dropdown-item command="REJECTED" :active="selectedStatus === 'REJECTED'">{{ $t('testcase.statusReviewRejected') }}</el-dropdown-item>
                          <el-dropdown-item command="DEPRECATED" :active="selectedStatus === 'DEPRECATED'">{{ $t('testcase.statusDeprecated') }}</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  <el-tag v-if="scope.row.status === 'REVIEWED'" class="status-tag-demo status-reviewed" size="small">{{ $t('testcase.statusReviewed') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'PENDING'" class="status-tag-demo status-pending" size="small">{{ $t('testcase.statusPendingReview') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'REJECTED'" class="status-tag-demo status-rejected" size="small">{{ $t('testcase.statusReviewRejected') }}</el-tag>
                  <el-tag v-else-if="scope.row.status === 'DEPRECATED'" class="status-tag-demo status-deprecated" size="small">{{ $t('testcase.statusDeprecated') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              
              <!-- 用例等级 -->
              <el-table-column 
                v-else-if="column.key === 'level'"
                prop="level" 
                :label="$t('testcase.level')" 
                width="140" 
                align="center"
                resizable
              >
                <template #header>
                  <div class="filter-header">
                    <span>{{ $t('testcase.level') }}</span>
                    <el-dropdown trigger="click" @command="handleLevelFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedLevel }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedLevel">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item command="L1" :active="selectedLevel === 'L1'">L1</el-dropdown-item>
                          <el-dropdown-item command="L2" :active="selectedLevel === 'L2'">L2</el-dropdown-item>
                          <el-dropdown-item command="L3" :active="selectedLevel === 'L3'">L3</el-dropdown-item>
                          <el-dropdown-item command="L4" :active="selectedLevel === 'L4'">L4</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  <el-tag :class="['level-tag-demo', `level-${scope.row.level?.toLowerCase()}`]" size="small">
                    {{ scope.row.level }}
                  </el-tag>
                </template>
              </el-table-column>
              
              <!-- PR数量 -->
              <el-table-column 
                v-else-if="column.key === 'zmind_link_count'"
                prop="zmind_link_count" 
                width="160" 
                align="center"
                resizable
                sortable="custom"
              >
                <template #header>
                  <el-tooltip content="该字段展示：打开的PR数量/已关闭的PR数量" placement="top" :show-after="500">
                    <span>PR数量</span>
                  </el-tooltip>
                </template>
                <template #default="scope">
                  <span v-if="scope.row.zmind_link_count > 0" class="pr-count-clickable" @click.stop="handleLinkZmind(scope.row)">
                    <el-tag type="success" size="small" style="margin-right: 2px;">
                      {{ scope.row.zmind_link_open_count || 0 }}
                    </el-tag>
                    /
                    <el-tag type="info" size="small" style="margin-left: 2px;">
                      {{ scope.row.zmind_link_close_count || 0 }}
                    </el-tag>
                  </span>
                  <span v-else class="pr-count-clickable" @click.stop="handleLinkZmind(scope.row)">
                    <el-tag type="info" size="small">0</el-tag>
                  </span>
                </template>
              </el-table-column>
              
              <!-- 自动化 -->
              <el-table-column 
                v-else-if="column.key === 'automation'"
                prop="automation" 
                :label="$t('testcase.automation')" 
                width="180" 
                align="center"
                resizable
              >
                <template #header>
                  <div class="filter-header">
                    <span>{{ $t('testcase.automation') }}</span>
                    <el-dropdown trigger="click" @command="handleAutomationFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedAutomation }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedAutomation">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item command="D" :active="selectedAutomation === 'D'">{{ $t('testcase.automationD') }}</el-dropdown-item>
                          <el-dropdown-item command="Y" :active="selectedAutomation === 'Y'">{{ $t('testcase.automationY') }}</el-dropdown-item>
                          <el-dropdown-item command="null" :active="selectedAutomation === 'null'">{{ $t('testcase.automationPending') }}</el-dropdown-item>
                          <el-dropdown-item command="N" :active="selectedAutomation === 'N'">{{ $t('common.no') }} - All</el-dropdown-item>
                          <el-dropdown-item command="N-HW_PHYSICAL" :active="selectedAutomation === 'N-HW_PHYSICAL'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNHwPhysical') }}
                            <el-tooltip :content="$t('testcase.automationNHwPhysicalTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-VISUAL_JUDGE" :active="selectedAutomation === 'N-VISUAL_JUDGE'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNVisualJudge') }}
                            <el-tooltip :content="$t('testcase.automationNVisualJudgeTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-BOOT_PROCESS" :active="selectedAutomation === 'N-BOOT_PROCESS'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNBootProcess') }}
                            <el-tooltip :content="$t('testcase.automationNBootProcessTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-MEDIA_PLAY" :active="selectedAutomation === 'N-MEDIA_PLAY'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNMediaPlay') }}
                            <el-tooltip :content="$t('testcase.automationNMediaPlayTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-OTA_UPGRADE" :active="selectedAutomation === 'N-OTA_UPGRADE'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNOtaUpgrade') }}
                            <el-tooltip :content="$t('testcase.automationNOtaUpgradeTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-DATA_CONFIG" :active="selectedAutomation === 'N-DATA_CONFIG'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNDataConfig') }}
                            <el-tooltip :content="$t('testcase.automationNDataConfigTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-LOG_CHECK" :active="selectedAutomation === 'N-LOG_CHECK'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNLogCheck') }}
                            <el-tooltip :content="$t('testcase.automationNLogCheckTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-BACKEND_CONFIG" :active="selectedAutomation === 'N-BACKEND_CONFIG'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNBackendConfig') }}
                            <el-tooltip :content="$t('testcase.automationNBackendConfigTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-DATA_DYNAMIC" :active="selectedAutomation === 'N-DATA_DYNAMIC'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNDataDynamic') }}
                            <el-tooltip :content="$t('testcase.automationNDataDynamicTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                          <el-dropdown-item command="N-OTHER_SPECIAL" :active="selectedAutomation === 'N-OTHER_SPECIAL'">
                            {{ $t('common.no') }} - {{ $t('testcase.automationNSpecial') }}
                            <el-tooltip :content="$t('testcase.automationNSpecialTip')" placement="right" :show-after="500">
                              <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                            </el-tooltip>
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  <el-tag v-if="scope.row.automation === 'Y'" type="success" size="small">{{ $t('testcase.automationY') }}</el-tag>
                  <el-tag v-else-if="scope.row.automation === 'D'" type="success" size="small">{{ $t('testcase.automationD') }}</el-tag>
                  <el-tag v-else-if="scope.row.automation && scope.row.automation.startsWith('N-')" type="info" size="small">
                    {{ getAutomationDisplay(scope.row.automation) }}
                  </el-tag>
                  <el-tag v-else-if="scope.row.automation === 'N'" type="info" size="small">{{ $t('testcase.automationN') }}</el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              
              <!-- 标签 -->
              <el-table-column 
                v-else-if="column.key === 'tags'"
                prop="tags" 
                :label="$t('testcase.tags')" 
                min-width="150" 
                align="center"
                resizable
              >
                <template #header>
                  <div class="filter-header">
                    <span>{{ $t('testcase.tags') }}</span>
                    <el-dropdown trigger="click" @command="handleTagFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedTag }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedTag">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item 
                            v-for="tag in tagList" 
                            :key="tag"
                            :command="tag"
                            :active="selectedTag === tag"
                          >
                            {{ tag }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  <div v-if="scope.row.tags" class="tags-container">
                    <el-tag 
                      v-for="(tag, index) in parseTags(scope.row.tags)" 
                      :key="index"
                      size="small"
                      style="margin: 2px;"
                    >
                      {{ tag }}
                    </el-tag>
                  </div>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              
              <!-- 归档来源 -->
              <el-table-column 
                v-else-if="column.key === 'archive_source'"
                prop="archive_source" 
                label="归档来源" 
                min-width="150" 
                align="center"
                resizable
              >
                <template #header>
                  <div class="filter-header">
                    <span>归档来源</span>
                    <el-dropdown trigger="click" @command="handleArchiveSourceFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedArchiveSource }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedArchiveSource">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item 
                            v-for="source in archiveSourceList" 
                            :key="source"
                            :command="source"
                            :active="selectedArchiveSource === source"
                          >
                            {{ source }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  <span v-if="scope.row.archive_source">{{ scope.row.archive_source }}</span>
                  <span v-else>-</span>
                </template>
              </el-table-column>
              
              <!-- 备注 -->
              <el-table-column 
                v-else-if="column.key === 'remarks'"
                prop="remarks" 
                :label="$t('testcase.remarks')" 
                min-width="150" 
                align="left"
                resizable
                :show-overflow-tooltip="{ showAfter: 500 }"
              >
                <template #default="scope">
                  <div class="text-content single-line-ellipsis">{{ scope.row.remarks || '-' }}</div>
                </template>
              </el-table-column>
              
              <!-- 创建人 -->
              <el-table-column 
                v-else-if="column.key === 'creator_name'"
                prop="creator_name" 
                :label="$t('testcase.creator')" 
                width="120" 
                align="center"
                resizable
                :show-overflow-tooltip="{ showAfter: 500 }"
              >
                <template #header>
                  <div class="filter-header">
                    <span>{{ $t('testcase.creator') }}</span>
                    <el-dropdown trigger="click" @command="handleCreatorFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedCreator }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedCreator">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item 
                            v-for="creator in creatorList" 
                            :key="creator"
                            :command="creator"
                            :active="selectedCreator === creator"
                          >
                            {{ creator }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  {{ scope.row.creator_name }}
                </template>
              </el-table-column>
              
              <!-- 更新人 -->
              <el-table-column 
                v-else-if="column.key === 'updater_name'"
                prop="updater_name" 
                :label="$t('testcase.updater')" 
                width="120" 
                align="center"
                resizable
                :show-overflow-tooltip="{ showAfter: 500 }"
              >
                <template #header>
                  <div class="filter-header">
                    <span>{{ $t('testcase.updater') }}</span>
                    <el-dropdown trigger="click" @command="handleUpdaterFilter">
                      <el-icon class="filter-icon" :class="{ active: selectedUpdater }"><Filter /></el-icon>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item :command="''" :active="!selectedUpdater">{{ $t('common.all') }}</el-dropdown-item>
                          <el-dropdown-item 
                            v-for="updater in updaterList" 
                            :key="updater"
                            :command="updater"
                            :active="selectedUpdater === updater"
                          >
                            {{ updater }}
                          </el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </template>
                <template #default="scope">
                  {{ scope.row.updater_name }}
                </template>
              </el-table-column>
              
              <!-- 创建时间 -->
              <el-table-column 
                v-else-if="column.key === 'created_at'"
                prop="created_at" 
                :label="$t('common.createdAt')" 
                width="160" 
                align="center"
                resizable
                sortable="custom"
              >
                <template #default="scope">
                  <span>{{ formatDateTime(scope.row.created_at) }}</span>
                </template>
              </el-table-column>
              
              <!-- 更新时间 -->
              <el-table-column 
                v-else-if="column.key === 'updated_at'"
                prop="updated_at" 
                :label="$t('common.updatedAt')" 
                width="160" 
                align="center"
                resizable
                sortable="custom"
              >
                <template #default="scope">
                  <span>{{ formatDateTime(scope.row.updated_at) }}</span>
                </template>
              </el-table-column>
            </template>
            
            <!-- 操作列（固定在最后） -->
            <el-table-column 
              v-if="visibleColumns.operations"
              :label="$t('common.operation')" 
              width="240" 
              align="center"
              fixed="right"
            >
              <template #default="scope">
                <div class="operation-buttons">
                  <el-button 
                    type="primary" 
                    size="small" 
                    :icon="Link"
                    link
                    @click="handleLinkZmind(scope.row)"
                  >
                    PR
                  </el-button>
                  <el-button 
                    v-if="hasButton('testcases', 'edit')"
                    type="primary" 
                    size="small" 
                    :icon="Edit"
                    link
                    @click="handleEdit(scope.row)"
                  >
                    {{ $t('common.edit') }}
                  </el-button>
                  <el-dropdown v-if="hasButton('testcases', 'delete') || hasButton('testcases', 'copy')" trigger="hover" @command="(cmd) => handleDropdownCommand(cmd, scope.row)">
                    <el-button 
                      type="info" 
                      size="small" 
                      link
                      :icon="MoreFilled"
                    />
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item 
                          v-if="hasButton('testcases', 'copy')"
                          command="copy"
                        >
                          <el-icon><CopyDocument /></el-icon>
                          <span>复制</span>
                        </el-dropdown-item>
                        <el-dropdown-item 
                          v-if="hasButton('testcases', 'delete')"
                          command="delete"
                        >
                          <el-icon><Delete /></el-icon>
                          <span>{{ $t('common.delete') }}</span>
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
      </el-card>
    </div>

    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogTitle" 
      width="900px"
      :close-on-click-modal="false"
      @closed="handleDialogClosed"
    >
      <el-form :model="form" label-width="130px" label-position="left">
        <!-- 新建时显示用例库选择，用例编号由系统自动生成 -->
        <el-row :gutter="20" v-if="!form.id">
          <el-col :span="12">
            <el-form-item :label="$t('testcase.caseLibrary')" required>
              <el-select 
                v-model="form.primary_project_id" 
                :placeholder="$t('testcase.selectProject')"
                style="width: 100%"
                filterable
                @change="handleFormProjectChange"
              >
                <el-option
                  v-for="project in teamProjectList"
                  :key="project.id"
                  :label="project.name"
                  :value="project.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('testcase.type')" required>
              <el-select 
                v-model="form.case_type" 
                :placeholder="$t('testcase.allTypes')" 
                style="width: 100%"
                popper-class="module-select-dropdown"
                :fit-input-width="true"
              >
                <el-option :label="$t('testcase.typeFunctional')" value="COMMON" />
                <el-option :label="$t('testcase.typePerformance')" value="PERFORMANCE" />
                <el-option :label="$t('testcase.typeSecurity')" value="SECURITY" />
                <el-option :label="$t('testcase.typeInterface')" value="INTERFACE" />
                <el-option :label="$t('testcase.typeInstall')" value="INSTALL" />
                <el-option :label="$t('testcase.typeConfig')" value="CONFIG" />
                <el-option :label="$t('testcase.typeCompatibility')" value="COMPATIBILITY" />
                <el-option :label="$t('testcase.typeOther')" value="OTHER" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <!-- 新建时显示第二行：所属模块 -->
        <el-row :gutter="20" v-if="!form.id">
          <el-col :span="12">
            <el-form-item :label="$t('testcase.moduleBelongs')" required>
              <el-tree-select
                v-model="form.module"
                :data="formModuleTree"
                :props="{ label: 'label', value: 'value', children: 'children' }"
                :placeholder="$t('testcase.selectProject')"
                filterable
                :filter-node-method="filterModuleNode"
                check-strictly
                :render-after-expand="false"
                style="width: 100%"
                :disabled="!formProjectId"
                popper-class="module-tree-select-dropdown"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12" />
        </el-row>
        <!-- 编辑时显示：第一行 用例库+所属模块，第二行 用例编号+类型 -->
        <!-- 复制时显示：第一行 用例库+类型，第二行 所属模块 -->
        <template v-else>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="$t('testcase.caseLibrary')" required>
                <el-select 
                  v-model="form.primary_project_id" 
                  :placeholder="$t('testcase.selectProject')"
                  style="width: 100%"
                  filterable
                  @change="handleFormProjectChange"
                >
                  <el-option
                    v-for="project in teamProjectList"
                    :key="project.id"
                    :label="project.name"
                    :value="project.id"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <!-- 复制模式：右侧显示功能类型 -->
              <el-form-item v-if="isCopyMode" :label="$t('testcase.type')" required>
                <el-select 
                  v-model="form.case_type" 
                  :placeholder="$t('testcase.allTypes')" 
                  style="width: 100%"
                  popper-class="module-select-dropdown"
                  :fit-input-width="true"
                >
                  <el-option :label="$t('testcase.typeFunctional')" value="COMMON" />
                  <el-option :label="$t('testcase.typePerformance')" value="PERFORMANCE" />
                  <el-option :label="$t('testcase.typeSecurity')" value="SECURITY" />
                  <el-option :label="$t('testcase.typeInterface')" value="INTERFACE" />
                  <el-option :label="$t('testcase.typeInstall')" value="INSTALL" />
                  <el-option :label="$t('testcase.typeConfig')" value="CONFIG" />
                  <el-option :label="$t('testcase.typeCompatibility')" value="COMPATIBILITY" />
                  <el-option :label="$t('testcase.typeOther')" value="OTHER" />
                </el-select>
              </el-form-item>
              <!-- 普通编辑模式：右侧显示所属模块 -->
              <el-form-item v-else :label="$t('testcase.moduleBelongs')" required>
                <el-tree-select
                  v-model="form.module"
                  :data="formModuleTree"
                  :props="{ label: 'label', value: 'value', children: 'children' }"
                  :placeholder="$t('testcase.selectProject')"
                  filterable
                  :filter-node-method="filterModuleNode"
                  check-strictly
                  :render-after-expand="false"
                  style="width: 100%"
                  :disabled="!formProjectId"
                  popper-class="module-tree-select-dropdown"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <!-- 复制模式：第二行左侧显示所属模块 -->
            <el-col v-if="isCopyMode" :span="12">
              <el-form-item :label="$t('testcase.moduleBelongs')" required>
                <el-tree-select
                  v-model="form.module"
                  :data="formModuleTree"
                  :props="{ label: 'label', value: 'value', children: 'children' }"
                  :placeholder="$t('testcase.selectProject')"
                  filterable
                  :filter-node-method="filterModuleNode"
                  check-strictly
                  :render-after-expand="false"
                  style="width: 100%"
                  :disabled="!formProjectId"
                  popper-class="module-tree-select-dropdown"
                />
              </el-form-item>
            </el-col>
            <!-- 普通编辑模式：第二行左侧显示用例编号 -->
            <el-col v-else :span="12">
              <el-form-item :label="$t('testcase.caseNumber')">
                <el-input 
                  v-model="form.case_number" 
                  :placeholder="$t('testcase.inputModule')"
                  :disabled="true"
                />
              </el-form-item>
            </el-col>
            <!-- 普通编辑模式：第二行右侧显示功能类型 -->
            <el-col v-if="!isCopyMode" :span="12">
              <el-form-item :label="$t('testcase.type')" required>
                <el-select 
                  v-model="form.case_type" 
                  :placeholder="$t('testcase.allTypes')" 
                  style="width: 100%"
                  popper-class="module-select-dropdown"
                  :fit-input-width="true"
                >
                  <el-option :label="$t('testcase.typeFunctional')" value="COMMON" />
                  <el-option :label="$t('testcase.typePerformance')" value="PERFORMANCE" />
                  <el-option :label="$t('testcase.typeSecurity')" value="SECURITY" />
                  <el-option :label="$t('testcase.typeInterface')" value="INTERFACE" />
                  <el-option :label="$t('testcase.typeInstall')" value="INSTALL" />
                  <el-option :label="$t('testcase.typeConfig')" value="CONFIG" />
                  <el-option :label="$t('testcase.typeCompatibility')" value="COMPATIBILITY" />
                  <el-option :label="$t('testcase.typeOther')" value="OTHER" />
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
        
        <el-form-item :label="$t('testcase.name')" required>
          <el-input 
            v-model="form.name" 
            :placeholder="$t('testcase.inputName')"
            :prefix-icon="Document"
          />
        </el-form-item>
        
        <el-form-item :label="$t('testcase.precondition')">
          <el-input 
            v-model="form.precondition" 
            type="textarea" 
            :rows="2"
            :placeholder="$t('testcase.inputPrecondition')"
          />
        </el-form-item>
        
        <el-form-item :label="$t('testcase.steps')" required>
          <StepEditor v-model="form.steps" />
        </el-form-item>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('testcase.level')" required>
              <el-select v-model="form.level" :placeholder="$t('testcase.selectLevel')" style="width: 100%;">
                <el-option :label="'L1 - ' + $t('testcase.levelHighest')" value="L1">
                  <el-tag type="danger" size="small">L1</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.levelHighest') }}</span>
                </el-option>
                <el-option :label="'L2 - ' + $t('testcase.levelHigh')" value="L2">
                  <el-tag type="warning" size="small">L2</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.levelHigh') }}</span>
                </el-option>
                <el-option :label="'L3 - ' + $t('testcase.levelMedium')" value="L3">
                  <el-tag type="primary" size="small">L3</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.levelMedium') }}</span>
                </el-option>
                <el-option :label="'L4 - ' + $t('testcase.levelLow')" value="L4">
                  <el-tag type="info" size="small">L4</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.levelLow') }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('testcase.automation')">
              <el-select v-model="form.automation" :placeholder="$t('testcase.selectAutomation')" clearable style="width: 100%;">
                <el-option :label="$t('testcase.automationY')" value="Y">
                  <el-tag type="success" size="small">Y</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationY') }}</span>
                </el-option>
                <el-option :label="$t('testcase.automationD')" value="D">
                  <el-tag type="success" size="small">D</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationD') }}</span>
                </el-option>
                <el-option :label="$t('testcase.automationNHwPhysical')" value="N-HW_PHYSICAL">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNHwPhysical') }}</span>
                  <el-tooltip :content="$t('testcase.automationNHwPhysicalTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNVisualJudge')" value="N-VISUAL_JUDGE">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNVisualJudge') }}</span>
                  <el-tooltip :content="$t('testcase.automationNVisualJudgeTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNBootProcess')" value="N-BOOT_PROCESS">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNBootProcess') }}</span>
                  <el-tooltip :content="$t('testcase.automationNBootProcessTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNMediaPlay')" value="N-MEDIA_PLAY">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNMediaPlay') }}</span>
                  <el-tooltip :content="$t('testcase.automationNMediaPlayTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNOtaUpgrade')" value="N-OTA_UPGRADE">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNOtaUpgrade') }}</span>
                  <el-tooltip :content="$t('testcase.automationNOtaUpgradeTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNDataConfig')" value="N-DATA_CONFIG">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNDataConfig') }}</span>
                  <el-tooltip :content="$t('testcase.automationNDataConfigTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNLogCheck')" value="N-LOG_CHECK">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNLogCheck') }}</span>
                  <el-tooltip :content="$t('testcase.automationNLogCheckTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNBackendConfig')" value="N-BACKEND_CONFIG">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNBackendConfig') }}</span>
                  <el-tooltip :content="$t('testcase.automationNBackendConfigTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNDataDynamic')" value="N-DATA_DYNAMIC">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNDataDynamic') }}</span>
                  <el-tooltip :content="$t('testcase.automationNDataDynamicTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
                <el-option :label="$t('testcase.automationNSpecial')" value="N-OTHER_SPECIAL">
                  <el-tag type="info" size="small">N</el-tag>
                  <span style="margin-left: 8px;">{{ $t('testcase.automationNSpecial') }}</span>
                  <el-tooltip :content="$t('testcase.automationNSpecialTip')" placement="top" :show-after="500">
                    <el-icon style="margin-left: 4px; cursor: pointer; color: #909399;"><QuestionFilled /></el-icon>
                  </el-tooltip>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item :label="$t('testcase.tags')">
          <el-input 
            v-model="form.tags" 
            :placeholder="$t('testcase.tagsPlaceholder') || '多个标签用逗号分隔'"
          />
        </el-form-item>
        
        <el-form-item label="归档来源">
          <el-input 
            v-model="form.archive_source" 
            placeholder="请输入归档来源"
          />
        </el-form-item>
        
        <el-form-item :label="$t('testcase.remarks')">
          <el-input 
            v-model="form.remarks" 
            type="textarea" 
            :rows="2"
            :placeholder="$t('testcase.inputRemarks')"
          />
        </el-form-item>

        
        <!-- 附件部分 -->
        <el-form-item :label="$t('testcase.linkDialog.operation')">
          <!-- 创建模式：临时附件上传 -->
          <div v-if="!form.id" class="attachments-section">
            <el-upload
              ref="uploadRef"
              :auto-upload="false"
              :on-change="handleTempFileChange"
              :on-remove="handleTempFileRemove"
              multiple
              :show-file-list="true"
              :file-list="tempAttachments"
            >
              <div style="display: flex; align-items: center; gap: 12px;">
                <el-button type="primary" size="small" :icon="Download">
                  {{ $t('common.import') }}
                </el-button>
                <span style="color: #909399; font-size: 12px;">{{ $t('testcase.uploadTip') }}</span>
              </div>
            </el-upload>
          </div>
          
          <!-- 编辑模式附件上传 -->
          <div v-else class="attachments-section">
            <el-upload
              class="attachment-dragger"
              drag
              :action="`/api/testcase-attachments/${form.id}/attachments`"
              :headers="uploadHeaders"
              :on-success="handleAttachmentSuccess"
              :on-error="handleAttachmentError"
              :before-upload="beforeAttachmentUpload"
              multiple
              :show-file-list="false"
              :disabled="uploadingFile"
            >
              <div class="attachment-drop-area">
                <el-icon :size="28" color="#c0c4cc"><Upload /></el-icon>
                <div class="attachment-drop-text">
                  <span>拖拽文件到此处，或</span>
                  <el-button type="primary" link size="small" :loading="uploadingFile" style="padding: 0 4px; font-size: 13px;">点击上传</el-button>
                </div>
                <div class="attachment-drop-tip">{{ $t('testcase.uploadTip') }}</div>
              </div>
            </el-upload>

            <!-- 附件列表 -->
            <div v-if="attachments.length > 0" class="attachment-file-list">
              <div
                v-for="att in attachments"
                :key="att.id"
                class="attachment-file-item"
              >
                <div class="attachment-file-info">
                  <el-icon :size="18" :color="getFileIconColor(att.file_name)"><Document /></el-icon>
                  <div class="attachment-file-meta">
                    <span class="attachment-file-name" :title="att.file_name">{{ att.file_name }}</span>
                    <span class="attachment-file-size">{{ formatFileSize(att.file_size) }} · {{ formatDateTime(att.upload_time) }}</span>
                  </div>
                </div>
                <div class="attachment-file-actions">
                  <el-button
                    v-if="isPreviewable(att.file_name)"
                    type="primary"
                    size="small"
                    link
                    @click="handlePreviewAttachment(att)"
                  >预览</el-button>
                  <el-button
                    type="primary"
                    size="small"
                    link
                    @click="handleDownloadAttachment(att)"
                  >下载</el-button>
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="handleDeleteAttachment(att)"
                  >删除</el-button>
                </div>
              </div>
            </div>

            <el-empty
              v-else
              :description="$t('testcase.noAttachment')"
              :image-size="50"
              style="padding: 12px 0;"
            />
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

    <BatchCreateDialog
      v-model="batchCreateVisible"
      :project-list="teamProjectList"
      @success="handleBatchCreateSuccess"
      @closed="handleBatchCreateClose"
    />

    <!-- 导入对话框 -->
    <el-dialog 
      v-model="importDialogVisible" 
      :title="$t('testcase.importExcel')" 
      width="650px"
      :close-on-click-modal="false"
      :close-on-press-escape="!importing"
      :show-close="!importing"
      @closed="handleImportDialogClosed"
    >
      <div class="import-dialog-content">
        <el-alert
          :title="$t('testcase.importTemplateNote')"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          <template #default>
            <div style="margin-bottom: 10px; line-height: 1.8;">
              <p>• 模板第一列为"所属用例库"，请填写系统中已存在的用例库名称</p>
              <p>• 模块列格式为"模块/子模块"，必须是系统中已创建的模块</p>
              <p>• 请确保用例库和模块已在系统中创建，并设置好Tag</p>
              <p>• 模板中包含当前项目组下所有用例库和模块的参考信息</p>
            </div>
            <el-button 
              type="success" 
              size="small" 
              :icon="Download"
              link
              @click="downloadTemplate"
              :disabled="importing"
            >
              下载 Excel 模板
            </el-button>
          </template>
          </el-alert>

        <!-- 自动创建模块选项 -->
        <el-checkbox 
          v-if="hasButton('testcases', 'importAutoCreate')"
          v-model="importAutoCreateModule"
          :disabled="importing"
          style="margin: 15px 0;"
        >
          自动创建模块（模块不存在时自动创建，并生成4位字母Tag）
        </el-checkbox>

        <el-upload
          ref="importUploadRef"
          :auto-upload="false"
          :on-change="handleImportFileChange"
          :on-remove="handleImportFileRemove"
          :limit="1"
          accept=".xlsx,.xls,.csv"
          drag
          :disabled="importing"
        >
          <el-icon class="el-icon--upload"><Upload /></el-icon>
          <div class="el-upload__text">
            拖拽或点击此区域选择文件
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 xls/xlsx/csv，单个文件不超过 100M
            </div>
          </template>
        </el-upload>

        <!-- 上传进度 -->
        <div v-if="importing" style="margin-top: 20px;">
          <el-progress 
            :percentage="importProgress" 
            :status="importStatus === '' && importProgress === 100 ? 'success' : undefined"
            :striped="importStatus === 'committing'"
            :striped-flow="importStatus === 'committing'"
          />
          <div v-if="importStatus === 'uploading'" style="margin-top: 8px; font-size: 12px; color: #909399;">
            正在上传文件... {{ importProgress }}%
          </div>
          <div v-else-if="importStatus === 'parsing'" style="margin-top: 8px; font-size: 12px; color: #E6A23C;">
            <el-icon class="is-loading" style="vertical-align: middle; margin-right: 4px;"><Loading /></el-icon>
            {{ importStatusText }}
          </div>
          <div v-else-if="importStatus === 'importing'" style="margin-top: 8px; font-size: 12px; color: #409EFF;">
            <el-icon class="is-loading" style="vertical-align: middle; margin-right: 4px;"><Loading /></el-icon>
            {{ importStatusText }}
            <span v-if="importStats.total > 0" style="margin-left: 8px; color: #67C23A;">
              新建 {{ importStats.created }} | 更新 {{ importStats.updated }} | 跳过 {{ importStats.skipped }}
            </span>
          </div>
          <div v-else-if="importStatus === 'committing'" style="margin-top: 8px; font-size: 12px; color: #E6A23C;">
            <el-icon class="is-loading" style="vertical-align: middle; margin-right: 4px;"><Loading /></el-icon>
            {{ importStatusText }}
          </div>
        </div>

        <!-- 导入错误提示 -->
        <div v-if="importErrors.length > 0" class="import-errors" style="margin-top: 15px;">
          <el-alert
            :title="$t('testcase.importTip')"
            type="warning"
            :closable="false"
          >
            <template #default>
              <div style="max-height: 150px; overflow-y: auto;">
                <p v-for="(error, index) in importErrors.slice(0, 10)" :key="index" style="margin: 5px 0; font-size: 12px;">
                  {{ error }}
                </p>
                <p v-if="importErrors.length > 10" style="color: #909399; font-size: 12px;">
                  ... 还有 {{ importErrors.length - 10 }} 条提示
                </p>
              </div>
            </template>
          </el-alert>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="importDialogVisible = false" :disabled="importing">{{ $t('common.cancel') }}</el-button>
        <el-button 
          type="primary" 
          @click="handleImportSubmit" 
          :loading="importing"
          :disabled="!importFile"
        >
          开始导入
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量删除进度对话框 -->
    <el-dialog 
      v-model="batchDeleteDialogVisible" 
      title="批量删除进度" 
      width="500px"
      :close-on-click-modal="false"
      :close-on-press-escape="!batchDeleting"
      :show-close="!batchDeleting"
    >
      <div class="batch-delete-progress">
        <el-progress 
          :percentage="deleteProgress" 
          :status="deleteProgress === 100 ? 'success' : undefined"
          :striped="batchDeleting"
          :striped-flow="batchDeleting"
        />
        <div style="margin-top: 12px; font-size: 14px; color: #409EFF; text-align: center;">
          <el-icon class="is-loading" style="vertical-align: middle; margin-right: 4px;" v-if="batchDeleting"><Loading /></el-icon>
          {{ deleteStatusText || (batchDeleting ? '正在删除...' : '删除完成') }}
        </div>
      </div>
    </el-dialog>

    <!-- 关联PR对话框 -->
    <el-dialog 
      v-model="linkDialogVisible" 
      :title="$t('testcase.linkDialog.title')" 
      width="1000px"
      :close-on-click-modal="false"
      v-loading="refreshingPRLinks"
      :element-loading-text="$t('testcase.linkDialog.refreshingPR')"
      @closed="handleDialogClosed"
    >
      <div class="link-dialog-content">
        <!-- 已关联的PR列表 -->
        <div class="linked-section">
          <div style="display: flex; align-items: center; justify-content: space-between;">
            <h3>{{ $t('testcase.linkDialog.linkedSection') }} ({{ zmindLinks.length }})</h3>
            <el-tooltip :content="$t('testcase.linkDialog.refreshPRTooltip')" placement="bottom" effect="light" :show-after="500">
              <el-button
                type="primary"
                size="small"
                :loading="refreshingPRLinks"
                :disabled="refreshingPRLinks"
                @click="handleRefreshPRLinks"
              >
                <el-icon v-if="!refreshingPRLinks"><Refresh /></el-icon>
                {{ refreshingPRLinks ? $t('testcase.linkDialog.refreshingPR') : $t('testcase.linkDialog.refreshPR') }}
              </el-button>
            </el-tooltip>
          </div>
          <el-table 
            :data="filteredZmindLinks" 
            style="width: 100%; margin-top: 12px;" 
            :cell-style="{ 'vertical-align': 'middle' }"
            :header-cell-style="{ 'vertical-align': 'middle' }"
            :empty-text="zmindLinks.length > 0 ? $t('testcase.filteredNoData') : $t('testcase.noLinkedPR')"
            border
            stripe
          >
            <el-table-column :label="$t('testcase.linkDialog.prId')" width="100" align="left">
              <template #default="scope">
                <a 
                  :href="`https://zmind.whaletv.com/issues/${scope.row.zmind_issue_id}`" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  style="color: #409EFF; text-decoration: underline;"
                >
                  {{ scope.row.zmind_issue_id }}
                </a>
              </template>
            </el-table-column>
            <el-table-column prop="zmind_issue_subject" :label="$t('testcase.linkDialog.prTitle')" min-width="200" align="left">
              <template #default="scope">
                <el-tooltip :content="scope.row.zmind_issue_subject" placement="top" :disabled="!scope.row.zmind_issue_subject" :show-after="500">
                  <div style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    {{ scope.row.zmind_issue_subject || '-' }}
                  </div>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column prop="zmind_issue_severity" :label="$t('testcase.linkDialog.prSeverity')" width="120" align="center">
              <template #default="scope">
                {{ scope.row.zmind_issue_severity || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="zmind_issue_status" :label="$t('testcase.linkDialog.prStatus')" width="120" align="center">
              <template #default="scope">
                {{ scope.row.zmind_issue_status || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="created_by_name" :label="$t('testcase.creator')" width="100" align="center">
              <template #default="scope">
                {{ scope.row.created_by_name || '-' }}
              </template>
            </el-table-column>
            <el-table-column :label="$t('testcase.linkDialog.operation')" width="100" align="center">
              <template #default="scope">
                <el-button 
                  type="danger" 
                  size="small" 
                  link
                  @click="handleRemoveLink(scope.row)"
                >
                  {{ $t('testcase.linkDialog.removeLink') }}
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <el-divider />

        <!-- 添加PR表单 -->
        <div class="add-section">
          <h3>{{ $t('testcase.linkDialog.addSection') }}</h3>
          <el-form :model="addLinkForm" label-width="100px" style="margin-top: 16px;">
            <el-form-item :label="$t('testcase.linkDialog.prId')" required>
              <el-input 
                v-model="addLinkForm.zmind_issue_id" 
                :placeholder="$t('testcase.linkDialog.inputPrId')"
                style="width: 100%;"
                @keyup.enter="handleFetchPRInfo"
              />
              <div v-if="addLinkForm.zmind_issue_subject" style="margin-top: 8px; padding: 12px; background-color: #f5f7fa; border-radius: 4px;">
                <div style="margin-bottom: 6px;"><strong>{{ $t('testcase.prSubject') }}：</strong>{{ addLinkForm.zmind_issue_subject }}</div>
                <div v-if="addLinkForm.zmind_issue_status" style="margin-bottom: 6px;"><strong>{{ $t('testcase.prStatus') }}：</strong>{{ addLinkForm.zmind_issue_status }}</div>
                <div v-if="addLinkForm.zmind_issue_severity"><strong>{{ $t('testcase.prSeverity') }}：</strong>{{ addLinkForm.zmind_issue_severity }}</div>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleFetchPRInfo"
                :loading="fetchingPRInfo"
                :disabled="!addLinkForm.zmind_issue_id"
              >
                查询PR
              </el-button>
              <el-button 
                v-if="addLinkForm.zmind_issue_subject"
                type="success" 
                @click="handleAddLink"
              >
                添加关联
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="linkDialogVisible = false">{{ $t('testcase.linkDialog.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 用例详情对话框 -->
    <el-dialog 
      v-model="detailDialogVisible" 
      :title="$t('testcase.editCase')" 
      width="1000px"
      top="5vh"
      :close-on-click-modal="false"
      class="detail-fixed-dialog"
    >
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between; padding-right: 20px;">
          <span style="font-size: 16px; font-weight: 600;">{{ $t('testcase.editCase') }}</span>
          <div style="display: flex; align-items: center; gap: 8px;">
            <el-button :disabled="currentDetailIndex <= 0" size="small" @click="handlePrevDetail">
              <el-icon><ArrowLeft /></el-icon>
              上一条
            </el-button>
            <span style="font-size: 12px; color: #909399;">{{ currentDetailIndex + 1 }} / {{ tableData.length }}</span>
            <el-button :disabled="currentDetailIndex >= tableData.length - 1" size="small" @click="handleNextDetail">
              下一条
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </template>
      <div v-if="detailData" style="position: relative;">
        <el-button
          v-if="detailData.feedback"
          type="warning"
          size="small"
          style="position: absolute; right: 0; top: 4px; z-index: 10;"
          @click="feedbackViewDialogVisible = true"
        >
          存在问题反馈
        </el-button>
      </div>
      <el-tabs v-if="detailData" v-model="activeTabName">
        <!-- 基本信息标签页 -->
        <el-tab-pane :label="$t('profile.basicInfo')" name="basic">
          <div class="detail-content">
            <el-descriptions :column="2" border>
              <el-descriptions-item :label="$t('testcase.caseNumber')">
                <el-tag type="info" size="small">{{ detailData.case_number }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.type')">
                <el-tag :type="getCaseTypeColor(detailData.case_type)" size="small">
                  {{ getCaseTypeName(detailData.case_type) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.moduleBelongs')">
                {{ detailData.module || '-' }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.name')" :span="2">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <el-icon color="#6366f1"><Document /></el-icon>
                  <span style="font-weight: 500;">{{ detailData.name }}</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.precondition')" :span="2">
                <div class="detail-section">{{ detailData.precondition || '-' }}</div>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.steps')" :span="2">
                <div class="detail-section">
                  <div 
                    v-for="(step, stepIndex) in parseSteps(detailData.steps)" 
                    :key="`detail-step-${stepIndex}`"
                    class="detail-step-item"
                  >
                    <span class="step-number">{{ stepIndex + 1 }}.</span>
                    <span class="step-text">{{ step }}</span>
                  </div>
                </div>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.expectedResult')" :span="2">
                <div class="detail-section">
                  <div 
                    v-for="(result, resultIndex) in parseExpected(detailData.expected_result)" 
                    :key="`detail-result-${resultIndex}`"
                    class="detail-step-item"
                  >
                    <span class="step-number">{{ resultIndex + 1 }}.</span>
                    <span class="step-text">{{ result }}</span>
                  </div>
                </div>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.level')">
                <el-tag :type="getLevelType(detailData.level)" size="small">
                  {{ detailData.level }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.automation')">
                <el-tag v-if="detailData.automation === 'Y'" type="success" size="small">{{ $t('testcase.automationY') }}</el-tag>
                <el-tag v-else-if="detailData.automation === 'D'" type="success" size="small">{{ $t('testcase.automationD') }}</el-tag>
                <el-tag v-else-if="detailData.automation && detailData.automation.startsWith('N-')" type="info" size="small">
                  {{ getAutomationDisplay(detailData.automation) }}
                </el-tag>
                <el-tag v-else-if="detailData.automation === 'N'" type="info" size="small">{{ $t('testcase.automationN') }}</el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('common.status')">
                <el-tag v-if="detailData.status === 'REVIEWED'" type="success" size="small">{{ $t('testcase.statusReviewed') }}</el-tag>
                <el-tag v-else-if="detailData.status === 'PENDING'" type="warning" size="small">{{ $t('testcase.statusPendingReview') }}</el-tag>
                <el-tag v-else-if="detailData.status === 'REJECTED'" type="danger" size="small">{{ $t('testcase.statusReviewRejected') }}</el-tag>
                <el-tag v-else-if="detailData.status === 'DEPRECATED'" type="info" size="small">{{ $t('testcase.statusDeprecated') }}</el-tag>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.prCount')">
                <span v-if="detailData.zmind_link_count > 0">
                  <el-tag type="success" size="small" style="margin-right: 2px;">
                    {{ detailData.zmind_link_open_count || 0 }}
                  </el-tag>
                  /
                  <el-tag type="info" size="small" style="margin-left: 2px;">
                    {{ detailData.zmind_link_close_count || 0 }}
                  </el-tag>
                </span>
                <el-tag v-else type="info" size="small">0</el-tag>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.tags')">
                <div v-if="detailData.tags" class="tags-container" style="text-align: left;">
                  <el-tag 
                    v-for="(tag, index) in parseTags(detailData.tags)" 
                    :key="index"
                    size="small"
                    style="margin: 2px;"
                  >
                    {{ tag }}
                  </el-tag>
                </div>
                <span v-else>-</span>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.remarks')" :span="2">
                <div class="detail-section">{{ detailData.remarks || '-' }}</div>
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.creator')">
                {{ detailData.creator_name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('testcase.updater')">
                {{ detailData.updater_name || '-' }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('common.createdAt')">
                {{ formatDateTime(detailData.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item :label="$t('common.updatedAt')">
                {{ formatDateTime(detailData.updated_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="归档来源" :span="2">
                {{ detailData.archive_source || '-' }}
              </el-descriptions-item>
            </el-descriptions>

            <!-- 附件区域 -->
            <div v-loading="detailAttachmentsLoading" style="margin-top: 16px;">
              <div style="font-size: 14px; font-weight: 500; color: #303133; margin-bottom: 10px;">
                附件 <el-tag v-if="detailAttachments.length > 0" size="small" type="info" round>{{ detailAttachments.length }}</el-tag>
              </div>
              <el-empty v-if="!detailAttachmentsLoading && detailAttachments.length === 0" description="暂无附件" :image-size="60" />
              <div v-else class="detail-attachments-list">
                <div 
                  v-for="att in detailAttachments" 
                  :key="att.id" 
                  class="detail-attachment-item"
                >
                  <div class="attachment-info">
                    <el-icon :size="20" :color="getFileIconColor(att.file_name)">
                      <Document />
                    </el-icon>
                    <div class="attachment-meta">
                      <span class="attachment-name">{{ att.file_name }}</span>
                      <span class="attachment-size">{{ formatFileSize(att.file_size) }} · {{ formatDateTime(att.upload_time) }}</span>
                    </div>
                  </div>
                  <div class="attachment-actions">
                    <el-button 
                      v-if="isPreviewable(att.file_name)"
                      type="primary" 
                      size="small" 
                      link
                      @click="handlePreviewAttachment(att)"
                    >
                      预览
                    </el-button>
                    <el-button 
                      type="primary" 
                      size="small" 
                      link
                      @click="handleDownloadAttachment(att)"
                    >
                      下载
                    </el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-tab-pane>

        <!-- 历史记录标签页 -->
        <el-tab-pane :label="$t('execution.viewHistory')" name="history">
          <div v-loading="historyLoading" style="min-height: 200px;">
            <el-empty v-if="!historyLoading && historyList.length === 0" description="暂无历史记录" />
            <el-timeline v-else>
              <el-timeline-item
                v-for="item in historyList"
                :key="item.id"
                :timestamp="item.changed_at"
                placement="top"
              >
                <el-card shadow="hover">
                  <div class="history-item">
                    <p class="history-user">
                      <el-icon><User /></el-icon>
                      <template v-if="item.field_name === '创建用例'">
                        <strong>{{ item.changed_by_name }}</strong> 创建了用例 <strong>{{ item.new_value }}</strong>
                      </template>
                      <template v-else-if="item.field_name === '上传附件'">
                        <strong>{{ item.changed_by_name }}</strong> 上传了附件 <strong>{{ item.new_value }}</strong>
                      </template>
                      <template v-else-if="item.field_name === '删除附件'">
                        <strong>{{ item.changed_by_name }}</strong> 删除了附件 <strong>{{ item.old_value || item.new_value || '' }}</strong>
                      </template>
                      <template v-else-if="item.field_name === '问题反馈'">
                        <strong>{{ item.changed_by_name }}</strong> 提交了问题反馈
                      </template>
                      <template v-else>
                        <strong>{{ item.changed_by_name }}</strong> 修改了 <strong>{{ item.field_name }}</strong>
                      </template>
                    </p>
                    <!-- 问题反馈显示具体内容 -->
                    <div v-if="item.field_name === '问题反馈'" class="history-change" style="margin-top: 8px;">
                      <div class="history-value new-value" style="flex: 1;">
                        <span class="value-label">反馈内容：</span>
                        <span class="value-content" style="white-space: pre-wrap;">{{ item.new_value }}</span>
                      </div>
                    </div>
                    <div v-if="!['创建用例', '上传附件', '删除附件', '问题反馈'].includes(item.field_name)" class="history-change">
                      <div class="history-value old-value">
                        <span class="value-label">{{ $t('testcase.beforeChange') }}：</span>
                        <span class="value-content">{{ item.old_value || $t('common.empty') }}</span>
                      </div>
                      <el-icon class="arrow-icon"><Right /></el-icon>
                      <div class="history-value new-value">
                        <span class="value-label">{{ $t('testcase.afterChange') }}：</span>
                        <span class="value-content">{{ item.new_value || $t('common.empty') }}</span>
                      </div>
                    </div>
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>

        <!-- 执行历史标签页 -->
        <el-tab-pane :label="$t('execution.title')" name="execution">
          <div v-loading="executionHistoryLoading" style="min-height: 200px;">
            <el-empty v-if="!executionHistoryLoading && executionHistoryList.length === 0" description="暂无执行历史" />
            <el-timeline v-else>
              <el-timeline-item
                v-for="item in executionHistoryList"
                :key="item.id"
                :timestamp="formatDateTime(item.executed_at)"
                placement="top"
              >
                <el-card shadow="hover">
                  <!-- FAIL和BLOCK显示完整信息 -->
                  <template v-if="item.result === 'FAIL' || item.result === 'BLOCK'">
                    <div style="margin-bottom: 12px;">
                      <el-tag v-if="item.result === 'FAIL'" type="danger" size="large">FAIL</el-tag>
                      <el-tag v-else-if="item.result === 'BLOCK'" type="warning" size="large">BLOCK</el-tag>
                    </div>
                    
                    <el-descriptions :column="1" border size="small">
                      <el-descriptions-item :label="$t('testcase.testPlanLabel')">{{ item.testplan_name || $t('common.unknown') }}</el-descriptions-item>
                      <el-descriptions-item :label="$t('testcase.executorLabel')">{{ item.executor_name || $t('common.unknown') }}</el-descriptions-item>
                      <el-descriptions-item :label="$t('testcase.executionTimeLabel')">{{ formatDateTime(item.executed_at) }}</el-descriptions-item>
                      <el-descriptions-item :label="$t('executionDetail.linkedPRLabel')">
                        <div v-if="item.pr_links_snapshot && item.pr_links_snapshot.length > 0">
                          <span v-for="(link, index) in item.pr_links_snapshot" :key="index" style="margin-right: 12px;">
                            <a :href="`https://zmind.whaletv.com/issues/${link.zmind_issue_id}`" target="_blank" rel="noopener noreferrer" style="color: #409EFF; text-decoration: underline;">{{ link.zmind_issue_id }}</a>
                            <span v-if="index < item.pr_links_snapshot.length - 1">,</span>
                          </span>
                        </div>
                        <span v-else>-</span>
                      </el-descriptions-item>
                      <el-descriptions-item :label="$t('testcase.executionRemarkLabel')">
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
                        <el-tag v-if="item.result === 'PASS'" type="success">{{ $t('execution.passed') }}</el-tag>
                        <el-tag v-else-if="item.result === 'SKIP'" type="info">{{ $t('execution.skipped') }}</el-tag>
                        <el-tag v-else type="info">{{ item.result }}</el-tag>
                      </div>
                      <span style="color: #909399; font-size: 14px;">{{ $t('execution.executor') }}：{{ item.executor_name || $t('execution.unknown') }}</span>
                    </div>
                    <div style="color: #606266; margin-bottom: 8px;">
                      {{ $t('testcase.testPlanLabel') }}：{{ item.testplan_name || $t('common.unknown') }}
                    </div>
                    <div v-if="item.remarks" style="color: #606266; white-space: pre-wrap;" v-html="$t('common.remark') + '：' + renderRemarkWithPR(item.remarks)">
                    </div>
                    <div style="color: #909399; font-size: 13px; margin-top: 4px;">
                      {{ $t('execution.versionInfo') }}：{{ item.version_info || '-' }}
                    </div>
                  </template>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>

      </el-tabs>

      <!-- 附件预览对话框 -->
      <el-dialog
        v-model="previewDialogVisible"
        :title="previewFileName"
        width="80%"
        top="5vh"
        append-to-body
        destroy-on-close
      >
        <div class="preview-container">
          <img 
            v-if="previewType === 'image'" 
            :src="previewUrl" 
            style="max-width: 100%; max-height: 70vh; display: block; margin: 0 auto;"
            :alt="previewFileName"
          />
          <iframe 
            v-else-if="previewType === 'pdf'" 
            :src="previewUrl" 
            style="width: 100%; height: 70vh; border: none;"
          />
          <div v-else-if="previewType === 'text'" style="max-height: 70vh; overflow: auto;">
            <pre style="white-space: pre-wrap; word-break: break-all; padding: 16px; background: #f5f7fa; border-radius: 4px; font-size: 13px;">{{ previewTextContent }}</pre>
          </div>
          <div v-else style="text-align: center; padding: 40px; color: #909399;">
            该文件类型不支持预览，请下载后查看
          </div>
        </div>
      </el-dialog>
      
      <template #footer>
        <el-button @click="detailDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button 
          v-if="hasButton('testcases', 'copy')"
          @click="handleCopyFromDetail"
        >
          复制
        </el-button>
        <el-button 
          v-if="hasButton('testcases', 'edit')"
          type="primary" 
          @click="handleEditFromDetail"
        >
          编辑
        </el-button>
      </template>
    </el-dialog>

    <!-- 反馈信息查看对话框 -->
    <el-dialog
      v-model="feedbackViewDialogVisible"
      :title="$t('testcase.feedback')"
      width="500px"
      append-to-body
    >
      <div style="white-space: pre-wrap; color: #606266; line-height: 1.8; padding: 8px 0;">{{ detailData?.feedback || '' }}</div>
      <template #footer>
        <el-button @click="feedbackViewDialogVisible = false">{{ $t('common.close') }}</el-button>
        <el-button type="danger" @click="confirmClearFeedback">移除提示</el-button>
      </template>
    </el-dialog>

    <!-- 模块管理对话框 -->
    <el-dialog 
      v-model="moduleManagementVisible" 
      :title="$t('testcase.moduleManagement')" 
      width="600px"
      :close-on-click-modal="false"
      @closed="handleModuleManagementClosed"
    >
      <div class="module-management" v-loading="moduleManagementLoading">
        <div class="management-header">
          <el-button 
            type="primary" 
            :icon="Plus" 
            size="small"
            @click="handleAddModule"
          >
            {{ $t('testcase.addModule') }}
          </el-button>
        </div>
        
        <el-tree
          ref="moduleTreeRef"
          :data="managementModuleTree"
          node-key="id"
          :props="{ label: 'name', children: 'children' }"
          draggable
          :allow-drag="allowDrag"
          :allow-drop="allowDrop"
          @node-drop="handleNodeDrop"
          class="module-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <span class="node-label">{{ data.name }}<span v-if="data.tag" class="node-tag">({{ data.tag }})</span></span>
              <span class="node-count">({{ data.count || 0 }})</span>
              <div class="node-actions">
                <el-button 
                  type="primary" 
                  :icon="Plus" 
                  size="small" 
                  link
                  @click.stop="handleAddSubModule(data)"
                  :title="$t('testcase.addSubModule')"
                />
                <el-button 
                  type="primary" 
                  :icon="Edit" 
                  size="small" 
                  link
                  @click.stop="handleEditModule(data)"
                  :title="$t('common.edit')"
                />
                <el-button 
                  type="danger" 
                  :icon="Delete" 
                  size="small" 
                  link
                  @click.stop="handleDeleteModule(data)"
                  :title="$t('common.delete')"
                />
              </div>
            </div>
          </template>
        </el-tree>
      </div>
      
      <template #footer>
        <el-button @click="moduleManagementVisible = false">{{ $t('common.close') }}</el-button>
      </template>
    </el-dialog>

    <!-- 模块编辑对话框 -->
    <el-dialog 
      v-model="moduleEditVisible" 
      :title="moduleEditTitle" 
      width="400px"
      :close-on-click-modal="false"
      @closed="handleModuleEditClosed"
    >
      <el-form :model="moduleForm" label-width="100px">
        <el-form-item :label="$t('module.moduleName')" required>
          <el-input 
            v-model="moduleForm.name" 
            :placeholder="$t('module.namePlaceholder')"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
        <!-- Tag字段：仅主模块显示，新建时可填写，编辑时需要权限 -->
        <el-form-item label="Tag" v-if="!moduleForm.parentId" :required="false">
          <el-input 
            v-model="moduleForm.tag" 
            :placeholder="(moduleForm.id && !canEditModuleTag) ? '' : $t('module.tagPlaceholder')"
            :maxlength="50"
            :disabled="!!moduleForm.id && !canEditModuleTag"
            :show-word-limit="!moduleForm.id || canEditModuleTag"
          />
          <div style="color: #909399; font-size: 12px; margin-top: 4px;" v-if="!moduleForm.id">
            {{ $t('module.tagTip') }}
          </div>
          <div style="color: #909399; font-size: 12px; margin-top: 4px;" v-else>
            {{ $t('module.tagTip') }}
          </div>
        </el-form-item>
        <el-form-item :label="$t('module.requirementDoc')" v-if="!moduleForm.parentId">
          <el-input 
            v-model="moduleForm.requirementLink" 
            :placeholder="$t('module.linkPlaceholder')"
            maxlength="500"
          />
        </el-form-item>
        <el-form-item :label="$t('testcase.parentModule')" v-if="!moduleForm.parentId && !moduleForm.id">
          <el-select 
            v-model="moduleForm.parentId" 
            :placeholder="$t('testcase.noParentModule')"
            clearable
            filterable
            style="width: 100%"
          >
            <el-option 
              v-for="module in parentModuleOptions" 
              :key="module.id" 
              :label="module.label" 
              :value="module.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('testcase.parentModule')" v-else-if="moduleForm.parentId && !moduleForm.id">
          <el-input :value="moduleForm.parentName" disabled />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="moduleEditVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleSaveModule" :loading="moduleSaving">
          {{ $t('common.save') }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量编辑对话框 -->
    <el-dialog 
      v-model="batchEditVisible" 
      :title="$t('testcase.batchEdit')" 
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="batchEditForm" label-width="100px">
        <el-alert
          :title="$t('common.tip')"
          type="info"
          :closable="false"
          style="margin-bottom: 20px;"
        >
          已选择 {{ selectedRows.length }} 个用例，只修改勾选的字段
        </el-alert>
        
        <el-form-item>
          <el-checkbox v-model="batchEditForm.updateLevel">{{ $t('testcase.level') }}</el-checkbox>
          <el-select 
            v-model="batchEditForm.level" 
            :placeholder="$t('testcase.selectLevel')"
            :disabled="!batchEditForm.updateLevel"
            style="width: 200px; margin-left: 10px;"
          >
            <el-option :label="$t('testcase.levelL1')" value="L1" />
            <el-option :label="$t('testcase.levelL2')" value="L2" />
            <el-option :label="$t('testcase.levelL3')" value="L3" />
            <el-option :label="$t('testcase.levelL4')" value="L4" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="batchEditForm.updateModule">{{ $t('testcase.module') }}</el-checkbox>
          <div style="display: inline-flex; align-items: center; gap: 8px; margin-left: 10px; flex-wrap: wrap;">
            <el-select
              v-model="batchEditForm.targetProjectId"
              :placeholder="$t('testcase.selectProject')"
              :disabled="!batchEditForm.updateModule"
              filterable
              style="width: 190px;"
              @change="handleBatchTargetProjectChange"
            >
              <el-option
                v-for="project in teamProjectList"
                :key="project.id"
                :label="project.name"
                :value="project.id"
              />
            </el-select>
            <el-tree-select
              v-model="batchEditForm.module"
              :data="batchTargetModuleTree"
              :props="{ label: 'label', value: 'value', children: 'children' }"
              :placeholder="$t('testcase.selectModule')"
              :disabled="!batchEditForm.updateModule || !batchEditForm.targetProjectId"
              filterable
              :filter-node-method="filterModuleNode"
              check-strictly
              :render-after-expand="false"
              default-expand-all
              style="width: 240px;"
            />
          </div>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="batchEditForm.updateAutomation">{{ $t('testcase.automation') }}</el-checkbox>
          <el-select 
            v-model="batchEditForm.automation" 
            :placeholder="$t('testcase.selectAutomation')"
            :disabled="!batchEditForm.updateAutomation"
            style="width: 200px; margin-left: 10px;"
          >
            <el-option :label="$t('testcase.automationY')" value="Y" />
            <el-option :label="$t('testcase.automationD')" value="D" />
            <el-option :label="$t('testcase.automationNHwPhysical')" value="N-HW_PHYSICAL" />
            <el-option :label="$t('testcase.automationNVisualJudge')" value="N-VISUAL_JUDGE" />
            <el-option :label="$t('testcase.automationNBootProcess')" value="N-BOOT_PROCESS" />
            <el-option :label="$t('testcase.automationNMediaPlay')" value="N-MEDIA_PLAY" />
            <el-option :label="$t('testcase.automationNOtaUpgrade')" value="N-OTA_UPGRADE" />
            <el-option :label="$t('testcase.automationNDataConfig')" value="N-DATA_CONFIG" />
            <el-option :label="$t('testcase.automationNLogCheck')" value="N-LOG_CHECK" />
            <el-option :label="$t('testcase.automationNBackendConfig')" value="N-BACKEND_CONFIG" />
            <el-option :label="$t('testcase.automationNDataDynamic')" value="N-DATA_DYNAMIC" />
            <el-option :label="$t('testcase.automationNSpecial')" value="N-OTHER_SPECIAL" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="batchEditForm.updateStatus">{{ $t('testcase.status') }}</el-checkbox>
          <el-select 
            v-model="batchEditForm.status" 
            :placeholder="$t('common.pleaseSelect')"
            :disabled="!batchEditForm.updateStatus"
            style="width: 200px; margin-left: 10px;"
          >
            <el-option :label="$t('testcase.statusReviewed')" value="REVIEWED" />
            <el-option :label="$t('testcase.statusPendingReview')" value="PENDING" />
            <el-option :label="$t('testcase.statusReviewRejected')" value="REJECTED" />
            <el-option :label="$t('testcase.statusDeprecated')" value="DEPRECATED" />
          </el-select>
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="batchEditForm.updateTags">{{ $t('testcase.tags') }}</el-checkbox>
          <el-input 
            v-model="batchEditForm.tags" 
            :placeholder="$t('testcase.tagsPlaceholder')"
            :disabled="!batchEditForm.updateTags"
            style="width: 200px; margin-left: 10px;"
          />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="batchEditForm.updateArchiveSource">归档来源</el-checkbox>
          <el-input 
            v-model="batchEditForm.archive_source" 
            placeholder="请输入归档来源"
            :disabled="!batchEditForm.updateArchiveSource"
            style="width: 200px; margin-left: 10px;"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="batchEditVisible = false">{{ $t('common.cancel') }}</el-button>
        <el-button type="primary" @click="handleBatchEdit" :loading="batchEditing">
          {{ $t('common.confirm') }}
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>
<script setup>
defineOptions({ name: 'TestCaseList' })
import { ref, reactive, onMounted, onUnmounted, onActivated, computed, watch, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { getTestCases, getAllTestCaseIds, createTestCase, updateTestCase, deleteTestCase, batchDeleteTestCases, getDeleteProgress, exportTestCases, batchUpdateTestCases, batchMoveTestCases, exportTestCasesByIds, getZmindLinks, linkZmindIssue, unlinkZmindIssue, updateZmindLink, getTestCaseHistory, getTestCaseExecutionHistory, reorderTestCase, refreshAllPRStatus as refreshAllPRStatusAPI, refreshTestcasePRStatus, getTestCaseStatistics, clearTestCaseFeedback, getFilterOptions } from '../../api/testcase'
import { getAttachments, uploadAttachment, deleteAttachment, downloadAttachment, getAttachmentPreviewUrl } from '../../api/testcaseAttachment'
import { getZmindIssue } from '../../api/zmind'
import { getModuleTree, createModule, updateModule, deleteModule, sortModules, getModulesFlat } from '../../api/module'
import { useScrollToTop } from '../../composables/useScrollToTop'
import { ElMessage, ElMessageBox, ElLoading } from 'element-plus'
import { Document, Upload, Download, Plus, Edit, Delete, Link, Search, ArrowLeft, ArrowRight, ArrowDown, Paperclip, DArrowLeft, DArrowRight, QuestionFilled, Setting, Filter, MoreFilled, User, Right, Warning, CircleClose, Rank, Loading, View, Hide, VideoPlay, List, Calendar, Refresh, CopyDocument } from '@element-plus/icons-vue'
import { useTeam } from '../../composables/useTeam'
import { useUserRole } from '../../composables/useUserRole'
import { usePagination } from '../../composables/usePagination'
import StepEditor from '../../components/StepEditor.vue'
import ProjectSelector from '../../components/ProjectSelector.vue'
import BatchCreateDialog from '../../components/BatchCreateDialog.vue'
import { useLoadingStore } from '../../stores/loading'
import { eventBus } from '../../utils/eventBus'
import { useProjectPreference } from '../../composables/useProjectPreference'
import { renderRemarkWithPR } from '../../composables/useRemarkPR'

const { t } = useI18n()
const router = useRouter()
const { currentTeam, teamProjects, loadTeamProjects } = useTeam()
const { hasButton, isSuperAdmin } = useUserRole()
const canEditModuleTag = computed(() => isSuperAdmin.value || hasButton('projects', 'editModuleTag'))
const loadingStore = useLoadingStore()

// 用例库选择相关 - 新版本
const { selectedProjectIdList, applyPreference, updateSelection, resetPreference } = useProjectPreference()
const teamProjectList = computed(() => teamProjects.value || [])

// 计算当前选中的用例库ID列表（用于API调用）
const currentProjectIds = computed(() => {
  return selectedProjectIdList.value.length > 0 
    ? selectedProjectIdList.value 
    : teamProjectList.value.map(p => p.id)
})

// 兼容旧代码的 currentProjectId（取第一个选中的用例库）
const currentProjectId = computed(() => {
  if (currentProjectIds.value.length > 0) {
    return currentProjectIds.value[0]
  }
  return null
})

// 是否有选中的用例库
const hasSelectedProjects = computed(() => {
  return currentProjectIds.value.length > 0
})

// 是否选中了单个用例库（用于判断是否允许模块管理）
const isSingleProject = computed(() => {
  return selectedProjectIdList.value.length === 1
})

// 处理用例库选择器变化（防抖，防止快速切换导致数据错乱）
let _projectChangeTimer = null
const handleProjectSelectorChange = (ids) => {
  updateSelection(ids)
  page.value = 1
  // 切换用例库时重置模块状态
  selectedModulePath.value = ''
  expandedModulePaths.value = new Set()
  clearTimeout(_projectChangeTimer)
  _projectChangeTimer = setTimeout(() => {
    loadData()
    loadModuleList()
  }, 300)
}

const tableData = ref([])
const { page, size, total } = usePagination('testCaseList', 10)
const totalCount = ref(0)
const loading = ref(false)
const dataReady = ref(false)
const statusStats = ref({
  pending: 0,
  rejected: 0
})
// 统计数据
const statistics = ref({
  total: 0,
  level: {
    L1: 0,
    L2: 0,
    L3: 0,
    L4: 0
  },
  automation: {
    automated: 0,
    cannot_automate: 0,
    not_automated: 0
  },
  review: {
    pending: 0,
    rejected: 0
  }
})
const containerLoading = ref(false)
const dialogVisible = ref(false)
const isCopyMode = ref(false)
const dialogTitle = computed(() => {
  if (isCopyMode.value) return '复制用例'
  return form.id ? t('testcase.editCase') : t('testcase.createCase')
})
const submitting = ref(false)
const exporting = ref(false)

// 拖拽排序相关（用例行拖拽）
const draggedRow = ref(null)
const draggedRowIndex = ref(null)
const dropTargetIndex = ref(null)

// 模块管理相关
const moduleManagementVisible = ref(false)
const moduleEditVisible = ref(false)
const moduleEditTitle = computed(() => {
  if (moduleForm.id) return t('testcase.editModule')
  if (moduleForm.parentId) return t('testcase.addSubModule')
  return t('testcase.addModule')
})
const moduleSaving = ref(false)
const moduleTreeRef = ref(null)
const managementModuleTree = ref([])
const moduleForm = reactive({
  id: null,
  name: '',
  tag: '',
  parentId: null,
  parentName: '',
  requirementLink: ''
})
const parentModuleOptions = computed(() => {
  // 扁平化模块树，所有模块都可以作为父模块
  const result = []
  const flatten = (nodes, prefix = '') => {
    for (const node of nodes) {
      const label = prefix ? `${prefix} / ${node.name}` : node.name
      result.push({ id: node.id, name: node.name, label })
      if (node.children && node.children.length > 0) {
        flatten(node.children, label)
      }
    }
  }
  flatten(managementModuleTree.value)
  return result
})

// 模块扁平列表（用于用例表单选择，带完整路径）
const flatModuleOptions = ref([])

// 加载模块扁平列表
const loadFlatModules = async () => {
  if (!hasSelectedProjects.value) {
    flatModuleOptions.value = []
    return
  }
  try {
    const projectParam = currentProjectIds.value.join(',')
    if (!projectParam) return
    const res = await getModulesFlat(projectParam)
    flatModuleOptions.value = res.data || []
  } catch (error) {
    console.error('加载模块列表失败:', error)
  }
}

// 主模块选项(用于创建/编辑用例 - 保留兼容)
const mainModuleOptions = computed(() => {
  return moduleTree.value.map(m => ({
    name: m.name,
    count: m.count
  }))
})

// ==================== 表单模块树选择（新建/编辑用例） ====================
const formModuleTree = ref([])

// 表单当前用例库ID（新建取 form.primary_project_id，编辑取 form.primary_project_id）
const formProjectId = computed(() => form.primary_project_id)

// 将后端模块树转换为 el-tree-select 需要的格式
const buildFormTreeData = (nodes, parentPath = '') => {
  return nodes.map(node => {
    const path = parentPath ? `${parentPath}/${node.name}` : node.name
    const item = {
      label: node.name,
      value: path,
      children: []
    }
    if (node.children && node.children.length > 0) {
      item.children = buildFormTreeData(node.children, path)
    }
    return item
  })
}

// 加载指定用例库的模块树
const loadFormModuleTree = async (projectId) => {
  if (!projectId) {
    formModuleTree.value = []
    return
  }
  try {
    const res = await getModuleTree(projectId)
    formModuleTree.value = buildFormTreeData(res.data || [])
  } catch (error) {
    console.error('加载表单模块树失败:', error)
    formModuleTree.value = []
  }
}

// 模块树搜索过滤
const filterModuleNode = (value, data) => {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}

// 批量编辑用的模块树（基于当前侧边栏的模块树）
const batchModuleTreeData = computed(() => {
  return buildFormTreeData(moduleTree.value || [])
})
// ====================

// 批量编辑的子模块选项（已废弃，保留空实现避免引用错误）
const batchSubModuleOptions = computed(() => [])

// 处理主模块变化（已简化，不再需要清空子模块）
const handleModuleChange = () => {}

// 处理批量编辑主模块变化
const handleBatchModuleChange = () => {}

const linkDialogVisible = ref(false)
const currentTestCaseId = ref(null)
const zmindLinks = ref([])
const refreshingPRLinks = ref(false)  // 刷新PR loading状态
const detailDialogVisible = ref(false)
const detailData = ref(null)
const feedbackViewDialogVisible = ref(false)
const historyList = ref([])
const historyLoading = ref(false)
const executionHistoryList = ref([])
const executionHistoryLoading = ref(false)
const activeTabName = ref('basic')  // 控制详情对话框的标签页
// 详情弹窗附件相关
const detailAttachments = ref([])
const detailAttachmentsLoading = ref(false)
// 附件预览相关
const previewDialogVisible = ref(false)
const previewUrl = ref('')
const previewFileName = ref('')
const previewType = ref('')  // 'image' | 'pdf' | 'text' | 'other'
const previewTextContent = ref('')
const searchKeyword = ref('')
const regexMode = ref(false)
const selectedModulePath = ref('')  // 选中的模块完整路径
const selectedCaseType = ref('')  // 选中的用例类型
const hasFeedbackFilter = ref(null)  // 筛选有用户反馈的用例
const selectedLevel = ref('')  // 选中的用例等级
const selectedAutomation = ref('')  // 选中的自动化状态
const selectedStatus = ref('')  // 选中的状态
const selectedCreator = ref('')  // 选中的创建人
const selectedUpdater = ref('')  // 选中的更新人
const selectedTag = ref('')  // 选中的标签
const selectedArchiveSource = ref('')  // 选中的归档来源
const creatorList = ref([])  // 创建人列表
const updaterList = ref([])  // 更新人列表
const tagList = ref([])  // 标签列表
const archiveSourceList = ref([])  // 归档来源列表

// 批量操作相关
const selectedRows = ref([])  // 选中的行
const batchEditVisible = ref(false)  // 批量编辑对话框
const batchEditing = ref(false)  // 批量编辑加载状态
const batchEditForm = reactive({
  updateLevel: false,
  level: '',
  updateAutomation: false,
  automation: '',
  updateStatus: false,
  status: '',
  updateTags: false,
  tags: '',
  updateArchiveSource: false,
  archive_source: '',
  updateModule: false,
  module: '',
  targetProjectId: null
})
const batchTargetModuleTree = ref([])  // 批量移动的目标模块树
const moduleTree = ref([])
const expandedModulePaths = ref(new Set())  // 展开的模块路径集合
const moduleSearchKeyword = ref('')  // 模块搜索关键字
const savedExpandedPaths = ref(null)  // 搜索前保存的展开状态，用于恢复

// 搜索时自动展开匹配项的所有父级路径
watch(moduleSearchKeyword, (keyword) => {
  const kw = keyword.trim().toLowerCase()
  if (!kw) {
    if (savedExpandedPaths.value !== null) {
      expandedModulePaths.value = savedExpandedPaths.value
      savedExpandedPaths.value = null
    }
    return
  }
  if (savedExpandedPaths.value === null) {
    savedExpandedPaths.value = new Set(expandedModulePaths.value)
  }
  const pathsToExpand = new Set()
  const findMatches = (nodes) => {
    for (const node of nodes) {
      if (node.name.toLowerCase().includes(kw)) {
        let p = node.path
        while (p.includes('/')) {
          p = p.substring(0, p.lastIndexOf('/'))
          pathsToExpand.add(p)
        }
      }
      if (node.children && node.children.length > 0) {
        findMatches(node.children)
      }
    }
  }
  if (moduleTree.value && moduleTree.value.length > 0) {
    findMatches(moduleTree.value)
  }
  if (pathsToExpand.size > 0) {
    expandedModulePaths.value = new Set([...expandedModulePaths.value, ...pathsToExpand])
  }
})

// 过滤后的模块列表（搜索时展示匹配项及其祖先链，可正常展开收起）
const filteredSidebarModules = computed(() => {
  const keyword = moduleSearchKeyword.value.trim().toLowerCase()
  if (!keyword) return flatSidebarModules.value

  const matchingPaths = new Set()
  const ancestorPaths = new Set()
  const collectAncestors = (nodes) => {
    for (const node of nodes) {
      if (node.name.toLowerCase().includes(keyword)) {
        matchingPaths.add(node.path)
        let p = node.path
        while (p.includes('/')) {
          p = p.substring(0, p.lastIndexOf('/'))
          ancestorPaths.add(p)
        }
      }
      if (node.children && node.children.length > 0) {
        collectAncestors(node.children)
      }
    }
  }
  collectAncestors(moduleTree.value)

  return flatSidebarModules.value.filter(item =>
    matchingPaths.has(item.path) || ancestorPaths.has(item.path)
  )
})

// 将树形模块数据扁平化为列表（根据展开状态过滤）
const flatSidebarModules = computed(() => {
  const result = []
  const flatten = (nodes, depth) => {
    for (const node of nodes) {
      result.push({
        name: node.name,
        path: node.path,
        tag: node.tag,
        count: node.count,
        depth,
        hasChildren: node.children && node.children.length > 0
      })
      if (node.children && node.children.length > 0 && expandedModulePaths.value.has(node.path)) {
        flatten(node.children, depth + 1)
      }
    }
  }
  flatten(moduleTree.value, 0)
  return result
})

// 切换模块展开/收起
const toggleModulePath = (path) => {
  const newSet = new Set(expandedModulePaths.value)
  if (newSet.has(path)) {
    newSet.delete(path)
  } else {
    newSet.add(path)
  }
  expandedModulePaths.value = newSet
}
const moduleListLoading = ref(false)
let moduleListRequestId = 0  // 防止切换用例库时旧请求覆盖新数据
let _loadDataVer = 0  // 防止快速切换用例库时旧请求覆盖新数据
const moduleManagementLoading = ref(false)
const attachments = ref([])  // 附件列表
const tableHeight = ref(400)
const tableContainerRef = ref(null)
const updateTableHeight = () => {
  nextTick(() => {
    if (tableContainerRef.value && tableContainerRef.value.clientHeight > 0) {
      tableHeight.value = tableContainerRef.value.clientHeight
    }
  })
}
let tableResizeObserver = null
const tempAttachments = ref([])  // 临时附件列表（创建时使用）
const tempFiles = ref([])  // 临时文件对象列表
const uploadingFile = ref(false)
const uploadRef = ref(null)
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))
const sidebarCollapsed = ref(false)
const sidebarWidth = ref(220)
const isSidebarResizing = ref(false)
const showStatistics = ref(false)
const importDialogVisible = ref(false)
const batchDeleteDialogVisible = ref(false)
const importFile = ref(null)
const importOverwrite = ref(false)
const importAutoCreateModule = ref(false)
const importing = ref(false)
const importUploadRef = ref(null)
const importProgress = ref(0)
const importStatus = ref('')  // 'uploading' | 'parsing' | 'importing' | 'committing' | ''
const importStatusText = ref('')  // 服务器推送的状态文字
const importStats = ref({ created: 0, updated: 0, skipped: 0, current: 0, total: 0 })
const importErrors = ref([])  // 导入错误信息

// 批量删除相关
const batchDeleting = ref(false)
const deleteProgress = ref(0)
const deleteStatusText = ref('')
const columnSettingsVisible = ref(false)
const visibleColumns = ref({
  case_number: true,
  name: true,
  precondition: false,
  steps: false,
  expected_result: false,
  status: true,
  level: true,
  zmind_link_count: true,
  automation: false,
  tags: false,
  archive_source: false,
  remarks: false,
  creator_name: false,  // 创建人默认不显示
  updater_name: false,
  created_at: false,
  updated_at: false,
  operations: true
})

// 列顺序配置（用于拖拽排序）
const columnOrder = ref([
  { key: 'case_number', label: t('testcase.caseNumber') },
  { key: 'name', label: t('testcase.caseName') },
  { key: 'precondition', label: t('testcase.precondition') },
  { key: 'steps', label: t('testcase.steps') },
  { key: 'expected_result', label: t('testcase.expectedResult') },
  { key: 'status', label: t('testcase.status') },
  { key: 'level', label: t('testcase.level') },
  { key: 'zmind_link_count', label: 'PR' },
  { key: 'automation', label: t('testcase.automation') },
  { key: 'tags', label: t('testcase.tags') },
  { key: 'archive_source', label: '归档来源' },
  { key: 'remarks', label: t('testcase.remarks') },
  { key: 'creator_name', label: t('testcase.creator') },
  { key: 'updater_name', label: t('testcase.updater') },
  { key: 'created_at', label: t('common.createdAt') },
  { key: 'updated_at', label: t('common.updatedAt') }
])

// 计算属性：按顺序返回可见的列
const orderedVisibleColumns = computed(() => {
  return columnOrder.value.filter(col => visibleColumns.value[col.key])
})
const sortProp = ref(null)
const sortOrder = ref(null)
const addLinkForm = reactive({
  zmind_issue_id: '',
  zmind_issue_subject: '',
  zmind_issue_status: '',
  zmind_issue_severity: ''
})

// 控制获取PR信息的加载状态
const fetchingPRInfo = ref(false)

// 筛选相关变量
const severityFilter = ref('')
const statusFilter = ref('')

// 严重程度选项
const severityOptions = [
  { value: 'Critical', label: 'Critical' },
  { value: 'Major', label: 'Major' },
  { value: 'Minor', label: 'Minor' },
  { value: 'Block', label: 'Block' }
]

// 状态选项
const statusOptions = [
  { value: 'New', label: 'New' },
  { value: 'On-going', label: 'On-going' },
  { value: 'Info', label: 'Info' },
  { value: 'Closed', label: 'Closed' },
  { value: 'Confirm', label: 'Confirm' }
]

// 筛选后的PR列表
const filteredZmindLinks = computed(() => {
  return zmindLinks.value.filter(link => {
    // 严重程度筛选
    if (severityFilter.value && link.zmind_issue_severity !== severityFilter.value) {
      return false
    }
    // 状态筛选
    if (statusFilter.value && link.zmind_issue_status !== statusFilter.value) {
      return false
    }
    return true
  })
})

const form = reactive({
  id: null,
  case_number: '',
  module: '',
  name: '',
  case_type: 'COMMON',
  precondition: '',
  steps: [{ step: '', expected: '' }],  // 改为数组格式
  expected_result: '',
  level: 'L3',
  remarks: '',
  automation: null,
  status: 'PENDING',  // 新建用例默认为待评审状态
  primary_project_id: null,
  tags: '',
  archive_source: ''
})

// 监听表单用例库变化，自动加载模块树（不清空模块，由切换事件处理）
watch(() => form.primary_project_id, (newVal, oldVal) => {
  if (newVal !== oldVal) {
    loadFormModuleTree(newVal)
  }
})

// 切换用例库时清空已选模块（旧模块路径在新库中无效）
const handleFormProjectChange = () => {
  form.module = ''
}

// 拖拽相关
const dragOverIndex = ref(null)

const handleDragStart = (index) => {
  draggedIndex.value = index
}

const handleDragEnter = (index) => {
  dragOverIndex.value = index
}

const handleDragEnd = () => {
  draggedIndex.value = null
  dragOverIndex.value = null
}

const handleDrop = (targetIndex) => {
  if (draggedIndex.value === null || draggedIndex.value === targetIndex) {
    draggedIndex.value = null
    dragOverIndex.value = null
    return
  }
  
  const newOrder = [...columnOrder.value]
  const draggedItem = newOrder[draggedIndex.value]
  newOrder.splice(draggedIndex.value, 1)
  newOrder.splice(targetIndex, 0, draggedItem)
  
  columnOrder.value = newOrder
  draggedIndex.value = null
  dragOverIndex.value = null
  
  // 保存列顺序到 localStorage
  saveColumnSettings()
}

// 处理列可见性变化
const handleColumnVisibilityChange = (key, value) => {
  visibleColumns.value[key] = value
  saveColumnSettings()
}

// 保存列设置到 localStorage
const saveColumnSettings = () => {
  const settings = {
    visibility: visibleColumns.value,
    order: columnOrder.value.map(col => col.key)
  }
  localStorage.setItem('testcase_column_settings', JSON.stringify(settings))
}

// 列显示数组（用于checkbox-group）
const visibleColumnsArray = computed({
  get: () => {
    return Object.keys(visibleColumns.value).filter(key => visibleColumns.value[key])
  },
  set: (val) => {
    // 更新 visibleColumns 对象
    Object.keys(visibleColumns.value).forEach(key => {
      visibleColumns.value[key] = val.includes(key)
    })
    // 保存到 localStorage
    saveColumnSettings()
  }
})

// 处理列显示变化
const handleColumnChange = () => {
  // checkbox-group 的 change 事件会自动触发 computed 的 set
}

// 处理排序变化
const handleSortChange = ({ column, prop, order }) => {
  sortProp.value = prop
  sortOrder.value = order
  loadData()
}

// 从 localStorage 加载列设置
const loadColumnSettings = () => {
  const saved = localStorage.getItem('testcase_column_settings')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      
      // 加载可见性设置
      if (parsed.visibility) {
        Object.keys(parsed.visibility).forEach(key => {
          if (key in visibleColumns.value) {
            visibleColumns.value[key] = parsed.visibility[key]
          }
        })
      }
      
      // 加载列顺序
      if (parsed.order && Array.isArray(parsed.order)) {
        const columnMap = new Map(columnOrder.value.map(col => [col.key, col]))
        const newOrder = []
        
        // 按保存的顺序重新排列
        parsed.order.forEach(key => {
          if (columnMap.has(key)) {
            newOrder.push(columnMap.get(key))
            columnMap.delete(key)
          }
        })
        
        // 添加新增的列（如果有）
        columnMap.forEach(col => {
          newOrder.push(col)
        })
        
        columnOrder.value = newOrder
      }
    } catch (e) {
      console.error('加载列设置失败:', e)
    }
  }
}

// 解析步骤文本（支持JSON格式和纯文本格式）
const parseSteps = (stepsText) => {
  if (!stepsText) return []
  
  // 如果已经是数组，直接处理
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
  
  // 转换为字符串并去除首尾空格
  const textStr = String(stepsText).trim()
  if (!textStr) return []
  
  try {
    // 尝试解析JSON格式
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
  
  // 如果已经是数组，直接处理
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
  
  // 转换为字符串并去除首尾空格
  const textStr = String(expectedText).trim()
  if (!textStr) return []
  
  try {
    // 尝试解析JSON格式
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

// 获取等级标签颜色
const getLevelType = (level) => {
  const types = {
    'L1': 'danger',   // 红色
    'L2': 'warning',  // 橙色
    'L3': 'primary',  // 蓝色
    'L4': 'info'      // 灰色
  }
  return types[level] || 'info'
}

// 获取用例类型名称
const getCaseTypeName = (caseType) => {
  const names = {
    'COMMON': t('testcase.typeFunctional'),
    'PERFORMANCE': t('testcase.typePerformance'),
    'SECURITY': t('testcase.typeSecurity'),
    'INTERFACE': t('testcase.typeInterface'),
    'INSTALL': t('testcase.typeInstall'),
    'CONFIG': t('testcase.typeConfig'),
    'COMPATIBILITY': t('testcase.typeCompatibility'),
    'OTHER': t('testcase.typeOther')
  }
  return names[caseType] || t('testcase.typeFunctional')
}

// 获取用例类型颜色
const getCaseTypeColor = (caseType) => {
  const colors = {
    'COMMON': 'primary',
    'PERFORMANCE': 'warning',
    'SECURITY': 'danger',
    'INTERFACE': 'success',
    'INSTALL': 'info',
    'CONFIG': '',
    'COMPATIBILITY': 'warning',
    'OTHER': 'info'
  }
  return colors[caseType] || 'primary'
}

// 加载统计数据
const loadStatistics = async () => {
  if (!hasSelectedProjects.value) {
    return
  }
  
  try {
    const params = {}
    
    // 添加用例库ID参数
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    
    // 如果选择了模块，添加模块筛选
    if (selectedModulePath.value) {
      params.module = selectedModulePath.value
    }
    
    // 添加关键词搜索（统计也需要跟随关键词过滤）
    if (searchKeyword.value) {
      params.keyword = regexMode.value ? `regex:${searchKeyword.value}` : searchKeyword.value
    }
    
    const res = await getTestCaseStatistics(params)
    if (res.code === 200) {
      statistics.value = res.data
      // 从统计接口获取待评审/未通过计数，避免额外的全量查询
      if (res.data.review) {
        statusStats.value.pending = res.data.review.pending || 0
        statusStats.value.rejected = res.data.review.rejected || 0
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const handleSearch = () => {
  page.value = 1
  loadData()
}

const loadData = async () => {
  if (!hasSelectedProjects.value) {
    tableData.value = []
    total.value = 0
    loading.value = false
    dataReady.value = true
    return
  }
  
  const ver = ++_loadDataVer
  loading.value = true

  try {
    const params = { 
      page: page.value, 
      size: size.value 
    }
    
    // 添加用例库ID参数
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    
    // 添加用例类型筛选
    if (selectedCaseType.value) {
      params.case_type = selectedCaseType.value
    }
    
    // 添加模块筛选
    if (selectedModulePath.value) {
      params.module = selectedModulePath.value
    }
    
    // 添加关键词搜索
    if (searchKeyword.value) {
      params.keyword = regexMode.value ? `regex:${searchKeyword.value}` : searchKeyword.value
    }
    
    // 添加排序参数
    if (sortProp.value && sortOrder.value) {
      params.sort_by = sortProp.value
      params.sort_order = sortOrder.value
    }
    
    // 添加状态筛选（服务端过滤）
    if (selectedStatus.value) {
      params.status = selectedStatus.value
    }
    
    // 添加等级筛选（服务端过滤）
    if (selectedLevel.value) {
      params.level_in = selectedLevel.value
    }
    
    // 添加自动化筛选（服务端过滤）
    if (selectedAutomation.value) {
      params.automation = selectedAutomation.value
    }
    
    // 添加用户反馈筛选（服务端过滤）
    if (hasFeedbackFilter.value !== null) {
      params.has_feedback = hasFeedbackFilter.value
    }
    
    // 添加归档来源筛选（服务端过滤）
    if (selectedArchiveSource.value) {
      params.archive_source = selectedArchiveSource.value
    }
    
    const res = await getTestCases(params)
    if (ver !== _loadDataVer) return
    let records = res.data.records
    
    // 前端筛选（用于创建人、更新人）
    if (selectedCreator.value) {
      records = records.filter(item => item.creator_name === selectedCreator.value)
    }
    if (selectedUpdater.value) {
      records = records.filter(item => item.updater_name === selectedUpdater.value)
    }
    // 标签筛选
    if (selectedTag.value) {
      records = records.filter(item => {
        if (!item.tags) return false
        const tags = parseTags(item.tags)
        return tags.includes(selectedTag.value)
      })
    }
    
    total.value = res.data.total
    // 处理空值，将 null 或 undefined 转换为 "-"
    tableData.value = records.map(record => ({
      ...record,
      creator_name: record.creator_name || '-',
      updater_name: record.updater_name || '-'
    }))
    
    // 加载统计数据（包含待评审/未通过计数）
    await loadStatistics()
    
    // 提取创建人、更新人列表
    const creators = new Set()
    const updaters = new Set()
    res.data.records.forEach(item => {
      if (item.creator_name) creators.add(item.creator_name)
      if (item.updater_name) updaters.add(item.updater_name)
    })
    creatorList.value = Array.from(creators).sort()
    updaterList.value = Array.from(updaters).sort()
    
    // 加载筛选选项（归档来源、标签等）
    loadFilterOptions()
  } catch (error) {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    if (status === 400 && detail) {
      ElMessage.error(`正则搜索错误：${detail}`)
    } else if (status === 408) {
      ElMessage.error(detail || '正则搜索超时，请简化正则表达式后重试')
    } else {
      ElMessage.error(t('testcase.loadDataFailed'))
    }
  } finally {
    if (ver === _loadDataVer) {
      loading.value = false
      dataReady.value = true
    }
  }
}

// 加载筛选选项（归档来源、标签等）
const loadFilterOptions = async () => {
  try {
    const params = {}
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }
    if (selectedModulePath.value) {
      params.module = selectedModulePath.value
    }
    const res = await getFilterOptions(params)
    if (res.code === 200 && res.data) {
      archiveSourceList.value = res.data.archive_sources || []
      tagList.value = res.data.tags || []
    }
  } catch (error) {
    console.error('加载筛选选项失败:', error)
  }
}

// 加载模块列表和统计（树形结构）
const loadModuleList = async () => {
  if (!hasSelectedProjects.value) {
    moduleTree.value = []
    totalCount.value = 0
    return
  }
  
  moduleListLoading.value = true
  const requestId = ++moduleListRequestId  // 记录本次请求ID
  try {
    // 获取模块树参数
    let projectParam
    if (currentProjectIds.value.length > 0) {
      projectParam = currentProjectIds.value.join(',')
    }
    
    if (!projectParam) {
      moduleTree.value = []
      totalCount.value = 0
      return
    }
    
    // 从后端API获取模块树（已包含path字段）
    const res = await getModuleTree(projectParam)
    
    // 如果已有更新的请求发出，丢弃本次过期响应
    if (requestId !== moduleListRequestId) return
    
    // 保存当前展开状态（不重置）
    // 后端返回的树已经包含 path 字段，直接使用
    moduleTree.value = res.data || []
    
    // 递归累加子模块的 count 到父模块
    // 注意：单项目模式下后端已经累加过了，需要判断是否需要前端累加
    // 判断方式：如果父模块的 count 已经 >= 所有子模块 count 之和，说明后端已累加
    const accumulateCount = (nodes) => {
      for (const node of nodes) {
        if (node.children && node.children.length > 0) {
          accumulateCount(node.children)
          const childrenSum = node.children.reduce((sum, c) => sum + (c.count || 0), 0)
          // 只有当父模块 count 小于子模块之和时才累加（说明后端没有累加）
          if ((node.count || 0) < childrenSum) {
            node.count = (node.count || 0) + childrenSum
          }
        }
      }
    }
    accumulateCount(moduleTree.value)
    
    // 使用后端返回的精确总数（包含未分配模块的用例）
    if (res.total_count !== undefined) {
      totalCount.value = res.total_count
    } else {
      // 兼容旧版后端：取根节点累加
      totalCount.value = moduleTree.value.reduce((sum, node) => sum + (node.count || 0), 0)
    }
  } catch (error) {
    if (requestId !== moduleListRequestId) return
    console.error('加载模块列表失败:', error)
  } finally {
    if (requestId === moduleListRequestId) {
      moduleListLoading.value = false
    }
  }
  
  // 同时加载扁平模块列表（用于表单选择）
  loadFlatModules()
}

// 处理用例类型变化
const handleCaseTypeChange = () => {
  page.value = 1
  loadData()
}

// 处理用户反馈筛选变化
const handleHasFeedbackChange = () => {
  page.value = 1
  loadData()
}

// 处理用例等级筛选
const handleLevelFilter = (level) => {
  selectedLevel.value = level
  page.value = 1
  loadData()
}

// 处理自动化筛选
const handleAutomationFilter = (automation) => {
  selectedAutomation.value = automation
  page.value = 1
  loadData()
}

const getAutomationDisplay = (value) => {
  if (!value) return '-'
  const map = {
    'N-HW_PHYSICAL': { label: 'testcase.automationNHwPhysical', tip: 'testcase.automationNHwPhysicalTip' },
    'N-VISUAL_JUDGE': { label: 'testcase.automationNVisualJudge', tip: 'testcase.automationNVisualJudgeTip' },
    'N-BOOT_PROCESS': { label: 'testcase.automationNBootProcess', tip: 'testcase.automationNBootProcessTip' },
    'N-MEDIA_PLAY': { label: 'testcase.automationNMediaPlay', tip: 'testcase.automationNMediaPlayTip' },
    'N-OTA_UPGRADE': { label: 'testcase.automationNOtaUpgrade', tip: 'testcase.automationNOtaUpgradeTip' },
    'N-DATA_CONFIG': { label: 'testcase.automationNDataConfig', tip: 'testcase.automationNDataConfigTip' },
    'N-LOG_CHECK': { label: 'testcase.automationNLogCheck', tip: 'testcase.automationNLogCheckTip' },
    'N-BACKEND_CONFIG': { label: 'testcase.automationNBackendConfig', tip: 'testcase.automationNBackendConfigTip' },
    'N-DATA_DYNAMIC': { label: 'testcase.automationNDataDynamic', tip: 'testcase.automationNDataDynamicTip' },
    'N-OTHER_SPECIAL': { label: 'testcase.automationNSpecial', tip: 'testcase.automationNSpecialTip' }
  }
  const item = map[value]
  if (item) {
    return `${t('common.no')} - ${t(item.label)}`
  }
  return t('common.no')
}

// 处理状态筛选
const handleStatusFilter = (status) => {
  selectedStatus.value = status
  page.value = 1
  loadData()
}

// 处理创建人筛选
const handleCreatorFilter = (creator) => {
  selectedCreator.value = creator
  page.value = 1
  loadData()
}

// 处理更新人筛选
const handleUpdaterFilter = (updater) => {
  selectedUpdater.value = updater
  page.value = 1
  loadData()
}

// 解析标签
const parseTags = (tagsText) => {
  if (!tagsText) return []
  try {
    const parsed = JSON.parse(tagsText)
    return Array.isArray(parsed) ? parsed : []
  } catch (e) {
    return tagsText.split(',').map(t => t.trim()).filter(t => t)
  }
}

// 格式化日期时间
const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

// 保存用户偏好到localStorage
const saveUserPreferences = () => {
  const preferences = {
    sidebarCollapsed: sidebarCollapsed.value,
    sidebarWidth: sidebarWidth.value,
    showStatistics: showStatistics.value
  }
  localStorage.setItem('testcase_user_preferences', JSON.stringify(preferences))
}

// 加载用户偏好从localStorage
const loadUserPreferences = () => {
  const saved = localStorage.getItem('testcase_user_preferences')
  if (saved) {
    try {
      const preferences = JSON.parse(saved)
      if (preferences.sidebarCollapsed !== undefined) {
        sidebarCollapsed.value = preferences.sidebarCollapsed
      }
      if (preferences.showStatistics !== undefined) {
        showStatistics.value = preferences.showStatistics
      }
      if (preferences.sidebarWidth) {
        sidebarWidth.value = preferences.sidebarWidth
      }
    } catch (e) {
      console.error('加载用户偏好失败:', e)
    }
  }
}

// 切换侧边栏展开/收起
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
  saveUserPreferences()
}

// 拖拽调整侧边栏宽度
const startSidebarResize = (e) => {
  e.preventDefault()
  isSidebarResizing.value = true
  const startX = e.clientX
  const startWidth = sidebarWidth.value

  const onMouseMove = (ev) => {
    const newWidth = startWidth + (ev.clientX - startX)
    sidebarWidth.value = Math.max(150, Math.min(500, newWidth))
  }
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
    isSidebarResizing.value = false
    saveUserPreferences()
  }
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// 切换统计卡片显示/隐藏
const toggleStatistics = () => {
  showStatistics.value = !showStatistics.value
  saveUserPreferences()
}

// 切换模块展开/收起
// 切换模块展开/收起（已废弃，保留空实现避免引用错误）
const toggleModule = () => {}

// 处理模块点击
const handleModuleClick = (modulePath) => {
  selectedModulePath.value = modulePath
  page.value = 1
  loadData()
}

// 判断文本是否溢出需要显示tooltip
const isTextOverflow = (text, type) => {
  if (!text) return false
  
  // 根据类型估算可用宽度
  // 侧边栏宽度280px，减去padding、图标、数字标签等
  const mainModuleMaxWidth = 280 - 40 - 14 - 8 - 50 // 约168px
  const subModuleMaxWidth = 280 - 60 - 14 - 8 - 50 // 约148px
  
  const maxWidth = type === 'main' ? mainModuleMaxWidth : subModuleMaxWidth
  
  // 估算文本宽度（中文约14px，英文约7px）
  const chineseCount = (text.match(/[\u4e00-\u9fa5]/g) || []).length
  const otherCount = text.length - chineseCount
  const estimatedWidth = chineseCount * 14 + otherCount * 7
  
  return estimatedWidth > maxWidth
}

// ==================== 模块管理功能 ====================

// 显示模块管理对话框
const showModuleManagement = async () => {
  moduleManagementVisible.value = true
  await buildManagementModuleTree()
}

// 模块管理对话框关闭时移除按钮焦点
const handleModuleManagementClosed = () => {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

// 模块编辑对话框关闭时移除按钮焦点
const handleModuleEditClosed = () => {
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
}

// 构建管理用的模块树(从后端API获取)
const buildManagementModuleTree = async () => {
  moduleManagementLoading.value = true
  try {
    const res = await getModuleTree(currentProjectId.value)
    managementModuleTree.value = res.data
  } catch (error) {
    console.error('加载模块树失败:', error)
    ElMessage.error(t('testcase.loadModuleTreeFailed'))
  } finally {
    moduleManagementLoading.value = false
  }
}

// 新增主模块
const handleAddModule = () => {
  if (!currentProjectId.value) {
    ElMessage.warning(t('testcase.addModuleWarning'))
    return
  }
  moduleForm.id = null
  moduleForm.name = ''
  moduleForm.tag = ''
  moduleForm.parentId = null
  moduleForm.parentName = ''
  moduleForm.requirementLink = ''
  moduleEditVisible.value = true
}

// 新增子模块
const handleAddSubModule = (parentModule) => {
  if (!parentModule.id) {
    ElMessage.warning(t('testcase.multiProjectNoSubModule'))
    return
  }
  moduleForm.id = null
  moduleForm.name = ''
  moduleForm.tag = ''  // 子模块不显示Tag
  moduleForm.parentId = parentModule.id
  moduleForm.parentName = parentModule.name
  moduleForm.requirementLink = ''  // 子模块不显示需求链接
  moduleEditVisible.value = true
}

// 编辑模块
const handleEditModule = (module) => {
  if (!module.id) {
    ElMessage.warning(t('testcase.multiProjectNoEdit'))
    return
  }
  moduleForm.id = module.id
  moduleForm.name = module.name
  moduleForm.tag = module.tag || ''  // 主模块显示Tag，子模块为空
  moduleForm.parentId = module.parent_id || null
  moduleForm.parentName = module.parentName || ''
  moduleForm.requirementLink = module.requirement_link || module.requirementLink || ''  // 主模块显示需求链接
  moduleEditVisible.value = true
}

// 删除模块
const handleDeleteModule = async (module) => {
  if (!module.id) {
    ElMessage.warning(t('testcase.multiProjectNoDelete'))
    return
  }
  
  if (module.count > 0) {
    ElMessage.warning(t('testcase.moduleHasCases'))
    return
  }
  
  if (module.children && module.children.length > 0) {
    ElMessage.warning(t('testcase.moduleHasChildren'))
    return
  }
  
  try {
    await ElMessageBox.confirm(
      t('testcase.deleteModuleConfirm', { name: module.name }),
      t('common.deleteConfirmTitle'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning'
      }
    )
    
    await deleteModule(module.id)
    ElMessage.success(t('testcase.deleteSuccess'))
    
    // 重新加载模块树
    await buildManagementModuleTree()
    await loadModuleList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || t('common.failed'))
    }
  }
}

// 保存模块
const handleSaveModule = async () => {
  if (!moduleForm.name || !moduleForm.name.trim()) {
    ElMessage.warning(t('testcase.inputModuleName'))
    return
  }
  
  if (!moduleForm.id && !currentProjectId.value) {
    ElMessage.warning(t('testcase.addModuleWarning'))
    return
  }
  
  moduleSaving.value = true
  
  try {
    if (moduleForm.id) {
      // 编辑模块
      const updateData = {
        name: moduleForm.name.trim()
      }
      // 有权限的用户可以修改Tag
      if (canEditModuleTag.value && !moduleForm.parentId) {
        updateData.tag = moduleForm.tag || null
      }
      // 主模块可以修改需求链接
      if (!moduleForm.parentId) {
        updateData.requirement_link = moduleForm.requirementLink || null
      }
      await updateModule(moduleForm.id, updateData)
      ElMessage.success(t('testcase.updateSuccess'))
    } else {
      // 新增模块
      const createData = {
        project_id: currentProjectId.value,
        name: moduleForm.name.trim(),
        parent_id: moduleForm.parentId
      }
      // 只有主模块才能设置Tag（parentId为null或undefined）
      if (!moduleForm.parentId) {
        createData.tag = moduleForm.tag || null
        createData.requirement_link = moduleForm.requirementLink || null
      }
      await createModule(createData)
      ElMessage.success(t('testcase.createSuccess'))
    }
    
    moduleEditVisible.value = false
    
    // 重新加载模块树
    await buildManagementModuleTree()
    await loadModuleList()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || t('testcase.operationFailed'))
  } finally {
    moduleSaving.value = false
  }
}

// 允许拖动判断（只允许主模块拖动）
const allowDrag = (draggingNode) => {
  return !draggingNode.data.parent_id
}

// 允许拖放判断
const allowDrop = (draggingNode, dropNode, type) => {
  if (type !== 'prev' && type !== 'next') {
    return false
  }
  
  // 只允许主模块拖动排序，子模块禁止拖动
  if (!draggingNode.data.parent_id && !dropNode.data.parent_id) {
    return true
  }
  
  return false
}

// 处理节点拖放
const handleNodeDrop = async () => {
  try {
    // 递归收集所有模块的新排序
    const moduleOrders = []
    const collectOrders = (nodes) => {
      nodes.forEach((node, index) => {
        moduleOrders.push({
          id: node.id,
          sort_order: index
        })
        if (node.children && node.children.length > 0) {
          collectOrders(node.children)
        }
      })
    }
    collectOrders(managementModuleTree.value)
    
    // 批量更新排序
    await sortModules(moduleOrders)
    ElMessage.success(t('testcase.sortUpdated'))
    
    // 重新加载模块列表和用例数据
    await loadModuleList()
    loadData()
  } catch (error) {
    ElMessage.error(t('testcase.sortUpdateFailed'))
    // 重新加载以恢复原状态
    await buildManagementModuleTree()
  }
}

// ==================== 模块管理功能结束 ====================

const handleCreate = () => {
  form.id = null
  form.case_number = ''
  form.module = ''
  form.name = ''
  form.case_type = 'COMMON'
  form.precondition = ''
  form.steps = [{ step: '', expected: '' }]
  form.expected_result = ''
  form.level = 'L3'
  form.remarks = ''
  form.automation = null
  form.status = 'PENDING'  // 新建用例默认为待评审状态
  form.tags = ''
  form.archive_source = ''
  formModuleTree.value = []
  form.primary_project_id = isSingleProject.value ? currentProjectIds.value[0] : null
  attachments.value = []
  tempAttachments.value = []
  tempFiles.value = []
  
  // 使用 nextTick 确保 DOM 更新完成后再打开对话框
  dialogVisible.value = true
  
  // 主动加载模块树（watch 在值不变时不会触发）
  if (form.primary_project_id) {
    loadFormModuleTree(form.primary_project_id)
  }
}

const batchCreateVisible = ref(false)
let batchCreateCollapsedNav = false

const handleBatchCreate = () => {
  // 记录打开时导航栏是否展开（未折叠），打开时自动折叠导航栏
  batchCreateCollapsedNav = !isNavCollapsed()
  if (batchCreateCollapsedNav) {
    eventBus.emit('nav-collapse', true)
  }
  batchCreateVisible.value = true
}

const handleBatchCreateClose = () => {
  // 关闭时恢复导航栏（仅当打开时是由此处折叠的）
  if (batchCreateCollapsedNav) {
    eventBus.emit('nav-collapse', false)
    batchCreateCollapsedNav = false
  }
}

// 辅助：读取导航栏当前状态（通过 Layout 存入 localStorage，或直接通过 DOM 宽度判断）
const isNavCollapsed = () => {
  const aside = document.querySelector('.sidebar-demo')
  if (aside) return aside.offsetWidth <= 64
  return false
}

const handleBatchCreateSuccess = () => {
  loadData()
  loadModuleList()
  eventBus.emit('testcases-changed')
}

const handleEdit = (row) => {
  form.id = row.id
  form.case_number = row.case_number || ''
  form.module = row.module || ''
  form.name = row.name
  form.case_type = row.case_type || 'COMMON'
  form.precondition = row.precondition || ''
  
  // 解析步骤数据
  try {
    const parsed = JSON.parse(row.steps)
    if (Array.isArray(parsed) && parsed.length > 0) {
      // 移除步骤和预期结果中的序号
      form.steps = parsed.map(item => {
        let stepText = String(item.step || '').trim()
        let expectedText = String(item.expected || '').trim()
        
        // 使用循环移除所有开头的序号（排除小数点：. 后不能紧跟数字）
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(stepText)) {
          stepText = stepText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(expectedText)) {
          expectedText = expectedText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        
        return {
          step: stepText,
          expected: expectedText
        }
      })
    } else {
      form.steps = [{ step: row.steps || '', expected: row.expected_result || '' }]
    }
  } catch (e) {
    // 如果不是JSON格式，转换为新格式
    form.steps = [{ step: row.steps || '', expected: row.expected_result || '' }]
  }
  
  form.expected_result = row.expected_result || ''
  form.level = row.level || 'L3'
  form.remarks = row.remarks || ''
  form.automation = row.automation || null
  form.status = row.status || 'PENDING'  // 读取状态，默认为待评审
  form.tags = row.tags ? parseTags(row.tags).join(', ') : ''
  form.archive_source = row.archive_source || ''
  form.primary_project_id = row.primary_project_id || row.project_id
  
  // 加载该用例库的模块树
  loadFormModuleTree(form.primary_project_id)
  
  // 加载附件列表
  loadAttachments(row.id)
  
  dialogVisible.value = true
}

// 加载附件列表
const loadAttachments = async (testCaseId) => {
  try {
    const res = await getAttachments(testCaseId)
    attachments.value = res.data || []
  } catch (error) {
    console.error('加载附件失败:', error)
  }
}

// 附件上传前检查
const beforeAttachmentUpload = (file) => {
  const maxSize = 100 * 1024 * 1024 // 100MB
  if (file.size > maxSize) {
    ElMessage.error(t('testcase.fileSizeLimit'))
    return false
  }
  uploadingFile.value = true
  return true
}

// 附件上传成功
const handleAttachmentSuccess = (response) => {
  uploadingFile.value = false
  if (response.code === 200) {
    ElMessage.success(t('attachment.uploadSuccess'))
    loadAttachments(form.id)
  } else {
    ElMessage.error(response.message || t('testcase.uploadFailed'))
  }
}

// 附件上传失败
const handleAttachmentError = () => {
  uploadingFile.value = false
  ElMessage.error(t('testcase.uploadFailed'))
}

// 下载附件
const handleDownloadAttachment = async (attachment) => {
  try {
    const response = await downloadAttachment(attachment.id)
    // response 是完整的 axios response 对象（responseType: 'blob'），
    // 实际文件数据在 response.data，不能直接用 response 构造 Blob
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
    ElMessage.error(t('testcase.downloadFailed'))
  }
}

// 删除附件
const handleDeleteAttachment = async (attachment) => {
  try {
    await ElMessageBox.confirm(t('testcase.deleteAttachmentConfirm'), t('common.deleteConfirmTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning'
    })
    
    await deleteAttachment(attachment.id)
    ElMessage.success(t('common.deleteSuccess'))
    loadAttachments(form.id)
  } catch (error) {
    // 用户取消
  }
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 处理临时文件选择（创建模式）
const handleTempFileChange = (file, fileList) => {
  // 检查文件大小
  const maxSize = 100 * 1024 * 1024 // 100MB
  if (file.size > maxSize) {
    ElMessage.error(t('testcase.fileSizeLimit'))
    // 移除超大文件
    const index = fileList.findIndex(f => f.uid === file.uid)
    if (index > -1) {
      fileList.splice(index, 1)
    }
    return
  }
  
  tempAttachments.value = fileList
  tempFiles.value = fileList.map(f => f.raw)
}

// 处理临时文件移除（创建模式）
const handleTempFileRemove = (file, fileList) => {
  tempAttachments.value = fileList
  tempFiles.value = fileList.map(f => f.raw)
}

// 上传临时附件到已创建的测试用例
const uploadTempAttachments = async (testCaseId) => {
  if (tempFiles.value.length === 0) {
    return true
  }
  
  try {
    // 逐个上传附件
    for (const file of tempFiles.value) {
      const formData = new FormData()
      formData.append('file', file)
      
      await uploadAttachment(testCaseId, formData)
    }
    return true
  } catch (error) {
    console.error('上传附件失败:', error)
    ElMessage.warning(t('testcase.createSuccessAttachmentFailed'))
    return false
  }
}

const handleSubmit = async () => {
  // 验证必填字段（用例编号已改为自动生成，不再检查）
  if (!form.module || !form.name || !form.level) {
    ElMessage.warning(t('testcase.fillRequiredFields'))
    return
  }

  // 新建时验证用例库必选
  if (!form.id && !form.primary_project_id) {
    ElMessage.warning(t('testcase.selectProjectFirst'))
    return
  }

  // 验证步骤
  if (!form.steps || form.steps.length === 0) {
    ElMessage.warning(t('testcase.addStep'))
    return
  }

  // 检查步骤是否至少有一个字段填写了（操作步骤或预期结果至少填一个）
  const hasEmptyStep = form.steps.some(s => !s.step && !s.expected)
  if (hasEmptyStep) {
    ElMessage.warning(t('testcase.stepContentRequired'))
    return
  }

  // 验证等级
  if (!['L1', 'L2', 'L3', 'L4'].includes(form.level)) {
    ElMessage.warning(t('testcase.levelInvalid'))
    return
  }

  // 验证自动化字段
  const validAutomation = ['Y', 'D', 'N', 'N-HW_PHYSICAL', 'N-VISUAL_JUDGE', 'N-BOOT_PROCESS', 'N-MEDIA_PLAY', 'N-OTA_UPGRADE', 'N-DATA_CONFIG', 'N-LOG_CHECK', 'N-BACKEND_CONFIG', 'N-DATA_DYNAMIC', 'N-OTHER_SPECIAL']
  if (form.automation && !validAutomation.includes(form.automation)) {
    ElMessage.warning(t('testcase.automationInvalid'))
    return
  }

  submitting.value = true
  try {
    // 将步骤数组转换为JSON字符串（保持原样，不修改序号）
    const stepsJson = JSON.stringify(form.steps)
    
    // 生成纯文本格式的预期结果（用于兼容和搜索）
    // 注意：需要先移除预期结果中已有的序号，避免重复添加
    const expectedText = form.steps.map((s, i) => {
      let expectedText = String(s.expected || '').trim()
      // 移除开头的序号（支持多种格式：1. 1。 1、）
      expectedText = expectedText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
      return `${i + 1}. ${expectedText}`
    }).join('\n')
    
    const submitData = {
      ...form,
      steps: stepsJson,  // 保存JSON格式（保持原样）
      expected_result: expectedText,  // 保存文本格式用于兼容
      tags: form.tags ? JSON.stringify(form.tags.split(/[,，]/).map(t => t.trim()).filter(t => t)) : null
    }
    
    if (form.id && !isCopyMode.value) {
      // 编辑模式
      await updateTestCase(form.id, submitData)
      ElMessage.success(t('testcase.updateSuccess'))
    } else {
      // 创建模式（包括复制模式）
      const createData = { ...submitData, id: undefined }
      const response = await createTestCase(createData)
      const newTestCaseId = response.data.id
      const newTestCase = response.data  // 含 module, primary_project_id, case_number 等
      
      // 如果有临时附件，上传它们
      if (tempFiles.value.length > 0) {
        await uploadTempAttachments(newTestCaseId)
      }
      
      ElMessage.success(t('testcase.createSuccess'))

      dialogVisible.value = false
      // 复制模式：定位到新用例
      if (isCopyMode.value) {
        loadModuleList()
        eventBus.emit('testcases-changed')
        await scrollToCopiedRow(newTestCaseId, newTestCase)
        return
      }
    }
    
    dialogVisible.value = false
    loadData()
    loadModuleList()
    eventBus.emit('testcases-changed')
  } catch (error) {
    let errorMsg = t('testcase.operationFailed')
    
    // 处理不同类型的错误
    if (error.response) {
      const detail = error.response.data?.detail
      const message = error.response.data?.message
      
      // 优先使用 detail
      if (detail) {
        if (typeof detail === 'string') {
          errorMsg = detail
        } else if (Array.isArray(detail)) {
          // 处理 FastAPI 验证错误格式
          errorMsg = detail.map(d => {
            if (d.msg) return d.msg
            if (d.message) return d.message
            return JSON.stringify(d)
          }).join('; ')
        } else if (typeof detail === 'object') {
          errorMsg = JSON.stringify(detail)
        }
      } else if (message) {
        errorMsg = message
      }
    } else if (error.message) {
      errorMsg = error.message
    }
    
    ElMessage.error(errorMsg)
  } finally {
    submitting.value = false
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('testcase.deleteConfirm'), t('user.deleteTitle'), {
      confirmButtonText: t('common.confirm'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
      buttonSize: 'default'
    })
    await deleteTestCase(row.id)
    ElMessage.success(t('testcase.deleteSuccess'))
    loadData()
    loadModuleList()
    eventBus.emit('testcases-changed')
  } catch (error) {
    // 用户取消
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning(t('testcase.selectCasesToDelete'))
    return
  }
  
  try {
    await ElMessageBox.confirm(
      t('testcase.batchDeleteConfirm', { count: selectedRows.value.length }), 
      t('common.batchDeleteConfirmTitle'), 
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        type: 'warning',
        buttonSize: 'default'
      }
    )
    
    // 开始批量删除
    batchDeleting.value = true
    deleteProgress.value = 0
    deleteStatusText.value = '正在创建删除任务...'
    batchDeleteDialogVisible.value = true
    
    // 调用批量删除API
    const ids = selectedRows.value.map(row => row.id)
    const res = await batchDeleteTestCases(ids)
    
    const taskId = res.data?.task_id
    if (!taskId) {
      throw new Error('未获取到删除任务ID')
    }
    
    // 轮询删除进度
    const deleteResult = await pollDeleteProgress(taskId)
    
    const { success_count, failed_count, failed_items } = deleteResult
    
    // 根据删除结果给出提示
    if (failed_count === 0) {
      ElMessage.success(t('testcase.batchDeleteSuccess', { count: success_count }))
    } else if (success_count > 0) {
      const failedNumbers = failed_items.map(item => item.id).join(', ')
      ElMessage.warning(`成功删除 ${success_count} 个用例，${failed_count} 个删除失败（ID: ${failedNumbers}）`)
    } else {
      ElMessage.error('所有用例删除失败，请重试')
    }
    
    selectedRows.value = []
    loadData()
    loadModuleList()
    eventBus.emit('testcases-changed')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || t('common.deleteRetry'))
    }
  } finally {
    batchDeleteDialogVisible.value = false
    batchDeleting.value = false
    deleteProgress.value = 0
    deleteStatusText.value = ''
  }
}

// 轮询删除进度
const pollDeleteProgress = (taskId) => {
  return new Promise((resolve, reject) => {
    const token = localStorage.getItem('token')
    const poll = () => {
      fetch(`/api/testcases/batch-delete/${taskId}/progress`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(res => {
          if (res.code !== 200) {
            reject(new Error(res.message || '查询进度失败'))
            return
          }
          const data = res.data
          // 更新UI进度
          deleteProgress.value = data.progress || 0
          deleteStatusText.value = data.message || ''
          
          if (data.status === 'done' || data.status === 'error') {
            resolve(data)
          } else {
            setTimeout(poll, 1000)  // 每秒轮询一次
          }
        })
        .catch(err => {
          console.error('轮询删除进度失败:', err)
          setTimeout(poll, 3000)
        })
    }
    poll()
  })
}

// 显示导入对话框
const showImportDialog = () => {
  // 新格式不需要选择用例库，从Excel读取
  importDialogVisible.value = true
  importFile.value = null
  importOverwrite.value = false
  importProgress.value = 0
  importStatus.value = ''
  importStatusText.value = ''
  importStats.value = { created: 0, updated: 0, skipped: 0, current: 0, total: 0 }
  importErrors.value = []
}

// 导入对话框关闭时清理
const handleImportDialogClosed = () => {
  importFile.value = null
  importOverwrite.value = false
  importProgress.value = 0
  importing.value = false
  importStatus.value = ''
  importStatusText.value = ''
  importStats.value = { created: 0, updated: 0, skipped: 0, current: 0, total: 0 }
  importErrors.value = []
  if (importUploadRef.value) {
    importUploadRef.value.clearFiles()
  }
}

// 下载模板（包含当前项目组的用例库和模块信息）
const downloadTemplate = async () => {
  try {
    // 传递当前项目组ID以获取相关的用例库和模块信息
    let url = '/api/testcases/template/download'
    if (currentTeam.value?.id) {
      url += `?team_id=${currentTeam.value.id}`
    }
    
    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error(t('testcase.downloadFailed2'))
    }
    
    const blob = await response.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', t('testcase.templateFileName'))
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(downloadUrl)
    
    ElMessage.success(t('testcase.templateDownloadSuccess'))
  } catch (error) {
    ElMessage.error(t('testcase.templateDownloadFailed'))
  }
}

// 处理导入文件选择
const handleImportFileChange = (file) => {
  const maxSize = 100 * 1024 * 1024 // 100MB
  if (file.size > maxSize) {
    ElMessage.error(t('testcase.fileSizeLimit'))
    importUploadRef.value?.clearFiles()
    return
  }
  importFile.value = file.raw
}

// 处理导入文件移除
const handleImportFileRemove = () => {
  importFile.value = null
}

// 提交导入
const handleImportSubmit = async () => {
  if (!importFile.value) {
    ElMessage.warning(t('testcase.selectImportFile'))
    return
  }
  
  importing.value = true
  importProgress.value = 0
  importStatus.value = 'uploading'
  importStatusText.value = t('testcase.uploadingFile')
  importStats.value = { created: 0, updated: 0, skipped: 0, current: 0, total: 0 }
  importErrors.value = []
  
  try {
    const formData = new FormData()
    formData.append('file', importFile.value)
    formData.append('overwrite', importOverwrite.value)
    if (currentTeam.value?.id) {
      formData.append('team_id', currentTeam.value.id)
    }
    if (importAutoCreateModule.value) {
      formData.append('auto_create_module', 'true')
    }
    
    // 第一步：上传文件，获取task_id（秒级返回）
    const uploadResult = await new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) {
          importProgress.value = Math.round((e.loaded / e.total) * 100)
        }
      }
      
      xhr.upload.onload = () => {
        importProgress.value = 100
        importStatus.value = 'parsing'
        importStatusText.value = t('testcase.uploadDoneParsing')
      }
      
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText))
          } catch {
            reject(new Error(t('common.serverError')))
          }
        } else {
          try {
            const err = JSON.parse(xhr.responseText)
            reject(new Error(err.detail || err.message || t('testcase.importFailed')))
          } catch {
            reject(new Error(t('common.serverError') + ` (${xhr.status})`))
          }
        }
      }
      
      xhr.onerror = () => reject(new Error(t('common.networkError')))
      xhr.ontimeout = () => reject(new Error(t('common.requestTimeout')))
      xhr.timeout = 120000  // 上传超时2分钟足够
      
      xhr.open('POST', '/api/testcases/import')
      xhr.setRequestHeader('Authorization', `Bearer ${localStorage.getItem('token')}`)
      xhr.send(formData)
    })
    
    const taskId = uploadResult?.data?.task_id
    if (!taskId) {
      throw new Error('未获取到导入任务ID')
    }
    
    // 第二步：轮询进度直到完成
    const finalResult = await pollImportProgress(taskId)
    
    if (finalResult.status === 'error') {
      importProgress.value = 0
      importStatus.value = ''
      ElMessage.error(finalResult.message || t('testcase.importFailed'))
    } else if (finalResult.status === 'done') {
      importStatus.value = ''
      const { created, skipped, errors, skipped_cases } = finalResult.result || finalResult
      let message = `导入完成：新建 ${created} 个`
      if (skipped > 0) message += `，跳过 ${skipped} 个`
      
      // 合并错误和跳过的信息
      const allMessages = []
      if (errors && errors.length > 0) {
        errors.forEach(err => allMessages.push(`错误: ${err}`))
      }
      if (skipped_cases && skipped_cases.length > 0) {
        skipped_cases.forEach(name => allMessages.push(`跳过: ${name}`))
      }
      
      if (allMessages.length > 0) {
        importErrors.value = allMessages
        ElMessage.warning(message + '，有错误/跳过项请查看详情')
      } else {
        ElMessage.success(message)
        importDialogVisible.value = false
      }
      loadData()
      loadModuleList()
      loadTeamProjects()
      eventBus.emit('testcases-changed')
    }
  } catch (error) {
    console.error('导入错误:', error)
    importProgress.value = 0
    importStatus.value = ''
    ElMessage.error(t('testcase.importFailed') + ': ' + (error.message || t('common.unknown')))
  } finally {
    importing.value = false
  }
}

// 轮询导入进度
const pollImportProgress = (taskId) => {
  return new Promise((resolve, reject) => {
    const token = localStorage.getItem('token')
    const poll = () => {
      fetch(`/api/testcases/import/${taskId}/progress`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(res => {
          if (res.code !== 200) {
            reject(new Error(res.message || '查询进度失败'))
            return
          }
          const data = res.data
          // 更新UI进度
          handlePollEvent(data)
          
          if (data.status === 'done' || data.status === 'error') {
            resolve(data)
          } else {
            setTimeout(poll, 1000)  // 每秒轮询一次
          }
        })
        .catch(err => {
          console.error('轮询进度失败:', err)
          // 网络错误时重试，不立即失败
          setTimeout(poll, 3000)
        })
    }
    poll()
  })
}

// 处理轮询进度事件
const handlePollEvent = (data) => {
  switch (data.status) {
    case 'parsing':
      importStatus.value = 'parsing'
      importStatusText.value = data.message
      break
    case 'importing':
      importStatus.value = 'importing'
      importStatusText.value = data.message
      importProgress.value = data.progress || 0
      if (data.total) {
        importStats.value = {
          created: data.created || 0,
          updated: data.updated || 0,
          skipped: data.skipped || 0,
          current: data.current || 0,
          total: data.total || 0
        }
      }
      break
    case 'committing':
      importStatus.value = 'committing'
      importStatusText.value = data.message
      importProgress.value = 100
      break
    case 'done':
      importStatus.value = ''
      importProgress.value = 100
      break
    case 'error':
      importStatus.value = ''
      importStatusText.value = data.message || '导入失败'
      break
  }
}

const handleExport = async () => {
  if (!currentProjectId.value) {
    ElMessage.warning(t('testcase.selectProject'))
    return
  }
  
  containerLoading.value = true
  exporting.value = true
  try {
    // 根据选择的模块导出
    const params = { project_id: currentProjectId.value }
    
    // 如果选择了模块，添加模块筛选
    if (selectedModulePath.value) {
      params.module = selectedModulePath.value
    }
    
    await exportTestCases(params.project_id, params)
    
    // 提示导出范围
    let exportRange = selectedModulePath.value || t('testcase.exportAll')
    ElMessage.success(t('testcase.exportedModule', { module: exportRange }))
  } catch (error) {
    ElMessage.error(t('common.failed'))
  } finally {
    exporting.value = false
    containerLoading.value = false
  }
}

// 跳转到用例评审页面
const goToReview = () => {
  router.push('/review-plans')
}

// 处理表格选择变化
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 拖拽排序处理函数（用例行拖拽）
const handleRowDragStart = (event, index, row) => {
  draggedRow.value = row
  draggedRowIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  
  // 设置拖拽数据
  event.dataTransfer.setData('text/plain', row.id)
  
  // 添加拖拽样式到整行
  setTimeout(() => {
    const tr = event.target.closest('tr')
    if (tr) {
      tr.classList.add('dragging')
    }
  }, 0)
}

const handleRowDragOver = (event, index) => {
  event.preventDefault()
  event.dataTransfer.dropEffect = 'move'
  
  if (draggedRowIndex.value === index) {
    return
  }
  
  // 添加悬停样式
  const tr = event.target.closest('tr')
  if (tr && !tr.classList.contains('dragging')) {
    tr.classList.add('drag-over')
  }
}

const handleRowDragLeave = (event) => {
  const tr = event.target.closest('tr')
  if (tr) {
    tr.classList.remove('drag-over')
  }
}

// 为表格行添加类名，用于绑定拖拽事件
const getRowClassName = ({ row, rowIndex }) => {
  return 'draggable-row'
}

// 在 mounted 后为表格行添加拖拽事件监听
onMounted(() => {
  // ... 其他 mounted 代码
  
  // 使用事件委托为表格行添加拖拽事件
  nextTick(() => {
    const tableEl = document.querySelector('.el-table__body-wrapper tbody')
    if (tableEl) {
      tableEl.addEventListener('dragover', (e) => {
        const tr = e.target.closest('tr.draggable-row')
        if (tr && draggedRow.value) {
          e.preventDefault()
          e.dataTransfer.dropEffect = 'move'
          
          // 移除所有 drag-over 样式
          document.querySelectorAll('.drag-over').forEach(el => el.classList.remove('drag-over'))
          
          // 添加到当前行
          if (!tr.classList.contains('dragging')) {
            tr.classList.add('drag-over')
          }
        }
      })
      
      tableEl.addEventListener('drop', async (e) => {
        const tr = e.target.closest('tr.draggable-row')
        if (tr && draggedRow.value) {
          e.preventDefault()
          
          // 获取目标行的索引和数据
          const targetIndex = Array.from(tr.parentNode.children).indexOf(tr)
          const targetRow = tableData.value[targetIndex]
          
          if (targetRow) {
            await handleRowDrop(e, targetIndex, targetRow)
          }
        }
      })
      
      tableEl.addEventListener('dragleave', (e) => {
        const tr = e.target.closest('tr.draggable-row')
        if (tr && e.target === tr) {
          tr.classList.remove('drag-over')
        }
      })
    }
  })
})

const handleRowDrop = async (event, targetIndex, targetRow) => {
  event.preventDefault()
  event.stopPropagation()
  
  // 移除悬停样式
  const tr = event.target.closest('tr')
  if (tr) {
    tr.classList.remove('drag-over')
  }
  
  if (!draggedRow.value || draggedRow.value.id === targetRow.id) {
    return
  }
  
  // 只检查主模块是否相同（允许跨子模块拖拽）
  const draggedModule = draggedRow.value.module || ''
  const targetModule = targetRow.module || ''
  
  console.log('拖拽检查:', {
    draggedModule,
    targetModule,
    sameModule: draggedModule === targetModule
  })
  
  if (draggedModule !== targetModule) {
    ElMessage.warning(t('testcase.sameModuleSortOnly'))
    return
  }
  
  try {
    loading.value = true
    
    // 调用后端 API 更新排序
    const res = await reorderTestCase({
      testcase_id: draggedRow.value.id,
      target_testcase_id: targetRow.id,
      target_position: targetIndex,
      insert_before: draggedRowIndex.value > targetIndex
    })
    
    if (res.code === 200) {
      ElMessage.success(t('testcase.sortSuccess'))
      // 重新加载数据
      await loadData()
    } else {
      ElMessage.error(res.message || t('testcase.sortFailed'))
    }
  } catch (error) {
    console.error('排序失败:', error)
    ElMessage.error(t('testcase.sortFailed'))
  } finally {
    loading.value = false
  }
}

const handleRowDragEnd = (event) => {
  // 移除所有拖拽相关样式
  const draggingRows = document.querySelectorAll('.dragging')
  draggingRows.forEach(row => {
    row.classList.remove('dragging')
  })
  
  const dragOverRows = document.querySelectorAll('.drag-over')
  dragOverRows.forEach(row => {
    row.classList.remove('drag-over')
  })
  
  draggedRow.value = null
  draggedRowIndex.value = null
  dropTargetIndex.value = null
}

// 全选当前模块
const tableRef = ref(null)
const { scrollToTop } = useScrollToTop(tableRef, '.main-content')

// 复制后高亮定位
const newlyCopiedId = ref(null)
let _copiedFlashTimer = null

const scrollToCopiedRow = async (newId, newTestCase) => {
  const targetModule = newTestCase?.module || null

  // 切换到新用例所在模块，重置到第1页
  page.value = 1
  if (targetModule) {
    selectedModulePath.value = targetModule
  }
  await loadData()

  // 在当前页查找
  let row = tableData.value.find(r => r.id === newId)

  // 找不到则继续翻页（该模块用例超过一页）
  if (!row && total.value > size.value) {
    const totalPages = Math.ceil(total.value / size.value)
    for (let p = 2; p <= totalPages && !row; p++) {
      page.value = p
      await loadData()
      row = tableData.value.find(r => r.id === newId)
    }
  }

  if (!row) return

  // 等 DOM 渲染完成
  await nextTick()
  await new Promise(resolve => requestAnimationFrame(resolve))

  if (!tableRef.value) return

  const rowIndex = tableData.value.findIndex(r => r.id === newId)
  const allRows = tableRef.value.$el.querySelectorAll('tbody tr.el-table__row')
  const rowEl = allRows[rowIndex] || null

  if (rowEl) {
    rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' })

    // 用 JS 直接控制背景色闪烁，绕过 CSS 优先级问题
    const flashColor = '#ede9fe'  // 浅紫色
    const steps = [flashColor, '', flashColor, '', flashColor, '', flashColor, '', '']
    const stepInterval = 400  // 每步 400ms，总时长约 3.2s，足够浏览器重绘
    let i = 0
    const flash = setInterval(() => {
      const tds = Array.from(rowEl.querySelectorAll('td'))
      tds.forEach(td => {
        td.style.setProperty('background-color', steps[i] || '', 'important')
      })
      i++
      if (i >= steps.length) clearInterval(flash)
    }, stepInterval)

    if (_copiedFlashTimer) clearTimeout(_copiedFlashTimer)
    _copiedFlashTimer = setTimeout(() => {
      Array.from(rowEl.querySelectorAll('td')).forEach(td => {
        td.style.backgroundColor = ''
      })
      newlyCopiedId.value = null
    }, 400 * 9 + 200)
  }
}

const handlePageOrSizeChange = async () => {
  await loadData()
  await nextTick()
  scrollToTop()
}

const handleSelectAll = async () => {
  try {
    // 构建查询参数，与 loadData 保持一致
    const params = {}

    // 添加用例库ID参数
    if (currentProjectIds.value.length > 0) {
      params.project_ids = currentProjectIds.value.join(',')
    }

    // 添加模块筛选
    if (selectedModulePath.value) {
      params.module = selectedModulePath.value
    }

    // 添加用例类型筛选
    if (selectedCaseType.value) {
      params.case_type = selectedCaseType.value
    }

    // 添加关键词搜索
    if (searchKeyword.value) {
      params.keyword = regexMode.value ? `regex:${searchKeyword.value}` : searchKeyword.value
    }

    // 添加排序参数
    if (sortProp.value && sortOrder.value) {
      params.sort_by = sortProp.value
      params.sort_order = sortOrder.value
    }

    // 添加状态筛选
    if (selectedStatus.value) {
      params.status = selectedStatus.value
    }

    // 添加等级筛选
    if (selectedLevel.value) {
      params.level_in = selectedLevel.value
    }

    // 添加自动化筛选
    if (selectedAutomation.value) {
      params.automation = selectedAutomation.value
    }

    // 添加用户反馈筛选
    if (hasFeedbackFilter.value !== null) {
      params.has_feedback = hasFeedbackFilter.value
    }

    // 添加归档来源筛选
    if (selectedArchiveSource.value) {
      params.archive_source = selectedArchiveSource.value
    }

    // 添加创建人/更新人/标签筛选（后端 all-ids 接口支持，确保全选跨页准确）
    if (selectedCreator.value) {
      params.creator_name = selectedCreator.value
    }
    if (selectedUpdater.value) {
      params.updater_name = selectedUpdater.value
    }
    if (selectedTag.value) {
      params.tag = selectedTag.value
    }

    // 调用专用接口获取所有 ID（不受分页限制）
    const res = await getAllTestCaseIds(params)
    const allRecords = res.data.records || []
    const allIds = allRecords.map(r => r.id)

    nextTick(() => {
      if (tableRef.value) {
        tableRef.value.clearSelection()

        // 勾选当前页所有行（视觉反馈），selectedRows 存储全量轻量对象
        tableData.value.forEach(row => {
          tableRef.value.toggleRowSelection(row, true)
        })
        selectedRows.value = allRecords

        // 显示模块名称
        let displayName = selectedModulePath.value || t('common.all')
        const pidPrefixMatch = displayName.match(/^p\d+\/(.+)$/)
        if (pidPrefixMatch) {
          displayName = pidPrefixMatch[1]
        }
        ElMessage.success(t('testcase.selectedModuleCases', { module: displayName, count: allRecords.length }))
      }
    })
  } catch (error) {
    ElMessage.error(t('testcase.getCaseFailed'))
  }
}

// 创建测试计划
const handleCreatePlan = () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning('请先选择用例')
    return
  }
  
  // 验证所有选中的用例是否都是已评审状态
  const nonReviewedCases = selectedRows.value.filter(row => row.status !== 'REVIEWED')
  if (nonReviewedCases.length > 0) {
    const caseNumbers = nonReviewedCases.slice(0, 5).map(row => row.case_number).join('、')
    const suffix = nonReviewedCases.length > 5 ? ` 等${nonReviewedCases.length}条` : ''
    ElMessage.warning(`选中的用例中包含非已评审状态的用例（${caseNumbers}${suffix}），只有已评审的用例才能创建测试计划`)
    return
  }
  
  // 收集选中用例的ID
  const testcaseIds = selectedRows.value.map(row => row.id)
  
  // 跳转到测试计划页面，传递用例ID
  router.push({
    path: '/testplans',
    query: {
      action: 'create',
      testcase_ids: testcaseIds.join(',')
    }
  })
}

// 显示批量编辑对话框
const showBatchEditDialog = () => {
  // 重置表单
  batchEditForm.updateLevel = false
  batchEditForm.level = ''
  batchEditForm.updateAutomation = false
  batchEditForm.automation = ''
  batchEditForm.updateStatus = false
  batchEditForm.status = ''
  batchEditForm.updateTags = false
  batchEditForm.tags = ''
  batchEditForm.updateArchiveSource = false
  batchEditForm.archive_source = ''
  batchEditForm.updateModule = false
  batchEditForm.module = ''
  
  // 自动检测选中用例的公共用例库，用于默认目标项目
  const projectIds = [...new Set(selectedRows.value.map(r => r.primary_project_id).filter(id => id))]
  batchEditForm.targetProjectId = projectIds.length === 1 ? projectIds[0] : null
  batchTargetModuleTree.value = []
  if (batchEditForm.targetProjectId) {
    handleBatchTargetProjectChange(batchEditForm.targetProjectId)
  }
  
  batchEditVisible.value = true
}

// 批量编辑时切换目标用例库，加载目标模块树
const handleBatchTargetProjectChange = async (projectId) => {
  batchEditForm.module = ''
  batchTargetModuleTree.value = []
  if (!projectId) return
  try {
    const res = await getModuleTree(projectId)
    if (res.data) {
      const treeData = buildFormTreeData(res.data)
      batchTargetModuleTree.value = treeData
    }
  } catch (error) {
    console.error('加载目标模块树失败:', error)
  }
}

// 批量编辑
const handleBatchEdit = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning(t('testcase.selectCasesToEdit'))
    return
  }
  
  // 检查是否至少选择了一个字段
  if (!batchEditForm.updateLevel && !batchEditForm.updateAutomation && 
      !batchEditForm.updateStatus && !batchEditForm.updateTags &&
      !batchEditForm.updateArchiveSource && !batchEditForm.updateModule) {
    ElMessage.warning(t('testcase.selectFieldToEdit'))
    return
  }
  
  batchEditing.value = true
  try {
    const ids = selectedRows.value.map(row => row.id)
    
    // 先处理模块变更（无论同库还是跨库，都走 batch-move 确保重新编号）
    if (batchEditForm.updateModule) {
      if (!batchEditForm.targetProjectId) {
        ElMessage.warning('请选择目标用例库')
        batchEditing.value = false
        return
      }
      await batchMoveTestCases({
        ids,
        target_project_id: batchEditForm.targetProjectId,
        target_module: batchEditForm.module
      })
    }
    
    // 再处理其他字段变更
    const updates = {}
    if (batchEditForm.updateLevel) updates.level = batchEditForm.level
    if (batchEditForm.updateAutomation) updates.automation = batchEditForm.automation
    if (batchEditForm.updateStatus) updates.status = batchEditForm.status
    if (batchEditForm.updateTags) updates.tags = batchEditForm.tags ? JSON.stringify(batchEditForm.tags.split(/[,，]/).map(t => t.trim()).filter(t => t)) : null
    if (batchEditForm.updateArchiveSource) updates.archive_source = batchEditForm.archive_source || null
    
    if (Object.keys(updates).length > 0) {
      await batchUpdateTestCases({ ids, updates })
    }
    
    ElMessage.success(t('testcase.batchUpdateSuccess', { count: ids.length }))
    batchEditVisible.value = false
    loadData()
    loadModuleList()
    eventBus.emit('testcases-changed')
  } catch (error) {
    ElMessage.error(t('testcase.batchUpdateFailed'))
  } finally {
    batchEditing.value = false
  }
}

// 批量导出选中的用例
const handleBatchExport = async () => {
  if (selectedRows.value.length === 0) {
    ElMessage.warning(t('testcase.selectCasesToExport'))
    return
  }
  
  exporting.value = true
  try {
    const ids = selectedRows.value.map(row => row.id)
    await exportTestCasesByIds(currentProjectId.value, ids)
    ElMessage.success(t('testcase.exportedCount', { count: ids.length }))
  } catch (error) {
    ElMessage.error(t('testcase.exportFailed'))
  } finally {
    exporting.value = false
  }
}

// 标签筛选
const handleTagFilter = (tag) => {
  selectedTag.value = tag
  page.value = 1
  loadData()
}

const handleArchiveSourceFilter = (source) => {
  selectedArchiveSource.value = source
  page.value = 1
  loadData()
}

const handleLinkZmind = async (row) => {
  currentTestCaseId.value = row.id
  linkDialogVisible.value = true
  addLinkForm.zmind_issue_id = ''
  addLinkForm.zmind_issue_subject = ''
  addLinkForm.zmind_issue_status = ''
  addLinkForm.zmind_issue_severity = ''
  
  // 重置筛选器
  severityFilter.value = ''
  statusFilter.value = ''
  
  // 加载已关联的PR（不再自动刷新，由用户手动点击刷新按钮）
  try {
    const res = await getZmindLinks(row.id)
    zmindLinks.value = res.data || []
  } catch (error) {
    console.error('加载关联PR失败:', error)
    ElMessage.error(t('testcase.linkDialog.loadFailed'))
    zmindLinks.value = []
  }
}

// 刷新当前对话框内的PR列表
const handleRefreshPRLinks = async () => {
  if (!currentTestCaseId.value || refreshingPRLinks.value) return
  
  refreshingPRLinks.value = true
  try {
    const res = await refreshTestcasePRStatus(currentTestCaseId.value)
    if (res.code === 200 && res.data) {
      zmindLinks.value = res.data
      ElMessage.success(t('testcase.linkDialog.refreshSuccess'))
    }
  } catch (error) {
    console.error('刷新PR失败:', error)
    ElMessage.error(t('testcase.linkDialog.refreshFailed'))
  } finally {
    refreshingPRLinks.value = false
  }
}

// 带重试机制的getZmindIssue函数
const getZmindIssueWithRetry = async (issueId, maxRetries = 2, delay = 1000) => {
  let lastError
  
  for (let i = 0; i <= maxRetries; i++) {
    try {
      // 添加超时处理（5分钟）
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5 * 60 * 1000) // 5分钟超时
      
      // 注意：这里需要修改getZmindIssue函数，使其支持AbortController
      // 暂时使用普通调用，后续可以优化
      const response = await getZmindIssue(issueId)
      
      clearTimeout(timeoutId)
      return response
    } catch (error) {
      lastError = error
      
      if (i < maxRetries) {
        console.warn(`获取PR ${issueId} 状态失败，${delay}ms后重试 (${i + 1}/${maxRetries})`, error)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
  }
  
  throw lastError
}

// 刷新所有PR的状态信息
const refreshAllPRStatus = async () => {
  const updatePromises = zmindLinks.value.map(async (link) => {
    try {
      link.refreshing = true
      
      const response = await getZmindIssueWithRetry(link.zmind_issue_id, 1, 500)
      
      if (response.code === 200 && response.data) {
        // 更新本地数据（只更新 subject 和 status，保留 severity）
        link.zmind_issue_subject = response.data.subject
        link.zmind_issue_status = response.data.status || ''
        
        // 更新数据库（只更新 subject 和 status）
        await updateZmindLink(currentTestCaseId.value, link.id, {
          zmind_issue_subject: link.zmind_issue_subject,
          zmind_issue_status: link.zmind_issue_status
        })
      }
    } catch (error) {
      // 静默处理，不阻塞对话框显示
    } finally {
      link.refreshing = false
    }
  })
  
  await Promise.all(updatePromises)
}

// 刷新单个PR的状态信息（通过后端接口刷新整个测试用例的PR）
const handleRefreshLinkStatus = async (link) => {
  try {
    link.refreshing = true
    const res = await refreshTestcasePRStatus(currentTestCaseId.value)
    
    if (res.code === 200 && res.data) {
      zmindLinks.value = res.data
      ElMessage.success(t('testcase.prStatusUpdated'))
    } else {
      ElMessage.warning(t('testcase.prStatusFetchFailed'))
    }
  } catch (error) {
    ElMessage.error(t('testcase.prRefreshFailed'))
  } finally {
    link.refreshing = false
  }
}

// 加载历史记录
const loadHistory = async (testcaseId) => {
  historyLoading.value = true
  try {
    const res = await getTestCaseHistory(testcaseId)
    if (res.code === 200) {
      historyList.value = res.data
      console.log('历史记录加载成功:', historyList.value)
    }
  } catch (error) {
    console.error('加载历史记录失败:', error)
    ElMessage.error(t('testcase.loadHistoryFailed'))
  } finally {
    historyLoading.value = false
  }
}

// 加载执行历史
const loadExecutionHistory = async (testcaseId) => {
  executionHistoryLoading.value = true
  try {
    const res = await getTestCaseExecutionHistory(testcaseId)
    if (res.code === 200) {
      executionHistoryList.value = res.data
      console.log('执行历史加载成功:', executionHistoryList.value)
    }
  } catch (error) {
    console.error('加载执行历史失败:', error)
    ElMessage.error(t('testcase.loadExecutionHistoryFailed'))
  } finally {
    executionHistoryLoading.value = false
  }
}

// 查看详情
const handleViewDetail = async (row) => {
  detailData.value = { ...row }
  activeTabName.value = 'basic'  // 每次打开都重置到基本信息标签页
  detailDialogVisible.value = true
  historyList.value = []
  executionHistoryList.value = []
  detailAttachments.value = []
  // 加载历史记录、执行历史和附件
  await Promise.all([
    loadHistory(row.id),
    loadExecutionHistory(row.id),
    loadDetailAttachments(row.id)
  ])
}

// 移除反馈提示（二次确认）
const confirmClearFeedback = () => {
  ElMessageBox.confirm(
    '确定移除反馈提示吗？移除后可在"查看历史"中查看反馈记录。',
    '确认移除',
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await clearTestCaseFeedback(detailData.value.id)
      detailData.value.feedback = null
      feedbackViewDialogVisible.value = false
      // 同步更新列表中的数据
      const idx = tableData.value.findIndex(tc => tc.id === detailData.value.id)
      if (idx !== -1) tableData.value[idx].feedback = null
      ElMessage.success('反馈提示已移除')
    } catch (error) {
      ElMessage.error('移除失败')
    }
  }).catch(() => {})
}

// 切换详情（上一条/下一条），不清空数据避免抖动
const switchDetail = async (row) => {
  detailData.value = { ...row }
  // 异步加载附属数据，不清空旧数据，等新数据到了再替换
  await Promise.all([
    loadHistory(row.id),
    loadExecutionHistory(row.id),
    loadDetailAttachments(row.id)
  ])
}

// 当前详情在表格中的索引
const currentDetailIndex = computed(() => {
  if (!detailData.value) return -1
  return tableData.value.findIndex(item => item.id === detailData.value.id)
})

// 上一条
const handlePrevDetail = () => {
  const idx = currentDetailIndex.value
  if (idx > 0) {
    switchDetail(tableData.value[idx - 1])
  }
}

// 下一条
const handleNextDetail = () => {
  const idx = currentDetailIndex.value
  if (idx < tableData.value.length - 1) {
    switchDetail(tableData.value[idx + 1])
  }
}

// 加载详情弹窗的附件列表
const loadDetailAttachments = async (testCaseId) => {
  detailAttachmentsLoading.value = true
  try {
    const res = await getAttachments(testCaseId)
    detailAttachments.value = res.data || []
  } catch (error) {
    console.error('加载附件失败:', error)
    detailAttachments.value = []
  } finally {
    detailAttachmentsLoading.value = false
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

// 预览附件
const handlePreviewAttachment = async (att) => {
  const ext = att.file_name.split('.').pop().toLowerCase()
  previewFileName.value = att.file_name
  previewTextContent.value = ''
  
  const imageExts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'svg']
  const textExts = ['txt', 'log', 'json', 'xml', 'csv', 'md', 'html', 'css', 'js', 'ts', 'jsx', 'tsx', 'py', 'bat', 'sh', 'cmd', 'ps1', 'yaml', 'yml', 'toml', 'ini', 'cfg', 'conf', 'env', 'vue', 'java', 'c', 'cpp', 'h', 'go', 'rs', 'rb', 'php', 'sql', 'dockerfile', 'gitignore', 'editorconfig']
  
  if (imageExts.includes(ext)) {
    previewType.value = 'image'
    previewUrl.value = getAttachmentPreviewUrl(att.id)
    previewDialogVisible.value = true
  } else if (ext === 'pdf') {
    previewType.value = 'pdf'
    previewUrl.value = getAttachmentPreviewUrl(att.id)
    previewDialogVisible.value = true
  } else if (textExts.includes(ext)) {
    previewType.value = 'text'
    try {
      const response = await downloadAttachment(att.id)
      // response.data 是 Blob（因为 responseType: 'blob'）
      const blob = response.data instanceof Blob
        ? response.data
        : new Blob([response.data])
      const text = await blob.text()
      previewTextContent.value = text
      previewDialogVisible.value = true
    } catch (error) {
      ElMessage.error('预览失败')
    }
  } else {
    previewType.value = 'other'
    previewDialogVisible.value = true
  }
}

// 处理行点击事件
const handleRowClick = (row, column, event) => {
  // 排除以下列的点击：
  // 1. 操作列（没有property）
  // 2. 多选框列（type为selection）
  // 3. 排序列（拖拽列）
  
  // 检查是否点击了操作列（操作列没有property属性）
  if (!column || !column.property) {
    return
  }
  
  // 检查是否点击了多选框列
  if (column.type === 'selection') {
    return
  }
  
  // 检查是否点击了拖拽手柄
  if (event.target.closest('.drag-handle-wrapper')) {
    return
  }
  
  // 检查是否点击了操作按钮区域
  if (event.target.closest('.operation-buttons')) {
    return
  }
  
  // 其他区域都可以点击进入详情
  handleViewDetail(row)
}

// 从详情对话框编辑
const handleEditFromDetail = () => {
  detailDialogVisible.value = false
  handleEdit(detailData.value)
}

// 复制用例（从列表或详情）
const handleCopy = (row) => {
  isCopyMode.value = true
  // 复制模式：保留原用例 id 用于加载附件，但提交时清除（走创建流程）
  form.id = row.id  // 仅用于在编辑模板中展示 primary_project_id 等已有字段，提交时被忽略
  form.case_number = ''  // 不展示编号
  form.module = row.module || ''
  form.name = row.name
  form.case_type = row.case_type || 'COMMON'
  form.precondition = row.precondition || ''

  // 解析步骤数据
  try {
    const parsed = JSON.parse(row.steps)
    if (Array.isArray(parsed) && parsed.length > 0) {
      form.steps = parsed.map(item => {
        let stepText = String(item.step || '').trim()
        let expectedText = String(item.expected || '').trim()
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(stepText)) {
          stepText = stepText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        while (/^(\d+)(?:[。、]|\.)(?!\d)\s*/.test(expectedText)) {
          expectedText = expectedText.replace(/^(\d+)(?:[。、]|\.)(?!\d)\s*/, '')
        }
        return { step: stepText, expected: expectedText }
      })
    } else {
      form.steps = [{ step: row.steps || '', expected: row.expected_result || '' }]
    }
  } catch (e) {
    form.steps = [{ step: row.steps || '', expected: row.expected_result || '' }]
  }

  form.expected_result = row.expected_result || ''
  form.level = row.level || 'L3'
  form.remarks = row.remarks || ''
  form.automation = row.automation || null
  form.status = 'PENDING'  // 复制的新用例默认为待评审
  form.tags = row.tags ? parseTags(row.tags).join(', ') : ''
  form.archive_source = row.archive_source || ''
  form.primary_project_id = row.primary_project_id || row.project_id

  // 加载该用例库的模块树
  loadFormModuleTree(form.primary_project_id)

  // 复制模式不加载附件（新用例从空附件开始）
  attachments.value = []
  tempAttachments.value = []
  tempFiles.value = []

  dialogVisible.value = true
}

// 从详情对话框复制
const handleCopyFromDetail = () => {
  detailDialogVisible.value = false
  handleCopy(detailData.value)
}

// 处理下拉菜单命令
const handleDropdownCommand = (command, row) => {
  if (command === 'delete') {
    handleDelete(row)
  } else if (command === 'copy') {
    handleCopy(row)
  }
}

// 处理PR ID输入变化，自动获取PR信息
const handleFetchPRInfo = async () => {
  const prId = addLinkForm.zmind_issue_id.trim()
  
  if (!prId) {
    addLinkForm.zmind_issue_subject = ''
    addLinkForm.zmind_issue_status = ''
    addLinkForm.zmind_issue_severity = ''
    return
  }
  
  try {
    fetchingPRInfo.value = true
    
    const response = await getZmindIssue(prId)
    
    if (response.code === 200 && response.data) {
      addLinkForm.zmind_issue_subject = response.data.subject
      addLinkForm.zmind_issue_status = response.data.status || ''
      addLinkForm.zmind_issue_severity = response.data.severity || ''
      ElMessage.success(t('testcase.prInfoFetched'))
    } else {
      ElMessage.warning(t('testcase.prInfoNotFound'))
      addLinkForm.zmind_issue_subject = ''
      addLinkForm.zmind_issue_status = ''
      addLinkForm.zmind_issue_severity = ''
    }
  } catch (error) {
    console.error('获取PR信息失败:', error)
    ElMessage.error(t('testcase.prInfoFetchFailed'))
    addLinkForm.zmind_issue_subject = ''
    addLinkForm.zmind_issue_status = ''
    addLinkForm.zmind_issue_severity = ''
  } finally {
    fetchingPRInfo.value = false
  }
}

const handleAddLink = async () => {
  if (!addLinkForm.zmind_issue_id || !addLinkForm.zmind_issue_subject) {
    ElMessage.warning(t('testcase.linkDialog.fillComplete'))
    return
  }
  
  try {
    await linkZmindIssue(currentTestCaseId.value, {
      test_case_id: currentTestCaseId.value,
      zmind_issue_id: addLinkForm.zmind_issue_id,
      zmind_issue_subject: addLinkForm.zmind_issue_subject,
      zmind_issue_status: addLinkForm.zmind_issue_status,
      zmind_issue_severity: addLinkForm.zmind_issue_severity
    })
    ElMessage.success(t('testcase.linkDialog.linkSuccess'))
    
    // 重新加载关联列表
    const res = await getZmindLinks(currentTestCaseId.value)
    zmindLinks.value = res.data
    
    // 刷新列表以更新统计数字
    loadData()
    
    // 清空表单（放在最后，确保所有操作完成后再清空）
    addLinkForm.zmind_issue_id = ''
    addLinkForm.zmind_issue_subject = ''
    addLinkForm.zmind_issue_status = ''
    addLinkForm.zmind_issue_severity = ''
  } catch (error) {
    const errorMsg = error.response?.data?.detail || t('testcase.linkDialog.linkFailed')
    ElMessage.error(errorMsg)
  }
}

const handleDialogClosed = () => {
  // 对话框关闭后,移除所有按钮的焦点
  if (document.activeElement instanceof HTMLElement) {
    document.activeElement.blur()
  }
  
  // 重置筛选器
  severityFilter.value = ''
  statusFilter.value = ''
  
  // 退出复制模式
  isCopyMode.value = false
  
  // 不再自动刷新，由具体操作决定是否需要刷新
}

const handleRemoveLink = async (link) => {
  try {
    await ElMessageBox.confirm(t('testcase.linkDialog.confirmRemove'), t('testcase.linkDialog.removeTitle'), {
      confirmButtonText: t('testcase.linkDialog.confirm'),
      cancelButtonText: t('testcase.linkDialog.cancel'),
      type: 'warning'
    })
    
    await unlinkZmindIssue(currentTestCaseId.value, link.id)
    ElMessage.success(t('testcase.linkDialog.removeSuccess'))
    
    // 重新加载关联列表
    const res = await getZmindLinks(currentTestCaseId.value)
    zmindLinks.value = res.data
    
    // 刷新列表以更新统计数字
    loadData()
  } catch (error) {
    // 用户取消
  }
}

// 监听用例库列表变化，自动应用偏好
watch(teamProjectList, (list) => {
  if (list && list.length > 0) {
    applyPreference(list)
  }
})

onMounted(async () => {
  loadUserPreferences()
  loadColumnSettings()
  // 刷新页面时 teamProjects 可能还没加载完，需要等待
  if (teamProjectList.value.length === 0 && currentTeam.value) {
    await loadTeamProjects()
    if (teamProjectList.value.length > 0) {
      applyPreference(teamProjectList.value)
    }
  }
  // 并行加载数据和模块列表
  loadData()
  loadModuleList()
  nextTick(() => {
    updateTableHeight()
    if (tableContainerRef.value && typeof ResizeObserver !== 'undefined') {
      tableResizeObserver = new ResizeObserver(updateTableHeight)
      tableResizeObserver.observe(tableContainerRef.value)
    }
  })
  window.addEventListener('resize', updateTableHeight)
})

// 模块变更时标记需要刷新
let _needsRefreshOnActivate = false
const _onModulesChanged = () => {
  _needsRefreshOnActivate = true
}
eventBus.on('modules-changed', _onModulesChanged)

// keep-alive 激活时，如果模块有变更则刷新数据
onActivated(() => {
  if (_needsRefreshOnActivate) {
    _needsRefreshOnActivate = false
    loadData()
    loadModuleList()
  }
})

// 监听项目组变化，重新加载数据
watch(currentTeam, async (newTeam, oldTeam) => {
  if (newTeam && newTeam.id !== oldTeam?.id) {
    // 项目组变化时，重置用例库选择和模块状态
    resetPreference()
    selectedModulePath.value = ''
    expandedModulePaths.value = new Set()
    // 等待用例库列表加载完成后再加载数据
    await loadTeamProjects()
    loadData()
    loadModuleList()
  }
}, { immediate: false })

onUnmounted(() => {
  window.removeEventListener('resize', updateTableHeight)
  if (tableResizeObserver) tableResizeObserver.disconnect()
  eventBus.off('modules-changed', _onModulesChanged)
})
</script>

<style scoped>
/* 统计面板样式 */
.statistics-card {
  margin-bottom: 16px;
  border-radius: 8px;
  border: 1px solid #e4e7ed;
  flex-shrink: 0;
}

/* 统计栏 - 紧凑设计 */
.statistics-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 20px;
  margin-bottom: 12px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
}

.stat-compact {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-compact .stat-label {
  font-size: 15px;
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
  display: flex;
  align-items: center;
}

.stat-compact .stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #409eff;
  display: flex;
  align-items: center;
}

.stat-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 4px;
}

.stat-tags .el-tag {
  font-size: 14px;
  padding: 5px 12px;
  border: none;
  display: inline-flex;
  align-items: center;
}

.stat-divider {
  width: 1px;
  height: 28px;
  background: #e2e8f0;
}

/* 拖拽排序样式 */
.drag-handle-wrapper {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: move;
  padding: 4px;
  user-select: none;
}

.drag-handle {
  font-size: 18px;
  color: #909399;
  transition: color 0.3s;
  pointer-events: none;
}

.drag-handle-wrapper:hover .drag-handle {
  color: #409EFF;
}

:deep(.dragging) {
  opacity: 0.5;
  background-color: #f0f9ff !important;
}

:deep(.drag-over) {
  background-color: #e6f7ff !important;
  border-top: 2px solid #409EFF;
}

:deep(.el-table__row) {
  transition: background-color 0.2s;
}

:deep(.el-table__row:hover) {
  background-color: #f5f7fa;
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

/* 页面布局 */
.testcase-page {
  display: flex;
  gap: 16px;
  height: 100%;
  padding: 12px 20px 20px 12px;
  box-sizing: border-box;
}

/* 左侧边栏 */
.sidebar {
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1;
  overflow: visible;
  height: 100%;
}

.sidebar.resizing {
  transition: none;
}

/* 拖拽调整宽度手柄 */
.sidebar-resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  width: 4px;
  height: 100%;
  cursor: col-resize;
  z-index: 10;
  transition: background-color 0.2s;
}

.sidebar-resize-handle:hover,
.sidebar-resize-handle:active {
  background-color: rgba(99, 102, 241, 0.3);
}

.sidebar.collapsed {
  width: 0;
  min-width: 0;
  overflow: visible;
}

.sidebar.collapsed .module-container {
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.15s ease, visibility 0s 0.15s;
}

.module-container {
  opacity: 1;
  visibility: visible;
  transition: opacity 0.15s ease 0.15s, visibility 0s;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

/* 展开/收起按钮 */
.collapse-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  right: -14px;
  width: 28px;
  height: 28px;
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1000;
  transition: all 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.sidebar.collapsed .collapse-btn {
  right: auto;
  left: -14px;
}

.collapse-btn:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.collapse-btn .el-icon {
  font-size: 14px;
  color: #606266;
}

.collapse-btn:hover .el-icon {
  color: #6366f1;
}

/* 用例库选择器样式 */
.project-filter-section {
  padding: 12px 14px;
  background: #f8fafc;
  overflow: visible;
  position: relative;
  z-index: 100;
}

.project-filter-section .section-header {
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 12px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.project-filter-content {
  display: flex;
  flex-direction: column;
  overflow: visible;
  position: relative;
}

.project-filter-content :deep(.el-radio-group) {
  display: flex;
  width: 100%;
}

/* Demo风格模块容器 */
.module-container {
  background: white;
  border-radius: 0;
  border: none;
  border-right: 1px solid #e2e8f0;
  box-shadow: none;
  overflow: hidden;
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}

.module-list {
  flex: 1;
  overflow-y: auto;
  min-height: 0;
  padding: 8px 0;
}

.module-header {
  padding: 12px 16px 4px;
  font-weight: 600;
  font-size: 12px;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #fff;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.module-header .el-button {
  font-size: 12px !important;
  color: #4f46e5 !important;
}

.module-search {
  padding: 4px 12px 0;
}

.module-search .el-input {
  width: 100%;
}

.module-search .el-input :deep(.el-input__wrapper) {
  padding: 1px 11px;
}

.module-search .el-input :deep(.el-input__inner) {
  height: 28px;
}

.module-item {
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: all 0.15s;
  border-left: none;
  position: relative;
  padding: 8px 12px;
  margin: 2px 8px;
  border-radius: 6px;
}

.module-item:hover {
  background: #f8fafc;
}

.module-item.active {
  background: #eef2ff;
}

.module-name {
  font-size: 14px;
  color: #475569;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
  display: block;
  font-weight: 400;
}

.module-item.active .module-name {
  color: #4338ca;
  font-weight: 500;
}

.module-count {
  font-size: 12px;
  color: #64748b;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 12px;
  margin-left: 12px;
  font-weight: 600;
  flex-shrink: 0;
}

.module-item.active .module-count {
  background: #eef2ff;
  color: #4338ca;
}

.module-item.main-module {
  font-weight: 500;
}

.module-item.sub-module {
  font-size: 13px;
}

.expand-icon {
  font-size: 12px;
  color: #909399;
  transition: transform 0.3s;
  cursor: pointer;
  flex-shrink: 0;
  margin-right: 4px;
}

.expand-icon-placeholder {
  width: 16px;
  display: inline-block;
  flex-shrink: 0;
}

.expand-icon:hover {
  color: #6366f1;
}

.module-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  cursor: pointer;
  min-width: 0;
  overflow: hidden;
}

/* 确保tooltip容器受宽度限制 */
.module-content > .el-tooltip,
.module-item > .el-tooltip {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.module-group {
  border-bottom: 1px solid #f1f5f9;
}

.module-group:last-child {
  border-bottom: none;
}

.sub-module-list {
  background: #fafafa;
}

/* 右侧主内容 */
.main-content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
  padding-top: 0 !important;
  margin-top: 0 !important;
}

.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.main-content::-webkit-scrollbar-track {
  background: #f1f5f9;
}

/* Demo风格表格卡片 */
.table-card {
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
  background: #fff;
}

.table-card :deep(.el-card__body) {
  display: flex;
  flex-direction: column;
  padding: 0 !important;
  flex: 1;
  min-height: 0;
}

.table-header {
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  background-color: rgba(248, 250, 252, 0.5);
  z-index: 100;
  border-radius: 16px 16px 0 0;
  flex-wrap: wrap;
  gap: 8px;
}

.header-left {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: nowrap;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.action-buttons .el-button {
  border-radius: 6px !important;
  font-weight: 500 !important;
  height: 32px !important;
  padding: 0 14px !important;
  font-size: 13px !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.action-buttons .el-button--primary {
  background: #4f46e5 !important;
  border: none !important;
}

.action-buttons .el-button--primary:hover {
  background: #4338ca !important;
}

.action-buttons .el-button--default,
.action-buttons .el-button.is-plain {
  background: #ffffff !important;
  border: 1px solid #e2e8f0 !important;
  color: #334155 !important;
}

.action-buttons .el-button--default:hover,
.action-buttons .el-button.is-plain:hover {
  background: #f8fafc !important;
  border-color: #cbd5e1 !important;
}

.header-left :deep(.el-button) {
  height: 32px;
}

/* 批量操作区域样式 */
.batch-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 16px;
  background: #eef2ff;
  border-radius: 8px;
}

.batch-actions .selected-count {
  font-size: 16px;
  font-weight: 600;
  color: #4f46e5;
  min-width: 24px;
  text-align: center;
}

.batch-actions .el-tag {
  font-size: 14px;
  padding: 8px 16px;
  height: auto;
}

/* 状态统计样式 */
.header-stats {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-shrink: 0;
}

.header-stats .el-button {
  height: 32px !important;
  border-radius: 6px !important;
  font-weight: 500 !important;
  padding: 0 12px !important;
  font-size: 13px !important;
}

.header-stats .el-button--primary {
  background: #4f46e5 !important;
  border: none !important;
}

.header-stats .el-button--primary:hover {
  background: #4338ca !important;
}

.header-stats .el-icon {
  font-size: 16px;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 统一所有输入控件的高度 */
.header-right :deep(.el-select),
.header-right :deep(.el-input) {
  height: 32px !important;
}

.header-right :deep(.el-select .el-input__wrapper),
.header-right :deep(.el-input__wrapper) {
  height: 32px !important;
  min-height: 32px !important;
  padding: 1px 11px !important;
  box-sizing: border-box !important;
  display: flex !important;
  align-items: center !important;
}

.header-right :deep(.el-select .el-input__inner),
.header-right :deep(.el-input__inner) {
  height: 30px !important;
  line-height: 30px !important;
  padding: 0 !important;
}

.header-right :deep(.el-select .el-input),
.header-right :deep(.el-select .el-input__inner) {
  height: 32px !important;
  line-height: 32px !important;
}

.header-right :deep(.el-button) {
  height: 32px !important;
  width: 32px !important;
}

.header-right :deep(.el-button.is-circle) {
  padding: 6px !important;
}

/* 表格容器 */
.table-wrapper {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  width: 100%;
  overflow: hidden;
}

.table-wrapper .table-container {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* 数据加载中隐藏空状态 */
.table-wrapper :deep(.hide-empty .el-table__empty-block) {
  display: none;
}

.table-wrapper :deep(.el-table) {
  width: 100%;
  position: relative;
}

/* 设置表格单元格高度 */
.table-wrapper :deep(.el-table td.el-table__cell),
.table-wrapper :deep(.el-table th.el-table__cell) {
  height: 36px !important;
  padding: 0 8px !important;
}

.table-wrapper :deep(.el-table td.el-table__cell .cell),
.table-wrapper :deep(.el-table th.el-table__cell .cell) {
  line-height: 36px;
  padding: 0;
  font-size: 13px;
}

/* 表格内部垂直和水平滚动 */
.table-wrapper :deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: auto !important;
}

/* 表格内部滚动条样式 */
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  height: 8px;
  width: 8px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-corner {
  background: #f1f5f9;
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

/* 解决鼠标悬停时显示底部内容的问题 */
.table-wrapper :deep(.el-table__row) {
  position: relative;
  z-index: 1;
}

.table-wrapper :deep(.el-table__row:hover) {
  position: relative;
  z-index: 2;
}

/* 确保单元格内容不溢出 */
.table-wrapper :deep(.el-table__cell) {
  overflow: hidden;
  position: relative;
  z-index: 1;
  height: 48px !important;
  line-height: 48px;
  padding: 0 12px !important;
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



.case-name {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 6px;
  font-weight: 500;
  padding: 0;
  width: 100%;
  height: 100%;
}

.text-content {
  color: #606266;
  line-height: 48px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0;
  width: 100%;
}

.steps-list {
  padding: 12px 16px;
  text-align: left;
}

.step-item {
  display: table;
  width: 100%;
  padding: 6px 0;
  line-height: 1.8;
  table-layout: fixed;
}

.step-number {
  display: table-cell;
  color: #6366f1;
  font-weight: 500;
  width: 25px;
  vertical-align: top;
  padding-right: 4px;
  text-align: left;
}

.step-text {
  display: table-cell;
  color: #606266;
  vertical-align: top;
  word-break: break-word;
  white-space: pre-line;
  text-align: left;
}

.creator-name {
  color: #606266;
  font-size: 13px;
}

.attachments-section {
  width: 100%;
  padding: 12px;
  background: #fafafa;
  border-radius: 4px;
  border: 1px solid #ebeef5;
}

/* 拖拽上传区域 */
.attachment-dragger {
  width: 100%;
}

.attachment-dragger :deep(.el-upload) {
  width: 100%;
}

.attachment-dragger :deep(.el-upload-dragger) {
  width: 100%;
  height: auto;
  padding: 18px 20px;
  border-radius: 6px;
  border: 1.5px dashed #dcdfe6;
  background: #fff;
  transition: border-color 0.2s, background 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.attachment-dragger :deep(.el-upload-dragger:hover),
.attachment-dragger :deep(.el-upload-dragger.is-dragover) {
  border-color: #409eff;
  background: #ecf5ff;
}

.attachment-drop-area {
  display: flex;
  align-items: center;
  gap: 10px;
}

.attachment-drop-text {
  display: flex;
  align-items: center;
  gap: 2px;
  font-size: 13px;
  color: #606266;
}

.attachment-drop-tip {
  font-size: 12px;
  color: #c0c4cc;
  margin-left: 4px;
}

/* 附件文件列表 */
.attachment-file-list {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.attachment-file-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 10px;
  border-radius: 5px;
  border: 1px solid #ebeef5;
  background: #fff;
  transition: background 0.15s, border-color 0.15s;
}

.attachment-file-item:hover {
  background: #f0f5ff;
  border-color: #d9e4ff;
}

.attachment-file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.attachment-file-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.attachment-file-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 280px;
}

.attachment-file-size {
  font-size: 11px;
  color: #909399;
  margin-top: 1px;
}

.attachment-file-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
  margin-left: 12px;
}

.attachment-tip {
  width: 100%;
}

.attachment-tip :deep(.el-alert) {
  border-radius: 8px;
}

:deep(.el-upload__tip) {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
}

.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  flex-shrink: 0;
  margin-top: 0;
  border-top: 1px solid #e2e8f0;
  border-radius: 0 0 16px 16px;
  min-height: 56px;
}

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

.pagination-container :deep(.el-pagination__total span) {
  font-weight: 500;
  color: #0f172a;
}

/* 对话框样式 */
:deep(.el-dialog) {
  border-radius: 12px;
}

:deep(.el-dialog__header) {
  padding: 24px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #606266;
}

:deep(.el-form-item__content) {
  min-width: 0;
}

:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  border-radius: 8px;
}

/* 按钮样式优化 */
.el-button {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s;
}

.el-button:hover {
  transform: translateY(-2px);
}

.el-button:active {
  transform: translateY(0);
}

/* 表格行悬停效果 */
:deep(.el-table__row:hover) {
  background: rgba(248, 250, 252, 0.8) !important;
}

/* 移除默认的单元格padding，使用全局样式 */
:deep(.el-table__cell) {
  padding: 0 12px !important;
  height: 48px !important;
}

/* 移除特殊列的额外padding */
:deep(.el-table__body .el-table__cell) {
  padding: 0 12px !important;
}

/* 关联PR对话框样式 */
.link-dialog-content {
  padding: 0;
}

.linked-section,
.add-section {
  margin-bottom: 20px;
}

.linked-section h3,
.add-section h3 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

/* 导入对话框样式 */
.import-dialog-content {
  padding: 0;
}

.import-dialog-content :deep(.el-upload-dragger) {
  width: 100%;
  padding: 40px;
}

/* 列设置样式 */
.column-settings {
  padding: 8px 0;
}

.settings-title {
  font-weight: 600;
  font-size: 14px;
  color: #2c3e50;
  margin-bottom: 12px;
  padding: 0 4px;
}

.column-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 400px;
  overflow-y: auto;
}

.column-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: move;
  transition: all 0.3s;
  background: white;
  border: 2px solid transparent;
}

.column-item:hover {
  background: #f1f5f9;
}

.column-item.dragging {
  opacity: 0.4;
  background: #eef2ff;
  border-color: #6366f1;
}

.drag-handle {
  color: #909399;
  font-size: 16px;
  cursor: grab;
  flex-shrink: 0;
}

.drag-handle:active {
  cursor: grabbing;
}

.column-item :deep(.el-checkbox) {
  margin: 0;
  flex: 1;
}

.column-item :deep(.el-checkbox__label) {
  font-size: 13px;
}

.column-settings :deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.column-settings :deep(.el-checkbox) {
  margin: 0;
  padding: 6px 4px;
  border-radius: 4px;
  transition: background 0.3s;
}

.column-settings :deep(.el-checkbox:hover) {
  background: #f1f5f9;
}

.column-settings :deep(.el-checkbox__label) {
  font-size: 13px;
}

/* 滚动条样式 */
.module-list::-webkit-scrollbar,
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.module-list::-webkit-scrollbar-thumb,
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.module-list::-webkit-scrollbar-thumb:hover,
.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-track {
  background: #f1f5f9;
}

.table-wrapper :deep(.el-table__body-wrapper)::-webkit-scrollbar-corner {
  background: transparent;
}

/* 排序箭头样式 - 只显示单个箭头 */
:deep(.el-table th.el-table__cell .caret-wrapper) {
  height: 14px;
  width: 24px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  vertical-align: middle;
  cursor: pointer;
  overflow: initial;
  position: relative;
}

:deep(.el-table th.el-table__cell .sort-caret) {
  width: 0;
  height: 0;
  border: 5px solid transparent;
  position: absolute;
  left: 7px;
}

:deep(.el-table th.el-table__cell .sort-caret.ascending) {
  border-bottom-color: #c0c4cc;
  top: -5px;
}

:deep(.el-table th.el-table__cell .sort-caret.descending) {
  border-top-color: #c0c4cc;
  bottom: -3px;
}

/* 激活状态的箭头 */
:deep(.el-table th.el-table__cell.ascending .sort-caret.ascending) {
  border-bottom-color: #409eff;
}

:deep(.el-table th.el-table__cell.descending .sort-caret.descending) {
  border-top-color: #409eff;
}

/* 隐藏未激活的箭头 */
:deep(.el-table th.el-table__cell.ascending .sort-caret.descending) {
  display: none;
}

:deep(.el-table th.el-table__cell.descending .sort-caret.ascending) {
  display: none;
}

/* 筛选表头样式 */
.filter-header {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  white-space: nowrap;
}

.filter-icon {
  font-size: 14px;
  color: #909399;
  cursor: pointer;
  transition: all 0.3s;
  flex-shrink: 0;
}

.filter-icon:hover {
  color: #6366f1;
}

.filter-icon.active {
  color: #e6a23c;
  font-weight: bold;
}

/* 筛选下拉菜单选中状态 */
:deep(.el-dropdown-menu__item.active) {
  color: #409eff;
  font-weight: bold;
}

/* 标签容器 */
.tags-container {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}

/* 单元格内容样式 */
.cell-content {
  width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cell-content.single-line {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cell-content.clickable {
  cursor: pointer;
  transition: color 0.3s;
}

.cell-content.clickable:hover {
  color: #6366f1;
}

.ellipsis-text {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

/* 单行省略号样式 */
.single-line-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
  padding: 0;
  line-height: 48px;
}

/* 可点击的标题样式 */
.clickable-title {
  cursor: pointer;
  transition: all 0.3s;
}

.clickable-title:hover {
  color: #6366f1;
  transform: translateX(2px);
}

.clickable-title .ellipsis-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 标签省略号样式 */
.ellipsis-tag {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}

/* Tooltip 中的步骤列表样式 */
.tooltip-steps-list {
  max-width: 500px;
  padding: 8px 0;
}

.tooltip-step-item {
  display: flex;
  padding: 6px 0;
  line-height: 1.6;
  word-break: break-word;
}

.tooltip-step-number {
  color: #6366f1;
  font-weight: 500;
  min-width: 30px;
  flex-shrink: 0;
}

.tooltip-step-text {
  flex: 1;
  color: #fff;
  word-break: break-word;
}

/* Tooltip 样式 */
:deep(.steps-tooltip) {
  max-width: 600px !important;
}

:deep(.steps-tooltip .el-popper__arrow::before) {
  background: #303133;
}

/* 操作按钮容器 */
.operation-buttons {
  display: flex;
  gap: 4px;
  align-items: center;
  justify-content: center;
  flex-wrap: nowrap;
}

.operation-buttons .el-button {
  padding: 5px 8px;
  min-width: auto;
}

/* 删除按钮默认隐藏，悬停时显示 */
.delete-button {
  opacity: 0;
  transition: opacity 0.3s;
}

:deep(.el-table__row:hover) .delete-button {
  opacity: 1;
}

/* 详情对话框样式 */
.detail-content {
  padding: 0;
}



.kpi-cards-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  margin-bottom: 24px;
}

/* 紧凑统计条 */
.stats-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  margin-bottom: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  flex-wrap: wrap;
}

.stats-bar-group {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
}

.stats-bar-group.clickable {
  cursor: pointer;
  border-radius: 4px;
  padding: 2px 4px;
  margin: -2px -4px;
  transition: background 0.15s;
}

.stats-bar-group.clickable:hover {
  background: #f1f5f9;
}

.stats-bar-label {
  font-size: 13px;
  color: #64748b;
  font-weight: 500;
}

.stats-bar-value {
  font-size: 15px;
  font-weight: 400;
  color: #0f172a;
}

.stats-bar-sub {
  font-size: 12px;
  font-weight: 400;
  color: #94a3b8;
}

.stats-bar-divider {
  width: 1px;
  height: 14px;
  background: #e2e8f0;
  margin: 0 2px;
}

.stats-bar-sep {
  color: #e2e8f0;
  font-size: 14px;
  user-select: none;
}

.stats-bar-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}

.stats-bar-tag.dark { background: #f1f5f9; color: #1e293b; }
.stats-bar-tag.medium { background: #f1f5f9; color: #475569; }
.stats-bar-tag.light { background: #f1f5f9; color: #94a3b8; }
.stats-bar-tag.lighter { background: #f1f5f9; color: #cbd5e1; }
.stats-bar-tag.blue { background: #eff6ff; color: #3b82f6; }
.stats-bar-tag.emerald { background: #ecfdf5; color: #059669; }
.stats-bar-tag.rose { background: #fff1f2; color: #e11d48; }
.stats-bar-tag.slate { background: #f1f5f9; color: #64748b; }
.stats-bar-tag.amber { background: #fffbeb; color: #d97706; }

/* Demo风格统计卡片 */
.summary-card {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  transition: box-shadow 0.2s ease;
  display: flex;
  flex-direction: column;
}

.summary-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.summary-card.clickable {
  cursor: pointer;
}

.card-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.card-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-icon-box.blue {
  background: #eff6ff;
  color: #3b82f6;
}

.card-icon-box.green {
  background: #ecfdf5;
  color: #10b981;
}

.card-icon-box.amber {
  background: #fffbeb;
  color: #f59e0b;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.card-main-number {
  font-size: 36px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1;
  margin-bottom: 24px;
}

.card-main-number-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 24px;
}

.card-main-number-row .card-main-number {
  margin-bottom: 0;
}

.card-sub-number {
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.card-stats-row {
  display: flex;
  gap: 24px;
  margin-top: auto;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-item .stat-label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
}

.stat-item .stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
}

.stat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.stat-dot.dark { background: #1e293b; }
.stat-dot.medium { background: #475569; }
.stat-dot.light { background: #94a3b8; }
.stat-dot.lighter { background: #cbd5e1; }
.stat-dot.emerald { background: #10b981; }
.stat-dot.rose { background: #f43f5e; }
.stat-dot.slate { background: #e2e8f0; }
.stat-dot.amber { background: #f59e0b; }

/* 保留旧样式兼容 */
.kpi-card {
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  transition: transform 0.2s, box-shadow 0.2s;
}

.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.purple-card {
  background: linear-gradient(135deg, #e9d5ff 0%, #c4b5fd 100%);
}

.blue-card {
  background: linear-gradient(135deg, #bfdbfe 0%, #93c5fd 100%);
}

.green-card {
  background: linear-gradient(135deg, #bbf7d0 0%, #86efac 100%);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.card-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.purple-icon {
  background: rgba(99, 102, 241, 0.1);
  color: #4f46e5;
}

.blue-icon {
  background: rgba(59, 130, 246, 0.2);
  color: #2563eb;
}

.green-icon {
  background: rgba(34, 197, 94, 0.2);
  color: #16a34a;
}

.card-menu {
  position: relative;
}

.card-menu-btn {
  width: 36px;
  height: 36px;
  border: none;
  background: transparent;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  color: #666;
}

.card-menu-btn:hover {
  background: rgba(0, 0, 0, 0.05);
}

.card-content {
  margin-bottom: 20px;
}

.kpi-number {
  font-size: 36px;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1;
  margin-bottom: 0;
}

.kpi-main-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}

.kpi-label {
  font-size: 32px;
  color: #1a1a1a;
  font-weight: 700;
  line-height: 1;
}

.status-tags {
  display: flex;
  gap: 16px;
}

.status-tag {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-dot.red {
  background: #ef4444;
}

.status-dot.orange {
  background: #f59e0b;
}

.status-dot.blue {
  background: #3b82f6;
}

.status-dot.green {
  background: #22c55e;
}

.status-dot.gray {
  background: #9ca3af;
}

.status-value {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a1a;
}

.status-text {
  font-size: 12px;
  color: #888;
}

/* Demo风格等级标签 - 使用el-tag */
.level-tag-demo {
  border-radius: 6px !important;
  font-weight: 700 !important;
  border: 1px solid !important;
  padding: 0 8px !important;
}

.level-tag-demo.level-l1 {
  background: #fef2f2 !important;
  color: #be123c !important;
  border-color: rgba(190, 18, 60, 0.3) !important;
}

.level-tag-demo.level-l2 {
  background: #fff7ed !important;
  color: #c2410c !important;
  border-color: rgba(194, 65, 12, 0.3) !important;
}

.level-tag-demo.level-l3 {
  background: #eff6ff !important;
  color: #1d4ed8 !important;
  border-color: rgba(29, 78, 216, 0.3) !important;
}

.level-tag-demo.level-l4 {
  background: #f8fafc !important;
  color: #475569 !important;
  border-color: rgba(71, 85, 105, 0.3) !important;
}

/* Demo风格状态标签 - 使用el-tag */
.status-tag-demo {
  border-radius: 6px !important;
  font-weight: 500 !important;
  border: 1px solid !important;
  padding: 0 8px !important;
}

.status-tag-demo.status-pending {
  background: #fffbeb !important;
  color: #b45309 !important;
  border-color: rgba(180, 83, 9, 0.3) !important;
}

.status-tag-demo.status-reviewed {
  background: #ecfdf5 !important;
  color: #047857 !important;
  border-color: rgba(4, 120, 87, 0.3) !important;
}

.status-tag-demo.status-rejected {
  background: #fef2f2 !important;
  color: #be123c !important;
  border-color: rgba(190, 18, 60, 0.3) !important;
}

.status-tag-demo.status-deprecated {
  background: #f8fafc !important;
  color: #64748b !important;
  border-color: rgba(100, 116, 139, 0.3) !important;
}

/* Demo风格主内容区背景 */
.main-content {
  background: #f8fafc;
  padding: 24px;
}

/* Demo风格页面布局 */
.testcase-page {
  height: 100%;
  padding: 0;
  background: #f8fafc;
}

/* 优化按钮样式 - Demo风格 */
:deep(.el-button) {
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.15s;
  height: 40px;
  padding: 0 16px;
}

:deep(.el-button:hover) {
  transform: none;
  box-shadow: none;
}

:deep(.el-button:active) {
  transform: none;
}

/* 主按钮样式 - Demo indigo色 */
:deep(.el-button--primary) {
  background: #4f46e5;
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--primary:hover) {
  background: #4338ca;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 朴素按钮样式 */
:deep(.el-button--primary.is-plain) {
  background: #ffffff;
  color: #334155;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--primary.is-plain:hover) {
  background: #f8fafc;
  color: #334155;
  border-color: #cbd5e1;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 危险按钮样式 - Demo风格 */
:deep(.el-button--danger) {
  background: #ef4444;
  border: none;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

:deep(.el-button--danger:hover) {
  background: #dc2626;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* 小按钮样式 */
:deep(.el-button--small) {
  height: 32px;
  padding: 0 12px;
  border-radius: 6px;
  font-weight: 500;
}

/* link按钮样式 */
:deep(.el-button--text),
:deep(.el-button--link),
:deep(.el-button.is-link) {
  height: auto;
  padding: 4px 8px;
  border-radius: 6px;
  background: transparent !important;
  border: none !important;
}

:deep(.el-button--primary.is-link),
:deep(.el-button--primary.is-link:focus),
:deep(.el-button--primary.is-link:active) {
  color: #4f46e5 !important;
  background: transparent !important;
  border: none !important;
}

:deep(.el-button--primary.is-link:hover) {
  color: #4338ca !important;
  background: transparent !important;
  border: none !important;
}

:deep(.el-button--info.is-link),
:deep(.el-button--info.is-link:hover),
:deep(.el-button--info.is-link:focus) {
  color: #64748b !important;
  background: transparent !important;
  border: none !important;
}

:deep(.el-button--info.is-link:hover) {
  color: #475569 !important;
}

/* 优化输入框样式 - Demo风格 */
:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
  border-radius: 8px;
  box-shadow: none;
  border: 1px solid #e2e8f0;
  transition: all 0.15s;
}

:deep(.el-input__wrapper:hover),
:deep(.el-textarea__inner:hover) {
  border-color: #cbd5e1;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-textarea__inner:focus) {
  border-color: #6366f1;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 优化选择器样式 - Demo风格 */
:deep(.el-select .el-input__wrapper) {
  border-radius: 8px;
}

:deep(.el-select-dropdown) {
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

:deep(.el-select-dropdown__item) {
  border-radius: 4px;
  margin: 2px 4px;
  font-weight: 400;
}

:deep(.el-select-dropdown__item:hover) {
  background: #f1f5f9;
  color: #334155;
}

:deep(.el-select-dropdown__item.selected) {
  background: #eef2ff;
  color: #4f46e5;
  font-weight: 500;
}

/* Demo风格表格头部样式 */
.table-header {
  padding: 8px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #e2e8f0;
  flex-shrink: 0;
  position: sticky;
  top: 0;
  background: #f8fafc;
  z-index: 100;
  gap: 12px;
  border-radius: 16px 16px 0 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 批量操作区域样式 */
.batch-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 20px;
  background: #f1f5f9;
  border-radius: 12px;
}

.batch-actions .selected-count {
  font-size: 15px;
  font-weight: 700;
  color: #4f46e5;
  min-width: 24px;
  text-align: center;
}

/* 统一所有输入控件的高度 */
.header-right :deep(.el-select),
.header-right :deep(.el-input) {
  height: 32px !important;
}

.header-right :deep(.el-select .el-input__wrapper),
.header-right :deep(.el-input__wrapper) {
  height: 32px !important;
  min-height: 32px !important;
  padding: 0 12px !important;
  border-radius: 6px !important;
  border: 1px solid #e2e8f0 !important;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
}

.header-right :deep(.el-select .el-input__wrapper:hover),
.header-right :deep(.el-input__wrapper:hover) {
  border-color: #cbd5e1 !important;
}

.header-right :deep(.el-select .el-input__wrapper.is-focus),
.header-right :deep(.el-input__wrapper.is-focus) {
  border-color: #6366f1 !important;
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
}

.header-right :deep(.el-button) {
  height: 32px !important;
  width: 32px !important;
  border-radius: 6px !important;
  border: 1px solid #e2e8f0 !important;
  background: #fff !important;
}

.header-right :deep(.el-button:hover) {
  border-color: #cbd5e1 !important;
  background: #f8fafc !important;
}

.header-right :deep(.el-button.is-circle) {
  padding: 6px !important;
}

/* 恢复 primary 按钮在 header-right 中的正确样式 */
.header-right :deep(.el-button--primary) {
  background: #4f46e5 !important;
  border: none !important;
  color: #fff !important;
  width: auto !important;
}

.header-right :deep(.el-button--primary:hover) {
  background: #4338ca !important;
}

.header-right :deep(.el-button--primary.is-plain) {
  background: #eef2ff !important;
  border: 1px solid #4f46e5 !important;
  color: #4f46e5 !important;
  width: auto !important;
}

.header-right :deep(.el-button--primary.is-plain:hover) {
  background: #4f46e5 !important;
  color: #fff !important;
  border-color: #4f46e5 !important;
}

.pagination-container :deep(.btn-prev:hover),
.pagination-container :deep(.btn-next:hover) {
  background: #f1f5f9;
}

/* 优化对话框样式 - Demo风格 */
:deep(.el-dialog) {
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.12);
}

:deep(.el-dialog__header) {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #e2e8f0;
}

:deep(.el-dialog__title) {
  font-size: 18px;
  font-weight: 600;
  color: #0f172a;
}

:deep(.el-dialog__body) {
  padding: 24px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: #475569;
}

/* 优化Tag样式 - Demo风格 */
:deep(.el-tag) {
  border-radius: 6px;
  font-weight: 500;
  border: 1px solid transparent;
}


/* 优化表头样式 - Demo风格 */
:deep(.el-table th.el-table__cell) {
  background: #f8fafc !important;
}

/* 固定列使用不透明背景，防止内容透出 */
:deep(.el-table td.el-table__cell) {
  background: #fff;
}
:deep(.el-table__row:hover > td.el-table__cell) {
  background: #f8fafc !important;
}

/* 优化复选框样式 - Demo风格 */
:deep(.el-checkbox__inner) {
  border-radius: 4px;
  transition: all 0.15s;
  border-color: #cbd5e1;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #4f46e5;
  border-color: #4f46e5;
}

/* 优化Popover样式 - Demo风格 */
:deep(.el-popover) {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
}

/* 优化Dropdown菜单样式 - Demo风格 */
:deep(.el-dropdown-menu) {
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border: 1px solid #e2e8f0;
  padding: 4px;
}

:deep(.el-dropdown-menu__item) {
  border-radius: 4px;
  margin: 2px 0;
  font-weight: 400;
  color: #475569;
}

:deep(.el-dropdown-menu__item:hover) {
  background: #f1f5f9;
  color: #334155;
}

.detail-content :deep(.el-descriptions__label) {
  font-weight: 500;
  color: #475569;
  background: #f8fafc;
}

.detail-content :deep(.el-descriptions__content) {
  color: #334155;
  text-align: left;
}

.detail-section {
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  line-height: 1.8;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
  min-height: 40px;
}

.detail-step-item {
  display: flex;
  padding: 6px 0;
  line-height: 1.8;
}

.detail-step-item .step-number {
  color: #6366f1;
  font-weight: 500;
  min-width: 30px;
  flex-shrink: 0;
}

.detail-step-item .step-text {
  flex: 1;
  color: #606266;
  word-break: break-word;
}

/* 历史记录样式 */
.history-item {
  padding: 4px 0;
}

.history-user {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

.history-user .el-icon {
  color: #6366f1;
}

.history-change {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.history-value {
  flex: 1;
  min-width: 0;
}

.value-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-bottom: 4px;
}

.value-content {
  display: block;
  font-size: 13px;
  word-break: break-word;
  white-space: pre-wrap;
  line-height: 1.6;
}

.old-value .value-content {
  color: #f56c6c;
}

.new-value .value-content {
  color: #67c23a;
}

.arrow-icon {
  color: #909399;
  font-size: 16px;
  flex-shrink: 0;
}

:deep(.el-timeline-item__timestamp) {
  color: #909399;
  font-size: 13px;
}

/* ==================== 模块管理样式 ==================== */

.module-management {
  padding: 0;
}

.management-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.module-tree {
  max-height: 500px;
  overflow-y: auto;
}

.module-tree :deep(.el-tree-node__content) {
  height: 40px;
  padding: 0 8px;
}

.tree-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 8px;
}

.node-label {
  flex: 1;
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-count {
  font-size: 12px;
  color: #909399;
  margin: 0 8px;
  flex-shrink: 0;
}

.node-tag {
  font-size: 12px;
  color: #409eff;
  margin-left: 2px;
  flex-shrink: 0;
}

.node-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.3s;
  flex-shrink: 0;
}

.tree-node:hover .node-actions {
  opacity: 1;
}

.node-actions .el-button {
  padding: 4px;
  min-width: auto;
}

/* 修复模块下拉框宽度问题 */
:deep(.el-select-dropdown.module-select-dropdown) {
  width: auto !important;
  min-width: 200px !important;
  overflow: hidden !important;
}

:deep(.module-select-dropdown .el-select-dropdown__item) {
  padding: 0 12px !important;
  white-space: nowrap !important;
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}

:deep(.module-select-dropdown .el-select-dropdown__item:focus),
:deep(.module-select-dropdown .el-select-dropdown__item:focus-visible) {
  outline: none !important;
  border: none !important;
  box-shadow: none !important;
}

/* 模块树选择器下拉框样式 */
:deep(.module-tree-select-dropdown) {
  min-width: 300px !important;
}

:deep(.module-tree-select-dropdown .el-tree-node__content) {
  height: 32px;
}

/* 表格行可点击样式 */
:deep(.el-table__body-wrapper tbody tr) {
  cursor: pointer;
}

:deep(.el-table__body-wrapper tbody tr:hover) {
  background-color: #f5f7fa;
}

/* 操作列、多选框列、拖拽列不显示指针 */
:deep(.el-table__body-wrapper tbody tr td:first-child),
:deep(.el-table__body-wrapper tbody tr td:nth-child(2)),
:deep(.el-table__body-wrapper tbody tr td:last-child) {
  cursor: default;
}

/* 详情弹窗附件列表样式 */
.detail-attachments-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.detail-attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.detail-attachment-item:hover {
  background: #f0f5ff;
  border-color: #d9e4ff;
}

.attachment-info {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.attachment-meta {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.attachment-name {
  font-size: 13px;
  color: #303133;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.attachment-size {
  font-size: 12px;
  color: #909399;
  margin-top: 2px;
}

.attachment-actions {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.preview-container {
  min-height: 200px;
}

.pr-count-clickable {
  cursor: pointer;
  transition: opacity 0.15s;
}
.pr-count-clickable:hover {
  opacity: 0.7;
}

</style>

<style>
/* 详情弹窗固定高度，防止切换上下条时抖动 */
.detail-fixed-dialog .el-dialog__body {
  height: 70vh;
  overflow-y: auto;
  padding: 16px 20px;
}

/* 复制用例后的行高亮闪烁效果 */
@keyframes copied-row-flash {
  0%,  100% { background-color: transparent; }
  20%, 60%  { background-color: #bbf7d0; }
  40%, 80%  { background-color: #dcfce7; }
}
tr.row-copied-flash > td {
  animation: copied-row-flash 3s ease-in-out forwards;
}
</style>
