import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import Header from '../../components/Header';
import KPICard from '../../components/KPICard';
import IndexTable from '../../components/IndexTable';
import LianBanTable from '../../components/LianBanTable';
import SectorTop5 from '../../components/SectorTop5';
import MarginChart from '../../components/MarginChart';
import NewsStrip from '../../components/NewsStrip';
import { type DashboardData, getDashboardData, getDashboardDataByDate, syncMarket } from '../../api/aims';

const SYNC_COOLDOWN_MS = 5 * 60 * 1000;

function formatLocalDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

const defaultTradeDate = formatLocalDate(new Date());

const fallbackDashboard: DashboardData = {
  date: defaultTradeDate,
  temperature: '--',
  turnover: '--',
  limitUp: '--',
  limitDown: '--',
  indexRows: [],
  lianBanRows: [],
  sectorRows: [],
  marginTrend: [],
  sentimentTrend: [],
  newsItems: [],
  usingFallback: true,
};

function emptyDashboardForDate(date: string): DashboardData {
  return {
    ...fallbackDashboard,
    date,
  };
}

export default function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardData>(fallbackDashboard);
  const [selectedDate, setSelectedDate] = useState(fallbackDashboard.date);
  const [pendingDate, setPendingDate] = useState(fallbackDashboard.date);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [syncCooldownUntil, setSyncCooldownUntil] = useState(0);
  const [reloadNonce, setReloadNonce] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const lastSyncAtRef = useRef(0);
  const visibleDate = pendingDate || selectedDate || dashboard.date;

  useEffect(() => {
    let cancelled = false;

    async function loadDashboard() {
      setLoading(true);
      const data = await getDashboardData(fallbackDashboard, selectedDate);
      if (!cancelled) {
        setDashboard(data);
        setPendingDate(selectedDate);
        setLoading(false);
      }
    }

    void loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [reloadNonce, selectedDate]);

  function handleRefresh() {
    setReloadNonce((value) => value + 1);
  }

  function showNotice(message: string, timeout = 3600) {
    setNotice(message);
    window.setTimeout(() => setNotice(null), timeout);
  }

  async function handleSync() {
    const now = Date.now();
    const elapsed = now - lastSyncAtRef.current;
    if (syncing || loading) {
      return;
    }

    if (elapsed < SYNC_COOLDOWN_MS) {
      const remaining = Math.ceil((SYNC_COOLDOWN_MS - elapsed) / 1000);
      showNotice(`同步请求过于频繁，请 ${remaining} 秒后再试`);
      return;
    }

    lastSyncAtRef.current = now;
    setSyncCooldownUntil(now + SYNC_COOLDOWN_MS);
    window.setTimeout(() => setSyncCooldownUntil(0), SYNC_COOLDOWN_MS);
    setSyncing(true);
    setLoading(true);
    setNotice(null);

    const targetDate = pendingDate || selectedDate;
    const result = await syncMarket(targetDate);

    if (!result?.ok) {
      setSyncing(false);
      setLoading(false);
      showNotice(result?.message ?? `${targetDate} 同步失败，请稍后再试`);
      return;
    }

    const data = await getDashboardDataByDate(fallbackDashboard, targetDate);
    setDashboard(data);
    setSelectedDate(targetDate);
    setPendingDate(targetDate);
    showNotice(data.usingFallback ? `${targetDate} 暂无数据` : `${data.date} 同步完成`, 2600);

    setSyncing(false);
    setLoading(false);
  }

  async function handleDateChange(date: string) {
    if (!date || date === selectedDate) {
      setPendingDate(date || selectedDate);
      return;
    }

    setPendingDate(date);
    setSelectedDate(date);
    setLoading(true);
    setNotice(null);

    const data = await getDashboardDataByDate(fallbackDashboard, date);

    setDashboard(data);
    setSelectedDate(date);
    setPendingDate(date);
    setLoading(false);
    if (data.usingFallback) {
      showNotice(`${date} 暂无数据，可点击手工同步`);
    }
  }

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
        <Header
          selectedDate={pendingDate}
          dataDate={visibleDate}
          usingFallback={dashboard.usingFallback}
          loading={loading}
          syncing={syncing}
          syncDisabled={syncCooldownUntil > Date.now()}
          notice={notice}
          onDateChange={handleDateChange}
          onRefresh={handleRefresh}
          onSync={handleSync}
        />

        <motion.section
          initial={{ y: -12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.1, duration: 0.35 }}
          className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4"
        >
          <KPICard
            label="市场温度"
            value={dashboard.temperature}
            statusColor="#FFFFFF"
            statusBadge="NORMAL"
          />
          <KPICard
            label="成交额"
            value={dashboard.turnover}
            sub={dashboard.usingFallback ? '暂无数据' : visibleDate}
            statusColor="#00D4FF"
          />
          <KPICard
            label="涨幅≥9%"
            value={dashboard.limitUp}
            sub={dashboard.usingFallback ? '暂无数据' : visibleDate}
            statusColor="#00E676"
          />
          <KPICard
            label="跌幅≥9%"
            value={dashboard.limitDown}
            sub={dashboard.usingFallback ? '暂无数据' : visibleDate}
            statusColor="#FF5252"
          />
        </motion.section>

        <motion.section
          initial={{ y: -12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.18, duration: 0.35 }}
          className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.35fr)]"
        >
          <IndexTable data={dashboard.indexRows} date={visibleDate} />
          <LianBanTable data={dashboard.lianBanRows} />
        </motion.section>

        <motion.section
          initial={{ y: -12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.26, duration: 0.35 }}
          className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.35fr)]"
        >
          <SectorTop5 data={dashboard.sectorRows} date={visibleDate} />
          <MarginChart data={dashboard.marginTrend} />
        </motion.section>

        <motion.section
          initial={{ y: -12, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.34, duration: 0.35 }}
        >
          <NewsStrip data={dashboard.newsItems} live={!dashboard.usingFallback} />
        </motion.section>
      </div>
    </main>
  );
}
