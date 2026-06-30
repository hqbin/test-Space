<template>
  <div class="flex-1 min-h-0 overflow-y-auto select-none px-margin-page pt-safe-area-top pb-4">
    <div class="glass-panel rounded-xl p-padding-card shadow-md flex flex-col min-h-0 overflow-hidden">
      <!-- Language -->
      <div class="flex items-center justify-between gap-4 min-w-0">
        <span class="font-body-md text-body-md text-on-surface font-medium shrink-0">{{ t("settings.language") }}</span>
        <div class="flex gap-2 shrink-0">
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md select-none"
            :class="lang === 'zh' ? 'glass-active' : ''"
            @click="setLanguage('zh')"
          >{{ t("settings.langZh") }}</button>
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md select-none"
            :class="lang === 'en' ? 'glass-active' : ''"
            @click="setLanguage('en')"
          >{{ t("settings.langEn") }}</button>
        </div>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- Appearance -->
      <div class="flex items-center justify-between gap-4 min-w-0">
        <span class="font-body-md text-body-md text-on-surface font-medium shrink-0">{{ t("settings.theme") }}</span>
        <div class="flex flex-wrap gap-2 justify-end">
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-2 select-none"
            :class="theme === 'light' ? 'glass-active' : ''"
            @click="setTheme('light')"
          >
            <span class="material-symbols-outlined text-[18px]">light_mode</span>
            {{ t("settings.themeLight") }}
          </button>
          <button
            class="glass-button px-4 py-2 rounded-full font-label-md text-label-md flex items-center gap-2 select-none"
            :class="theme === 'dark' ? 'glass-active' : ''"
            @click="setTheme('dark')"
          >
            <span class="material-symbols-outlined text-[18px]">dark_mode</span>
            {{ t("settings.themeDark") }}
          </button>
        </div>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- Backup & Restore -->
      <div class="min-w-0">
        <div class="flex flex-col gap-4">
          <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.backup") }}</span>
          <div class="flex flex-col gap-3 min-w-0">
            <div class="relative min-w-0 w-full">
              <input
                class="glass-input w-full min-w-0 px-3 py-2 rounded-lg font-body-md text-body-md outline-none select-text"
                :placeholder="t('settings.cloudDeviceIdPlaceholder')"
                :value="isEditingDeviceId ? deviceId : (deviceDisplayName || deviceId)"
                @focus="isEditingDeviceId = true; showDeviceDropdown = true"
                @blur="isEditingDeviceId = false; handleDeviceIdBlur()"
                @input="deviceId = ($event.target as HTMLInputElement).value"
              />
              <div
                v-if="showDeviceDropdown && deviceIdList.length > 0"
                class="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg shadow-md z-10 max-h-60 overflow-y-auto border border-gray-200"
              >
                <div
                  v-for="item in deviceIdList"
                  :key="item.id"
                  class="px-3 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2 group min-w-0"
                  @mousedown.prevent="selectDeviceId(item.id)"
                >
                  <div class="flex-1 min-w-0 flex items-center gap-2">
                    <span class="truncate">{{ item.name || item.id }}</span>
                    <span v-if="item.name" class="text-[11px] text-gray-400 truncate shrink-0">{{ item.id }}</span>
                  </div>
                  <button
                    class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity px-1 py-0.5 rounded hover:bg-gray-200"
                    @mousedown.stop.prevent="copyDeviceIdById(item.id)"
                    :title="t('settings.cloudDeviceIdCopy')"
                  >
                    <span class="material-symbols-outlined text-[14px]">content_copy</span>
                  </button>
                  <button
                    class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity px-1 py-0.5 rounded hover:bg-gray-200"
                    @mousedown.stop.prevent="startRenameDeviceId(item)"
                    :title="t('settings.deviceIdRename')"
                  >
                    <span class="material-symbols-outlined text-[14px]">edit</span>
                  </button>
                  <button
                    class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity px-1 py-0.5 rounded hover:bg-red-100 text-red-500"
                    @mousedown.stop.prevent="confirmDeleteDeviceId(item)"
                    :title="t('settings.deviceIdDelete')"
                  >
                    <span class="material-symbols-outlined text-[14px]">close</span>
                  </button>
                </div>
              </div>
            </div>
            <div class="flex flex-wrap gap-3">
              <!-- Backup dropdown -->
              <div class="relative">
                <button class="glass-button px-5 py-2.5 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="showBackupMenu = !showBackupMenu; showRestoreMenu = false">
                  <span class="material-symbols-outlined text-[18px]">upload</span>
                  {{ t("settings.cloudUpload") }}
                  <span class="material-symbols-outlined text-[16px]">arrow_drop_down</span>
                </button>
                <div v-if="showBackupMenu" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-md z-20 min-w-[160px] border border-gray-200">
                  <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleExport(); showBackupMenu = false">
                    <span class="material-symbols-outlined text-[18px]">file_upload</span>
                    {{ t("settings.exportLocal") }}
                  </div>
                  <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleCloudUpload(); showBackupMenu = false">
                    <span class="material-symbols-outlined text-[18px]">cloud_upload</span>
                    {{ t("settings.exportCloud") }}
                  </div>
                </div>
              </div>
              <!-- Restore dropdown -->
              <div class="relative">
                <button class="glass-button px-5 py-2.5 rounded-full font-label-md text-label-md flex items-center gap-2 select-none" @click="showRestoreMenu = !showRestoreMenu; showBackupMenu = false">
                  <span class="material-symbols-outlined text-[18px]">download</span>
                  {{ t("settings.restore") }}
                  <span class="material-symbols-outlined text-[16px]">arrow_drop_down</span>
                </button>
                <div v-if="showRestoreMenu" class="absolute top-full left-0 mt-1 bg-white rounded-lg shadow-md z-20 min-w-[160px] border border-gray-200">
                  <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleImport(); showRestoreMenu = false">
                    <span class="material-symbols-outlined text-[18px]">file_download</span>
                    {{ t("settings.importLocal") }}
                  </div>
                  <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleCloudRestore(); showRestoreMenu = false">
                    <span class="material-symbols-outlined text-[18px]">cloud_download</span>
                    {{ t("settings.importCloud") }}
                  </div>
                  <div class="border-t border-gray-100 my-1"></div>
                  <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleExportKey(); showRestoreMenu = false">
                    <span class="material-symbols-outlined text-[18px]">key</span>
                    {{ t("settings.exportKey") }}
                  </div>
                  <div class="px-4 py-2 font-body-md text-body-md text-on-surface hover:bg-gray-100 cursor-pointer flex items-center gap-2" @mousedown="handleImportKey(); showRestoreMenu = false">
                    <span class="material-symbols-outlined text-[18px]">vpn_key</span>
                    {{ t("settings.importKey") }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <p v-if="statusMessage" class="mt-3 font-body-md text-body-md text-[13px] break-words" :class="statusIsError ? 'text-error' : 'text-success-indicator'">{{ statusMessage }}</p>
      </div>

      <div class="border-t border-glass-border-light/30 my-5"></div>

      <!-- AI Configuration -->
      <div class="min-w-0">
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <span class="font-body-md text-body-md text-on-surface font-medium shrink-0">{{ t("settings.aiConfig") }}</span>
          <div class="flex items-center gap-2 self-start sm:self-auto">
            <button
              class="glass-button px-4 py-2 rounded-full text-[13px] select-none shrink-0"
              :disabled="aiTesting"
              @click="testAi"
            >
              <span v-if="aiTesting" class="material-symbols-outlined text-[16px] animate-spin align-middle mr-1">sync</span>
              {{ t("settings.aiTest") }}
            </button>
            <button class="glass-button px-4 py-2 rounded-full text-[13px] glass-active select-none shrink-0" @click="saveAi">{{ t("settings.aiSave") }}</button>
          </div>
        </div>
        <div class="grid grid-cols-1 gap-4 min-w-0">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 min-w-0">
            <div class="min-w-0">
              <label class="text-[12px] text-on-surface-variant block mb-1">{{ t("settings.aiProvider") }}</label>
              <select v-model="aiConfig.provider" class="glass-input w-full min-w-0 px-3 py-2 rounded-lg text-[14px] outline-none select-text" @change="onProviderChange">
                <option value="azure">{{ t("settings.aiProviderAzure") }}</option>
                <option value="deepseek">{{ t("settings.aiProviderDeepseek") }}</option>
                <option value="mimo">{{ t("settings.aiProviderMimo") }}</option>
                <option value="openai">{{ t("settings.aiProviderOpenai") }}</option>
                <option value="custom">{{ t("settings.aiProviderCustom") }}</option>
              </select>
            </div>
            <div class="min-w-0">
              <label class="text-[12px] text-on-surface-variant block mb-1">{{ t("settings.aiMaxTokens") }}</label>
              <input v-model.number="aiConfig.maxContextTokens" type="number" min="1000" max="32000" step="500" class="glass-input w-full min-w-0 px-3 py-2 rounded-lg text-[14px] outline-none select-text" />
            </div>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 min-w-0">
            <div class="min-w-0">
              <label class="text-[12px] text-on-surface-variant block mb-1">{{ t("settings.aiModel") }}</label>
              <input v-model="aiConfig.model" type="text" class="glass-input w-full min-w-0 px-3 py-2 rounded-lg text-[14px] outline-none select-text" />
            </div>
            <div class="min-w-0">
              <label class="text-[12px] text-on-surface-variant block mb-1">{{ t("settings.aiAuthMode") }}</label>
              <select v-model="aiConfig.authMode" class="glass-input w-full min-w-0 px-3 py-2 rounded-lg text-[14px] outline-none select-text">
                <option value="api-key">api-key</option>
                <option value="bearer">Bearer</option>
              </select>
            </div>
          </div>
          <div class="min-w-0">
            <label class="text-[12px] text-on-surface-variant block mb-1">{{ t("settings.aiEndpoint") }}</label>
            <input v-model="aiConfig.endpoint" type="url" class="glass-input w-full min-w-0 px-3 py-2 rounded-lg text-[12px] outline-none select-text font-mono break-all" />
          </div>
          <div class="min-w-0">
            <label class="text-[12px] text-on-surface-variant block mb-1">{{ t("settings.aiApiKey") }}</label>
            <input v-model="aiConfig.apiKey" type="password" autocomplete="off" class="glass-input w-full min-w-0 px-3 py-2 rounded-lg text-[12px] outline-none select-text font-mono" />
          </div>
        </div>
        <p v-if="aiStatusMessage" class="mt-3 font-body-md text-body-md text-[13px] break-words" :class="aiStatusIsError ? 'text-error' : 'text-success-indicator'">{{ aiStatusMessage }}</p>
      </div>

      <!-- AI Memory Management -->
      <div class="border-t border-glass-border-light/30 my-5"></div>
      <div class="min-w-0">
        <div class="flex items-center justify-between gap-3 mb-2">
          <span class="font-body-md text-body-md text-on-surface font-medium shrink-0">{{ t("settings.aiMemory") }}</span>
          <div class="flex items-center gap-1">
            <button
              class="glass-button px-2 py-1.5 rounded-full text-[12px] select-none"
              title="Refresh memories"
              @click="loadMemories"
            >
              <span class="material-symbols-outlined text-[14px]" :class="refreshingMemories ? 'animate-spin' : ''">refresh</span>
            </button>
            <button
              class="glass-button px-4 py-1.5 rounded-full text-[12px] select-none"
              @click="showMemoryModal = true"
            >
              <span class="material-symbols-outlined text-[14px] align-middle mr-1">manage_history</span>
              {{ t("settings.aiMemoryManage") }}
            </button>
          </div>
        </div>
        <p class="text-[12px] text-on-surface-variant/60">
          {{ memories.length > 0 ? t("settings.aiMemoryCount", { count: String(memories.length) }) : t("settings.aiMemoryEmpty") }}
          <span v-if="memoryStatusMessage && !showMemoryModal" class="ml-2 text-success-indicator">{{ memoryStatusMessage }}</span>
        </p>
      </div>

      <!-- AI Memory Modal -->
      <Teleport to="body">
        <div v-if="showMemoryModal" class="fixed inset-0 z-50 flex items-start justify-center pt-[8vh]" @click.self="showMemoryModal = false">
          <div class="absolute inset-0 bg-black/10 backdrop-blur-sm"></div>
          <div class="glass-panel rounded-[2rem] w-[560px] max-w-[calc(100vw-3rem)] max-h-[80vh] flex flex-col bg-white relative z-10 overflow-hidden" @click.stop>
            <div class="flex items-center justify-between gap-3 px-6 pt-5 pb-3 shrink-0">
              <h3 class="font-label-md text-label-md text-on-surface font-semibold select-none flex items-center gap-1.5">
                <span class="material-symbols-outlined text-[16px]">memory</span>
                {{ t("settings.aiMemory") }}
              </h3>
              <button class="glass-button p-1 rounded select-none shrink-0" @click="showMemoryModal = false">
                <span class="material-symbols-outlined text-[16px]">close</span>
              </button>
            </div>
            <div class="flex-1 overflow-y-auto custom-scrollbar px-6 py-2 min-h-0">
              <div v-if="memories.length === 0" class="text-[12px] text-on-surface-variant/60 text-center py-12">
                {{ t("settings.aiMemoryEmpty") }}
              </div>
              <div v-else class="space-y-1">
                <div
                  v-for="mem in memories"
                  :key="mem.id"
                  class="flex items-start gap-3 px-3 py-2.5 rounded-lg hover:bg-on-surface/[0.04] transition-colors group"
                >
                  <span
                    class="material-symbols-outlined text-[16px] shrink-0 mt-0.5 cursor-pointer select-none transition-colors"
                    :class="selectedMemoryIds.has(mem.id) ? 'text-secondary' : 'text-on-surface-variant/40'"
                    @click="toggleMemorySelect(mem.id)"
                  >{{ selectedMemoryIds.has(mem.id) ? 'check_circle' : 'radio_button_unchecked' }}</span>
                  <div class="flex-1 min-w-0 cursor-pointer select-none" @click="toggleMemorySelect(mem.id)">
                    <p class="text-[12px] text-on-surface leading-relaxed break-words">{{ mem.content }}</p>
                    <p class="text-[10px] text-on-surface-variant/50 mt-0.5">{{ formatDate(mem.createdAt) }}</p>
                  </div>
                  <button
                    class="shrink-0 opacity-0 group-hover:opacity-100 transition-opacity px-1 py-0.5 rounded hover:bg-red-100 text-red-400 hover:text-red-600 select-none"
                    :title="t('settings.aiMemoryDelete')"
                    @click="deleteMemory(mem.id)"
                  >
                    <span class="material-symbols-outlined text-[14px]">close</span>
                  </button>
                </div>
              </div>
            </div>
            <div class="flex items-center justify-between gap-3 px-6 py-4 border-t border-glass-border-light/30 shrink-0">
              <div class="flex items-center gap-2">
                <button
                  class="glass-button px-3 py-1.5 rounded-full text-[12px] select-none"
                  :disabled="selectedMemoryIds.size === 0"
                  @click="deleteSelectedMemories"
                >
                  {{ t("settings.aiMemoryDeleteSelected", { count: String(selectedMemoryIds.size) }) }}
                </button>
                <button
                  class="glass-button px-3 py-1.5 rounded-full text-[12px] select-none"
                  :disabled="memories.length === 0"
                  @click="clearAllMemories"
                >
                  <span v-if="clearingMemories" class="material-symbols-outlined text-[14px] animate-spin align-middle mr-1">sync</span>
                  {{ t("settings.aiMemoryClear") }}
                </button>
              </div>
              <span v-if="memoryStatusMessage" class="text-[12px]" :class="memoryStatusIsError ? 'text-error' : 'text-success-indicator'">{{ memoryStatusMessage }}</span>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Version -->
      <div class="mt-auto border-t border-glass-border-light/30 pt-5 flex items-center justify-between">
        <span class="font-body-md text-body-md text-on-surface font-medium">{{ t("settings.version") }}</span>
        <span class="font-body-md text-body-md text-on-surface-variant">v{{ appVersion }}</span>
      </div>
    </div>
  </div>

  <!-- Key Import Modal -->
  <div v-if="showKeyImportModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="showKeyImportModal = false">
    <div class="glass-panel rounded-2xl p-6 w-96 bg-white/60" @click.stop>
      <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-4 select-none">{{ t("settings.importKey") }}</h3>
      <input
        v-model="keyImportInput"
        type="text"
        placeholder="粘贴 44 位加密密钥"
        class="glass-input w-full px-3 py-2 rounded-lg text-[14px] outline-none select-text font-mono"
        @keydown.enter="confirmImportKey"
      />
      <div class="flex justify-end gap-2 mt-6">
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none" @click="showKeyImportModal = false">{{ t("settings.cancel") }}</button>
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none glass-active" @click="confirmImportKey">{{ t("settings.confirm") }}</button>
      </div>
    </div>
  </div>

  <!-- Delete Device ID Confirmation -->
  <div v-if="deleteDeviceIdTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" @click.self="deleteDeviceIdTarget = null">
    <div class="glass-panel rounded-2xl p-6 w-80 bg-white/80">
      <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-2 select-none">{{ t("settings.deviceIdDeleteTitle") }}</h3>
      <p class="text-[13px] text-on-surface-variant mb-6">{{ t("settings.deviceIdDeleteDesc") }}</p>
      <div class="flex justify-end gap-2">
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none" @click="deleteDeviceIdTarget = null">{{ t("settings.cancel") }}</button>
        <button class="px-4 py-2 rounded-full text-[13px] bg-red-500 text-white hover:bg-red-600 transition-colors select-none" @click="doDeleteDeviceId">{{ t("settings.confirm") }}</button>
      </div>
    </div>
  </div>

  <!-- Rename Device ID -->
  <div v-if="renameDeviceIdTarget" class="fixed inset-0 z-50 flex items-center justify-center bg-black/20 backdrop-blur-sm" @click.self="renameDeviceIdTarget = null">
    <div class="glass-panel rounded-2xl p-6 w-96 bg-white/60" @click.stop>
      <h3 class="font-label-md text-label-md text-on-surface font-semibold mb-1 select-none">{{ t("settings.deviceIdRenameTitle") }}</h3>
      <p class="text-[12px] text-on-surface-variant mb-4 font-mono break-all">{{ renameDeviceIdTarget.id }}</p>
      <input
        v-model="renameInput"
        type="text"
        :placeholder="t('settings.deviceIdRenamePlaceholder')"
        class="glass-input w-full px-3 py-2 rounded-lg text-[14px] outline-none select-text"
        @keydown.enter="confirmRenameDeviceId"
      />
      <div class="flex justify-end gap-2 mt-6">
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none" @click="renameDeviceIdTarget = null">{{ t("settings.cancel") }}</button>
        <button class="glass-button px-4 py-2 rounded-full text-[13px] select-none glass-active" @click="confirmRenameDeviceId">{{ t("settings.confirm") }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onActivated, onUnmounted } from "vue";
import * as db from "@/services/database";
import * as cloudApi from "@/services/cloudBackup";
import * as crypto from "@/services/crypto";
import { filterOversizedItems } from "@/services/cloudSync";
import { useI18n } from "@/composables/useI18n";
import { getVersion } from "@tauri-apps/api/app";
import type { AiMemory } from "@/services/database";
import {
  loadAiConfig,
  loadAiConfigForProvider,
  saveAiConfig,
  type AiConfig,
  type AiProvider,
} from "@/services/aiSettings";
import { testAiConnection } from "@/services/noteAi";

const { lang, t, setLanguage, initLanguage } = useI18n();

const theme = ref("light");
const statusMessage = ref("");
const statusIsError = ref(false);
const appVersion = ref("...");

function setStatus(msg: string, isError = false) {
  statusMessage.value = msg;
  statusIsError.value = isError;
}

// Cloud backup state
const deviceId = ref("");
const deviceIdList = ref<{ id: string; name: string }[]>([]);
const deviceIdNames = ref<Record<string, string>>({});
const showBackupMenu = ref(false);
const showRestoreMenu = ref(false);
const cloudBusy = ref(false);
const showDeviceDropdown = ref(false);
const isEditingDeviceId = ref(false);
const showKeyImportModal = ref(false);
const keyImportInput = ref("");
const deleteDeviceIdTarget = ref<{ id: string; name: string } | null>(null);
const renameDeviceIdTarget = ref<{ id: string; name: string } | null>(null);
const renameInput = ref("");

const aiConfig = ref<AiConfig>({
  provider: "azure",
  apiKey: "",
  endpoint: "",
  model: "",
  maxContextTokens: 8000,
  authMode: "api-key",
});
const aiStatusMessage = ref("");
const aiStatusIsError = ref(false);
const aiTesting = ref(false);
const activeAiProvider = ref<AiProvider>("azure");

// AI Memory state
const memories = ref<AiMemory[]>([]);
const clearingMemories = ref(false);
const refreshingMemories = ref(false);
const memoryStatusMessage = ref("");
const memoryStatusIsError = ref(false);
const showMemoryModal = ref(false);
const selectedMemoryIds = ref(new Set<string>());

function toggleMemorySelect(id: string) {
  const s = selectedMemoryIds.value;
  if (s.has(id)) s.delete(id);
  else s.add(id);
  // trigger reactivity by replacing
  selectedMemoryIds.value = new Set(s);
}

function setMemoryStatus(msg: string, isError = false) {
  memoryStatusMessage.value = msg;
  memoryStatusIsError.value = isError;
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
  } catch {
    return iso;
  }
}

