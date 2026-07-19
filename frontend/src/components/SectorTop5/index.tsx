import { useMemo } from 'react';
import { Table, ConfigProvider, theme } from 'antd';
import type { ColumnsType } from 'antd/es/table';

export interface SectorRow {
  key: string;
  rank: number;
  name: string;
  limitCount: number;
}

function getRankColor(rank: number): string {
  switch (rank) {
    case 1: return '#00D4FF';
    case 2: return '#FFB454';
    case 3: return '#FFD700';
    default: return '#6B7280';
  }
}

interface SectorTop5Props {
  data?: SectorRow[];
  date?: string;
}

export default function SectorTop5({ data = [], date = '2026-07-17' }: SectorTop5Props) {
  const tableData = data;
  const columns: ColumnsType<SectorRow> = useMemo(
    () => [
      {
        title: '#',
        dataIndex: 'rank',
        key: 'rank',
        width: 44,
        align: 'center',
        render: (rank: number) => (
          <span
            className="font-mono text-sm font-bold tabular-nums"
            style={{ color: getRankColor(rank) }}
          >
            {rank}
          </span>
        ),
      },
      {
        title: '板块名称',
        dataIndex: 'name',
        key: 'name',
        width: 100,
        render: (text: string) => (
          <span className="text-white/90 text-sm font-medium">{text}</span>
        ),
      },
      {
        title: '涨停数量',
        dataIndex: 'limitCount',
        key: 'limitCount',
        width: 90,
        align: 'right',
        render: (count: number) => (
          <span className="font-mono text-sm font-bold tabular-nums" style={{ color: '#FF5252' }}>
            {count}
            <span className="text-white/40 font-normal ml-0.5">只</span>
          </span>
        ),
      },
    ],
    []
  );

  return (
    <div className="card flex h-[300px] min-w-0 flex-col overflow-hidden rounded-lg border border-aims-border bg-aims-card">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-aims-border">
        <span className="text-white text-sm font-semibold">板块涨停 TOP5</span>
        <span className="font-mono text-xs tabular-nums text-white/40">{date}</span>
      </div>

      {/* Table */}
      <ConfigProvider
        theme={{
          algorithm: theme.darkAlgorithm,
          token: {
            colorBgContainer: 'transparent',
            colorBorderSecondary: 'rgba(255,255,255,0.04)',
            colorText: 'rgba(255,255,255,0.6)',
            colorTextHeading: 'rgba(255,255,255,0.4)',
            fontSize: 12,
            padding: 10,
            lineHeight: 1.4,
          },
        }}
      >
        <Table
          columns={columns}
          dataSource={tableData}
          pagination={false}
          size="small"
          showSorterTooltip={false}
          rowClassName={() => 'aims-table-row'}
          className="aims-sector-table"
          style={{ background: 'transparent' }}
          scroll={{ x: 260, y: 205 }}
        />
      </ConfigProvider>
    </div>
  );
}
