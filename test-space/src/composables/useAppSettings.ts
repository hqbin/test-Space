import { ref } from "vue";
import { getSetting, setSetting } from "@/services/database";

/** 命令执行浮窗自动消失：开启后命令完成 3 秒自动关闭，默认开启。 */
const POPUP_AUTO_DISMISS_KEY = "cmd_exec_auto_dismiss";

const popupAutoDismiss = ref(true);
let loadPromise: Promise<void> | null = null;
let userTouched = false;

/**
 * 读取全局设置。多次调用共享同一次数据库读取，
 * 避免设备页 / 设置页挂载时重复查询；读取失败时保持默认值，下次调用重试。
 */
export function loadAppSettings(): Promise<void> {
  if (!loadPromise) {
    loadPromise = (async () => {
      try {
        const saved = await getSetting(POPUP_AUTO_DISMISS_KEY);
        // 缺省视为开启，只有显式保存过 "0" 才关闭；用户已手动切换时以用户操作为准
        if (saved !== null && !userTouched) {
          popupAutoDismiss.value = saved !== "0";
        }
      } catch {
        loadPromise = null;
      }
    })();
  }
  return loadPromise;
}

/** 更新开关并持久化；写入失败时回滚，避免界面状态与实际行为不一致。 */
export async function setPopupAutoDismiss(value: boolean): Promise<void> {
  const previous = popupAutoDismiss.value;
  userTouched = true;
  popupAutoDismiss.value = value;
  try {
    await setSetting(POPUP_AUTO_DISMISS_KEY, value ? "1" : "0");
  } catch {
    popupAutoDismiss.value = previous;
  }
}

export function useAppSettings() {
  return { popupAutoDismiss, loadAppSettings, setPopupAutoDismiss };
}
