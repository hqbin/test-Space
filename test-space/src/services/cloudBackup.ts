const BASE_URL = "https://tms.zeasn.com/api/TestSpace";

let tauriFetch: typeof fetch | null = null;

async function getFetch(): Promise<typeof fetch> {
  if (tauriFetch) return tauriFetch;
  try {
    const mod = await import("@tauri-apps/plugin-http");
    tauriFetch = mod.fetch;
  } catch {
    tauriFetch = fetch;
  }
  return tauriFetch;
}

function headers(deviceId: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "X-Device-ID": deviceId,
  };
}

async function request<T>(
  method: string,
  path: string,
  deviceId: string,
  body?: any
): Promise<T> {
  const url = `${BASE_URL}${path}`;
  const f = await getFetch();
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 300000);
  try {
    const res = await f(url, {
      method,
      headers: headers(deviceId),
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
    const text = await res.text();
    if (res.status === 204) return undefined as T;
    let json: any;
    try {
      json = JSON.parse(text);
    } catch {
      throw new Error(`Server returned non-JSON (HTTP ${res.status}): ${text.slice(0, 200)}`);
    }
    if (!res.ok) {
      throw new Error(json.error || `HTTP ${res.status}`);
    }
    return json as T;
  } finally {
    clearTimeout(timer);
  }
}

export interface BackupListItem {
  id: string;
  device_id: string;
  size_bytes: number;
  checksum: string;
  metadata: { version: string; exportedAt: string };
  created_at: string;
}

export interface BackupDetail extends BackupListItem {
  data: string;
  iv: string;
  salt: string;
  auth_tag: string;
}

export interface BackupUploadPayload {
  data: string;
  iv: string;
  salt: string;
  auth_tag: string;
  size_bytes: number;
  checksum: string;
  metadata: { version: string; exportedAt: string };
}

export function uploadBackup(
  deviceId: string,
  payload: BackupUploadPayload
): Promise<{ id: string; created_at: string }> {
  return request("POST", "/backups", deviceId, payload);
}

export function listBackups(deviceId: string): Promise<BackupListItem[]> {
  return request("GET", "/backups", deviceId);
}

export function getBackup(
  deviceId: string,
  backupId: string
): Promise<BackupDetail> {
  return request("GET", `/backups/${backupId}`, deviceId);
}

export function deleteBackup(
  deviceId: string,
  backupId: string
): Promise<void> {
  return request("DELETE", `/backups/${backupId}`, deviceId);
}
