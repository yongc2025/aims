import React from 'react';

interface MetricCardProps {
  title: string;
  value: string;
  unit?: string;
  status?: 'normal' | 'up' | 'down';
}

export default function MetricCard({ title, value, unit, status = 'normal' }: MetricCardProps) {
  const statusClass = {
    normal: 'text-cyan-400',
    up: 'text-green-400',
    down: 'text-red-400',
  }[status];

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900/80 p-5 shadow-lg">
      <div className="text-sm text-slate-400