async function loadMemories() {
  refreshingMemories.value = true;
  try {
    memories.value = await db.loadAiMemories();
    if (memoryStatusMessage.value !== t("settings.aiMemoryDeleted") && memoryStatusMessage.value !== t("settings.aiMemoryCleared")) {
      setMemoryStatus(`${t("settings.aiMemoryCount", { count: String(memories.value.length) })}`);
      setTimeout(() => { if (memoryStatusMessage.value === t("settings.aiMemoryCount", { count: String(memories.value.length) })) setMemoryStatus(""); }, 2000);
    }
  } catch { memories.value = []; }
  refreshingMemories.value = false;
}

async function deleteMemory(id: string) {
  try {
    await db.deleteAiMemory(id);
    memories.value = memories.value.filter(m => m.id !== id);
    setMemoryStatus(t("settings.aiMemoryDeleted"));
    setTimeout(() => { if (memoryStatusMessage.value === t("settings.aiMemoryDeleted")) setMemoryStatus(""); }, 2000);
  } catch (e: any) {
    setMemoryStatus(e.message || "Delete failed", true);
  }
}

async function clearAllMemories() {
  if (memories.value.length === 0) return;
  clearingMemories.value = true;
  try {
    await db.clearAiMemories();
    memories.value = [];
    setMemoryStatus(t("settings.aiMemoryCleared"));
    setTimeout(() => { if (memoryStatusMessage.value === t("settings.aiMemoryCleared")) setMemoryStatus(""); }, 2000);
  } catch (e: any) {
    setMemoryStatus(e.message || "Clear failed", true);
  } finally {
    clearingMemories.value = false;
  }
}

