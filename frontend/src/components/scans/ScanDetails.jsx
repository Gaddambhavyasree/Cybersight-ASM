import Modal from '../ui/Modal'
import ScanTimeline from './ScanTimeline'
import { AlertTriangle, Ban, Server } from 'lucide-react'

const STATUS_STYLES = {
  pending: 'bg-slate-500/10 text-[var(--muted-foreground)] border-slate-500/20',
  queued: 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  running: 'bg-[var(--primary)] text-[var(--primary)] border-[var(--primary)]',
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
  return new Date(dateStr).toLocaleString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function ScanDetails({ isOpen, onClose, scan }) {
  if (!scan) return null

  const isFailed = scan.status === 'failed'
  const isCancelled = scan.status === 'cancelled'

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Scan Details">
      <div className="space-y-5 max-h-[70vh] overflow-y-auto pr-1">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Scan Name</p>
            <p className="text-sm text-[var(--foreground)] font-medium">{scan.scan_name}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Project</p>
            <p className="text-sm text-[var(--foreground)]">{scan.project_name || '--'}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Status</p>
            <span className={`text-xs font-medium px-2 py-1 rounded-md border ${STATUS_STYLES[scan.status] || STATUS_STYLES.pending}`}>
              {scan.status?.charAt(0).toUpperCase() + scan.status?.slice(1)}
            </span>
          </div>
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Current Stage</p>
            <p className="text-sm text-[var(--primary)] font-medium">
              {STAGE_LABELS[scan.current_stage] || scan.current_stage}
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Progress</p>
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-[var(--muted)] rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    isFailed ? 'bg-red-500' : isCancelled ? 'bg-amber-500' : 'bg-[var(--primary)]'
                  }`}
                  style={{ width: `${scan.progress}%` }}
                />
              </div>
              <span className="text-sm text-[var(--foreground)] font-medium">{scan.progress}%</span>
            </div>
          </div>
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Initiated By</p>
            <p className="text-sm text-[var(--foreground)]">{scan.initiated_by_name || '--'}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Started At</p>
            <p className="text-sm text-[var(--foreground)]">{formatDate(scan.started_at)}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Completed At</p>
            <p className="text-sm text-[var(--foreground)]">{formatDate(scan.completed_at)}</p>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Assets Discovered</p>
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-[var(--primary)]" />
              <span className="text-sm text-[var(--foreground)] font-medium">{scan.assets_count || 0}</span>
            </div>
          </div>
        </div>

        {scan.cancelled_at && (
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Cancelled At</p>
            <p className="text-sm text-amber-400">{formatDate(scan.cancelled_at)}</p>
          </div>
        )}

        {(isFailed || isCancelled) && (
          <div className={`rounded-lg border p-3 ${
            isFailed
              ? 'bg-red-500/5 border-red-500/20'
              : 'bg-amber-500/5 border-amber-500/20'
          }`}>
            <div className="flex items-start gap-2">
              {isFailed ? (
                <AlertTriangle className="h-4 w-4 text-red-400 mt-0.5 flex-shrink-0" />
              ) : (
                <Ban className="h-4 w-4 text-amber-400 mt-0.5 flex-shrink-0" />
              )}
              <div>
                <p className={`text-sm font-medium ${isFailed ? 'text-red-400' : 'text-amber-400'}`}>
                  {isFailed ? 'Scan Failed' : 'Scan Cancelled'}
                </p>
                {isFailed && scan.failure_stage && (
                  <p className="text-xs text-[var(--muted-foreground)] mt-1">
                    Failed at: {STAGE_LABELS[scan.failure_stage] || scan.failure_stage}
                  </p>
                )}
                {isFailed && scan.failure_message && (
                  <p className="text-xs text-red-400/70 mt-1">{scan.failure_message}</p>
                )}
              </div>
            </div>
          </div>
        )}

        <div>
          <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-3">Workflow Timeline</p>
          <ScanTimeline currentStage={scan.current_stage} status={scan.status} />
        </div>

        <div>
          <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-3">Execution Logs</p>
          <div className="bg-[var(--muted)] rounded-lg border border-[var(--border)] max-h-48 overflow-y-auto">
            {scan.logs?.length > 0 ? (
              <div className="p-3 space-y-1.5">
                {scan.logs.map((log, i) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span className="text-[var(--muted-foreground)] font-mono whitespace-nowrap">
                      {new Date(log.timestamp).toLocaleTimeString('en-US', { hour12: false })}
                    </span>
                    <span className={
                      log.level === 'warning' ? 'text-amber-400' :
                      log.level === 'error' ? 'text-red-400' : 'text-[var(--muted-foreground)]'
                    }>
                      {log.message}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="p-3 text-xs text-[var(--muted-foreground)]">No logs available.</p>
            )}
          </div>
        </div>

        <div className="flex justify-end pt-2 border-t border-[var(--border)]">
          <button onClick={onClose} className="btn-secondary text-sm">Close</button>
        </div>
      </div>
    </Modal>
  )
}
