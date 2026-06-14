import request from "./request";

export interface TableInfo {
  name: string;
  schema: string;
  columns: { name: string; type: string; nullable: boolean; key?: string }[];
  rowCount: number;
}

export interface QueryResult {
  columns: string[];
  rows: Record<string, any>[];
  rowCount: number;
  executionTime: number;
}

export async function fetchTables(): Promise<TableInfo[]> {
  const res = await request.get("/database/tables");
  return res.data;
}

export async function fetchTableData(tableName: string, params?: {
  page?: number;
  pageSize?: number;
}): Promise<QueryResult> {
  const res = await request.get(`/database/tables/${tableName}/data`, { params });
  return res.data;
}

export async function executeQuery(sql: string): Promise<QueryResult> {
  const res = await request.post("/database/sql", { sql });
  return res.data;
}

export async function fetchTableSchema(tableName: string): Promise<TableInfo> {
  const res = await request.get(`/database/tables/${tableName}/schema`);
  return res.data;
}
