import { useState, useEffect, useCallback } from 'react'
import { Search, Server } from 'lucide-react'
import toast from 'react-hot-toast'
import assetApi from '../../services/assetApi'
import EmptyState from '../ui/EmptyState'

const SOURCE_STYLES = {
  Subfinder: 'bg-[var(--primary)] text-[var(--primary)] border-[var(--primary)]',
  Amass: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  Manual: 'bg-slate-500/10 text-[var(--muted-foreground)] border-slate-500/20',
}

const STATUS_STYLES = {
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  inactive: 'bg-slate-500/10 text-[var(--muted-foreground)] border-slate-500/20',
  unknown: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function ProjectAssetsTab({ project }) {
  const [assets, setAssets] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [loading, setLoading] = useState(true)

  const perPage = 20

  const fetchAssets = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: perPage }
      if (search) params.search = search
      const res = await assetApi.byProject(project.id, params)
      setAssets(res.data.assets)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to load assets')
    } finally {
      setLoading(false)
    }
  }, [page, search, project.id])

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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-[var(--muted-foreground)]">
          {total} asset{total !== 1 ? 's' : ''} discovered
        </p>
      </div>

      <form onSubmit={handleSearch} className="flex gap-2">
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

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[var(--primary)]" />
        </div>
      ) : assets.length === 0 ? (
        <EmptyState
          icon={Server}
          title="No assets discovered"
          description="No assets have been discovered for this project yet."
        />
      ) : (
        <>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[var(--muted-foreground)] border-b border-[var(--border)]">
                  <th className="pb-3 font-medium">Hostname</th>
                  <th className="pb-3 font-medium">Source</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 font-medium">First Seen</th>
                  <th className="pb-3 font-medium">Last Seen</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {assets.map((asset) => (
                  <tr key={asset.id} className="hover:bg-[var(--muted)] transition-colors">
                    <td className="py-3">
                      <span className="text-[var(--primary)] font-mono text-xs">{asset.hostname}</span>
                    </td>
                    <td className="py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded border ${SOURCE_STYLES[asset.source] || SOURCE_STYLES.Manual}`}>
                        {asset.source}
                      </span>
                    </td>
                    <td className="py-3">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded border ${STATUS_STYLES[asset.status] || STATUS_STYLES.unknown}`}>
                        {asset.status?.charAt(0).toUpperCase() + asset.status?.slice(1)}
                      </span>
                    </td>
                    <td className="py-3 text-[var(--muted-foreground)] text-xs">{formatDate(asset.first_seen)}</td>
                    <td className="py-3 text-[var(--muted-foreground)] text-xs">{formatDate(asset.last_seen)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between pt-4 border-t border-[var(--border)]">
              <p className="text-sm text-[var(--muted-foreground)]">
                Page {page} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1.5 text-xs rounded-lg border border-[var(--border)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
