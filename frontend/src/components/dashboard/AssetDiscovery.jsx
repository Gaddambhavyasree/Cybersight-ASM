import { Radar } from 'lucide-react'

export default function AssetDiscovery() {
  return (
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-lg bg-[var(--primary)] flex items-center justify-center">
          <Radar className="h-4.5 w-4.5 text-[var(--primary)]" />
        </div>
        <h2 className="text-base font-semibold text-[var(--foreground)]">Asset Discovery</h2>
      </div>

      <div className="flex flex-col items-center justify-center py-10 text-center">
        <p className="text-[var(--muted-foreground)] text-sm">No scans have been executed.</p>
        <button
          className="mt-5 bg-[var(--primary)] hover:bg-[var(--primary)] text-slate-950 font-semibold text-sm py-2.5 px-5 rounded-lg transition-colors"
          disabled
        >
          Start New Scan
        </button>
      </div>
    </div>
  )
}
