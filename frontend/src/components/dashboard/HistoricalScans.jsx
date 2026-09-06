import { Clock } from 'lucide-react'

export default function HistoricalScans() {
  return (
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-lg bg-[var(--primary)] flex items-center justify-center">
          <Clock className="h-4.5 w-4.5 text-[var(--primary)]" />
        </div>
        <h2 className="text-base font-semibold text-[var(--foreground)]">Historical Scan Comparison</h2>
      </div>

      <div className="flex items-center justify-center py-16">
        <p className="text-[var(--muted-foreground)] text-sm">Historical scan data will appear after multiple scans.</p>
      </div>
    </div>
  )
}
