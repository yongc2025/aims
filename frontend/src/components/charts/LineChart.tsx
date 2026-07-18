import React from 'react';
import ReactECharts from 'echarts-for-react';

export interface LineChartPoint {
  name: string;
  value: number;
}

interface Props {
  data: LineChartPoint[];
  height?: number;
}

export default function LineChart({ data, height = 320 }: Props) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    grid: {
      left: 20,
      right: 20,
      top: 30,
      bottom: 30,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: data.map((item) => item.name),
      axisLabel: {
        color: '#94a3b8',
      },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        color: '#94a3b8',
      },
    },
    series: [
      {
        type: 'line',
        smooth: true,
        data: data.map((item) => item.value),
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
