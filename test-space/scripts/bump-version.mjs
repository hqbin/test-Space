import { readFileSync, writeFileSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const root = resolve(__dirname, '..')
const pkgPath = resolve(root, 'package.json')

const pkg = JSON.parse(readFileSync(pkgPath, 'utf-8'))
const parts = pkg.version.split('.').map(Number)
const type = process.argv[2]

if (type === 'major') { parts[0]++; parts[1] = 0; parts[2] = 0 }
else if (type === 'minor') { parts[1]++; parts[2] = 0 }
else { parts[2]++ }

pkg.version = parts.join('.')
writeFileSync(pkgPath, JSON.stringify(pkg, null, 2) + '\n')
console.log(`Bumped to ${pkg.version}`)
