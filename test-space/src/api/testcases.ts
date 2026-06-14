import request from "./request";

export interface TestCase {
  id: number;
  case_number?: string;
  module: string;
  sub_module?: string;
  name: string;
  precondition?: string;
  steps: { step: string; expected: string }[];
  expected_result?: string;
  level: string;
  remarks?: string;
  automation?: string;
  status: string;
  case_type?: string;
  tags?: string[];
  priority?: string;
  primary_project_id?: number;
  created_at?: string;
  updated_at?: string;
}

export interface TestCasePayload {
  module: string;
  name: string;
  precondition?: string;
  steps?: { step: string; expected: string }[];
  expected_result?: string;
  level?: string;
  remarks?: string;
  automation?: string;
  status?: string;
  case_type?: string;
  tags?: string[];
  priority?: string;
}

export interface ModuleNode {
  id: number;
  name: string;
  tag?: string;
  parent_id: number | null;
  sort_order?: number;
  children?: ModuleNode[];
  cases?: TestCase[];
}

export async function fetchTestCases(params?: {
  search?: string;
  module?: string;
  project_id?: number;
  page?: number;
  page_size?: number;
}): Promise<TestCase[]> {
  const res = await request.get("/testcases", { params });
  return res.data;
}

export async function fetchTestCase(id: number): Promise<TestCase> {
  const res = await request.get(`/testcases/${id}`);
  return res.data;
}

export async function createTestCase(payload: TestCasePayload): Promise<TestCase> {
  const res = await request.post("/testcases", payload);
  return res.data;
}

export async function batchCreateTestCases(payload: TestCasePayload[]): Promise<TestCase[]> {
  const res = await request.post("/testcases/batch-create", payload);
  return res.data;
}

export async function updateTestCase(id: number, payload: Partial<TestCasePayload>): Promise<TestCase> {
  const res = await request.put(`/testcases/${id}`, payload);
  return res.data;
}

export async function deleteTestCase(id: number): Promise<void> {
  await request.delete(`/testcases/${id}`);
}

export async function batchDeleteTestCases(ids: number[]): Promise<void> {
  await request.post("/testcases/batch-delete", { ids });
}

export async function exportTestCases(params: {
  project_id?: number;
  module?: string;
  ids?: number[];
}): Promise<Blob> {
  const res = await request.get("/testcases/export", {
    params,
    responseType: "blob",
  });
  return res.data;
}

export async function fetchModulesTree(projectId: number): Promise<ModuleNode[]> {
  const res = await request.get("/modules/tree", { params: { project_id: projectId } });
  return res.data;
}

export async function fetchTestCasesStatistics(params: {
  project_id?: number;
  module?: string;
}): Promise<any> {
  const res = await request.get("/testcases/statistics", { params });
  return res.data;
}
