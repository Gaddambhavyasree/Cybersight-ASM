import OverviewCards from '../../components/dashboard/OverviewCards'
import QuickActions from '../../components/dashboard/QuickActions'
import RecentScans from '../../components/dashboard/RecentScans'
import AttackSurfaceInsights from '../../components/dashboard/AttackSurfaceInsights'
import ScanWorkflow from '../../components/dashboard/ScanWorkflow'
import FeatureGrid from '../../components/dashboard/FeatureGrid'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* Executive hero */}
      <div className="card p-6 lg:p-8 overflow-hidden relative">
        <div className="absolute inset-0 bg-gradient-to-br from-[var(--primary)]/[0.06] via-transparent to-transparent pointer-events-none" />
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-[var(--primary)]/10 blur-2xl hidden lg:block" />
        <div className="relative">
          <p className="text-[11px] font-extrabold uppercase tracking-[0.2em] text-[var(--primary)]">CyberSight ASM</p>
          <h1 className="mt-1 text-2xl lg:text-[28px] font-extrabold tracking-tight text-[var(--foreground)]">Attack Surface Management Platform</h1>
          <p className="mt-2 text-sm font-medium text-[var(--muted-foreground)]">
            Discover <span className="text-[var(--primary)]">•</span> Assess <span className="text-[var(--primary)]">•</span> Prioritize <span className="text-[var(--primary)]">•</span> Protect
          </p>
          <p className="mt-3 text-sm leading-relaxed text-[var(--muted-foreground)] max-w-3xl">
            End-to-end visibility across external assets, exposures, and risk — designed for SOC, threat analysts, and executives. All metrics below are sourced from live backend APIs.
          </p>
        </div>
      </div>

      <OverviewCards />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <RecentScans />
        <QuickActions />
      </div>

      <ScanWorkflow />
      <FeatureGrid />
      <AttackSurfaceInsights />
    </div>
  )
}
