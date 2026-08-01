import OverviewCards from '../../components/dashboard/OverviewCards'
import QuickActions from '../../components/dashboard/QuickActions'
import RecentScans from '../../components/dashboard/RecentScans'
import AttackSurfaceInsights from '../../components/dashboard/AttackSurfaceInsights'

export default function DashboardPage() {
  return <div className="space-y-6"><div><p className="text-xs uppercase tracking-[0.2em] text-sky-400">CyberSight ASM</p><h1 className="mt-1 text-2xl font-bold text-slate-100">Attack Surface Overview</h1><p className="mt-1 text-sm text-slate-400">A concise, data-driven view of your organization’s external exposure.</p></div><OverviewCards /><div className="grid gap-6 lg:grid-cols-[1fr_320px]"><RecentScans /><QuickActions /></div><AttackSurfaceInsights /></div>
}
