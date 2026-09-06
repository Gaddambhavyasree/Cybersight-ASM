export default function SectionPage({ title, description }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-[var(--foreground)]">{title}</h1>
        {description && <p className="text-sm text-[var(--muted-foreground)] mt-1.5 max-w-2xl">{description}</p>}
      </div>
      <div className="card flex flex-col items-center justify-center py-20 text-center">
        <div className="h-12 w-12 rounded-2xl bg-[var(--muted)] border border-[var(--border)] flex items-center justify-center mb-3">
          <span className="text-[var(--muted-foreground)] text-lg">◐</span>
        </div>
        <p className="text-sm font-medium text-[var(--foreground)]">This section is under development.</p>
        <p className="text-xs text-[var(--muted-foreground)] mt-1 max-w-md">Real data wiring is preserved — UI will be upgraded in the next iteration.</p>
      </div>
    </div>
  )
}
