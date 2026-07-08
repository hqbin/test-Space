import type Database from '@tauri-apps/plugin-sql'
import DOMPurify from 'dompurify'
import type { InputHistoryEntry, LogSession, NoteSpace, NoteFolder, NoteItem, NoteVersion, NoteLink, AutoCase, AutoCaseVersion, AutoRunRecord, AutoRunStep, AutoStateGraph } from '@/types'
import type { ApiRewriteRule } from '@/types'

let db: Database | null = null
let dbPromise: Promise<Database> | null = null

function escapeLike(s: string): string {
  return s.replace(/\\/g, '\\\\').replace(/%/g, '\\%').replace(/_/g, '\\_')
}

function safeJsonParse<T = any>(raw: string | null | undefined, fallback: T): T {
  if (!raw) return fallback
  try { return JSON.parse(raw) } catch { return fallback }
}

async function initDb(): Promise<Database> {
  const { default: DatabaseClass } = await import('@tauri-apps/plugin-sql')
  const { appDataDir } = await import('@tauri-apps/api/path')
  const dir = await appDataDir()
  const instance = await DatabaseClass.load(`sqlite:${dir}/test-space.db`)
  await instance.execute('PRAGMA journal_mode = WAL')
  await instance.execute('PRAGMA busy_timeout = 30000')
  console.log('[DB] path:', `sqlite:${dir}/test-space.db`)
  await migrateInternal(instance)
  return instance
}

async function getDb(): Promise<Database> {
  if (db) return db
  if (!dbPromise) dbPromise = initDb()
  db = await dbPromise
  return db
}

