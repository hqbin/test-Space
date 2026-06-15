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
