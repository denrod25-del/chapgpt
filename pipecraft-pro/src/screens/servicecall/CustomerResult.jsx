import { partById } from '../../data/parts.js'
import { Card, Button, Badge, Stars, ProgressBar, money } from '../../components/ui.jsx'

// Post-job report card: score breakdown, mistakes, money, XP, review.
export default function CustomerResult({ job, report, onInspection, onDone, onCareer }) {
  const r = report
  const grade = r.score >= 90 ? 'A' : r.score >= 80 ? 'B' : r.score >= 65 ? 'C' : r.score >= 50 ? 'D' : 'F'
  const gradeTone = r.score >= 80 ? 'text-emerald-400' : r.score >= 50 ? 'text-yellow-400' : 'text-red-400'

  return (
    <div className="animate-pop">
      <Card className="mb-4 p-6 text-center">
        <div className="text-5xl">{r.score >= 65 ? '🎉' : r.score >= 50 ? '😅' : '😬'}</div>
        <h2 className="mt-2 text-2xl font-extrabold text-white">Job Complete: {job.title}</h2>
        {r.timedOut && <Badge tone="red" className="mt-2">⏱️ Ran out of time</Badge>}
        <div className={`mt-3 text-6xl font-black ${gradeTone}`}>{r.score}<span className="text-2xl text-slate-500">/100</span></div>
        <div className={`text-xl font-bold ${gradeTone}`}>Grade: {grade}</div>
        <div className="mt-3 flex justify-center"><Stars value={r.stars} size="text-2xl" /></div>
        <p className="mx-auto mt-3 max-w-md italic text-slate-300">“{r.review}”</p>
        <p className="mt-1 text-xs text-slate-500">— {job.customer}</p>
      </Card>

      <div className="mb-4 grid gap-4 md:grid-cols-2">
        {/* Score breakdown */}
        <Card className="p-5">
          <h3 className="mb-3 font-bold text-slate-100">Score Breakdown</h3>
          <div className="space-y-3">
            {r.breakdown.map((b, i) => (
              <div key={i}>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="text-slate-300">{b.label}</span>
                  <span className={b.earned === b.max ? 'font-semibold text-emerald-400' : b.earned === 0 ? 'font-semibold text-red-400' : 'font-semibold text-yellow-400'}>
                    {b.earned}/{b.max}
                  </span>
                </div>
                <ProgressBar value={b.earned} max={b.max} color={b.earned === b.max ? 'bg-emerald-500' : b.earned === 0 ? 'bg-red-500' : 'bg-yellow-500'} />
              </div>
            ))}
            {r.apprenticeBonus > 0 && (
              <div className="flex justify-between border-t border-ink-600/60 pt-2 text-sm">
                <span className="text-slate-300">🧑‍🔧 Apprentice assist</span>
                <span className="font-semibold text-pipe-300">+{r.apprenticeBonus}</span>
              </div>
            )}
          </div>
          {r.mistakes.length > 0 && (
            <div className="mt-4 rounded-xl bg-red-500/10 p-3">
              <h4 className="mb-2 text-sm font-bold text-red-300">Mistakes</h4>
              <ul className="space-y-1 text-sm">
                {r.mistakes.map((m, i) => (
                  <li key={i} className="flex justify-between gap-2 text-red-200/90">
                    <span>{m.label}</span>
                    <span className="font-mono font-semibold">{m.points}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </Card>

        {/* Money & inventory */}
        <Card className="p-5">
          <h3 className="mb-3 font-bold text-slate-100">Invoice & Payout</h3>
          <div className="space-y-2 text-sm">
            <Row label="Customer billed" value={money(r.revenue)} tone="text-emerald-400" />
            {r.disputed && <p className="rounded-lg bg-red-500/10 px-3 py-1.5 text-xs text-red-300">⚠️ Customer disputed the bill over poor work — only paid 60%.</p>}
            <Row label="Parts cost" value={money(-r.partsCost)} tone="text-red-300" />
            {r.wages > 0 && <Row label="Apprentice wages" value={money(-r.wages)} tone="text-red-300" />}
            <div className="border-t border-ink-600/60 pt-2">
              <Row label="Net profit" value={money(r.profit)} tone={r.profit >= 0 ? 'text-emerald-400 text-lg' : 'text-red-400 text-lg'} bold />
            </div>
            <Row label="XP earned" value={`+${r.xpEarned} XP`} tone="text-flame-300" bold />
            <Row label="Time used" value={`${Math.floor(r.timeUsedSec / 60)}:${String(r.timeUsedSec % 60).padStart(2, '0')} / ${Math.floor(r.timeLimitSec / 60)}:${String(r.timeLimitSec % 60).padStart(2, '0')}`} tone="text-slate-300" />
          </div>
          <div className="mt-4">
            <h4 className="mb-2 text-sm font-bold text-slate-200">Inventory Used</h4>
            {r.partsUsed.length === 0 ? (
              <p className="text-xs text-slate-500">No parts consumed on this job.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {r.partsUsed.map((p, i) => {
                  const wasted = (r.partsWasted || []).includes(p)
                  return (
                    <Badge key={i} tone={wasted ? 'red' : 'orange'}>
                      {partById[p]?.icon} {partById[p]?.name} −1{wasted ? ' (wasted, not billable)' : ''}
                    </Badge>
                  )
                })}
              </div>
            )}
          </div>
          {r.inspection && (
            <div className={`mt-4 rounded-xl p-3 text-sm ${r.inspectionPassed ? 'bg-emerald-500/10 text-emerald-300' : 'bg-red-500/10 text-red-300'}`}>
              {r.inspectionPassed ? '✅ City inspection: PASSED' : '❌ City inspection: FAILED'}
            </div>
          )}
        </Card>
      </div>

      <div className="flex flex-wrap gap-3">
        {onInspection && <Button variant="ghost" onClick={onInspection}>📄 View inspection report</Button>}
        <Button variant="accent" onClick={onDone}>📋 Back to Job Board</Button>
        <Button variant="ghost" onClick={onCareer}>📈 Career Dashboard</Button>
      </div>
    </div>
  )
}

function Row({ label, value, tone = 'text-slate-200', bold }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-slate-400">{label}</span>
      <span className={`${tone} ${bold ? 'font-bold' : 'font-medium'}`}>{value}</span>
    </div>
  )
}