async function deleteSelectedMemories() {
  const ids = [...selectedMemoryIds.value];
  if (ids.length === 0) return;
  let deleted = 0;
  for (const id of ids) {
    try {
      await db.deleteAiMemory(id);
      memories.value = memories.value.filter(m => m.id !== id);
      deleted++;
    } catch {}
  }
  selectedMemoryIds.value = new Set();
  if (deleted > 0) {
    setMemoryStatus(t("settings.aiMemoryDeleted"));
    setTimeout(() => { if (memoryStatusMessage.value === t("settings.aiMemoryDeleted")) setMemoryStatus(""); }, 2000);
  }
}

function setAiStatus(msg: string, isError = false) {
  aiStatusMessage.value = msg;
  aiStatusIsError.value = isError;
}

async function onProviderChange() {
  const nextProvider = aiConfig.value.provider as AiProvider;
  const previousProvider = activeAiProvider.value;
  try {
    await saveAiConfig({ ...aiConfig.value, provider: previousProvider });
    aiConfig.value = await loadAiConfigForProvider(nextProvider);
    activeAiProvider.value = nextProvider;
  } catch (e: any) {
    setAiStatus(t("settings.aiSaveFail") + ": " + (e.message || e), true);
  }
}

async function saveAi() {
  try {
    await saveAiConfig(aiConfig.value);
    setAiStatus(t("settings.aiSaveSuccess"));
    setTimeout(() => { if (aiStatusMessage.value === t("settings.aiSaveSuccess")) setAiStatus(""); }, 3000);
  } catch (e: any) {
    setAiStatus(t("settings.aiSaveFail") + ": " + (e.message || e), true);
  }
}

