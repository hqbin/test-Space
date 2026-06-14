import request from "./request";

export interface DashboardStats {
  pageViews: number;
  activeUsers: number;
  interactions: number;
  avgSession: number;
  trends: { pageViews: number; activeUsers: number; interactions: number; avgSession: number };
}

export interface QuickAction {
  icon: string;
  title: string;
  description: string;
}

export interface ProjectItem {
  title: string;
  description: string;
  icon: string;
  running: boolean;
  time: string;
  members: string[];
}

export async function fetchDashboardStats(): Promise<DashboardStats> {
  const res = await request.get("/dashboard/v2/stats");
  return res.data;
}

export async function fetchQuickActions(): Promise<QuickAction[]> {
  const res = await request.get("/dashboard/v2/quick-actions");
  return res.data;
}

export async function fetchProjects(): Promise<ProjectItem[]> {
  const res = await request.get("/dashboard/v2/projects");
  return res.data;
}
