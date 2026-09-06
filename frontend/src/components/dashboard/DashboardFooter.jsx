export default function DashboardFooter() {
  return (
    <footer className="border-t border-[var(--border)] pt-6 pb-2">
      <div className="flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[var(--muted-foreground)]">
        <span className="font-semibold text-[var(--muted-foreground)]">CyberSight ASM</span>
        <span>Attack Surface Management Platform</span>
        <span>Version 1.0</span>
      </div>
    </footer>
  )
}
