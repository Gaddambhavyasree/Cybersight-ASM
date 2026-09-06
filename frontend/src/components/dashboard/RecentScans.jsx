import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Radar, Server, ArrowUpRight } from 'lucide-react'
import scanApi from '../../services/scanApi'
import { StatusBadge } from '../ui/StatusBadge'

const STAGE_LABELS = {
  waiting: 'Waiting',
  asset_discovery: 'Asset Discovery',
  live_host_detection: 'Live Host Verification',
  port_scanning: 'Port Discovery',
  technology_detection: 'Technology Detection',
  dns_intelligence: 'DNS Intelligence',
  ssl_analysis: 'SSL Analysis',
  web_crawling: 'Web Crawling',
  vulnerability_assessment: 'Vulnerability Assessment',
  threat_intelligence: 'Threat Intelligence',
  risk_assessment: 'Risk Assessment',
  completed: 'Completed',
}

const POLL_INTERVAL = 5000

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function RecentScans() {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()
  const pollRef = useRef(null)

  const fetchRecent = async () => {
    try {
      const res = await scanApi.list({ page: 1, per_page: 5 })
      setScans(res.data.scans)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchRecent() }, [])

  useEffect(() => {
    const hasActive = scans.some((s) => ['pending', 'queued', 'running'].includes(s.status))
    if (hasActive) pollRef.current = setInterval(fetchRecent, POLL_INTERVAL)
    return () => { if (pollRef.current) { clearInterval(pollRef.current); pollRef.current = null } }
  }, [scans])

  return (
    <div className="card p-0 overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border)]">
        <div>
          <h2 className="text-sm font-bold tracking-tight text-[var(--foreground)]">Recent Scan Activity</h2>
          <p className="text-xs text-[var(--muted-foreground)] mt-0.5">Latest 5 executions across all projects</p>
        </div>
        <button onClick={() => navigate('/dashboard/scans')} className="inline-flex items-center gap-1 text-xs font-semibold text-[var(--primary)] hover:opacity-80">
          View All <ArrowUpRight className="h-3 w-3" />
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[var(--primary)]" />
        </div>
      ) : scans.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center px-6">
          <div className="h-12 w-12 rounded-2xl bg-[var(--muted)] border border-[var(--border)] flex items-center justify-center mb-3">
            <Radar className="h-6 w-6 text-[var(--muted-foreground)]" />
          </div>
          <p className="text-sm font-medium text-[var(--foreground)]">No scans yet</p>
          <p className="text-xs text-[var(--muted-foreground)] mt-1">Start a scan to populate this timeline.</p>
          <button onClick={() => navigate('/dashboard/scans')} className="btn-primary mt-4 text-sm">Start Scan</button>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] font-bold uppercase tracking-widest text-[var(--muted-foreground)] border-b border-[var(--border)] bg-[var(--muted)]/40">
                <th className="px-6 py-3 font-bold">Scan</th>
                <th className="py-3 font-bold">Project</th>
                <th className="py-3 font-bold">Stage</th>
                <th className="py-3 font-bold">Status</th>
                <th className="py-3 font-bold">Assets</th>
                <th className="py-3 font-bold">Progress</th>
                <th className="py-3 font-bold">Started</th>
                <th className="px-6 py-3 font-bold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[var(--border)]">
              {scans.map((scan) => (
                <tr key={scan.id} className="hover:bg-[var(--muted)]/50 transition-colors">
                  <td className="px-6 py-3.5 font-semibold text-[var(--foreground)] max-w-[180px] truncate">{scan.scan_name}</td>
                  <td className="py-3.5 text-xs text-[var(--muted-foreground)] truncate max-w-[120px]">{scan.project_name || '--'}</td>
                  <td className="py-3.5 text-xs font-medium">
                    {scan.status === 'running' || scan.status === 'queued' ? (
                      <span className="text-[var(--primary)]">{STAGE_LABELS[scan.current_stage] || scan.current_stage || '--'}</span>
                    ) : scan.status === 'completed' ? (
                      <span className="text-emerald-600 dark:text-emerald-400">Completed</span>
                    ) : scan.status === 'failed' ? (
                      <span className="text-red-600 dark:text-red-400">Failed</span>
                    ) : (
                      <span className="text-[var(--muted-foreground)]">{STAGE_LABELS[scan.current_stage] || scan.current_stage || '--'}</span>
                    )}
                  </td>
                  <td className="py-3.5"><StatusBadge status={scan.status} /></td>
                  <td className="py-3.5">
                    <div className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--card)] px-2.5 py-1 text-xs">
                      <Server className="h-3 w-3 text-[var(--muted-foreground)]" />
                      <span className="font-medium text-[var(--foreground)]">{scan.assets_count || 0}</span>
                    </div>
                  </td>
                  <td className="py-3.5">
                    <div className="flex items-center gap-2 min-w-[110px]">
                      <div className="flex-1 h-1.5 bg-[var(--muted)] rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${scan.status === 'failed' ? 'bg-red-500' : scan.status === 'cancelled' ? 'bg-amber-500' : 'bg-[var(--primary)]'}`}
                          style={{ width: `${scan.progress ?? 0}%` }}
                        />
                      </div>
                      <span className="text-xs font-medium text-[var(--muted-foreground)] w-8 text-right">{scan.progress ?? 0}%</span>
                    </div>
                  </td>
                  <td className="py-3.5 text-xs text-[var(--muted-foreground)] whitespace-nowrap">{formatDate(scan.started_at)}</td>
                  <td className="px-6 py-3.5">
                    <button onClick={() => navigate('/dashboard/scans')} className="text-xs font-semibold text-[var(--primary)] hover:opacity-80 border border-[var(--border)] bg-[var(--card)] rounded-full px-3 py-1">
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
