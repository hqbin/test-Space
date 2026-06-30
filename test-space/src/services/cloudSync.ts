import * as db from "@/services/database";
import * as cloudApi from "@/services/cloudBackup";
import * as crypto from "@/services/crypto";

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

export async function syncBackupToCloud(): Promise<void> {
  await db.checkDatabaseReady();
  await yieldToMain();
  const deviceId = await ensureDeviceId();
  await yieldToMain();
  const data = await db.exportAllData();
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

