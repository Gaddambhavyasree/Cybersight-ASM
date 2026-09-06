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
    <div className="bg-[var(--card)] border border-[var(--border)] rounded-xl p-6">
      <h2 className="text-base font-semibold text-[var(--foreground)] mb-6">System Status</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {tools.map((tool) => (
          <div
            key={tool}
            className="flex items-center gap-3 bg-[var(--muted)] border border-[var(--border)] rounded-lg px-4 py-3"
          >
            <XCircle className="h-4 w-4 text-[var(--muted-foreground)] flex-shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-[var(--foreground)]">{tool}</p>
              <p className="text-xs text-[var(--muted-foreground)]">Not Configured</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
