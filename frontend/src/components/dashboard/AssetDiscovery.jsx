import { Radar } from 'lucide-react'

export default function AssetDiscovery() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-lg bg-sky-500/10 flex items-center justify-center">
          <Radar className="h-4.5 w-4.5 text-sky-500" />
        </div>
        <h2 className="text-base font-semibold text-slate-100">Asset Discovery</h2>
      </div>

      <div className="flex flex-col items-center justify-center py-10 text-center">
        <p className="text-slate-500 text-sm">No scans have been executed.</p>
        <button
          className="mt-5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-semibold text-sm py-2.5 px-5 rounded-lg transition-colors"
          disabled
        >
          Start New Scan
        </button>
      </div>
    </div>
  )
}
