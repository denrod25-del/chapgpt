import { useMemo, useState } from 'react'
import { useGame } from '../state/GameContext.jsx'
import { useNav } from '../state/NavContext.jsx'
import { JOBS } from '../data/jobs.js'
import { rankForXp, RANKS } from '../data/ranks.js'
import { Card, SectionTitle, Badge, Button, money } from '../components/ui.jsx'

const DIFF_LABEL = ['', 'Easy', 'Routine', 'Tricky', 'Hard', 'Expert']

export default function JobBoard() {
  const { state } = useGame()
  const { navigate } = useNav()
  const rank = rankForXp(state.xp)
  const [shuffleSeed, setShuffleSeed] = useState(0)

  // "Random jobs": shuffle the board order on demand.
  const jobs = useMemo(() => {
    const arr = [...JOBS]
    if (shuffleSeed > 0) {
      for (let i = arr.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1))
        ;[arr[i], arr[j]] = [arr[j], arr[i]]
      }
    }
    return arr.sort((a, b) => (a.minRank <= rank.level ? 0 : 1) - (b.minRank <= rank.level ? 0 : 1))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [shuffleSeed, rank.level])

  const randomJob = () => {
    const unlocked = JOBS.filter(j => j.minRank <= rank.level)
    const pick = unlocked[Math.floor(Math.random() * unlocked.length)]
    navigate('service-call', { jobId: pick.id })
  }

  return (
    <div className="animate-pop">
      <SectionTitle sub="Dispatch is holding calls for you. Locked jobs open up as you rank up.">📋 Job Board</SectionTitle>

      <div className="mb-4 flex flex-wrap gap-2">
        <Button variant="accent" onClick={randomJob}>🎲 Dispatch me a random call</Button>
        <Button variant="ghost" onClick={() => setShuffleSeed(s => s + 1)}>🔀 Shuffle board</Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {jobs.map(job => {
          const locked = job.minRank > rank.level
          const best = state.bestScores[job.id]
          const missingParts = job.requiredParts.filter(p => (state.partsStock[p] || 0) === 0)
          const missingTools = job.requiredTools.filter(t => !state.ownedTools.includes(t))
          return (
            <Card key={job.id} className={`flex flex-col p-5 ${locked ? 'opacity-60' : ''}`}>
              <div className="mb-2 flex items-start justify-between gap-2">
                <div className="text-3xl">{job.icon}</div>
                <div className="flex flex-wrap justify-end gap-1.5">
                  <Badge tone={job.difficulty <= 2 ? 'green' : job.difficulty <= 3 ? 'yellow' : 'red'}>
                    {DIFF_LABEL[job.difficulty]}
                  </Badge>
                  {job.inspectionRequired && <Badge tone="orange">Inspection</Badge>}
                  {best != null && <Badge tone="blue">Best: {best}</Badge>}
                </div>
              </div>
              <h3 className="font-bold text-slate-100">{job.title}</h3>
              <p className="mt-1 text-xs text-slate-500">{job.propertyType} · {job.customer}</p>
              <p className="mt-2 flex-1 text-sm italic text-slate-400">{job.complaint}</p>
              <div className="mt-3 flex items-center justify-between text-xs text-slate-400">
                <span>⏱️ {Math.round(job.timeLimitSec / 60)} min limit</span>
                <span className="font-semibold text-emerald-400">{money(job.laborCharge)}+ labor</span>
              </div>
              {!locked && (missingTools.length > 0 || missingParts.length > 0) && (
                <div className="mt-2 rounded-lg bg-yellow-500/10 px-3 py-1.5 text-[11px] text-yellow-300">
                  ⚠️ {missingTools.length > 0 && `Missing tools: ${missingTools.join(', ')}. `}
                  {missingParts.length > 0 && `Out of stock: ${missingParts.join(', ')}.`}
                </div>
              )}
              <div className="mt-3">
                {locked ? (
                  <Button variant="ghost" disabled className="w-full">
                    🔒 Requires {RANKS[job.minRank].title}
                  </Button>
                ) : (
                  <Button className="w-full" onClick={() => navigate('service-call', { jobId: job.id })}>
                    Accept Call
                  </Button>
                )}
              </div>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
