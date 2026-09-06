import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react'

export default function StatCard({ label, value, icon: Icon, trend, tone, description, loading }) {
  const toneClass = tone || 'text-[var(--foreground)]'
  return (
    <div className="card p-5 relative overflow-hidden group">
      <div className="absolute inset-x-0 top-0 h-[3px] bg-[var(--primary)] opacity-0 group-hover:opacity-100 transition-opacity" />
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-bold uppercase tracking-[0.12em] text-[var(--muted-foreground)]">{label}</p>
          {loading ? (
            <div className="mt-3 h-8 w-20 animate-pulse rounded-lg bg-[var(--muted)]" />
          ) : (
            <p className={`mt-2 text-[22px] font-extrabold tracking-tight leading-none truncate ${toneClass}`}>{value ?? '--'}</p>
          )}
          {description && <p className="mt-1.5 text-xs leading-snug text-[var(--muted-foreground)]">{description}</p>}
          {trend && !loading && (
            <div className={`mt-2 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold border ${trend.positive ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900' : trend.negative ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-950/30 dark:text-red-300 dark:border-red-900' : 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]'}`}>
              {trend.positive ? <ArrowUpRight className="h-3 w-3" /> : trend.negative ? <ArrowDownRight className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
              {trend.value}
            </div>
          )}
        </div>
        {Icon && (
          <div className="h-10 w-10 rounded-xl bg-[var(--secondary)] border border-[var(--border)] flex items-center justify-center flex-shrink-0">
            <Icon className="h-5 w-5 text-[var(--primary)]" />
          </div>
        )}
      </div>
    </div>
  )
}
