import { useState, useEffect } from 'react'
import Modal from '../ui/Modal'
import Spinner from '../ui/Spinner'

const STATUS_OPTIONS = [
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'archived', label: 'Archived' },
]

export default function ProjectForm({ isOpen, onClose, onSubmit, project = null, loading = false }) {
  const isEdit = !!project

  const [form, setForm] = useState({
    name: '',
    organization: '',
    target_domain: '',
    description: '',
    tags: '',
    status: 'active',
  })

  const [errors, setErrors] = useState({})

  useEffect(() => {
    if (project) {
      setForm({
        name: project.name || '',
        organization: project.organization || '',
        target_domain: project.target_domain || '',
        description: project.description || '',
        tags: (project.tags || []).join(', '),
        status: project.status || 'active',
      })
    } else {
      setForm({ name: '', organization: '', target_domain: '', description: '', tags: '', status: 'active' })
    }
    setErrors({})
  }, [project, isOpen])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: '' }))
  }

  const validate = () => {
    const errs = {}
    if (!form.name.trim()) errs.name = 'Project name is required'
    if (!form.target_domain.trim()) {
      errs.target_domain = 'Target domain is required'
    } else if (!/^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$/.test(form.target_domain.trim().toLowerCase())) {
      errs.target_domain = 'Invalid domain format'
    }
    setErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!validate()) return

    const tags = form.tags
      ? form.tags.split(',').map((t) => t.trim().toLowerCase()).filter(Boolean)
      : []

    onSubmit({
      name: form.name.trim(),
      organization: form.organization.trim() || null,
      target_domain: form.target_domain.trim().toLowerCase(),
      description: form.description.trim() || null,
      tags,
      status: form.status,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={isEdit ? 'Edit Project' : 'New Project'}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Project Name <span className="text-red-400">*</span></label>
          <input
            name="name"
            className={`input-field ${errors.name ? 'input-error' : ''}`}
            placeholder="e.g. Corporate ASM"
            value={form.name}
            onChange={handleChange}
            disabled={loading}
          />
          {errors.name && <p className="error-text">{errors.name}</p>}
        </div>

        <div>
          <label className="label">Organization</label>
          <input
            name="organization"
            className="input-field"
            placeholder="e.g. Acme Corp"
            value={form.organization}
            onChange={handleChange}
            disabled={loading}
          />
        </div>

        <div>
          <label className="label">Target Domain <span className="text-red-400">*</span></label>
          <input
            name="target_domain"
            className={`input-field ${errors.target_domain ? 'input-error' : ''}`}
            placeholder="e.g. example.com"
            value={form.target_domain}
            onChange={handleChange}
            disabled={loading}
          />
          {errors.target_domain && <p className="error-text">{errors.target_domain}</p>}
        </div>

        <div>
          <label className="label">Description</label>
          <textarea
            name="description"
            className="input-field resize-none"
            rows={3}
            placeholder="Optional description..."
            value={form.description}
            onChange={handleChange}
            disabled={loading}
          />
        </div>

        <div>
          <label className="label">Tags</label>
          <input
            name="tags"
            className="input-field"
            placeholder="Comma-separated, e.g. production, external"
            value={form.tags}
            onChange={handleChange}
            disabled={loading}
          />
        </div>

        <div>
          <label className="label">Status</label>
          <select
            name="status"
            className="input-field"
            value={form.status}
            onChange={handleChange}
            disabled={loading}
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary text-sm" disabled={loading}>
            Cancel
          </button>
          <button type="submit" className="btn-primary text-sm flex items-center gap-2" disabled={loading}>
            {loading && <Spinner size="sm" />}
            {loading ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Project'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
