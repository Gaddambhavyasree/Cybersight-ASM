import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import api from '../../services/api'
import { Shield, CheckCircle, XCircle } from 'lucide-react'
import Spinner from '../../components/ui/Spinner'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const [status, setStatus] = useState('verifying')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setStatus('error')
      setMessage('No verification token provided')
      return
    }

    const verify = async () => {
      try {
        const res = await api.post('/api/auth/verify-email', { token })
        setStatus('success')
        setMessage(res.data.message)
      } catch (err) {
        setStatus('error')
        setMessage(err.response?.data?.detail || 'Verification failed')
      }
    }

    verify()
  }, [searchParams])

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-sky-500/10 mb-4">
          <Shield className="h-7 w-7 text-sky-500" />
        </div>

        <div className="card">
          {status === 'verifying' && (
            <div className="py-8">
              <Spinner size="lg" className="mx-auto text-sky-500" />
              <p className="text-slate-400 mt-4">Verifying your email...</p>
            </div>
          )}

          {status === 'success' && (
            <div className="py-8">
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-100 mb-2">Email Verified!</h2>
              <p className="text-slate-400 text-sm mb-6">{message}</p>
              <Link to="/login" className="btn-primary inline-block">
                Sign in to your account
              </Link>
            </div>
          )}

          {status === 'error' && (
            <div className="py-8">
              <XCircle className="h-16 w-16 text-red-500 mx-auto mb-4" />
              <h2 className="text-xl font-semibold text-slate-100 mb-2">Verification Failed</h2>
              <p className="text-slate-400 text-sm mb-6">{message}</p>
              <Link to="/login" className="btn-primary inline-block">
                Go to Login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
