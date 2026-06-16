# test-Space

基于 Tauri 2 + Vue 3 + Vite 的桌面应用。

## 环境要求

- Node.js >= 18
- Rust >= 1.77.2
- Visual Studio 2022 Build Tools（含 VC++ 工具集）
- ADB（可选，用于设备调试功能）

## 日常开发

```bash
cd test-space
npm install                # 安装依赖（首次或依赖变更后）
npm run tauri dev          # 启动开发模式（前端 HMR + 桌面窗口）
npm run dev                # 仅启动前端 Web 服务器（浏览器预览）
```

## 调试

- **前端调试**: `npm run tauri dev` 启动后，Tauri 窗口内右键 → 检查，打开 Chrome DevTools
- **Rust 调试**: VS Code + CodeLLDB 扩展，附加到 `npm run tauri dev` 进程
- **类型检查**: `npx vue-tsc --noEmit`

## 清缓存

```bash
node scripts/clean.mjs           # 清理 dist/ 目录
node scripts/clean.mjs --full    # 同时清理 src-tauri/target/（Rust 编译缓存）
```

清缓存后首次编译会较慢，属正常现象。

## 改版本

版本号同步写在三个文件中：`package.json`、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml`，使用脚本一键修改：

```bash
npm run version:patch      # 0.1.3 → 0.1.4
npm run version:minor      # 0.1.3 → 0.2.0
npm run version:major      # 0.1.3 → 1.0.0
```

## 打包发布

```bash
npm run release:patch      # 改版本 + 清缓存 + 生产构建
npm run release:minor
npm run release:major
```

构建产物位于 `src-tauri/target/release/bundle/`，包含 `.msi` 安装包。