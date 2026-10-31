export type TabId = 'overview' | 'by-agent' | 'by-skill' | 'by-command'

export interface TokenRow {
  category: 'agent' | 'skill' | 'command' | 'main_session'
  name: string
  input: number
  output: number
  cache_read: number
  cache_write: number
}

export interface SummaryResponse {
  date_range: {
    start: string
    end: string
  }
  total: {
    input: number
    output: number
    cache_read: number
    cache_write: number
  }
  rows: TokenRow[]
}

export interface RefreshResponse {
  status: 'ok' | 'partial'
  sessions_scanned: number
  errors: Array<{
    file: string
    error: string
  }>
}

export interface ToastData {
  id: string
  variant: 'success' | 'warning' | 'error'
  message: string
}
