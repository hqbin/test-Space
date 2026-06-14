<template>
  <div class="db-page">
    <!-- 左侧表列表 -->
    <aside class="db-sidebar">
      <div class="sidebar-header">数据库表</div>
      <div class="sidebar-search">
        <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5L14 14" stroke-linecap="round"/></svg>
        <input v-model="tableKeyword" placeholder="搜索表名…" class="search-input" />
      </div>
      <div class="table-list">
        <div
          v-for="t in filteredTables" :key="t"
          class="table-item" :class="{ active: t === selectedTable }"
          @click="selectTable(t)"
        >
          <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.4" style="flex-shrink:0;opacity:.55"><rect x="1" y="1" width="12" height="12" rx="1.5"/><path d="M1 4.5h12M1 8h12M5 4.5v7"/></svg>
          <el-tooltip :content="t" placement="right" :show-after="500" :enterable="false">
            <span class="table-name">{{ t }}</span>
          </el-tooltip>
        </div>
      </div>
    </aside>

    <!-- 右侧主区域 -->
    <div class="db-main">

      <!-- Tab 栏 -->
      <div class="view-tabs">
        <button class="view-tab" :class="{ active: activeView === 'table' }" @click="switchView('table')">
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="1" width="12" height="12" rx="1.5"/><path d="M1 4.5h12M1 8h12M5 4.5v7"/></svg>
          表格视图
        </button>
        <button class="view-tab" :class="{ active: activeView === 'sql' }" @click="switchView('sql')">
          <svg viewBox="0 0 14 14" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 4l-2 3 2 3M11 4l2 3-2 3M8 2l-2 10" stroke-linecap="round" stroke-linejoin="round"/></svg>
          SQL 执行
        </button>
        <div class="tab-pill" :style="{ transform: activeView === 'sql' ? 'translateX(100%)' : 'translateX(0)' }" />
      </div>

      <!-- 滑动容器 -->
      <div class="slider-wrap">
        <div class="slider" :style="{ transform: activeView === 'sql' ? 'translateX(-50%)' : 'translateX(0)' }">

          <!-- ① 表格视图 -->
          <div class="panel">
            <div class="panel-bar">
              <div class="bar-left">
                <span class="panel-title">{{ selectedTable || '—' }}</span>
                <!-- 表说明按钮 -->
                <button v-if="selectedTable && tableDoc" class="doc-btn" @click="docVisible = true">
                  <svg viewBox="0 0 14 14" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="7" cy="7" r="6"/><path d="M7 6v4M7 4.5v.5" stroke-linecap="round"/></svg>
                  表说明
                </button>
              </div>
              <div class="bar-right">
                <button class="btn btn-ghost" @click="handleBackup">导出备份</button>
                <button class="btn btn-ghost" @click="openRestoreDialog">导入恢复</button>
                <div class="search-box">
                  <svg class="search-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="6.5" cy="6.5" r="4.5"/><path d="M10.5 10.5L14 14" stroke-linecap="round"/></svg>
                  <input v-model="rowKeyword" placeholder="搜索行 / test_plan_id:123" class="search-input" @keyup.enter="loadRows" />
                </div>
                <button class="btn btn-default" @click="loadRows">搜索</button>
                <button class="btn btn-primary" :disabled="!selectedTable" @click="openCreate">+ 新增</button>
              </div>
            </div>

            <div class="table-wrap">
              <el-table
                :data="rows"
                border
                v-loading="loadingRows"
                style="width:100%;height:100%"
                table-layout="fixed"
                height="100%"
              >
                <el-table-column
                  v-for="c in columns"
                  :key="c.name"
                  :label="c.name"
                  width="180"
                >
                  <template #default="{ row }">
                    <el-tooltip
                      :content="String(row[c.name] ?? '')"
                      placement="top"
                      :show-after="500"
                      :disabled="row[c.name] === null || row[c.name] === undefined || row[c.name] === ''"
                      popper-class="db-cell-tooltip"
                    >
                      <div class="cell-ellipsis">{{ row[c.name] ?? '' }}</div>
                    </el-tooltip>
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="130" fixed="right" class-name="col-action">
                  <template #default="{ row }">
                    <button class="op-btn" @click="openEdit(row)">编辑</button>
                    <button class="op-btn danger" @click="removeRow(row)">删除</button>
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <div class="panel-footer">
              <span class="count-label">共 <b>{{ total }}</b> 条</span>
              <el-pagination
                layout="prev, pager, next"
                :total="total" :current-page="page" :page-size="size"
                @current-change="onPageChange"
              />
            </div>
          </div>

          <!-- ② SQL 视图 -->
          <div class="panel">
            <div class="panel-bar">
              <span class="panel-title">SQL 执行</span>
              <div class="bar-right">
                <span class="shortcut-hint">Ctrl+Enter 执行</span>
                <button class="btn btn-primary" :disabled="sqlRunning" @click="runSql">
                  <svg v-if="!sqlRunning" viewBox="0 0 12 12" width="11" height="11" fill="currentColor"><path d="M2 1.5l8 4.5-8 4.5z"/></svg>
                  <span v-if="sqlRunning">执行中…</span>
                  <span v-else>执行</span>
                </button>
              </div>
            </div>

            <div class="sql-editor-area">
              <textarea
                v-model="sql"
                class="sql-editor"
                placeholder="SELECT * FROM users LIMIT 20;"
                spellcheck="false"
                @keydown.ctrl.enter.prevent="runSql"
                @keydown.meta.enter.prevent="runSql"
              />
            </div>

            <div v-if="sqlResultType" class="sql-result-area">
              <div class="result-status" :class="sqlResultType">
                <template v-if="sqlResultType === 'query'">
                  <svg viewBox="0 0 12 12" width="12" height="12" fill="#52c41a"><path d="M10 3L5 8.5 2 5.5l-1 1 4 4 6-6.5z"/></svg>
                  查询到 <b>{{ sqlRows.length }}</b> 条
                </template>
                <template v-else-if="sqlResultType === 'mutation'">
                  <svg viewBox="0 0 12 12" width="12" height="12" fill="#52c41a"><path d="M10 3L5 8.5 2 5.5l-1 1 4 4 6-6.5z"/></svg>
                  执行成功，影响 <b>{{ affected }}</b> 行
                </template>
                <template v-else-if="sqlResultType === 'error'">
                  <svg viewBox="0 0 12 12" width="12" height="12" fill="#ff4d4f"><path d="M6 1a5 5 0 100 10A5 5 0 006 1zm-.5 2.5h1v3h-1zm0 4h1v1h-1z"/></svg>
                  {{ sqlError }}
                </template>
              </div>

              <div v-if="sqlResultType === 'query' && sqlRows.length" class="sql-table-wrap">
                <el-table :data="pagedSqlRows" border style="width:100%;height:100%" height="100%"
                  table-layout="fixed">
                  <el-table-column v-for="k in sqlColumns" :key="k" :label="k" width="180">
                    <template #default="{ row }">
                      <el-tooltip
                        :content="String(row[k] ?? '')"
                        placement="top"
                        :show-after="500"
                        :disabled="row[k] === null || row[k] === undefined || row[k] === ''"
                        popper-class="db-cell-tooltip"
                      >
                        <div class="cell-ellipsis">{{ row[k] ?? '' }}</div>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                </el-table>
                <div class="panel-footer">
                  <span class="count-label">共 <b>{{ sqlRows.length }}</b> 条</span>
                  <el-pagination layout="prev, pager, next" :total="sqlRows.length" :current-page="sqlPage" :page-size="sqlPageSize" @current-change="p => sqlPage = p" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 表说明抽屉 -->
    <el-drawer v-model="docVisible" :title="selectedTable + ' — 表说明'" size="460px" destroy-on-close>
      <div v-if="tableDoc" class="doc-drawer">
        <section class="doc-section">
          <div class="doc-section-title">📋 用途说明</div>
          <p class="doc-text">{{ tableDoc.desc }}</p>
        </section>
        <section v-if="tableDoc.scene" class="doc-section">
          <div class="doc-section-title">🔍 使用场景</div>
          <p class="doc-text">{{ tableDoc.scene }}</p>
        </section>
        <section v-if="tableDoc.relations && tableDoc.relations.length" class="doc-section">
          <div class="doc-section-title">🔗 关联关系</div>
          <div v-for="r in tableDoc.relations" :key="r.table" class="rel-item">
            <span class="rel-table">{{ r.table }}</span>
            <span class="rel-via">{{ r.via }}</span>
          </div>
        </section>
        <section v-if="tableDoc.fields && tableDoc.fields.length" class="doc-section">
          <div class="doc-section-title">📐 字段说明</div>
          <div class="field-list">
            <div v-for="f in tableDoc.fields" :key="f.name" class="field-row">
              <code class="field-name">{{ f.name }}</code>
              <span class="field-note">{{ f.note }}</span>
            </div>
          </div>
        </section>
      </div>
    </el-drawer>

    <!-- 编辑 / 新增 Dialog -->
    <el-dialog v-model="editDialogVisible" :title="editMode === 'create' ? '新增行' : '编辑行'" width="600px">
      <el-form label-width="130px" size="default">
        <el-form-item v-for="c in columns" :key="c.name" :label="c.name">
          <el-input v-model="editForm[c.name]" :disabled="editMode === 'edit' && primaryKeys.includes(c.name)" />
        </el-form-item>
      </el-form>
      <template #footer>
        <button class="btn btn-ghost" @click="editDialogVisible = false">取消</button>
        <button class="btn btn-primary" style="margin-left:8px" @click="submitEdit">确认</button>
      </template>
    </el-dialog>

    <!-- 备份 Dialog -->
    <el-dialog v-model="backupDialogVisible" title="导出备份" width="480px">
      <el-alert type="info" :closable="false" style="margin-bottom:14px">留空则备份所有表</el-alert>
      <el-checkbox-group v-model="selectedTables">
        <el-checkbox v-for="t in tables" :key="t" :label="t" :value="t">{{ t }}</el-checkbox>
      </el-checkbox-group>
      <template #footer>
        <button class="btn btn-ghost" @click="backupDialogVisible = false">取消</button>
        <button class="btn btn-primary" style="margin-left:8px" :disabled="backupLoading" @click="doBackup">{{ backupLoading ? '导出中…' : '确认导出' }}</button>
      </template>
    </el-dialog>

    <!-- 恢复 Dialog -->
    <el-dialog v-model="restoreDialogVisible" title="导入恢复" width="500px" :close-on-click-modal="false" @closed="onRestoreDialogClosed">
      <template v-if="restoreStatus !== 'running'">
        <el-alert v-if="restoreMode === 'append'" type="info" :closable="false" style="margin-bottom:14px">
          追加模式：已有数据保留，仅补充缺失记录，不影响在线用户。
        </el-alert>
        <el-alert v-else type="warning" :closable="false" style="margin-bottom:14px">
          覆盖模式：已有记录会被备份数据覆盖，请谨慎操作。
        </el-alert>
        <div style="margin-bottom:14px">
          <span style="font-size:13px;font-weight:500;margin-right:12px">恢复模式</span>
          <el-radio-group v-model="restoreMode">
            <el-radio value="append">追加</el-radio>
            <el-radio value="upsert">覆盖</el-radio>
          </el-radio-group>
        </div>
        <el-upload ref="uploadRef" :auto-upload="false" :limit="1" accept=".sql" :on-change="handleFileChange">
          <button class="btn btn-default">选择 SQL 文件</button>
          <template #tip><div style="font-size:12px;color:#8c8c8c;margin-top:4px">仅支持 .sql 文件</div></template>
        </el-upload>
      </template>
      <div v-if="restoreStatus === 'running'" style="padding:16px 0">
        <el-progress :percentage="restoreProgress" :stroke-width="12" :text-inside="true" />
        <p style="text-align:center;font-size:13px;color:#595959;margin-top:14px;white-space:pre-wrap">{{ restoreMessage || '正在启动…' }}</p>
      </div>
      <template #footer>
        <button class="btn btn-ghost" :disabled="restoreStatus === 'running'" @click="restoreDialogVisible = false">取消</button>
        <button v-if="restoreStatus === 'running'" class="btn btn-danger" style="margin-left:8px" :disabled="cancellingTask" @click="doCancelRestore">{{ cancellingTask ? '取消中…' : '中止任务' }}</button>
        <button v-else class="btn btn-primary" style="margin-left:8px" :disabled="restoreLoading" @click="doRestore">{{ restoreLoading ? '导入中…' : '确认导入' }}</button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  createTableRow, deleteTableRow, executeDatabaseSql,
  getDatabaseTables, getTableRows, getTableSchema, updateTableRow,
  backupDatabase, restoreDatabase, getRestoreProgress, cancelRestoreTask
} from '../../api/database'

