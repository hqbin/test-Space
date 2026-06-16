import type Database from '@tauri-apps/plugin-sql'
import type { InputHistoryEntry, LogSession, NoteSpace, NoteFolder, NoteItem, NoteVersion, NoteLink } from '@/types'

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
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_notes_folder ON notes(folder_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_notes_fav ON notes(is_favorite)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_versions_note ON note_versions(note_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_links_source ON note_links(source_note_id)`)
  await d.execute(`CREATE INDEX IF NOT EXISTS idx_note_links_target ON note_links(target_note_id)`)
  await d.execute(`CREATE TABLE IF NOT EXISTS scripts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL DEFAULT 'bat',
    content TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
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
  await d.execute('DELETE FROM note_spaces WHERE id = ?', [id])
  await d.execute('DELETE FROM note_folders WHERE space_id = ?', [id])
  await d.execute('UPDATE notes SET folder_id = NULL WHERE folder_id IN (SELECT id FROM note_folders WHERE space_id = ?)', [id])
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
  await d.execute('DELETE FROM note_folders WHERE id = ?', [id])
  // Move notes in this folder to uncategorized
  await d.execute('UPDATE notes SET folder_id = NULL WHERE folder_id = ?', [id])
}

export async function renameNoteFolder(id: string, name: string) {
  const d = await getDb()
  await d.execute('UPDATE note_folders SET name = ?, updated_at = ? WHERE id = ?', [name, new Date().toISOString(), id])
}

// ── Notes ─────────────────────────────────────────────────────

export async function loadNotes(): Promise<NoteItem[]> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, tags, is_favorite as isFavorite,
            created_at as createdAt, updated_at as updatedAt
     FROM notes ORDER BY updated_at DESC`
  )
  return rows.map(r => ({ ...r, tags: JSON.parse(r.tags || '[]'), isFavorite: !!r.isFavorite }))
}

export async function loadNote(id: string): Promise<NoteItem | null> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, tags, is_favorite as isFavorite,
            created_at as createdAt, updated_at as updatedAt
     FROM notes WHERE id = ?`, [id]
  )
  if (rows.length === 0) return null
  const r = rows[0]
  return { ...r, tags: JSON.parse(r.tags || '[]'), isFavorite: !!r.isFavorite }
}

