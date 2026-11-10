import { ChevronDown } from 'lucide-react'

const stages = [
  'Domain',
  'Subfinder',
  'Amass',
  'HTTPX',
  'Naabu',
  'Technology Detection',
  'Katana',
  'Nuclei',
  'Threat Intelligence',
  'Risk Engine',
  'Database',
  'Dashboard',
]

export default function ScanWorkflow() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <h2 className="text-base font-semibold text-slate-100 mb-6">Scan Workflow</h2>

      <div className="flex flex-col items-center gap-0">
        {stages.map((stage, i) => (
          <div key={stage} className="flex flex-col items-center">
            <div className="w-full max-w-[280px] bg-slate-800/60 border border-slate-700/50 rounded-lg px-4 py-3 text-center">
              <p className="text-sm font-medium text-slate-200">{stage}</p>
              <p className="text-xs text-slate-600 mt-0.5">Waiting for execution</p>
            </div>
            {i < stages.length - 1 && (
              <ChevronDown className="h-4 w-4 text-slate-700 my-1" />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
