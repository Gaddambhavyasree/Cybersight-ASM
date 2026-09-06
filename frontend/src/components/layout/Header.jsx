import { useNavigate } from 'react-router-dom'
import { Bell, Search, ShieldCheck, Menu } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import ThemeToggle, { ThemeSwitch } from '../ui/ThemeToggle'
import { useEffect, useState } from 'react'
import notificationApi from '../../services/notificationApi'

export default function Header({ onMenuClick }) {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [unread, setUnread] = useState(0)

  useEffect(() => {
    const load = () => notificationApi.unread().then(r => setUnread(r.data.unread_count || 0)).catch(() => {})
    load()
    const t = setInterval(load, 45000)
    return () => clearInterval(t)
  }, [])

  return (
    <header className="sticky top-0 z-30 flex h-[64px] items-center justify-between gap-4 border-b border-[var(--border)] bg-[var(--card)]/95 backdrop-blur supports-[backdrop-filter]:bg-[var(--card)]/80 px-4 lg:px-6">
      <div className="flex items-center gap-3 min-w-0 flex-1">
        <button
          onClick={onMenuClick}
          className="lg:hidden inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)] hover:text-[var(--foreground)]"
          aria-label="Open navigation"
        >
          <Menu className="h-4 w-4" />
        </button>

        {/* Branding - visible on desktop within sidebar already, but keep compact on mobile/header */}
        <div className="hidden lg:flex items-center gap-3 min-w-0">
          <div className="h-9 w-9 rounded-xl bg-[var(--primary)] flex items-center justify-center shadow-sm">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
          <div className="min-w-0 leading-tight">
            <p className="text-[13px] font-extrabold tracking-tight text-[var(--foreground)]">CyberSight ASM</p>
            <p className="text-[11px] font-medium tracking-wide text-[var(--muted-foreground)] -mt-0.5">Attack Surface Management</p>
          </div>
          <span className="hidden xl:inline-flex ml-2 rounded-full bg-[var(--secondary)] border border-[var(--border)] px-2.5 py-1 text-[10px] font-semibold tracking-widest uppercase text-[var(--secondary-foreground)]">
            Discover • Assess • Prioritize • Protect
          </span>
        </div>

        {/* Mobile title */}
        <div className="lg:hidden min-w-0">
          <p className="text-sm font-bold text-[var(--foreground)]">CyberSight ASM</p>
          <p className="text-[11px] text-[var(--muted-foreground)] hidden sm:block">Attack Surface Management</p>
        </div>
      </div>

      <div className="flex items-center gap-2 lg:gap-3">
        {/* Search – decorative / future global search */}
        <div className="hidden md:flex items-center gap-2 rounded-full border border-[var(--border)] bg-[var(--muted)]/60 px-3 py-1.5 text-sm text-[var(--muted-foreground)]">
          <Search className="h-4 w-4" />
          <input
            placeholder="Search assets, scans..."
            className="hidden lg:block bg-transparent outline-none placeholder:text-[var(--muted-foreground)] text-[13px] w-[180px] xl:w-[220px]"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                const q = e.currentTarget.value.trim()
                if (q) navigate(`/dashboard/assets?search=${encodeURIComponent(q)}`)
              }
            }}
          />
          <span className="hidden lg:inline text-[10px] tracking-wide border border-[var(--border)] bg-[var(--card)] rounded px-1.5 py-0.5">↵</span>
        </div>

        <div className="hidden sm:flex items-center gap-2">
          <ThemeToggle />
        </div>
        <div className="sm:hidden">
          <ThemeSwitch />
        </div>

        <button
          onClick={() => navigate('/dashboard/notifications')}
          className="relative inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)] transition-colors"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          {unread > 0 && (
            <span className="absolute -right-1 -top-1 min-w-[18px] rounded-full bg-[#EF4444] px-1 py-0.5 text-center text-[10px] font-bold leading-none text-white border-2 border-[var(--card)]">
              {unread > 99 ? '99+' : unread}
            </span>
          )}
        </button>

        <div className="hidden sm:flex items-center gap-3 pl-3 border-l border-[var(--border)]">
          <div className="text-right leading-tight hidden lg:block">
            <p className="text-xs font-semibold text-[var(--foreground)] truncate max-w-[140px]">{user?.full_name || user?.email}</p>
            <p className="text-[11px] text-[var(--muted-foreground)] capitalize">{user?.role || 'user'}</p>
          </div>
          <div className="h-9 w-9 rounded-full bg-[var(--primary)] flex items-center justify-center text-white text-xs font-bold">
            {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
          </div>
        </div>
      </div>
    </header>
  )
}
