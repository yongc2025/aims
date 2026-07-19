export interface IndexRow {
  key: string;
  name: string;
  point: string;
  change: number;
  changeStr: string;
  volume: string;
  upDown: string;
}

export interface LianBanRow {
  key: string;
  name: string;
  code: string;
  boardCount: string;
  detail: string;
  industry: string;
  reason: string;
}

export interface SectorRow {
  key: string;
  rank: number;
  name: string;
  limitCount: number;
}

export interface NewsItem {
  time: string;
  category: string;
  categoryColor: string;
  headline: string;
}

export interface ChartPoint {
  name: string;
  value: number;
}

export interface MarketReportResponse {
  date?: string;
  data?: Record<string, unknown>;
  markdown?: string | null;
}

export interface MarketSyncResponse {
  ok: boolean;
  date: string;
  reason?: string;
  message?: string;
  summary?: Record<string, unknown>;
}

export interface DashboardData {
  date: string;
  temperature: string;
  turnover: string;
  limitUp: string;
  limitDown: string;
  indexRows: IndexRow[];
  lianBanRows: LianBanRow[];
  sectorRows: SectorRow[];
  marginTrend: ChartPoint[];
  sentimentTrend: ChartPoint[];
  newsItems: NewsItem[];
  usingFallback: boolean;
}

const API_BASE = '/api';

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

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === 'object' && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function firstDefined<T>(...values: T[]): T | undefined {
  return values.find((value) => value !== undefined && value !== null);
}

function formatNumber(value: unknown, fallback = '--'): string {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return value.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
  }
  if (typeof value === 'string' && value.trim()) {
    return value;
  }
  return fallback;
}

function formatAmount(value: unknown, fallback = '--'): string {
  const num =
    typeof value === 'number'
      ? value
      : typeof value === 'string'
        ? Number.parseFloat(value.replace(/,/g, ''))
        : NaN;

  if (!Number.isFinite(num)) {
    return typeof value === 'string' && value.trim() ? value : fallback;
  }

  if (Math.abs(num) >= 1_000_000_000_000) {
    return `${(num / 1_000_000_000_000).toFixed(2)}万亿`;
  }

  if (Math.abs(num) >= 100_000_000) {
    return `${(num / 100_000_000).toFixed(0)}亿`;
  }

  return num.toLocaleString('zh-CN', { maximumFractionDigits: 2 });
}

function formatPercent(value: unknown): { change: number; changeStr: string } {
  const num =
    typeof value === 'number'
      ? value
      : typeof value === 'string'
        ? Number.parseFloat(value.replace('%', ''))
        : 0;
  const change = Number.isFinite(num) ? num : 0;
  const sign = change > 0 ? '+' : '';
  return {
    change,
    changeStr: `${sign}${change.toFixed(2)}%`,
  };
}

function formatLimitStat(value: unknown): string {
  if (typeof value !== 'string') {
    return '--';
  }

  const match = value.match(/^(\d+)\/(\d+)$/);
  if (!match) {
    return value || '--';
  }

  return `${match[1]}天${match[2]}板`;
}

function chartPointFromItem(item: unknown): ChartPoint | null {
  const record = asRecord(item);
  const name = firstDefined(record.name, record.date, record.trade_date, record.week_date);
  const value = firstDefined(record.value, record.margin_balance, record.up, record.limit_up);
  const numericValue =
    typeof value === 'number'
      ? value
      : typeof value === 'string'
        ? Number.parseFloat(value)
        : NaN;

  if (!name || !Number.isFinite(numericValue)) {
    return null;
  }

  const normalizedValue = numericValue > 1_000_000_000 ? numericValue / 1_000_000_000_000 : numericValue;

  return {
    name: String(name).slice(5) || String(name),
    value: normalizedValue,
  };
}

function normalizeIndexRows(data: Record<string, unknown>): IndexRow[] {
  const indices = asArray(data.indices);
  const legacyIndexData = asArray(data.index_data);
  const indexCandidates = (
    indices.length
      ? indices
      : legacyIndexData.length
        ? legacyIndexData
        : [data.shanghai_index]
  ).filter(Boolean);

  return indexCandidates.map((item, index) => {
    const record = asRecord(item);
    const pct = formatPercent(firstDefined(record.change_pct, record.change, record.change_percent));
    const up = firstDefined(record.up_count, record.up);
    const down = firstDefined(record.down_count, record.down);

    return {
      key: String(index + 1),
      name: String(firstDefined(record.name, record.index_name, '上证指数')),
      point: formatNumber(firstDefined(record.close, record.point, record.value)),
      change: pct.change,
      changeStr: pct.changeStr,
      volume: formatAmount(firstDefined(record.amount, record.volume, record.turnover)),
      upDown: up !== undefined || down !== undefined ? `${formatNumber(up)}/${formatNumber(down)}` : '--',
    };
  });
}

function normalizeLianBanRows(data: Record<string, unknown>): LianBanRow[] {
  const rows = asArray(firstDefined(data.limit_chain_stocks, data.lianban_stocks, data.limit_up_stocks));

  return rows.map((item, index) => {
    const record = asRecord(item);
    const chainDays = firstDefined(record.chain_days, record.board_count, record.limit_days);

    return {
      key: String(index + 1),
      name: String(firstDefined(record.stock_name, record.name, '--')),
      code: String(firstDefined(record.stock_code, record.code, '--')),
      boardCount: chainDays ? `${chainDays}连板` : '--',
      detail: formatLimitStat(firstDefined(record.detail, record.sequence, '--')),
      industry: String(firstDefined(record.industry, record.sector, '--')),
      reason: String(firstDefined(record.reason, record.concept, '--')),
    };
  });
}