// ── 表说明数据 ────────────────────────────────────────────
const TABLE_DOCS = {
  users: {
    desc: '系统用户表，存储所有登录账号的基本信息和认证凭据。',
    scene: '用于登录鉴权、展示操作人、分配测试任务、发送通知等场景。',
    relations: [
      { table: 'user_roles', via: 'users.id → user_roles.user_id  （角色分配）' },
      { table: 'user_projects', via: 'users.id → user_projects.user_id  （项目授权）' },
      { table: 'user_teams', via: 'users.id → user_teams.user_id  （项目组归属）' },
    ],
    fields: [
      { name: 'id', note: '主键，自增' },
      { name: 'username', note: '登录用户名，全局唯一' },
      { name: 'password', note: 'BCrypt 哈希密码，不可逆' },
      { name: 'full_name', note: '显示名称（姓名）' },
      { name: 'position_tag_id', note: '职位标签 ID，关联 position_tags' },
      { name: 'zmind_api_key', note: '用户个人的 Zmind API Key' },
      { name: 'must_change_password', note: '首次登录强制改密标志' },
      { name: 'status', note: '1=启用，0=禁用' },
    ]
  },
  projects: {
    desc: '用例库（项目）表，支持三层树形结构：小组(GROUP) → 分类(CATEGORY) → 产品线(PRODUCT)。',
    scene: '作为测试用例、测试计划的顶层容器，用于按产品线隔离数据并控制访问权限。',
    relations: [
      { table: 'test_cases', via: 'projects.id → test_cases.primary_project_id' },
      { table: 'test_plans', via: 'projects.id → test_plans.project_id' },
      { table: 'user_projects', via: 'projects.id → user_projects.project_id  （用户授权）' },
    ],
    fields: [
      { name: 'id', note: '主键' },
      { name: 'name', note: '用例库名称' },
      { name: 'tag', note: '用于生成用例编号前缀，如 STB → STB-001' },
      { name: 'parent_id', note: '上级节点 ID，为空则是根节点' },
      { name: 'level', note: '层级：1=小组 2=分类 3=产品线' },
      { name: 'path', note: '完整路径，如 "1/3/5"，便于树形查询' },
      { name: 'project_type', note: 'GROUP / CATEGORY / PRODUCT' },
    ]
  },
  test_cases: {
    desc: '测试用例主表，存储所有功能用例的完整内容，包括步骤、预期结果、等级、模块等。',
    scene: '用例库页面的核心数据，也是测试计划、评审计划的基础数据来源。',
    relations: [
      { table: 'test_plan_test_cases', via: 'test_cases.id → test_plan_test_cases.test_case_id  （计划关联）' },
      { table: 'test_executions', via: 'test_cases.id → test_executions.test_case_id  （执行记录）' },
      { table: 'test_case_zmind_links', via: 'test_cases.id → test_case_zmind_links.test_case_id  （问题单）' },
    ],
    fields: [
      { name: 'case_number', note: '用例编号，系统自动生成，如 STB-001' },
      { name: 'module / sub_module', note: '模块路径，用斜杠分隔，如 "ISDB/Setting"' },
      { name: 'level', note: '用例等级：L1（最高）~ L4（最低）' },
      { name: 'steps', note: 'JSON 格式，[{"step":"…","expected":"…"},…]' },
      { name: 'status', note: 'REVIEWED / PENDING / REJECTED / DEPRECATED' },
      { name: 'source', note: 'LOCAL=本地创建，ZMIND=从 Zmind 同步' },
      { name: 'share_scope', note: '跨项目共享范围：NONE/GROUP/CATEGORY/ALL' },
    ]
  },
  test_plans: {
    desc: '测试计划表，定义一次测试活动的范围、时间、执行人和审核流程。',
    scene: '每次版本测试创建一个计划，关联若干用例，分配给测试人员执行，最终生成测试报告。',
    relations: [
      { table: 'test_plan_test_cases', via: 'test_plans.id → test_plan_test_cases.test_plan_id  （关联用例）' },
      { table: 'test_executions', via: 'test_plans.id → test_executions.test_plan_id  （执行结果）' },
      { table: 'test_plan_executors', via: 'test_plans.id → test_plan_executors.test_plan_id  （执行人）' },
      { table: 'reports', via: 'test_plans.id → reports.test_plan_id  （测试报告）' },
    ],
    fields: [
      { name: 'status', note: 'PENDING / IN_PROGRESS / IN_REVIEW / REJECTED / COMPLETED / CANCELLED' },
      { name: 'reviewer_id', note: '审核人，关联 users.id' },
      { name: 'team_id', note: '所属项目组，关联 teams.id' },
      { name: 'suite_id', note: '从某个套件初始化用例时记录来源套件 ID' },
    ]
  },
  test_plan_test_cases: {
    desc: '测试计划与测试用例的多对多关联表，记录哪些用例被纳入哪个测试计划。',
    scene: '添加/移除计划用例时操作此表；删除此表记录会将该用例从计划统计中移除。',
    relations: [
      { table: 'test_plans', via: 'test_plan_id → test_plans.id' },
      { table: 'test_cases', via: 'test_case_id → test_cases.id' },
    ],
    fields: [
      { name: 'test_plan_id', note: '测试计划 ID' },
      { name: 'test_case_id', note: '测试用例 ID' },
      { name: 'created_at', note: '关联时间' },
    ]
  },
  test_executions: {
    desc: '测试执行记录表，每次提交执行结果都追加一条记录（不覆盖），并保存执行时的用例快照。',
    scene: '执行页面提交结果时写入，计划进度统计取每条用例的最新一条执行记录。',
    relations: [
      { table: 'test_plans', via: 'test_plan_id → test_plans.id' },
      { table: 'test_cases', via: 'test_case_id → test_cases.id' },
      { table: 'users', via: 'executor_id → users.id  （执行人）' },
    ],
    fields: [
      { name: 'result', note: 'PASS / FAIL / NA / NT / BLOCK / ONGOING / 待确认' },
      { name: 'testcase_* (快照)', note: '执行时固化的用例内容，防止用例修改污染历史' },
      { name: 'pr_links_snapshot', note: 'JSON，执行时关联的 Zmind PR 列表快照' },
      { name: 'version_info', note: '执行时填写的版本信息，自由文本' },
    ]
  },
  test_plan_executors: {
    desc: '测试计划执行人关联表，一个计划可以指定多名执行人。',
    scene: '创建/编辑计划时设置执行人，用于权限控制（只有执行人可以提交执行结果）。',
    relations: [
      { table: 'test_plans', via: 'test_plan_id → test_plans.id' },
      { table: 'users', via: 'executor_id → users.id' },
    ],
    fields: []
  },
  test_plan_viewers: {
    desc: '测试计划查看人关联表，查看人可以查看计划进度但不能提交执行结果，且不能与执行人重叠。',
    scene: '用于让 PM、RD 等非测试人员只读查看测试计划进度。',
    relations: [
      { table: 'test_plans', via: 'test_plan_id → test_plans.id' },
      { table: 'users', via: 'viewer_id → users.id' },
    ],
    fields: []
  },
  reports: {
    desc: '测试报告表，存储从测试计划生成的报告，支持 PDF/Excel 格式，有审核流程。',
    scene: '测试完成后提交报告审核，审核通过后可对外发布；报告审核通过时会保存快照防止篡改。',
    relations: [
      { table: 'test_plans', via: 'test_plan_id → test_plans.id' },
      { table: 'users', via: 'reviewed_by → users.id  （审核人）' },
    ],
    fields: [
      { name: 'status', note: 'PENDING_REVIEW / APPROVED / REJECTED' },
      { name: 'snapshot_data', note: 'JSON，审核通过后冻结的完整报告数据' },
      { name: 'zmind_pr_stats', note: 'JSON，CSV 统计结果（PR 汇总）' },
      { name: 'is_archived', note: '0=未归档，1=已归档' },
    ]
  },
  teams: {
    desc: '项目组表，是系统最顶层的业务隔离单元，测试计划、通知机器人等均归属于项目组。',
    scene: '不同产品团队创建各自的项目组，数据天然隔离，成员只能看到自己项目组的内容。',
    relations: [
      { table: 'user_teams', via: 'teams.id → user_teams.team_id  （成员）' },
      { table: 'team_projects', via: 'teams.id → team_projects.team_id  （用例库）' },
      { table: 'test_plans', via: 'teams.id → test_plans.team_id' },
    ],
    fields: [
      { name: 'leader_id', note: '项目组负责人，可管理成员和计划' },
      { name: 'department_id', note: '所属组织，关联 departments.id' },
      { name: 'status', note: '1=启用，0=禁用' },
    ]
  },
  test_suites: {
    desc: '测试套件表，是可复用的用例集合，可以从套件快速初始化测试计划。',
    scene: '将常用的回归测试用例集合打包为套件，每次新建测试计划时一键导入，避免重复选择。',
    relations: [
      { table: 'test_suite_test_cases', via: 'test_suites.id → test_suite_test_cases.test_suite_id' },
      { table: 'test_plans', via: 'test_suites.id → test_plans.suite_id  （初始化来源）' },
    ],
    fields: []
  },
  test_suite_test_cases: {
    desc: '测试套件与测试用例的多对多关联表。',
    scene: '管理套件包含哪些用例；添加套件到计划时从此表批量读取用例 ID。',
    relations: [
      { table: 'test_suites', via: 'test_suite_id → test_suites.id' },
      { table: 'test_cases', via: 'test_case_id → test_cases.id' },
    ],
    fields: []
  },
  system_logs: {
    desc: '系统操作日志表，记录所有增删改操作的完整审计轨迹。',
    scene: '用于操作审计、问题溯源、合规要求；管理员可在日志页面按模块/用户/时间筛选查询。',
    relations: [
      { table: 'users', via: 'user_id → users.id' },
    ],
    fields: [
      { name: 'module', note: '操作模块：testcases / testplans / users 等' },
      { name: 'action', note: '操作类型：create / update / delete / import / export 等' },
      { name: 'description', note: '人类可读的操作描述' },
    ]
  },
  notifications: {
    desc: '通知主表，存储系统生成的所有通知消息，支持站内信和钉钉推送。',
    scene: '测试计划分配、报告审核通过/拒绝等事件触发后，系统自动创建通知并推送给相关人员。',
    relations: [
      { table: 'notification_recipients', via: 'notifications.id → notification_recipients.notification_id' },
    ],
    fields: [
      { name: 'notification_type', note: 'testcase / testplan / execution / report' },
      { name: 'dingtalk_status', note: '钉钉推送状态：null / pending / sent / failed' },
    ]
  },
  notification_recipients: {
    desc: '通知接收人表，记录每条通知的接收人以及已读状态。',
    scene: '前端未读消息角标和消息列表均从此表查询当前用户的未读/全部通知。',
    relations: [
      { table: 'notifications', via: 'notification_id → notifications.id' },
      { table: 'users', via: 'user_id → users.id' },
    ],
    fields: [
      { name: 'is_read', note: '是否已读，true=已读' },
      { name: 'read_at', note: '阅读时间' },
    ]
  },
  modules: {
    desc: '模块表，管理测试用例的模块树形结构，支持多级嵌套，每个模块可设置 RD 负责人。',
    scene: '在用例库中定义模块目录结构；测试计划报告中的模块通过率统计依赖此表的 rd_owner 字段。',
    relations: [
      { table: 'projects', via: 'project_id → projects.id' },
      { table: 'modules', via: 'parent_id → modules.id  （自关联，树形结构）' },
    ],
    fields: [
      { name: 'tag', note: '模块缩写，参与用例编号生成' },
      { name: 'sort_order', note: '自定义排序序号' },
      { name: 'rd_owner', note: 'RD 负责人姓名，用于报告中标注模块责任人' },
    ]
  },
  testcase_history: {
    desc: '测试用例历史记录表，记录每次字段级变更的前后值，实现操作追溯。',
    scene: '用例详情页的"变更历史"功能从此表读取，可以看到谁在什么时候改了哪个字段。',
    relations: [
      { table: 'test_cases', via: 'testcase_id → test_cases.id' },
      { table: 'users', via: 'changed_by → users.id' },
    ],
    fields: [
      { name: 'field_name', note: '修改的字段名' },
      { name: 'old_value / new_value', note: '修改前后的值' },
    ]
  },
  roles: {
    desc: '角色表，定义系统内的权限角色，每个角色持有一组权限码（JSON 存储）。',
    scene: '角色管理页面维护角色权限；登录后根据用户角色决定可见菜单和可执行操作。',
    relations: [
      { table: 'user_roles', via: 'roles.id → user_roles.role_id' },
    ],
    fields: [
      { name: 'permissions', note: 'JSON 数组，权限码列表' },
      { name: 'is_system', note: 'true=系统内置角色，不可删除' },
    ]
  },
  user_roles: {
    desc: '用户与角色的多对多关联表。',
    scene: '给用户分配角色时写入此表；鉴权时查此表判断用户拥有哪些角色。',
    relations: [
      { table: 'users', via: 'user_id → users.id' },
      { table: 'roles', via: 'role_id → roles.id' },
    ],
    fields: []
  },
  user_projects: {
    desc: '用户与用例库的授权关联表，控制哪些用户有权访问哪个用例库。',
    scene: '项目授权页面操作此表；用户进入用例库前先查此表验证权限。',
    relations: [
      { table: 'users', via: 'user_id → users.id' },
      { table: 'projects', via: 'project_id → projects.id' },
    ],
    fields: []
  },
  test_case_zmind_links: {
    desc: '测试用例与 Zmind 问题单的关联表，记录用例关联的缺陷单。',
    scene: '执行失败时在执行页关联 Zmind 问题单；报告中统计 PR 关联情况时从此表读取。',
    relations: [
      { table: 'test_cases', via: 'test_case_id → test_cases.id' },
      { table: 'test_plans', via: 'test_plan_id → test_plans.id  （问题单所属计划）' },
    ],
    fields: [
      { name: 'zmind_issue_id', note: 'Zmind 问题单 ID（字符串）' },
      { name: 'zmind_issue_status', note: '同步自 Zmind 的问题单状态' },
    ]
  },
  review_plans: {
    desc: '用例评审计划表，用于组织一次正式的用例评审活动，涵盖评审人、时间范围和状态流转。',
    scene: '上线前的用例质量把关；通过后自动更新对应用例的 status 为 REVIEWED。',
    relations: [
      { table: 'review_plan_testcases', via: 'review_plans.id → review_plan_testcases.review_plan_id' },
      { table: 'teams', via: 'team_id → teams.id' },
    ],
    fields: [
      { name: 'status', note: 'PENDING / IN_PROGRESS / COMPLETED / CANCELLED' },
      { name: 'reviewer_ids', note: 'JSON 数组，评审人 ID 列表' },
    ]
  },
  review_plan_testcases: {
    desc: '评审计划与测试用例的关联表，记录每条用例在某次评审中的草稿意见和最终结论。',
    scene: '评审人逐条标记通过/拒绝/废弃（写入 pending_ 草稿字段），计划提交后才升级为正式结论。',
    relations: [
      { table: 'review_plans', via: 'review_plan_id → review_plans.id' },
      { table: 'test_cases', via: 'testcase_id → test_cases.id' },
    ],
    fields: [
      { name: 'pending_review_result', note: '草稿结论，提交前可修改' },
      { name: 'review_result', note: '正式结论，提交后写入' },
      { name: 'testcase_status_snapshot', note: '提交时快照的用例状态' },
    ]
  },
  departments: {
    desc: '组织（部门）表，是高于项目组的管理层级，用于对项目组进行分组管理。',
    scene: '大团队可按部门划分项目组，便于跨组统计和权限管理。',
    relations: [
      { table: 'teams', via: 'departments.id → teams.department_id' },
      { table: 'user_departments', via: 'departments.id → user_departments.department_id' },
    ],
    fields: []
  },
  comments: {
    desc: '评论表，支持在测试计划、测试用例、测试执行上添加多级评论。',
    scene: '团队成员在用例或执行记录上讨论问题，支持回复形成评论树。',
    relations: [
      { table: 'users', via: 'author_id → users.id' },
      { table: 'comments', via: 'parent_id → comments.id  （自关联，回复）' },
    ],
    fields: [
      { name: 'entity_type', note: '关联对象类型：testplan / testcase / execution' },
      { name: 'entity_id', note: '关联对象 ID' },
    ]
  },
  test_execution_attachments: {
    desc: '测试执行附件表，存储执行时上传的截图、日志等附件（Base64 编码存入数据库）。',
    scene: '执行 FAIL/BLOCK 时上传问题截图，作为缺陷的佐证材料。',
    relations: [
      { table: 'test_executions', via: 'execution_id → test_executions.id' },
    ],
    fields: [
      { name: 'file_data', note: 'Base64 编码的文件内容，直接存库' },
      { name: 'is_deleted', note: '软删除标志' },
    ]
  },
  test_case_attachments: {
    desc: '测试用例附件表，存储用例本身的参考资料、设计文档等附件。',
    scene: '用例编辑时上传辅助文档，执行时可查阅原始资料。',
    relations: [
      { table: 'test_cases', via: 'test_case_id → test_cases.id' },
    ],
    fields: [
      { name: 'file_data', note: 'Base64 编码的文件内容' },
      { name: 'is_deleted', note: '软删除标志' },
    ]
  },
  dingtalk_bots: {
    desc: '钉钉机器人配置表，每个项目组可以配置一个或多个群机器人，用于推送测试通知。',
    scene: '测试计划状态变更、报告审核结果等事件触发后，通过对应项目组的机器人推送消息到钉钉群。',
    relations: [
      { table: 'teams', via: 'team_id → teams.id' },
    ],
    fields: [
      { name: 'security_type', note: '安全方式：keyword（关键词）/ sign（加签）' },
      { name: 'notification_types', note: 'JSON 数组，订阅的通知类型' },
    ]
  },
}

