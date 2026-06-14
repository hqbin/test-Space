import request from "./request";

export interface NoteFile {
  id: string;
  name: string;
  content: string;
  folderId?: string;
  entities: string[];
  linkedIssues: { id: string; type: string; description: string }[];
}

export interface NoteFolder {
  id: string;
  name: string;
  files: NoteFile[];
}

export async function fetchNotes(): Promise<NoteFolder[]> {
  const res = await request.get("/notes");
  return res.data;
}

export async function fetchNoteContent(id: string): Promise<string> {
  const res = await request.get(`/notes/${id}`);
  return res.data.content;
}

export async function saveNote(id: string, content: string): Promise<void> {
  await request.put(`/notes/${id}`, { content });
}

export async function createNote(payload: { name: string; folderId?: string }): Promise<NoteFile> {
  const res = await request.post("/notes", payload);
  return res.data;
}

export async function deleteNote(id: string): Promise<void> {
  await request.delete(`/notes/${id}`);
}