export async function saveNote(note: { id: string; folderId?: string | null; title: string; content: string; tags?: string[]; isFavorite?: boolean }) {
  const d = await getDb()
  const now = new Date().toISOString()
  const existing = await d.select<any[]>('SELECT id FROM notes WHERE id = ?', [note.id])
  if (existing.length === 0) {
    await d.execute(
      `INSERT INTO notes (id, folder_id, title, content, tags, is_favorite, created_at, updated_at)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [note.id, note.folderId || null, note.title, note.content,
       JSON.stringify(note.tags || []), note.isFavorite ? 1 : 0, now, now]
    )
  } else {
    await d.execute(
      `UPDATE notes SET folder_id = ?, title = ?, content = ?, tags = ?, is_favorite = ?, updated_at = ?
       WHERE id = ?`,
      [note.folderId || null, note.title, note.content,
       JSON.stringify(note.tags || []), note.isFavorite ? 1 : 0, now, note.id]
    )
  }
}

export async function deleteNote(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM notes WHERE id = ?', [id])
  await d.execute('DELETE FROM note_versions WHERE note_id = ?', [id])
  await d.execute('DELETE FROM note_links WHERE source_note_id = ? OR target_note_id = ?', [id, id])
}

export async function toggleNoteFavorite(id: string): Promise<boolean> {
  const d = await getDb()
  const rows = await d.select<{ is_favorite: number }[]>('SELECT is_favorite FROM notes WHERE id = ?', [id])
  if (rows.length === 0) return false
  const newVal = rows[0].is_favorite ? 0 : 1
  await d.execute('UPDATE notes SET is_favorite = ?, updated_at = ? WHERE id = ?', [newVal, new Date().toISOString(), id])
  return !!newVal
}

export async function searchNotes(query: string): Promise<NoteItem[]> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, tags, is_favorite as isFavorite,
            created_at as createdAt, updated_at as updatedAt
     FROM notes WHERE title LIKE ? OR content LIKE ?
     ORDER BY updated_at DESC`,
    [`%${query}%`, `%${query}%`]
  )
  return rows.map(r => ({ ...r, tags: JSON.parse(r.tags || '[]'), isFavorite: !!r.isFavorite }))
}

export async function getFavoriteNotes(): Promise<NoteItem[]> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, folder_id as folderId, title, content, tags, is_favorite as isFavorite,
            created_at as createdAt, updated_at as updatedAt
     FROM notes WHERE is_favorite = 1 ORDER BY updated_at DESC`
  )
  return rows.map(r => ({ ...r, tags: JSON.parse(r.tags || '[]'), isFavorite: !!r.isFavorite }))
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
}

export async function saveScript(script: { id: string; name: string; type: string; content: string }) {
  const d = await getDb()
  const now = new Date().toISOString()
  const existing = await d.select<any[]>('SELECT id FROM scripts WHERE id = ?', [script.id])
  if (existing.length === 0) {
    await d.execute(
      `INSERT INTO scripts (id, name, type, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)`,
      [script.id, script.name, script.type, script.content, now, now]
    )
  } else {
    await d.execute(
      `UPDATE scripts SET name = ?, type = ?, content = ?, updated_at = ? WHERE id = ?`,
      [script.name, script.type, script.content, now, script.id]
    )
  }
}

export async function loadScript(id: string): Promise<ScriptItem | null> {
  const d = await getDb()
  const rows = await d.select<any[]>(
    `SELECT id, name, type, content, created_at as createdAt, updated_at as updatedAt FROM scripts WHERE id = ?`,
    [id]
  )
  return rows.length > 0 ? rows[0] : null
}

export async function listScripts(): Promise<ScriptItem[]> {
  const d = await getDb()
  return await d.select<any[]>(
    `SELECT id, name, type, content, created_at as createdAt, updated_at as updatedAt FROM scripts ORDER BY updated_at DESC`
  )
}

export async function deleteScript(id: string) {
  const d = await getDb()
  await d.execute('DELETE FROM scripts WHERE id = ?', [id])
}

export interface AppBackup {
  version: string
  exportedAt: string
  fieldRuleSets: any[]
  caseFiles: any[]
  recentFiles: any[]
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
}

export async function exportAllData(): Promise<AppBackup> {
  const fieldRuleSets = await loadFieldRuleSets()
  const caseFiles = await loadCaseFiles()
  const recentFiles = await getRecentFiles()
  const favPaths = await getFavorites()
  const settings = await loadSettings()
  const d = await getDb()
  const inputHistory = await d.select<InputHistoryEntry[]>(
    'SELECT id, key_name as keyName, value, created_at as createdAt FROM input_history ORDER BY sort_order DESC'
  )
  const logSessions = await d.select<LogSession[]>(
    'SELECT id, type, device_serial as deviceSerial, status, started_at as startedAt, metadata FROM log_sessions ORDER BY started_at DESC'
  )
  const noteSpaces = await d.select<any[]>('SELECT id, name, sort_order as sortOrder, created_at as createdAt, updated_at as updatedAt FROM note_spaces')
  const noteFolders = await loadNoteFolders()
  const notes = await loadNotes()
  const noteVersions = await d.select<NoteVersion[]>(
    'SELECT id, note_id as noteId, content, saved_at as savedAt FROM note_versions ORDER BY saved_at ASC'
  )
  const noteLinks = await d.select<NoteLink[]>(
    'SELECT id, source_note_id as sourceNoteId, target_note_id as targetNoteId, created_at as createdAt FROM note_links'
  )
  const scripts = await listScripts()
  return {
    version: '1.3',
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
  }
}

export async function importAllData(backup: AppBackup) {
  const d = await getDb()
  await d.execute('DELETE FROM field_rule_sets')
  await d.execute('DELETE FROM case_files')
  await d.execute('DELETE FROM recent_files')
  await d.execute('DELETE FROM favorites')
  await d.execute('DELETE FROM app_settings')
  await d.execute('DELETE FROM input_history')
  await d.execute('DELETE FROM log_sessions')
  await d.execute('DELETE FROM note_folders')
  await d.execute('DELETE FROM notes')
  await d.execute('DELETE FROM note_versions')
  await d.execute('DELETE FROM note_links')
  try { await d.execute('DELETE FROM note_spaces') } catch {}
  await d.execute('DELETE FROM scripts')

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
  for (const h of backup.inputHistory || []) {
    await d.execute(
      'INSERT INTO input_history (key_name, value, created_at, sort_order) VALUES (?, ?, ?, ?)',
      [h.keyName, h.value, h.createdAt, Date.parse(h.createdAt)]
    )
  }
  for (const s of backup.logSessions || []) {
    await d.execute(
      'INSERT INTO log_sessions (id, type, device_serial, status, started_at, metadata) VALUES (?, ?, ?, ?, ?, ?)',
      [s.id, s.type, s.deviceSerial, s.status, s.startedAt, s.metadata]
    )
  }
  // ── Notes ──────────────────────────────────────────────────
  for (const raw of backup.noteSpaces || []) {
    const s: any = raw
    await d.execute(
      'INSERT INTO note_spaces (id, name, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?)',
      [s.id, s.name, s.sortOrder ?? s.sort_order ?? 0, s.createdAt ?? s.created_at, s.updatedAt ?? s.updated_at]
    )
  }
  for (const raw of backup.noteFolders || []) {
    const f: any = raw
    await d.execute(
      'INSERT INTO note_folders (id, space_id, name, parent_id, sort_order, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
      [f.id, f.spaceId ?? f.space_id ?? null, f.name, f.parentId ?? f.parent_id ?? null, f.sortOrder ?? f.sort_order ?? 0, f.createdAt ?? f.created_at, f.updatedAt ?? f.updated_at]
    )
  }
  for (const raw of backup.notes || []) {
    const n: any = raw
    await d.execute(
      'INSERT INTO notes (id, folder_id, title, content, tags, is_favorite, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
      [n.id, n.folderId ?? n.folder_id ?? null, n.title ?? '', n.content ?? '',
       JSON.stringify(n.tags ?? []), n.isFavorite ? 1 : 0, n.createdAt ?? n.created_at, n.updatedAt ?? n.updated_at]
    )
  }
  for (const raw of backup.noteVersions || []) {
    const v: any = raw
    await d.execute(
      'INSERT INTO note_versions (id, note_id, content, saved_at) VALUES (?, ?, ?, ?)',
      [v.id, v.noteId ?? v.note_id, v.content, v.savedAt ?? v.saved_at]
    )
  }
  for (const raw of backup.noteLinks || []) {
    const l: any = raw
    await d.execute(
      'INSERT INTO note_links (id, source_note_id, target_note_id, created_at) VALUES (?, ?, ?, ?)',
      [l.id, l.sourceNoteId ?? l.source_note_id, l.targetNoteId ?? l.target_note_id, l.createdAt ?? l.created_at]
    )
  }
  for (const raw of backup.scripts || []) {
    const s: any = raw
    await d.execute(
      'INSERT INTO scripts (id, name, type, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)',
      [s.id, s.name, s.type ?? 'bat', s.content ?? '', s.createdAt ?? s.created_at, s.updatedAt ?? s.updated_at ?? s.createdAt]
    )
  }
}
