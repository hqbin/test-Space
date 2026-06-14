import type Database from '@tauri-apps/plugin-sql'

let db: Database | null = null

async function getDb(): Promise<Database> {
  if (db) return db
  const { default: DatabaseClass } = await import('@tauri-apps/plugin-sql')
  const { appDataDir } = await import('@tauri-apps/api/path')
  const dir = await appDataDir()
  db = await DatabaseClass.load(`sqlite:${dir}/test-space.db`)
  console.log('[DB] path:', `sqlite:${dir}/test-space.db`)
  await migrate()
  return db
}

async function migrate() {
  const d = await getDb()
  await d.execute(`CREATE TABLE IF NOT EXISTS field_rule_sets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    rules TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS case_files (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    data TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    custom_fields TEXT NOT NULL DEFAULT '[]',
    rule_set_id TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS recent_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    case_count INTEGER NOT NULL DEFAULT 0,
    last_opened TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS favorites (
    path TEXT PRIMARY KEY,
    added_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
  )`)
}

export async function closeDb() {
  if (db) {
    await db.close()
    db = null
  }
}

export async function loadSettings(): Promise<Record<string, string>> {
  const d = await getDb()
  const rows = await d.select<{ key: string; value: string }[]>('SELECT key, value FROM app_settings')
  const map: Record<string, string> = {}
  for (const r of rows) map[r.key] = r.value
  return map
}

export async function getSetting(key: string): Promise<string | null> {
  const d = await getDb()
  const rows = await d.select<{ value: string }[]>('SELECT value FROM app_settings WHERE key = ?', [key])
  return rows.length > 0 ? rows[0].value : null
}

export async function setSetting(key: string, value: string) {
  const d = await getDb()
  await d.execute(
    'INSERT INTO app_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value',
    [key, value]
  )
}

// ── Field Rule Sets ──────────────────────────────────────────

export async function loadFieldRuleSets(): Promise<any[]> {
  const d = await getDb()
  const rows = await d.select<{ id: string; name: string; rules: string; created_at: string; updated_at: string }[]>(
    'SELECT * FROM field_rule_sets ORDER BY created_at ASC'
  )
  return rows.map(r => ({ ...r, rules: JSON.parse(r.rules) }))
}

export async function saveFieldRuleSet(set: { id: string; name: string; rules: any[]; createdAt: string; updatedAt?: string }) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO field_rule_sets (id, name, rules, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET name = excluded.name, rules = excluded.rules, updated_at = excluded.updated_at`,
    [set.id, set.name, JSON.stringify(set.rules), set.createdAt, set.updatedAt || now]
  )
}

export async function deleteFieldRuleSet(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM field_rule_sets WHERE id = ?', [id])
}

// ── Case Files ───────────────────────────────────────────────

export async function loadCaseFiles(): Promise<any[]> {
  const d = await getDb()
  return await d.select('SELECT * FROM case_files ORDER BY updated_at DESC')
}

export async function loadCaseFile(id: string): Promise<any | null> {
  const d = await getDb()
  const rows = await d.select<any[]>('SELECT * FROM case_files WHERE id = ?', [id])
  return rows.length > 0 ? rows[0] : null
}

export async function saveCaseFile(file: { id: string; name: string; data: any; tags?: string[]; customFields?: any[]; ruleSetId?: string; createdAt: string; updatedAt?: string }) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO case_files (id, name, data, tags, custom_fields, rule_set_id, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name,
       data = excluded.data,
       tags = excluded.tags,
       custom_fields = excluded.custom_fields,
       rule_set_id = excluded.rule_set_id,
       updated_at = excluded.updated_at`,
    [
      file.id,
      file.name,
      JSON.stringify(file.data),
      JSON.stringify(file.tags || []),
      JSON.stringify(file.customFields || []),
      file.ruleSetId || '',
      file.createdAt,
      file.updatedAt || now,
    ]
  )
}

export async function deleteCaseFile(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM case_files WHERE id = ?', [id])
}

export async function searchCaseFiles(query: string): Promise<any[]> {
  const d = await getDb()
  return await d.select(
    'SELECT * FROM case_files WHERE name LIKE ? ORDER BY updated_at DESC',
    [`%${query}%`]
  )
}

// ── Recent Files ─────────────────────────────────────────────