// ── 视图切换 ──────────────────────────────────────────────
const activeView = ref('table')
function switchView(v) { activeView.value = v }

// ── 表格视图 ──────────────────────────────────────────────
const tables       = ref([])
const tableKeyword = ref('')
const selectedTable = ref('')
const columns      = ref([])
const primaryKeys  = ref([])
const rows         = ref([])
const total        = ref(0)
const page         = ref(1)
const size         = ref(20)
const rowKeyword   = ref('')
const loadingRows  = ref(false)

const filteredTables = computed(() => {
  const kw = tableKeyword.value.trim().toLowerCase()
  return kw ? tables.value.filter(t => t.toLowerCase().includes(kw)) : tables.value
})

// 当前表的说明
const docVisible = ref(false)
const tableDoc = computed(() => selectedTable.value ? TABLE_DOCS[selectedTable.value] || null : null)

// ── SQL 视图 ──────────────────────────────────────────────
const sql           = ref('')
const sqlRunning    = ref(false)
const sqlResultType = ref('')
const sqlRows       = ref([])
const sqlError      = ref('')
const affected      = ref(0)
const sqlPage       = ref(1)
const sqlPageSize   = 50

const sqlColumns   = computed(() => sqlRows.value[0] ? Object.keys(sqlRows.value[0]) : [])
const pagedSqlRows = computed(() => {
  const s = (sqlPage.value - 1) * sqlPageSize
  return sqlRows.value.slice(s, s + sqlPageSize)
})

