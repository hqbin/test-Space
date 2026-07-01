import { ref, computed, nextTick } from "vue";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";

export interface OutputLine {
  text: string;
  stream: "stdout" | "stderr";
}

export interface ScriptTab {
  id: string;
  label: string;
  status: "running" | "success" | "error" | "killed";
  startTime: number;
  elapsed: string;
  exitCode: number | null;
  output: OutputLine[];
}

const tabs = ref<ScriptTab[]>([]);
const activeTabId = ref<string>("");

// 每个 tab 最多保留的输出行数，超出后丢弃最早的行（循环缓冲区）
// 压测场景下大量输出不会导致内存溢出
const MAX_OUTPUT_LINES = 5000;

let elapsedTimer: ReturnType<typeof setInterval> | null = null;
let unlistenLine: (() => void) | null = null;
let unlistenExit: (() => void) | null = null;
let setupCalled = false;
let setupInProgress = false;

function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

const activeTab = computed(() => tabs.value.find(t => t.id === activeTabId.value));
const activeTabOutput = computed(() => activeTab.value?.output ?? []);

function addTab(label: string): ScriptTab {
  const tab: ScriptTab = {
    id: genId(),
    label,
    status: "running",
    startTime: Date.now(),
    elapsed: "00:00",
    exitCode: null,
    output: [],
  };
  tabs.value.push(tab);
  activeTabId.value = tab.id;
  if (!elapsedTimer) {
    elapsedTimer = setInterval(() => {
      for (const t of tabs.value) {
        if (t.status === "running") {
          const secs = Math.floor((Date.now() - t.startTime) / 1000);
          t.elapsed = `${String(Math.floor(secs / 60)).padStart(2, "0")}:${String(secs % 60).padStart(2, "0")}`;
        }
      }
    }, 1000);
  }
  return tab;
}

function clearTabOutput(id: string) {
  const tab = tabs.value.find(t => t.id === id);
  if (tab) tab.output = [];
}

async function killScript(id: string) {
  try {
    await invoke("script_kill", { id });
    const tab = tabs.value.find(t => t.id === id);
    if (tab) {
      tab.status = "killed";
      tab.output.push({ text: "\n[Terminated]", stream: "stderr" });
    }
  } catch { }
}

function destroy() {
  if (elapsedTimer) { clearInterval(elapsedTimer); elapsedTimer = null; }
  unlistenLine?.();
  unlistenExit?.();
  unlistenLine = null;
  unlistenExit = null;
  tabs.value = [];
  activeTabId.value = "";
  setupCalled = false;
  setupInProgress = false;
}

async function setup() {
  if (setupInProgress) return;
  setupInProgress = true;
  // 先清理旧的监听器，保证全局只有一组监听器（防止 HMR 或重复调用叠加）
  unlistenLine?.();
  unlistenExit?.();
  unlistenLine = null;
  unlistenExit = null;
  setupCalled = true;

  try {
    unlistenLine = await listen<{ id: string; line: string; stream: string }>("script-line", (event) => {
      const tab = tabs.value.find(t => t.id === event.payload.id);
      if (tab) {
        tab.output.push({ text: event.payload.line, stream: event.payload.stream as "stdout" | "stderr" });
        // 超出上限时从头部丢弃，避免长时间压测撑爆内存
        if (tab.output.length > MAX_OUTPUT_LINES) {
          tab.output.splice(0, tab.output.length - MAX_OUTPUT_LINES);
        }
        scrollToBottom();
      }
    });
    unlistenExit = await listen<{ id: string; exit_code: number }>("script-exit", (event) => {
      const tab = tabs.value.find(t => t.id === event.payload.id);
      if (tab) {
        tab.status = event.payload.exit_code === 0 ? "success" : "error";
        tab.exitCode = event.payload.exit_code;
        tab.output.push({ text: `\n[Exit ${event.payload.exit_code}]`, stream: "stdout" });
        scrollToBottom();
      }
    });
  } finally {
    setupInProgress = false;
  }
}

let scrollContainer: HTMLElement | null = null;

function setScrollContainer(el: HTMLElement | null) {
  scrollContainer = el;
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollContainer) scrollContainer.scrollTop = scrollContainer.scrollHeight;
  });
}

export function useScriptRunner() {
  return {
    tabs,
    activeTabId,
    activeTab,
    activeTabOutput,
    addTab,
    clearTabOutput,
    killScript,
    setup,
    destroy,
    setScrollContainer,
  };
}
