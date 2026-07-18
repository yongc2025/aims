import React from 'react';
import ReactECharts from 'echarts-for-react';

export interface LineChartPoint {
  name: string;
  value: number;
}

interface Props {
  data: LineChartPoint[];
}

export default function LineChart({ data }: Props) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'category',
      data: data.map((item) => item.name),
    },
    yAxis: {
      type: 'value',
    },
    series