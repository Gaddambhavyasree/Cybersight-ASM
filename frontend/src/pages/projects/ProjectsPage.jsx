import { useState, useEffect, useCallback } from 'react'
import { Plus, Search, Radar, FolderOpen, Server } from 'lucide-react'
import toast from 'react-hot-toast'
import projectApi from '../../services/projectApi'
import ProjectTable from '../../components/projects/ProjectTable'
import ProjectForm from '../../components/projects/ProjectForm'
import ProjectView from '../../components/projects/ProjectView'
import DeleteConfirm from '../../components/projects/DeleteConfirm'
import ProjectScansTab from '../../components/projects/ProjectScansTab'
import ProjectAssetsTab from '../../components/projects/ProjectAssetsTab'

const STATUS_FILTERS = [
  { value: '', label: 'All Status' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'archived', label: 'Archived' },
]

const PROJECT_TABS = [
  { key: 'scans', label: 'Scans', icon: Radar },
  { key: 'assets', label: 'Assets', icon: Server },
]

export default function ProjectsPage() {
  const [projects, setProjects] = useState([])
  const [allProjects, setAllProjects] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [searchInput, setSearchInput] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const [formOpen, setFormOpen] = useState(false)
  const [editProject, setEditProject] = useState(null)
  const [viewProject, setViewProject] = useState(null)
  const [deleteProject, setDeleteProject] = useState(null)
  const [detailProject, setDetailProject] = useState(null)
  const [detailTab, setDetailTab] = useState('scans')

  const perPage = 10

  const fetchProjects = useCallback(async () => {
    setLoading(true)
    try {
      const params = { page, per_page: perPage }
      if (search) params.search = search
      if (statusFilter) params.status = statusFilter
      const res = await projectApi.list(params)
      setProjects(res.data.projects)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to load projects')
    } finally {
      setLoading(false)
    }
  }, [page, search, statusFilter])

  const fetchAllProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ per_page: 100 })
      setAllProjects(res.data.projects)
    } catch (err) {}
  }, [])

  useEffect(() => {
    fetchProjects()
  }, [fetchProjects])

  useEffect(() => {
    fetchAllProjects()
  }, [fetchAllProjects])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setSearch(searchInput)
  }

  const handleStatusFilter = (value) => {
    setStatusFilter(value)
    setPage(1)
  }

  const handleCreate = async (data) => {
    setActionLoading(true)
    try {
      await projectApi.create(data)
      toast.success('Project created successfully')
      setFormOpen(false)
      setPage(1)
      fetchProjects()
      fetchAllProjects()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create project')
    } finally {
      setActionLoading(false)
    }
  }

  const handleUpdate = async (data) => {
    setActionLoading(true)
    try {
      await projectApi.update(editProject.id, data)
      toast.success('Project updated successfully')
      setEditProject(null)
      fetchProjects()
      fetchAllProjects()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update project')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async () => {
    setActionLoading(true)
    try {
      await projectApi.delete(deleteProject.id)
      toast.success('Project deleted')
      setDeleteProject(null)
      const newTotal = total - 1
      const newTotalPages = Math.ceil(newTotal / perPage)
      if (page > newTotalPages && newTotalPages > 0) setPage(newTotalPages)
      else fetchProjects()
      fetchAllProjects()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete project')
    } finally {
      setActionLoading(false)
    }
  }

  const totalPages = Math.ceil(total / perPage)

  if (detailProject) {
    return (
      <div className="space-y-6">
        <div>
          <button
            onClick={() => setDetailProject(null)}
            className="text-sm text-sky-400 hover:text-sky-300 transition-colors mb-3"
          >
            &larr; Back to Projects
          </button>
          <h1 className="text-2xl font-bold text-slate-100">{detailProject.name}</h1>
          <p className="text-slate-400 mt-1 text-sm">{detailProject.target_domain}</p>
        </div>

        <div className="flex gap-1 border-b border-slate-800">
          {PROJECT_TABS.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setDetailTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                detailTab === tab.key
                  ? 'border-sky-500 text-sky-400'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="card">
          {detailTab === 'scans' && (
            <ProjectScansTab project={detailProject} projects={allProjects} />
          )}
          {detailTab === 'assets' && (
            <ProjectAssetsTab project={detailProject} />
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Projects</h1>
          <p className="text-slate-400 mt-1 text-sm">Manage attack surface monitoring projects.</p>
        </div>
        <button onClick={() => setFormOpen(true)} className="btn-primary flex items-center gap-2 text-sm flex-shrink-0">
          <Plus className="h-4 w-4" />
          New Project
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
                placeholder="Search by name, organization, or domain..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
            <button type="submit" className="btn-primary text-sm">Search</button>
          </form>
          <select
            className="input-field w-auto text-sm min-w-[140px]"
            value={statusFilter}
            onChange={(e) => handleStatusFilter(e.target.value)}
          >
            {STATUS_FILTERS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <ProjectTable
          projects={projects}
          loading={loading}
          onView={(p) => setViewProject(p)}
          onEdit={(p) => setEditProject(p)}
          onDelete={(p) => setDeleteProject(p)}
          onEmpty={() => setFormOpen(true)}
          onScans={(p) => { setDetailProject(p); setDetailTab('scans') }}
          onAssets={(p) => { setDetailProject(p); setDetailTab('assets') }}
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

      <ProjectForm
        isOpen={formOpen}
        onClose={() => setFormOpen(false)}
        onSubmit={handleCreate}
        loading={actionLoading}
      />

      <ProjectForm
        isOpen={!!editProject}
        onClose={() => setEditProject(null)}
        onSubmit={handleUpdate}
        project={editProject}
        loading={actionLoading}
      />

      <ProjectView
        isOpen={!!viewProject}
        onClose={() => setViewProject(null)}
        project={viewProject}
      />

      <DeleteConfirm
        isOpen={!!deleteProject}
        onClose={() => setDeleteProject(null)}
        onConfirm={handleDelete}
        projectName={deleteProject?.name}
        loading={actionLoading}
      />
    </div>
  )
}
