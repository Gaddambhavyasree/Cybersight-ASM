import { AlertTriangle } from 'lucide-react'

export default function EmptyState({ icon: Icon = AlertTriangle, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-14 h-14 rounded-full bg-slate-800 flex items-center justify-center mb-4">
        <Icon className="h-7 w-7 text-slate-500" />
      </div>
      <h3 className="text-lg font-semibold text-slate-200 mb-1">{title}</h3>
      {description && <p className="text-slate-400 text-sm max-w-md">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}
