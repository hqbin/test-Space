export interface UserInfo {
  id: number;
  username: string;
  full_name?: string;
  email?: string;
  phone?: string;
  avatar?: string;
  role?: string;
  is_super?: boolean;
}

export interface LoginCredentials {
  username: string;
  password: string;
  captcha_id: string;
  captcha_code: string;
}

export interface LoginResponse {
  code: number;
  message?: string;
  data?: {
    token: string;
    signKey?: string;
    user: UserInfo;
    must_change_password?: boolean;
  };
}

export interface CaptchaResponse {
  code: number;
  data?: {
    captcha_id: string;
    captcha_image: string;
  };
}

export interface ApiResponse<T = unknown> {
  code: number;
  message?: string;
  data?: T;
}

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

export interface VersionRelease {
  id: number;
  version: string;
  title: string;
  changelog: ChangelogItem[];
  status: "draft" | "published";
  created_at: string;
  published_at?: string;
}

export interface ChangelogItem {
  type: "new" | "fix" | "improve" | "delete" | "other";
  content: string;
}

export interface DatabaseTable {
  name: string;
  comment?: string;
  rows: number;
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
