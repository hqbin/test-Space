import request from "./request";

export interface ChangelogItem {
  type: string;
  content: string;
}

export interface VersionRelease {
  id: number;
  version: string;
  title: string;
  status: "draft" | "published";
  changelog: ChangelogItem[];
  createdAt: string;
  publishedAt?: string;
}

export interface CreateVersionPayload {
  version: string;
  title: string;
  changelog: ChangelogItem[];
}

export async function fetchVersions(): Promise<VersionRelease[]> {
  const res = await request.get("/version-releases");
  return res.data;
}

export async function createVersion(payload: CreateVersionPayload): Promise<VersionRelease> {
  const res = await request.post("/version-releases", payload);
  return res.data;
}

export async function publishVersion(id: number): Promise<VersionRelease> {
  const res = await request.post(`/version-releases/${id}/publish`);
  return res.data;
}

export async function deleteVersion(id: number): Promise<void> {
  await request.delete(`/version-releases/${id}`);
}
