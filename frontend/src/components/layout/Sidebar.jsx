import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import {
  LayoutDashboard, FolderOpen, Radar, Server, Lock, Code2,
  Globe, ShieldCheck, Globe2, Bug, Crosshair, Gauge,
  Clock, FileText, Bell, Settings, Users, LogOut,
  ChevronLeft, ChevronRight
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

export default function Sidebar() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside
      className={`bg-slate-900 border-r border-slate-800 flex flex-col transition-all duration-300 ${
        collapsed ? 'w-[68px]' : 'w-64'
      }`}
    >
      <div className="h-14 flex items-center justify-between px-3 border-b border-slate-800 flex-shrink-0">
        {!collapsed && (
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center flex-shrink-0">
              <ShieldCheck className="h-4.5 w-4.5 text-slate-950" />
            </div>
            <span className="font-bold text-sm text-slate-100 truncate">CyberSight</span>
          </div>
        )}
        {collapsed && (
          <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center mx-auto">
            <ShieldCheck className="h-4.5 w-4.5 text-slate-950" />
          </div>
        )}
        {!collapsed && (
          <button
            onClick={() => setCollapsed(true)}
            className="text-slate-500 hover:text-slate-300 p-1 rounded flex-shrink-0"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
        )}
      </div>

      {collapsed && (
        <button
          onClick={() => setCollapsed(false)}
          className="text-slate-500 hover:text-slate-300 p-2 flex justify-center border-b border-slate-800"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      )}

      <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-5">
        {navSections.map((section) => (
          <div key={section.label}>
            {!collapsed && (
              <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                {section.label}
              </p>
            )}
            <div className="space-y-0.5">
              {section.items.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.end}
                  className={({ isActive }) =>
                    `flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                      isActive
                        ? 'bg-sky-500/10 text-sky-400'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
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
              <p className="px-3 mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-slate-600">
                Admin
              </p>
            )}
            <NavLink
              to="/dashboard/admin/users"
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-colors ${
                  isActive
                    ? 'bg-sky-500/10 text-sky-400'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
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

      <div className="p-2 border-t border-slate-800 flex-shrink-0">
        {!collapsed && (
          <div className="px-3 py-2 mb-1">
            <p className="text-xs font-medium text-slate-300 truncate">{user?.full_name}</p>
            <p className="text-[11px] text-slate-600 truncate">{user?.email}</p>
          </div>
        )}
        <NavLink
          to="/dashboard/profile"
          className={({ isActive }) =>
            `flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-[13px] font-medium transition-colors ${
              isActive
                ? 'bg-sky-500/10 text-sky-400'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            } ${collapsed ? 'justify-center' : ''}`
          }
          title={collapsed ? 'Profile' : undefined}
        >
          <Users className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Profile</span>}
        </NavLink>
        <button
          onClick={handleLogout}
          className={`flex items-center gap-2.5 w-full px-3 py-2 rounded-lg text-[13px] font-medium text-slate-400 hover:text-red-400 hover:bg-slate-800/60 transition-colors ${
            collapsed ? 'justify-center' : ''
          }`}
          title={collapsed ? 'Logout' : undefined}
        >
          <LogOut className="h-4 w-4 flex-shrink-0" />
          {!collapsed && <span>Logout</span>}
        </button>
      </div>
    </aside>
  )
}
