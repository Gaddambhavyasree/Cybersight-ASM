import Modal from '../ui/Modal'
import Spinner from '../ui/Spinner'
import { AlertTriangle } from 'lucide-react'

export default function DeleteConfirm({ isOpen, onClose, onConfirm, projectName, loading = false }) {
  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Delete Project">
      <div className="space-y-4">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-lg bg-red-500/10 flex items-center justify-center flex-shrink-0 mt-0.5">
            <AlertTriangle className="h-5 w-5 text-red-400" />
          </div>
          <div>
            <p className="text-sm text-slate-300">
              Are you sure you want to delete <span className="font-semibold text-slate-100">{projectName}</span>?
            </p>
            <p className="text-xs text-slate-500 mt-1">This action cannot be undone. All associated data will be permanently removed.</p>
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button onClick={onClose} className="btn-secondary text-sm" disabled={loading}>
            Cancel
          </button>
          <button onClick={onConfirm} className="btn-danger text-sm flex items-center gap-2" disabled={loading}>
            {loading && <Spinner size="sm" />}
            {loading ? 'Deleting...' : 'Delete Project'}
          </button>
        </div>
      </div>
    </Modal>
  )
}