// ── 编辑 Dialog ───────────────────────────────────────────
const editDialogVisible = ref(false)
const editMode          = ref('create')
const editForm          = ref({})
const editingPk         = ref({})

// ── 备份/恢复 ─────────────────────────────────────────────
const backupDialogVisible  = ref(false)
const restoreDialogVisible = ref(false)
const selectedTables       = ref([])
const restoreFile          = ref(null)
const restoreLoading       = ref(false)
const restoreProgress      = ref(0)
const restoreMessage       = ref('')
const restoreStatus        = ref('')
const restoreMode          = ref('append')
const uploadRef            = ref(null)
const cancellingTask       = ref(false)
const backupLoading        = ref(false)
let currentTaskId = null
let restoreTimer  = null

// ── 核心方法 ──────────────────────────────────────────────
async function loadTables() {
  const res = await getDatabaseTables()
  tables.value = res.data.tables || []
  if (!selectedTable.value && tables.value.length) await selectTable(tables.value[0])
}

async function selectTable(t) {
  selectedTable.value = t
  page.value = 1
  const res = await getTableSchema(t)
  columns.value    = res.data.columns      || []
  primaryKeys.value = res.data.primary_keys || []
  await loadRows()
}

async function loadRows() {
  if (!selectedTable.value) return
  loadingRows.value = true
  try {
    const res = await getTableRows(selectedTable.value, { page: page.value, size: size.value, keyword: rowKeyword.value || undefined })
    rows.value  = res.data.records || []
    total.value = res.data.total   || 0
  } finally {
    loadingRows.value = false
  }
}

