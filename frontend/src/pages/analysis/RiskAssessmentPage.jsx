import { useCallback, useEffect, useState } from 'react'
import { AlertCircle, RefreshCw, ShieldAlert, X } from 'lucide-react'
import riskApi from '../../services/riskApi'

const levels = ['Critical', 'High', 'Medium', 'Low', 'Very Low']
const colors = { Critical: 'text-red-300', High: 'text-orange-300', Medium: 'text-amber-300', Low: 'text-sky-300', 'Very Low': 'text-emerald-300' }
const dt = (v) => v ? new Date(v).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' }) : '--'

function Stat({ label, value, tone = 'text-slate-100' }) { return <div className="card p-4"><p className="text-[11px] uppercase tracking-wider text-slate-500">{label}</p><p className={`mt-2 text-2xl font-bold ${tone}`}>{value ?? 0}</p></div> }

function Detail({ asset, close }) {
  if (!asset) return null
  return <><div className="fixed inset-0 z-40 bg-slate-950/60" onClick={close} /><aside className="fixed right-0 top-0 z-50 h-full w-full max-w-lg overflow-y-auto border-l border-slate-800 bg-slate-950 p-6"><div className="flex items-start justify-between"><div><p className="text-xs uppercase tracking-wider text-slate-500">Risk assessment</p><h2 className="mt-1 text-xl font-semibold text-slate-100">{asset.hostname}</h2></div><button onClick={close} className="text-slate-400"><X /></button></div><div className="mt-5 grid grid-cols-2 gap-3"><Stat label="Risk score" value={asset.risk_score} tone={colors[asset.risk_level]} /><Stat label="Risk level" value={asset.risk_level} tone={colors[asset.risk_level]} /></div><h3 className="mt-6 text-sm font-semibold text-slate-200">Risk breakdown</h3><div className="mt-3 space-y-2">{Object.entries(asset.risk_breakdown || {}).map(([key, value]) => <div className="flex justify-between rounded border border-slate-800 bg-slate-900/60 px-3 py-2 text-sm" key={key}><span className="capitalize text-slate-400">{key.replaceAll('_', ' ')}</span><span className="font-semibold text-slate-100">{value}</span></div>)}</div><h3 className="mt-6 text-sm font-semibold text-slate-200">Recommendations</h3>{asset.risk_recommendations?.length ? <ul className="mt-2 list-disc space-y-2 pl-5 text-sm text-slate-300">{asset.risk_recommendations.map((x, i) => <li key={i}>{x}</li>)}</ul> : <p className="mt-2 text-sm text-slate-500">No recommendations.</p>}<p className="mt-6 text-xs text-slate-500">Last calculated {dt(asset.last_risk_calculation)}</p></aside></>
}

