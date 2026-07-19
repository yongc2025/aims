import { useMemo } from 'react';

export interface NewsItem {
  time: string;
  category: string;
  categoryColor: string;
  headline: string;
}

function NewsCard({ item }: { item: NewsItem }) {
  return (
    <div className="flex items-center gap-3 min-w-0 flex-1">
      {/* Timestamp */}
      <span className="font-mono text-xs tabular-nums text-white/35 shrink-0">
        {item.time}
      </span>

      {/* Category tag */}
      <span
        className={`inline-flex text-[11px] px-1.5 py-0.5 rounded border font-mono font-semibold shrink-0 ${item.categoryColor}`}
      >
        {item.category}
      </span>

      {/* Headline */}
      <span className="text-white/80 text-sm font-medium truncate">
        {item.headline}
      </span>
    </div>
  );
}

interface NewsStripProps {
  data?: NewsItem[];
  live?: boolean;
}

export default function NewsStrip({ data = [], live = false }: NewsStripProps) {
  const newsItems = data;
  const cards = useMemo(
    () => newsItems.map((item, i) => <NewsCard key={i} item={item} />),
    [newsItems]
  );

  return (
    <div className="card flex min-h-[82px] min-w-0 flex-col overflow-hidden rounded-lg border border-aims-border bg-aims-card md:flex-row md:items-center">
      {/* Left label */}
      <div className="flex shrink-0 flex-col items-start justify-center gap-0.5 border-b border-aims-border px-4 py-3 md:h-full md:w-[180px] md:border-b-0 md:border-r">
        <span className="text-white text-sm font-bold tracking-wide">最新新闻</span>
        <span className="text-aims-amber text-[11px] font-medium">
          AI Agent · {live ? '实时数据' : '暂无数据'}
        </span>
      </div>

      {/* Right: news items */}
      <div className="grid min-w-0 flex-1 grid-cols-1 md:grid-cols-3">
        {cards.length ? cards.map((card, i) => (
          <div key={i} className="flex min-w-0 items-center border-t border-aims-border px-4 py-3 first:border-t-0 md:border-l md:border-t-0 md:first:border-l-0">
            {card}
          </div>
        )) : (
          <div className="px-4 py-3 text-sm text-white/35">暂无新闻数据</div>
        )}
      </div>
    </div>
  );
}