async function testAi() {
  aiTesting.value = true;
  setAiStatus(t("settings.aiTesting"));
  try {
    const reply = await testAiConnection(aiConfig.value);
    setAiStatus(t("settings.aiTestSuccess") + ": " + reply);
  } catch (e: any) {
    setAiStatus(t("settings.aiTestFail") + ": " + (e.message || e), true);
  } finally {
    aiTesting.value = false;
  }
}

const deviceDisplayName = computed(() => {
  const item = deviceIdList.value.find(item => item.id === deviceId.value);
  return item?.name || "";
});

async function ensureDeviceId() {
  const last = await db.getLastDeviceId();
  const list = await db.getDeviceIdList();
  const names = await db.getDeviceIdNames();
  deviceIdNames.value = names;
  deviceIdList.value = list.map(id => ({ id, name: names[id] || "" }));
  if (last) {
    deviceId.value = last;
  } else {
    const id = crypto.generateDeviceId();
    deviceId.value = id;
    deviceIdList.value = [{ id, name: "" }];
    await db.saveDeviceIdList([id]);
    await db.saveLastDeviceId(id);
  }
}

function handleDeviceIdBlur() {
  setTimeout(() => { showDeviceDropdown.value = false; }, 200);
}

function closeMenus(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (!target.closest('.relative')) {
    showBackupMenu.value = false;
    showRestoreMenu.value = false;
  }
}

