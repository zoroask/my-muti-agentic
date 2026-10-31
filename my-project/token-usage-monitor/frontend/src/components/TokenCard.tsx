interface TokenCardProps {
  label: string
  value: number | null
  loading: boolean
}

function formatNumber(n: number): string {
  return n.toLocaleString()
}

export default function TokenCard({ label, value, loading }: TokenCardProps) {
  return (
    <div className="bg-surface rounded-card p-4 border border-border">
      <div className="text-xs text-muted mb-1.5 uppercase tracking-wider font-medium">{label}</div>
      {loading ? (
        <div
          className="h-8 w-28 bg-surface-raised animate-pulse rounded"
          aria-hidden="true"
          role="presentation"
        />
      ) : (
        <div className="text-2xl font-semibold tabular-nums text-text">
          {value !== null ? formatNumber(value) : '—'}
        </div>
      )}
    </div>
  )
}
