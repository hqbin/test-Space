import { createApp } from "vue";
import { createPinia } from "pinia";
import App from "./App.vue";
import router from "./router";
import "./styles/main.css";

/**
 * 全局 UI 流体缩放（fluid zoom）
 * ─────────────────────────────────────────────────────────────
 * 参考成熟做法：clamp(min, viewport/ref, max)
 *   - 设计基准宽 1440px → scale = 1.0
 *   - 最小 0.90（1296px 窗口以下不再更小，保证可读）
 *   - 最大 1.30（1872px 以上不再放大，防太空旷）
 * 用 `zoom` 而非 `transform: scale`，因为 zoom 会连带布局重排，
 * 而 transform 只影响绘制、字体点阵不重排会糊。
 *
 * 项目中 3000+ 行硬编码 px 无需改动，一次让所有元素等比缩放。
 */
const DESIGN_WIDTH = 1440;
const MIN_SCALE = 0.9;
const MAX_SCALE = 1.3;

function applyUIScale() {
  const w = window.innerWidth;
  const raw = w / DESIGN_WIDTH;
  const scale = Math.min(MAX_SCALE, Math.max(MIN_SCALE, raw));
  // Chromium `zoom` 接受数字（1.0 = 100%）
  (document.documentElement.style as any).zoom = String(scale);
  document.documentElement.style.setProperty("--ui-scale", String(scale));
}

applyUIScale();
let rafId: number | null = null;
window.addEventListener(
  "resize",
  () => {
    if (rafId !== null) cancelAnimationFrame(rafId);
    rafId = requestAnimationFrame(() => {
      applyUIScale();
      rafId = null;
    });
  },
  { passive: true }
);

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.mount("#app");
