import { useState, useEffect, useCallback, useRef } from 'react'
import { Plus, Search, Radar } from 'lucide-react'
import toast from 'react-hot-toast'
import scanApi from '../../services/scanApi'
import projectApi from '../../services/projectApi'
import ScanTable from '../../components/scans/ScanTable'
import ScanDetails from '../../components/scans/ScanDetails'
import StartScanModal from '../../components/scans/StartScanModal'
import DeleteScanConfirm from '../../components/scans/DeleteScanConfirm'

const STATUS_FILTERS = [
  { value: '', label: 'All Status' },
  { value: 'pending', label: 'Pending' },
  { value: 'queued', label: 'Queued' },
  { value: 'running', label: 'Running' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'cancelled', label: 'Cancelled' },
]

const POLL_INTERVAL = 3000

export default function ScansPage() {
  const [scans, setScans] = useState([])
  const [projects, setProjects] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const [startOpen, setStartOpen] = useState(false)
  const [viewScan, setViewScan] = useState(null)
  const [deleteScan, setDeleteScan] = useState(null)

  const pollRef = useRef(null)
  const perPage = 10

  const fetchScans = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: perPage }
      if (search) params.search = search
      if (statusFilter) params.status = statusFilter
      const res = await scanApi.list(params)
      setScans(res.data.scans)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to load scans')
    } finally {
      setLoading(false)
    }
  }, [page, search, statusFilter])

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ per_page: 100 })
      setProjects(res.data.projects)
    } catch (err) {
    }
  }, [])

  useEffect(() => {
    fetchScans()
  }, [fetchScans])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    const hasActiveScans = scans.some(
      (s) => ['pending', 'queued', 'running'].includes(s.status)
    )

    if (hasActiveScans) {
      pollRef.current = setInterval(() => {
        fetchScans()
      }, POLL_INTERVAL)
    }

    return () => {
      if (pollRef.current) {
        clearInterval(pollRef.current)
        pollRef.current = null
      }
    }
  }, [scans, fetchScans])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput)
  }

  const handleStartScan = async (data) => {
    setActionLoading(true)
    try {
      await scanApi.start(data)
      toast.success('Scan started successfully')
      setStartOpen(false)
      setPage(1)
      fetchScans()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start scan')
    } finally {
      setActionLoading(false)
    }
  }

  const handleCancelScan = async (scan) => {
    setActionLoading(true)
    try {
      await scanApi.cancel(scan.id)
      toast.success('Scan cancelled')
      fetchScans()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to cancel scan')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDeleteScan = async () => {
    setActionLoading(true)
    try {
      await scanApi.delete(deleteScan.id)
      toast.success('Scan deleted')
      setDeleteScan(null)
      const newTotal = total - 1
      const newTotalPages = Math.ceil(newTotal / perPage)
      if (page > newTotalPages && newTotalPages > 0) setPage(newTotalPages)
      else fetchScans()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete scan')
    } finally {
      setActionLoading(false)
    }
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Scans</h1>
          <p className="text-slate-400 mt-1 text-sm">View and manage scan executions.</p>
        </div>
        <button onClick={() => setStartOpen(true)} className="btn-primary flex items-center gap-2 text-sm flex-shrink-0">
          <Plus className="h-4 w-4" />
          Start Scan
        </button>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <form onSubmit={handleSearch} className="flex gap-2 flex-1">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
              <input
                type="text"
                className="input-field pl-10 text-sm"
                placeholder="Search by scan name or project..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary text-sm">Search</button>
          </form>
          <select
            className="input-field w-auto text-sm min-w-[140px]"
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1) }}
          >
            {STATUS_FILTERS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <ScanTable
          scans={scans}
          loading={loading}
          onView={(s) => setViewScan(s)}
          onCancel={handleCancelScan}
          onDelete={(s) => setDeleteScan(s)}
          onEmpty={() => setStartOpen(true)}
        />

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
      </div>

      <StartScanModal
        isOpen={startOpen}
        onClose={() => setStartOpen(false)}
        onSubmit={handleStartScan}
        projects={projects}
        loading={actionLoading}
      />

      <ScanDetails
        isOpen={!!viewScan}
        onClose={() => setViewScan(null)}
        scan={viewScan}
      />

      <DeleteScanConfirm
        isOpen={!!deleteScan}
        onClose={() => setDeleteScan(null)}
        onConfirm={handleDeleteScan}
        scanName={deleteScan?.scan_name}
        loading={actionLoading}
      />
    </div>
  )
}