export async function getRecentFiles(): Promise<any[]> {
  const d = await getDb()
  return await d.select('SELECT * FROM recent_files ORDER BY last_opened DESC LIMIT 50')
}

export async function addRecentFile(path: string, name: string, caseCount: number) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO recent_files (path, name, case_count, last_opened)
     VALUES (?, ?, ?, ?)
     ON CONFLICT(path) DO UPDATE SET
       name = excluded.name,
       case_count = excluded.case_count,
       last_opened = excluded.last_opened`,
    [path, name, caseCount, new Date().toISOString()]
  )
}

export async function removeRecentFile(path: string) {
  const d = await getDb()
  await d.execute('DELETE FROM recent_files WHERE path = ?', [path])
}

// ── Favorites ────────────────────────────────────────────────

export async function getFavorites(): Promise<string[]> {
  const d = await getDb()
  const rows = await d.select<{ path: string }[]>('SELECT path FROM favorites ORDER BY added_at DESC')
  return rows.map(r => r.path)
}

export async function toggleFavorite(path: string): Promise<boolean> {
  const d = await getDb()
  const existing = await d.select<{ path: string }[]>('SELECT path FROM favorites WHERE path = ?', [path])
  if (existing.length > 0) {
    await d.execute('DELETE FROM favorites WHERE path = ?', [path])
    return false
  } else {
    await d.execute('INSERT INTO favorites (path, added_at) VALUES (?, ?)', [path, new Date().toISOString()])
    return true
  }
}

export async function isFavorite(path: string): Promise<boolean> {
  const d = await getDb()
  const rows = await d.select<{ path: string }[]>('SELECT path FROM favorites WHERE path = ?', [path])
  return rows.length > 0
}

// ── Export / Import ──────────────────────────────────────────

export interface AppBackup {
  version: string
  exportedAt: string
  fieldRuleSets: any[]
  caseFiles: any[]
  recentFiles: any[]
  favorites: string[]
  settings: Record<string, string>
}

export async function exportAllData(): Promise<AppBackup> {
  const fieldRuleSets = await loadFieldRuleSets()
  const caseFiles = await loadCaseFiles()
  const recentFiles = await getRecentFiles()
  const favPaths = await getFavorites()
  const settings = await loadSettings()
  return {
    version: '1.0',
    exportedAt: new Date().toISOString(),
    fieldRuleSets,
    caseFiles,
    recentFiles,
    favorites: favPaths,
    settings,
  }
}

export async function importAllData(backup: AppBackup) {
  const d = await getDb()
  await d.execute('DELETE FROM field_rule_sets')
  await d.execute('DELETE FROM case_files')
  await d.execute('DELETE FROM recent_files')
  await d.execute('DELETE FROM favorites')
  await d.execute('DELETE FROM app_settings')

  for (const s of backup.fieldRuleSets || []) {
    await d.execute(
      'INSERT INTO field_rule_sets (id, name, rules, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
      [s.id, s.name, JSON.stringify(s.rules), s.createdAt || s.created_at, s.updatedAt || s.updated_at || s.createdAt]
    )
  }
  for (const f of backup.caseFiles || []) {
    await d.execute(
      'INSERT INTO case_files (id, name, data, tags, custom_fields, rule_set_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      [f.id, f.name, f.data || JSON.stringify(f), JSON.stringify(f.tags || []), JSON.stringify(f.custom_fields || f.customFields || []), f.rule_set_id || f.ruleSetId || '', f.created_at || f.createdAt, f.updated_at || f.updatedAt]
    )
  }
  for (const r of backup.recentFiles || []) {
    await d.execute(
      'INSERT INTO recent_files (path, name, case_count, last_opened) VALUES (?, ?, ?, ?)',
      [r.path, r.name, r.case_count || r.caseCount || 0, r.last_opened || r.lastOpened]
    )
  }
  for (const path of backup.favorites || []) {
    await d.execute(
      'INSERT INTO favorites (path, added_at) VALUES (?, ?)',
      [path, new Date().toISOString()]
    )
  }
  for (const [key, value] of Object.entries(backup.settings || {})) {
    await d.execute(
      'INSERT INTO app_settings (key, value) VALUES (?, ?)',
      [key, value]
    )
  }
}
