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
  Subfinder: 'bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20',
  Amass: 'bg-purple-500/10 text-purple-600 dark:text-purple-300 border-purple-500/20',
  Manual: 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]',
}

const STATUS_STYLES = {
  active: 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-900',
  inactive: 'bg-[var(--muted)] text-[var(--muted-foreground)] border-[var(--border)]',
  unknown: 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-900',
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
    return <span className="text-xs text-[var(--muted-foreground)]">--</span>
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
    <span className="text-xs font-medium px-2 py-1 rounded-md border bg-slate-500/10 text-[var(--muted-foreground)] border-slate-500/20">
      Offline
    </span>
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
        <h1 className="text-2xl font-bold text-[var(--foreground)]">Assets</h1>
        <p className="text-[var(--muted-foreground)] mt-1 text-sm">Discovered subdomains and hosts across all projects.</p>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
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
            <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-[var(--primary)]" />
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
                <tr className="text-left text-[var(--muted-foreground)] border-b border-[var(--border)]">
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
                <tbody className="divide-y divide-[var(--border)]">
                  {assets.map((asset) => (
                    <>
                      <tr
                        key={asset.id}
                        className="hover:bg-[var(--muted)] transition-colors cursor-pointer"
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
                            <ChevronDown className="h-4 w-4 text-[var(--muted-foreground)]" />
                          ) : (
                            <ChevronRight className="h-4 w-4 text-[var(--muted-foreground)]" />
                          )}
                        </td>
                        <td className="py-3.5">
                          <span className="text-[var(--primary)] font-mono text-xs">{asset.hostname}</span>
                        </td>
                        <td className="py-3.5 text-[var(--muted-foreground)] text-xs font-mono">
                          {asset.ip || <span className="text-[var(--muted-foreground)]">--</span>}
                        </td>
                        <td className="py-3.5">
                          <LiveBadge isLive={asset.is_live} httpStatus={asset.http_status} />
                        </td>
                        <td className="py-3.5 text-[var(--foreground)] font-mono text-xs">
                          {asset.open_ports_count ?? 0}
                        </td>
                        <td className="py-3.5">
                          {asset.https_enabled === null || asset.https_enabled === undefined ? (
                            <span className="text-[var(--muted-foreground)] text-xs">--</span>
                          ) : asset.https_enabled ? (
                            <span className="text-emerald-400 text-xs font-medium">Yes</span>
                          ) : (
                            <span className="text-[var(--muted-foreground)] text-xs">No</span>
                          )}
                        </td>
                        <td className="py-3.5 text-[var(--muted-foreground)] text-xs">
                          {asset.web_server || <span className="text-[var(--muted-foreground)]">--</span>}
                        </td>
                        <td className="py-3.5 text-[var(--muted-foreground)] text-xs max-w-[200px] truncate">
                          {asset.page_title || <span className="text-[var(--muted-foreground)]">--</span>}
                        </td>
                        <td className="py-3.5">
                          <span className={`text-xs font-medium px-2 py-1 rounded-md border ${SOURCE_STYLES[asset.source] || SOURCE_STYLES.Manual}`}>
                            {asset.source}
                          </span>
                        </td>
                        <td className="py-3.5 text-[var(--muted-foreground)] text-xs">
                          {asset.last_http_check ? formatDate(asset.last_http_check) : '--'}
                        </td>
                      </tr>
                      {expandedAssetId === asset.id && (
                        <tr>
                          <td colSpan={10} className="py-3.5 bg-[var(--muted)]">
                            <div className="px-4">
                              <h4 className="text-sm font-medium text-[var(--foreground)] mb-3">Open Ports</h4>
                              {portsLoading[asset.id] ? (
                                <div className="flex justify-center py-4">
                                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-[var(--primary)]" />
                                </div>
                              ) : assetPorts[asset.id]?.length > 0 ? (
                                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                                  {[...assetPorts[asset.id]].sort((a, b) => a.port - b.port).map((port) => (
                                    <div
                                      key={port.id}
                                      className="p-2 rounded-lg border border-[var(--border)] bg-[var(--muted)]"
                                    >
                                      <div className="flex items-center justify-between">
                                        <span className="font-mono text-sm text-[var(--foreground)]">
                                          {port.port}/{port.protocol}
                                        </span>
                                        <span className="text-xs text-emerald-400 font-medium">
                                          {port.state}
                                        </span>
                                      </div>
                                      {port.service && (
                                        <div className="text-xs text-[var(--muted-foreground)] mt-1">
                                          {port.service}
                                        </div>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              ) : (
                                <p className="text-sm text-[var(--muted-foreground)]">No open ports detected.</p>
                              )}
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
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-[var(--border)]">
                <p className="text-sm text-[var(--muted-foreground)]">
                  Showing {Math.min((page - 1) * perPage + 1, total)}-{Math.min(page * perPage, total)} of {total}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:border-[var(--border)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                  >
                    Previous
                  </button>
                  <span className="text-sm text-[var(--muted-foreground)] px-2">Page {page} of {totalPages}</span>
                  <button
                    onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:border-[var(--border)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
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
