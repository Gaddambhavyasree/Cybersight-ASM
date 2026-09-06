import { FileText, Eye, Play, Plus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

export default function QuickActions() {
  const navigate = useNavigate()
  const actions = [
    { label: 'Start Scan', icon: Play, path: '/dashboard/scans', desc: 'Launch ASM workflow' },
    { label: 'Create Project', icon: Plus, path: '/dashboard/projects', desc: 'New target scope' },
    { label: 'Generate Report', icon: FileText, path: '/dashboard/reports', desc: 'Executive summary' },
    { label: 'View Assets', icon: Eye, path: '/dashboard/assets', desc: 'Inventory & hosts' },
  ]
  return (
    <div className="card p-5">
      <h2 className="text-sm font-bold tracking-tight text-[var(--foreground)]">Quick Actions</h2>
      <p className="text-xs text-[var(--muted-foreground)] mt-1">Frequent operations — one click away</p>
      <div className="grid grid-cols-2 gap-3 mt-4">
        {actions.map((x) => (
          <button
            key={x.label}
            onClick={() => navigate(x.path)}
            className="group flex flex-col gap-2 rounded-xl border border-[var(--border)] bg-[var(--muted)]/50 hover:bg-[var(--card)] hover:border-[var(--primary)]/20 hover:shadow-soft px-3 py-3 text-left transition-all"
          >
            <span className="h-8 w-8 rounded-lg bg-[var(--card)] border border-[var(--border)] group-hover:bg-[var(--primary)] flex items-center justify-center transition-colors">
              <x.icon className="h-4 w-4 text-[var(--primary)] group-hover:text-white" />
            </span>
            <span className="text-sm font-semibold text-[var(--foreground)] leading-none">{x.label}</span>
            <span className="text-[11px] text-[var(--muted-foreground)] leading-none">{x.desc}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
