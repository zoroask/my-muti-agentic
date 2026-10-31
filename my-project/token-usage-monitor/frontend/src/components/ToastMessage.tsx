import { useEffect } from 'react'
import { CheckCircle2, AlertTriangle, XCircle, X } from 'lucide-react'

type ToastVariant = 'success' | 'warning' | 'error'

interface ToastMessageProps {
  variant: ToastVariant
  message: string
  onDismiss: () => void
}

type LucideIcon = typeof CheckCircle2

interface VariantConfig {
  Icon: LucideIcon
  borderClass: string
  iconClass: string
  srLabel: string
}

const VARIANT_CONFIG: Record<ToastVariant, VariantConfig> = {
  success: { Icon: CheckCircle2, borderClass: 'border-l-success', iconClass: 'text-success', srLabel: 'Success' },
  warning: { Icon: AlertTriangle, borderClass: 'border-l-warning', iconClass: 'text-warning', srLabel: 'Warning' },
  error: { Icon: XCircle, borderClass: 'border-l-danger', iconClass: 'text-danger', srLabel: 'Error' },
}

const DISMISS_DELAY_MS = 5000

export default function ToastMessage({ variant, message, onDismiss }: ToastMessageProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, DISMISS_DELAY_MS)
    return () => clearTimeout(timer)
  }, [onDismiss])

  const { Icon, borderClass, iconClass, srLabel } = VARIANT_CONFIG[variant]

  return (
    <div
      role="alert"
      aria-atomic="true"
      className={`flex items-start gap-3 px-4 py-3 rounded-card border-l-4 bg-surface-raised shadow-lg min-w-[280px] max-w-sm ${borderClass}`}
    >
      <Icon size={16} className={`mt-0.5 flex-shrink-0 ${iconClass}`} aria-hidden="true" />
      <div className="flex-1 min-w-0">
        <span className="sr-only">{srLabel}: </span>
        <p className="text-sm text-text leading-snug">{message}</p>
      </div>
      <button
        onClick={onDismiss}
        className="flex-shrink-0 text-muted hover:text-text transition-colors focus:outline-none focus:ring-2 focus:ring-accent rounded"
        aria-label="Dismiss notification"
      >
        <X size={14} aria-hidden="true" />
      </button>
    </div>
  )
}
