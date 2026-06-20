export interface DeviceInfo {
  id: string;
  name: string;
  serial: string;
  model: string;
  androidVersion: string;
  firmwareVersion: string;
  ipAddress: string;
  status: "online" | "offline" | "standby";
  cpuUsage: number;
  memoryUsage: number;
  batteryLevel: number;
  connectionType: "USB" | "TCP/IP";
}

export interface TelemetryData {
  cpu: number;
  memory: number;
  battery: number;
  batteryStatus: string;
  storage: number;
}

export interface LogEntry {
  timestamp: string;
  level: "V" | "D" | "I" | "W" | "E" | "F";
  tag: string;
  message: string;
  pid?: number;
  tid?: number;
}

export interface CaseItem {
  id: string
  module: string
  title: string
  precondition: string
  steps: string
  expected: string
  priority: string
  tags: string[]
  assignee: string
  remarks: string
  [key: string]: any
}

export interface CustomFieldDef {
  key: string
  label: string
  type: 'text' | 'select' | 'textarea'
  options?: string[]
}

export interface CaseFile {
  id: string
  name: string
  version: string
  cases: CaseItem[]
  createdAt: string
  updatedAt: string
  tags: string[]
  customFields?: CustomFieldDef[]
}

export interface RecentFileInfo {
  path: string
  name: string
  caseCount: number
  lastOpened: string
  isFavorite: boolean
  isPinned: boolean
}

export interface FileTab {
  fileId: string
  fileName: string
  isDirty: boolean
  path: string | null
}

export interface InputHistoryEntry {
  id: number
  keyName: string
  value: string
  createdAt: string
}

export interface LogSession {
  id: string
  type: 'logcat' | 'diagnostic' | 'boot_logcat'
  deviceSerial: string
  status: 'running' | 'stopped'
  startedAt: string
  metadata: string
}

// ── Notes Space ──────────────────────────────────────────────

export interface NoteSpace {
  id: string
  name: string
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface NoteFolder {
  id: string
  spaceId: string | null
  name: string
  parentId: string | null
  sortOrder: number
  createdAt: string
  updatedAt: string
}

export interface NoteItem {
  id: string
  folderId: string | null
  title: string
  content: string
  tags: string[]
  isFavorite: boolean
  createdAt: string
  updatedAt: string
}

export interface NoteVersion {
  id: string
  noteId: string
  content: string
  savedAt: string
}

export interface NoteLink {
  id: string
  sourceNoteId: string
  targetNoteId: string
  createdAt: string
}

// ── API Proxy ──────────────────────────────────────────────

export interface ApiCapturedRequest {
  id: string
  method: string
  url: string
  host: string
  path: string
  query: string | null
  request_headers: string[][]       // [[name, value], ...]
  request_body: string | null
  response_status_code: number | null
  response_status_text: string | null
  response_headers: string[][] | null
  response_body: string | null
  start_time: number
  end_time: number | null
  duration: number | null           // milliseconds
  is_https: boolean
  request_size: number
  response_size: number
}

export interface ApiRewriteRule {
  id: string
  name: string
  enabled: boolean
  url_pattern: string
  match_type: 'contains' | 'regex' | 'prefix'
  action_type: 'modify_request_header' | 'modify_request_body'
    | 'modify_response_header' | 'modify_response_body'
    | 'drop' | 'redirect' | 'replace_status'
  header_name: string | null
  header_value: string | null
  body_search: string | null
  body_replace: string | null
  redirect_url: string | null
  status_code: number | null
}

export interface ApiProxyStatus {
  running: boolean
  port: number | null
  breakpoint_enabled: boolean
  captured_count: number
}