function onPageChange(p) { page.value = p; loadRows() }

function openCreate() {
  editMode.value = 'create'
  const form = {}
  columns.value.forEach(c => { form[c.name] = '' })
  editForm.value  = form
  editingPk.value = {}
  editDialogVisible.value = true
}

function openEdit(row) {
  editMode.value = 'edit'
  editForm.value = { ...row }
  const pk = {}
  primaryKeys.value.forEach(k => { pk[k] = row[k] })
  editingPk.value = pk
  editDialogVisible.value = true
}

async function submitEdit() {
  if (!selectedTable.value) return
  editMode.value === 'create'
    ? await createTableRow(selectedTable.value, editForm.value)
    : await updateTableRow(selectedTable.value, editingPk.value, editForm.value)
  ElMessage.success(editMode.value === 'create' ? '新增成功' : '更新成功')
  editDialogVisible.value = false
  loadRows()
}

async function removeRow(row) {
  const pk = {}
  primaryKeys.value.forEach(k => { pk[k] = row[k] })
  if (!Object.keys(pk).length) { ElMessage.warning('该表无主键，无法删除'); return }
  await ElMessageBox.confirm('确认删除该行？此操作不可撤销。', '警告', { type: 'warning' })
  await deleteTableRow(selectedTable.value, pk)
  ElMessage.success('已删除')
  loadRows()
}

