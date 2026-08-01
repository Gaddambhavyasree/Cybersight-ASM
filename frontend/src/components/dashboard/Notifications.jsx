import { useCallback, useEffect, useState } from 'react'
import { Bell, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import notificationApi from '../../services/notificationApi'

export default function Notifications() {
  const [data, setData] = useState({ records: [], unread_count: 0 }); const navigate = useNavigate()
  const load = useCallback(() => notificationApi.list({ per_page: 10 }).then(r => setData(r.data)).catch(() => {}), [])
  useEffect(() => { load(); const t = setInterval(load, 45000); return () => clearInterval(t) }, [load])
  return <div className="rounded-xl border border-slate-800 bg-slate-900 p-6"><div className="flex items-center justify-between mb-6"><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-lg bg-sky-500/10"><Bell className="h-4 w-4 text-sky-500" /></div><div><h2 className="text-base font-semibold text-slate-100">Notification Center</h2><p className="text-xs text-slate-500">{data.unread_count || 0} unread</p></div></div><button onClick={() => navigate('/dashboard/notifications')} className="text-slate-500 hover:text-sky-300"><ChevronRight className="h-4 w-4" /></button></div>{data.records?.length ? <div className="space-y-3">{data.records.slice(0, 10).map(x => <button onClick={() => navigate('/dashboard/notifications')} key={x.id} className="block w-full rounded border border-slate-800 bg-slate-950/30 p-3 text-left hover:border-slate-700"><div className="flex justify-between gap-3"><span className="truncate text-xs font-medium text-slate-300">{x.title}</span><span className={`text-[10px] ${x.severity === 'Critical' ? 'text-red-300' : x.severity === 'High' ? 'text-orange-300' : 'text-slate-500'}`}>{x.severity}</span></div><p className="mt-1 truncate text-xs text-slate-600">{x.description}</p></button>)}</div> : <div className="flex items-center justify-center py-8"><p className="text-sm text-slate-600">No notifications available.</p></div>}</div>
}
