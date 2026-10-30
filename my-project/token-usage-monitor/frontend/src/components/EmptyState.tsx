import { RefreshCw, AlertTriangle } from 'lucide-react'

interface EmptyStateProps {
  variant: 'no-data' | 'scan-error'
}

export default function EmptyState({ variant }: EmptyStateProps) {
  if (variant === 'scan-error') {
    return (
      <div className="flex flex-col items-center gap-2 py-6 text-center">
        <AlertTriangle size={24} className="text-danger" aria-hidden="true" />
        <p className="text-sm font-medium text-text">Failed to load data</p>
        <p className="text-xs text-muted">
          Check that the backend is running at{' '}
          <code className="font-mono bg-surface px-1 py-0.5 rounded text-danger">
            http://localhost:8000
          </code>
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center gap-2 py-6 text-center">
      <RefreshCw size={24} className="text-muted" aria-hidden="true" />
      <p className="text-sm font-medium text-text">No data available</p>
      <p className="text-xs text-muted">Click Refresh to scan .jsonl transcript files</p>
    </div>
  )
}
