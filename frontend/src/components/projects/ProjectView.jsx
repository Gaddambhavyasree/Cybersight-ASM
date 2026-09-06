import Modal from '../ui/Modal'

const STATUS_STYLES = {
  active: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  inactive: 'bg-slate-500/10 text-[var(--muted-foreground)] border-slate-500/20',
  archived: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}

export default function ProjectView({ isOpen, onClose, project }) {
  if (!project) return null

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Project Details">
      <div className="space-y-4">
        <div>
          <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Project Name</p>
          <p className="text-sm text-[var(--foreground)] font-medium">{project.name}</p>
        </div>

        {project.organization && (
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Organization</p>
            <p className="text-sm text-[var(--foreground)]">{project.organization}</p>
          </div>
        )}

        <div>
          <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Target Domain</p>
          <p className="text-sm text-[var(--primary)] font-mono">{project.target_domain}</p>
        </div>

        {project.description && (
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Description</p>
            <p className="text-sm text-[var(--foreground)]">{project.description}</p>
          </div>
        )}

        {project.tags?.length > 0 && (
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Tags</p>
            <div className="flex gap-1.5 flex-wrap">
              {project.tags.map((tag) => (
                <span key={tag} className="text-xs bg-[var(--muted)] text-[var(--muted-foreground)] px-2 py-1 rounded-md border border-[var(--border)]">
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        <div>
          <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Status</p>
          <span className={`text-xs font-medium px-2 py-1 rounded-md border ${STATUS_STYLES[project.status] || STATUS_STYLES.active}`}>
            {project.status?.charAt(0).toUpperCase() + project.status?.slice(1)}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-4 pt-2 border-t border-[var(--border)]">
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Created By</p>
            <p className="text-sm text-[var(--foreground)]">{project.created_by_name || '--'}</p>
          </div>
          <div>
            <p className="text-xs text-[var(--muted-foreground)] uppercase tracking-wider mb-1">Created At</p>
            <p className="text-sm text-[var(--foreground)]">{formatDate(project.created_at)}</p>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button onClick={onClose} className="btn-secondary text-sm">Close</button>
        </div>
      </div>
    </Modal>
  )
}
