import { useMemo } from 'react';
import { Table, ConfigProvider, theme } from 'antd';
import type { ColumnsType } from 'antd/es/table';

export interface IndexRow {
  key: string;
  name: string;
  point: string;
  change: number;
  changeStr: string;
  volume: string;
  upDown: string;
}

interface IndexTableProps {
  data?: IndexRow[];
  date?: string;
}

export default function IndexTable({ data = [], date = '2026-07-17' }: IndexTableProps) {
  const tableData = data;
  const columns: ColumnsType<IndexRow> = useMemo(
    () => [
      {
        title: '指数名称',
        dataIndex: 'name',
        key: 'name',
        width: 140,
        render: (text: string) => (
          <span className="text-white/90 text-sm font-medium">{text}</span>
        ),
      },
      {
        title: '当前点位',
        dataIndex: 'point',
        key: 'point',
        width: 130,
        align: 'right',
        render: (text: string) => (
          <span className="font-mono text-sm tabular-nums text-white/85">{text}</span>
        ),
      },
      {
        title: '涨跌幅',
        dataIndex: 'changeStr',
        key: 'change',
        width: 100,
        align: 'right',
        sorter: (a, b) => a.change - b.change,
        render: (_: string, record: IndexRow) => {
          const isUp = record.change > 0;
          const color = isUp ? '#00E676' : '#FF5252';
          return (
            <span
              className="font-mono text-sm font-semibold tabular-nums"
              style={{ color }}
            >
              {record.changeStr}
            </span>
          );
        },
      },
      {
        title: '成交额',
        dataIndex: 'volume',
        key: 'volume',
        width: 120,
        align: 'right',
        render: (text: string) => (
          <span className="font-mono text-xs tabular-nums text-white/55">{text}</span>
        ),
      },
      {
        title: '涨跌比',
        dataIndex: 'upDown',
        key: 'upDown',
        width: 110,
        align: 'right',
        render: (text: string) => (
          <span className="font-mono text-xs tabular-nums text-white/45">{text}</span>
        ),
      },
    ],
    []
  );

  return (
    <div className="card flex h-[330px] min-w-0 flex-col overflow-hidden rounded-lg border border-aims-border bg-aims-card">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-aims-border">
        <span className="text-white text-sm font-semibold">指数行情</span>
        <div className="flex items-center gap-1 cursor-pointer text-white/55 hover:text-white/80 transition-colors">
          <span className="font-mono text-xs tabular-nums">{date}</span>
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
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
          className="aims-index-table"
          style={{ background: 'transparent' }}
          scroll={{ x: 560, y: 235 }}
        />
      </ConfigProvider>
    </div>
  );
}
