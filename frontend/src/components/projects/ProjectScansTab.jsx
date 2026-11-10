import { useState, useEffect, useCallback } from 'react'
import { Plus, Search, Radar } from 'lucide-react'
import toast from 'react-hot-toast'
import scanApi from '../../services/scanApi'
import ScanTable from '../scans/ScanTable'
import ScanDetails from '../scans/ScanDetails'
import StartScanModal from '../scans/StartScanModal'
import DeleteScanConfirm from '../scans/DeleteScanConfirm'

export default function ProjectScansTab({ project, projects }) {
  const [scans, setScans] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const [startOpen, setStartOpen] = useState(false)
  const [viewScan, setViewScan] = useState(null)
  const [deleteScan, setDeleteScan] = useState(null)

  const perPage = 10

  const fetchScans = useCallback(async () => {
    setLoading(true)
    try {
      const res = await scanApi.list({ page, per_page: perPage, project_id: project.id })
      setScans(res.data.scans)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to load scans')
    } finally {
      setLoading(false)
    }
  }, [page, project.id])

  useEffect(() => {
    fetchScans()
  }, [fetchScans])

  const handleStartScan = async (data) => {
    setActionLoading(true)
    try {
      await scanApi.start(data)
      toast.success('Scan started')
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
      fetchScans()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete scan')
    } finally {
      setActionLoading(false)
    }
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">
          {total} scan{total !== 1 ? 's' : ''} for this project
        </p>
        <button onClick={() => setStartOpen(true)} className="btn-primary text-sm flex items-center gap-2">
          <Plus className="h-4 w-4" />
          Start Scan
        </button>
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
        <div className="flex items-center justify-between pt-4 border-t border-slate-800">
          <p className="text-sm text-slate-500">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs rounded-lg border border-slate-700 text-slate-400 hover:text-slate-200 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}

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
