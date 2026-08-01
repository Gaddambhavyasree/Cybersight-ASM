import { Clock } from 'lucide-react'

export default function HistoricalScans() {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-lg bg-sky-500/10 flex items-center justify-center">
          <Clock className="h-4.5 w-4.5 text-sky-500" />
        </div>
        <h2 className="text-base font-semibold text-slate-100">Historical Scan Comparison</h2>
      </div>

      <div className="flex items-center justify-center py-16">
        <p className="text-slate-600 text-sm">Historical scan data will appear after multiple scans.</p>
      </div>
    </div>
  )
}