onMounted(() => { document.addEventListener('click', closeMenus); });
onUnmounted(() => { document.removeEventListener('click', closeMenus); });

function selectDeviceId(id: string) {
  deviceId.value = id;
  showDeviceDropdown.value = false;
  isEditingDeviceId.value = false;
  db.saveLastDeviceId(id);
}

async function saveCurrentDeviceId() {
  const id = deviceId.value.trim();
  if (!id) return;
  await db.saveLastDeviceId(id);
  if (!deviceIdList.value.some(item => item.id === id)) {
    deviceIdList.value.unshift({ id, name: deviceIdNames.value[id] || "" });
    await db.saveDeviceIdList(deviceIdList.value.map(item => item.id));
  }
}

async function copyDeviceId() {
  if (!deviceId.value) return;
  try {
    await navigator.clipboard.writeText(deviceId.value);
    setStatus(t("settings.cloudDeviceIdCopied"));
    setTimeout(() => { if (statusMessage.value === t("settings.cloudDeviceIdCopied")) setStatus(""); }, 2000);
  } catch {}
}

async function copyDeviceIdById(id: string) {
  try {
    await navigator.clipboard.writeText(id);
    setStatus(t("settings.cloudDeviceIdCopied"));
    setTimeout(() => { if (statusMessage.value === t("settings.cloudDeviceIdCopied")) setStatus(""); }, 2000);
  } catch {}
}

