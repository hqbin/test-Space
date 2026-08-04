// 桌面便签窗口生命周期管理
// 每张便签一个独立窗口，label = `sticky-<noteId>`（UUID 字符集安全）。
// 位置/尺寸全程使用物理像素（outerPosition/setPosition 均为 Physical*，多显示器安全）。
import { WebviewWindow } from "@tauri-apps/api/webviewWindow";
import { PhysicalPosition, PhysicalSize, availableMonitors } from "@tauri-apps/api/window";
import {
  loadStickyNotes,
  getStickyNote,
  unpinNoteFromDesktop,
  loadNote,
} from "./database";

const DEFAULT_WIDTH = 360;
const DEFAULT_HEIGHT = 420;

export const stickyLabel = (noteId: string) => `sticky-${noteId}`;

// 校验窗口位置是否落在任一显示器可见区域内（物理像素，多显示器安全）
async function isPositionVisible(x: number, y: number, w: number, h: number): Promise<boolean> {
  try {
    const monitors = await availableMonitors()
    if (!monitors.length) return false
    // 窗口左上角或中心落在某个显示器内即视为有效
    const cx = x + w / 2
    const cy = y + h / 2
    return monitors.some(m => {
      const { x: mx, y: my } = m.position
      const { width: mw, height: mh } = m.size
      const inX = (x >= mx && x < mx + mw) || (cx >= mx && cx < mx + mw)
      const inY = (y >= my && y < my + mh) || (cy >= my && cy < my + mh)
      return inX && inY
    })
  } catch {
    return false
  }
}

/**
 * 确保便签窗口存在。
 * - 已存在 → show + setFocus（防重复创建），返回 false
 * - 不存在 → 创建（visible:false 防闪屏，created 后恢复位置再显示），返回 true
 */
export async function ensureStickyWindow(noteId: string): Promise<boolean> {
  const label = stickyLabel(noteId)
  const existing = await WebviewWindow.getByLabel(label)
  if (existing) {
    try { await existing.show() } catch {}
    try { await existing.setFocus() } catch {}
    return false
  }

  const win = new WebviewWindow(label, {
    url: `/sticky?noteId=${noteId}`,
    title: "Sticky Note",
    width: DEFAULT_WIDTH,
    height: DEFAULT_HEIGHT,
    visible: false, // 防闪屏：恢复位置后再 show
    skipTaskbar: true,
    decorations: false,
    transparent: true,  // 透明窗口才能让 CSS rounded corners 裁掉四角
    shadow: false,      // 关掉 DWM 系统阴影，只用 CSS box-shadow，避免双层阴影
    alwaysOnTop: false, // wallpaper pin() 负责桌面层级，不覆盖其他窗口
    resizable: true,
  })
  win.once("tauri://created", async () => {
    // 与主窗口一致：运行时关闭 DWM 系统阴影，只留 CSS box-shadow
    try { await win.setShadow(false) } catch {}
    // 恢复上次位置：0,0 表示"未定位过"（保持居中），越界则回退居中
    try {
      const sticky = await getStickyNote(noteId)
      const sized = sticky && (sticky.width > 0 || sticky.height > 0)
      const positioned = sticky && (sticky.posX !== 0 || sticky.posY !== 0)
      if (sticky && sized) {
        await win.setSize(new PhysicalSize(sticky.width || DEFAULT_WIDTH, sticky.height || DEFAULT_HEIGHT))
      }
      if (sticky && positioned) {
        const w = sticky.width || DEFAULT_WIDTH
        const h = sticky.height || DEFAULT_HEIGHT
        if (await isPositionVisible(sticky.posX, sticky.posY, w, h)) {
          await win.setPosition(new PhysicalPosition(sticky.posX, sticky.posY))
        }
      }
    } catch (e) {
      console.error("[sticky] restore position failed:", e)
    }
    try { await win.show() } catch {}
    try { await win.setFocus() } catch {}
  })
  win.once("tauri://error", (e) => {
    console.error("[sticky] window create failed:", e)
  })
  return true
}

/**
 * 启动恢复：为所有固定记录重建便签窗口。
 * 仅应由主窗口调用（App.vue 中判断 label === 'main'），否则便签窗口会递归开窗。
 * 顺带清理孤儿记录：笔记已被删除的固定记录。
 */
export async function restoreStickyWindows() {
  const stickyNotes = await loadStickyNotes()
  // 并行校验 + 开窗，不逐条串行等待
  await Promise.all(stickyNotes.map(async (s) => {
    const note = await loadNote(s.noteId).catch(() => null)
    if (!note) {
      await unpinNoteFromDesktop(s.noteId).catch(() => {})
      return
    }
    await ensureStickyWindow(s.noteId)
  }))
}

/**
 * 取消固定并关闭便签窗口（供主窗口与便签页面共用）。
 * 先清记录再销毁窗口，绕开一切 hide 拦截；幂等，可安全重复调用。
 */
export async function unpinAndClose(noteId: string) {
  await unpinNoteFromDesktop(noteId).catch(() => {})
  const win = await WebviewWindow.getByLabel(stickyLabel(noteId))
  if (win) await win.destroy().catch(() => {})
}
