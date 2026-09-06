import { AlertTriangle } from 'lucide-react'

export default function EmptyState({ icon: Icon = AlertTriangle, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center px-4">
      <div className="w-14 h-14 rounded-2xl bg-[var(--muted)] border border-[var(--border)] flex items-center justify-center mb-4">
        <Icon className="h-7 w-7 text-[var(--muted-foreground)]" />
      </div>
      <h3 className="text-base font-bold text-[var(--foreground)] mb-1">{title}</h3>
      {description && <p className="text-sm text-[var(--muted-foreground)] max-w-md leading-relaxed">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
