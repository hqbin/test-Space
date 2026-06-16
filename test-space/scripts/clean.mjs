import { rmSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

console.log('Cleaning build cache...');

try { rmSync(join(root, 'dist'), { recursive: true, force: true }); console.log('  ✓ dist/'); } catch {}

// 如需强制清理 Rust 编译缓存，执行: node scripts/clean.mjs --full
if (process.argv.includes('--full')) {
  try { rmSync(join(root, 'src-tauri', 'target'), { recursive: true, force: true }); console.log('  ✓ src-tauri/target/'); } catch {}
}

console.log('Done.');