function confirmDeleteDeviceId(item: { id: string; name: string }) {
  deleteDeviceIdTarget.value = item;
}

async function doDeleteDeviceId() {
  if (!deleteDeviceIdTarget.value) return;
  const target = deleteDeviceIdTarget.value;
  deleteDeviceIdTarget.value = null;

  deviceIdList.value = deviceIdList.value.filter(item => item.id !== target.id);
  await db.saveDeviceIdList(deviceIdList.value.map(item => item.id));

  if (deviceIdNames.value[target.id]) {
    delete deviceIdNames.value[target.id];
    await db.saveDeviceIdNames(deviceIdNames.value);
  }

  if (deviceId.value === target.id) {
    if (deviceIdList.value.length > 0) {
      deviceId.value = deviceIdList.value[0].id;
    } else {
      const id = crypto.generateDeviceId();
      deviceId.value = id;
      deviceIdList.value = [{ id, name: "" }];
      await db.saveDeviceIdList([id]);
    }
    await db.saveLastDeviceId(deviceId.value);
  }
}

function startRenameDeviceId(item: { id: string; name: string }) {
  renameDeviceIdTarget.value = item;
  renameInput.value = item.name || "";
}

async function confirmRenameDeviceId() {
  if (!renameDeviceIdTarget.value) return;
  const id = renameDeviceIdTarget.value.id;
  const name = renameInput.value.trim();
  renameDeviceIdTarget.value = null;

  if (name) {
    deviceIdNames.value[id] = name;
  } else {
    delete deviceIdNames.value[id];
  }
  await db.saveDeviceIdNames(deviceIdNames.value);

  const item = deviceIdList.value.find(item => item.id === id);
  if (item) item.name = name;
}

