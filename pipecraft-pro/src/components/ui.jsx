// Small shared UI kit: cards, buttons, bars, badges, stars.

export function Card({ children, className = '', onClick }) {
  return (
    <div
      onClick={onClick}
      className={`rounded-2xl border border-ink-600/60 bg-ink-800/80 backdrop-blur shadow-lg shadow-black/30 ${onClick ? 'cursor-pointer transition hover:border-pipe-500/70 hover:bg-ink-700/70' : ''} ${className}`}
    >
      {children}
    </div>
  )
}

export function Button({ children, onClick, variant = 'primary', disabled, className = '', size = 'md' }) {
  const base = 'inline-flex items-center justify-center gap-2 rounded-xl font-semibold transition active:scale-95 disabled:opacity-40 disabled:pointer-events-none'
  const sizes = { sm: 'px-3 py-1.5 text-sm', md: 'px-4 py-2.5 text-sm', lg: 'px-6 py-3 text-base' }
  const variants = {
    primary: 'bg-pipe-500 text-white hover:bg-pipe-400 shadow shadow-pipe-500/30',
    accent: 'bg-flame-500 text-white hover:bg-flame-400 shadow shadow-flame-500/30',
    ghost: 'bg-ink-700/60 text-slate-200 hover:bg-ink-600/80 border border-ink-600',
    danger: 'bg-red-600/90 text-white hover:bg-red-500',
    success: 'bg-emerald-600 text-white hover:bg-emerald-500',
  }
  return (
    <button onClick={onClick} disabled={disabled} className={`${base} ${sizes[size]} ${variants[variant]} ${className}`}>
      {children}
    </button>
  )
}

export function ProgressBar({ value, max = 100, color = 'bg-pipe-500', className = '' }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  return (
    <div className={`h-2.5 w-full overflow-hidden rounded-full bg-ink-950/80 ${className}`}>
      <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export function Badge({ children, tone = 'blue', className = '' }) {
  const tones = {
    blue: 'bg-pipe-500/15 text-pipe-300 border-pipe-500/30',
    orange: 'bg-flame-500/15 text-flame-300 border-flame-500/30',
    green: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30',
    red: 'bg-red-500/15 text-red-300 border-red-500/30',
    gray: 'bg-slate-500/15 text-slate-300 border-slate-500/30',
    yellow: 'bg-yellow-500/15 text-yellow-300 border-yellow-500/30',
  }
  return <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-medium ${tones[tone]} ${className}`}>{children}</span>
}

export function Stars({ value, size = 'text-lg' }) {
  return (
    <span className={`${size} tracking-tight`} aria-label={`${value} out of 5 stars`}>
      {[1, 2, 3, 4, 5].map(i => (
        <span key={i} className={i <= value ? 'text-yellow-400' : 'text-slate-700'}>★</span>
      ))}
    </span>
  )
}

export function Stat({ label, value, icon, tone = 'text-slate-100' }) {
  return (
    <Card className="p-4">
      <div className="flex items-center gap-3">
        {icon && <div className="text-2xl">{icon}</div>}
        <div className="min-w-0">
          <div className="text-xs uppercase tracking-wider text-slate-400">{label}</div>
          <div className={`truncate text-xl font-bold ${tone}`}>{value}</div>
        </div>
      </div>
    </Card>
  )
}

export function SectionTitle({ children, sub }) {
  return (
    <div className="mb-4">
      <h2 className="text-xl font-bold text-slate-100 sm:text-2xl">{children}</h2>
      {sub && <p className="mt-1 text-sm text-slate-400">{sub}</p>}
    </div>
  )
}

export const money = n => (n < 0 ? `-$${Math.abs(n).toLocaleString()}` : `$${n.toLocaleString()}`)