async function migrateInternal(d: Database) {
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
  await d.execute(`CREATE TABLE IF NOT EXISTS input_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key_name TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL,
    sort_order INTEGER DEFAULT 0
  )`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_input_history_key ON input_history(key_name)`)
  await d.execute(`CREATE TABLE IF NOT EXISTS log_sessions (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    device_serial TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    started_at TEXT NOT NULL,
    metadata TEXT NOT NULL DEFAULT '{}'
  )`)
  // ── Notes Space ─────────────────────────────────────────────
  await d.execute(`CREATE TABLE IF NOT EXISTS note_spaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS note_folders (
    id TEXT PRIMARY KEY,
    space_id TEXT,
    name TEXT NOT NULL,
    parent_id TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  // Migrate: add space_id column if missing (existing DBs)
  try { await d.execute('ALTER TABLE note_folders ADD COLUMN space_id TEXT') } catch {}
  await d.execute(`CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    folder_id TEXT,
    title TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL DEFAULT '',
    tags TEXT NOT NULL DEFAULT '[]',
    is_favorite INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS note_versions (
    id TEXT PRIMARY KEY,
    note_id TEXT NOT NULL,
    content TEXT NOT NULL,
    saved_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS note_links (
    id TEXT PRIMARY KEY,
    source_note_id TEXT NOT NULL,
    target_note_id TEXT NOT NULL,
    created_at TEXT NOT NULL
  )`)
  try { await d.execute('ALTER TABLE notes ADD COLUMN plain_text TEXT NOT NULL DEFAULT \'\'') } catch {}
  try { await d.execute('ALTER TABLE notes ADD COLUMN content_json TEXT') } catch {}
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes(folder_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_notes_fav ON notes(is_favorite)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_notes_updated ON notes(updated_at)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_folders_space ON note_folders(space_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_folders_parent ON note_folders(parent_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_versions_note ON note_versions(note_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_links_source ON note_links(source_note_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_links_target ON note_links(target_note_id)`)
  await d.execute(`CREATE TABLE IF NOT EXISTS note_ai_memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  // ── Automation (Auto Space) ──────────────────────────────────
  await d.execute(`CREATE TABLE IF NOT EXISTS auto_cases (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    file_key    TEXT NOT NULL UNIQUE,
    module      TEXT NOT NULL DEFAULT '',
    tags        TEXT NOT NULL DEFAULT '[]',
    priority    TEXT NOT NULL DEFAULT 'P2',
    author      TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    yaml_content TEXT NOT NULL,
    version     TEXT NOT NULL DEFAULT '1.0',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
  )`)
  try { await d.execute('ALTER TABLE auto_cases ADD COLUMN module TEXT NOT NULL DEFAULT \'\'') } catch {}
  await d.execute(`CREATE TABLE IF NOT EXISTS auto_case_versions (
    id          TEXT PRIMARY KEY,
    case_id     TEXT NOT NULL REFERENCES auto_cases(id) ON DELETE CASCADE,
    version     TEXT NOT NULL,
    yaml_content TEXT NOT NULL,
    saved_by    TEXT NOT NULL DEFAULT '',
    saved_at    TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS auto_run_records (
    id          TEXT PRIMARY KEY,
    trigger     TEXT NOT NULL DEFAULT 'manual',
    device_serial TEXT NOT NULL DEFAULT '',
    device_info TEXT NOT NULL DEFAULT '{}',
    suite_config TEXT NOT NULL DEFAULT '{}',
    status      TEXT NOT NULL DEFAULT 'running',
    total       INTEGER NOT NULL DEFAULT 0,
    passed      INTEGER NOT NULL DEFAULT 0,
    failed      INTEGER NOT NULL DEFAULT 0,
    healed      INTEGER NOT NULL DEFAULT 0,
    skipped     INTEGER NOT NULL DEFAULT 0,
    duration_ms INTEGER NOT NULL DEFAULT 0,
    report_path TEXT NOT NULL DEFAULT '',
    started_at  TEXT NOT NULL,
    ended_at    TEXT
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS auto_run_steps (
    id            TEXT PRIMARY KEY,
    run_id        TEXT NOT NULL REFERENCES auto_run_records(id) ON DELETE CASCADE,
    case_id       TEXT NOT NULL,
    step_id       TEXT NOT NULL,
    step_desc     TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL,
    duration_ms   INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    heal_log      TEXT,
    screenshot_before TEXT,
    screenshot_after  TEXT,
    screenshot_ref    TEXT,
    locator_used  TEXT,
    created_at    TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS auto_state_graphs (
    id          TEXT PRIMARY KEY,
    app_package TEXT NOT NULL,
    app_version TEXT NOT NULL DEFAULT '',
    device_info TEXT NOT NULL DEFAULT '{}',
    graph_json  TEXT NOT NULL,
    node_count  INTEGER NOT NULL DEFAULT 0,
    edge_count  INTEGER NOT NULL DEFAULT 0,
    explore_duration_ms INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'bat',
    content TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  // Add sort_order column if not exists (safe migration for existing installs)
  try {
    await d.execute(`ALTER TABLE scripts ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0`)
    // Back-fill existing rows with a stable default order based on updated_at
    await d.execute(`UPDATE scripts SET sort_order = rowid`)
  } catch {
    // Column already exists — ignore
  }
  // FTS5 full-text search for notes
  try {
    await d.execute(`CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
      note_id, title, plain_text, tags,
      tokenize='unicode61'
    )`)
  } catch (e) {
    console.warn('[DB] FTS5 not available, falling back to LIKE search')
  }
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

// ── Cloud Backup Settings ────────────────────────────────────

export async function checkDatabaseReady() {
  const d = await getDb()
  await d.select('SELECT 1')
}

const DEVICE_ID_LIST_KEY = "cloud_device_id_list";
const DEVICE_ID_LAST_KEY = "cloud_device_id_last";

export async function getDeviceIdList(): Promise<string[]> {
  const raw = await getSetting(DEVICE_ID_LIST_KEY);
  return raw ? safeJsonParse<string[]>(raw, []) : [];
}

export async function saveDeviceIdList(ids: string[]) {
  await setSetting(DEVICE_ID_LIST_KEY, JSON.stringify(ids));
}

export async function getLastDeviceId(): Promise<string | null> {
  return getSetting(DEVICE_ID_LAST_KEY);
}

export async function saveLastDeviceId(id: string) {
  await setSetting(DEVICE_ID_LAST_KEY, id);
}

const DEVICE_ID_NAMES_KEY = "cloud_device_id_names";

export async function getDeviceIdNames(): Promise<Record<string, string>> {
  const raw = await getSetting(DEVICE_ID_NAMES_KEY);
  return raw ? safeJsonParse<Record<string, string>>(raw, {}) : {};
}

export async function saveDeviceIdNames(names: Record<string, string>) {
  await setSetting(DEVICE_ID_NAMES_KEY, JSON.stringify(names));
}

// ── Field Rule Sets ──────────────────────────────────────────

export async function loadFieldRuleSets(): Promise<any[]> {
  const d = await getDb()
  const rows = await d.select<{ id: string; name: string; rules: string; created_at: string; updated_at: string }[]>(
    'SELECT * FROM field_rule_sets ORDER BY created_at ASC'
  )
  return rows.map(r => ({ ...r, rules: safeJsonParse(r.rules, []) }))
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
    'SELECT * FROM case_files WHERE name LIKE ? ESCAPE \'\\\' ORDER BY updated_at DESC',
    [`%${escapeLike(query)}%`]
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
    await d.execute('INSERT OR IGNORE INTO favorites (path, added_at) VALUES (?, ?)', [path, new Date().toISOString()])
    return true
  }
}

export async function isFavorite(path: string): Promise<boolean> {
  const d = await getDb()
  const rows = await d.select<{ path: string }[]>('SELECT path FROM favorites WHERE path = ?', [path])
  return rows.length > 0
}

// ── Input History ────────────────────────────────────────────

export async function addInputHistory(key: string, value: string, maxEntries = 20) {
  const d = await getDb()
  const now = new Date().toISOString()
  // Remove duplicate for same key+value
  await d.execute(
    'DELETE FROM input_history WHERE key_name = ? AND value = ?',
    [key, value]
  )
  // Insert new entry at top
  await d.execute(
    'INSERT INTO input_history (key_name, value, created_at, sort_order) VALUES (?, ?, ?, ?)',
    [key, value, now, Date.now()]
  )
  // Trim to max entries
  await d.execute(
    `DELETE FROM input_history WHERE key_name = ? AND id NOT IN (
      SELECT id FROM input_history WHERE key_name = ? ORDER BY sort_order DESC LIMIT ?
    )`,
    [key, key, maxEntries]
  )
}

export async function getInputHistory(key: string, limit = 15): Promise<InputHistoryEntry[]> {
  const d = await getDb()
  return await d.select<InputHistoryEntry[]>(
    'SELECT id, key_name as keyName, value, created_at as createdAt FROM input_history WHERE key_name = ? ORDER BY sort_order DESC LIMIT ?',
    [key, limit]
  )
}

export async function clearInputHistory(key?: string) {
  const d = await getDb()
  if (key) {
    await d.execute('DELETE FROM input_history WHERE key_name = ?', [key])
  } else {
    await d.execute('DELETE FROM input_history')
  }
}

// ── Log Sessions ─────────────────────────────────────────────

export async function saveLogSession(session: { id: string; type: string; deviceSerial: string; status: string; startedAt: string; metadata?: string }) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO log_sessions (id, type, device_serial, status, started_at, metadata)
     VALUES (?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET status = excluded.status, metadata = excluded.metadata`,
    [session.id, session.type, session.deviceSerial, session.status, session.startedAt, session.metadata || '{}']
  )
}

export async function getRunningLogSessions(): Promise<LogSession[]> {
  const d = await getDb()
  return await d.select<LogSession[]>(
    `SELECT id, type, device_serial as deviceSerial, status, started_at as startedAt, metadata
     FROM log_sessions WHERE status = 'running' ORDER BY started_at DESC`
  )
}

export async function removeLogSession(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM log_sessions WHERE id = ?', [id])
}

// ── Note Spaces ──────────────────────────────────────────────

export async function loadNoteSpaces(): Promise<NoteSpace[]> {
  const d = await getDb()
  return await d.select<NoteSpace[]>(
    'SELECT id, name, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM note_spaces ORDER BY sort_order ASC, created_at ASC'
  )
}

export async function saveNoteSpace(space: { id: string; name: string; sortOrder?: number }) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO note_spaces (id, name, sort_order, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET name = excluded.name, sort_order = excluded.sort_order, updated_at = excluded.updated_at`,
    [space.id, space.name, space.sortOrder || 0, now, now]
  )
}

export async function deleteNoteSpace(id: string) {
  const d = await getDb()
  // First: move notes out of folders that belong to this space
  await d.execute('UPDATE notes SET folder_id = NULL WHERE folder_id IN (SELECT id FROM note_folders WHERE space_id = ?)', [id])
  // Second: delete folders
  await d.execute('DELETE FROM note_folders WHERE space_id = ?', [id])
  // Third: delete the space itself
  await d.execute('DELETE FROM note_spaces WHERE id = ?', [id])
}

export async function renameNoteSpace(id: string, name: string) {
  const d = await getDb()
  await d.execute('UPDATE note_spaces SET name = ?, updated_at = ? WHERE id = ?', [name, new Date().toISOString(), id])
}

// ── Note Folders ─────────────────────────────────────────────

export async function loadNoteFolders(spaceId?: string): Promise<NoteFolder[]> {
  const d = await getDb()
  if (spaceId) {
    return await d.select<NoteFolder[]>(
      'SELECT id, space_id as spaceId, name, parent_id as parentId, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM note_folders WHERE space_id = ? ORDER BY sort_order ASC, created_at ASC',
      [spaceId]
    )
  }
  return await d.select<NoteFolder[]>(
    'SELECT id, space_id as spaceId, name, parent_id as parentId, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM note_folders ORDER BY sort_order ASC, created_at ASC'
  )
}

export async function saveNoteFolder(folder: { id: string; spaceId?: string | null; name: string; parentId?: string | null; sortOrder?: number }) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO note_folders (id, space_id, name, parent_id, sort_order, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET space_id = excluded.space_id, name = excluded.name, parent_id = excluded.parent_id, sort_order = excluded.sort_order, updated_at = excluded.updated_at`,
    [folder.id, folder.spaceId || null, folder.name, folder.parentId || null, folder.sortOrder || 0, now, now]
  )
}

export async function deleteNoteFolder(id: string) {
  const d = await getDb()
  // Collect all descendant folder IDs (BFS)
  const allIds: string[] = [id]
  let currentIds = [id]
  while (currentIds.length > 0) {
    const placeholders = currentIds.map(() => '?').join(',')
    const children = await d.select<{ id: string }[]>(
      `SELECT id FROM note_folders WHERE parent_id IN (${placeholders})`, currentIds
    )
    const childIds = children.map(c => c.id)
    if (childIds.length === 0) break
    allIds.push(...childIds)
    currentIds = childIds
  }
  // Move notes in all these folders to uncategorized
  const placeholders = allIds.map(() => '?').join(',')
  await d.execute(`UPDATE notes SET folder_id = NULL WHERE folder_id IN (${placeholders})`, allIds)
  // Delete all descendant folders first (children before parents to respect FK order)
  await d.execute(`DELETE FROM note_folders WHERE id IN (${placeholders})`, allIds)
}

export async function deleteNoteFolderWithNotes(id: string) {
  const d = await getDb()
  // Collect all descendant folder IDs (BFS)
  const allIds: string[] = [id]
  let currentIds = [id]
  while (currentIds.length > 0) {
    const placeholders = currentIds.map(() => '?').join(',')
    const children = await d.select<{ id: string }[]>(
      `SELECT id FROM note_folders WHERE parent_id IN (${placeholders})`, currentIds
    )
    const childIds = children.map(c => c.id)
    if (childIds.length === 0) break
    allIds.push(...childIds)
    currentIds = childIds
  }
  // Delete notes in all these folders
  const placeholders = allIds.map(() => '?').join(',')
  await d.execute(`DELETE FROM notes WHERE folder_id IN (${placeholders})`, allIds)
  // Delete all descendant folders
  await d.execute(`DELETE FROM note_folders WHERE id IN (${placeholders})`, allIds)
}

export async function renameNoteFolder(id: string, name: string) {
  const d = await getDb()
  await d.execute('UPDATE note_folders SET name = ?, updated_at = ? WHERE id = ?', [name, new Date().toISOString(), id])
}

// ── Notes ─────────────────────────────────────────────────────

let _plainTextRepaired = false

export async function loadNotes(): Promise<NoteItem[]> {
  const d = await getDb()
  if (!_plainTextRepaired) await repairEmptyPlainText(d)
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, content_json as contentJson, plain_text as plainText,
            tags, is_favorite as isFavorite, created_at as createdAt, updated_at as updatedAt
     FROM notes ORDER BY title COLLATE NOCASE ASC`
  )
  return rows.map(r => ({ ...r, tags: safeJsonParse(r.tags, []), isFavorite: !!r.isFavorite, plainText: r.plainText || '' }))
}

export async function loadNoteList(): Promise<NoteItem[]> {
  const d = await getDb()
  if (!_plainTextRepaired) await repairEmptyPlainText(d)
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, '' as content, '' as contentJson, plain_text as plainText, tags,
            is_favorite as isFavorite, created_at as createdAt, updated_at as updatedAt
     FROM notes ORDER BY title COLLATE NOCASE ASC`
  )
  return rows.map(r => ({ ...r, tags: safeJsonParse(r.tags, []), isFavorite: !!r.isFavorite, plainText: r.plainText || '' }))
}

export async function loadNote(id: string): Promise<NoteItem | null> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, content_json as contentJson, plain_text as plainText,
            tags, is_favorite as isFavorite, created_at as createdAt, updated_at as updatedAt
     FROM notes WHERE id = ?`, [id]
  )
  if (rows.length === 0) return null
  const r = rows[0]
  return { ...r, tags: safeJsonParse(r.tags, []), isFavorite: !!r.isFavorite, plainText: r.plainText || '' }
}

function htmlToPlainText(html: string): string {
  const doc = new DOMParser().parseFromString(html, 'text/html')
  doc.querySelectorAll('img').forEach(img => {
    const alt = img.getAttribute('alt') || ''
    const placeholder = document.createTextNode(alt ? `[图片: ${alt}]` : '[图片]')
    img.replaceWith(placeholder)
  })
  return (doc.body.textContent || '')
    .replace(/\r\n/g, '\n')
    .replace(/[\u00A0\u202F\u2007]/g, ' ')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

async function repairEmptyPlainText(d: Database) {
  // Check persistent flag first — if repair was done in a previous session, skip entirely.
  try {
    const rows = await d.select<{ value: string }[]>(
      `SELECT value FROM app_settings WHERE key = 'plain_text_repaired'`
    )
    if (rows.length > 0 && rows[0].value === '1') {
      _plainTextRepaired = true
      return
    }
  } catch {}

  try {
    const rows = await d.select<{ id: string; content: string }[]>(
      `SELECT id, content FROM notes WHERE content IS NOT NULL AND content != '' AND (plain_text IS NULL OR plain_text = '')`
    )
    for (const row of rows) {
      const plainText = htmlToPlainText(DOMPurify.sanitize(row.content))
      if (plainText) {
        await d.execute('UPDATE notes SET plain_text = ? WHERE id = ?', [plainText, row.id])
        try {
          await d.execute('DELETE FROM notes_fts WHERE note_id = ?', [row.id])
          await d.execute(
            'INSERT INTO notes_fts (note_id, title, plain_text, tags) SELECT id, title, ?, tags FROM notes WHERE id = ?',
            [plainText, row.id]
          )
        } catch {}
      }
    }
    if (rows.length > 0) console.log(`[DB] Repaired plain_text for ${rows.length} notes`)
    _plainTextRepaired = true
    // Persist the flag so future startups skip this scan entirely
    await d.execute(
      `INSERT INTO app_settings (key, value) VALUES ('plain_text_repaired', '1')
       ON CONFLICT(key) DO UPDATE SET value = '1'`
    )
  } catch {}
}

export async function saveNote(note: { id: string; folderId?: string | null; title: string; content: string; contentJson?: string | null; tags?: string[]; isFavorite?: boolean }) {
  const d = await getDb()
  const now = new Date().toISOString()
  const safeContent = DOMPurify.sanitize(note.content)
  const plainText = htmlToPlainText(safeContent)
  const cj = note.contentJson || null
  await d.execute(
    `INSERT INTO notes (id, folder_id, title, content, content_json, plain_text, tags, is_favorite, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       folder_id = excluded.folder_id, title = excluded.title,
       content = CASE WHEN length(trim(excluded.content)) = 0 THEN content ELSE excluded.content END,
       content_json = CASE WHEN length(trim(excluded.content)) = 0 THEN content_json ELSE excluded.content_json END,
       plain_text = CASE WHEN length(trim(excluded.content)) = 0 THEN plain_text ELSE excluded.plain_text END,
       tags = excluded.tags,
       is_favorite = excluded.is_favorite, updated_at = excluded.updated_at`,
    [note.id, note.folderId || null, note.title, safeContent, cj, plainText,
     JSON.stringify(note.tags || []), note.isFavorite ? 1 : 0, now, now]
  )
  // Sync FTS5 index
  try {
    await d.execute(
"DELETE FROM notes_fts WHERE note_id = ?"
, [note.id])
    await d.execute(
"INSERT INTO notes_fts (note_id, title, plain_text, tags) VALUES (?, ?, ?, ?)"
,
      [note.id, note.title, plainText, JSON.stringify(note.tags || [])])
  } catch {}
}

export async function deleteNote(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM note_versions WHERE note_id = ?', [id])
  await d.execute('DELETE FROM note_links WHERE source_note_id = ? OR target_note_id = ?', [id, id])
  await d.execute('DELETE FROM notes WHERE id = ?', [id])
  try { await d.execute('DELETE FROM notes_fts WHERE note_id = ?', [id]) } catch {}
}

export async function toggleNoteFavorite(id: string): Promise<boolean> {
  const d = await getDb()
  const rows = await d.select<{ is_favorite: number }[]>('SELECT is_favorite FROM notes WHERE id = ?', [id])
  if (rows.length === 0) return false
  const newVal = rows[0].is_favorite ? 0 : 1
  await d.execute('UPDATE notes SET is_favorite = ?, updated_at = ? WHERE id = ?', [newVal, new Date().toISOString(), id])
  return !!newVal
}

function buildFtsQuery(query: string): string {
  const words = query.trim().split(/\s+/).filter(Boolean)
  if (words.length === 0) return ""
  const escaped = words.map(w => {
    const safe = w.replace(/"/g, '""')
    return '"' + safe + '"*'
  })
  return escaped.join(" AND ")
}

export async function rebuildFtsIndex(externalDb?: Database) {
  try {
    const d = externalDb ?? await getDb()
    await d.execute("DELETE FROM notes_fts")
    const notes = await d.select<any[]>("SELECT id, title, plain_text, tags FROM notes")
    for (const note of notes) {
      try {
        await d.execute(
          "INSERT INTO notes_fts (note_id, title, plain_text, tags) VALUES (?, ?, ?, ?)",
          [note.id, note.title, note.plain_text || "", note.tags || "[]"]
        )
      } catch {}
    }
    console.log("[DB] FTS5 index rebuilt:", notes.length, "notes indexed")
  } catch (e) {
    console.warn("[DB] FTS5 rebuild failed:", e)
  }
}

export async function searchNotes(query: string): Promise<NoteItem[]> {
  const d = await getDb()
  
  // Try FTS5 full-text search first
  try {
    const ftsQuery = buildFtsQuery(query)
    if (ftsQuery) {
      const ftRows = await d.select<{ note_id: string }[]>(
        "SELECT note_id FROM notes_fts WHERE notes_fts MATCH ? ORDER BY rank",
        [ftsQuery]
      )
      if (ftRows.length > 0) {
        const ids = ftRows.map(r => r.note_id)
        const placeholders = ids.map(() => "?").join(",")
        const rows = await d.select<any[]>(
          `SELECT id, folder_id as folderId, title, content, content_json as contentJson, plain_text as plainText,
                  tags, is_favorite as isFavorite, created_at as createdAt, updated_at as updatedAt
           FROM notes WHERE id IN (${placeholders})`,
          ids
        )
        return rows.map(r => ({ ...r, tags: safeJsonParse(r.tags, []), isFavorite: !!r.isFavorite, plainText: r.plainText || "" }))
      }
      return []
    }
  } catch (e) {
    console.warn("[DB] FTS5 search failed, fallback to LIKE:", e)
  }

  // Fallback: LIKE search
  const like = "%" + escapeLike(query) + "%"
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, content_json as contentJson, plain_text as plainText,
            tags, is_favorite as isFavorite, created_at as createdAt, updated_at as updatedAt
     FROM notes WHERE title LIKE ? ESCAPE '\\' OR content LIKE ? ESCAPE '\\'
     ORDER BY updated_at DESC`,
    [like, like]
  )
  return rows.map(r => ({ ...r, tags: safeJsonParse(r.tags, []), isFavorite: !!r.isFavorite, plainText: r.plainText || "" }))
}

export async function getFavoriteNotes(): Promise<NoteItem[]> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, content_json as contentJson, plain_text as plainText,
            tags, is_favorite as isFavorite, created_at as createdAt, updated_at as updatedAt
     FROM notes WHERE is_favorite = 1 ORDER BY updated_at DESC`
  )
  return rows.map(r => ({ ...r, tags: safeJsonParse(r.tags, []), isFavorite: !!r.isFavorite, plainText: r.plainText || '' }))
}

// ── Note Versions ─────────────────────────────────────────────

export async function saveNoteVersion(noteId: string, content: string) {
  const d = await getDb()
  const id = crypto.randomUUID()
  const now = new Date().toISOString()
  await d.execute(
    'INSERT INTO note_versions (id, note_id, content, saved_at) VALUES (?, ?, ?, ?)',
    [id, noteId, content, now]
  )
  // Keep only last 20 versions per note
  await d.execute(
    `DELETE FROM note_versions WHERE note_id = ? AND id NOT IN (
      SELECT id FROM note_versions WHERE note_id = ? ORDER BY saved_at DESC LIMIT 20
    )`, [noteId, noteId]
  )
}

export async function loadNoteVersions(noteId: string): Promise<NoteVersion[]> {
  const d = await getDb()
  return await d.select<NoteVersion[]>(
    `SELECT id, note_id as noteId, content, saved_at as savedAt
     FROM note_versions WHERE note_id = ? ORDER BY saved_at DESC`, [noteId]
  )
}

export async function deleteNoteVersion(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM note_versions WHERE id = ?', [id])
}

// ── Note Links (bi-directional) ───────────────────────────────

export async function addNoteLink(sourceNoteId: string, targetNoteId: string) {
  const d = await getDb()
  // Avoid duplicates
  const existing = await d.select<any[]>(
    'SELECT id FROM note_links WHERE source_note_id = ? AND target_note_id = ?',
    [sourceNoteId, targetNoteId]
  )
  if (existing.length > 0) return
  const id = crypto.randomUUID()
  await d.execute(
    'INSERT INTO note_links (id, source_note_id, target_note_id, created_at) VALUES (?, ?, ?, ?)',
    [id, sourceNoteId, targetNoteId, new Date().toISOString()]
  )
}

export async function removeNoteLink(sourceNoteId: string, targetNoteId: string) {
  const d = await getDb()
  await d.execute(
    'DELETE FROM note_links WHERE source_note_id = ? AND target_note_id = ?',
    [sourceNoteId, targetNoteId]
  )
}

export async function getNoteLinks(noteId: string): Promise<{ linkedNoteIds: string[]; backlinkNoteIds: string[] }> {
  const d = await getDb()
  const outgoing = await d.select<{ target_note_id: string }[]>(
    'SELECT target_note_id FROM note_links WHERE source_note_id = ?', [noteId]
  )
  const incoming = await d.select<{ source_note_id: string }[]>(
    'SELECT source_note_id FROM note_links WHERE target_note_id = ?', [noteId]
  )
  return {
    linkedNoteIds: outgoing.map(r => r.target_note_id),
    backlinkNoteIds: incoming.map(r => r.source_note_id),
  }
}

// ── Auto Cases (Automation) ──────────────────────────────────────

export async function listAutoCases(): Promise<AutoCase[]> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    'SELECT * FROM auto_cases ORDER BY updated_at DESC'
  )
  return rows.map(r => ({ ...r, tags: safeJsonParse(r.tags, []) }))
}

export async function loadAutoCase(id: string): Promise<AutoCase | null> {
  const d = await getDb()
  const rows = await d.select<any[]>('SELECT * FROM auto_cases WHERE id = ?', [id])
  if (rows.length === 0) return null
  const r = rows[0]
  return { ...r, tags: safeJsonParse(r.tags, []) }
}

export async function saveAutoCase(c: {
  id: string
  name: string
  file_key: string
  module?: string
  tags?: string[]
  priority?: string
  author?: string
  description?: string
  yaml_content: string
  version?: string
}) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO auto_cases (id, name, file_key, module, tags, priority, author, description, yaml_content, version, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name, file_key = excluded.file_key, module = excluded.module, tags = excluded.tags,
       priority = excluded.priority, author = excluded.author, description = excluded.description,
       yaml_content = excluded.yaml_content, version = excluded.version, updated_at = excluded.updated_at`,
    [c.id, c.name, c.file_key, c.module || '', JSON.stringify(c.tags || []), c.priority || 'P2',
     c.author || '', c.description || '', c.yaml_content, c.version || '1.0', now, now]
  )
}

export async function deleteAutoCase(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM auto_case_versions WHERE case_id = ?', [id])
  await d.execute('DELETE FROM auto_cases WHERE id = ?', [id])
}

// ── Auto Case Versions ─────────────────────────────────────────

export async function saveAutoCaseVersion(caseId: string, version: string, yamlContent: string, savedBy = '') {
  const d = await getDb()
  const id = crypto.randomUUID()
  await d.execute(
    'INSERT INTO auto_case_versions (id, case_id, version, yaml_content, saved_by, saved_at) VALUES (?, ?, ?, ?, ?, ?)',
    [id, caseId, version, yamlContent, savedBy, new Date().toISOString()]
  )
  await d.execute(
    `DELETE FROM auto_case_versions WHERE case_id = ? AND id NOT IN (
      SELECT id FROM auto_case_versions WHERE case_id = ? ORDER BY saved_at DESC LIMIT 20
    )`, [caseId, caseId]
  )
}

export async function loadAutoCaseVersions(caseId: string): Promise<AutoCaseVersion[]> {
  const d = await getDb()
  return await d.select<any[]>(
    'SELECT id, case_id as caseId, version, yaml_content as yamlContent, saved_by as savedBy, saved_at as savedAt FROM auto_case_versions WHERE case_id = ? ORDER BY saved_at DESC',
    [caseId]
  )
}

// ── Auto Run Records ───────────────────────────────────────────

export async function saveAutoRunRecord(r: {
  id: string
  trigger?: string
  deviceSerial?: string
  deviceInfo?: string
  suiteConfig?: string
  status?: string
  total?: number
  passed?: number
  failed?: number
  healed?: number
  skipped?: number
  durationMs?: number
  reportPath?: string
  startedAt: string
  endedAt?: string | null
}) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO auto_run_records (id, trigger, device_serial, device_info, suite_config, status, total, passed, failed, healed, skipped, duration_ms, report_path, started_at, ended_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       status = excluded.status, total = excluded.total, passed = excluded.passed,
       failed = excluded.failed, healed = excluded.healed, skipped = excluded.skipped,
       duration_ms = excluded.duration_ms, report_path = excluded.report_path, ended_at = excluded.ended_at`,
    [r.id, r.trigger || 'manual', r.deviceSerial || '', r.deviceInfo || '{}', r.suiteConfig || '{}',
     r.status || 'running', r.total || 0, r.passed || 0, r.failed || 0, r.healed || 0, r.skipped || 0,
     r.durationMs || 0, r.reportPath || '', r.startedAt, r.endedAt || null]
  )
}

export async function listAutoRunRecords(limit = 50): Promise<AutoRunRecord[]> {
  const d = await getDb()
  return await d.select<any[]>(
    `SELECT id, trigger, device_serial as deviceSerial, device_info as deviceInfo, suite_config as suiteConfig,
            status, total, passed, failed, healed, skipped, duration_ms as durationMs,
            report_path as reportPath, started_at as startedAt, ended_at
     FROM auto_run_records ORDER BY started_at DESC LIMIT ?`,
    [limit]
  )
}

export async function loadAutoRunRecord(id: string): Promise<AutoRunRecord | null> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, trigger, device_serial as deviceSerial, device_info as deviceInfo, suite_config as suiteConfig,
            status, total, passed, failed, healed, skipped, duration_ms as durationMs,
            report_path as reportPath, started_at as startedAt, ended_at
     FROM auto_run_records WHERE id = ?`, [id]
  )
  return rows.length > 0 ? rows[0] : null
}

