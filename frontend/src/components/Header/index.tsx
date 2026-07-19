import { useMemo } from 'react';

function formatTimestamp(): string {
  const now = new Date();
  const y = now.getFullYear();
  const mo = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  const h = String(now.getHours()).padStart(2, '0');
  const mi = String(now.getMinutes()).padStart(2, '0');
  const s = String(now.getSeconds()).padStart(2, '0');
  return `${y}-${mo}-${d} ${h}:${mi}:${s}`;
}

interface HeaderProps {
  selectedDate: string;
  dataDate: string;
  usingFallback: boolean;
  loading: boolean;
  syncing: boolean;
  syncDisabled: boolean;
  notice?: string | null;
  onDateChange: (date: string) => void;
  onRefresh: () => void;
  onSync: () => void;
}

export default function Header({
  selectedDate,
  dataDate,
  usingFallback,
  loading,
  syncing,
  syncDisabled,
  notice,
  onDateChange,
  onRefresh,
  onSync,
}: HeaderProps) {
  const timestamp = useMemo(() => formatTimestamp(), []);
  const statusText = usingFallback ? 'NO DATA' : 'LIVE';
  const statusClass = usingFallback ? 'text-aims-warn' : 'text-aims-up';

  return (
    <header className="flex min-h-[64px] w-full flex-wrap items-center justify-between gap-4 border-b border-aims-border px-3 py-3 sm:px-4">
      <div className="flex min-w-0 items-center gap-3">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-aims-primary">
          <span className="text-sm font-bold tracking-tight text-white">AI</span>
        </div>
        <div className="min-w-0">
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="text-base font-bold tracking-wide text-white">AIMS</span>
            <span className="text-xs font-medium text-aims-amber">
              AI Market Intelligence System
            </span>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-white/40">
            <span className="font-mono tabular-nums">Updated {timestamp}</span>
            <span className="hidden sm:inline">·</span>
            <span className="font-mono tabular-nums">Data {dataDate}</span>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {notice ? (
          <span className="max-w-[360px] truncate rounded border border-aims-warn/30 bg-aims-warn/10 px-2 py-1 text-[11px] text-aims-warn">
            {notice}
          </span>
        ) : null}

        <span className={`inline-flex items-center gap-1 rounded border border-aims-border bg-aims-card px-2 py-1 text-[11px] font-mono font-semibold ${statusClass}`}>
          <span className="h-1.5 w-1.5 rounded-full bg-current shadow-[0_0_6px_currentColor]" />
          {statusText}
        </span>

        <label className="flex items-center gap-2 rounded border border-aims-border bg-aims-card px-2 py-1">
          <span className="text-[11px] font-medium text-white/45">日期</span>
          <input
            type="date"
            value={selectedDate}
            onChange={(event) => onDateChange(event.target.value)}
            className="w-[136px] bg-transparent font-mono text-xs tabular-nums text-white/80 outline-none [color-scheme:dark]"
          />
        </label>

        <button
          type="button"
          onClick={onRefresh}
          disabled={loading || syncing}
          className="rounded border border-aims-border bg-aims-card px-3 py-1.5 text-xs font-medium text-white/70 transition-colors hover:border-aims-primary/40 hover:text-white disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? '刷新中' : '刷新'}
        </button>

        <button
          type="button"
          onClick={onSync}
          disabled={syncing || loading || syncDisabled}
          className="rounded border border-aims-primary/35 bg-aims-primary/10 px-3 py-1.5 text-xs font-semibold text-aims-primary transition-colors hover:border-aims-primary hover:bg-aims-primary/15 disabled:cursor-not-allowed disabled:border-aims-border disabled:bg-aims-card disabled:text-white/35"
        >
          {syncing ? '同步中' : '手工同步'}
        </button>
      </div>
    </header>
  );
}
