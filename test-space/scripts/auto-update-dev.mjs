#!/usr/bin/env node

/**
 * 自动更新 DEVELOPMENT.md
 * 
 * 在每次 Git commit 后执行，根据 git diff 中的变更内容，自动在
 * DEVELOPMENT.md 中找到对应的页面/模块，追加一行变更记录。
 * 
 * 用法：
 *   1. 安装 Git Hook（推荐，只需执行一次）：
 *        node scripts/auto-update-dev.mjs --install
 *     之后每次 `git commit` 成功后脚本自动运行。
 *   2. 手动运行：
 *        node scripts/auto-update-dev.mjs
 * 
 * 工作原理：
 *   - 读取最后一条 commit 的 message + 变更文件列表
 *   - 根据文件路径映射到 DEVELOPMENT.md 中的页面/模块标题
 *   - 在对应标题下追加 "- 自动记录：<commit message>"
 *   - 如果找不到匹配的标题，则追加到 "未归类变更" 区域
 */

import { execSync } from 'child_process';
import { readFileSync, writeFileSync, existsSync, mkdirSync, copyFileSync, chmodSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const DEV_MD = resolve(ROOT, 'DEVELOPMENT.md');
const HOOKS_DIR = resolve(ROOT, '.git', 'hooks');
const HOOK_FILE = resolve(HOOKS_DIR, 'post-commit');

// 文件路径 → DEVELOPMENT.md 中的二级标题关键词
const MODULE_MAP = [
  { match: /src\/views\/device-space\/DeviceSpacePage/, title: 'Device Space' },
  { match: /src\/views\/api-space\/ApiSpacePage/,       title: 'API Space' },
  { match: /src\/views\/note-space\/NotesSpacePage/,    title: 'Notes Space' },
  { match: /src\/views\/script-space\/ScriptSpacePage/, title: 'Script Space' },
  { match: /src\/views\/settings\/SettingsPage/,        title: 'Settings' },
  { match: /src\/views\/case-space/,                    title: 'Case Space' },
  { match: /src\/stores\//,                              title: 'Store / State' },
  { match: /src\/services\//,                            title: 'Services (Database etc.)' },
  { match: /src\/composables\//,                         title: 'Composables' },
  { match: /src\/layouts\//,                             title: 'Layout / Sidebar' },
  { match: /src-tauri\/src\/adb\.rs/,                    title: 'ADB Module' },
  { match: /src-tauri\/src\/proxy\.rs/,                  title: 'Proxy (MITM)' },
  { match: /src-tauri\/src\/mirror\.rs/,                 title: 'Mirror (Scrcpy)' },
  { match: /src-tauri\/src\/script_exec\.rs/,            title: 'Script Execution' },
  { match: /src-tauri\/src\/serial_port\.rs/,            title: 'Serial Port' },
  { match: /src-tauri\/src\/lib\.rs/,                    title: 'Rust Entry (lib.rs)' },
  { match: /src\/views\/device-space\/PerfMonitorPage/,  title: 'PerfMonitor' },
];

// 未归类标题（若找不到匹配）
const DEFAULT_SECTION = '## 未归类变更';

// ----------------------------------------------------------------
// 安装钩子
function installHook() {
  const scriptPath = resolve(__dirname, 'auto-update-dev.mjs');
  if (!existsSync(scriptPath)) {
    console.error('❌ 找不到自身脚本文件:', scriptPath);
    process.exit(1);
  }

  // 确保 .git/hooks 目录存在
  if (!existsSync(HOOKS_DIR)) {
    mkdirSync(HOOKS_DIR, { recursive: true });
    console.log('📁 已创建 .git/hooks 目录');
  }

  // 写一个 shell 脚本快捷方式（跨平台兼容）
  const hookContent = `#!/bin/sh
node "${scriptPath}" "$@"
`;

  writeFileSync(HOOK_FILE, hookContent, 'utf-8');
  chmodSync(HOOK_FILE, 0o755); // 可执行

  console.log('✅ Git hook 已安装到', HOOK_FILE);
  console.log('   之后每次 `git commit` 成功后，会自动更新 DEVELOPMENT.md');
}

// ----------------------------------------------------------------
// 获取最后一次提交信息
function getLastCommitInfo() {
  const message = execSync('git log -1 --pretty=%B', { cwd: ROOT })
    .toString().trim().split('\n')[0]; // 取第一行 subject
  const files = execSync('git diff --name-only HEAD~1..HEAD', { cwd: ROOT })
    .toString().trim().split('\n').filter(Boolean);
  return { message, files };
}

function findModuleTitle(filePath) {
  for (const { match, title } of MODULE_MAP) {
    if (match.test(filePath)) return title;
  }
  return null;
}

function updateDevMd(content, entry) {
  const lines = content.split('\n');
  let inserted = false;

  // 尝试找到匹配的二级标题（## 或 ###）
  for (let i = 0; i < lines.length; i++) {
    const matchTitle = lines[i].match(/^#{2,3}\s+(.+)/);
    if (matchTitle && matchTitle[1].trim() === entry.section) {
      // 在该标题下插入条目，尽量放在该标题下的第一个未命名段落之后
      let insertIdx = i + 1;
      // 跳过空行和已有的列表项
      while (insertIdx < lines.length && 
             (lines[insertIdx].trim() === '' || 
              lines[insertIdx].trim().startsWith('-'))) {
        insertIdx++;
      }
      lines.splice(insertIdx, 0, '', `- **${entry.message}** (自动记录)`);
      inserted = true;
      break;
    }
  }

  if (!inserted) {
    // 追加到「未归类变更」区域，如果不存在则创建
    const defaultIdx = lines.findIndex(l => l.trim() === DEFAULT_SECTION);
    if (defaultIdx >= 0) {
      lines.splice(defaultIdx + 1, 0, `- **${entry.message}** (自动记录) — 涉及文件：${entry.files.slice(0,3).join(', ')}`);
    } else {
      lines.push('', DEFAULT_SECTION);
      lines.push(`- **${entry.message}** (自动记录) — 涉及文件：${entry.files.slice(0,3).join(', ')}`);
    }
  }

  return lines.join('\n');
}

function main() {
  const args = process.argv.slice(2);

  if (args.includes('--install') || args.includes('install')) {
    installHook();
    return;
  }

  if (!existsSync(DEV_MD)) {
    console.error('❌ 未找到 DEVELOPMENT.md');
    process.exit(1);
  }

  const { message, files } = getLastCommitInfo();
  if (!files.length) {
    console.log('➡️ 无文件变更，跳过更新');
    return;
  }

  console.log(`📦 最后一次提交: ${message}`);
  console.log(`📁 变更文件 (${files.length}):`);
  files.forEach(f => console.log(`   ${f}`));

  // 按模块分组
  const sectionGroups = new Map(); // section → files[]
  for (const file of files) {
    const section = findModuleTitle(file);
    if (section) {
      if (!sectionGroups.has(section)) sectionGroups.set(section, []);
      sectionGroups.get(section).push(file);
    }
  }

  // 读取当前 DEVELOPMENT.md
  let content = readFileSync(DEV_MD, 'utf-8');

  // 为每个模块生成一条更新记录
  for (const [section, modFiles] of sectionGroups) {
    const entry = {
      section,
      message: `${message} (${modFiles.length} files)`,
      files: modFiles,
    };
    content = updateDevMd(content, entry);
  }

  // 如果有些文件没有匹配到模块，也生成一个「未归类」条目
  const unmatched = files.filter(f => !findModuleTitle(f));
  if (unmatched.length > 0) {
    const entry = {
      section: DEFAULT_SECTION.replace(/^##\s+/, ''),  // 去掉标题 markdown
      message: `${message} (未归类)`,
      files: unmatched,
    };
    content = updateDevMd(content, entry);
  }

  // 写回文件
  writeFileSync(DEV_MD, content, 'utf-8');
  console.log('✅ DEVELOPMENT.md 已自动更新');
}

main();
