'use client'

import { useEffect, useRef, useState, useCallback } from 'react'

/* ── Types ─────────────────────────────────────────────────────── */
interface GraphNode {
  x: number; y: number
  vx: number; vy: number
  radius: number; active: boolean; pulsePhase: number
}

/* ── Knowledge Graph Canvas ─────────────────────────────────────── */
function KnowledgeGraphCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const rafRef = useRef<number | undefined>(undefined)
  const nodes = useRef<GraphNode[]>([])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const resize = () => {
      const dpr = window.devicePixelRatio || 1
      canvas.width = canvas.offsetWidth * dpr
      canvas.height = canvas.offsetHeight * dpr
      ctx.scale(dpr, dpr)
    }
    resize()
    window.addEventListener('resize', resize)

    nodes.current = Array.from({ length: 55 }, () => ({
      x: Math.random() * canvas.offsetWidth,
      y: Math.random() * canvas.offsetHeight,
      vx: (Math.random() - 0.5) * 0.25,
      vy: (Math.random() - 0.5) * 0.25,
      radius: Math.random() * 2.5 + 1,
      active: Math.random() < 0.12,
      pulsePhase: Math.random() * Math.PI * 2,
    }))

    const draw = () => {
      const w = canvas.offsetWidth
      const h = canvas.offsetHeight
      ctx.clearRect(0, 0, w, h)

      nodes.current.forEach(n => {
        n.x += n.vx; n.y += n.vy; n.pulsePhase += 0.018
        if (n.x < 0 || n.x > w) n.vx *= -1
        if (n.y < 0 || n.y > h) n.vy *= -1
      })

      // Edges
      for (let i = 0; i < nodes.current.length; i++) {
        for (let j = i + 1; j < nodes.current.length; j++) {
          const a = nodes.current[i], b = nodes.current[j]
          const dx = a.x - b.x, dy = a.y - b.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          if (dist < 120) {
            const t = 1 - dist / 120
            const hot = a.active || b.active
            ctx.beginPath()
            ctx.moveTo(a.x, a.y)
            ctx.lineTo(b.x, b.y)
            ctx.strokeStyle = hot
              ? `rgba(0,198,245,${t * 0.35})`
              : `rgba(26,60,100,${t * 0.4})`
            ctx.lineWidth = hot ? 0.8 : 0.4
            ctx.stroke()
          }
        }
      }

      // Nodes
      nodes.current.forEach(n => {
        const pulse = Math.sin(n.pulsePhase) * 0.5 + 0.5
        if (n.active) {
          const g = ctx.createRadialGradient(n.x, n.y, 0, n.x, n.y, n.radius * 5)
          g.addColorStop(0, `rgba(0,198,245,${0.25 * pulse})`)
          g.addColorStop(1, 'rgba(0,198,245,0)')
          ctx.beginPath(); ctx.arc(n.x, n.y, n.radius * 5, 0, Math.PI * 2)
          ctx.fillStyle = g; ctx.fill()
          ctx.beginPath(); ctx.arc(n.x, n.y, n.radius + pulse, 0, Math.PI * 2)
          ctx.fillStyle = `rgba(0,198,245,${0.85 + pulse * 0.15})`; ctx.fill()
        } else {
          ctx.beginPath(); ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2)
          ctx.fillStyle = 'rgba(26,60,100,0.9)'; ctx.fill()
        }
      })

      rafRef.current = requestAnimationFrame(draw)
    }
    draw()

    return () => {
      window.removeEventListener('resize', resize)
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />
}

/* ── Counter ────────────────────────────────────────────────────── */
function Counter({ end, suffix = '', duration = 1800, trigger }: {
  end: number; suffix?: string; duration?: number; trigger: boolean
}) {
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!trigger) return
    let start: number | null = null
    const step = (ts: number) => {
      if (!start) start = ts
      const p = Math.min((ts - start) / duration, 1)
      const eased = 1 - Math.pow(1 - p, 3)
      setVal(Math.floor(eased * end))
      if (p < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [trigger, end, duration])
  return <>{val}{suffix}</>
}

