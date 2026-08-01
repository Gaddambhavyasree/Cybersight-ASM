import { Eye, Pencil, Trash2, Radar, Server } from 'lucide-react'
import EmptyState from '../ui/EmptyState'
import { FolderOpen } from 'lucide-react'

const STATUS_STYLES = {
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  inactive: 'bg-slate-500/10 text-slate-400 border-slate-500/20',
  archived: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function ProjectTable({ projects, loading, onView, onEdit, onDelete, onEmpty, onScans, onAssets }) {
  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <div className="animate-spin rounded-full h-7 w-7 border-b-2 border-sky-500" />
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <EmptyState
        icon={FolderOpen}
        title="No projects found"
        description="No projects have been created yet."
        action={
          <button onClick={onEmpty} className="btn-primary text-sm">
            Create Your First Project
          </button>
        }
      />
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-slate-500 border-b border-slate-800">
            <th className="pb-3 font-medium">Project Name</th>
            <th className="pb-3 font-medium">Organization</th>
            <th className="pb-3 font-medium">Target Domain</th>
            <th className="pb-3 font-medium">Status</th>
            <th className="pb-3 font-medium">Created By</th>
            <th className="pb-3 font-medium">Created At</th>
            <th className="pb-3 font-medium text-right">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800/60">
          {projects.map((project) => (
            <tr key={project.id} className="hover:bg-slate-800/20 transition-colors">
              <td className="py-3.5">
                <p className="font-medium text-slate-200">{project.name}</p>
                {project.tags?.length > 0 && (
                  <div className="flex gap-1 mt-1 flex-wrap">
                    {project.tags.slice(0, 3).map((tag) => (
                      <span key={tag} className="text-[10px] bg-slate-800 text-slate-500 px-1.5 py-0.5 rounded">
                        {tag}
                      </span>
                    ))}
                    {project.tags.length > 3 && (
                      <span className="text-[10px] text-slate-600">+{project.tags.length - 3}</span>
                    )}
                  </div>
                )}
              </td>
              <td className="py-3.5 text-slate-400">{project.organization || '--'}</td>
              <td className="py-3.5">
                <span className="text-sky-400 font-mono text-xs">{project.target_domain}</span>
              </td>
              <td className="py-3.5">
                <span className={`text-xs font-medium px-2 py-1 rounded-md border ${STATUS_STYLES[project.status] || STATUS_STYLES.active}`}>
                  {project.status?.charAt(0).toUpperCase() + project.status?.slice(1)}
                </span>
              </td>
              <td className="py-3.5 text-slate-400 text-xs">{project.created_by_name || '--'}</td>
              <td className="py-3.5 text-slate-500 text-xs">{formatDate(project.created_at)}</td>
              <td className="py-3.5">
                <div className="flex items-center justify-end gap-1">
                  <button
                    onClick={() => onView(project)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                    title="View"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onScans?.(project)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                    title="Scans"
                  >
                    <Radar className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onAssets?.(project)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-sky-400 hover:bg-slate-800 transition-colors"
                    title="Assets"
                  >
                    <Server className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onEdit(project)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-amber-400 hover:bg-slate-800 transition-colors"
                    title="Edit"
                  >
                    <Pencil className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => onDelete(project)}
                    className="p-1.5 rounded-md text-slate-500 hover:text-red-400 hover:bg-slate-800 transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
