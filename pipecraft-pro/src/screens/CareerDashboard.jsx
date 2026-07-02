import { useGame } from '../state/GameContext.jsx'
import { useNav } from '../state/NavContext.jsx'
import { RANKS, rankForXp, nextRank } from '../data/ranks.js'
import { Card, SectionTitle, ProgressBar, Stars, Badge, Stat, money, Button } from '../components/ui.jsx'

export default function CareerDashboard() {
  const { state } = useGame()
  const { navigate } = useNav()
  const rank = rankForXp(state.xp)
  const next = nextRank(state.xp)

  const jobs = state.completedJobs
  const avgScore = jobs.length ? Math.round(jobs.reduce((s, j) => s + j.score, 0) / jobs.length) : 0
  const avgStars = jobs.length ? (jobs.reduce((s, j) => s + j.stars, 0) / jobs.length).toFixed(1) : '—'
  const totalRevenue = jobs.reduce((s, j) => s + j.revenue, 0)
  const totalProfit = jobs.reduce((s, j) => s + j.profit, 0)

  return (
    <div className="animate-pop">
      <SectionTitle sub="Your journey from Helper to Plumbing Company Owner.">📈 Career Dashboard</SectionTitle>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Current Rank" value={`${rank.icon} ${rank.title}`} />
        <Stat label="Average Job Score" value={jobs.length ? `${avgScore}/100` : '—'} tone={avgScore >= 80 ? 'text-emerald-400' : 'text-slate-100'} />
        <Stat label="Avg Satisfaction" value={`${avgStars} ★`} tone="text-yellow-400" />
        <Stat label="Lifetime Profit" value={money(Math.round(totalProfit))} tone={totalProfit >= 0 ? 'text-emerald-400' : 'text-red-400'} />
      </div>

      {/* Career ladder */}
      <Card className="mb-6 p-5">
        <h3 className="mb-4 font-bold text-slate-100">Career Ladder</h3>
        <div className="space-y-3">
          {RANKS.map(r => {
            const reached = state.xp >= r.xp
            const isCurrent = r.level === rank.level
            const spanStart = r.xp
            const spanEnd = RANKS.find(x => x.xp > r.xp)?.xp ?? r.xp
            const progress = isCurrent && next ? ((state.xp - spanStart) / (spanEnd - spanStart)) * 100 : reached ? 100 : 0
            return (
              <div key={r.level} className={`rounded-xl border p-3 ${isCurrent ? 'border-pipe-500/60 bg-pipe-500/10' : 'border-ink-600/50'}`}>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xl">{r.icon}</span>
                  <span className={`font-semibold ${reached ? 'text-slate-100' : 'text-slate-500'}`}>{r.title}</span>
                  {isCurrent && <Badge tone="blue">current</Badge>}
                  {!reached && <Badge tone="gray">{r.xp} XP</Badge>}
                  <span className="ml-auto text-xs text-slate-500">{r.unlocks.join(' · ')}</span>
                </div>
                {isCurrent && next && (
                  <div className="mt-2">
                    <ProgressBar value={progress} color="bg-gradient-to-r from-pipe-500 to-flame-500" />
                    <div className="mt-1 text-right text-[11px] text-slate-400">{next.xp - state.xp} XP to {next.title}</div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      {/* Job history */}
      <Card className="p-5">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-bold text-slate-100">Job History</h3>
          <span className="text-xs text-slate-400">Revenue to date: <span className="font-semibold text-emerald-400">{money(Math.round(totalRevenue))}</span></span>
        </div>
        {jobs.length === 0 ? (
          <div className="py-8 text-center text-slate-400">
            No jobs completed yet.
            <div className="mt-3"><Button onClick={() => navigate('job-board')}>Take your first call</Button></div>
          </div>
        ) : (
          <div className="space-y-2">
            {jobs.map((j, i) => (
              <div key={i} className="flex flex-wrap items-center gap-3 rounded-xl bg-ink-900/60 p-3">
                <span className="text-xl">{j.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold text-slate-100">{j.title}</div>
                  <Stars value={j.stars} size="text-xs" />
                </div>
                <Badge tone={j.score >= 80 ? 'green' : j.score >= 55 ? 'yellow' : 'red'}>{j.score}/100</Badge>
                <span className={`text-sm font-bold ${j.profit >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>{money(Math.round(j.profit))}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  )
}
