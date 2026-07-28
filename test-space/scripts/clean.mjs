import { execSync } from 'child_process'
execSync('cargo clean', { cwd: 'src-tauri', stdio: 'inherit' })