/* ── Intersection Observer Hook ─────────────────────────────────── */
function useReveal() {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) { setVisible(true); obs.disconnect() }
    }, { threshold: 0.15 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])
  return { ref, visible }
}

/* ── Data ───────────────────────────────────────────────────────── */
const features = [
  {
    sym: '⬡', label: 'GRAPH', title: 'GraphRAG Knowledge Engine',
    desc: 'Builds a live knowledge graph from your documents. Multi-hop reasoning across entities and relationships — no SQL required.',
    tag: 'Core Technology',
  },
  {
    sym: '◎', label: 'DOMAIN', title: 'Auto Domain Detection',
    desc: 'Identifies your industry context — Beauty, Supply Chain, Energy, Manufacturing, Logistics, Finance — and calibrates analysis accordingly.',
    tag: '90% Accuracy',
  },
  {
    sym: '▦', label: 'BRIEF', title: 'Daily AI Briefings',
    desc: '4-card automated briefing every morning: inventory alerts, top performers, reorder triggers, and anomaly flags. Zero manual effort.',
    tag: 'Automated',
  },
  {
    sym: '◈', label: 'CHAT', title: 'Intelligent Data Chat',
    desc: 'Five query modes — Charts, Rankings, Comparisons, Risk, and Descriptions. Every answer comes with source citations and next actions.',
    tag: 'Claude AI',
  },
  {
    sym: '⊞', label: 'INGEST', title: 'Universal Data Ingestion',
    desc: 'CSV, PDF, Excel, DOCX — upload anything. FK relationships auto-detected. Tables link. Patterns surface automatically.',
    tag: 'Any Format',
  },
  {
    sym: '◑', label: 'STREAM', title: 'Streaming Responses',
    desc: 'Real-time streamed answers with data provenance. Each response tagged with CSV, Document, or Knowledge Graph source badges.',
    tag: 'Real-time',
  },
]

const domains = [
  { name: 'Beauty / E-commerce', sym: '◉', color: '#e91e8c', glow: 'rgba(233,30,140,0.15)', desc: 'SKU · MOQ · Lead Time · D2C' },
  { name: 'Supply Chain', sym: '◎', color: '#00c6f5', glow: 'rgba(0,198,245,0.15)', desc: 'Safety Stock · Reorder · ABC' },
  { name: 'Energy', sym: '◈', color: '#f59e0b', glow: 'rgba(245,158,11,0.15)', desc: 'Generation · Peak · Power Factor' },
  { name: 'Manufacturing', sym: '⊞', color: '#10b981', glow: 'rgba(16,185,129,0.15)', desc: 'OEE · Utilization · Defect Rate' },
  { name: 'Logistics', sym: '⬡', color: '#8b5cf6', glow: 'rgba(139,92,246,0.15)', desc: 'Delivery Rate · Routes · Fleet' },
  { name: 'Finance', sym: '◑', color: '#06b6d4', glow: 'rgba(6,182,212,0.15)', desc: 'Credit Score · Risk · Anomaly' },
]

const steps = [
  {
    num: '01', title: 'Upload Your Data',
    desc: 'Drop in any combination of CSV files, PDFs, Excel sheets, or documents. The system ingests everything.',
    detail: 'CSV · PDF · XLSX · DOCX',
  },
  {
    num: '02', title: 'AI Builds Context',
    desc: 'Knowledge graphs form automatically. FK relationships are traced. Domain is detected. Everything is indexed for semantic search.',
    detail: 'GraphRAG · Domain Detection · Vector Index',
  },
  {
    num: '03', title: 'Insights & Action',
    desc: 'Get daily briefings, ask questions in natural language, and receive evidence-backed recommendations with clear next steps.',
    detail: 'Briefings · Chat · Action Items',
  },
]

