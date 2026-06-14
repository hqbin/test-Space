import request from "./request";

export interface AnalyticsStats {
  pageViews: number;
  activeUsers: number;
  interactions: number;
  avgSession: number;
  pageViewsTrend: number;
  activeUsersTrend: number;
  interactionsTrend: number;
  avgSessionTrend: number;
}

export interface FeatureUsage {
  name: string;
  usage: number;
  total: number;
}

export interface TrendDataPoint {
  date: string;
  value: number;
}

export async function fetchAnalyticsStats(): Promise<AnalyticsStats> {
  const res = await request.get("/analytics/stats");
  return res.data;
}

export async function fetchUsageTrend(params?: {
  days?: number;
  metric?: string;
}): Promise<TrendDataPoint[]> {
  const res = await request.get("/analytics/trend", { params });
  return res.data;
}

export async function fetchFeatureUsage(): Promise<FeatureUsage[]> {
  const res = await request.get("/analytics/feature-usage");
  return res.data;
}

export async function fetchActiveUsers(params?: {
  days?: number;
}): Promise<TrendDataPoint[]> {
  const res = await request.get("/analytics/active-users", { params });
  return res.data;
}
