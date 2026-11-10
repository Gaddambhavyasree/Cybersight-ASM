import { useState, useEffect, useCallback } from 'react'
import { Search, Server, ChevronDown, ChevronRight } from 'lucide-react'
import toast from 'react-hot-toast'
import assetApi from '../../services/assetApi'
import portApi from '../../services/portApi'
import EmptyState from '../../components/ui/EmptyState'

const SOURCE_FILTERS = [
  { value: '', label: 'All Sources' },
  { value: 'Subfinder', label: 'Subfinder' },
  { value: 'Amass', label: 'Amass' },
  { value: 'Manual', label: 'Manual' },
]

const STATUS_FILTERS = [
  { value: '', label: 'All Status' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'unknown', label: 'Unknown' },
]

const SOURCE_STYLES = {
  Subfinder: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
  Amass: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  Manual: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
}

const STATUS_STYLES = {
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  inactive: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  unknown: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

function LiveBadge({ isLive, httpStatus }) {
  if (isLive === null || isLive === undefined) {
    return <span className="text-xs text-slate-600">--</span>
  }
  if (isLive) {
    const bg = httpStatus && httpStatus < 400
      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
      : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
    return (
      <span className={`text-xs font-medium px-2 py-1 rounded-md border ${bg}`}>
        {httpStatus || '200'}
      </span>
    )
  }
  return (
    <span className="text-xs font-medium px-2 py-1 rounded-md border bg-slate-500/10 text-slate-500 border-slate-500/20">
      Offline
    </span>
  )
}

const CONTEXT_OPTIONS = [
  { value: '', label: 'Not classified' },
  { value: 'production', label: 'Production' },
  { value: 'staging', label: 'Staging' },
  { value: 'development', label: 'Development' },
  { value: 'third_party', label: 'Third party' },
  { value: 'cloud_junk', label: 'Cloud junk (review/remove)' },
  { value: 'internal', label: 'Internal only' },
]

function ContextEditor({ asset, onSaved }) {
  const [ctx, setCtx] = useState(asset.business_context || '')
  const [crit, setCrit] = useState(asset.criticality ?? '')
  const [tags, setTags] = useState((asset.tags || []).join(', '))
  const [saving, setSaving] = useState(false)
  const [shotUrl, setShotUrl] = useState(null)

  useEffect(() => {
    let revoked = null
    if (asset.screenshot_file) {
      assetApi.screenshot(asset.id)
        .then((r) => { revoked = URL.createObjectURL(r.data); setShotUrl(revoked) })
        .catch(() => {})
    }
    return () => { if (revoked) URL.revokeObjectURL(revoked) }
  }, [asset.id, asset.screenshot_file])

  const save = async () => {
    setSaving(true)
    try {
      const payload = { tags: tags.split(',').map((t) => t.trim()).filter(Boolean) }
      if (ctx) payload.business_context = ctx
      if (crit !== '') payload.criticality = Number(crit)
      const res = await assetApi.updateContext(asset.id, payload)
      toast.success('Asset context updated — reflected in next risk calculation')
      if (onSaved && res.data?.asset) onSaved(res.data.asset)
    } catch {
      toast.error('Failed to update asset context')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-4 pt-4 border-t border-slate-700/60">
      <h4 className="text-sm font-medium text-slate-300 mb-3">Business Context</h4>
      <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-end">
        <div>
          <label className="text-xs text-slate-500 block mb-1">Environment</label>
          <select className="input-field text-sm min-w-[150px]" value={ctx} onChange={(e) => setCtx(e.target.value)}>
            {CONTEXT_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs text-slate-500 block mb-1">Criticality</label>
          <select className="input-field text-sm min-w-[150px]" value={crit} onChange={(e) => setCrit(e.target.value)}>
            <option value="">Not set</option>
            <option value="5">5 — Crown jewel</option>
            <option value="4">4 — Business critical</option>
            <option value="3">3 — Important</option>
            <option value="2">2 — Supporting</option>
            <option value="1">1 — Low impact</option>
          </select>
        </div>
        <div className="flex-1">
          <label className="text-xs text-slate-500 block mb-1">Tags (comma separated)</label>
          <input type="text" className="input-field text-sm" placeholder="e.g. crm, customer-data"
                 value={tags} onChange={(e) => setTags(e.target.value)} />
        </div>
        <button onClick={save} disabled={saving} className="btn-primary text-sm disabled:opacity-40">
          {saving ? 'Saving…' : 'Save context'}
        </button>
      </div>
      {shotUrl && (
        <div className="mt-3">
          <p className="text-xs text-slate-500 mb-1">Screenshot ({asset.hostname})</p>
          <img src={shotUrl} alt={`Screenshot of ${asset.hostname}`} className="rounded-lg border border-slate-700 max-w-xl w-full" />
        </div>
      )}
    </div>
  )
}

export default function AssetsPage() {
  const [assets, setAssets] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [sourceFilter, setSourceFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [expandedAssetId, setExpandedAssetId] = useState(null)
  const [assetPorts, setAssetPorts] = useState({})
  const [portsLoading, setPortsLoading] = useState({})

  const perPage = 50

  const fetchAssetPorts = useCallback(async (assetId) => {
    if (assetPorts[assetId]) return
    setPortsLoading(prev => ({ ...prev, [assetId]: true }))
    try {
      const res = await portApi.list({ asset_id: assetId, per_page: 100 })
      setAssetPorts(prev => ({ ...prev, [assetId]: res.data.ports }))
    } catch (err) {
      toast.error('Failed to load ports')
    } finally {
      setPortsLoading(prev => ({ ...prev, [assetId]: false }))
    }
  }, [assetPorts])

  const fetchAssets = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: perPage }
      if (search) params.search = search
      if (sourceFilter) params.source = sourceFilter
      if (statusFilter) params.status = statusFilter
      const res = await assetApi.list(params)
      setAssets(res.data.assets)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to load assets')
    } finally {
      setLoading(false)
    }
  }, [page, search, sourceFilter, statusFilter])

  useEffect(() => {
    fetchAssets()
  }, [fetchAssets])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput)
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Assets</h1>
        <p className="text-slate-400 mt-1 text-sm">Discovered subdomains and hosts across all projects.</p>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                className="input-field pl-10 text-sm"
                placeholder="Search by hostname..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary text-sm">Search</button>
          </form>
          <div className="flex gap-2">
            <select
              className="input-field w-auto text-sm min-w-[130px]"
              value={sourceFilter}
              onChange={(e) => { setSourceFilter(e.target.value); setPage(1) }}
            >
              {SOURCE_FILTERS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <select
              className="input-field w-auto text-sm min-w-[130px]"
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
            >
              {STATUS_FILTERS.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center py-16">
            <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-sky-500" />
          </div>
        ) : assets.length === 0 ? (
          <EmptyState
            icon={Server}
            title="No assets discovered"
            description="No assets have been discovered yet. Start a scan to discover subdomains."
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                <tr className="text-left text-slate-500 border-b border-slate-800">
                  <th className="pb-3 font-medium w-8"></th>
                  <th className="pb-3 font-medium">Hostname</th>
                  <th className="pb-3 font-medium">IP</th>
                  <th className="pb-3 font-medium">Live</th>
                  <th className="pb-3 font-medium">Port Count</th>
                  <th className="pb-3 font-medium">HTTPS</th>
                  <th className="pb-3 font-medium">Web Server</th>
                  <th className="pb-3 font-medium">Page Title</th>
                  <th className="pb-3 font-medium">Source</th>
                  <th className="pb-3 font-medium">Last Checked</th>
                </tr>
              </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {assets.map((asset) => (
                    <>
                      <tr
                        key={asset.id}
                        className="hover:bg-slate-800/20 transition-colors cursor-pointer"
                        onClick={() => {
                          if (expandedAssetId === asset.id) {
                            setExpandedAssetId(null)
                          } else {
                            setExpandedAssetId(asset.id)
                            fetchAssetPorts(asset.id)
                          }
                        }}
                      >
                        <td className="py-3.5 w-8">
                          {expandedAssetId === asset.id ? (
                            <ChevronDown className="h-4 w-4 text-slate-500" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-slate-500" />
                          )}
                        </td>
                        <td className="py-3.5">
                          <span className="text-sky-400 font-mono text-xs">{asset.hostname}</span>
                        </td>
                        <td className="py-3.5 text-slate-400 text-xs font-mono">
                          {asset.ip || <span className="text-slate-600">--</span>}
                        </td>
                        <td className="py-3.5">
                          <LiveBadge isLive={asset.is_live} httpStatus={asset.http_status} />
                        </td>
                        <td className="py-3.5 text-slate-300 font-mono text-xs">
                          {asset.open_ports_count ?? 0}
                        </td>
                        <td className="py-3.5">
                          {asset.https_enabled === null || asset.https_enabled === undefined ? (
                            <span className="text-slate-600 text-xs">--</span>
                          ) : asset.https_enabled ? (
                            <span className="text-emerald-400 text-xs font-medium">Yes</span>
                          ) : (
                            <span className="text-slate-500 text-xs">No</span>
                          )}
                        </td>
                        <td className="py-3.5 text-slate-400 text-xs">
                          {asset.web_server || <span className="text-slate-600">--</span>}
                        </td>
                        <td className="py-3.5 text-slate-400 text-xs max-w-[200px] truncate">
                          {asset.page_title || <span className="text-slate-600">--</span>}
                        </td>
                        <td className="py-3.5">
                          <span className={`text-xs font-medium px-2 py-1 rounded-md border ${SOURCE_STYLES[asset.source] || SOURCE_STYLES.Manual}`}>
                            {asset.source}
                          </span>
                        </td>
                        <td className="py-3.5 text-slate-500 text-xs">
                          {asset.last_http_check ? formatDate(asset.last_http_check) : '--'}
                        </td>
                      </tr>
                      {expandedAssetId === asset.id && (
                        <tr>
                          <td colSpan={10} className="py-3.5 bg-slate-800/30">
                            <div className="px-4">
                              <h4 className="text-sm font-medium text-slate-300 mb-3">Open Ports</h4>
                              {portsLoading[asset.id] ? (
                                <div className="flex justify-center py-4">
                                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-sky-500" />
                                </div>
                              ) : assetPorts[asset.id]?.length > 0 ? (
                                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                                  {[...assetPorts[asset.id]].sort((a, b) => a.port - b.port).map((port) => (
                                    <div
                                      key={port.id}
                                      className="p-2 rounded-lg border border-slate-700 bg-slate-800/40"
                                    >
                                      <div className="flex items-center justify-between">
                                        <span className="font-mono text-sm text-slate-200">
                                          {port.port}/{port.protocol}
                                        </span>
                                        <span className="text-xs text-emerald-400 font-medium">
                                          {port.state}
                                        </span>
                                      </div>
                                      {port.service && (
                                        <div className="text-xs text-slate-400 mt-1">
                                          {port.service}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-slate-500">No open ports detected.</p>
                              )}
                              <ContextEditor asset={asset} onSaved={(patch) => setAssets(prev => prev.map(a => a.id === asset.id ? { ...a, ...patch } : a))} />
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-slate-800">
                <p className="text-sm text-slate-500">
                  Showing {Math.min((page - 1) * perPage + 1, total)}-{Math.min(page * perPage, total)} of {total}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-slate-500 px-2">Page {page} of {totalPages}</span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 hover:border-slate-600 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
