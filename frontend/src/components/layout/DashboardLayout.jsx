import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { Bell } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import notificationApi from '../../services/notificationApi'

export default function DashboardLayout() {
  const [unread, setUnread] = useState(0)
  const navigate = useNavigate()
  useEffect(() => { const load = () => notificationApi.unread().then(r => setUnread(r.data.unread_count || 0)).catch(() => {}); load(); const timer = setInterval(load, 45000); return () => clearInterval(timer) }, [])
  return (
    <div className="flex h-screen overflow-hidden bg-slate-950">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        <div className="flex justify-end border-b border-slate-800 px-5 py-3 lg:px-7"><button onClick={() => navigate('/dashboard/notifications')} className="relative text-slate-400 hover:text-sky-300" aria-label="Notifications"><Bell className="h-5 w-5" />{unread > 0 && <span className="absolute -right-2 -top-2 min-w-4 rounded-full bg-red-500 px-1 text-center text-[10px] text-white">{unread > 99 ? '99+' : unread}</span>}</button></div>
        <div className="p-5 lg:p-7 max-w-[1600px] mx-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
