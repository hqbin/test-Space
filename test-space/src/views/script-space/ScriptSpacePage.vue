<template>
  <div class="pt-12">
    <div class="flex justify-between items-end mb-8">
      <div>
        <h2 class="font-display-lg text-display-lg font-semibold text-on-surface tracking-tight">Script Space</h2>
        <p class="font-body-lg text-body-lg text-on-surface-variant mt-2">Manage and execute automation scripts.</p>
      </div>
      <button class="glass-button px-6 py-2 rounded-full font-label-md text-label-md flex items-center gap-2">
        <span class="material-symbols-outlined text-[18px]">add</span>
        New Script
      </button>
    </div>

    <!-- Category Cards with script list -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-gutter-grid mb-8">
      <div v-for="cat in categories" :key="cat.name" class="glass-card rounded-xl p-padding-card cursor-pointer glass-hover" @click="selectCategory(cat)">
        <div class="flex items-center gap-3 mb-4">
          <div class="w-10 h-10 rounded-lg bg-secondary-fixed flex items-center justify-center text-on-secondary-fixed-variant" :class="selectedCategory?.name === cat.name ? 'ring-2 ring-primary' : ''">
            <span class="material-symbols-outlined">{{ cat.icon }}</span>
          </div>
          <div>
            <h3 class="font-headline-md text-headline-md text-on-surface">{{ cat.name }}</h3>
            <p class="font-caption text-caption text-on-surface-variant">{{ cat.scripts.length }} scripts</p>
          </div>
        </div>
        <div class="space-y-1">
          <div v-for="script in cat.scripts" :key="script.name" class="flex items-center gap-2 px-2 py-1 rounded hover:bg-white/30 transition-colors text-caption text-on-surface-variant">
            <span class="material-symbols-outlined text-[14px]">description</span>
            <span class="flex-1 truncate">{{ script.name }}</span>
          </div>
          <div v-if="cat.scripts.length === 0" class="text-caption text-on-surface-variant/50 italic px-2 py-1">No scripts yet</div>
        </div>
      </div>
    </div>

    <!-- Execution Panel -->
    <div class="glass-panel rounded-2xl overflow-hidden">
      <!-- Header -->
      <div class="flex items-center justify-between px-6 py-4 border-b border-glass-border-dark bg-white/5">
        <div class="flex items-center gap-3">
          <span class="material-symbols-outlined text-on-surface-variant">terminal</span>
          <span class="font-label-md text-label-md text-on-surface font-medium">Execute</span>
          <span v-if="selectedCategory" class="px-2 py-0.5 rounded-full bg-secondary-fixed/50 text-caption text-on-secondary-fixed-variant">{{ selectedCategory.name }}</span>
        </div>
        <div class="flex items-center gap-2">
          <input v-model="inlineCommand" class="glass-input rounded-lg px-3 py-1.5 font-label-md text-label-md text-on-surface placeholder:text-on-surface-variant/60 focus:outline-none w-80" placeholder="Type a command to run..." @keydown.enter="runInline" />
          <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption flex items-center gap-1" @click="runInline">
            <span class="material-symbols-outlined text-[14px]">play_arrow</span>
            Run
          </button>
          <button class="glass-button px-4 py-1.5 rounded-full font-caption text-caption text-on-surface-variant flex items-center gap-1" @click="selectScriptFile">
            <span class="material-symbols-outlined text-[14px]">folder_open</span>
            Browse
          </button>
          <button v-if="output" class="glass-button text-on-surface-variant p-1 rounded" @click="clearOutput">
            <span class="material-symbols-outlined text-[18px]">delete</span>
          </button>
        </div>
      </div>
      <!-- Output Terminal -->
      <div class="bg-[#1a1c1d] p-4 font-mono text-[13px] leading-relaxed min-h-[200px] max-h-[400px] overflow-y-auto logcat-scroll">
        <div v-if="!output" class="text-[#6b6f82]">
          <div class="flex items-center gap-2 mb-2">
            <span class="text-green-400">$</span>
            <span>Select a script or type a command above and click Run.</span>
          </div>
          <div class="flex items-center gap-2 text-[#6b6f82]">
            <span class="text-green-400">$</span>
            <span>Available: Python, BAT, PowerShell, Shell commands</span>
          </div>
        </div>
        <div v-for="(line, idx) in outputLines" :key="idx" class="whitespace-pre-wrap">
          <span v-if="line.startsWith('$')" class="text-green-400">{{ line }}</span>
          <span v-else-if="line.startsWith('Error:') || line.startsWith('error:')" class="text-red-400">{{ line }}</span>
          <span v-else class="text-[#e4e5e7]">{{ line }}</span>
        </div>
        <div v-if="executing" class="flex items-center gap-2 mt-2 text-[#6b6f82]">
          <span class="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
          Executing...
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { useScriptExec } from "@/composables/useScriptExec";

interface Script {
  name: string;
  path?: string;
}

interface Category {
  name: string;
  icon: string;
  scripts: Script[];
}

const { executePython, executeBat, executePowershell, executeShell } = useScriptExec();

const categories = ref<Category[]>([
  { name: "Python", icon: "code", scripts: [{ name: "test_runner.py" }, { name: "data_migration.py" }] },
  { name: "Shell / CMD", icon: "terminal", scripts: [{ name: "setup_env.bat" }, { name: "build_project.sh" }] },
  { name: "PowerShell", icon: "terminal", scripts: [{ name: "deploy.ps1" }, { name: "cleanup.ps1" }] },
]);

const selectedCategory = ref<Category | null>(null);
const inlineCommand = ref("");
const output = ref("");
const executing = ref(false);

const outputLines = computed(() => {
  if (!output.value) return [];
  return output.value.split("\n");
});

function selectCategory(cat: Category) {
  selectedCategory.value = selectedCategory.value?.name === cat.name ? null : cat;
}

async function runInline() {
  if (!inlineCommand.value.trim()) return;
  const cmd = inlineCommand.value.trim();
  output.value = "";
  executing.value = true;
  output.value = `$ ${cmd}\n`;
  try {
    const result = await executeShell(cmd);
    output.value += result.stdout;
    if (result.stderr) output.value += `Error: ${result.stderr}`;
    if (result.exit_code !== 0) output.value += `\n[Exit code: ${result.exit_code}]`;
  } catch (e: any) {
    output.value += `Error: ${e?.message || e}`;
  }
  executing.value = false;
}

async function selectScriptFile() {
  try {
    const { open } = await import("@tauri-apps/plugin-dialog");
    const selected = await open({
      multiple: false,
      filters: [
        { name: "Scripts", extensions: ["py", "bat", "cmd", "ps1", "sh"] },
        { name: "All Files", extensions: ["*"] },
      ],
    });
    if (selected) {
      executing.value = true;
      output.value = `$ Running: ${selected}\n`;
      const ext = selected.toLowerCase().split(".").pop();
      try {
        let result;
        switch (ext) {
          case "py":
            result = await executePython(selected, []);
            break;
          case "bat":
          case "cmd":
            result = await executeBat(selected, []);
            break;
          case "ps1":
            result = await executePowershell(selected, []);
            break;
          default:
            result = await executeShell(selected);
        }
        output.value += result.stdout;
        if (result.stderr) output.value += `Error: ${result.stderr}`;
        if (result.exit_code !== 0) output.value += `\n[Exit code: ${result.exit_code}]`;
      } catch (e: any) {
        output.value += `Error: ${e?.message || e}`;
      }
      executing.value = false;
    }
  } catch {
  }
}

function clearOutput() {
  output.value = "";
}
</script>
