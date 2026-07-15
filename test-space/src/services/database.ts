import type Database from '@tauri-apps/plugin-sql'
import DOMPurify from 'dompurify'
import type { InputHistoryEntry, LogSession, NoteSpace, NoteFolder, NoteItem, NoteVersion, NoteLink, ApiTestCase, ApiTestGroup, ApiTestReport, ApiTestResult } from '@/types'
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

  // ── API Test Cases ──────────────────────────────────────────
  await d.execute(`CREATE TABLE IF NOT EXISTS api_test_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    color TEXT NOT NULL DEFAULT '#6366f1',
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS api_test_cases (
    id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    type TEXT NOT NULL DEFAULT 'positive',
    method TEXT NOT NULL,
    url TEXT NOT NULL,
    host TEXT NOT NULL DEFAULT '',
    path TEXT NOT NULL DEFAULT '',
    query TEXT,
    headers TEXT NOT NULL DEFAULT '[]',
    body TEXT,
    body_is_base64 INTEGER NOT NULL DEFAULT 0,
    assertions TEXT NOT NULL DEFAULT '[]',
    source_request_id TEXT,
    enabled INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS api_test_reports (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    total_cases INTEGER NOT NULL DEFAULT 0,
    passed_cases INTEGER NOT NULL DEFAULT 0,
    failed_cases INTEGER NOT NULL DEFAULT 0,
    total_duration REAL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    created_at TEXT NOT NULL
  )`)
  await d.execute(`CREATE TABLE IF NOT EXISTS api_test_results (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    report_id TEXT NOT NULL,
    passed INTEGER NOT NULL DEFAULT 0,
    status_code INTEGER,
    response_body TEXT,
    response_headers TEXT,
    duration REAL,
    error_message TEXT,
    assertion_results TEXT NOT NULL DEFAULT '[]',
    started_at TEXT NOT NULL,
    completed_at TEXT
  )`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_api_test_cases_group ON api_test_cases(group_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_api_test_results_report ON api_test_results(report_id)`)
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
  apiTestGroups?: ApiTestGroup[]
  apiTestCases?: ApiTestCase[]
  apiTestReports?: ApiTestReport[]
  apiTestResults?: ApiTestResult[]
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
  const apiTestGroups = await loadApiTestGroups()
  await _yieldToMain()
  const apiTestCases = await loadApiTestCases()
  await _yieldToMain()
  const apiTestReports = await d.select<any[]>(
    `SELECT id, name, description, total_cases as totalCases, passed_cases as passedCases,
            failed_cases as failedCases, total_duration as totalDuration,
            started_at as startedAt, completed_at as completedAt,
            status, created_at as createdAt
     FROM api_test_reports ORDER BY created_at DESC`
  )
  await _yieldToMain()
  const apiTestResults = await d.select<any[]>(
    `SELECT id, report_id as reportId, case_id as caseId, passed,
            status_code as statusCode, response_body as responseBody,
            response_headers as responseHeaders, duration,
            error_message as errorMessage, assertion_results as assertionResults,
            started_at as startedAt, completed_at as completedAt
     FROM api_test_results`
  )
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
    apiTestGroups: apiTestGroups.length > 0 ? apiTestGroups : undefined,
    apiTestCases: apiTestCases.length > 0 ? apiTestCases : undefined,
    apiTestReports: apiTestReports.length > 0 ? apiTestReports : undefined,
    apiTestResults: apiTestResults.length > 0 ? apiTestResults : undefined,
  }
}

function validateBackup(backup: any): string | null {
  if (!backup || typeof backup !== 'object') return '备份数据格式无效'
  if (!backup.version) return '备份文件缺少版本号，可能是旧格式或损坏文件'
  const tables = ['fieldRuleSets', 'caseFiles', 'recentFiles', 'favorites', 'settings', 'inputHistory', 'logSessions', 'noteSpaces', 'noteFolders', 'notes', 'noteVersions', 'noteLinks', 'scripts', 'aiMemories', 'apiTestGroups', 'apiTestCases', 'apiTestReports', 'apiTestResults']
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

  // ── 10. API TEST GROUPS ─ match by name ──
  const localGroups = (await d.select<{ name: string }[]>(
    'SELECT name FROM api_test_groups'
  )) || []
  const localGroupNames = new Set(localGroups.map(g => g.name))
  const groupIdMap: Record<string, string> = {}
  for (const rawG of backup.apiTestGroups || []) {
    const g: any = rawG
    if (localGroupNames.has(g.name)) { skipped++; continue }
    try {
      await d.execute(
        'INSERT INTO api_test_groups (id, name, description, color, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        [g.id, g.name, g.description ?? '', g.color ?? '#6366f1', g.sortOrder ?? g.sort_order ?? 0, g.createdAt ?? g.created_at, g.updatedAt ?? g.updated_at]
      )
      groupIdMap[g.id] = g.id
      imported++
    } catch (e: any) { failures.push(`group "${g.name}": ${e.message || e}`) }
  }

  // ── 11. API TEST CASES ─ match by (group_id, method, path, name); only for newly inserted groups ──
  const localCases = (await d.select<{ group_id: string; method: string; path: string; name: string }[]>(
    'SELECT group_id, method, path, name FROM api_test_cases'
  )) || []
  const localCaseKeys = new Set(localCases.map(c => `${c.group_id}::${c.method}::${c.path}::${c.name}`))
  const caseIdMap: Record<string, string> = {}
  const freshlyInsertedCaseIds = new Set<string>()
  for (const rawC of backup.apiTestCases || []) {
    const c: any = rawC
    const bkGroupId = c.groupId ?? c.group_id
    const localGroupId = groupIdMap[bkGroupId] ?? bkGroupId
    const caseKey = `${localGroupId}::${c.method}::${c.path}::${c.name}`
    if (localCaseKeys.has(caseKey)) { skipped++; continue }
    try {
      await d.execute(
        `INSERT INTO api_test_cases (id, group_id, name, description, type, method, url, host, path, query, headers, body, body_is_base64, assertions, source_request_id, enabled, sort_order, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [c.id, localGroupId, c.name, c.description ?? '', c.type, c.method, c.url, c.host ?? '', c.path, c.query ?? null, JSON.stringify(c.headers ?? []), c.body ?? null, c.bodyIsBase64 ? 1 : 0, JSON.stringify(c.assertions ?? []), c.sourceRequestId ?? c.source_request_id ?? null, c.enabled ? 1 : 0, c.sortOrder ?? c.sort_order ?? 0, c.createdAt ?? c.created_at, c.updatedAt ?? c.updated_at]
      )
      caseIdMap[c.id] = c.id
      freshlyInsertedCaseIds.add(c.id)
      imported++
    } catch (e: any) { failures.push(`case "${c.name}": ${e.message || e}`) }
  }

  // ── 12. API TEST REPORTS ─ match by name ──
  const localReports = (await d.select<{ name: string }[]>(
    'SELECT name FROM api_test_reports'
  )) || []
  const localReportNames = new Set(localReports.map(r => r.name))
  const reportIdMap: Record<string, string> = {}
  const freshlyInsertedReportIds = new Set<string>()
  for (const rawR of backup.apiTestReports || []) {
    const r: any = rawR
    if (localReportNames.has(r.name)) { skipped++; continue }
    try {
      await d.execute(
        `INSERT INTO api_test_reports (id, name, description, total_cases, passed_cases, failed_cases, total_duration, started_at, completed_at, status, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [r.id, r.name, r.description ?? '', r.totalCases ?? r.total_cases ?? 0, r.passedCases ?? r.passed_cases ?? 0, r.failedCases ?? r.failed_cases ?? 0, r.totalDuration ?? r.total_duration ?? 0, r.startedAt ?? r.started_at, r.completedAt ?? r.completed_at ?? null, r.status, r.createdAt ?? r.created_at]
      )
      reportIdMap[r.id] = r.id
      freshlyInsertedReportIds.add(r.id)
      imported++
    } catch (e: any) { failures.push(`report "${r.name}": ${e.message || e}`) }
  }

  // ── 13. API TEST RESULTS ─ only for freshly-inserted reports ──
  for (const rawR of backup.apiTestResults || []) {
    const r: any = rawR
    const bkReportId = r.reportId ?? r.report_id
    if (!freshlyInsertedReportIds.has(bkReportId)) continue
    try {
      await d.execute(
        `INSERT INTO api_test_results (id, report_id, case_id, passed, status_code, response_body, response_headers, duration, error_message, assertion_results, started_at, completed_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [r.id, bkReportId, r.caseId ?? r.case_id, r.passed ? 1 : 0, r.statusCode ?? r.status_code ?? null, r.responseBody ?? r.response_body ?? null, r.responseHeaders ?? r.response_headers ? JSON.stringify(r.responseHeaders ?? r.response_headers) : null, r.duration ?? null, r.errorMessage ?? r.error_message ?? null, r.assertionResults ?? r.assertion_results ? JSON.stringify(r.assertionResults ?? r.assertion_results) : null, r.startedAt ?? r.started_at, r.completedAt ?? r.completed_at]
      )
      imported++
    } catch { /* ignore individual result failures */ }
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
    'api_test_groups', 'api_test_cases', 'api_test_reports', 'api_test_results',
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
    ['api_test_groups', 'id, name, description, color, sort_order, created_at, updated_at', backup.apiTestGroups || [], (g: any) => [g.id, g.name, g.description ?? '', g.color ?? '#6366f1', g.sortOrder ?? g.sort_order ?? 0, g.createdAt ?? g.created_at, g.updatedAt ?? g.updated_at]],
    ['api_test_cases', 'id, group_id, name, description, type, method, url, host, path, query, headers, body, body_is_base64, assertions, source_request_id, enabled, sort_order, created_at, updated_at', backup.apiTestCases || [], (c: any) => [c.id, c.groupId ?? c.group_id, c.name, c.description ?? '', c.type, c.method, c.url, c.host ?? '', c.path, c.query ?? null, JSON.stringify(c.headers ?? []), c.body ?? null, c.bodyIsBase64 ? 1 : 0, JSON.stringify(c.assertions ?? []), c.sourceRequestId ?? c.source_request_id ?? null, c.enabled ? 1 : 0, c.sortOrder ?? c.sort_order ?? 0, c.createdAt ?? c.created_at, c.updatedAt ?? c.updated_at]],
    ['api_test_reports', 'id, name, description, total_cases, passed_cases, failed_cases, total_duration, started_at, completed_at, status, created_at', backup.apiTestReports || [], (r: any) => [r.id, r.name, r.description ?? '', r.totalCases ?? r.total_cases ?? 0, r.passedCases ?? r.passed_cases ?? 0, r.failedCases ?? r.failed_cases ?? 0, r.totalDuration ?? r.total_duration ?? 0, r.startedAt ?? r.started_at, r.completedAt ?? r.completed_at ?? null, r.status, r.createdAt ?? r.created_at]],
    ['api_test_results', 'id, report_id, case_id, passed, status_code, response_body, response_headers, duration, error_message, assertion_results, started_at, completed_at', backup.apiTestResults || [], (r: any) => [r.id, r.reportId ?? r.report_id, r.caseId ?? r.case_id, r.passed ? 1 : 0, r.statusCode ?? r.status_code ?? null, r.responseBody ?? r.response_body ?? null, r.responseHeaders ?? r.response_headers ? JSON.stringify(r.responseHeaders ?? r.response_headers) : null, r.duration ?? null, r.errorMessage ?? r.error_message ?? null, r.assertionResults ?? r.assertion_results ? JSON.stringify(r.assertionResults ?? r.assertion_results) : null, r.startedAt ?? r.started_at, r.completedAt ?? r.completed_at]],
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

// ── API Test Groups ──────────────────────────────────────────

export async function loadApiTestGroups(): Promise<ApiTestGroup[]> {
  const d = await getDb()
  return await d.select<ApiTestGroup[]>(
    `SELECT id, name, description, color, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt
     FROM api_test_groups ORDER BY sort_order ASC, created_at ASC`
  )
}

export async function saveApiTestGroup(group: { id: string; name: string; description?: string; color?: string; sortOrder?: number }) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO api_test_groups (id, name, description, color, sort_order, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       name = excluded.name, description = excluded.description,
       color = excluded.color, sort_order = excluded.sort_order, updated_at = excluded.updated_at`,
    [group.id, group.name, group.description || '', group.color || '#6366f1', group.sortOrder || 0, now, now]
  )
}

export async function deleteApiTestGroup(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM api_test_cases WHERE group_id = ?', [id])
  await d.execute('DELETE FROM api_test_groups WHERE id = ?', [id])
}

// ── API Test Cases ────────────────────────────────────────────

function caseRowToCase(row: any): ApiTestCase {
  return {
    ...row,
    headers: safeJsonParse(row.headers, []),
    assertions: safeJsonParse(row.assertions, []),
    bodyIsBase64: !!row.body_is_base64,
    enabled: !!row.enabled,
    query: row.query || null,
    body: row.body || null,
    sourceRequestId: row.source_request_id || null,
    sortOrder: row.sort_order ?? 0,
  }
}

export async function loadApiTestCases(groupId?: string): Promise<ApiTestCase[]> {
  const d = await getDb()
  if (groupId) {
    const rows = await d.select<any[]>(
      `SELECT id, group_id as groupId, name, description, type, method, url, host, path, query,
              headers, body, body_is_base64 as bodyIsBase64, assertions, source_request_id as sourceRequestId,
              enabled, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt
       FROM api_test_cases WHERE group_id = ? ORDER BY sort_order ASC, created_at ASC`,
      [groupId]
    )
    return rows.map(caseRowToCase)
  }
  const rows = await d.select<any[]>(
    `SELECT id, group_id as groupId, name, description, type, method, url, host, path, query,
            headers, body, body_is_base64 as bodyIsBase64, assertions, source_request_id as sourceRequestId,
            enabled, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt
     FROM api_test_cases ORDER BY sort_order ASC, created_at ASC`
  )
  return rows.map(caseRowToCase)
}

export async function saveApiTestCase(testCase: ApiTestCase) {
  const d = await getDb()
  const now = new Date().toISOString()
  await d.execute(
    `INSERT INTO api_test_cases (id, group_id, name, description, type, method, url, host, path, query,
      headers, body, body_is_base64, assertions, source_request_id, enabled, sort_order, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       group_id = excluded.group_id, name = excluded.name, description = excluded.description,
       type = excluded.type, method = excluded.method, url = excluded.url, host = excluded.host,
       path = excluded.path, query = excluded.query, headers = excluded.headers, body = excluded.body,
       body_is_base64 = excluded.body_is_base64, assertions = excluded.assertions,
       source_request_id = excluded.source_request_id, enabled = excluded.enabled,
       sort_order = excluded.sort_order, updated_at = excluded.updated_at`,
    [
      testCase.id, testCase.groupId, testCase.name, testCase.description, testCase.type,
      testCase.method, testCase.url, testCase.host, testCase.path, testCase.query,
      JSON.stringify(testCase.headers), testCase.body, testCase.bodyIsBase64 ? 1 : 0,
      JSON.stringify(testCase.assertions), testCase.sourceRequestId, testCase.enabled ? 1 : 0,
      testCase.sortOrder, testCase.createdAt || now, now
    ]
  )
}

export async function deleteApiTestCase(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM api_test_cases WHERE id = ?', [id])
}

export async function deleteApiTestCasesByGroup(groupId: string) {
  const d = await getDb()
  await d.execute('DELETE FROM api_test_cases WHERE group_id = ?', [groupId])
}

// ── API Test Reports ──────────────────────────────────────────

export async function loadApiTestReports(limit = 50): Promise<ApiTestReport[]> {
  const d = await getDb()
  return await d.select<ApiTestReport[]>(
    `SELECT id, name, description, total_cases as totalCases, passed_cases as passedCases,
            failed_cases as failedCases, total_duration as totalDuration,
            started_at as startedAt, completed_at as completedAt, status, created_at as createdAt
     FROM api_test_reports ORDER BY created_at DESC LIMIT ?`,
    [limit]
  )
}

export async function saveApiTestReport(report: ApiTestReport) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO api_test_reports (id, name, description, total_cases, passed_cases, failed_cases,
      total_duration, started_at, completed_at, status, created_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       total_cases = excluded.total_cases, passed_cases = excluded.passed_cases,
       failed_cases = excluded.failed_cases, total_duration = excluded.total_duration,
       completed_at = excluded.completed_at, status = excluded.status`,
    [
      report.id, report.name, report.description, report.totalCases, report.passedCases,
      report.failedCases, report.totalDuration, report.startedAt, report.completedAt,
      report.status, report.createdAt
    ]
  )
}

export async function deleteApiTestReport(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM api_test_results WHERE report_id = ?', [id])
  await d.execute('DELETE FROM api_test_reports WHERE id = ?', [id])
}

// ── API Test Results ──────────────────────────────────────────

export async function loadApiTestResults(reportId: string): Promise<ApiTestResult[]> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, case_id as caseId, report_id as reportId, passed, status_code as statusCode,
            response_body as responseBody, response_headers as responseHeaders, duration,
            error_message as errorMessage, assertion_results as assertionResults,
            started_at as startedAt, completed_at as completedAt
     FROM api_test_results WHERE report_id = ? ORDER BY started_at ASC`,
    [reportId]
  )
  return rows.map(r => ({
    ...r,
    passed: !!r.passed,
    assertionResults: safeJsonParse(r.assertionResults, []),
    responseHeaders: safeJsonParse(r.responseHeaders, null),
  }))
}

export async function saveApiTestResult(result: ApiTestResult) {
  const d = await getDb()
  await d.execute(
    `INSERT INTO api_test_results (id, case_id, report_id, passed, status_code, response_body,
      response_headers, duration, error_message, assertion_results, started_at, completed_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
     ON CONFLICT(id) DO UPDATE SET
       passed = excluded.passed, status_code = excluded.status_code,
       response_body = excluded.response_body, response_headers = excluded.response_headers,
       duration = excluded.duration, error_message = excluded.error_message,
       assertion_results = excluded.assertion_results, completed_at = excluded.completed_at`,
    [
      result.id, result.caseId, result.reportId, result.passed ? 1 : 0,
      result.statusCode, result.responseBody,
      result.responseHeaders ? JSON.stringify(result.responseHeaders) : null,
      result.duration, result.errorMessage,
      JSON.stringify(result.assertionResults), result.startedAt, result.completedAt
    ]
  )
}
