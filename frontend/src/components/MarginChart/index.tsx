import { useMemo } from 'react';
import ReactEChartsCore from 'echarts-for-react/lib/core';
import * as echarts from 'echarts/core';
import { LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  MarkLineComponent,
  MarkPointComponent,
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  MarkLineComponent,
  MarkPointComponent,
  CanvasRenderer,
]);

const THREE_YEAR_TRADING_DAYS = 732;

interface PeriodData {
  dates: string[];
  values: number[];
  current: string;
}

export interface MarginChartPoint {
  name: string;
  value: number;
}

interface MarginChartProps {
  data?: MarginChartPoint[];
}

function compactTickLabel(name: string): string {
  return name.length >= 10 ? name.slice(5) : name;
}

function buildThreeYearData(data: MarginChartPoint[]): PeriodData | null {
  if (!data.length) {
    return null;
  }

  const sampled = data.slice(-THREE_YEAR_TRADING_DAYS);
  const latest = sampled[sampled.length - 1]?.value ?? 0;

  return {
    dates: sampled.map((item) => compactTickLabel(item.name)),
    values: sampled.map((item) => item.value),
    current: `${latest.toFixed(2)}万亿`,
  };
}

export default function MarginChart({ data = [] }: MarginChartProps) {
  const sourceData = data;

  const periodData = useMemo(() => buildThreeYearData(sourceData), [sourceData]);
  const hasChartData = Boolean(periodData);

  const option = useMemo(() => {
    const { dates, values, current } = periodData ?? { dates: [], values: [], current: '--' };

    return {
      backgroundColor: 'transparent',
      grid: {
        left: 48,
        right: 20,
        top: 32,
        bottom: 28,
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(10,15,35,0.92)',
        borderColor: 'rgba(255,255,255,0.08)',
        textStyle: {
          color: '#E0E6F0',
          fontSize: 12,
          fontFamily: '"JetBrains Mono", monospace',
        },
        formatter: (params: { name: string; value: number }[]) => {
          const p = params[0];
          return `<div style="display:flex;flex-direction:column;gap:4px">
            <span style="color:rgba(255,255,255,0.5);font-size:11px">${p.name}</span>
            <span style="color:#00D4FF;font-size:14px;font-weight:700">${p.value.toFixed(2)}万亿</span>
          </div>`;
        },
      },
      xAxis: {
        type: 'category',
        data: dates,
        boundaryGap: false,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#FFB454',
          fontSize: 10,
          fontFamily: '"JetBrains Mono", monospace',
          interval: 'auto',
        },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        min: (min: number) => Math.floor(min * 100) / 100 - 0.05,
        max: (max: number) => Math.ceil(max * 100) / 100 + 0.05,
        axisLabel: {
          color: '#FFB454',
          fontSize: 10,
          fontFamily: '"JetBrains Mono", monospace',
          formatter: '{value}',
        },
        splitLine: {
          lineStyle: {
            color: 'rgba(255,255,255,0.04)',
            type: 'dashed',
          },
        },
      },
      series: [
        {
          type: 'line',
          data: values,
          smooth: values.length > 2,
          symbol: 'circle',
          symbolSize: values.length === 1 ? 8 : 6,
          showSymbol: values.length <= 9,
          lineStyle: {
            color: '#00D4FF',
            width: 2,
            shadowBlur: 8,
            shadowColor: 'rgba(0,212,255,0.4)',
          },
          itemStyle: {
            color: '#00D4FF',
            borderColor: '#050816',
            borderWidth: 2,
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(0,212,255,0.18)' },
              { offset: 1, color: 'rgba(0,212,255,0.0)' },
            ]),
          },
          markPoint: values.length
            ? {
                data: [
                  {
                    name: '当前',
                    coord: [dates.length - 1, values[values.length - 1]],
                    value: current,
                    symbol: 'pin',
                    symbolSize: 36,
                    itemStyle: {
                      color: '#00D4FF',
                    },
                    label: {
                      show: true,
                      formatter: '{c}',
                      position: 'top',
                      distance: 8,
                      color: '#00D4FF',
                      fontSize: 12,
                      fontWeight: 'bold',
                      fontFamily: '"JetBrains Mono", monospace',
                    },
                  },
                ],
              }
            : undefined,
        },
      ],
    };
  }, [periodData]);

  const current = periodData?.current ?? '--';

  return (
    <div className="card flex h-[300px] min-w-0 flex-col overflow-hidden rounded-lg border border-aims-border bg-aims-card">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-aims-border px-5 py-3">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">融资金额趋势</span>
          <span className="font-mono text-[11px] text-aims-primary">{current}</span>
        </div>
        <span className="font-mono text-[11px] text-white/35">最近约3年</span>
      </div>

      <div className="h-[248px] p-2">
        {hasChartData ? (
          <ReactEChartsCore
            echarts={echarts}
            option={option}
            style={{ height: '100%', width: '100%' }}
            notMerge
            lazyUpdate
          />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-white/35">
            暂无两融数据
          </div>
        )}
      </div>
    </div>
  );
}
