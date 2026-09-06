import { useCallback, useEffect, useState } from 'react'
import { Bell, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import notificationApi from '../../services/notificationApi'

export default function Notifications() {
  const [data, setData] = useState({ records: [], unread_count: 0 }); const navigate = useNavigate()
  const load = useCallback(() => notificationApi.list({ per_page: 10 }).then(r => setData(r.data)).catch(() => {}), [])
  useEffect(() => { load(); const t = setInterval(load, 45000); return () => clearInterval(t) }, [load])
  return <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6"><div className="flex items-center justify-between mb-6"><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[var(--primary)]"><Bell className="h-4 w-4 text-[var(--primary)]" /></div><div><h2 className="text-base font-semibold text-[var(--foreground)]">Notification Center</h2><p className="text-xs text-[var(--muted-foreground)]">{data.unread_count || 0} unread</p></div></div><button onClick={() => navigate('/dashboard/notifications')} className="text-[var(--muted-foreground)] hover:text-[var(--primary)]"><ChevronRight className="h-4 w-4" /></button></div>{data.records?.length ? <div className="space-y-3">{data.records.slice(0, 10).map(x => <button onClick={() => navigate('/dashboard/notifications')} key={x.id} className="block w-full rounded border border-[var(--border)] bg-[var(--background)] p-3 text-left hover:border-[var(--border)]"><div className="flex justify-between gap-3"><span className="truncate text-xs font-medium text-[var(--foreground)]">{x.title}</span><span className={`text-[10px] ${x.severity === 'Critical' ? 'text-red-300' : x.severity === 'High' ? 'text-orange-300' : 'text-[var(--muted-foreground)]'}`}>{x.severity}</span></div><p className="mt-1 truncate text-xs text-[var(--muted-foreground)]">{x.description}</p></button>)}</div> : <div className="flex items-center justify-center py-8"><p className="text-sm text-[var(--muted-foreground)]">No notifications available.</p></div>}</div>
}
