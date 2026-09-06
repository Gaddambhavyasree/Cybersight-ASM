const STATUS_MAP = {
  pending: 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]',
  queued: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-950/40 dark:text-blue-300 dark:border-blue-900',
  running: 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-900',
  completed: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900',
  failed: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900',
  cancelled: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900',
}

const SEVERITY_MAP = {
  critical: 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/40 dark:text-red-300 dark:border-red-900',
  high: 'bg-orange-50 text-orange-700 border-orange-200 dark:bg-orange-950/40 dark:text-orange-300 dark:border-orange-900',
  medium: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900',
  low: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900',
  info: 'bg-sky-50 text-sky-700 border-sky-200 dark:bg-sky-950/40 dark:text-sky-300 dark:border-sky-900',
  unknown: 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]',
}

export function StatusBadge({ status }) {
  const key = String(status || '').toLowerCase()
  const cls = STATUS_MAP[key] || STATUS_MAP.pending
  const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : '--'
  return <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold border ${cls}`}>{label}</span>
}

export function SeverityBadge({ severity }) {
  const key = String(severity || '').toLowerCase()
  const cls = SEVERITY_MAP[key] || 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]'
  const label = severity ? severity.charAt(0).toUpperCase() + severity.slice(1) : '--'
  return <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-[11px] font-bold border ${cls}`}>{label}</span>
}

export default StatusBadge
