import { useEffect, useState } from 'react'
import { Bug, FolderOpen, Gauge, Server, ShieldAlert, Wifi } from 'lucide-react'
import projectApi from '../../services/projectApi'
import assetApi from '../../services/assetApi'
import vulnerabilityApi from '../../services/vulnerabilityApi'
import riskApi from '../../services/riskApi'
import scanApi from '../../services/scanApi'
import StatCard from '../ui/StatCard'

export default function OverviewCards() {
  const [data, setData] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.allSettled([
      projectApi.list({ per_page: 1 }),
      assetApi.stats(),
      vulnerabilityApi.stats(),
      riskApi.stats(),
      scanApi.list({ per_page: 5 }),
    ])
      .then(([p, a, v, r, s]) => {
        const scans = s.status === 'fulfilled' ? s.value.data.scans || [] : []
        const last = scans.find((x) => x.status === 'completed')
        setData({
          projects: p.status === 'fulfilled' ? p.value.data.total : null,
          assets: a.status === 'fulfilled' ? a.value.data.total_assets : null,
          live: a.status === 'fulfilled' ? a.value.data.active_assets : null,
          critical: v.status === 'fulfilled' ? v.value.data.critical : null,
          risk: r.status === 'fulfilled' ? r.value.data.overall_risk_score : null,
          riskLevel: r.status === 'fulfilled' ? r.value.data.overall_risk_level : null,
          last: last?.completed_at || last?.created_at || null,
        })
      })
      .finally(() => setLoading(false))
  }, [])

  const last = data.last
    ? new Date(data.last).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
    : '--'

  const riskTone =
    data.riskLevel === 'Critical'
      ? 'text-red-600 dark:text-red-400'
      : data.riskLevel === 'High'
        ? 'text-orange-600 dark:text-orange-400'
        : data.riskLevel === 'Medium'
          ? 'text-amber-600 dark:text-amber-400'
          : 'text-[var(--foreground)]'

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      <StatCard label="Total Projects" value={data.projects} icon={FolderOpen} loading={loading} description="Active monitoring scopes" />
      <StatCard label="Total Assets" value={data.assets} icon={Server} loading={loading} description="Discovered subdomains & hosts" />
      <StatCard label="Live Hosts" value={data.live} icon={Wifi} loading={loading} description="Validated HTTP endpoints" />
      <StatCard
        label="Critical Vulns"
        value={data.critical}
        icon={Bug}
        loading={loading}
        tone="text-red-600 dark:text-red-400"
        description="Requires immediate attention"
      />
      <StatCard label="Overall Risk" value={data.risk ?? '--'} icon={ShieldAlert} loading={loading} tone={riskTone} description={data.riskLevel || 'Risk posture'} />
      <StatCard label="Last Scan" value={last} icon={Gauge} loading={loading} description="Recent completion time" />
    </div>
  )
}
