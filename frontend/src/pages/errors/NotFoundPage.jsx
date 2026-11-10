import { Link } from 'react-router-dom'
import { AlertTriangle, ArrowLeft } from 'lucide-react'

export default function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-slate-800 mb-6">
          <AlertTriangle className="h-8 w-8 text-slate-500" />
        </div>
        <h1 className="text-6xl font-bold text-slate-200 mb-4">404</h1>
        <p className="text-slate-400 text-lg mb-8">The page you're looking for doesn't exist.</p>
        <Link to="/" className="btn-primary inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Go Home
        </Link>
      </div>
    </div>
  )
}
