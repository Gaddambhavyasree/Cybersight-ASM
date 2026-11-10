import { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import api from '../../services/api'
import { Shield, Lock, Eye, EyeOff, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import Spinner from '../../components/ui/Spinner'

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [form, setForm] = useState({ password: '', confirm_password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.password || !form.confirm_password) {
      toast.error('Please fill in all fields')
      return
    }
    if (form.password.length < 8) {
      toast.error('Password must be at least 8 characters')
      return
    }
    if (form.password !== form.confirm_password) {
      toast.error('Passwords do not match')
      return
    }
    if (!token) {
      toast.error('No reset token found')
      return
    }

    setLoading(true)
    try {
      await api.post('/api/auth/reset-password', { token, ...form })
      setSuccess(true)
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Reset failed')
    } finally {
      setLoading(false)
    }
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center px-4">
        <div className="card text-center">
          <p className="text-slate-400 mb-4">Invalid reset link. Please request a new one.</p>
          <Link to="/forgot-password" className="btn-primary">Request new link</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-sky-500/10 mb-4">
            <Shield className="h-7 w-7 text-sky-500" />
          </div>
          <h1 className="text-2xl font-bold text-slate-100">Reset password</h1>
          <p className="text-slate-400 mt-1 text-sm">Enter your new password below</p>
        </div>

        <div className="card">
          {success ? (
            <div className="text-center py-4">
              <h2 className="text-lg font-semibold text-slate-100 mb-2">Password Reset!</h2>
              <p className="text-slate-400 text-sm mb-6">Your password has been updated successfully.</p>
              <Link to="/login" className="btn-primary inline-block">Sign in with new password</Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="label">New Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="password"
                    className="input-field pl-10 pr-10"
                    placeholder="At least 8 characters"
                    value={form.password}
                    onChange={handleChange}
                    disabled={loading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              <div>
                <label className="label">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    name="confirm_password"
                    className="input-field pl-10"
                    placeholder="Confirm your password"
                    value={form.confirm_password}
                    onChange={handleChange}
                    disabled={loading}
                  />
                </div>
              </div>

              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                {loading && <Spinner size="sm" />}
                {loading ? 'Resetting...' : 'Reset password'}
              </button>
            </form>
          )}
        </div>

        <p className="text-center text-sm text-slate-400 mt-6">
          <Link to="/login" className="inline-flex items-center gap-1 text-sky-400 hover:text-sky-300 font-medium transition-colors">
            <ArrowLeft className="h-3 w-3" />
            Back to sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
