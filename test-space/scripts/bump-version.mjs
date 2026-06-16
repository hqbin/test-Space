import { readFileSync, writeFileSync } from 'fs';
import { execSync } from 'child_process';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = join(__dirname, '..');

const bumpType = process.argv[2] || 'patch';
if (!['patch', 'minor', 'major'].includes(bumpType)) {
  console.error(`Usage: node scripts/bump-version.mjs [patch|minor|major]`);
  process.exit(1);
}

// 1. Read current version from package.json
const pkgPath = join(root, 'package.json');
const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'));
const oldVersion = pkg.version;

// 2. Calculate new version
const parts = oldVersion.split('.').map(Number);
let [major, minor, patch] = parts;
if (bumpType === 'major') { major += 1; minor = 0; patch = 0; }
else if (bumpType === 'minor') { minor += 1; patch = 0; }
else { patch += 1; }
const newVersion = `${major}.${minor}.${patch}`;

console.log(`Bumping version: ${oldVersion} → ${newVersion} (${bumpType})`);

// 3. Update package.json
pkg.version = newVersion;
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n');
console.log(`  ✓ package.json`);

// 4. Update src-tauri/tauri.conf.json
const tauriConfPath = join(root, 'src-tauri', 'tauri.conf.json');
let tauriConf = readFileSync(tauriConfPath, 'utf-8');
tauriConf = tauriConf.replace(/"version":\s*"[^"]+"/, `"version": "${newVersion}"`);
writeFileSync(tauriConfPath, tauriConf);
console.log(`  ✓ src-tauri/tauri.conf.json`);

// 5. Update src-tauri/Cargo.toml
const cargoPath = join(root, 'src-tauri', 'Cargo.toml');
let cargo = readFileSync(cargoPath, 'utf-8');
cargo = cargo.replace(/^version\s*=\s*"[^"]+"/m, `version = "${newVersion}"`);
writeFileSync(cargoPath, cargo);
console.log(`  ✓ src-tauri/Cargo.toml`);

console.log(`\nDone! Ready to build: npm run tauri build`);
