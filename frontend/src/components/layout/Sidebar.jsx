import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import {
  LayoutDashboard, FolderOpen, Radar, Server, Lock, Code2,
  Globe, ShieldCheck, Globe2, Bug, Crosshair, Gauge,
  Clock, FileText, Bell, Settings, Users, LogOut,
  ChevronLeft, ChevronRight, X
} from 'lucide-react'
import { useState } from 'react'

const navSections = [
  {
    label: 'Overview',
    items: [
      { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', end: true },
      { to: '/dashboard/projects', icon: FolderOpen, label: 'Projects' },
      { to: '/dashboard/scans', icon: Radar, label: 'Scans' },
    ],
  },
  {
    label: 'Discovery',
    items: [
      { to: '/dashboard/assets', icon: Server, label: 'Assets' },
      { to: '/dashboard/ports', icon: Lock, label: 'Ports' },
      { to: '/dashboard/technologies', icon: Code2, label: 'Technologies' },
    ],
  },
  {
    label: 'Intelligence',
    items: [
      { to: '/dashboard/dns', icon: Globe, label: 'DNS Intelligence' },
      { to: '/dashboard/ssl', icon: ShieldCheck, label: 'SSL Analysis' },
      { to: '/dashboard/web-crawling', icon: Globe2, label: 'Web Crawling' },
      { to: '/dashboard/vulnerabilities', icon: Bug, label: 'Vulnerabilities' },
      { to: '/dashboard/threat-intel', icon: Crosshair, label: 'Threat Intelligence' },
    ],
  },
  {
    label: 'Analysis',
    items: [
      { to: '/dashboard/risk', icon: Gauge, label: 'Risk Assessment' },
      { to: '/dashboard/history', icon: Clock, label: 'Historical Scans' },
      { to: '/dashboard/reports', icon: FileText, label: 'Reports' },
    ],
  },
  {
    label: 'System',
    items: [
      { to: '/dashboard/notifications', icon: Bell, label: 'Notifications' },
      { to: '/dashboard/settings', icon: Settings, label: 'Settings' },
    ],
  },
]

export default function Sidebar({ collapsed, onToggle, mobileOpen, onMobileClose }) {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const sidebarContent = (
    <>
      <div className="h-[64px] flex items-center justify-between px-3 border-b border-[var(--border)] flex-shrink-0 bg-[var(--card)]">
        {!collapsed ? (
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-[var(--primary)] flex items-center justify-center flex-shrink-0 shadow-sm">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <div className="leading-tight">
              <span className="font-bold text-sm text-[var(--foreground)]">CyberSight</span>
              <p className="text-[10px] font-semibold tracking-widest uppercase text-[var(--muted-foreground)] -mt-0.5">ASM Platform</p>
            </div>
          </div>
        ) : (
          <div className="w-8 h-8 rounded-xl bg-[var(--primary)] flex items-center justify-center mx-auto shadow-sm">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
        )}
        {!collapsed && (
          <button
            onClick={onToggle}
            className="hidden lg:flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--border)] bg-[var(--muted)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] transition-colors"
            aria-label="Collapse sidebar"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
        {/* Mobile close */}
        <button
          onClick={onMobileClose}
          className="lg:hidden inline-flex h-8 w-8 items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]"
          aria-label="Close navigation"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {collapsed && (
        <button
          onClick={onToggle}
          className="hidden lg:flex text-[var(--muted-foreground)] hover:text-[var(--foreground)] p-2 justify-center border-b border-[var(--border)] bg-[var(--card)]"
          aria-label="Expand sidebar"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      )}

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-5">
        {navSections.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                {section.label}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  onClick={onMobileClose}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium transition-colors ${
                      isActive
                        ? 'bg-[var(--primary)] text-white shadow-sm'
                        : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]'
                    } ${collapsed ? 'justify-center' : ''}`
                  }
                  title={collapsed ? item.label : undefined}
                >
                  <item.icon className="h-4 w-4 flex-shrink-0" />
                  {!collapsed && <span className="truncate">{item.label}</span>}
                </NavLink>
              ))}
            </div>
          </div>
        ))}

        {isAdmin && (
          <div>
            {!collapsed && (
              <p className="px-3 mb-2 text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--muted-foreground)]">
                Admin
              </p>
            )}
            <NavLink
              to="/dashboard/admin/users"
              onClick={onMobileClose}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-xl text-[13px] font-medium transition-colors ${
                  isActive
                    ? 'bg-[var(--primary)] text-white shadow-sm'
                    : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]'
                } ${collapsed ? 'justify-center' : ''}`
              }
              title={collapsed ? 'User Management' : undefined}
            >
              <Users className="h-4 w-4 flex-shrink-0" />
              {!collapsed && <span>User Management</span>}
            </NavLink>
          </div>
        )}
      </nav>

      <div className="p-2 border-t border-[var(--border)] flex-shrink-0 bg-[var(--card)]">
        {!collapsed && (
          <div className="px-3 py-2 mb-1">
            <p className="text-xs font-semibold text-[var(--foreground)] truncate">{user?.full_name}</p>
            <p className="text-[11px] text-[var(--muted-foreground)] truncate">{user?.email}</p>
            <span className="inline-flex mt-1.5 rounded-full bg-[var(--secondary)] border border-[var(--border)] px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-[var(--secondary-foreground)]">
              {user?.role}
            </span>
          </div>
        )}
        <NavLink
          to="/dashboard/profile"
          onClick={onMobileClose}
          className={({ isActive }) =>
            `flex items-center gap-2.5 w-full px-3 py-2 rounded-xl text-[13px] font-medium transition-colors ${
              isActive
                ? 'bg-[var(--secondary)] text-[var(--secondary-foreground)] border border-[var(--border)]'
                : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)]'
            } ${collapsed ? 'justify-center' : ''}`
          }
          title={collapsed ? 'Profile' : undefined}
        >
          <Users className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Profile</span>}
        </NavLink>
        <button
          onClick={handleLogout}
          className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-xl text-[13px] font-medium text-[var(--muted-foreground)] hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors ${
            collapsed ? 'justify-center' : ''
          }`}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </>
  )

  return (
    <>
      {/* Desktop sidebar */}
      <aside
        className={`hidden lg:flex bg-[var(--card)] border-r border-[var(--border)] flex-col transition-all duration-300 flex-shrink-0 ${
          collapsed ? 'w-[72px]' : 'w-[256px]'
        }`}
      >
        {sidebarContent}
      </aside>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onMobileClose} />
          <aside className="absolute left-0 top-0 h-full w-[280px] bg-[var(--card)] border-r border-[var(--border)] flex flex-col shadow-2xl">
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  )
}
