import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import api from '../../services/api'
import { Shield, CheckCircle, XCircle } from 'lucide-react'
import Spinner from '../../components/ui/Spinner'
import ThemeToggle from '../../components/ui/ThemeToggle'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('verifying')
  const [message, setMessage] = useState('')
  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) { setStatus('error'); setMessage('No verification token provided'); return }
    const verify = async () => {
      try { const res = await api.post('/api/auth/verify-email', { token }); setStatus('success'); setMessage(res.data.message) } catch (err) { setStatus('error'); setMessage(err.response?.data?.detail || 'Verification failed') }
    }
    verify()
  }, [searchParams])
  return (
    <div className="min-h-screen flex flex-col bg-[var(--background)]">
      <div className="flex justify-end p-4"><ThemeToggle /></div>
      <div className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="w-full max-w-md text-center">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-[var(--primary)] shadow-sm mb-4">
            <Shield className="h-7 w-7 text-white" />
          </div>
          <div className="card">
            {status === 'verifying' && <div className="py-8"><Spinner size="lg" className="mx-auto text-[var(--primary)]" /><p className="text-[var(--muted-foreground)] mt-4">Verifying your email...</p></div>}
            {status === 'success' && <div className="py-8"><CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" /><h2 className="text-xl font-bold text-[var(--foreground)] mb-2">Email Verified!</h2><p className="text-[var(--muted-foreground)] text-sm mb-6">{message}</p><Link to="/login" className="btn-primary inline-block">Sign in to your account</Link></div>}
            {status === 'error' && <div className="py-8"><XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" /><h2 className="text-xl font-bold text-[var(--foreground)] mb-2">Verification Failed</h2><p className="text-[var(--muted-foreground)] text-sm mb-6">{message}</p><Link to="/login" className="btn-primary inline-block">Go to Login</Link></div>}
          </div>
        </div>
      </div>
    </div>
  )
}
