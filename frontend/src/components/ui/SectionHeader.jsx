export default function SectionHeader({ eyebrow, title, subtitle, action }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
      <div className="min-w-0">
        {eyebrow && (
          <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--primary)]">{eyebrow}</p>
        )}
        {title && <h1 className="mt-1 text-2xl font-bold tracking-tight text-[var(--foreground)]">{title}</h1>}
        {subtitle && <p className="mt-1.5 text-sm leading-relaxed text-[var(--muted-foreground)] max-w-2xl">{subtitle}</p>}
      </div>
      {action && <div className="flex-shrink-0">{action}</div>}
    </div>
  )
}
