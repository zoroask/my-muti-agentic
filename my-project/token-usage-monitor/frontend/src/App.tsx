import { useState, useCallback, useEffect } from 'react'
import FilterBar from './components/FilterBar'
import TokenCard from './components/TokenCard'
import DistributionChart from './components/DistributionChart'
import TokenTable from './components/TokenTable'
import ToastMessage from './components/ToastMessage'
import type { SummaryResponse, TabId, ToastData, RefreshResponse } from './types'

const API_BASE = ''

const TABS: Array<{ id: TabId; label: string; endpoint: string }> = [
  { id: 'overview', label: 'Overview', endpoint: '/api/summary' },
  { id: 'by-agent', label: 'By Agent', endpoint: '/api/by-agent' },
  { id: 'by-skill', label: 'By Skill', endpoint: '/api/by-skill' },
  { id: 'by-command', label: 'By Command', endpoint: '/api/by-command' },
]

function getDefaultDates(): { start: string; end: string } {
  const pad = (n: number) => String(n).padStart(2, '0')
  const fmt = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
  const end = new Date()
  const start = new Date(end)
  start.setDate(start.getDate() - 29)
  return { start: fmt(start), end: fmt(end) }
}

export default function App() {
  const defaults = getDefaultDates()

  const [activeTab, setActiveTab] = useState<TabId>('overview')
  const [startDate, setStartDate] = useState(defaults.start)
  const [endDate, setEndDate] = useState(defaults.end)
  const [data, setData] = useState<SummaryResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [toasts, setToasts] = useState<ToastData[]>([])

  const addToast = useCallback((variant: ToastData['variant'], message: string) => {
    const id = String(Date.now())
    setToasts(prev => [...prev, { id, variant, message }])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const fetchData = useCallback(async (tab: TabId, start: string, end: string) => {
    const endpoint = TABS.find(t => t.id === tab)?.endpoint
    if (!endpoint) return
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({ start, end })
      const res = await fetch(`${API_BASE}${endpoint}?${params}`)
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const json: SummaryResponse = await res.json()
      setData(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data')
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const { start, end } = getDefaultDates()
    fetchData('overview', start, end)
  }, [fetchData])

  const handleTabChange = useCallback(
    (tab: TabId) => {
      setActiveTab(tab)
      fetchData(tab, startDate, endDate)
    },
    [fetchData, startDate, endDate],
  )

  const handleDateChange = useCallback(
    (start: string, end: string) => {
      setStartDate(start)
      setEndDate(end)
      fetchData(activeTab, start, end)
    },
    [fetchData, activeTab],
  )

  const handleRefresh = useCallback(async () => {
    setRefreshing(true)
    try {
      const res = await fetch(`${API_BASE}/api/refresh`, { method: 'POST' })
      if (!res.ok) throw new Error(`Server error: ${res.status}`)
      const json: RefreshResponse = await res.json()
      if (json.status === 'ok') {
        addToast('success', `Refresh complete. ${json.sessions_scanned} sessions scanned.`)
      } else {
        addToast(
          'warning',
          `Refresh partial. ${json.sessions_scanned} sessions scanned, ${json.errors.length} error(s).`,
        )
      }
      await fetchData(activeTab, startDate, endDate)
    } catch (err) {
      addToast('error', err instanceof Error ? err.message : 'Refresh failed')
    } finally {
      setRefreshing(false)
    }
  }, [fetchData, addToast, activeTab, startDate, endDate])

  return (
    <div className="min-h-screen bg-bg text-text font-sans">
      <header className="flex items-center justify-between px-6 py-3 border-b border-border bg-surface">
        <h1 className="text-lg font-semibold tracking-tight">Token Usage Monitor</h1>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="px-4 py-1.5 bg-accent hover:bg-accent-hover disabled:opacity-50 disabled:cursor-not-allowed rounded-btn text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2 focus:ring-offset-bg"
        >
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </header>

      <nav
        role="tablist"
        aria-label="Dashboard views"
        className="flex border-b border-border bg-surface px-6"
      >
        {TABS.map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => handleTabChange(tab.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-inset ${
              activeTab === tab.id
                ? 'border-accent text-accent'
                : 'border-transparent text-muted hover:text-text hover:border-surface-raised'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="px-6 py-4 space-y-4">
        <FilterBar
          startDate={startDate}
          endDate={endDate}
          onDateChange={handleDateChange}
          disabled={refreshing || loading}
        />

        <div className="grid grid-cols-4 gap-3">
          <TokenCard label="Input Tokens" value={data?.total.input ?? null} loading={loading} />
          <TokenCard label="Output Tokens" value={data?.total.output ?? null} loading={loading} />
          <TokenCard label="Cache Read" value={data?.total.cache_read ?? null} loading={loading} />
          <TokenCard label="Cache Write" value={data?.total.cache_write ?? null} loading={loading} />
        </div>

        <DistributionChart rows={data?.rows ?? null} loading={loading} error={error} />

        <TokenTable rows={data?.rows ?? null} loading={loading} error={error} />
      </main>

      <div className="fixed bottom-4 right-4 space-y-2 z-50">
        {toasts.map(toast => (
          <ToastMessage
            key={toast.id}
            variant={toast.variant}
            message={toast.message}
            onDismiss={() => removeToast(toast.id)}
          />
        ))}
      </div>
    </div>
  )
}
