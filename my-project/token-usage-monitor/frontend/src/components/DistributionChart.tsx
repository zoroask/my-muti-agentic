import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Tooltip,
  Legend,
} from 'chart.js'
import type { ChartOptions, ChartData, TooltipItem } from 'chart.js'
import { Bar } from 'react-chartjs-2'
import type { TokenRow } from '../types'
import EmptyState from './EmptyState'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

interface DistributionChartProps {
  rows: TokenRow[] | null
  loading: boolean
  error: string | null
}

const BAR_HEIGHT_PX = 32
const MIN_CHART_HEIGHT_PX = 200
const CHART_PADDING_PX = 40

function buildChartData(rows: TokenRow[]): ChartData<'bar'> {
  return {
    labels: rows.map(r => r.name),
    datasets: [
      {
        label: 'Total Tokens',
        data: rows.map(r => r.input + r.output + r.cache_read + r.cache_write),
        backgroundColor: '#3b82f6',
        hoverBackgroundColor: '#2563eb',
        borderRadius: 3,
        borderSkipped: false as const,
      },
    ],
  }
}

const CHART_OPTIONS: ChartOptions<'bar'> = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      callbacks: {
        label: (ctx: TooltipItem<'bar'>) => ` ${ctx.parsed.x.toLocaleString()} tokens`,
      },
    },
  },
  scales: {
    x: {
      ticks: { color: '#94a3b8', font: { size: 11 } },
      grid: { color: '#334155' },
    },
    y: {
      ticks: { color: '#94a3b8', font: { size: 11 } },
      grid: { display: false },
    },
  },
}

export default function DistributionChart({ rows, loading, error }: DistributionChartProps) {
  if (loading) {
    return (
      <div className="bg-surface rounded-card p-4 border border-border">
        <div className="h-5 w-28 bg-surface-raised animate-pulse rounded mb-4" aria-hidden="true" />
        <div className="h-48 bg-surface-raised animate-pulse rounded" aria-hidden="true" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-surface rounded-card p-4 border border-border">
        <EmptyState variant="scan-error" />
      </div>
    )
  }

  if (!rows || rows.length === 0) {
    return (
      <div className="bg-surface rounded-card p-4 border border-border">
        <EmptyState variant="no-data" />
      </div>
    )
  }

  const chartHeight = Math.max(MIN_CHART_HEIGHT_PX, rows.length * BAR_HEIGHT_PX + CHART_PADDING_PX)

  return (
    <div className="bg-surface rounded-card p-4 border border-border">
      <h2 className="text-xs text-muted uppercase tracking-wider font-medium mb-4">Distribution</h2>
      <div
        role="img"
        aria-label={`Horizontal bar chart: total token usage per entry. ${rows.length} ${rows.length === 1 ? 'entry' : 'entries'} shown.`}
        style={{ height: `${chartHeight}px` }}
      >
        <Bar data={buildChartData(rows)} options={CHART_OPTIONS} />
      </div>
    </div>
  )
}
