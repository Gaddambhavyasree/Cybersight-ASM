export default function SectionPage({ title, description }) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">{title}</h1>
        {description && <p className="text-slate-400 text-sm mt-1">{description}</p>}
      </div>
      <div className="card flex items-center justify-center py-20">
        <p className="text-slate-500 text-sm">This section is under development.</p>
      </div>
    </div>
  )
}
