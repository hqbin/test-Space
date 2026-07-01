import * as db from "@/services/database";
import * as cloudApi from "@/services/cloudBackup";
import * as crypto from "@/services/crypto";
import type { AppBackup } from "@/services/database";

function yieldToMain(): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, 0));
}

async function ensureDeviceId(): Promise<string> {
  let id = (await db.getLastDeviceId())?.trim() || "";
  if (!id) {
    id = crypto.generateDeviceId();
    const list = await db.getDeviceIdList();
    const next = list.includes(id) ? list : [id, ...list];
    await db.saveDeviceIdList(next);
    await db.saveLastDeviceId(id);
    return id;
  }

  const list = await db.getDeviceIdList();
  if (!list.includes(id)) {
    await db.saveDeviceIdList([id, ...list]);
  }
  return id;
}

/**
 * Maximum size (in bytes, uncompressed) for any single item to be included in a cloud backup.
 * Items larger than this are silently dropped from the sync payload (with a console warning
 * that lists the skipped items). 1 MB per item keeps the overall encrypted+gzipped payload
 * well under the server's `client_max_body_size` limit even for large workspaces.
 */
const CLOUD_MAX_ITEM_SIZE = 1 * 1024 * 1024;

function filterOversizedItems(data: AppBackup): AppBackup {
  const skipped: string[] = [];

  const notes = data.notes.filter(n => {
    const size = (n.content?.length || 0) + ((n as any).contentJson?.length || 0);
    if (size >= CLOUD_MAX_ITEM_SIZE) {
      skipped.push(`笔记 ${n.id} (${Math.round(size / 1024 / 1024 * 100) / 100}MB)`);
      return false;
    }
    return true;
  });

  const noteVersions = data.noteVersions.filter(v => {
    const size = v.content?.length || 0;
    if (size >= CLOUD_MAX_ITEM_SIZE) {
      skipped.push(`笔记版本 ${v.id} (${Math.round(size / 1024 / 1024 * 100) / 100}MB)`);
      return false;
    }
    return true;
  });

  const caseFiles = data.caseFiles.filter(f => {
    const dataSize = typeof f.data === 'string' ? f.data.length : JSON.stringify(f.data || '').length;
    if (dataSize >= CLOUD_MAX_ITEM_SIZE) {
      skipped.push(`用例文件 ${f.id} (${Math.round(dataSize / 1024 / 1024 * 100) / 100}MB)`);
      return false;
    }
    return true;
  });

  if (skipped.length > 0) {
    console.warn(`[cloudSync] 跳过 ${skipped.length} 个超大项目:\n${skipped.join('\n')}`);
  }

  return { ...data, notes, noteVersions, caseFiles };
}

export { filterOversizedItems };

export async function syncBackupToCloud(): Promise<void> {
  await db.checkDatabaseReady();
  await yieldToMain();
  const deviceId = await ensureDeviceId();
  await yieldToMain();
  const raw = await db.exportAllData();
  await yieldToMain();
  const data = filterOversizedItems(raw);
  await yieldToMain();
  const json = JSON.stringify(data);
  await yieldToMain();
  const key = await crypto.getOrCreateKey();
  await yieldToMain();
  const payload = await crypto.encryptBackup(json, key, {
    version: data.version,
    exportedAt: data.exportedAt,
  });
  await yieldToMain();
  await cloudApi.uploadBackup(deviceId.trim(), payload);
}

