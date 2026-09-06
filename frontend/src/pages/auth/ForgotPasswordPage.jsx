import { useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../../services/api'
import { Shield, Mail, ArrowLeft } from 'lucide-react'
import toast from 'react-hot-toast'
import Spinner from '../../components/ui/Spinner'
import ThemeToggle from '../../components/ui/ThemeToggle'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [sent, setSent] = useState(false)
  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!email) { toast.error('Please enter your email'); return }
    setLoading(true)
    try { await api.post('/api/auth/forgot-password', { email }); setSent(true) } catch { toast.error('Something went wrong') } finally { setLoading(false) }
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
            <h1 className="text-2xl font-extrabold tracking-tight text-[var(--foreground)]">Forgot password?</h1>
            <p className="text-[var(--muted-foreground)] mt-1 text-sm">Enter your email and we'll send you a reset link</p>
          </div>
          <div className="card">
            {sent ? (
              <div className="text-center py-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-green-500/10 mb-4">
                  <Mail className="h-6 w-6 text-green-500" />
                </div>
                <h2 className="text-lg font-bold text-[var(--foreground)] mb-2">Check your email</h2>
                <p className="text-[var(--muted-foreground)] text-sm">If an account exists with <span className="font-semibold text-[var(--foreground)]">{email}</span>, we've sent a password reset link.</p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="label">Email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--muted-foreground)]" />
                    <input type="email" className="input-field pl-10" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} disabled={loading} />
                  </div>
                </div>
                <button type="submit" className="btn-primary w-full flex items-center justify-center gap-2" disabled={loading}>
                  {loading && <Spinner size="sm" />}
                  {loading ? 'Sending...' : 'Send reset link'}
                </button>
              </form>
            )}
          </div>
          <p className="text-center text-sm mt-6">
            <Link to="/login" className="inline-flex items-center gap-1 font-semibold text-[var(--primary)] hover:opacity-80"><ArrowLeft className="h-3 w-3" /> Back to sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