export async function deleteAutoRunRecord(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM auto_run_steps WHERE run_id = ?', [id])
  await d.execute('DELETE FROM auto_run_records WHERE id = ?', [id])
}

// ── Auto Run Steps ─────────────────────────────────────────────

export async function saveAutoRunStep(s: {
  id: string
  runId: string
  caseId: string
  stepId: string
  stepDesc?: string
  status: string
  durationMs?: number
  errorMessage?: string | null
  healLog?: string | null
  screenshotBefore?: string | null
  screenshotAfter?: string | null
  screenshotRef?: string | null
  locatorUsed?: string | null
}) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO auto_run_steps (id, run_id, case_id, step_id, step_desc, status, duration_ms, error_message, heal_log, screenshot_before, screenshot_after, screenshot_ref, locator_used, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET status = excluded.status, duration_ms = excluded.duration_ms, error_message = excluded.error_message, heal_log = excluded.heal_log`,
    [s.id, s.runId, s.caseId, s.stepId, s.stepDesc || '', s.status, s.durationMs || 0,
     s.errorMessage || null, s.healLog || null, s.screenshotBefore || null, s.screenshotAfter || null,
     s.screenshotRef || null, s.locatorUsed || null, new Date().toISOString()]
  )
}

export async function listAutoRunSteps(runId: string): Promise<AutoRunStep[]> {
  const d = await getDb()
  return await d.select<any[]>(
    `SELECT id, run_id as runId, case_id as caseId, step_id as stepId, step_desc as stepDesc,
            status, duration_ms as durationMs, error_message as errorMessage, heal_log as healLog,
            screenshot_before as screenshotBefore, screenshot_after as screenshotAfter,
            screenshot_ref as screenshotRef, locator_used as locatorUsed, created_at as createdAt
     FROM auto_run_steps WHERE run_id = ? ORDER BY created_at ASC`, [runId]
  )
}

// ── State Graphs ───────────────────────────────────────────────

export async function saveAutoStateGraph(g: {
  id: string
  appPackage: string
  appVersion?: string
  deviceInfo?: string
  graphJson: string
  nodeCount?: number
  edgeCount?: number
  exploreDurationMs?: number
}) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO auto_state_graphs (id, app_package, app_version, device_info, graph_json, node_count, edge_count, explore_duration_ms, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET graph_json = excluded.graph_json, node_count = excluded.node_count, edge_count = excluded.edge_count`,
    [g.id, g.appPackage, g.appVersion || '', g.deviceInfo || '{}', g.graphJson,
     g.nodeCount || 0, g.edgeCount || 0, g.exploreDurationMs || 0, new Date().toISOString()]
  )
}