const statItems = [
  { end: 90, suffix: '%', label: 'Domain Detection', sub: '18/20 test cases' },
  { end: 100, suffix: '%', label: 'FK Detection Precision', sub: 'Zero false positives' },
  { end: 6, suffix: '+', label: 'Industry Domains', sub: 'Plus custom domains' },
  { end: 3, suffix: 's', label: 'Avg. Time to Insight', sub: 'From upload to answer' },
]

/* ── Main Page ──────────────────────────────────────────────────── */
export default function Page() {
  const [menuOpen, setMenuOpen] = useState(false)
  const statsSection = useReveal()
  const featSection = useReveal()
  const stepsSection = useReveal()
  const domainsSection = useReveal()

  return (
    <div className="min-h-screen bg-bg text-ink font-sans">

      {/* ── Nav ── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 bg-bg/80 backdrop-blur-xl">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-accent text-xl leading-none">⬡</span>
            <span className="font-display font-700 text-ink tracking-tight text-[15px]">
              OPS<span className="text-accent">.</span>COPILOT
            </span>
          </div>

          <div className="hidden md:flex items-center gap-8 text-[13px] text-muted font-medium">
            {['Features', 'How it works', 'Domains', 'Pricing'].map(l => (
              <a key={l} href={`#${l.toLowerCase().replace(/ /g, '-')}`}
                className="hover:text-ink transition-colors duration-200">{l}</a>
            ))}
          </div>

          <div className="hidden md:flex items-center gap-3">
            <button className="text-[13px] text-muted hover:text-ink transition-colors px-4 py-2 font-medium">
              Sign in
            </button>
            <button className="text-[13px] font-semibold bg-accent text-bg px-4 py-2 rounded-md hover:bg-accent/90 transition-colors">
              Request Demo
            </button>
          </div>

          <button className="md:hidden text-muted hover:text-ink" onClick={() => setMenuOpen(!menuOpen)}>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d={menuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
            </svg>
          </button>
        </div>

        {menuOpen && (
          <div className="md:hidden border-t border-border/50 bg-bg/95 px-6 py-4 flex flex-col gap-4">
            {['Features', 'How it works', 'Domains', 'Pricing'].map(l => (
              <a key={l} href={`#${l.toLowerCase().replace(/ /g, '-')}`}
                className="text-sm text-muted hover:text-ink"
                onClick={() => setMenuOpen(false)}>{l}</a>
            ))}
            <button className="mt-2 text-[13px] font-semibold bg-accent text-bg px-4 py-2 rounded-md w-full">
              Request Demo
            </button>
          </div>
        )}
      </nav>

      {/* ── Hero ── */}
      <section className="relative min-h-screen flex flex-col justify-center overflow-hidden pt-16">
        {/* Background graph */}
        <div className="absolute inset-0 opacity-70">
          <KnowledgeGraphCanvas />
        </div>

        {/* Grid overlay */}
        <div className="absolute inset-0 grid-bg opacity-30" />

        {/* Radial glow */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] rounded-full"
          style={{ background: 'radial-gradient(circle, rgba(0,198,245,0.06) 0%, transparent 70%)' }} />

        <div className="relative z-10 max-w-7xl mx-auto px-6 py-24 grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Copy */}
          <div>
            {/* Badge */}
            <div className="inline-flex items-center gap-2 border border-accent/30 bg-accent/5 rounded-full px-3 py-1.5 mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              <span className="font-mono text-[11px] text-accent tracking-widest uppercase">
                Powered by Claude AI · Anthropic
              </span>
            </div>

            <h1 className="font-display text-5xl lg:text-6xl xl:text-7xl font-800 leading-[0.95] tracking-tight mb-6">
              <span className="text-ink">Your operations</span>
              <br />
              <span className="text-ink">data, finally</span>
              <br />
              <span className="gradient-text">speaking to you.</span>
            </h1>

            <p className="text-muted text-lg leading-relaxed max-w-lg mb-10">
              Upload your CSV files, PDFs, and reports. Ops Copilot builds a live
              knowledge graph, detects problems, and tells you exactly what to do —
              before your next standup.
            </p>

            <div className="flex flex-wrap gap-3">
              <button className="group relative px-6 py-3 bg-accent text-bg font-semibold text-sm rounded-md hover:bg-accent/90 transition-all duration-200 glow-accent">
                Start Free Trial
                <span className="ml-2 group-hover:translate-x-0.5 inline-block transition-transform">→</span>
              </button>
              <button className="px-6 py-3 border border-border text-ink/70 font-medium text-sm rounded-md hover:border-accent/40 hover:text-ink transition-all duration-200">
                Watch Demo
                <span className="ml-2 text-muted">▶</span>
              </button>
            </div>

            <div className="mt-10 flex items-center gap-6 text-[12px] text-muted font-mono">
              <span className="flex items-center gap-1.5">
                <span className="text-emerald">■</span> No credit card required
              </span>
              <span className="flex items-center gap-1.5">
                <span className="text-accent">■</span> Up in 2 minutes
              </span>
            </div>
          </div>

          {/* Right: Mock briefing card */}
          <div className="relative hidden lg:block">
            <div className="relative">
              {/* Outer glow */}
              <div className="absolute -inset-px rounded-xl bg-gradient-to-br from-accent/20 via-transparent to-purple-500/10" />

              {/* Card */}
              <div className="relative bg-surface border border-border rounded-xl overflow-hidden glow-accent">
                {/* Card header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface-2">
                  <div className="flex items-center gap-2">
                    <span className="text-accent text-sm">⬡</span>
                    <span className="font-mono text-[11px] text-muted uppercase tracking-widest">
                      Daily Briefing
                    </span>
                  </div>
                  <span className="font-mono text-[10px] text-muted/60">2026.04.19 · 09:00</span>
                </div>

                {/* Scan line */}
                <div className="relative scanline">
                  {/* Briefing cards */}
                  <div className="p-4 space-y-3">
                    {[
                      {
                        label: 'INVENTORY RISK', color: '#ef4444', icon: '⚠',
                        title: '3 SKUs below safety stock',
                        detail: 'PRD001 · PRD002 · PRD007',
                        sub: 'Action: Issue reorder today — lead time 7–14d',
                      },
                      {
                        label: 'TOP PERFORMER', color: '#10b981', icon: '↑',
                        title: 'Sunscreen +38% MoM',
                        detail: 'PRD002 · D2C Channel',
                        sub: 'Peak season approaching — stock buffer recommended',
                      },
                      {
                        label: 'ANOMALY', color: '#f59e0b', icon: '◈',
                        title: 'Supplier lead time +6d',
                        detail: 'SUP001 · CosmeLab',
                        sub: 'Deviation from 14d avg — confirm with supplier',
                      },
                    ].map((card, i) => (
                      <div key={i} className="rounded-lg border border-border/60 bg-bg p-3 hover:border-border transition-colors">
                        <div className="flex items-start justify-between mb-1.5">
                          <span className="font-mono text-[9px] tracking-widest" style={{ color: card.color }}>
                            {card.icon} {card.label}
                          </span>
                          <span className="font-mono text-[9px] text-muted/40">KG·CSV</span>
                        </div>
                        <p className="text-[13px] font-semibold text-ink mb-0.5">{card.title}</p>
                        <p className="font-mono text-[10px] text-muted mb-1.5">{card.detail}</p>
                        <p className="text-[11px] text-muted/70 leading-relaxed">{card.sub}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Chat input mock */}
                <div className="px-4 pb-4">
                  <div className="flex items-center gap-2 border border-border rounded-lg px-3 py-2 bg-bg">
                    <span className="text-muted/50 text-xs">◈</span>
                    <span className="text-[12px] text-muted/50 font-mono">
                      Ask about PRD001 inventory risk...
                    </span>
                    <span className="ml-auto text-accent/50 text-xs">⏎</span>
                  </div>
                </div>
              </div>

              {/* Floating label */}
              <div className="absolute -bottom-3 -right-3 bg-accent text-bg text-[10px] font-mono font-500 px-2.5 py-1 rounded-full tracking-wider">
                LIVE ANALYSIS
              </div>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2">
          <span className="font-mono text-[10px] text-muted/50 tracking-widest uppercase">Scroll</span>
          <div className="w-px h-8 bg-gradient-to-b from-muted/40 to-transparent" />
        </div>
      </section>

      {/* ── Ticker ── */}
      <div className="border-y border-border bg-surface-2/50 overflow-hidden py-3">
        <div className="flex animate-ticker whitespace-nowrap">
          {[...Array(2)].map((_, ri) => (
            <div key={ri} className="flex items-center gap-0 shrink-0">
              {[
                '90% Domain Accuracy', '◈', '100% FK Precision', '◈',
                '6 Industry Domains', '◈', 'GraphRAG Technology', '◈',
                'Real-time Streaming', '◈', 'Claude AI Powered', '◈',
                'Beauty · Supply Chain · Energy · Manufacturing · Logistics · Finance', '◈',
                'Upload CSV · PDF · Excel · DOCX', '◈',
              ].map((item, i) => (
                <span key={i} className={
                  item === '◈'
                    ? 'text-accent/40 mx-6 font-mono text-xs'
                    : 'font-mono text-[11px] text-muted/60 tracking-wider uppercase'
                }>{item}</span>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* ── How It Works ── */}
      <section id="how-it-works" className="py-32 relative">
        <div className="absolute inset-0 grid-bg opacity-15" />
        <div className="relative max-w-7xl mx-auto px-6">
          <div ref={stepsSection.ref} className={`reveal ${stepsSection.visible ? 'visible' : ''}`}>
            <div className="mb-16 text-center">
              <span className="font-mono text-[11px] text-accent tracking-widest uppercase mb-3 block">
                How it works
              </span>
              <h2 className="font-display text-4xl lg:text-5xl font-700 text-ink tracking-tight">
                From raw data to decision,<br />
                <span className="gradient-text">in three steps.</span>
              </h2>
            </div>

            <div className="relative grid md:grid-cols-3 gap-8">
              {/* Connector line */}
              <div className="hidden md:block absolute top-12 left-[calc(16.66%-1px)] right-[calc(16.66%-1px)] h-px bg-gradient-to-r from-transparent via-border to-transparent" />

              {steps.map((step, i) => (
                <div key={i} className="relative group">
                  <div className="flex flex-col">
                    {/* Step number */}
                    <div className="mb-6 flex items-center gap-4">
                      <div className="relative w-12 h-12 border border-border group-hover:border-accent/40 bg-surface rounded-lg flex items-center justify-center transition-colors duration-300">
                        <span className="font-mono text-[13px] font-500 text-accent">{step.num}</span>
                        <div className="absolute -inset-px rounded-lg bg-accent/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>

                    <h3 className="font-display text-xl font-700 text-ink mb-3 tracking-tight">{step.title}</h3>
                    <p className="text-muted text-[14px] leading-relaxed mb-4">{step.desc}</p>
                    <div className="flex flex-wrap gap-2">
                      {step.detail.split(' · ').map(tag => (
                        <span key={tag} className="font-mono text-[10px] text-accent/70 border border-accent/20 bg-accent/5 px-2 py-0.5 rounded">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section id="features" className="py-32 bg-surface/30">
        <div className="max-w-7xl mx-auto px-6">
          <div ref={featSection.ref} className={`reveal ${featSection.visible ? 'visible' : ''}`}>
            <div className="mb-16 text-center">
              <span className="font-mono text-[11px] text-accent tracking-widest uppercase mb-3 block">
                Features
              </span>
              <h2 className="font-display text-4xl lg:text-5xl font-700 text-ink tracking-tight">
                Everything ops teams<br />
                <span className="gradient-text">actually need.</span>
              </h2>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {features.map((feat, i) => (
                <div key={i}
                  className="group relative border border-border hover:border-accent/30 bg-surface rounded-xl p-6 transition-all duration-300 hover:-translate-y-0.5"
                  style={{ animationDelay: `${i * 80}ms` }}
                >
                  <div className="absolute inset-0 rounded-xl bg-accent/3 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                  <div className="relative">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xl text-accent/60 group-hover:text-accent transition-colors">
                          {feat.sym}
                        </span>
                        <span className="font-mono text-[10px] text-muted/60 tracking-widest uppercase">
                          {feat.label}
                        </span>
                      </div>
                      <span className="font-mono text-[9px] text-accent/50 border border-accent/20 px-2 py-0.5 rounded-full">
                        {feat.tag}
                      </span>
                    </div>

                    <h3 className="font-display text-[17px] font-700 text-ink mb-2 tracking-tight leading-snug">
                      {feat.title}
                    </h3>
                    <p className="text-[13px] text-muted leading-relaxed">{feat.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Domains ── */}
      <section id="domains" className="py-32">
        <div className="max-w-7xl mx-auto px-6">
          <div ref={domainsSection.ref} className={`reveal ${domainsSection.visible ? 'visible' : ''}`}>
            <div className="mb-16 flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <span className="font-mono text-[11px] text-accent tracking-widest uppercase mb-3 block">
                  Domain Support
                </span>
                <h2 className="font-display text-4xl lg:text-5xl font-700 text-ink tracking-tight">
                  Built for your industry.<br />
                  <span className="gradient-text">Out of the box.</span>
                </h2>
              </div>
              <p className="text-muted text-[14px] leading-relaxed max-w-sm">
                7 industry presets included. Or enter any domain name and Claude
                generates a custom configuration instantly.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {domains.map((d, i) => (
                <div key={i}
                  className="group relative border border-border rounded-xl p-6 bg-surface overflow-hidden transition-all duration-300 hover:-translate-y-0.5"
                  style={{ ['--domain-color' as string]: d.color, ['--domain-glow' as string]: d.glow }}
                >
                  {/* Hover glow */}
                  <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-xl"
                    style={{ background: `radial-gradient(circle at 30% 50%, ${d.glow} 0%, transparent 70%)` }} />
                  <div className="absolute bottom-0 left-0 right-0 h-px opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ background: `linear-gradient(90deg, transparent, ${d.color}60, transparent)` }} />

                  <div className="relative">
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-2xl transition-transform group-hover:scale-110 duration-200"
                        style={{ color: d.color }}>
                        {d.sym}
                      </span>
                      <div className="w-px h-5 bg-border" />
                      <span className="font-mono text-[10px] tracking-wider" style={{ color: d.color }}>
                        DOMAIN
                      </span>
                    </div>
                    <h3 className="font-display text-[16px] font-700 text-ink mb-1.5 tracking-tight">{d.name}</h3>
                    <p className="font-mono text-[11px] text-muted/60">{d.desc}</p>
                  </div>
                </div>
              ))}

              {/* Custom domain card */}
              <div className="group border border-dashed border-border hover:border-accent/40 rounded-xl p-6 bg-surface/50 flex flex-col items-center justify-center text-center transition-all duration-300 cursor-pointer">
                <span className="text-2xl text-muted/40 group-hover:text-accent/60 transition-colors mb-3">+</span>
                <p className="font-display text-[15px] font-600 text-muted/60 group-hover:text-ink transition-colors mb-1">
                  Custom Domain
                </p>
                <p className="font-mono text-[11px] text-muted/40 group-hover:text-muted transition-colors">
                  Claude generates config instantly
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats ── */}
      <section className="py-24 border-y border-border bg-surface/50">
        <div className="max-w-7xl mx-auto px-6">
          <div ref={statsSection.ref}
            className={`grid grid-cols-2 lg:grid-cols-4 gap-8 reveal ${statsSection.visible ? 'visible' : ''}`}>
            {statItems.map((s, i) => (
              <div key={i} className="text-center group">
                <div className="font-display text-5xl lg:text-6xl font-800 gradient-text mb-2 tabular-nums">
                  <Counter end={s.end} suffix={s.suffix} trigger={statsSection.visible} duration={1600 + i * 200} />
                </div>
                <p className="text-[14px] font-semibold text-ink mb-1">{s.label}</p>
                <p className="font-mono text-[11px] text-muted/60">{s.sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Trust Bar ── */}
      <section className="py-16 border-b border-border">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center font-mono text-[11px] text-muted/40 uppercase tracking-widest mb-10">
            Built on enterprise-grade infrastructure
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16">
            {[
              { name: 'Claude AI', sym: '◈', desc: 'LLM Backbone' },
              { name: 'Supabase', sym: '⊞', desc: 'Vector Database' },
              { name: 'NetworkX', sym: '⬡', desc: 'Graph Engine' },
              { name: 'GraphRAG', sym: '◎', desc: 'Community Search' },
              { name: 'Vercel', sym: '◑', desc: 'Deployment' },
            ].map((t, i) => (
              <div key={i} className="flex items-center gap-2.5 text-muted/50 hover:text-muted transition-colors">
                <span className="text-muted/30 font-mono">{t.sym}</span>
                <div>
                  <p className="text-[13px] font-semibold text-ink/60">{t.name}</p>
                  <p className="font-mono text-[10px] text-muted/40">{t.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-32 relative overflow-hidden">
        {/* Background */}
        <div className="absolute inset-0"
          style={{ background: 'radial-gradient(ellipse at 50% 50%, rgba(0,198,245,0.08) 0%, transparent 65%)' }} />
        <div className="absolute inset-0 grid-bg opacity-20" />

        <div className="relative max-w-4xl mx-auto px-6 text-center">
          <span className="font-mono text-[11px] text-accent tracking-widest uppercase mb-4 block">
            Get Started
          </span>
          <h2 className="font-display text-4xl lg:text-6xl font-800 text-ink tracking-tight leading-[0.95] mb-6">
            Stop guessing.<br />
            <span className="gradient-text">Start deciding.</span>
          </h2>
          <p className="text-muted text-lg max-w-2xl mx-auto mb-10 leading-relaxed">
            Upload your first dataset and get a complete operational analysis in under
            3 minutes. No setup, no SQL, no data science team required.
          </p>

          <div className="flex flex-wrap items-center justify-center gap-4">
            <button className="group px-8 py-4 bg-accent text-bg font-semibold text-sm rounded-md hover:bg-accent/90 transition-all duration-200 glow-accent-strong">
              Start Free Trial
              <span className="ml-2 group-hover:translate-x-0.5 inline-block transition-transform">→</span>
            </button>
            <button className="px-8 py-4 border border-border text-ink/70 font-medium text-sm rounded-md hover:border-accent/40 hover:text-ink transition-all duration-200">
              Book a Demo
            </button>
          </div>

          <p className="mt-6 font-mono text-[11px] text-muted/40">
            No credit card · Free tier available · Enterprise plans on request
          </p>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-border py-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-accent">⬡</span>
            <span className="font-display font-700 text-[13px] text-ink/60 tracking-tight">
              OPS<span className="text-accent/60">.</span>COPILOT
            </span>
          </div>

          <div className="flex items-center gap-6 text-[12px] text-muted/50">
            {['Privacy', 'Terms', 'Docs', 'GitHub'].map(l => (
              <a key={l} href="#" className="hover:text-muted transition-colors">{l}</a>
            ))}
          </div>

          <p className="font-mono text-[11px] text-muted/30">
            © 2026 Ops Copilot · Built with Claude AI
          </p>
        </div>
      </footer>
    </div>
  )
}
