import { useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { getPlan2030Daily, type Plan2030Daily, type PlanTheme } from '../../api/plan2030';

const THEMES_PER_PAGE = 6;

function formatPercent(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return '--';
  }
  return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`;
}

function changeColor(value: number | null): string {
  if (value === null || !Number.isFinite(value)) return 'text-white/58';
  if (value > 0) return 'text-aims-rise';   // A股: 涨=红色
  if (value < 0) return 'text-aims-fall';    // A股: 跌=绿色
  return 'text-white/58';                     // 平盘
}

function formatYi(value: number | null): string {
  if (value === null || !Number.isFinite(value)) {
    return '--';
  }
  return `${value.toFixed(1)}亿`;
}

function statusClass(status: PlanTheme['status']): string {
  switch (status) {
    case '扩散':
      return 'border-aims-up/25 bg-aims-up/10 text-aims-up';
    case '高潮':
      return 'border-aims-down/25 bg-aims-down/10 text-aims-down';
    case '分歧':
      return 'border-aims-warn/25 bg-aims-warn/10 text-aims-warn';
    case '退潮':
      return 'border-white/10 bg-white/5 text-white/45';
    default:
      return 'border-aims-primary/25 bg-aims-primary/10 text-aims-primary';
  }
}

export default function Plan2030() {
  const [daily, setDaily] = useState<Plan2030Daily | null>(null);
  const [loading, setLoading] = useState(true);
  const themes = daily?.themes ?? [];
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [themePage, setThemePage] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function loadDaily() {
      setLoading(true);
      const data = await getPlan2030Daily();
      if (!cancelled) {
        setDaily(data);
        if (data?.themes?.length) {
          setSelectedId(data.themes[0].id);
          setThemePage(0);
        }
        setLoading(false);
      }
    }

    void loadDaily();

    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => themes.find((item) => item.id === selectedId) ?? themes[0] ?? null,
    [selectedId, themes],
  );
  const themePageCount = Math.max(1, Math.ceil(themes.length / THEMES_PER_PAGE));
  const visibleThemes = themes.slice(
    themePage * THEMES_PER_PAGE,
    themePage * THEMES_PER_PAGE + THEMES_PER_PAGE,
  );
  const selectedTheme: PlanTheme = selected ?? {
    id: 'empty',
    name: loading ? '加载中' : '暂无真实数据',
    axis: '等待接口返回',
    score: 0,
    status: '待验证',
    change: null,
    turnover: null,
    inflow: null,
    limitUp: 0,
    continuity: null,
    concepts: [],
    leaders: [],
    coreStocks: [],
    catalysts: [],
    risks: [loading ? '正在加载十五五主题数据' : '接口未返回主题数据，请检查后端服务和数据源'],
  };
  const visibleLeaders = selectedTheme.leaders.slice(0, 5);
  const visibleCoreStocks = (selectedTheme.coreStocks ?? []).slice(0, 5);
  const totalScore = daily?.summary.avgScore ?? 0;
  const totalLimitUp = daily?.summary.limitUpCount ?? 0;
  const totalInflow = daily?.summary.inflow ?? null;

  return (
    <main className="min-h-screen bg-aims-bg text-slate-100">
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.025]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(255,255,255,0.16) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.16) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
        }}
      />

      <div className="relative z-10 mx-auto flex min-h-screen w-full max-w-[1800px] flex-col gap-4 px-4 py-4 sm:px-5 lg:px-6">
        <header className="flex min-h-[64px] w-full flex-wrap items-center justify-between gap-4 border-b border-aims-border px-3 py-3 sm:px-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-aims-primary">
              <span className="text-sm font-bold tracking-tight text-white">AI</span>
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
                <span className="text-base font-bold tracking-wide text-white">十五五战略主线</span>
                <span className="text-xs font-medium text-aims-amber">Policy Theme Radar</span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-white/40">
                <span className="font-mono tabular-nums">数据 {daily?.sourceDate ?? daily?.date ?? '--'}</span>
                <span>{loading ? '加载中' : daily?.usingFallback ? '暂无市场日报' : '现代化产业体系'}</span>
              </div>
            </div>
            <nav className="hidden items-center gap-1 rounded border border-aims-border bg-aims-card p-1 md:flex">
              <a href="#/" className="rounded px-2.5 py-1 text-xs font-medium text-white/50 transition-colors hover:text-white/80">
                每日复盘
              </a>
              <a href="#/plan-2030" className="rounded bg-aims-primary/15 px-2.5 py-1 text-xs font-medium text-aims-primary">
                十五五规划
              </a>
            </nav>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded border border-aims-primary/25 bg-aims-primary/10 px-2 py-1 text-[11px] font-mono font-semibold text-aims-primary">
              <span className="h-1.5 w-1.5 rounded-full bg-current shadow-[0_0_6px_currentColor]" />
              POLICY
            </span>
            <span className="rounded border border-aims-border bg-aims-card px-2 py-1 text-[11px] text-white/45">
              {daily?.usingFallback ? '等待同步后计算' : '最新已同步交易日'}
            </span>
          </div>
        </header>

        <section className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Metric label="主线综合热度" value={String(totalScore)} suffix="/100" tone="primary" />
          <Metric label="样本涨停数" value={String(totalLimitUp)} suffix="只" tone="up" />
          <Metric label="主力净流入" value={formatYi(totalInflow)} suffix="" tone="amber" />
        </section>

        <section className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(320px,0.8fr)_minmax(520px,1.2fr)_minmax(320px,0.8fr)] xl:[&>*]:h-[600px]">
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="card flex min-h-[600px] flex-col overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-aims-border px-5 py-3">
              <span className="text-sm font-semibold text-white">主题强度排行</span>
              <span className="text-[11px] text-white/35">
                {themes.length ? `${themePage + 1}/${themePageCount}` : '政策映射 + 市场验证'}
              </span>
            </div>
            <div className="flex-1 divide-y divide-white/[0.04] overflow-hidden">
              {visibleThemes.map((theme, index) => (
                <button
                  key={theme.id}
                  type="button"
                  onClick={() => {
                    setSelectedId(theme.id);
                    const selectedIndex = themes.findIndex((item) => item.id === theme.id);
                    setThemePage(Math.max(0, Math.floor(selectedIndex / THEMES_PER_PAGE)));
                  }}
                  className={`flex w-full items-center gap-3 px-5 py-3 text-left transition-colors ${
                    selectedId === theme.id ? 'bg-aims-primary/8' : 'hover:bg-white/[0.03]'
                  }`}
                >
                  <span className="w-6 shrink-0 font-mono text-sm text-aims-amber">
                    {themePage * THEMES_PER_PAGE + index + 1}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-semibold text-white">{theme.name}</span>
                      <span className={`rounded border px-1.5 py-0.5 text-[10px] ${statusClass(theme.status)}`}>
                        {theme.status}
                      </span>
                    </div>
                    <div className="mt-1.5 h-1.5 overflow-hidden rounded bg-white/[0.06]">
                      <div
                        className="h-full rounded bg-aims-primary"
                        style={{ width: `${theme.score}%` }}
                      />
                    </div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-white/42">
                      <span>{theme.axis}</span>
                      <span>涨幅 {formatPercent(theme.change)}</span>
                      <span>涨停 {theme.limitUp}</span>
                    </div>
                  </div>
                  <span className="font-mono text-xl font-bold text-aims-primary">{theme.score}</span>
                </button>
              ))}
            </div>
            {themePageCount > 1 && (
              <div className="flex items-center justify-between border-t border-aims-border px-5 py-2">
                <button
                  type="button"
                  disabled={themePage === 0}
                  onClick={() => setThemePage((page) => Math.max(0, page - 1))}
                  className="rounded border border-white/10 px-2.5 py-1 text-xs text-white/55 transition-colors hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
                >
                  上一页
                </button>
                <span className="font-mono text-[11px] text-white/35">
                  {Math.min(themes.length, themePage * THEMES_PER_PAGE + 1)}-{Math.min(themes.length, (themePage + 1) * THEMES_PER_PAGE)} / {themes.length}
                </span>
                <button
                  type="button"
                  disabled={themePage >= themePageCount - 1}
                  onClick={() => setThemePage((page) => Math.min(themePageCount - 1, page + 1))}
                  className="rounded border border-white/10 px-2.5 py-1 text-xs text-white/55 transition-colors hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
                >
                  下一页
                </button>
              </div>
            )}
          </motion.div>

          <motion.div
            key={`leaders-${selectedTheme.id}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid min-h-[600px] grid-rows-2 gap-4 overflow-hidden"
          >
            <section className="card flex min-h-0 flex-col overflow-hidden">
              <div className="flex items-center justify-between border-b border-aims-border px-5 py-3">
                <span className="text-sm font-semibold text-white">龙头映射 · {selectedTheme.name}</span>
                <span className="text-[11px] text-white/35">涨停池 Top5</span>
              </div>
              <div className="flex-1 overflow-hidden overflow-x-auto">
                <table className="w-full min-w-[620px] text-left">
                  <thead className="bg-white/[0.02] text-[11px] uppercase text-white/42">
                    <tr>
                      <th className="px-4 py-2.5 font-semibold">代码</th>
                      <th className="px-4 py-2.5 font-semibold">名称</th>
                      <th className="px-4 py-2.5 font-semibold">产业角色</th>
                      <th className="px-4 py-2.5 text-right font-semibold">涨幅</th>
                      <th className="px-4 py-2.5 text-right font-semibold">封板资金</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {visibleLeaders.length ? (
                      visibleLeaders.map((stock) => (
                        <tr key={stock.code} className="text-sm text-white/78">
                          <td className="px-4 py-2 font-mono text-white/52">{stock.code || '待映射'}</td>
                          <td className="px-4 py-2 font-semibold text-white">{stock.name}</td>
                          <td className="px-4 py-2 text-white/58">{stock.role}</td>
                          <td className={`px-4 py-2 text-right font-mono ${changeColor(stock.change)}`}>{formatPercent(stock.change)}</td>
                          <td className="px-4 py-2 text-right font-mono text-aims-amber">{formatYi(stock.sealAmount ?? null)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr className="text-sm text-white/45">
                        <td className="px-4 py-6 text-center" colSpan={5}>
                          暂无涨停池映射标的
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="card flex min-h-0 flex-col overflow-hidden">
              <div className="flex items-center justify-between border-b border-aims-border px-5 py-3">
                <span className="text-sm font-semibold text-white">市值核心 · {selectedTheme.name}</span>
                <span className="text-[11px] text-white/35">流通市值 Top5</span>
              </div>
              <div className="flex-1 overflow-hidden overflow-x-auto">
                <table className="w-full min-w-[620px] text-left">
                  <thead className="bg-white/[0.02] text-[11px] uppercase text-white/42">
                    <tr>
                      <th className="px-4 py-2.5 font-semibold">代码</th>
                      <th className="px-4 py-2.5 font-semibold">名称</th>
                      <th className="px-4 py-2.5 font-semibold">流通市值</th>
                      <th className="px-4 py-2.5 text-right font-semibold">总市值</th>
                      <th className="px-4 py-2.5 text-right font-semibold">涨幅</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/[0.04]">
                    {visibleCoreStocks.length ? (
                      visibleCoreStocks.map((stock) => (
                        <tr key={stock.code} className="text-sm text-white/78">
                          <td className="px-4 py-2 font-mono text-white/52">{stock.code}</td>
                          <td className="px-4 py-2 font-semibold text-white">{stock.name}</td>
                          <td className="px-4 py-2 font-mono text-aims-amber">{formatYi(stock.freeFloatMarketCap ?? null)}</td>
                          <td className="px-4 py-2 text-right font-mono text-aims-amber">{formatYi(stock.totalMarketCap ?? null)}</td>
                          <td className={`px-4 py-2 text-right font-mono ${changeColor(stock.change)}`}>{formatPercent(stock.change)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr className="text-sm text-white/45">
                        <td className="px-4 py-6 text-center" colSpan={5}>
                          暂无主题成分市值快照
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </section>
          </motion.div>

          <motion.div
            key={`detail-${selectedTheme.id}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="grid min-h-[600px] grid-rows-[auto_minmax(0,1fr)] gap-4"
          >
            <section className="card overflow-hidden">
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-aims-border px-5 py-3">
                <div>
                  <span className="text-sm font-semibold text-white">主题详情 · {selectedTheme.name}</span>
                  <span className="ml-2 text-xs text-aims-amber">{selectedTheme.axis}</span>
                </div>
                <span className={`rounded border px-2 py-1 text-[11px] ${statusClass(selectedTheme.status)}`}>
                  {selectedTheme.status}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-px bg-white/[0.04]">
                <DataCell label="平均涨幅" value={formatPercent(selectedTheme.change)} tone="up" />
                <DataCell label="资金活跃" value={formatYi(selectedTheme.turnover)} tone="primary" />
                <DataCell label="净流入" value={formatYi(selectedTheme.inflow)} tone="amber" />
                <DataCell label="连续强势" value={selectedTheme.continuity === null ? '--' : `${selectedTheme.continuity}天`} tone="plain" />
              </div>
              <div className="px-5 py-4">
                <div className="mb-3 text-xs font-semibold text-white/60">概念映射</div>
                <div className="flex flex-wrap gap-2">
                  {selectedTheme.concepts.map((concept) => (
                    <span key={concept} className="rounded border border-white/10 bg-white/[0.04] px-2 py-1 text-xs text-white/68">
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
              <div className="border-t border-aims-border px-5 py-4">
                <div className="mb-3 text-xs font-semibold text-white/60">催化事件</div>
                <div className="space-y-2">
                  {selectedTheme.catalysts.length ? (
                    selectedTheme.catalysts.map((item) => (
                      <div key={item} className="flex gap-2 text-sm text-white/78">
                        <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-aims-primary" />
                        <span>{item}</span>
                      </div>
                    ))
                  ) : (
                    <div className="rounded border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white/45">
                      暂无匹配新闻，等待新闻关键词数据补充
                    </div>
                  )}
                </div>
              </div>
            </section>

            <section className="card overflow-hidden">
              <div className="flex items-center justify-between border-b border-aims-border px-5 py-3">
                <span className="text-sm font-semibold text-white">风险状态</span>
                <span className="font-mono text-[11px] text-white/35">WATCH</span>
              </div>
              <div className="px-5 py-4">
                <div className="mb-4 h-2 overflow-hidden rounded bg-white/[0.06]">
                  <div
                    className="h-full rounded bg-gradient-to-r from-aims-primary via-aims-warn to-aims-down"
                    style={{ width: `${Math.min(100, selectedTheme.score)}%` }}
                  />
                </div>
                <div className="space-y-3">
                  {selectedTheme.risks.map((item) => (
                    <div key={item} className="rounded border border-aims-warn/15 bg-aims-warn/5 px-3 py-2 text-sm text-white/72">
                      {item}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </motion.div>
        </section>

        <section className="card overflow-hidden">
            <div className="flex items-center justify-between border-b border-aims-border px-5 py-3">
              <span className="text-sm font-semibold text-white">后续数据接入</span>
              <span className="font-mono text-[11px] text-white/35">AKShare</span>
            </div>
            <div className="grid grid-cols-1 divide-y divide-white/[0.04] sm:grid-cols-2 sm:divide-x sm:divide-y-0 xl:grid-cols-8">
              {([
                ['主题股票池配置', daily?.dataCoverage.themeConfig],
                ['本地市场日报', daily?.dataCoverage.marketReport],
                ['概念板块行情', daily?.dataCoverage.conceptQuotes],
                ['行业/概念资金流', daily?.dataCoverage.fundFlow],
                ['财经新闻关键词', daily?.dataCoverage.newsKeywordMatch],
                ['个股日度明细', daily?.dataCoverage.stockDaily],
                ['全A市值快照', daily?.dataCoverage.stockSnapshot],
                ['十五五主题日表', daily?.dataCoverage.themeDaily],
              ] as Array<[string, boolean | undefined]>).map(([item, ready]) => (
                <div key={item} className="flex min-h-[64px] items-center justify-between gap-3 px-5 py-3 text-sm">
                  <span className="text-white/72">{item}</span>
                  <span className={`rounded border px-2 py-0.5 text-[11px] ${
                    ready
                      ? 'border-aims-primary/20 bg-aims-primary/8 text-aims-primary'
                      : 'border-white/10 bg-white/[0.03] text-white/35'
                  }`}>
                    {ready ? 'READY' : 'TODO'}
                  </span>
                </div>
              ))}
            </div>
        </section>
      </div>
    </main>
  );
}

function Metric({
  label,
  value,
  suffix,
  tone,
}: {
  label: string;
  value: string;
  suffix: string;
  tone: 'primary' | 'up' | 'amber';
}) {
  const color = tone === 'up' ? 'text-aims-up' : tone === 'amber' ? 'text-aims-amber' : 'text-aims-primary';
  return (
    <div className="card min-h-[104px] px-5 py-4">
      <div className="text-xs font-medium text-aims-amber">{label}</div>
      <div className={`mt-2 font-mono text-4xl font-bold leading-none ${color}`}>
        {value}
        <span className="ml-1 text-sm font-medium text-white/38">{suffix}</span>
      </div>
    </div>
  );
}

function DataCell({ label, value, tone }: { label: string; value: string; tone: 'up' | 'primary' | 'amber' | 'plain' }) {
  const color =
    tone === 'up'
      ? 'text-aims-up'
      : tone === 'primary'
        ? 'text-aims-primary'
        : tone === 'amber'
          ? 'text-aims-amber'
          : 'text-white';
  return (
    <div className="bg-aims-card px-5 py-4">
      <div className="text-[11px] text-white/38">{label}</div>
      <div className={`mt-1 font-mono text-lg font-semibold ${color}`}>{value}</div>
    </div>
  );
}