export async function listAutoStateGraphs(appPackage?: string): Promise<AutoStateGraph[]> {
  const d = await getDb()
  if (appPackage) {
    return await d.select<any[]>(
      `SELECT id, app_package as appPackage, app_version as appVersion, device_info as deviceInfo,
              graph_json as graphJson, node_count as nodeCount, edge_count as edgeCount,
              explore_duration_ms as exploreDurationMs, created_at as createdAt
       FROM auto_state_graphs WHERE app_package = ? ORDER BY created_at DESC`, [appPackage]
    )
  }
  return await d.select<any[]>(
    `SELECT id, app_package as appPackage, app_version as appVersion, device_info as deviceInfo,
            graph_json as graphJson, node_count as nodeCount, edge_count as edgeCount,
            explore_duration_ms as exploreDurationMs, created_at as createdAt
     FROM auto_state_graphs ORDER BY created_at DESC`
  )
}

// ── Export / Import ──────────────────────────────────────────

// ── Scripts ────────────────────────────────────────────────────

export interface ScriptItem {
  id: string
  name: string
  type: string
  content: string
  createdAt: string
  updatedAt: string
  sortOrder?: number
}

export async function saveScript(script: { id: string; name: string; type: string; content: string; sortOrder?: number }) {
  const d = await getDb()
  const now = new Date().toISOString()
  if (script.sortOrder !== undefined) {
    await d.execute(
      `INSERT INTO scripts (id, name, type, content, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(id) DO UPDATE SET name = excluded.name, type = excluded.type, content = excluded.content, sort_order = excluded.sort_order, updated_at = excluded.updated_at`,
      [script.id, script.name, script.type, script.content, script.sortOrder, now, now]
    )
  } else {
    await d.execute(
      `INSERT INTO scripts (id, name, type, content, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(sort_order), 0) + 1 FROM scripts WHERE type = ?), ?, ?)
       ON CONFLICT(id) DO UPDATE SET name = excluded.name, type = excluded.type, content = excluded.content, updated_at = excluded.updated_at`,
      [script.id, script.name, script.type, script.content, script.type, now, now]
    )
  }
}

