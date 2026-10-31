interface FilterBarProps {
  startDate: string
  endDate: string
  onDateChange: (start: string, end: string) => void
  disabled: boolean
}

export default function FilterBar({ startDate, endDate, onDateChange, disabled }: FilterBarProps) {
  return (
    <div className="flex items-center gap-3 text-sm py-1">
      <span className="text-muted font-medium">Date Range:</span>
      <input
        type="date"
        value={startDate}
        onChange={e => onDateChange(e.target.value, endDate)}
        disabled={disabled}
        aria-label="Start date"
        className="bg-surface border border-border rounded px-2 py-1 text-text focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      />
      <span className="text-muted select-none" aria-hidden="true">&rarr;</span>
      <input
        type="date"
        value={endDate}
        onChange={e => onDateChange(startDate, e.target.value)}
        disabled={disabled}
        aria-label="End date"
        className="bg-surface border border-border rounded px-2 py-1 text-text focus:outline-none focus:ring-2 focus:ring-accent disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
      />
    </div>
  )
}
