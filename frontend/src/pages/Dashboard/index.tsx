import { MetricCard } from '../../components/cards/MetricCard';
import { ChartPanel } from '../../components/charts/ChartPanel';

export default function Dashboard() {
  return (
    <div className="aims-dashboard">
      <div className="dashboard-header">
        <h1>AIMS Dashboard</h1>
        <p>AI Market Intelligence System</p>
      </div>

      <div className="metric-grid">
        <MetricCard title="成交额" value="--" />
        <MetricCard title="上涨数量" value="--" />
        <