function yieldToMain(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0));
}

async function handleCloudUpload() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.cloudBackingUp"));
  if (!deviceId.value.trim()) {
    deviceId.value = crypto.generateDeviceId();
    await saveCurrentDeviceId();
  }
  await saveCurrentDeviceId();
  await yieldToMain();
  try {
    const raw = await db.exportAllData();
    await yieldToMain();
    const data = filterOversizedItems(raw);
    const json = JSON.stringify(data);
    await yieldToMain();
    const key = await crypto.getOrCreateKey();
    await yieldToMain();
    const payload = await crypto.encryptBackup(json, key, {
      version: data.version,
      exportedAt: data.exportedAt,
    });
    await yieldToMain();
    await cloudApi.uploadBackup(deviceId.value.trim(), payload);
    setStatus(t("settings.cloudUploadSuccess"));
  } catch (e: any) {
    setStatus(t("settings.cloudUploadFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

async function handleCloudRestore() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.cloudRestoring"));
  if (!deviceId.value.trim()) { cloudBusy.value = false; setStatus(""); return; }
  await saveCurrentDeviceId();
  try {
    if (!await checkDbReady()) { cloudBusy.value = false; return; }
    const list = await cloudApi.listBackups(deviceId.value.trim());
    if (!list || list.length === 0) {
      setStatus(t("settings.cloudEmpty"));
      cloudBusy.value = false;
      return;
    }
    const sorted = [...list].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
    const latest = sorted[0];
    const detail = await cloudApi.getBackup(deviceId.value.trim(), latest.id);
    const key = await crypto.getOrCreateKey();
    const json = await crypto.decryptBackup(detail, key);
    let backup: any;
    try { backup = JSON.parse(json); } catch { setStatus(t("settings.cloudRestoreFail") + ": 解密失败，密钥可能不匹配", true); return; }
    if (!backup.version) {
      setStatus(t("settings.cloudRestoreFail") + ": invalid backup data", true);
      return;
    }
    await db.importAllData(backup);
    setStatus(t("settings.cloudRestoreSuccess"));
    setTimeout(() => window.location.reload(), 1500);
  } catch (e: any) {
    setStatus(t("settings.cloudRestoreFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

async function handleExportKey() {
  const key = await crypto.getOrCreateKey();
  await navigator.clipboard.writeText(key);
  setStatus(t("settings.keyExported"));
  setTimeout(() => { if (statusMessage.value === t("settings.keyExported")) setStatus(""); }, 3000);
}

async function handleImportKey() {
  keyImportInput.value = "";
  showKeyImportModal.value = true;
}

async function confirmImportKey() {
  showKeyImportModal.value = false;
  const trimmed = keyImportInput.value.trim();
  if (!trimmed) return;
  if (trimmed.length !== 44 || !/^[A-Za-z0-9+/=]+$/.test(trimmed)) {
    setStatus(t("settings.keyImportFail"), true);
    return;
  }
  await db.setSetting("cloud_encryption_key", trimmed);
  setStatus(t("settings.keyImported"));
}

async function checkDbReady(): Promise<boolean> {
  try {
    await db.checkDatabaseReady();
    return true;
  } catch {
    setStatus(t("settings.dbBusy"), true);
    return false;
  }
}

async function loadTheme() {
  const saved = await db.getSetting("theme");
  if (saved) {
    theme.value = saved;
    applyTheme(saved);
  }
}

function applyTheme(t: string) {
  const root = document.documentElement;
  if (t === "dark") {
    root.classList.add("dark");
  } else {
    root.classList.remove("dark");
  }
}

async function setTheme(t: string) {
  theme.value = t;
  applyTheme(t);
  await db.setSetting("theme", t);
}

async function handleExport() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.exporting"));
  try {
    const data = await db.exportAllData();
    const json = JSON.stringify(data, null, 2);
    try {
      const { save } = await import("@tauri-apps/plugin-dialog");
      const { invoke } = await import("@tauri-apps/api/core");
      const path = await save({
        filters: [{ name: "Test Space Backup", extensions: ["tsb"] }],
        defaultPath: "test-space-backup.tsb",
      });
      if (path) {
        await invoke("write_text_file", { path, content: json });
        setStatus(t("settings.exportSuccess"));
      } else {
        setStatus("");
      }
    } catch {
      const blob = new Blob([json], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "test-space-backup.tsb";
      a.click();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setStatus(t("settings.exportSuccess"));
    }
  } catch (e: any) {
    setStatus(t("settings.exportFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

async function handleImport() {
  if (cloudBusy.value) return;
  cloudBusy.value = true;
  setStatus(t("settings.importing"));
  try {
    let json: string;
    try {
      const { open } = await import("@tauri-apps/plugin-dialog");
      const { invoke } = await import("@tauri-apps/api/core");
      const path = await open({
        filters: [{ name: "Test Space Backup", extensions: ["tsb", "json"] }],
        multiple: false,
      });
      if (!path) { cloudBusy.value = false; setStatus(""); return; }
      json = await invoke<string>("read_text_file", { path: path as string });
    } catch {
      const input = document.createElement("input");
      input.type = "file";
      input.accept = ".tsb,.json";
      const file = await new Promise<File | null>((resolve) => {
        input.onchange = () => resolve(input.files?.[0] || null);
        input.click();
      });
      if (!file) { cloudBusy.value = false; setStatus(""); return; }
      json = await file.text();
    }
    if (!await checkDbReady()) { cloudBusy.value = false; return; }
    let backup: any;
    try { backup = JSON.parse(json); } catch { setStatus(t("settings.importFail") + ": JSON 解析失败，文件可能损坏", true); return; }
    if (!backup.version) {
      setStatus(t("settings.importFail") + ": invalid backup file", true);
      cloudBusy.value = false;
      return;
    }
    await db.importAllData(backup);
    setStatus(t("settings.importSuccess"));
    setTimeout(() => window.location.reload(), 1500);
  } catch (e: any) {
    setStatus(t("settings.importFail") + ": " + (e.message || e), true);
  } finally {
    cloudBusy.value = false;
  }
}

watch(showMemoryModal, (v) => {
  if (v) {
    selectedMemoryIds.value = new Set();
    loadMemories();
  }
});

onMounted(async () => {
  await initLanguage();
  await loadTheme();
  aiConfig.value = await loadAiConfig();
  activeAiProvider.value = aiConfig.value.provider;
  try {
    appVersion.value = await getVersion();
  } catch {
    appVersion.value = "1.0.0";
  }
  await ensureDeviceId();
  await loadMemories();
});

onActivated(() => {
  loadMemories();
});
</script>