function PriorityQueue({ priorities }) {
  if (!priorities) return null
  const summary = priorities.summary || {}
  const items = priorities.patch_first || []
  const sevColors = { critical: 'text-red-300', high: 'text-orange-300', medium: 'text-amber-300', low: 'text-sky-300', info: 'text-slate-300' }
  const pColors = { P1: 'bg-red-500/10 text-red-300 border-red-500/20', P2: 'bg-orange-500/10 text-orange-300 border-orange-500/20', P3: 'bg-amber-500/10 text-amber-300 border-amber-500/20', P4: 'bg-slate-500/10 text-slate-300 border-slate-500/20' }
  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-orange-400" />
          <h2 className="text-sm font-semibold text-slate-200">Patch priority queue</h2>
        </div>
        <div className="flex gap-2 text-xs">
          <span className="px-2 py-1 rounded border border-slate-800 bg-slate-900/60 text-slate-400">KEV: {summary.kev_findings ?? 0}</span>
          <span className="px-2 py-1 rounded border border-slate-800 bg-slate-900/60 text-slate-400">High EPSS: {summary.high_epss ?? 0}</span>
          <span className="px-2 py-1 rounded border border-slate-800 bg-slate-900/60 text-slate-400">P1: {summary.p1 ?? 0}</span>
          <span className="px-2 py-1 rounded border border-slate-800 bg-slate-900/60 text-slate-400">P2: {summary.p2 ?? 0}</span>
        </div>
      </div>
      <p className="mt-1 text-xs text-slate-500">Ranked by CVSS, EPSS exploit probability, CISA KEV, exposure and business criticality — fix from the top.</p>
      {items.length === 0 ? <p className="mt-4 text-sm text-slate-500">No findings to prioritize yet — run a scan first.</p> : (
        <div className="mt-4 overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-slate-500 border-b border-slate-800 text-xs"><th className="pb-2 font-medium">Priority</th><th className="pb-2 font-medium">Finding</th><th className="pb-2 font-medium">Asset</th><th className="pb-2 font-medium">Severity</th><th className="pb-2 font-medium">EPSS</th><th className="pb-2 font-medium">Score</th></tr></thead>
            <tbody className="divide-y divide-slate-800/60">
              {items.map((x, i) => (
                <tr key={x.vulnerability_id || i} className="hover:bg-slate-800/20">
                  <td className="py-2.5"><span className={`text-xs font-semibold px-2 py-1 rounded-md border ${pColors[x.priority_level] || pColors.P4}`}>{x.priority_level}</span></td>
                  <td className="py-2.5 text-slate-200 text-xs">{x.title}{x.kev && <span className="ml-2 text-[10px] font-bold text-red-400 border border-red-500/30 rounded px-1.5 py-0.5">KEV</span>}</td>
                  <td className="py-2.5 text-slate-400 text-xs font-mono">{x.hostname || '—'}</td>
                  <td className={`py-2.5 text-xs capitalize ${sevColors[x.severity] || ''}`}>{x.severity}</td>
                  <td className="py-2.5 text-xs text-slate-400">{x.epss ? `${Math.round(x.epss * 100)}%` : '—'}</td>
                  <td className="py-2.5"><span className="font-semibold text-slate-100">{x.priority_score}</span><span className="text-slate-600 text-xs">/100</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function RiskAssessmentPage() {
  const [stats, setStats] = useState(null); const [rows, setRows] = useState([]); const [selected, setSelected] = useState(null); const [loading, setLoading] = useState(true); const [error, setError] = useState(false); const [priorities, setPriorities] = useState(null)
  const load = useCallback(async () => { setLoading(true); setError(false); try { const [s, r] = await Promise.all([riskApi.stats(), riskApi.list({ per_page: 200 })]); setStats(s.data); setRows(r.data.records || []) } catch { setError(true) } finally { setLoading(false) } try { const p = await riskApi.priorities({ per_page: 12 }); setPriorities(p.data) } catch { setPriorities(null) } }, [])
  useEffect(() => { load() }, [load])
  return <div className="space-y-6"><div className="flex items-start justify-between"><div><p className="text-xs uppercase tracking-[0.2em] text-sky-400">Security posture</p><h1 className="mt-1 text-2xl font-bold text-slate-100">Risk Assessment</h1><p className="mt-1 text-sm text-slate-400">Business risk across your discovered attack surface.</p></div><button onClick={load} className="btn-secondary text-sm"><RefreshCw className="h-4 w-4" /> Refresh</button></div>{error ? <div className="card flex flex-col items-center py-20"><AlertCircle className="h-8 w-8 text-red-400" /><p className="mt-3 text-sm text-slate-300">Couldn’t load risk assessments.</p><button onClick={load} className="btn-primary mt-3 text-sm">Try again</button></div> : <><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5"><Stat label="Overall risk" value={stats?.overall_risk_score} tone={colors[stats?.overall_risk_level]} /><Stat label="Risk level" value={stats?.overall_risk_level} tone={colors[stats?.overall_risk_level]} /><Stat label="Critical assets" value={stats?.critical_assets} tone="text-red-300" /><Stat label="Average asset risk" value={stats?.average_asset_risk} /><Stat label="Highest risk" value={stats?.highest_risk_asset?.hostname || '--'} /></div><PriorityQueue priorities={priorities} /><div className="grid gap-4 lg:grid-cols-3"><div className="card p-5 lg:col-span-1"><div className="flex items-center gap-2"><ShieldAlert className="h-4 w-4 text-sky-400" /><h2 className="text-sm font-semibold text-slate-200">Risk distribution</h2></div><div className="mt-5 space-y-3">{(stats?.risk_distribution || levels.map(label => ({ label, count: 0 }))).map(x => <div key={x.label}><div className="flex justify-between text-xs"><span className={colors[x.label]}>{x.label}</span><span className="text-slate-400">{x.count}</span></div><div className="mt-1 h-2 rounded bg-slate-800"><div className={`h-full rounded ${x.label === 'Critical' ? 'bg-red-500' : x.label === 'High' ? 'bg-orange-500' : x.label === 'Medium' ? 'bg-amber-500' : x.label === 'Low' ? 'bg-sky-500' : 'bg-emerald-500'}`} style={{ width: `${rows.length ? x.count / rows.length * 100 : 0}%` }} /></div></div>)}</div></div><div className="card overflow-hidden p-0 lg:col-span-2"><div className="border-b border-slate-800 px-5 py-4"><h2 className="text-sm font-semibold text-slate-200">Top 10 highest-risk assets</h2></div>{loading ? <div className="p-8 text-center text-sm text-slate-500">Loading…</div> : rows.length === 0 ? <div className="p-8 text-center text-sm text-slate-500">No completed risk assessments yet.</div> : <div className="overflow-x-auto"><table className="w-full min-w-[650px] text-left text-sm"><thead className="border-b border-slate-800 text-xs uppercase text-slate-500"><tr>{['Asset', 'IP', 'Score', 'Level', 'Ports', 'CVEs', 'SSL'].map(x => <th className="px-5 py-3 font-medium" key={x}>{x}</th>)}</tr></thead><tbody className="divide-y divide-slate-800/60">{rows.slice(0, 10).map(x => <tr key={x.id} onClick={() => setSelected(x)} className="cursor-pointer hover:bg-slate-800/30"><td className="px-5 py-4 font-mono text-xs text-sky-300">{x.hostname}</td><td className="px-5 py-4 text-xs text-slate-400">{x.ip || '--'}</td><td className="px-5 py-4 font-semibold text-slate-100">{x.risk_score}</td><td className={`px-5 py-4 text-xs font-semibold ${colors[x.risk_level]}`}>{x.risk_level}</td><td className="px-5 py-4 text-xs text-slate-400">{x.risk_breakdown?.ports ?? 0}</td><td className="px-5 py-4 text-xs text-slate-400">{x.risk_breakdown?.vulnerabilities ?? 0}</td><td className="px-5 py-4 text-xs text-slate-400">{x.risk_breakdown?.ssl ?? 0}</td></tr>)}</tbody></table></div>}</div></div></>} {selected && <Detail asset={selected} close={() => setSelected(null)} />}</div>
}
