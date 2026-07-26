export type PlanStatus = '启动' | '扩散' | '高潮' | '分歧' | '退潮' | '待验证';

export interface PlanLeader {
  code: string;
  name: string;
  role: string;
  change: number | null;
  inflow: number | null;
  freeFloatMarketCap?: number | null;
  totalMarketCap?: number | null;
  turnoverRate?: number | null;
  sealAmount?: number | null;
}

export interface PlanTheme {
  id: string;
  name: string;
  axis: string;
  score: number;
  status: PlanStatus;
  change: number | null;
  turnover: number | null;
  inflow: number | null;
  limitUp: number;
  continuity: number | null;
  concepts: string[];
  leaders: PlanLeader[];
  coreStocks?: PlanLeader[];
  catalysts: string[];
  risks: string[];
  matchedSectors?: string[];
}

export interface Plan2030Daily {
  date: string;
  sourceDate?: string | null;
  usingFallback: boolean;
  themes: PlanTheme[];
  summary: {
    themeCount: number;
    avgScore: number;
    limitUpCount: number;
    inflow: number | null;
  };
  dataCoverage: {
    marketReport: boolean;
    themeConfig: boolean;
    conceptQuotes: boolean;
    fundFlow: boolean;
    newsKeywordMatch: boolean;
    stockDaily?: boolean;
    stockSnapshot?: boolean;
    themeDaily?: boolean;
  };
  diagnostics?: {
    akshareErrors?: string[];
  };
}

async function requestJson<T>(url: string, fallback: T): Promise<T> {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      return fallback;
    }
    return response.json();
  } catch {
    return fallback;
  }
}

export async function getPlan2030Daily(date?: string): Promise<Plan2030Daily | null> {
  const query = date ? `?date=${encodeURIComponent(date)}` : '';
  return requestJson<Plan2030Daily | null>(`/api/plan2030/daily${query}`, null);
}
