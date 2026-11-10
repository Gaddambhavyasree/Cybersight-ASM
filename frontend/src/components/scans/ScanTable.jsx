import { Eye, Trash2, Square, Server } from 'lucide-react'
import EmptyState from '../ui/EmptyState'
import { Radar } from 'lucide-react'

const STATUS_STYLES = {
  pending: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  queued: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  running: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  completed: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  failed: 'bg-red-500/10 text-red-400 border-red-500/20',
  cancelled: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
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

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function ScanTable({ scans, loading, onView, onCancel, onDelete, onEmpty }) {
  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-sky-500" />
      </div>
    )
  }

  if (scans.length === 0) {
    return (
      <EmptyState
        icon={Radar}
        title="No scans found"
        description="No scan records available."
        action={
          <button onClick={onEmpty} className="btn-primary text-sm">
            Start New Scan
          </button>
        }
      />
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-800">
            <th className="pb-3 font-medium">Scan Name</th>
            <th className="pb-3 font-medium">Project</th>
            <th className="pb-3 font-medium">Current Stage</th>
            <th className="pb-3 font-medium">Status</th>
            <th className="pb-3 font-medium">Assets</th>
            <th className="pb-3 font-medium">Progress</th>
            <th className="pb-3 font-medium">Date</th>
            <th className="pb-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {scans.map((scan) => (
            <tr key={scan.id} className="hover:bg-slate-800/20 transition-colors">
              <td className="py-3.5">
                <p className="font-medium text-slate-200">{scan.scan_name}</p>
              </td>
              <td className="py-3.5 text-slate-400 text-xs">{scan.project_name || '--'}</td>
              <td className="py-3.5">
                {scan.status === 'running' || scan.status === 'queued' ? (
                  <span className="text-xs text-sky-400 font-medium">
                    {STAGE_LABELS[scan.current_stage] || scan.current_stage}
                  </span>
                ) : scan.status === 'failed' && scan.failure_stage ? (
                  <span className="text-xs text-red-400 font-medium">
                    Failed at {STAGE_LABELS[scan.failure_stage] || scan.failure_stage}
                  </span>
                ) : scan.status === 'completed' ? (
                  <span className="text-xs text-emerald-400 font-medium">Completed</span>
                ) : (
                  <span className="text-xs text-slate-500">
                    {STAGE_LABELS[scan.current_stage] || scan.current_stage}
                  </span>
                )}
              </td>
              <td className="py-3.5">
                <span className={`text-xs font-medium px-2 py-1 rounded-md border ${STATUS_STYLES[scan.status] || STATUS_STYLES.pending}`}>
                  {scan.status?.charAt(0).toUpperCase() + scan.status?.slice(1)}
                </span>
              </td>
              <td className="py-3.5">
                <div className="flex items-center gap-1.5">
                  <Server className="h-3.5 w-3.5 text-slate-500" />
                  <span className="text-xs text-slate-400">{scan.assets_count || 0}</span>
                </div>
              </td>
              <td className="py-3.5">
                <div className="flex items-center gap-2">
                  <div className="w-20 h-1.5 bg-slate-800 rounded-full overflow-hidden">
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
              <td className="py-3.5 text-slate-500 text-xs">{formatDate(scan.created_at)}</td>
              <td className="py-3.5">
                <div className="flex items-center justify-end gap-1">
                  <button
                    onClick={() => onView(scan)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                    title="View Details"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  {['pending', 'queued', 'running'].includes(scan.status) && (
                    <button
                      onClick={() => onCancel(scan)}
                      className="p-1.5 rounded-md text-slate-500 hover:text-amber-400 hover:bg-slate-800 transition-colors"
                      title="Cancel Scan"
                    >
                      <Square className="h-4 w-4" />
                    </button>
                  )}
                  {['completed', 'failed', 'cancelled'].includes(scan.status) && (
                    <button
                      onClick={() => onDelete(scan)}
                      className="p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                      title="Delete"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
