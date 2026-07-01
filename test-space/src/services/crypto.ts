import * as db from "./database";

const KEY_ITERATIONS = 100000;
const KEY_LENGTH = 256;
const SALT_SIZE = 16;
const IV_SIZE = 12;
const AUTH_TAG_SIZE = 16;
const STORAGE_KEY = "cloud_encryption_key";

function base64Encode(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let binary = "";
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function base64Decode(str: string): Uint8Array {
  const binary = atob(str);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

function strToBuf(s: string): Uint8Array {
  return new TextEncoder().encode(s);
}

function bufToStr(buf: ArrayBuffer): string {
  return new TextDecoder().decode(buf);
}

/** Gzip-compress a string. Uses native CompressionStream (available in all modern webviews). */
async function gzipCompress(str: string): Promise<Uint8Array> {
  const cs = new (globalThis as any).CompressionStream("gzip");
  const writer = cs.writable.getWriter();
  writer.write(strToBuf(str));
  writer.close();
  const chunks: Uint8Array[] = [];
  const reader = cs.readable.getReader();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value as Uint8Array);
  }
  const total = chunks.reduce((n, c) => n + c.byteLength, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.byteLength;
  }
  return out;
}

/** Gzip-decompress bytes back into a string. */
async function gzipDecompress(bytes: Uint8Array): Promise<string> {
  const ds = new (globalThis as any).DecompressionStream("gzip");
  const writer = ds.writable.getWriter();
  writer.write(bytes);
  writer.close();
  const chunks: Uint8Array[] = [];
  const reader = ds.readable.getReader();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value as Uint8Array);
  }
  const total = chunks.reduce((n, c) => n + c.byteLength, 0);
  const out = new Uint8Array(total);
  let offset = 0;
  for (const c of chunks) {
    out.set(c, offset);
    offset += c.byteLength;
  }
  return new TextDecoder().decode(out);
}

export async function getOrCreateKey(): Promise<string> {
  let key = await db.getSetting(STORAGE_KEY);
  if (!key) {
    const raw = crypto.getRandomValues(new Uint8Array(32));
    key = base64Encode(raw.buffer);
    await db.setSetting(STORAGE_KEY, key);
  }
  return key;
}

async function deriveKey(masterKeyBase64: string, salt: Uint8Array): Promise<CryptoKey> {
  const masterKey = await crypto.subtle.importKey(
    "raw",
    base64Decode(masterKeyBase64),
    "PBKDF2",
    false,
    ["deriveKey"]
  );
  return crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: KEY_ITERATIONS, hash: "SHA-256" },
    masterKey,
    { name: "AES-GCM", length: KEY_LENGTH },
    false,
    ["encrypt", "decrypt"]
  );
}

export interface BackupMetadata {
  version: string;
  exportedAt: string;
  /** If true, decrypted bytes are gzip-compressed and must be decompressed to get JSON. */
  compressed?: boolean;
}

export interface EncryptedPayload {
  data: string;
  iv: string;
  salt: string;
  auth_tag: string;
  size_bytes: number;
  checksum: string;
  metadata: BackupMetadata;
}

/**
 * Encrypt a JSON string for cloud upload.
 * Flow: JSON string → gzip-compress → AES-GCM encrypt → base64.
 * `size_bytes` and `checksum` are computed on the ORIGINAL plaintext JSON
 * (so restore-side checksum verification remains meaningful).
 */
export async function encryptBackup(
  jsonStr: string,
  masterKeyBase64: string,
  metadata: { version: string; exportedAt: string }
): Promise<EncryptedPayload> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_SIZE));
  const iv = crypto.getRandomValues(new Uint8Array(IV_SIZE));
  const derivedKey = await deriveKey(masterKeyBase64, salt);

  // Checksum on plaintext JSON (before compression) for end-to-end verification.
  const checksumBytes = await crypto.subtle.digest("SHA-256", strToBuf(jsonStr));
  const checksum = Array.from(new Uint8Array(checksumBytes))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  // Gzip-compress before encrypting to shrink the upload payload (text/JSON compresses 3-10x).
  const compressedBytes = await gzipCompress(jsonStr);

  const encrypted = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    derivedKey,
    compressedBytes
  );

  const encryptedBytes = new Uint8Array(encrypted);
  const authTag = encryptedBytes.slice(encryptedBytes.length - AUTH_TAG_SIZE);
  const ciphertext = encryptedBytes.slice(0, encryptedBytes.length - AUTH_TAG_SIZE);

  return {
    data: base64Encode(ciphertext.buffer),
    iv: base64Encode(iv.buffer),
    salt: base64Encode(salt.buffer),
    auth_tag: base64Encode(authTag.buffer),
    size_bytes: jsonStr.length,
    checksum,
    metadata: { ...metadata, compressed: true },
  };
}

/**
 * Decrypt a cloud backup payload back into the original JSON string.
 * If `payload.metadata.compressed === true` the decrypted bytes are treated as gzip;
 * otherwise (legacy uncompressed backups) they are decoded directly as UTF-8.
 */
export async function decryptBackup(
  payload: {
    data: string;
    iv: string;
    salt: string;
    auth_tag: string;
    checksum: string;
    metadata?: BackupMetadata;
  },
  masterKeyBase64: string
): Promise<string> {
  const salt = base64Decode(payload.salt);
  const iv = base64Decode(payload.iv);
  const ciphertext = base64Decode(payload.data);
  const authTag = base64Decode(payload.auth_tag);
  const derivedKey = await deriveKey(masterKeyBase64, salt);

  const combined = new Uint8Array(ciphertext.length + authTag.length);
  combined.set(ciphertext);
  combined.set(authTag, ciphertext.length);

  let decrypted: ArrayBuffer;
  try {
    decrypted = await crypto.subtle.decrypt(
      { name: "AES-GCM", iv },
      derivedKey,
      combined
    );
  } catch {
    throw new Error("密钥不匹配，解密失败");
  }

  // Legacy backups (before Phase 36) stored plain UTF-8; new ones are gzip-compressed.
  const isCompressed = payload.metadata?.compressed === true;
  const plaintext = isCompressed
    ? await gzipDecompress(new Uint8Array(decrypted))
    : bufToStr(decrypted);

  const checksumBytes = await crypto.subtle.digest("SHA-256", strToBuf(plaintext));
  const checksum = Array.from(new Uint8Array(checksumBytes))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  if (checksum !== payload.checksum) {
    throw new Error("Checksum mismatch: data may be corrupted");
  }

  return plaintext;
}

export function generateDeviceId(): string {
  return crypto.randomUUID();
}
