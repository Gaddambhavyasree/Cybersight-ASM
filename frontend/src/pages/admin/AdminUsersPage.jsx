import { useState, useEffect } from 'react'
import api from '../../services/api'
import { Users, Search, ChevronLeft, ChevronRight, Shield } from 'lucide-react'
import toast from 'react-hot-toast'
import Spinner from '../../components/ui/Spinner'
import EmptyState from '../../components/ui/EmptyState'
import Modal from '../../components/ui/Modal'

const ROLES = [
  { value: 'admin', label: 'Admin' },
  { value: 'threat_analyst', label: 'Threat Analyst' },
  { value: 'soc_analyst', label: 'SOC Analyst' },
  { value: 'viewer', label: 'Viewer' },
]

const ROLE_BADGE = {
  admin: 'bg-red-500/10 text-red-400 border-red-500/20',
  threat_analyst: 'bg-[var(--primary)] text-[var(--primary)] border-[var(--primary)]',
  soc_analyst: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
  viewer: 'bg-slate-500/10 text-[var(--muted-foreground)] border-slate-500/20',
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [roleModal, setRoleModal] = useState(null)
  const [deleteModal, setDeleteModal] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const perPage = 10

  const fetchUsers = async () => {
    setLoading(true)
    try {
      const params = { page, per_page: perPage }
      if (search) params.search = search
      const res = await api.get('/api/admin/users', { params })
      setUsers(res.data.users)
      setTotal(res.data.total)
    } catch (err) {
      toast.error('Failed to load users')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers()
  }, [page])

  const handleSearch = (e) => {
    e.preventDefault()
    setPage(1)
    fetchUsers()
  }

  const handleRoleChange = async (userId, newRole) => {
    setActionLoading(true)
    try {
      await api.put(`/api/admin/users/${userId}/role`, { role: newRole })
      toast.success('Role updated')
      setRoleModal(null)
      fetchUsers()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update role')
    } finally {
      setActionLoading(false)
    }
  }

  const handleToggleActive = async (userId, isActive) => {
    setActionLoading(true)
    try {
      await api.put(`/api/admin/users/${userId}/active`, { is_active: isActive })
      toast.success(isActive ? 'User activated' : 'User deactivated')
      fetchUsers()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to update user')
    } finally {
      setActionLoading(false)
    }
  }

  const handleDelete = async (userId) => {
    setActionLoading(true)
    try {
      await api.delete(`/api/admin/users/${userId}`)
      toast.success('User deleted')
      setDeleteModal(null)
      fetchUsers()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to delete user')
    } finally {
      setActionLoading(false)
    }
  }

  const totalPages = Math.ceil(total / perPage)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[var(--foreground)]">User Management</h1>
        <p className="text-[var(--muted-foreground)] mt-1">Manage users and their roles</p>
      </div>

      <div className="card">
        <form onSubmit={handleSearch} className="flex gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
            <input
              type="text"
              className="input-field pl-10"
              placeholder="Search by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-primary">Search</button>
        </form>

        {loading ? (
          <div className="flex justify-center py-12">
            <Spinner size="lg" className="text-[var(--primary)]" />
          </div>
        ) : users.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No users found"
            description={search ? 'Try a different search term' : 'No users have registered yet'}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[var(--muted-foreground)] border-b border-[var(--border)]">
                    <th className="pb-3 font-medium">User</th>
                    <th className="pb-3 font-medium">Role</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Verified</th>
                    <th className="pb-3 font-medium text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-[var(--muted)]">
                      <td className="py-3">
                        <div>
                          <p className="font-medium text-[var(--foreground)]">{u.full_name}</p>
                          <p className="text-xs text-[var(--muted-foreground)]">{u.email}</p>
                        </div>
                      </td>
                      <td className="py-3">
                        <span className={`text-xs font-medium px-2 py-1 rounded-md border ${ROLE_BADGE[u.role]}`}>
                          {ROLES.find(r => r.value === u.role)?.label || u.role}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`text-xs font-medium px-2 py-1 rounded-md ${u.is_active ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                          {u.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={`text-xs font-medium px-2 py-1 rounded-md ${u.email_verified ? 'bg-green-500/10 text-green-400' : 'bg-amber-500/10 text-amber-400'}`}>
                          {u.email_verified ? 'Yes' : 'No'}
                        </span>
                      </td>
                      <td className="py-3">
                        <div className="flex items-center justify-end gap-2">
                          <button
                            onClick={() => setRoleModal(u)}
                            className="text-xs text-[var(--muted-foreground)] hover:text-[var(--primary)] px-2 py-1 rounded hover:bg-[var(--muted)] transition-colors"
                          >
                            Role
                          </button>
                          <button
                            onClick={() => handleToggleActive(u.id, !u.is_active)}
                            className={`text-xs px-2 py-1 rounded transition-colors ${u.is_active ? 'text-amber-400 hover:bg-[var(--muted)]' : 'text-green-400 hover:bg-[var(--muted)]'}`}
                          >
                            {u.is_active ? 'Deactivate' : 'Activate'}
                          </button>
                          <button
                            onClick={() => setDeleteModal(u)}
                            className="text-xs text-red-400 hover:bg-[var(--muted)] px-2 py-1 rounded transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {totalPages > 1 && (
              <div className="flex items-center justify-between mt-6 pt-4 border-t border-[var(--border)]">
                <p className="text-sm text-[var(--muted-foreground)]">
                  Showing {(page - 1) * perPage + 1}-{Math.min(page * perPage, total)} of {total}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="p-1.5 rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)] disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <span className="text-sm text-[var(--muted-foreground)]">Page {page} of {totalPages}</span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="p-1.5 rounded-lg text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)] disabled:opacity-30 disabled:cursor-not-allowed"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Role Change Modal */}
      <Modal isOpen={!!roleModal} onClose={() => setRoleModal(null)} title="Change User Role">
        {roleModal && (
          <div className="space-y-4">
            <p className="text-sm text-[var(--muted-foreground)]">
              Change role for <span className="text-[var(--foreground)] font-medium">{roleModal.full_name}</span>
            </p>
            <div className="space-y-2">
              {ROLES.map((role) => (
                <button
                  key={role.value}
                  onClick={() => handleRoleChange(roleModal.id, role.value)}
                  disabled={actionLoading || roleModal.role === role.value}
                  className={`w-full text-left px-4 py-3 rounded-lg border transition-colors ${
                    roleModal.role === role.value
                      ? 'border-[var(--primary)] bg-[var(--primary)] text-[var(--primary)]'
                      : 'border-[var(--border)] hover:border-[var(--border)] text-[var(--foreground)] hover:bg-[var(--muted)]'
                  } disabled:opacity-50`}
                >
                  <span className="font-medium text-sm">{role.label}</span>
                  {roleModal.role === role.value && (
                    <span className="text-xs text-[var(--primary)] ml-2">(current)</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal isOpen={!!deleteModal} onClose={() => setDeleteModal(null)} title="Delete User">
        {deleteModal && (
          <div className="space-y-4">
            <p className="text-sm text-[var(--muted-foreground)]">
              Are you sure you want to delete <span className="text-[var(--foreground)] font-medium">{deleteModal.full_name}</span>?
              This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setDeleteModal(null)}
                className="btn-secondary text-sm"
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteModal.id)}
                className="btn-danger text-sm flex items-center gap-2"
                disabled={actionLoading}
              >
                {actionLoading && <Spinner size="sm" />}
                Delete
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}
