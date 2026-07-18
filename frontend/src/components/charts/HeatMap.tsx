import React from 'react';
import ReactECharts from 'echarts-for-react';

interface HeatMapItem {
  name: string;
  value: number;
}

interface Props {
  data: HeatMapItem[];
}

export default function HeatMap({ data }: Props) {
  const option = {
    tooltip: {},
    series: [
      {
        type: 'treemap',
        data: data.map((item) => ({
          name: item.name,
          value: item.value,
        })),
      },
    ],
  };

  return <ReactECharts option={option} style={{ height: 320 }} />;
}
