import { Server, Wifi, Lock, Code2, Globe, ShieldCheck, Globe2, Bug, Crosshair, Gauge, Clock, FileText, Bell, FolderOpen } from 'lucide-react'

const features = [
  { icon: Server, title: 'Asset Discovery', desc: 'Subfinder & Amass enumeration with de-duplication and scope validation.' },
  { icon: Wifi, title: 'Live Host Verification', desc: 'HTTPX probing, status codes, titles, and web server detection.' },
  { icon: Lock, title: 'Port Discovery', desc: 'Naabu-powered discovery with service and state enrichment.' },
  { icon: Code2, title: 'Technology Fingerprinting', desc: 'Detect CMS, frameworks, and JavaScript stacks across hosts.' },
  { icon: Globe, title: 'DNS Intelligence', desc: 'DNSX enumeration of records, resolution chains, and misconfigurations.' },
  { icon: ShieldCheck, title: 'SSL Security Analysis', desc: 'Certificate validity, chain, expiry, and TLS posture via SSLyze.' },
  { icon: Globe2, title: 'Web Crawling', desc: 'Katana crawl graph, endpoints, and attack surface expansion.' },
  { icon: Bug, title: 'Vulnerability Assessment', desc: 'Nuclei templates, CVE mapping, and severity triage.' },
  { icon: Crosshair, title: 'Threat Intelligence', desc: 'Shodan, VirusTotal, NVD, and CISA KEV enrichment.' },
  { icon: Gauge, title: 'Risk Assessment', desc: 'Weighted scoring across exposure, exploitability, and business impact.' },
  { icon: Clock, title: 'Historical Comparison', desc: 'Diff scans over time to surface drift and regressions.' },
  { icon: FileText, title: 'Executive Reports', desc: 'PDF/JSON exports with remediation guidance and trends.' },
]

export default function FeatureGrid() {
  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-1">
        <h2 className="text-sm font-bold tracking-tight text-[var(--foreground)]">Core Features</h2>
        <span className="text-[11px] font-bold uppercase tracking-widest text-[var(--muted-foreground)] hidden sm:block">Production-ready • API-driven</span>
      </div>
      <p className="text-xs text-[var(--muted-foreground)] mb-6">All features map to real backend modules — no mock workflows.</p>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <div key={f.title} className="rounded-xl border border-[var(--border)] bg-[var(--muted)]/30 p-4 hover:bg-[var(--card)] hover:shadow-soft transition-all group">
            <div className="h-9 w-9 rounded-xl bg-[var(--card)] border border-[var(--border)] group-hover:bg-[var(--primary)] flex items-center justify-center transition-colors">
              <f.icon className="h-4 w-4 text-[var(--primary)] group-hover:text-white" />
            </div>
            <p className="mt-3 text-sm font-bold text-[var(--foreground)]">{f.title}</p>
            <p className="mt-1 text-xs leading-relaxed text-[var(--muted-foreground)]">{f.desc}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
