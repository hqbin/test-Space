# test-Space

基于 Tauri 2 + Vue 3 + Vite 的桌面应用。

## 环境要求

- Node.js >= 18
- Rust >= 1.77.2
- Visual Studio 2022 Build Tools（含 VC++ 工具集）
- ADB（可选，用于设备调试功能）

## 运行

```bash
cd test-space

# 安装前端依赖
npm install

# 开发模式（前端 HMR + Tauri 桌面窗口）
npm run tauri dev

# 仅启动前端 Web 开发服务器（浏览器预览）
npm run dev
```

## 构建

```bash
cd test-space
npm run tauri build    # 生产构建
npm run build          # 仅构建前端
```

## 调试

- **前端调试**: `npm run tauri dev` 启动后，Tauri 窗口内右键 → 检查，打开 Chrome DevTools；或使用 VS Code + Vite 调试配置
- **Rust 调试**: 使用 VS Code + CodeLLDB 扩展，配置 `.vscode/launch.json` 附加到 `npm run tauri dev` 进程
- **类型检查**: `npx vue-tsc --noEmit`
- **代码检查**: `npm run build`（含类型检查）

## 技术栈

| 层级 | 技术 |
|------|------|
| 桌面框架 | Tauri 2 |
| 前端 | Vue 3 + TypeScript + Pinia + Vue Router |
| 构建 | Vite 6 |
| 样式 | TailwindCSS 3 |
| 原生层 | Rust（ADB、串口、脚本执行）|