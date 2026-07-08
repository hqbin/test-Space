import { invoke } from "@tauri-apps/api/core"
import { listen } from "@tauri-apps/api/event"

export interface AutoStepEvent {
  type: "step_start" | "step_done" | "step_heal" | "step_fail" | "screenshot" | "suite_done"
  step_id?: string
  desc?: string
  status?: string
  ms?: number
  phase?: number
  method?: string
  error?: string
  path?: string
  passed?: number
  failed?: number
  healed?: number
  step_total?: number
  heal_log?: string
}

let unlistenStep: (() => void) | null = null

export async function listenAutoEvents(onEvent: (event: AutoStepEvent) => void): Promise<() => void> {
  if (unlistenStep) unlistenStep()
  unlistenStep = await listen<AutoStepEvent>("auto:step_event", (event) => {
    onEvent(event.payload)
  })
  return () => {
    unlistenStep?.()
    unlistenStep = null
  }
}

export async function runAutoCase(
  runId: string,
  caseId: string,
  deviceSerial: string,
): Promise<void> {
  await invoke("auto_run_case", {
    runId,
    caseId,
    deviceSerial,
  })
}

export async function runAutoSuite(
  runId: string,
  caseIds: string[],
  deviceSerial: string,
): Promise<void> {
  await invoke("auto_run_suite", {
    runId,
    caseIds,
    deviceSerial,
  })
}

export async function stopAutoRun(runId: string) {
  try {
    await invoke("auto_stop_run", { runId })
  } catch (e) {
    console.error("[AutoRun] stop failed:", e)
  }
}

export async function autoGenSkeleton(graphJson: string, packageName: string): Promise<string> {
  try {
    return await invoke<string>("auto_gen_skeleton", { graphJson, package: packageName })
  } catch (e) {
    console.error("[AutoRun] gen skeleton failed:", e)
    return ""
  }
}

export async function checkPythonEngine(): Promise<boolean> {
  try {
    const result = await invoke<string>("auto_check_engine")
    return result === "ok"
  } catch {
    return false
  }
}
