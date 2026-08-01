import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { Radar, Server } from 'lucide-react'
import scanApi from '../../services/scanApi'

const STATUS_STYLES = {
  pending: 'bg-slate-500/10 text-slate-400',
  queued: 'bg-blue-500/10 text-blue-400',
  running: 'bg-sky-500/10 text-sky-400',
  completed: 'bg-emerald-500/10 text-emerald-400',
  failed: 'bg-red-500/10 text-red-400',
  cancelled: 'bg-amber-500/10 text-amber-400',
}

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
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchRecent()
  }, [])

  useEffect(() => {
    const hasActiveScans = scans.some(
      (s) => ['pending', 'queued', 'running'].includes(s.status)
    )

    if (hasActiveScans) {
      pollRef.current = setInterval(fetchRecent, POLL_INTERVAL)
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [scans])

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-base font-semibold text-slate-100">Recent Scan Activity</h2>
        <button
          onClick={() => navigate('/dashboard/scans')}
          className="text-xs text-sky-400 hover:text-sky-300 transition-colors"
        >
          View All
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-sky-500" />
        </div>
      ) : scans.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <Radar className="h-8 w-8 text-slate-700 mb-3" />
          <p className="text-slate-600 text-sm">No scans available.</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-slate-800">
                <th className="pb-3 font-medium">Scan</th>
                <th className="pb-3 font-medium">Project</th>
                <th className="pb-3 font-medium">Stage</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium">Assets</th>
                <th className="pb-3 font-medium">Progress</th>
                <th className="pb-3 font-medium">Started</th>
                <th className="pb-3 font-medium">Completed</th>
                <th className="pb-3 font-medium">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {scans.map((scan) => (
                <tr key={scan.id} className="hover:bg-slate-800/20">
                  <td className="py-3 text-slate-200 font-medium">{scan.scan_name}</td>
                  <td className="py-3 text-slate-400 text-xs">{scan.project_name || '--'}</td>
                  <td className="py-3 text-xs">
                    {scan.status === 'running' || scan.status === 'queued' ? (
                      <span className="text-sky-400 font-medium">
                        {STAGE_LABELS[scan.current_stage] || scan.current_stage}
                      </span>
                    ) : scan.status === 'completed' ? (
                      <span className="text-emerald-400">Completed</span>
                    ) : scan.status === 'failed' ? (
                      <span className="text-red-400">Failed</span>
                    ) : scan.status === 'cancelled' ? (
                      <span className="text-amber-400">Cancelled</span>
                    ) : (
                      <span className="text-slate-500">
                        {STAGE_LABELS[scan.current_stage] || scan.current_stage}
                      </span>
                    )}
                  </td>
                  <td className="py-3">
                    <span className={`text-xs font-medium px-2 py-0.5 rounded ${STATUS_STYLES[scan.status] || STATUS_STYLES.pending}`}>
                      {scan.status?.charAt(0).toUpperCase() + scan.status?.slice(1)}
                    </span>
                  </td>
                  <td className="py-3">
                    <div className="flex items-center gap-1.5">
                      <Server className="h-3 w-3 text-slate-500" />
                      <span className="text-xs text-slate-400">{scan.assets_count || 0}</span>
                    </div>
                  </td>
                  <td className="py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            scan.status === 'failed' ? 'bg-red-500' :
                            scan.status === 'cancelled' ? 'bg-amber-500' :
                            'bg-sky-500'
                          }`}
                          style={{ width: `${scan.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-500">{scan.progress}%</span>
                    </div>
                  </td>
                  <td className="py-3 text-slate-500 text-xs">{formatDate(scan.started_at)}</td>
                  <td className="py-3 text-slate-500 text-xs">{formatDate(scan.completed_at)}</td>
                  <td className="py-3 text-sky-300 text-xs"><button onClick={() => navigate(`/dashboard/scans`)}>View</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
