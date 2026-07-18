export interface MarketSummary {
  date: string;
  data: Record<string, unknown>;
}

export interface ReportResponse {
  date: string;
  content: string;
}

const API_BASE = '/api';

export async function getMarket(date: string): Promise<MarketSummary> {
  const response = await fetch(`${API_BASE}/market/${date}`);
  return response.json();
}

export async function getReport(date: string): Promise<ReportResponse> {
  const response = await fetch(`${API_BASE}/reports/${date}`);
  return response.json();
}

export async function getMarginTrend() {
  const response