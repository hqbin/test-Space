import type { Config } from "tailwindcss";

/**
 * 视觉体系：Quarterly（季刊） + Gazette（公报）
 *
 * 颜色骨架：
 *   paper (#F1EDE4)   温羊皮纸  主背景
 *   ink   (#1C1B1F)   墨黑      正文/标题
 *   graphite/mist/fog 次级文本三档，保证 WCAG AA
 *   prussian(#1E3A5F) 普鲁士蓝  唯一常态强调色（active / focus / 链接）
 *   rust  (#C24E3A)   氧化红    警告 / 破坏性动作
 *   mint  (#14A085)   荧光青    成功 / 数据高亮
 *   line              发丝分隔  取代阴影承担分层
 *
 * 类型体系：Fraunces（可变衬线） + Inter（正文） + Newsreader（长文） +
 *          Instrument Serif Italic（署名点缀） + JetBrains Mono（数据）
 */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // ── 杂志核心色板 ─────────────────────────────
        paper: "#F1EDE4",
        "paper-2": "#E8E2D3",
        ink: "#1C1B1F",
        graphite: "#3A3833",
        mist: "#6B6660",
        fog: "#A8A29A",
        prussian: "#1E3A5F",
        "prussian-2": "#2C5589",
        rust: "#C24E3A",
        mint: "#14A085",
        hairline: "rgba(28, 27, 31, 0.14)",
        "hairline-strong": "rgba(28, 27, 31, 0.24)",

        // ── 保留旧 token 名，值指向新色板 ─────────────
        primary: "#1E3A5F",
        "primary-container": "#2C5589",
        secondary: "#1E3A5F",
        "secondary-container": "#2C5589",
        tertiary: "#C24E3A",
        "tertiary-container": "#C24E3A",
        "success-indicator": "#14A085",
        error: "#C24E3A",
        "error-container": "#F4D9D0",
        "on-error": "#ffffff",
        "on-error-container": "#5F1E13",

        // 中性/表面
        surface: "#F1EDE4",
        background: "#F1EDE4",
        "surface-bright": "#F5F1E9",
        "surface-container-lowest": "#FBF7EE",
        "surface-container-low": "#EEE9DE",
        "surface-container": "#E8E2D3",
        "surface-container-high": "#DFD8C6",
        "surface-container-highest": "#D5CCB6",
        "surface-variant": "#DFD8C6",
        "surface-dim": "#DFD8C6",
        "surface-tint": "#1E3A5F",
        "inverse-surface": "#26241F",
        "inverse-on-surface": "#F1EDE4",
        "inverse-primary": "#B3C5D6",

        // 文本
        "on-surface": "#1C1B1F",
        "on-background": "#1C1B1F",
        "on-surface-variant": "#3A3833", // 由 #424656 提升到 4.5:1+
        "on-primary": "#FFFFFF",
        "on-secondary": "#FFFFFF",
        "on-tertiary": "#FFFFFF",
        "on-primary-container": "#F3EFE7",
        "on-secondary-container": "#F3EFE7",
        "on-tertiary-container": "#FFF6F3",
        "on-primary-fixed": "#0F1F35",
        "on-primary-fixed-variant": "#0F1F35",
        "on-secondary-fixed": "#0F1F35",
        "on-secondary-fixed-variant": "#0F1F35",
        "on-tertiary-fixed": "#3B1508",
        "on-tertiary-fixed-variant": "#7C2D18",

        // fixed 容器色（对话/浮层）
        "primary-fixed": "#D3DFF0",
        "primary-fixed-dim": "#A9BFDA",
        "secondary-fixed": "#D3DFF0",
        "secondary-fixed-dim": "#A9BFDA",
        "tertiary-fixed": "#F4D9D0",
        "tertiary-fixed-dim": "#E8B2A0",

        // 玻璃/发丝
        "glass-border-light": "rgba(28, 27, 31, 0.10)",
        "glass-border-dark": "rgba(28, 27, 31, 0.16)",
        "glass-surface": "rgba(241, 237, 228, 0.55)",
        outline: "#6B6660",
        "outline-variant": "#C9C2B4",
      },
      borderRadius: {
        // 收紧圆角尺度：卡片圆但不 blob，控件小圆或直角
        DEFAULT: "12px",
        sm: "6px",
        md: "10px",
        lg: "18px",
        xl: "24px",
        "2xl": "28px",
        "3xl": "32px",
        full: "9999px",
      },
      spacing: {
        "padding-card": "28px",
        "margin-page": "32px",
        "safe-area-top": "56px",
        "gutter-grid": "20px",
        unit: "8px",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        display: ["Fraunces", "Georgia", "serif"],
        news: ["Newsreader", "Georgia", "serif"],
        editorial: ["Instrument Serif", "Fraunces", "Georgia", "serif"],
        mono: ["JetBrains Mono", "SFMono-Regular", "Consolas", "monospace"],

        // 语义名指向杂志字体
        caption: ["Inter"],
        "headline-md": ["Fraunces", "Georgia", "serif"],
        "headline-lg": ["Fraunces", "Georgia", "serif"],
        "display-lg": ["Fraunces", "Georgia", "serif"],
        "body-lg": ["Inter"],
        "body-md": ["Inter"],
        "label-md": ["Inter"],
      },
      fontSize: {
        // 严格 8 档：11 / 12 / 13 / 15 / 17 / 22 / 28 / 40
        eyebrow: [
          "11px",
          { lineHeight: "1.4", letterSpacing: "0.14em", fontWeight: "600" },
        ],
        caption: [
          "13px",
          { lineHeight: "1.45", letterSpacing: "0.01em", fontWeight: "500" },
        ],
        "body-sm": [
          "13px",
          { lineHeight: "1.5", letterSpacing: "0", fontWeight: "400" },
        ],
        "body-md": [
          "15px",
          { lineHeight: "1.55", letterSpacing: "0", fontWeight: "400" },
        ],
        "body-lg": [
          "17px",
          { lineHeight: "1.55", letterSpacing: "-0.005em", fontWeight: "400" },
        ],
        "label-md": [
          "13px",
          { lineHeight: "1.2", letterSpacing: "0.005em", fontWeight: "600" },
        ],
        "label-xs": [
          "12px",
          { lineHeight: "1.2", letterSpacing: "0.02em", fontWeight: "600" },
        ],
        "label-lg": [
          "15px",
          { lineHeight: "1.2", letterSpacing: "0", fontWeight: "600" },
        ],
        "headline-md": [
          "22px",
          { lineHeight: "1.2", letterSpacing: "-0.02em", fontWeight: "600" },
        ],
        "headline-lg": [
          "28px",
          { lineHeight: "1.15", letterSpacing: "-0.025em", fontWeight: "700" },
        ],
        "display-lg": [
          "40px",
          { lineHeight: "1.05", letterSpacing: "-0.035em", fontWeight: "700" },
        ],
      },
      boxShadow: {
        // 弱化阴影：优先靠发丝分隔
        "soft-1": "0 1px 2px rgba(28, 27, 31, 0.05)",
        "soft-2": "0 4px 12px rgba(28, 27, 31, 0.08)",
        "soft-3": "0 8px 24px rgba(28, 27, 31, 0.10)",
        editorial: "0 1px 0 rgba(28, 27, 31, 0.10)",
      },
    },
  },
  plugins: [],
} satisfies Config;
