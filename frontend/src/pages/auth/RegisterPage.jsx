import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { getApiErrorMessage } from '../../services/api'
import { Shield, User, Mail, Lock, Eye, EyeOff } from 'lucide-react'
import toast from 'react-hot-toast'
import Spinner from '../../components/ui/Spinner'
import ThemeToggle from '../../components/ui/ThemeToggle'

export default function RegisterPage() {
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm_password: '' })
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const { register } = useAuth()

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.full_name || !form.email || !form.password || !form.confirm_password) { toast.error('Please fill in all fields'); return }
    if (form.password.length < 8) { toast.error('Password must be at least 8 characters'); return }
    if (form.password !== form.confirm_password) { toast.error('Passwords do not match'); return }
    setLoading(true)
    try {
      const result = await register({ ...form, full_name: form.full_name.trim(), email: form.email.trim().toLowerCase() })
      toast.success(result.message || 'Registration successful! Check your email.')
      setForm({ full_name: '', email: '', password: '', confirm_password: '' })
    } catch (err) { toast.error(getApiErrorMessage(err, 'Registration failed')) } finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <div className="flex justify-end p-4"><ThemeToggle /></div>
      <div className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--primary)] shadow-sm mb-4">
              <Shield className="h-7 w-7 text-white" />
            </div>
            <p className="text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--primary)]">CyberSight ASM</p>
            <h1 className="text-2xl font-extrabold tracking-tight text-[var(--foreground)] mt-1">Create an account</h1>
            <p className="text-[var(--muted-foreground)] mt-1.5 text-sm">Join CyberSight ASM to start attack surface management</p>
          </div>

          <div className="card">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label className="label">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                  <input type="text" name="full_name" className="input-field pl-10" placeholder="John Doe" value={form.full_name} onChange={handleChange} disabled={loading} />
                </div>
              </div>
              <div>
                <label className="label">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                  <input type="email" name="email" autoComplete="email" className="input-field pl-10" placeholder="you@example.com" value={form.email} onChange={handleChange} disabled={loading} />
                </div>
              </div>
              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                  <input type={showPassword ? 'text' : 'password'} name="password" autoComplete="new-password" className="input-field pl-10 pr-10" placeholder="At least 8 characters" value={form.password} onChange={handleChange} disabled={loading} />
                  <button type="button" onClick={() => setShowPassword(!showPassword)} className="absolute right-1 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-lg text-[var(--muted-foreground)] hover:bg-[var(--muted)]">
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>
              <div>
                <label className="label">Confirm Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                  <input type={showPassword ? 'text' : 'password'} name="confirm_password" autoComplete="new-password" className="input-field pl-10" placeholder="Confirm your password" value={form.confirm_password} onChange={handleChange} disabled={loading} />
                </div>
              </div>
              <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                {loading && <Spinner size="sm" />}
                {loading ? 'Creating account...' : 'Create account'}
              </button>
            </form>
          </div>

          <p className="text-center text-sm text-[var(--muted-foreground)] mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-[var(--primary)] hover:opacity-80 font-semibold">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
