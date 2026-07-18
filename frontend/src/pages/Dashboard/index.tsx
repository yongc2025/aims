import { useEffect, useState } from 'react';
import { MetricCard } from '../../components/cards/MetricCard';
import { ChartPanel } from '../../components/charts/ChartPanel';
import LineChart from '../../components/charts/LineChart';
import HeatMap from '../../components/charts/HeatMap';
import { getMarket, getMarginTrend, getSentimentTrend, getSectorTrend } from '../../api/aims';

interface DashboardData {
  turnover?: string;
  upCount?: string;
  downCount?: string;
  limitUp?: string;
  limitDown?: string;
}

export default function Dashboard() {
  const [market, setMarket] = useState<DashboardData>({});
  const [margin, setMargin] = useState([]);
  const [sentiment, setSentiment] = useState([]);
  const [sectors, setSectors] = useState([]);

  useEffect(() => {
    async function loadDashboard() {
      const today = new Date().toISOString().slice(0, 10);

      const [market