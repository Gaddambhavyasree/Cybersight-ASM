import { CheckCircle, XCircle } from 'lucide-react'

const tools = [
  'Subfinder',
  'Amass',
  'HTTPX',
  'Naabu',
  'Katana',
  'Nuclei',
]

export default function SystemStatus() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <h2 className="text-base font-semibold text-slate-100 mb-6">System Status</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {tools.map((tool) => (
          <div
            key={tool}
            className="flex items-center gap-3 bg-slate-800/40 border border-slate-700/40 rounded-lg px-4 py-3"
          >
            <XCircle className="h-4 w-4 text-slate-600 flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-slate-300">{tool}</p>
              <p className="text-xs text-slate-600">Not Configured</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