async function runSql() {
  if (!sql.value.trim()) return
  sqlRunning.value    = true
  sqlResultType.value = ''
  sqlError.value      = ''
  sqlPage.value       = 1
  try {
    const res = await executeDatabaseSql(sql.value)
    sqlResultType.value = res.data.type
    if (res.data.type === 'query') { sqlRows.value = res.data.rows || []; affected.value = 0 }
    else { sqlRows.value = []; affected.value = res.data.affected || 0 }
  } catch (e) {
    sqlResultType.value = 'error'
    sqlError.value = e?.response?.data?.detail || e?.message || '执行失败'
  } finally {
    sqlRunning.value = false
  }
}

// ── 备份 / 恢复 ───────────────────────────────────────────
async function handleBackup() { backupDialogVisible.value = true }

async function doBackup() {
  backupLoading.value = true
  try {
    const res = await backupDatabase(selectedTables.value.length ? selectedTables.value : undefined)
    const url  = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href  = url
    link.download = `backup_${new Date().toISOString().replace(/[:.]/g,'-').slice(0,19)}.sql`
    document.body.appendChild(link); link.click(); document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success('备份导出成功')
    backupDialogVisible.value = false
    selectedTables.value = []
  } catch (e) { ElMessage.error('备份失败: ' + (e.message || '')) }
  finally { backupLoading.value = false }
}

