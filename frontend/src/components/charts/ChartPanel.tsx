import React from 'react';

interface ChartPanelProps {
  title: string;
  children: React.ReactNode;
}

export default function ChartPanel({ title, children }: ChartPanelProps) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-900/80 p-5 shadow-lg">
      <h3 className="mb-4 text-sm font-medium text-slate-300">{title}</h3>
      <div className="min-h-[280px]">{children}</div>
    </section>
  );
}
