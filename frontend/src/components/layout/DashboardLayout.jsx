import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Header from './Header'
import { useState } from 'react'

export default function DashboardLayout() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <Header onMenuClick={() => setMobileOpen(true)} />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar
          collapsed={collapsed}
          onToggle={() => setCollapsed(v => !v)}
          mobileOpen={mobileOpen}
          onMobileClose={() => setMobileOpen(false)}
        />
        <main className="flex-1 overflow-y-auto">
          <div className="p-4 sm:p-5 lg:p-7 max-w-[1600px] mx-auto w-full">
            <Outlet />
          </div>
          <footer className="border-t border-[var(--border)] bg-[var(--card)]/50 mt-8">
            <div className="max-w-[1600px] mx-auto px-4 lg:px-7 py-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[var(--muted-foreground)]">
              <span>© {new Date().getFullYear()} CyberSight ASM — Attack Surface Management Platform</span>
              <span className="hidden sm:inline">Discover • Assess • Prioritize • Protect</span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  )
}