function openRestoreDialog() {
  restoreFile.value = null; restoreStatus.value = ''; restoreProgress.value = 0
  restoreMessage.value = ''; restoreMode.value = 'append'; currentTaskId = null
  cancellingTask.value = false
  if (restoreTimer) { clearInterval(restoreTimer); restoreTimer = null }
  if (uploadRef.value) uploadRef.value.clearFiles()
  restoreDialogVisible.value = true
}

function onRestoreDialogClosed() {
  if (restoreTimer) { clearInterval(restoreTimer); restoreTimer = null }
  restoreLoading.value = false
  if (restoreStatus.value === 'running') restoreStatus.value = ''
  if (uploadRef.value) uploadRef.value.clearFiles()
}

function handleFileChange(f) { restoreFile.value = f.raw }

async function doRestore() {
  if (!restoreFile.value) { ElMessage.warning('请选择 SQL 文件'); return }
  const label = restoreMode.value === 'upsert' ? '覆盖' : '追加'
  try {
    await ElMessageBox.confirm(`确认以「${label}」模式导入？`, '导入确认', { type: restoreMode.value === 'upsert' ? 'warning' : 'info' })
  } catch { return }
  restoreLoading.value = true; restoreStatus.value = 'running'; restoreProgress.value = 0
  restoreMessage.value = '正在启动…'; currentTaskId = null
  try {
    const res = await restoreDatabase(restoreFile.value, restoreMode.value)
    if (res.data?.task_id) {
      currentTaskId = res.data.task_id
      restoreTimer = setInterval(async () => {
        try {
          const r = await getRestoreProgress(currentTaskId)
          const t = r.data
          restoreProgress.value = t.progress || 0; restoreMessage.value = t.message || ''; restoreStatus.value = t.status
          if (['completed','failed','cancelled'].includes(t.status)) {
            clearInterval(restoreTimer); restoreTimer = null; restoreLoading.value = false; cancellingTask.value = false
            if (t.status === 'completed') { ElMessage.success(t.message || '恢复成功'); restoreDialogVisible.value = false; loadTables() }
            else if (t.status === 'failed') ElMessage.error(t.message || '恢复失败')
            else { ElMessage.warning(t.message || '已取消'); restoreDialogVisible.value = false; loadTables() }
          }
        } catch { clearInterval(restoreTimer); restoreTimer = null; restoreLoading.value = false; ElMessage.error('查询进度失败') }
      }, 800)
    } else { ElMessage.success(res.message || '恢复成功'); restoreDialogVisible.value = false; restoreLoading.value = false }
  } catch (e) { restoreLoading.value = false; restoreStatus.value = 'failed'; ElMessage.error('恢复失败: ' + (e?.response?.data?.detail || e?.message || '')) }
}

async function doCancelRestore() {
  if (!currentTaskId) return
  try { await ElMessageBox.confirm('确定中止恢复任务？已插入的数据不会回滚。', '确认', { type: 'warning' }) } catch { return }
  cancellingTask.value = true
  try { await cancelRestoreTask(currentTaskId); restoreMessage.value = '正在中止，等待当前批次完成…' }
  catch (e) { cancellingTask.value = false; ElMessage.error('中止失败') }
}

onMounted(loadTables)
</script>

<style scoped>
/* ── 页面骨架 ────────────────────────────────────────────── */
.db-page {
  display: grid;
  grid-template-columns: 240px 1fr;
  gap: 12px;
  height: calc(100vh - 80px);
  overflow: hidden;
  font-size: 13px;
}

