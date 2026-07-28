import { readFileSync, writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const pkgPath = resolve(root, 'package.json')
const tauriConfPath = resolve(root, 'src-tauri', 'tauri.conf.json')
const cargoTomlPath = resolve(root, 'src-tauri', 'Cargo.toml')

const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'))
const parts = pkg.version.split('.').map(Number)
const type = process.argv[2]

if (type === 'major') { parts[0]++; parts[1] = 0; parts[2] = 0 }
else if (type === 'minor') { parts[1]++; parts[2] = 0 }
else { parts[2]++ }

const newVersion = parts.join('.')

// Update package.json
pkg.version = newVersion
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n')

// Update tauri.conf.json
try {
  const tauriConf = JSON.parse(readFileSync(tauriConfPath, 'utf-8'))
  tauriConf.version = newVersion
  writeFileSync(tauriConfPath, JSON.stringify(tauriConf, null, 2) + '\n')
} catch (e) {
  console.warn('Failed to update tauri.conf.json:', e.message)
}

// Update Cargo.toml
try {
  const cargo = readFileSync(cargoTomlPath, 'utf-8')
  const updated = cargo.replace(/^version\s*=\s*"[^"]+"/m, `version = "${newVersion}"`)
  writeFileSync(cargoTomlPath, updated)
} catch (e) {
  console.warn('Failed to update Cargo.toml:', e.message)
}

console.log(`Bumped to ${newVersion}`)
