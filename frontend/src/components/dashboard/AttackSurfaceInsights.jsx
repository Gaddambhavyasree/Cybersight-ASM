import { useEffect, useState } from 'react'
import { BarChart3, Globe2, ShieldAlert, Activity, Layers3 } from 'lucide-react'
import assetApi from '../../services/assetApi'
import portApi from '../../services/portApi'
import technologyApi from '../../services/technologyApi'
import threatApi from '../../services/threatApi'
import vulnerabilityApi from '../../services/vulnerabilityApi'
import scanApi from '../../services/scanApi'
import historyApi from '../../services/historyApi'

function Box({ title, icon: Icon, children, action }) {
  return (
    <div className="card p-5 flex flex-col">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-xl bg-[var(--secondary)] border border-[var(--border)] flex items-center justify-center">
            <Icon className="h-4 w-4 text-[var(--primary)]" />
          </div>
          <h2 className="text-sm font-bold tracking-tight text-[var(--foreground)]">{title}</h2>
        </div>
        {action}
      </div>
      <div className="flex-1">{children}</div>
    </div>
  )
}

const initial = { assets: [], ports: [], tech: [], history: [], scans: [], vuln: null, threat: null }

export default function AttackSurfaceInsights() {
  const [data, setData] = useState(initial)
  useEffect(() => {
    Promise.allSettled([
      assetApi.list({ per_page: 5 }),
      portApi.stats(),
      technologyApi.stats(),
      threatApi.stats(),
      vulnerabilityApi.stats(),
      scanApi.list({ per_page: 5 }),
      historyApi.list({ per_page: 2 }),
    ]).then(([a, p, t, ti, v, s, h]) =>
      setData({
        assets: a.status === 'fulfilled' ? a.value.data.assets || [] : [],
        ports: p.status === 'fulfilled' ? p.value.data.top_open_ports || [] : [],
        tech: t.status === 'fulfilled' ? t.value.data.top_technologies || [] : [],
        threat: ti.status === 'fulfilled' ? ti.value.data : null,
        vuln: v.status === 'fulfilled' ? v.value.data : null,
        scans: s.status === 'fulfilled' ? s.value.data.scans || [] : [],
        history: h.status === 'fulfilled' ? h.value.data.records || [] : [],
      })
    )
  }, [])

  const max = Math.max(1, ...data.ports.map((x) => x.count || 0))

  const severityTone = {
    critical: 'border-red-200 bg-red-50 text-red-700 dark:bg-red-950/30 dark:border-red-900 dark:text-red-300',
    high: 'border-orange-200 bg-orange-50 text-orange-700 dark:bg-orange-950/30 dark:border-orange-900 dark:text-orange-300',
    medium: 'border-amber-200 bg-amber-50 text-amber-700 dark:bg-amber-950/30 dark:border-amber-900 dark:text-amber-300',
    low: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/30 dark:border-emerald-900 dark:text-emerald-300',
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Box title="Recently discovered assets" icon={Globe2}>
        {data.assets.length ? (
          <div className="overflow-x-auto -mx-1">
            <table className="w-full text-left text-xs">
              <thead className="text-[11px] font-bold uppercase tracking-widest text-[var(--muted-foreground)]">
                <tr className="border-b border-[var(--border)]">
                  <th className="pb-2.5 font-bold px-1">Hostname</th>
                  <th className="pb-2.5 font-bold">IP</th>
                  <th className="pb-2.5 font-bold">Status</th>
                  <th className="pb-2.5 font-bold">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[var(--border)]">
                {data.assets.map((x) => (
                  <tr key={x.id} className="hover:bg-[var(--muted)]/50">
                    <td className="py-2.5 font-mono text-xs font-semibold text-[var(--primary)] px-1 truncate max-w-[160px]">{x.hostname}</td>
                    <td className="py-2.5 text-[var(--muted-foreground)] font-mono text-xs">{x.ip || '--'}</td>
                    <td className="py-2.5">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-bold border ${x.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-900' : 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]'}`}>
                        {x.status}
                      </span>
                    </td>
                    <td className="py-2.5 text-xs font-semibold text-[var(--foreground)]">{x.risk_score ?? '--'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">No assets discovered yet.</p>
        )}
      </Box>

      <Box title="Top exposed ports" icon={BarChart3}>
        {data.ports.length ? (
          <div className="space-y-2.5">
            {data.ports.slice(0, 8).map((x) => (
              <div className="flex items-center gap-3" key={x.port}>
                <span className="w-10 font-mono text-xs font-bold text-[var(--foreground)]">{x.port}</span>
                <div className="h-2 flex-1 rounded-full bg-[var(--muted)] overflow-hidden">
                  <div className="h-full rounded-full bg-[var(--primary)]" style={{ width: `${(x.count / max) * 100}%` }} />
                </div>
                <span className="w-8 text-right text-xs font-semibold text-[var(--muted-foreground)]">{x.count}</span>
              </div>
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">No data available.</p>
        )}
      </Box>

      <Box title="Severity breakdown" icon={ShieldAlert}>
        {data.vuln ? (
          <div className="grid grid-cols-4 gap-2">
            {['critical', 'high', 'medium', 'low'].map((k) => (
              <div key={k} className={`rounded-xl border p-3 text-center ${severityTone[k]}`}>
                <p className="text-xl font-extrabold">{data.vuln[k] ?? 0}</p>
                <p className="mt-1 text-[10px] font-bold uppercase tracking-widest opacity-80">{k}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">No vulnerabilities found.</p>
        )}
        {data.vuln && (
          <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/50 p-3">
              <p className="text-[11px] uppercase tracking-widest font-bold text-[var(--muted-foreground)]">Total findings</p>
              <p className="text-lg font-bold text-[var(--foreground)] mt-1">{data.vuln.total_findings ?? 0}</p>
            </div>
            <div className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/50 p-3">
              <p className="text-[11px] uppercase tracking-widest font-bold text-[var(--muted-foreground)]">Affected assets</p>
              <p className="text-lg font-bold text-[var(--foreground)] mt-1">{data.vuln.affected_assets ?? 0}</p>
            </div>
          </div>
        )}
      </Box>

      <Box title="Technology distribution" icon={Layers3}>
        {data.tech.length ? (
          <div className="space-y-2">
            {data.tech.slice(0, 8).map((x) => (
              <div className="flex items-center justify-between text-xs border border-[var(--border)] rounded-xl px-3 py-2 bg-[var(--muted)]/30" key={x.label}>
                <span className="font-medium text-[var(--foreground)] truncate pr-3">{x.label}</span>
                <span className="inline-flex items-center rounded-full bg-[var(--card)] border border-[var(--border)] px-2 py-0.5 text-[11px] font-bold text-[var(--muted-foreground)]">
                  {x.count}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">No technology data.</p>
        )}
      </Box>

      <Box title="Scan health" icon={Activity}>
        {data.scans.length ? (
          <div className="grid grid-cols-3 gap-2">
            {Object.entries({
              Running: data.scans.filter((x) => x.status === 'running').length,
              Queued: data.scans.filter((x) => x.status === 'queued').length,
              Completed: data.scans.filter((x) => x.status === 'completed').length,
              Failed: data.scans.filter((x) => x.status === 'failed').length,
              Cancelled: data.scans.filter((x) => x.status === 'cancelled').length,
            }).map(([k, v]) => (
              <div key={k} className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/40 p-3 text-center">
                <p className="text-lg font-extrabold text-[var(--foreground)]">{v}</p>
                <p className="text-[10px] font-bold uppercase tracking-widest text-[var(--muted-foreground)] mt-1">{k}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">No recent scans.</p>
        )}
      </Box>

      <Box title="Threat intelligence" icon={Globe2}>
        {data.threat ? (
          <div className="space-y-3">
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-3 text-center">
                <p className="text-lg font-bold text-[var(--foreground)]">{data.threat.total_ips ?? 0}</p>
                <p className="text-[10px] uppercase tracking-widest font-bold text-[var(--muted-foreground)]">IPs</p>
              </div>
              <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-3 text-center">
                <p className="text-lg font-bold text-[var(--foreground)]">{data.threat.malicious ?? 0}</p>
                <p className="text-[10px] uppercase tracking-widest font-bold text-[var(--muted-foreground)]">Malicious</p>
              </div>
              <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-3 text-center">
                <p className="text-lg font-bold text-[var(--foreground)]">{data.threat.suspicious ?? 0}</p>
                <p className="text-[10px] uppercase tracking-widest font-bold text-[var(--muted-foreground)]">Suspicious</p>
              </div>
            </div>
            <p className="text-xs text-[var(--muted-foreground)] text-center">Enriched via Shodan / VirusTotal where available.</p>
          </div>
        ) : (
          <p className="py-8 text-center text-sm text-[var(--muted-foreground)]">No threat data.</p>
        )}
      </Box>
    </div>
  )
}