function normalizeSectorRows(data: Record<string, unknown>, apiRows: unknown[]): SectorRow[] {
  const rows = asArray(firstDefined(data.sectors, data.sector_data, data.sector_daily));
  const source = rows.length ? rows : apiRows;

  return source.slice(0, 5).map((item, index) => {
    const record = asRecord(item);

    return {
      key: String(index + 1),
      rank: Number(firstDefined(record.rank, index + 1)),
      name: String(firstDefined(record.sector_name, record.name, '--')),
      limitCount: Number(firstDefined(record.limit_up_count, record.limitCount, 0)),
    };
  });
}

function normalizeNews(data: Record<string, unknown>): NewsItem[] {
  const rows = asArray(firstDefined(data.news, data.news_events, data.events));

  return rows.slice(0, 3).map((item) => {
    const record = asRecord(item);
    return {
      time: String(firstDefined(record.time, record.date, '--')).slice(-5),
      category: String(firstDefined(record.category, '新闻')),
      categoryColor: 'text-aims-primary bg-aims-primary/10 border-aims-primary/25',
      headline: String(firstDefined(record.title, record.headline, '--')),
    };
  });
}

function normalizeMarketTemperature(stats: Record<string, unknown>): string {
  const up = Number(firstDefined(stats.up_count, stats.up, 0));
  const down = Number(firstDefined(stats.down_count, stats.down, 0));
  if (!Number.isFinite(up) || !Number.isFinite(down) || up + down <= 0) {
    return '--';
  }
  return Math.round((up / (up + down)) * 100).toString();
}

export async function getLatestMarket(): Promise<MarketReportResponse | null> {
  return requestJson<MarketReportResponse | null>(`${API_BASE}/market/latest`, null);
}

export async function getMarket(date: string): Promise<MarketReportResponse | null> {
  return requestJson<MarketReportResponse | null>(`${API_BASE}/market/${date}`, null);
}

export async function syncMarket(date: string): Promise<MarketSyncResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/market/sync`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ trade_date: date }),
    });

    if (!response.ok) {
      return null;
    }

    return response.json();
  } catch {
    return null;
  }
}

export async function getMarginTrend(): Promise<ChartPoint[]> {
  const rows = await requestJson<unknown[]>(`${API_BASE}/analysis/margin`, []);
  return rows.map(chartPointFromItem).filter(Boolean) as ChartPoint[];
}

export async function getSentimentTrend(): Promise<ChartPoint[]> {
  const rows = await requestJson<unknown[]>(`${API_BASE}/analysis/sentiment`, []);
  return rows.map(chartPointFromItem).filter(Boolean) as ChartPoint[];
}

export async function getSectorTrend(): Promise<unknown[]> {
  return requestJson<unknown[]>(`${API_BASE}/analysis/sectors`, []);
}

function buildDashboardData(
  fallback: DashboardData,
  marketResponse: MarketReportResponse,
  marginTrend: ChartPoint[],
  sentimentTrend: ChartPoint[],
  sectorTrend: unknown[],
): DashboardData {
  const data = asRecord(marketResponse.data);
  const stats = asRecord(data.market_statistics);

  return {
    date: String(firstDefined(marketResponse.date, data.date, fallback.date)),
    temperature: normalizeMarketTemperature(stats),
    turnover: formatAmount(firstDefined(data.turnover, data.total_turnover, stats.turnover)),
    limitUp: formatNumber(firstDefined(stats.limit_up_count, stats.limit_up)),
    limitDown: formatNumber(firstDefined(stats.limit_down_count, stats.limit_down)),
    indexRows: normalizeIndexRows(data),
    lianBanRows: normalizeLianBanRows(data),
    sectorRows: normalizeSectorRows(data, sectorTrend),
    marginTrend,
    sentimentTrend,
    newsItems: normalizeNews(data),
    usingFallback: false,
  };
}

export async function getDashboardData(
  fallback: DashboardData,
  date?: string,
): Promise<DashboardData> {
  const [marketResponse, marginTrend, sentimentTrend, sectorTrend] = await Promise.all([
    date ? getMarket(date) : getLatestMarket(),
    getMarginTrend(),
    getSentimentTrend(),
    getSectorTrend(),
  ]);

  const data = asRecord(marketResponse?.data);

  if (!marketResponse?.data) {
    return {
      ...fallback,
      date: date ?? fallback.date,
      marginTrend: [],
      sentimentTrend: [],
      sectorRows: [],
      usingFallback: true,
    };
  }

  return buildDashboardData(fallback, marketResponse, marginTrend, sentimentTrend, sectorTrend);
}

export async function getDashboardDataByDate(
  fallback: DashboardData,
  date: string,
): Promise<DashboardData> {
  const [marketResponse, marginTrend, sentimentTrend, sectorTrend] = await Promise.all([
    getMarket(date),
    getMarginTrend(),
    getSentimentTrend(),
    getSectorTrend(),
  ]);

  if (!marketResponse?.data) {
    return {
      ...fallback,
      date,
      marginTrend: [],
      sentimentTrend: [],
      sectorRows: [],
      usingFallback: true,
    };
  }

  return buildDashboardData(fallback, marketResponse, marginTrend, sentimentTrend, sectorTrend);
}