export async function loadScript(id: string): Promise<ScriptItem | null> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, name, type, content, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM scripts WHERE id = ?`,
    [id]
  )
  return rows.length > 0 ? rows[0] : null
}

export async function listScripts(): Promise<ScriptItem[]> {
  const d = await getDb()
  return await d.select<any[]>(
    `SELECT id, name, type, content, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM scripts ORDER BY sort_order ASC, updated_at DESC`
  )
}

/**
 * Persist a new sort order for a list of script IDs.
 * Each entry is [id, newSortOrder].
 */
export async function updateScriptSortOrders(items: { id: string; sortOrder: number }[]) {
  const d = await getDb()
  for (const item of items) {
    await d.execute(`UPDATE scripts SET sort_order = ? WHERE id = ?`, [item.sortOrder, item.id])
  }
}

export async function deleteScript(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM scripts WHERE id = ?', [id])
}

// ── AI Memories ────────────────────────────────────────────

export interface AiMemory {
  id: string
  content: string
  createdAt: string
  updatedAt: string
}

export async function saveAiMemory(content: string): Promise<AiMemory> {
  const d = await getDb()
  const id = crypto.randomUUID()
  const now = new Date().toISOString()
  await d.execute(
    'INSERT INTO note_ai_memories (id, content, created_at, updated_at) VALUES (?, ?, ?, ?)',
    [id, content.trim(), now, now]
  )
  return { id, content: content.trim(), createdAt: now, updatedAt: now }
}

export async function loadAiMemories(): Promise<AiMemory[]> {
  const d = await getDb()
  return await d.select<AiMemory[]>(
    'SELECT id, content, created_at as createdAt, updated_at as updatedAt FROM note_ai_memories ORDER BY created_at DESC'
  )
}

export async function deleteAiMemory(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM note_ai_memories WHERE id = ?', [id])
}

export async function clearAiMemories() {
  const d = await getDb()
  await d.execute('DELETE FROM note_ai_memories')
}

export async function saveProxyRules(rules: ApiRewriteRule[]) {
  const d = await getDb()
  await d.execute(
    'INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)',
    ['proxy_rules', JSON.stringify(rules)]
  )
}

export async function loadProxyRules(): Promise<ApiRewriteRule[]> {
  const d = await getDb()
  const rows = await d.select<{ value: string }[]>(
    "SELECT value FROM app_settings WHERE key = 'proxy_rules'"
  )
  return rows.length > 0 ? safeJsonParse<ApiRewriteRule[]>(rows[0].value, []) : []
}

export interface AppBackup {
  version: string
  exportedAt: string
  fieldRuleSets: any[]
  caseFiles: any[]
  recentFiles: string[]
  favorites: string[]
  settings: Record<string, string>
  inputHistory: InputHistoryEntry[]
  logSessions: LogSession[]
  noteSpaces: NoteSpace[]
  noteFolders: NoteFolder[]
  notes: NoteItem[]
  noteVersions: NoteVersion[]
  noteLinks: NoteLink[]
  scripts: ScriptItem[]
  aiMemories: AiMemory[]
  proxyRules?: ApiRewriteRule[]
  autoCases?: AutoCase[]
  autoCaseVersions?: AutoCaseVersion[]
  autoRunRecords?: AutoRunRecord[]
  autoRunSteps?: AutoRunStep[]
  autoStateGraphs?: AutoStateGraph[]
}

function _yieldToMain(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0));
}

export async function exportAllData(): Promise<AppBackup> {
  const fieldRuleSets = await loadFieldRuleSets()
  const caseFiles = await loadCaseFiles()
  await _yieldToMain()
  const recentFiles = await getRecentFiles()
  const favPaths = await getFavorites()
  const settings = await loadSettings()
  await _yieldToMain()
  const d = await getDb()
  const inputHistory = await d.select<InputHistoryEntry[]>(
    'SELECT id, key_name as keyName, value, created_at as createdAt FROM input_history ORDER BY sort_order DESC'
  )
  await _yieldToMain()
  const logSessions = await d.select<LogSession[]>(
    'SELECT id, type, device_serial as deviceSerial, status, started_at as startedAt, metadata FROM log_sessions ORDER BY started_at DESC'
  )
  await _yieldToMain()
  const noteSpaces = await d.select<any[]>('SELECT id, name, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM note_spaces')
  const noteFolders = await loadNoteFolders()
  await _yieldToMain()
  const notes = await loadNotes()
  const noteVersions = await d.select<NoteVersion[]>(
    'SELECT id, note_id as noteId, content, saved_at as savedAt FROM note_versions ORDER BY saved_at ASC'
  )
  await _yieldToMain()
  const noteLinks = await d.select<NoteLink[]>(
    'SELECT id, source_note_id as sourceNoteId, target_note_id as targetNoteId, created_at as createdAt FROM note_links'
  )
  const scripts = await listScripts()
  await _yieldToMain()
  const aiMemories = await d.select<AiMemory[]>(
    'SELECT id, content, created_at as createdAt, updated_at as updatedAt FROM note_ai_memories'
  )
  const proxyRules = await loadProxyRules()
  await _yieldToMain()
  const autoCases = await listAutoCases()
  const autoRunRecords = await listAutoRunRecords()
  return {
    version: '1.8',
    exportedAt: new Date().toISOString(),
    fieldRuleSets,
    caseFiles,
    recentFiles,
    favorites: favPaths,
    settings,
    inputHistory,
    logSessions,
    noteSpaces,
    noteFolders,
    notes,
    noteVersions,
    noteLinks,
    scripts,
    aiMemories,
    proxyRules: proxyRules.length > 0 ? proxyRules : undefined,
    autoCases: autoCases.length > 0 ? autoCases : undefined,
    autoCaseVersions: undefined,
    autoRunRecords: autoRunRecords.length > 0 ? autoRunRecords : undefined,
    autoRunSteps: undefined,
    autoStateGraphs: undefined,
  }
}

function validateBackup(backup: any): string | null {
  if (!backup || typeof backup !== 'object') return '备份数据格式无效'
  if (!backup.version) return '备份文件缺少版本号，可能是旧格式或损坏文件'
  const tables = ['fieldRuleSets', 'caseFiles', 'recentFiles', 'favorites', 'settings', 'inputHistory', 'logSessions', 'noteSpaces', 'noteFolders', 'notes', 'noteVersions', 'noteLinks', 'scripts', 'aiMemories', 'autoCases', 'autoRunRecords']
  for (const t of tables) {
    if (backup[t] !== undefined && !Array.isArray(backup[t]) && typeof backup[t] !== 'object') {
      return `字段 "${t}" 类型无效`
    }
  }
  return null
}

/**
 * Incremental restore — used exclusively by cloud restore.
 *
 * Contract: DO NOT delete any existing local data. For every user-facing named entity in the
 * backup, look up whether an item with the same name already exists locally.
 * - If it exists locally → skip the backup item entirely (keep local as-is).
 * - If it doesn't exist locally → insert the backup item (using backup's original ID).
 *
 * Reference-heavy tables (note_versions, note_links) are only imported for notes that were
 * newly inserted; skipped notes keep their existing local version history and links intact.
 *
 * Preference/session tables (app_settings, input_history, log_sessions, recent_files,
 * favorites, proxy_rules) are NEVER touched here — cloud restore should not overwrite the
 * user's local settings or session state.
 *
 * Returns per-category counts so the caller can present a summary to the user.
 */
export async function importAllDataIncremental(backup: AppBackup): Promise<{
  imported: number
  skipped: number
  failures: string[]
}> {
  const err = validateBackup(backup)
  if (err) throw new Error(err)
  const d = await getDb()
  const maxRetries = 3
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try { await d.select('SELECT 1'); break }
    catch {
      if (attempt === maxRetries) throw new Error('数据库繁忙，请稍后重试')
      await new Promise(r => setTimeout(r, 1000 * attempt))
    }
  }

  let imported = 0
  let skipped = 0
  const failures: string[] = []

  // ── 1. NOTE SPACES ─ match by name; build backupSpaceId → localSpaceId map ──
  const spaceIdMap: Record<string, string> = {}
  const localSpaces = (await d.select<{ id: string; name: string }[]>(
    'SELECT id, name FROM note_spaces'
  )) || []
  const localSpaceByName = new Map(localSpaces.map(s => [s.name, s.id]))
  for (const s of backup.noteSpaces || []) {
    const existing = localSpaceByName.get(s.name)
    if (existing) { spaceIdMap[s.id] = existing; skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO note_spaces (id, name, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
        [s.id, s.name, s.sortOrder ?? 0, s.createdAt, s.updatedAt]
      )
      spaceIdMap[s.id] = s.id
      imported++
    } catch (e: any) { failures.push(`space "${s.name}": ${e.message || e}`) }
  }

  // ── 2. NOTE FOLDERS ─ match by (remapped space_id, remapped parent_id, name); recursive ──
  const folderIdMap: Record<string, string> = {}
  const processedFolderIds = new Set<string>()
  const backupFoldersById = new Map<string, any>()
  for (const f of backup.noteFolders || []) backupFoldersById.set(f.id, f)

  async function processFolder(f: any): Promise<void> {
    if (processedFolderIds.has(f.id)) return
    processedFolderIds.add(f.id)

    const bkSpaceId = f.spaceId ?? f.space_id ?? null
    const localSpaceId: string | null = bkSpaceId ? (spaceIdMap[bkSpaceId] ?? null) : null
    const bkParentId = f.parentId ?? f.parent_id ?? null
    let localParentId: string | null = null
    if (bkParentId) {
      const parent = backupFoldersById.get(bkParentId)
      if (parent) await processFolder(parent)
      localParentId = folderIdMap[bkParentId] ?? null
    }

    const existing = (await d.select<{ id: string }[]>(
      `SELECT id FROM note_folders
        WHERE IFNULL(space_id, '') = IFNULL(?, '')
          AND IFNULL(parent_id, '') = IFNULL(?, '')
          AND name = ?`,
      [localSpaceId, localParentId, f.name]
    )) || []
    if (existing.length > 0) { folderIdMap[f.id] = existing[0].id; skipped++; return }

    try {
      await d.execute(
        'INSERT INTO note_folders (id, space_id, name, parent_id, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [f.id, localSpaceId, f.name, localParentId, f.sortOrder ?? 0, f.createdAt, f.updatedAt]
      )
      folderIdMap[f.id] = f.id
      imported++
    } catch (e: any) { failures.push(`folder "${f.name}": ${e.message || e}`) }
  }
  for (const f of backup.noteFolders || []) await processFolder(f)

  // ── 3. NOTES ─ match by (remapped folder_id, title). Track newly-inserted note IDs
  //             so version/link imports can be scoped to fresh notes only. ──
  const noteIdMap: Record<string, string> = {}
  const freshlyInsertedNoteIds = new Set<string>()
  for (const rawNote of backup.notes || []) {
    const n: any = rawNote
    const bkFolderId = n.folderId ?? n.folder_id ?? null
    const localFolderId: string | null = bkFolderId ? (folderIdMap[bkFolderId] ?? null) : null

    const existing = (await d.select<{ id: string }[]>(
      `SELECT id FROM notes
        WHERE IFNULL(folder_id, '') = IFNULL(?, '')
          AND title = ?`,
      [localFolderId, n.title ?? '']
    )) || []
    if (existing.length > 0) { noteIdMap[n.id] = existing[0].id; skipped++; continue }

    try {
      await d.execute(
        'INSERT INTO notes (id, folder_id, title, content, content_json, plain_text, tags, is_favorite, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [n.id, localFolderId, n.title ?? '', n.content ?? '', n.contentJson ?? null, n.plainText ?? n.plain_text ?? '', JSON.stringify(n.tags ?? []), n.isFavorite ? 1 : 0, n.createdAt, n.updatedAt]
      )
      noteIdMap[n.id] = n.id
      freshlyInsertedNoteIds.add(n.id)
      imported++
    } catch (e: any) { failures.push(`note "${n.title}": ${e.message || e}`) }
  }

  // ── 4. NOTE VERSIONS ─ only import for freshly-inserted notes (skipped notes keep local history) ──
  for (const rawV of backup.noteVersions || []) {
    const v: any = rawV
    const bkNoteId = v.noteId ?? v.note_id
    if (!freshlyInsertedNoteIds.has(bkNoteId)) continue
    try {
      await d.execute(
        'INSERT INTO note_versions (id, note_id, content, saved_at) VALUES (?, ?, ?, ?)',
        [v.id, bkNoteId, v.content, v.savedAt ?? v.saved_at]
      )
      imported++
    } catch { /* silently ignore individual version failures */ }
  }

  // ── 5. NOTE LINKS ─ only import if the source note was freshly inserted AND target
  //                   resolves to some local note (either fresh or existing by name) ──
  for (const rawL of backup.noteLinks || []) {
    const l: any = rawL
    const src = l.sourceNoteId ?? l.source_note_id
    const tgt = l.targetNoteId ?? l.target_note_id
    if (!freshlyInsertedNoteIds.has(src)) continue
    const localTgt = noteIdMap[tgt]
    if (!localTgt) continue
    try {
      await d.execute(
        'INSERT INTO note_links (id, source_note_id, target_note_id, created_at) VALUES (?, ?, ?, ?)',
        [l.id, src, localTgt, l.createdAt ?? l.created_at]
      )
      imported++
    } catch { /* ignore */ }
  }

  // ── 6. FIELD RULE SETS ─ match by name ──
  const localRuleSets = (await d.select<{ name: string }[]>(
    'SELECT name FROM field_rule_sets'
  )) || []
  const localRuleNames = new Set(localRuleSets.map(r => r.name))
  for (const r of backup.fieldRuleSets || []) {
    if (localRuleNames.has(r.name)) { skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO field_rule_sets (id, name, rules, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
        [r.id, r.name, JSON.stringify(r.rules), r.createdAt || r.created_at, r.updatedAt || r.updated_at || r.createdAt]
      )
      imported++
    } catch (e: any) { failures.push(`ruleset "${r.name}": ${e.message || e}`) }
  }

  // ── 7. CASE FILES ─ match by name ──
  const localCaseFiles = (await d.select<{ name: string }[]>(
    'SELECT name FROM case_files'
  )) || []
  const localCaseNames = new Set(localCaseFiles.map(f => f.name))
  for (const f of backup.caseFiles || []) {
    if (localCaseNames.has(f.name)) { skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO case_files (id, name, data, tags, custom_fields, rule_set_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        [f.id, f.name, f.data || JSON.stringify(f), JSON.stringify(f.tags || []), JSON.stringify(f.custom_fields || f.customFields || []), f.rule_set_id || f.ruleSetId || '', f.created_at || f.createdAt, f.updated_at || f.updatedAt]
      )
      imported++
    } catch (e: any) { failures.push(`case file "${f.name}": ${e.message || e}`) }
  }

  // ── 8. SCRIPTS ─ match by (type, name); scripts of same name in different types coexist ──
  const localScripts = (await d.select<{ type: string; name: string }[]>(
    'SELECT type, name FROM scripts'
  )) || []
  const localScriptKeys = new Set(localScripts.map(s => `${s.type}::${s.name}`))
  for (const rawS of backup.scripts || []) {
    const s: any = rawS
    const key = `${s.type ?? 'bat'}::${s.name}`
    if (localScriptKeys.has(key)) { skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO scripts (id, name, type, content, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [s.id, s.name, s.type ?? 'bat', s.content ?? '', s.sortOrder ?? s.sort_order ?? 0, s.createdAt ?? s.created_at, s.updatedAt ?? s.updated_at ?? s.createdAt]
      )
      imported++
    } catch (e: any) { failures.push(`script "${s.name}": ${e.message || e}`) }
  }

  // ── 9. AI MEMORIES ─ dedup by content (already the identity for user-visible memories) ──
  const localMems = (await d.select<{ content: string }[]>(
    'SELECT content FROM note_ai_memories'
  )) || []
  const localMemContents = new Set(localMems.map(m => m.content))
  for (const rawM of backup.aiMemories || []) {
    const m: any = rawM
    if (localMemContents.has(m.content)) { skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO note_ai_memories (id, content, created_at, updated_at) VALUES (?, ?, ?, ?)',
        [m.id, m.content, m.createdAt ?? m.created_at, m.updatedAt ?? m.updated_at ?? m.createdAt]
      )
      imported++
    } catch (e: any) { failures.push(`memory: ${e.message || e}`) }
  }

  // ── 10. AUTO CASES ─ match by file_key ──
  const localAutoCases = (await d.select<{ file_key: string }[]>(
    'SELECT file_key FROM auto_cases'
  )) || []
  const localAutoKeys = new Set(localAutoCases.map(c => c.file_key))
  for (const rawC of backup.autoCases || []) {
    const c: any = rawC
    if (localAutoKeys.has(c.file_key)) { skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO auto_cases (id, name, file_key, tags, priority, author, description, yaml_content, version, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
        [c.id, c.name, c.file_key, JSON.stringify(c.tags ?? []), c.priority || 'P2', c.author || '', c.description || '', c.yaml_content, c.version || '1.0', c.created_at ?? c.createdAt, c.updated_at ?? c.updatedAt]
      )
      imported++
    } catch (e: any) { failures.push(`auto case "${c.name}": ${e.message || e}`) }
  }

  // NOTE: app_settings, input_history, log_sessions, recent_files, favorites, proxy_rules
  // are intentionally NOT touched. Cloud restore preserves local preferences/state.

  // Reset plain_text repair flag so the next loadNoteList() call will re-scan any
  // newly imported notes whose plain_text may have been empty in the backup.
  _plainTextRepaired = false
  try {
    await d.execute(`DELETE FROM app_settings WHERE key = 'plain_text_repaired'`)
  } catch {}

  if (failures.length > 0) console.warn('[importAllDataIncremental] failures:', failures)
  return { imported, skipped, failures }
}

export async function importAllData(backup: AppBackup) {
  const err = validateBackup(backup)
  if (err) throw new Error(err)
  const d = await getDb()
  const maxRetries = 3
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      await d.select('SELECT 1')
      break
    } catch {
      if (attempt === maxRetries) throw new Error('数据库繁忙，请稍后重试')
      await new Promise(r => setTimeout(r, 1000 * attempt))
    }
  }
  const failures: string[] = []
  const deletes = [
    'field_rule_sets', 'case_files', 'recent_files', 'favorites',
    'app_settings', 'input_history', 'log_sessions',
    'note_folders', 'notes', 'notes_fts', 'note_versions', 'note_links', 'scripts', 'note_ai_memories',
    'auto_cases', 'auto_case_versions', 'auto_run_records', 'auto_run_steps', 'auto_state_graphs'
  ]
  for (const table of deletes) {
    try { await d.execute(`DELETE FROM ${table}`) } catch (e: any) { failures.push(`DELETE ${table}: ${e}`) }
  }
  try { await d.execute('DELETE FROM note_spaces') } catch {}
  const inserts: [string, string, any[], (item: any) => unknown[]][] = [
    ['field_rule_sets', 'id, name, rules, created_at, updated_at', backup.fieldRuleSets || [], s => [s.id, s.name, JSON.stringify(s.rules), s.createdAt || s.created_at, s.updatedAt || s.updated_at || s.createdAt]],
    ['case_files', 'id, name, data, tags, custom_fields, rule_set_id, created_at, updated_at', backup.caseFiles || [], f => [f.id, f.name, f.data || JSON.stringify(f), JSON.stringify(f.tags || []), JSON.stringify(f.custom_fields || f.customFields || []), f.rule_set_id || f.ruleSetId || '', f.created_at || f.createdAt, f.updated_at || f.updatedAt]],
    ['recent_files', 'path, name, case_count, last_opened', backup.recentFiles || [], r => [r.path, r.name, r.case_count || r.caseCount || 0, r.last_opened || r.lastOpened]],
    ['favorites', 'path, added_at', backup.favorites || [], path => [path, new Date().toISOString()]],
    ['input_history', 'key_name, value, created_at, sort_order', backup.inputHistory || [], h => [h.keyName, h.value, h.createdAt, Date.parse(h.createdAt)]],
    ['log_sessions', 'id, type, device_serial, status, started_at, metadata', backup.logSessions || [], s => [s.id, s.type, s.deviceSerial, s.status, s.startedAt, s.metadata]],
    ['note_spaces', 'id, name, sort_order, created_at, updated_at', backup.noteSpaces || [], (s: any) => [s.id, s.name, s.sortOrder ?? s.sort_order ?? 0, s.createdAt ?? s.created_at, s.updatedAt ?? s.updated_at]],
    ['note_folders', 'id, space_id, name, parent_id, sort_order, created_at, updated_at', backup.noteFolders || [], (f: any) => [f.id, f.spaceId ?? f.space_id ?? null, f.name, f.parentId ?? f.parent_id ?? null, f.sortOrder ?? f.sort_order ?? 0, f.createdAt ?? f.created_at, f.updatedAt ?? f.updated_at]],
    ['notes', 'id, folder_id, title, content, content_json, plain_text, tags, is_favorite, created_at, updated_at', backup.notes || [], (n: any) => [n.id, n.folderId ?? n.folder_id ?? null, n.title ?? '', n.content ?? '', n.contentJson ?? n.content_json ?? null, n.plainText ?? n.plain_text ?? '', JSON.stringify(n.tags ?? []), n.isFavorite ? 1 : 0, n.createdAt ?? n.created_at, n.updatedAt ?? n.updated_at]],
    ['note_versions', 'id, note_id, content, saved_at', backup.noteVersions || [], (v: any) => [v.id, v.noteId ?? v.note_id, v.content, v.savedAt ?? v.saved_at]],
    ['note_links', 'id, source_note_id, target_note_id, created_at', backup.noteLinks || [], (l: any) => [l.id, l.sourceNoteId ?? l.source_note_id, l.targetNoteId ?? l.target_note_id, l.createdAt ?? l.created_at]],
    ['scripts', 'id, name, type, content, sort_order, created_at, updated_at', backup.scripts || [], (s: any) => [s.id, s.name, s.type ?? 'bat', s.content ?? '', s.sortOrder ?? s.sort_order ?? 0, s.createdAt ?? s.created_at, s.updatedAt ?? s.updated_at ?? s.createdAt]],
    ['note_ai_memories', 'id, content, created_at, updated_at', backup.aiMemories || [], (m: any) => [m.id, m.content, m.createdAt ?? m.created_at, m.updatedAt ?? m.updated_at ?? m.createdAt]],
    ['auto_cases', 'id, name, file_key, tags, priority, author, description, yaml_content, version, created_at, updated_at', backup.autoCases || [], (c: any) => [c.id, c.name, c.file_key, JSON.stringify(c.tags ?? []), c.priority || 'P2', c.author || '', c.description || '', c.yaml_content, c.version || '1.0', c.created_at ?? c.createdAt, c.updated_at ?? c.updatedAt]],
    ['auto_run_records', 'id, trigger, device_serial, device_info, suite_config, status, total, passed, failed, healed, skipped, duration_ms, report_path, started_at, ended_at', backup.autoRunRecords || [], (r: any) => [r.id, r.trigger || 'manual', r.deviceSerial ?? r.device_serial ?? '', r.deviceInfo ?? r.device_info ?? '{}', r.suiteConfig ?? r.suite_config ?? '{}', r.status || 'running', r.total || 0, r.passed || 0, r.failed || 0, r.healed || 0, r.skipped || 0, r.durationMs ?? r.duration_ms ?? 0, r.reportPath ?? r.report_path ?? '', r.startedAt ?? r.started_at, r.endedAt ?? r.ended_at ?? null]],
  ]
  for (const [table, cols, items, toParams] of inserts) {
    if (!Array.isArray(items) || items.length === 0) continue
    for (const item of items) {
      try {
        const params = toParams(item)
        await d.execute(`INSERT INTO ${table} (${cols}) VALUES (${params.map(() => '?').join(',')})`, params)
      } catch (e: any) {
        failures.push(`INSERT ${table}: ${e.message || e}`)
      }
    }
  }
  for (const [key, value] of Object.entries(backup.settings || {})) {
    try {
      await d.execute('INSERT INTO app_settings (key, value) VALUES (?, ?)', [key, value])
    } catch (e: any) {
      failures.push(`INSERT app_settings(${key}): ${e.message || e}`)
    }
  }
  // Restore proxy rules
  if (backup.proxyRules && backup.proxyRules.length > 0) {
    try {
      await d.execute(
        'INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)',
        ['proxy_rules', JSON.stringify(backup.proxyRules)]
      )
    } catch (e: any) {
      failures.push(`INSERT proxy_rules: ${e.message || e}`)
    }
  }
  if (failures.length > 0) {
    console.warn('[importAllData] failures:', failures)
    throw new Error(`导入部分失败 (${failures.length}项): ${failures[0]}`)
  }
  // Reset plain_text repair flag so the next loadNoteList() re-scans any
  // notes whose plain_text was empty in the backup file.
  _plainTextRepaired = false
  try {
    await d.execute(`DELETE FROM app_settings WHERE key = 'plain_text_repaired'`)
  } catch {}
}
