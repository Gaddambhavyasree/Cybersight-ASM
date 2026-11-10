import { CheckCircle2, Circle, Clock, XCircle, Ban } from 'lucide-react'

const STAGES = [
  'Waiting',
  'Asset Discovery',
  'Live Host Detection',
  'Port Scanning',
  'Technology Detection',
  'DNS Intelligence',
  'SSL Analysis',
  'Web Crawling',
  'Vulnerability Assessment',
  'Threat Intelligence',
  'Risk Assessment',
  'Completed',
]

const STAGE_KEY_MAP = {
  'Waiting': 'waiting',
  'Asset Discovery': 'asset_discovery',
  'Live Host Detection': 'live_host_detection',
  'Port Scanning': 'port_scanning',
  'Technology Detection': 'technology_detection',
  'DNS Intelligence': 'dns_intelligence',
  'SSL Analysis': 'ssl_analysis',
  'Web Crawling': 'web_crawling',
  'Vulnerability Assessment': 'vulnerability_assessment',
  'Threat Intelligence': 'threat_intelligence',
  'Risk Assessment': 'risk_assessment',
  'Completed': 'completed',
}

export default function ScanTimeline({ currentStage, status }) {
  const currentIdx = STAGES.findIndex(
    (s) => STAGE_KEY_MAP[s] === currentStage
  )

  const isFailed = status === 'failed'
  const isCancelled = status === 'cancelled'

  return (
    <div className="flex flex-col items-start gap-0 pl-2">
      {STAGES.map((stage, i) => {
        const stageKey = STAGE_KEY_MAP[stage]
        const isCompleted = i < currentIdx
        const isCurrent = i === currentIdx && !isFailed && !isCancelled
        const isFailedStage = isFailed && i === currentIdx
        const isCancelledStage = isCancelled && i === currentIdx
        const isSkipped = (isFailed || isCancelled) && i > currentIdx

        let iconBg, iconBorder, IconComponent, iconColor

        if (isCompleted) {
          iconBg = 'bg-emerald-500/20'
          iconBorder = 'border-emerald-500/40'
          IconComponent = CheckCircle2
          iconColor = 'text-emerald-400'
        } else if (isFailedStage) {
          iconBg = 'bg-red-500/20'
          iconBorder = 'border-red-500/40'
          IconComponent = XCircle
          iconColor = 'text-red-400'
        } else if (isCancelledStage) {
          iconBg = 'bg-amber-500/20'
          iconBorder = 'border-amber-500/40'
          IconComponent = Ban
          iconColor = 'text-amber-400'
        } else if (isCurrent) {
          iconBg = 'bg-sky-500/20'
          iconBorder = 'border-sky-500/40'
          IconComponent = Clock
          iconColor = 'text-sky-400'
        } else {
          iconBg = 'bg-slate-800'
          iconBorder = 'border-slate-700'
          IconComponent = Circle
          iconColor = 'text-slate-600'
        }

        return (
          <div key={stage} className="flex items-start gap-3">
            <div className="flex flex-col items-center">
              <div className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 border ${iconBg} ${iconBorder}`}>
                <IconComponent className={`h-4 w-4 ${iconColor}`} />
              </div>
              {i < STAGES.length - 1 && (
                <div className={`w-px h-6 ${
                  isCompleted ? 'bg-emerald-500/40' :
                  isSkipped ? 'bg-slate-700/30' :
                  'bg-slate-700/60'
                }`} />
              )}
            </div>
            <div className="pt-0.5 pb-2">
              <p className={`text-sm font-medium ${
                isCompleted ? 'text-emerald-400' :
                isFailedStage ? 'text-red-400' :
                isCancelledStage ? 'text-amber-400' :
                isCurrent ? 'text-sky-400' :
                isSkipped ? 'text-slate-700' :
                'text-slate-600'
              }`}>
                {stage}
              </p>
              {isCurrent && (
                <p className="text-xs text-sky-500/70 mt-0.5">Current stage</p>
              )}
              {isCompleted && (
                <p className="text-xs text-emerald-500/50 mt-0.5">Completed</p>
              )}
              {isFailedStage && (
                <p className="text-xs text-red-500/70 mt-0.5">Failed</p>
              )}
              {isCancelledStage && (
                <p className="text-xs text-amber-500/70 mt-0.5">Cancelled</p>
              )}
              {isSkipped && (
                <p className="text-xs text-slate-700 mt-0.5">Skipped</p>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}
