import { useState } from 'react'
import Modal from '../ui/Modal'
import Spinner from '../ui/Spinner'

export default function StartScanModal({ isOpen, onClose, onSubmit, projects, loading = false }) {
  const [form, setForm] = useState({ project_id: '', scan_name: '' })
  const [errors, setErrors] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
  }

  const validate = () => {
    const errs = {}
    if (!form.project_id) errs.project_id = 'Please select a project'
    if (!form.scan_name.trim()) errs.scan_name = 'Scan name is required'
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return
    onSubmit({ project_id: form.project_id, scan_name: form.scan_name.trim() })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Start New Scan">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Project <span className="text-red-400">*</span></label>
          <select
            name="project_id"
            className={`input-field ${errors.project_id ? 'input-error' : ''}`}
            value={form.project_id}
            onChange={handleChange}
            disabled={loading}
          >
            <option value="">Select a project</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name} ({p.target_domain})</option>
            ))}
          </select>
          {errors.project_id && <p className="error-text">{errors.project_id}</p>}
        </div>

        <div>
          <label className="label">Scan Name <span className="text-red-400">*</span></label>
          <input
            name="scan_name"
            className={`input-field ${errors.scan_name ? 'input-error' : ''}`}
            placeholder="e.g. Initial recon scan"
            value={form.scan_name}
            onChange={handleChange}
            disabled={loading}
          />
          {errors.scan_name && <p className="error-text">{errors.scan_name}</p>}
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary text-sm" disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="btn-primary text-sm flex items-center gap-2" disabled={loading}>
            {loading && <Spinner size="sm" />}
            {loading ? 'Starting...' : 'Start Scan'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
