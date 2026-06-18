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

export interface EncryptedPayload {
  data: string;
  iv: string;
  salt: string;
  auth_tag: string;
  size_bytes: number;
  checksum: string;
  metadata: { version: string; exportedAt: string };
}

export async function encryptBackup(
  jsonStr: string,
  masterKeyBase64: string,
  metadata: { version: string; exportedAt: string }
): Promise<EncryptedPayload> {
  const salt = crypto.getRandomValues(new Uint8Array(SALT_SIZE));
  const iv = crypto.getRandomValues(new Uint8Array(IV_SIZE));
  const derivedKey = await deriveKey(masterKeyBase64, salt);

  const checksumBytes = await crypto.subtle.digest("SHA-256", strToBuf(jsonStr));
  const checksum = Array.from(new Uint8Array(checksumBytes))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");

  const encrypted = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    derivedKey,
    strToBuf(jsonStr)
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
    metadata,
  };
}

export async function decryptBackup(
  payload: { data: string; iv: string; salt: string; auth_tag: string; checksum: string },
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

  const plaintext = bufToStr(decrypted);

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
