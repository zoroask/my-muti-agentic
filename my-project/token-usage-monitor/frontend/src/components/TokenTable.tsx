import type { TokenRow } from '../types'
import EmptyState from './EmptyState'

interface TokenTableProps {
  rows: TokenRow[] | null
  loading: boolean
  error: string | null
}

function fmt(n: number): string {
  return n.toLocaleString()
}

const SKELETON_ROW_COUNT = 4

export default function TokenTable({ rows, loading, error }: TokenTableProps) {
  return (
    <div className="bg-surface rounded-card border border-border overflow-hidden">
      <table className="w-full text-sm" aria-label="Token usage breakdown by entry">
        <thead>
          <tr className="border-b border-border bg-surface-raised">
            <th scope="col" className="text-left px-4 py-2.5 font-medium text-muted">Name</th>
            <th scope="col" className="text-right px-4 py-2.5 font-medium text-muted">Input</th>
            <th scope="col" className="text-right px-4 py-2.5 font-medium text-muted">Output</th>
            <th scope="col" className="text-right px-4 py-2.5 font-medium text-muted">Cache Read</th>
            <th scope="col" className="text-right px-4 py-2.5 font-medium text-muted">Cache Write</th>
          </tr>
        </thead>
        <tbody>
          {loading ? (
            Array.from({ length: SKELETON_ROW_COUNT }).map((_, i) => (
              <tr key={i} className="border-b border-border last:border-0">
                {Array.from({ length: 5 }).map((_, j) => (
                  <td key={j} className="px-4 py-2.5">
                    <div
                      className={`h-4 bg-surface-raised animate-pulse rounded ${j === 0 ? 'w-32' : 'w-20 ml-auto'}`}
                      aria-hidden="true"
                    />
                  </td>
                ))}
              </tr>
            ))
          ) : error ? (
            <tr>
              <td colSpan={5} className="px-4 py-8">
                <EmptyState variant="scan-error" />
              </td>
            </tr>
          ) : !rows || rows.length === 0 ? (
            <tr>
              <td colSpan={5} className="px-4 py-8">
                <EmptyState variant="no-data" />
              </td>
            </tr>
          ) : (
            rows.map((row, i) => (
              <tr
                key={`${row.category}-${row.name}-${i}`}
                className="border-b border-border last:border-0 hover:bg-surface-raised transition-colors"
              >
                <td className="px-4 py-2.5 font-medium text-text">{row.name}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted">{fmt(row.input)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted">{fmt(row.output)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted">{fmt(row.cache_read)}</td>
                <td className="px-4 py-2.5 text-right tabular-nums text-muted">{fmt(row.cache_write)}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  )
}
