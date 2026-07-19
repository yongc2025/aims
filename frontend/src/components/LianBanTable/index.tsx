import { useMemo } from 'react';
import { Table, ConfigProvider, theme } from 'antd';
import type { ColumnsType } from 'antd/es/table';

export interface LianBanRow {
  key: string;
  name: string;
  code: string;
  boardCount: string;
  detail: string;
  industry: string;
  reason: string;
}

interface LianBanTableProps {
  data?: LianBanRow[];
}

export default function LianBanTable({ data = [] }: LianBanTableProps) {
  const tableData = data;
  const columns: ColumnsType<LianBanRow> = useMemo(
    () => [
      {
        title: '股票名称',
        dataIndex: 'name',
        key: 'name',
        width: 90,
        render: (text: string) => (
          <span className="text-white/90 text-sm font-medium">{text}</span>
        ),
      },
      {
        title: '代码',
        dataIndex: 'code',
        key: 'code',
        width: 80,
        render: (text: string) => (
          <span className="font-mono text-xs tabular-nums text-white/50">{text}</span>
        ),
      },
      {
        title: '连板数',
        dataIndex: 'boardCount',
        key: 'boardCount',
        width: 80,
        render: (text: string) => (
          <span className="font-mono text-sm font-bold tabular-nums" style={{ color: '#FF5252' }}>
            {text}
          </span>
        ),
      },
      {
        title: (
          <span title="例如 7天6板：近 7 个交易日内出现 6 次涨停；连板数表示当前连续涨停天数。">
            涨停统计
          </span>
        ),
        dataIndex: 'detail',
        key: 'detail',
        width: 100,
        render: (text: string) => (
          <span className="font-mono text-xs tabular-nums text-aims-warn">{text}</span>
        ),
      },
      {
        title: '所属行业',
        dataIndex: 'industry',
        key: 'industry',
        width: 90,
        render: (text: string) => (
          <span className="text-white/55 text-xs">{text}</span>
        ),
      },
      {
        title: '涨停原因',
        dataIndex: 'reason',
        key: 'reason',
        render: (text: string) => (
          <span className="text-white/40 text-xs">{text}</span>
        ),
      },
    ],
    []
  );

  return (
    <div className="card flex h-[330px] min-w-0 flex-col overflow-hidden rounded-lg border border-aims-border bg-aims-card">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-aims-border">
        <div className="flex items-center gap-2">
          <span className="text-white text-sm font-semibold">连板股票明细</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-bold text-white bg-aims-down/20">
            {tableData.length}只
          </span>
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
          rowClassName={() => 'aims-table-row'}
          className="aims-lianban-table"
          style={{ background: 'transparent' }}
          scroll={{ x: 620, y: 235 }}
        />
      </ConfigProvider>
    </div>
  );
}
