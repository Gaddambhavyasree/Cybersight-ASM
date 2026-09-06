import { useState, useEffect } from 'react'
import { BarChart3 } from 'lucide-react'
import portApi from '../../services/portApi'

export default function TopOpenPorts() {
  const [topPorts, setTopPorts] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTopPorts = async () => {
      try {
        const res = await portApi.stats()
        setTopPorts(res.data.top_open_ports || [])
      } catch (err) {
      } finally {
        setLoading(false)
      }
    }
    fetchTopPorts()
  }, [])

  if (loading) {
    return (
      <div className="card">
        <div className="h-64 flex items-center justify-center">
          <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-[var(--primary)]" />
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-6">
        <BarChart3 className="h-5 w-5 text-[var(--primary)]" />
        <h3 className="text-lg font-semibold text-[var(--foreground)]">Top Open Ports</h3>
      </div>
      {topPorts.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-[var(--muted-foreground)] text-sm">
          No port data available yet.
        </div>
      ) : (
        <div className="space-y-3">
          {topPorts.map((item) => (
            <div key={item.port} className="flex items-center gap-3">
              <div className="w-16 text-right font-mono text-[var(--foreground)] text-sm">
                {item.port}
              </div>
              <div className="flex-1 h-7 bg-[var(--muted)] rounded-lg overflow-hidden relative">
                <div
                  className="h-full bg-gradient-to-r from-sky-500 to-sky-600 rounded-lg transition-all duration-500"
                  style={{ width: `${Math.min(100, (item.count / Math.max(1, topPorts[0].count)) * 100)}%` }}
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-medium text-[var(--foreground)]">
                  {item.count}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