/* ── 左侧侧边栏 ──────────────────────────────────────────── */
.db-sidebar {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 12px 8px 8px;
}
.sidebar-header {
  font-size: 12px;
  font-weight: 600;
  color: #8c8c8c;
  letter-spacing: .5px;
  text-transform: uppercase;
  padding: 0 6px 10px;
}
.sidebar-search {
  position: relative;
  margin-bottom: 6px;
  padding: 0 2px;
}
.sidebar-search .search-icon {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  width: 13px;
  height: 13px;
  color: #bfbfbf;
  pointer-events: none;
}
.sidebar-search .search-input {
  width: 100%;
  height: 30px;
  padding: 0 8px 0 30px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-size: 12px;
  color: #262626;
  background: #fafafa;
  outline: none;
  box-sizing: border-box;
  transition: border-color .2s;
}
.sidebar-search .search-input:focus { border-color: #595959; background: #fff; }

.table-list { flex: 1; overflow-y: auto; padding: 2px 0; }
.table-list::-webkit-scrollbar { width: 3px; }
.table-list::-webkit-scrollbar-thumb { background: #e0e0e0; border-radius: 3px; }

.table-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 6px 8px;
  border-radius: 6px;
  cursor: pointer;
  color: #595959;
  transition: background .12s, color .12s;
}
.table-item:hover { background: #f5f5f5; }
.table-item.active { background: #f0f0f0; color: #141414; font-weight: 500; }
.table-name { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 12.5px; }

/* ── 右侧主区域 ──────────────────────────────────────────── */
.db-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  overflow: hidden;
}

/* ── Tab 栏 ──────────────────────────────────────────────── */
.view-tabs {
  position: relative;
  display: inline-flex;
  background: #f0f0f0;
  border-radius: 7px;
  padding: 3px;
  margin-bottom: 10px;
  align-self: flex-start;
  gap: 2px;
}
.view-tab {
  position: relative;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 18px;
  border: none;
  background: transparent;
  border-radius: 5px;
  font-size: 13px;
  font-weight: 500;
  color: #8c8c8c;
  cursor: pointer;
  transition: color .18s;
  min-width: 106px;
  justify-content: center;
}
.view-tab.active { color: #141414; }
.view-tab:hover:not(.active) { color: #595959; }

.tab-pill {
  position: absolute;
  inset: 3px;
  width: calc(50% - 3px);
  background: #fff;
  border-radius: 5px;
  box-shadow: 0 1px 3px rgba(0,0,0,.1);
  transition: transform .28s cubic-bezier(.4,0,.2,1);
  pointer-events: none;
}

/* ── 滑动容器 ────────────────────────────────────────────── */
.slider-wrap { flex: 1; overflow: hidden; border-radius: 8px; }
.slider {
  display: flex;
  width: 200%;
  height: 100%;
  transition: transform .3s cubic-bezier(.4,0,.2,1);
}
.panel {
  width: 50%;
  height: 100%;
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* ── 面板工具栏 ──────────────────────────────────────────── */
.panel-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
  gap: 10px;
  flex-wrap: wrap;
}
.bar-left { display: flex; align-items: center; gap: 8px; }
.bar-right { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-left: auto; }
.panel-title { font-weight: 600; font-size: 13.5px; color: #262626; }

/* 表说明按钮 */
.doc-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 9px;
  border: 1px solid #d9d9d9;
  border-radius: 5px;
  background: #fafafa;
  font-size: 12px;
  color: #595959;
  cursor: pointer;
  transition: border-color .15s, color .15s;
}
.doc-btn:hover { border-color: #8c8c8c; color: #262626; }

/* ── 统一按钮 ────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 30px;
  padding: 0 13px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: background .15s, border-color .15s, color .15s, opacity .15s;
  white-space: nowrap;
}
.btn:disabled { opacity: .45; cursor: not-allowed; }

.btn-primary  { background: #262626; color: #fff; border-color: #262626; }
.btn-primary:not(:disabled):hover  { background: #3d3d3d; border-color: #3d3d3d; }

.btn-default  { background: #fff; color: #262626; border-color: #d9d9d9; }
.btn-default:not(:disabled):hover  { border-color: #8c8c8c; }

.btn-ghost    { background: transparent; color: #595959; border-color: #d9d9d9; }
.btn-ghost:not(:disabled):hover    { color: #262626; border-color: #8c8c8c; }

.btn-danger   { background: #fff; color: #ff4d4f; border-color: #ff4d4f; }
.btn-danger:not(:disabled):hover   { background: #fff1f0; }

/* 工具栏搜索框 */
.search-box {
  position: relative;
  display: flex;
  align-items: center;
}
.search-box .search-icon {
  position: absolute;
  left: 9px;
  width: 13px;
  height: 13px;
  color: #bfbfbf;
  pointer-events: none;
}
.search-box .search-input {
  height: 30px;
  width: 230px;
  padding: 0 10px 0 30px;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  font-size: 13px;
  color: #262626;
  background: #fff;
  outline: none;
  box-sizing: border-box;
  transition: border-color .18s;
}
.search-box .search-input:focus { border-color: #595959; }

/* ── 表格区 ──────────────────────────────────────────────── */
/* 给 .table-wrap 一个确定高度，el-table height="100%" 才能生效固定表头 */
.table-wrap {
  flex: 1;
  min-height: 0;
  /* panel = 100vh - 80px(layout) - 210px(toolbar+footer) */
  height: calc(100vh - 290px);
  overflow: hidden;
}

/* 单元格省略 div —— 配合 table-layout:fixed 保证截断 */
.cell-ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  width: 100%;
}

/* 操作列：不截断，保证按钮完整显示；fixed 列自带独立滚动层不受影响 */
.table-wrap :deep(.col-action .cell),
.sql-table-wrap :deep(.col-action .cell) {
  overflow: visible !important;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 0 8px;
}

/* 行操作按钮 */
.op-btn {
  border: none;
  background: transparent;
  font-size: 12.5px;
  cursor: pointer;
  color: #595959;
  padding: 2px 6px;
  border-radius: 4px;
  transition: color .15s, background .15s;
}
.op-btn:hover        { color: #141414; background: #f0f0f0; }
.op-btn.danger       { color: #8c8c8c; }
.op-btn.danger:hover { color: #ff4d4f; background: #fff1f0; }

/* ── 底部分页 ────────────────────────────────────────────── */
.panel-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 6px 14px;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.count-label { font-size: 12.5px; color: #8c8c8c; white-space: nowrap; }

/* ── SQL 编辑器 ──────────────────────────────────────────── */
.shortcut-hint { font-size: 12px; color: #bfbfbf; }
.sql-editor-area { padding: 12px 14px 6px; flex-shrink: 0; }
.sql-editor {
  width: 100%;
  height: 160px;
  padding: 10px 12px;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  font-family: 'JetBrains Mono', 'Fira Code', Consolas, monospace;
  font-size: 13px;
  line-height: 1.65;
  color: #262626;
  resize: vertical;
  outline: none;
  box-sizing: border-box;
  background: #fafafa;
  transition: border-color .18s;
}
.sql-editor:focus { border-color: #595959; background: #fff; }

/* ── SQL 结果 ────────────────────────────────────────────── */
.sql-result-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 0 14px;
}
.result-status {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 0 4px;
  font-size: 13px;
  color: #595959;
  flex-shrink: 0;
}
.result-status.error { color: #ff4d4f; }
.sql-table-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: calc(100vh - 490px);
  min-height: 120px;
}

/* ── 抽屉：表说明 ────────────────────────────────────────── */
.doc-drawer { padding: 0 4px; }
.doc-section { margin-bottom: 22px; }
.doc-section-title { font-size: 13px; font-weight: 600; color: #262626; margin-bottom: 8px; }
.doc-text { font-size: 13px; color: #595959; line-height: 1.7; margin: 0; }

.rel-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 10px;
  border-left: 2px solid #e8e8e8;
  margin-bottom: 6px;
}
.rel-table { font-size: 13px; font-weight: 600; color: #262626; font-family: monospace; }
.rel-via   { font-size: 12px; color: #8c8c8c; }

.field-list { display: flex; flex-direction: column; gap: 1px; }
.field-row {
  display: flex;
  gap: 12px;
  align-items: baseline;
  padding: 6px 8px;
  border-radius: 5px;
  transition: background .12s;
}
.field-row:hover { background: #fafafa; }
.field-name {
  font-size: 12px;
  font-family: 'JetBrains Mono', Consolas, monospace;
  color: #262626;
  background: #f5f5f5;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
  flex-shrink: 0;
}
.field-note { font-size: 12.5px; color: #8c8c8c; line-height: 1.5; }
</style>

<!-- tooltip 挂 body 层，不受 scoped/overflow:hidden 影响 -->
<style>
.db-cell-tooltip.el-popper {
  max-width: 500px;
  word-break: break-all;
  font-size: 12px;
  line-height: 1.6;
}
</style>
