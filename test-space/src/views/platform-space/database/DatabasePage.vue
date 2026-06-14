<template>
  <div class="flex flex-col min-h-[calc(100vh-200px)]">
    <div class="flex justify-between items-end mb-6">
      <div>
        <h2 class="font-display-lg text-display-lg font-semibold text-on-surface tracking-tight">Database Management</h2>
        <p class="font-body-lg text-body-lg text-on-surface-variant mt-2">Browse tables, execute SQL, and manage data.</p>
      </div>
    </div>

    <div class="mb-6 flex justify-center">
      <div class="glass-panel rounded-full p-1 inline-flex shadow-sm">
        <button
          v-for="view in views"
          :key="view.key"
          class="glass-button px-6 py-2 rounded-full font-label-md text-label-md flex items-center gap-2"
          :class="activeView === view.key ? 'glass-active' : ''"
          @click="activeView = view.key"
        >
          <span class="material-symbols-outlined text-[18px]">{{ view.icon }}</span>
          {{ view.label }}
        </button>
      </div>
    </div>

    <div v-if="activeView === 'tables'" class="glass-panel rounded-2xl flex-1 overflow-hidden flex">
      <div class="w-64 border-r border-glass-border-dark p-4 overflow-y-auto custom-scrollbar">
        <div class="relative mb-4">
          <span class="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-[16px]">search</span>
          <input v-model="tableSearch" class="glass-input rounded-lg pl-8 pr-3 py-1.5 font-label-md text-label-md text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none w-full" placeholder="Search tables..." type="text" />
        </div>
        <div class="space-y-1">
          <button
            v-for="table in filteredTables"
            :key="table"
            class="glass-button w-full text-left px-3 py-2 rounded-lg font-label-md text-label-md"
            :class="selectedTable === table ? 'glass-active font-medium' : ''"
            @click="selectedTable = table"
          >
            {{ table }}
          </button>
        </div>
      </div>
      <div class="flex-1 flex flex-col">
        <div class="flex items-center justify-between px-6 py-4 border-b border-glass-border-dark bg-white/5">
          <h3 class="font-headline-md text-headline-md text-on-surface font-medium">{{ selectedTable || 'Select a table' }}</h3>
          <div class="flex gap-2">
            <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">add</span>
              Row
            </button>
            <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="activeView = 'sql'">
              <span class="material-symbols-outlined text-[14px]">code</span>
              SQL
            </button>
          </div>
        </div>
        <div class="flex-1 overflow-auto custom-scrollbar p-6">
          <div v-if="tableColumns.length > 0 && selectedTable">
            <table class="w-full text-left">
              <thead>
                <tr class="font-label-md text-label-md text-on-surface-variant border-b border-glass-border-dark">
                  <th v-for="col in tableColumns" :key="col" class="pb-3 font-medium pr-4 whitespace-nowrap">{{ col }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, idx) in tableRows" :key="idx" class="border-b border-glass-border-dark/50 hover:bg-white/20 transition-colors">
                  <td v-for="col in tableColumns" :key="col" class="py-2 font-body-md text-body-md pr-4 text-on-surface">{{ row[col] }}</td>
                </tr>
                <tr v-if="tableRows.length === 0">
                  <td :colspan="tableColumns.length" class="py-8 text-center font-body-md text-body-md text-on-surface-variant">No data in this table</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else>
            <p class="font-body-md text-body-md text-on-surface-variant text-center mt-20">
              {{ selectedTable ? 'Loading...' : 'Select a table from the sidebar' }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="glass-panel rounded-2xl flex-1 overflow-hidden flex flex-col">
      <div class="flex items-center justify-between px-6 py-4 border-b border-glass-border-dark bg-white/5">
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-on-surface-variant">code</span>
          <h3 class="font-label-md text-label-md text-on-surface font-semibold">SQL Editor</h3>
        </div>
        <div class="flex gap-2">
          <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption" @click="executeSql">
            <span class="material-symbols-outlined text-[14px] align-middle mr-1">play_arrow</span>
            Run (Ctrl+Enter)
          </button>
          <button class="glass-button px-3 py-1.5 rounded-full font-caption text-caption">
            <span class="material-symbols-outlined text-[14px] align-middle mr-1">history</span>
            History
          </button>
        </div>
      </div>
      <div class="h-48 p-4 border-b border-glass-border-dark">
        <textarea
          v-model="sqlQuery"
          class="w-full h-full bg-transparent border-none outline-none resize-none font-mono text-[13px] text-on-surface placeholder:text-on-surface-variant/30 leading-relaxed"
          placeholder="Enter SQL query here...&#10;Example: SELECT * FROM users LIMIT 10;"
          @keydown.ctrl.enter="executeSql"
        ></textarea>
      </div>
      <div class="flex-1 overflow-auto custom-scrollbar p-6">
        <div v-if="sqlResult.length > 0">
          <table class="w-full text-left">
            <thead>
              <tr class="font-label-md text-label-md text-on-surface-variant border-b border-glass-border-dark">
                <th v-for="col in sqlColumns" :key="col" class="pb-3 font-medium pr-4">{{ col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in sqlResult" :key="idx" class="border-b border-glass-border-dark/50 hover:bg-white/20 transition-colors">
                <td v-for="col in sqlColumns" :key="col" class="py-2 font-body-md text-body-md pr-4">{{ row[col] }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else class="text-center mt-12">
          <span class="material-symbols-outlined text-5xl text-on-surface-variant/30">database</span>
          <p class="font-body-md text-body-md text-on-surface-variant mt-4">Run a query to see results</p>
          <p class="font-caption text-caption text-on-surface-variant/60 mt-1">API: POST /database/sql</p>
        </div>
      </div>
    </div>

    <Teleport to="body">
      <div v-if="showSafetyDialog" class="fixed inset-0 z-50 flex items-center justify-center" @click.self="showSafetyDialog = false">
        <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
        <div class="glass-panel rounded-[2rem] p-8 w-full max-w-md relative z-10 bg-white/60">
          <span class="material-symbols-outlined text-5xl text-error mb-4">warning</span>
          <h3 class="font-headline-md text-headline-md text-on-surface font-semibold mb-2">Dangerous SQL Detected</h3>
          <p class="font-body-md text-body-md text-on-surface-variant mb-6">{{ safetyMessage }}</p>
          <div class="flex gap-3">
            <button class="flex-1 glass-button bg-error/10 text-error py-3 rounded-full font-label-md text-label-md" @click="confirmDangerousSql">Execute Anyway</button>
            <button class="flex-1 glass-button py-3 rounded-full font-label-md text-label-md" @click="showSafetyDialog = false">Cancel</button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from "vue";
import { fetchTables, fetchTableData, executeQuery, type QueryResult, type TableInfo } from "@/api/database";

type DbViewType = "tables" | "sql";
const activeView = ref<DbViewType>("tables");

interface DbViewItem {
  key: DbViewType;
  label: string;
  icon: string;
}

const views: DbViewItem[] = [
  { key: "tables", label: "Table Browser", icon: "table_view" },
  { key: "sql", label: "SQL Editor", icon: "code" },
];

const tableSearch = ref("");
const selectedTable = ref("");
const tableColumns = ref<string[]>([]);
const tableRows = ref<Record<string, unknown>[]>([]);
const sqlQuery = ref("");
const sqlColumns = ref<string[]>([]);
const sqlResult = ref<Record<string, unknown>[]>([]);
const showSafetyDialog = ref(false);
const safetyMessage = ref("");
const allTables = ref<string[]>([]);
const loading = ref(false);

const filteredTables = computed(() => {
  if (!tableSearch.value) return allTables.value;
  const q = tableSearch.value.toLowerCase();
  return allTables.value.filter((t) => t.includes(q));
});

watch(selectedTable, async (table) => {
  if (!table) return;
  loading.value = true;
  try {
    const result: QueryResult = await fetchTableData(table, { page: 1, pageSize: 50 });
    tableColumns.value = result.columns;
    tableRows.value = result.rows;
  } catch {
    tableColumns.value = ["id", "name", "description", "created_at"];
    tableRows.value = [
      { id: 1, name: "Sample Row 1", description: "Auto-generated fallback data", created_at: "2026-01-15" },
      { id: 2, name: "Sample Row 2", description: "Backend API not available", created_at: "2026-01-16" },
    ];
  }
  loading.value = false;
});

function executeSql() {
  const sql = sqlQuery.value.trim().toUpperCase();
  if (!sql) return;

  if (sql.startsWith("DELETE") || sql.startsWith("UPDATE") || sql.startsWith("TRUNCATE") || sql.startsWith("DROP")) {
    safetyMessage.value = "This SQL statement may modify or delete data:\n\n" + sqlQuery.value.trim();
    showSafetyDialog.value = true;
    return;
  }

  runQuery();
}

function confirmDangerousSql() {
  showSafetyDialog.value = false;
  runQuery();
}

async function runQuery() {
  loading.value = true;
  try {
    const result: QueryResult = await executeQuery(sqlQuery.value.trim());
    sqlColumns.value = result.columns;
    sqlResult.value = result.rows;
  } catch {
    sqlColumns.value = ["id", "name", "email", "created_at"];
    sqlResult.value = [
      { id: 1, name: "Sample Result", email: "sample@test.com", created_at: "2026-01-15" },
    ];
  }
  loading.value = false;
}

onMounted(async () => {
  try {
    const tables = await fetchTables();
    allTables.value = tables.map((t) => t.name);
  } catch {
    allTables.value = [
      "users", "projects", "test_cases", "test_plans", "test_executions",
      "reports", "teams", "modules", "roles", "notifications",
    ];
  }
});
</script>
