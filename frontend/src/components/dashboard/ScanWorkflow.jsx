import { ArrowRight, ChevronDown } from 'lucide-react'

const workflow = [
  { step: '01', title: 'Target Domain', tool: 'Project Input', desc: 'Scope & authorization' },
  { step: '02', title: 'Asset Discovery', tool: 'Subfinder • Amass', desc: 'Subdomain enumeration' },
  { step: '03', title: 'Live Host Validation', tool: 'HTTPX', desc: 'HTTP probing & status' },
  { step: '04', title: 'Port Discovery', tool: 'Naabu', desc: 'SYN scanning & services' },
  { step: '05', title: 'Technology Detection', tool: 'WhatWeb', desc: 'Stack fingerprinting' },
  { step: '06', title: 'DNS Intelligence', tool: 'DNSX', desc: 'Records & resolution' },
  { step: '07', title: 'SSL Analysis', tool: 'SSLyze', desc: 'Certs & TLS posture' },
  { step: '08', title: 'Web Crawling', tool: 'Katana', desc: 'Endpoints & crawl graph' },
  { step: '09', title: 'Vulnerability Assessment', tool: 'Nuclei', desc: 'Templates & CVEs' },
  { step: '10', title: 'Threat Intelligence', tool: 'Shodan • VT • NVD', desc: 'IOC & reputation' },
  { step: '11', title: 'Risk Assessment', tool: 'Risk Engine', desc: 'Business risk scoring' },
  { step: '12', title: 'Dashboard & Reports', tool: 'React • MongoDB', desc: 'Executive insights' },
]

export default function ScanWorkflow() {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-sm font-bold tracking-tight text-[var(--foreground)]">Core ASM Workflow</h2>
        <span className="hidden sm:inline-flex rounded-full bg-[var(--secondary)] border border-[var(--border)] px-3 py-1 text-[11px] font-bold uppercase tracking-widest text-[var(--secondary-foreground)]">
          12 Stages • Automated
        </span>
      </div>
      <p className="text-xs text-[var(--muted-foreground)] mb-6">End-to-end automation from domain to executive report — every stage is logged and observable.</p>

      {/* Desktop: horizontal wrapped, Mobile: vertical */}
      <div className="hidden lg:grid grid-cols-4 xl:grid-cols-6 gap-3">
        {workflow.map((s, i) => (
          <div key={s.step} className="relative group">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/30 hover:bg-[var(--card)] hover:border-[var(--primary)]/20 hover:shadow-soft p-4 h-full transition-all">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-extrabold tracking-widest text-[var(--primary)]">{s.step}</span>
                {i < workflow.length - 1 && <ArrowRight className="h-3 w-3 text-[var(--muted-foreground)]/50 hidden xl:block" />}
              </div>
              <p className="mt-1 text-sm font-bold leading-tight text-[var(--foreground)]">{s.title}</p>
              <p className="mt-1 text-[11px] font-semibold text-[var(--primary)]">{s.tool}</p>
              <p className="mt-1 text-[11px] leading-snug text-[var(--muted-foreground)]">{s.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="lg:hidden flex flex-col items-center gap-0">
        {workflow.map((s, i) => (
          <div key={s.step} className="flex flex-col items-center w-full max-w-[360px]">
            <div className="w-full rounded-xl border border-[var(--border)] bg-[var(--muted)]/30 px-4 py-3.5 flex items-center gap-3 text-left">
              <span className="h-8 w-8 rounded-lg bg-[var(--primary)] text-white flex items-center justify-center text-xs font-bold flex-shrink-0">{s.step}</span>
              <div className="min-w-0">
                <p className="text-sm font-bold text-[var(--foreground)] leading-none">{s.title}</p>
                <p className="text-[11px] font-semibold text-[var(--primary)]">{s.tool}</p>
              </div>
            </div>
            {i < workflow.length - 1 && <ChevronDown className="h-4 w-4 text-[var(--border)] my-1.5" />}
          </div>
        ))}
      </div>
    </div>
  )
}
