import { Link } from 'react-router-dom'
import { ShieldX, ArrowLeft } from 'lucide-react'

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-red-500/10 mb-6">
          <ShieldX className="h-8 w-8 text-red-500" />
        </div>
        <h1 className="text-6xl font-bold text-slate-200 mb-4">403</h1>
        <p className="text-slate-400 text-lg mb-8">You don't have permission to access this page.</p>
        <Link to="/dashboard" className="btn-primary inline-flex items-center gap-2">
          <ArrowLeft className="h-4 w-4" />
          Back to Dashboard
        </Link>
      </div>
    </div>
  )
}
