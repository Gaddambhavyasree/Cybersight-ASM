import { useState, useEffect } from 'react'
import { useAuth } from '../../contexts/AuthContext'
import api from '../../services/api'
import { UserCircle, Lock, Save } from 'lucide-react'
import toast from 'react-hot-toast'
import Spinner from '../../components/ui/Spinner'

export default function ProfilePage() {
  const { user, updateUser } = useAuth()
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(false)
  const [passwordForm, setPasswordForm] = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('profile')

  useEffect(() => {
    if (user) setName(user.full_name)
  }, [user])

  const handleNameUpdate = async (e) => {
    e.preventDefault()
    if (!name.trim()) {
      toast.error('Name cannot be empty')
      return
    }

    setLoading(true)
    try {
      const res = await api.put('/api/users/me', { full_name: name.trim() })
      updateUser(res.data)
      toast.success('Profile updated')
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Update failed')
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()
    if (!passwordForm.current_password || !passwordForm.new_password || !passwordForm.confirm_password) {
      toast.error('Please fill in all fields')
      return
    }
    if (passwordForm.new_password.length < 8) {
      toast.error('New password must be at least 8 characters')
      return
    }
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      toast.error('New passwords do not match')
      return
    }

    setPasswordLoading(true)
    try {
      await api.post('/api/users/change-password', passwordForm)
      toast.success('Password changed successfully')
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Password change failed')
    } finally {
      setPasswordLoading(false)
    }
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">Profile</h1>
        <p className="text-slate-400 mt-1">Manage your account settings</p>
      </div>

      <div className="flex gap-1 bg-slate-900 border border-slate-800 rounded-lg p-1 w-fit">
        <button
          onClick={() => setActiveTab('profile')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'profile' ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Profile
        </button>
        <button
          onClick={() => setActiveTab('password')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === 'password' ? 'bg-slate-800 text-slate-100' : 'text-slate-400 hover:text-slate-200'}`}
        >
          Password
        </button>
      </div>

      {activeTab === 'profile' && (
        <div className="card max-w-lg">
          <div className="flex items-center gap-3 mb-6">
            <UserCircle className="h-5 w-5 text-sky-500" />
            <h2 className="font-semibold text-slate-100">Personal Information</h2>
          </div>
          <form onSubmit={handleNameUpdate} className="space-y-5">
            <div>
              <label className="label">Full Name</label>
              <input
                type="text"
                className="input-field"
                value={name}
                onChange={(e) => setName(e.target.value)}
                disabled={loading}
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input-field"
                value={user?.email || ''}
                disabled
              />
              <p className="text-xs text-slate-500 mt-1">Email cannot be changed</p>
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={loading}>
              {loading ? <Spinner size="sm" /> : <Save className="h-4 w-4" />}
              {loading ? 'Saving...' : 'Save Changes'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'password' && (
        <div className="card max-w-lg">
          <div className="flex items-center gap-3 mb-6">
            <Lock className="h-5 w-5 text-sky-500" />
            <h2 className="font-semibold text-slate-100">Change Password</h2>
          </div>
          <form onSubmit={handlePasswordChange} className="space-y-5">
            <div>
              <label className="label">Current Password</label>
              <input
                type="password"
                className="input-field"
                placeholder="Enter current password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, current_password: e.target.value })}
                disabled={passwordLoading}
              />
            </div>
            <div>
              <label className="label">New Password</label>
              <input
                type="password"
                className="input-field"
                placeholder="At least 8 characters"
                value={passwordForm.new_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                disabled={passwordLoading}
              />
            </div>
            <div>
              <label className="label">Confirm New Password</label>
              <input
                type="password"
                className="input-field"
                placeholder="Confirm new password"
                value={passwordForm.confirm_password}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                disabled={passwordLoading}
              />
            </div>
            <button type="submit" className="btn-primary flex items-center gap-2" disabled={passwordLoading}>
              {passwordLoading ? <Spinner size="sm" /> : <Lock className="h-4 w-4" />}
              {passwordLoading ? 'Changing...' : 'Change Password'}
            </button>
          </form>
        </div>
      )}
    </div>
  )
}
