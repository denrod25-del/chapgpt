import { useGame } from '../state/GameContext.jsx'
import { useNav } from '../state/NavContext.jsx'
import { rankForXp, RANKS } from '../data/ranks.js'
import { STAFF, PRICING_TIERS } from '../data/business.js'
import { Card, SectionTitle, Badge, Button, Stars, Stat, money } from '../components/ui.jsx'

export default function BusinessDashboard() {
  const { state, dispatch } = useGame()
  const { navigate } = useNav()
  const rank = rankForXp(state.xp)

  const jobs = state.completedJobs
  const revenue = jobs.reduce((s, j) => s + j.revenue, 0)
  const expenses = state.ledger.filter(l => l.amount < 0).reduce((s, l) => s + l.amount, 0)
  const avgStars = jobs.length ? (jobs.reduce((s, j) => s + j.stars, 0) / jobs.length).toFixed(1) : '—'
  const apprentice = STAFF[0]

  return (
    <div className="animate-pop">
      <SectionTitle sub={`${state.companyName} — owned & operated by a ${rank.title}.`}>💼 Business Dashboard</SectionTitle>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Cash on Hand" value={money(Math.round(state.money))} icon="💵" tone={state.money >= 0 ? 'text-emerald-400' : 'text-red-400'} />
        <Stat label="Total Revenue" value={money(Math.round(revenue))} icon="📈" tone="text-pipe-300" />
        <Stat label="Total Expenses" value={money(Math.round(expenses))} icon="📉" tone="text-red-300" />
        <Stat label="Reputation" value={`${state.reputation}/100`} icon="⭐" tone="text-yellow-400" />
      </div>

      {/* Quick links (also serves as mobile access to sub-screens) */}
      <div className="mb-6 grid grid-cols-3 gap-2">
        <Button variant="ghost" onClick={() => navigate('toolbag')}>🧰 Tools</Button>
        <Button variant="ghost" onClick={() => navigate('parts')}>🔩 Restock</Button>
        <Button variant="ghost" onClick={() => navigate('van')}>🚐 Van</Button>
      </div>

      <div className="mb-6 grid gap-4 lg:grid-cols-2">
        {/* Pricing */}
        <Card className="p-5">
          <h3 className="mb-1 font-bold text-slate-100">Set Your Pricing</h3>
          <p className="mb-3 text-xs text-slate-500">Higher rates mean fatter invoices — and pickier reviews.</p>
          <div className="space-y-2">
            {PRICING_TIERS.map(t => (
              <label key={t.id} className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 text-sm transition ${state.pricingTier === t.id ? 'border-flame-500 bg-flame-500/10' : 'border-ink-600/60 hover:border-slate-500'}`}>
                <input type="radio" name="pricing" className="accent-flame-500" checked={state.pricingTier === t.id} onChange={() => dispatch({ type: 'SET_PRICING', tier: t.id })} />
                <span className="flex-1">
                  <span className="font-semibold text-slate-100">{t.label}</span>
                  <span className="block text-xs text-slate-500">{t.desc}</span>
                </span>
                <Badge tone={t.multiplier >= 1.25 ? 'orange' : 'blue'}>×{t.multiplier}</Badge>
              </label>
            ))}
          </div>
        </Card>

        {/* Staff */}
        <Card className="p-5">
          <h3 className="mb-1 font-bold text-slate-100">Staff</h3>
          <p className="mb-3 text-xs text-slate-500">A crew multiplies what one set of hands can do.</p>
          {state.apprenticeHired ? (
            <div className="rounded-xl bg-emerald-500/10 p-4">
              <div className="text-2xl">🧑‍🔧</div>
              <div className="font-semibold text-emerald-300">Apprentice on the crew</div>
              <p className="text-xs text-slate-400">+8 points on every job score · $40/job wages</p>
            </div>
          ) : (
            <div className="rounded-xl border border-ink-600/60 p-4">
              <div className="text-2xl">{apprentice.icon}</div>
              <div className="font-semibold text-slate-100">{apprentice.name}</div>
              <p className="mb-3 text-xs text-slate-500">{apprentice.desc}</p>
              {rank.level < apprentice.minRank ? (
                <Button size="sm" variant="ghost" disabled>🔒 Requires {RANKS[apprentice.minRank].title}</Button>
              ) : (
                <Button size="sm" disabled={state.money < apprentice.price} onClick={() => dispatch({ type: 'HIRE_APPRENTICE', price: apprentice.price })}>
                  Hire for {money(apprentice.price)}
                </Button>
              )}
            </div>
          )}
          <div className="mt-4 rounded-xl bg-ink-900/60 p-3 text-xs text-slate-500">
            🔮 Coming soon: journeymen, dispatchers, and a second van.
          </div>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* Reviews */}
        <Card className="p-5">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="font-bold text-slate-100">Customer Reviews</h3>
            <span className="text-sm text-yellow-400">{avgStars} ★ average</span>
          </div>
          {jobs.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">No reviews yet — go do great work.</p>
          ) : (
            <div className="max-h-72 space-y-2 overflow-y-auto pr-1">
              {jobs.slice(0, 10).map((j, i) => (
                <div key={i} className="rounded-xl bg-ink-900/60 p-3">
                  <div className="flex items-center justify-between">
                    <Stars value={j.stars} size="text-sm" />
                    <span className="text-xs text-slate-500">{j.title}</span>
                  </div>
                  <p className="mt-1 text-sm italic text-slate-300">“{j.review}”</p>
                </div>
              ))}
            </div>
          )}
        </Card>

        {/* Ledger */}
        <Card className="p-5">
          <h3 className="mb-3 font-bold text-slate-100">Ledger</h3>
          {state.ledger.length === 0 ? (
            <p className="py-6 text-center text-sm text-slate-500">No transactions yet.</p>
          ) : (
            <div className="max-h-72 space-y-1.5 overflow-y-auto pr-1">
              {state.ledger.map((l, i) => (
                <div key={i} className="flex items-center justify-between rounded-lg bg-ink-900/60 px-3 py-2 text-sm">
                  <span className="min-w-0 truncate text-slate-300">{l.label}</span>
                  <span className={`ml-3 shrink-0 font-mono font-semibold ${l.amount >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                    {money(Math.round(l.amount))}
                  </span>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  )
}
