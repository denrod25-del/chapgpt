import { useEffect, useMemo, useRef, useState } from 'react'
import { useGame, vanTimeBonus } from '../state/GameContext.jsx'
import { useNav } from '../state/NavContext.jsx'
import { jobById } from '../data/jobs.js'
import { toolById } from '../data/tools.js'
import { partById } from '../data/parts.js'
import { PRICING_TIERS, REVIEW_SNIPPETS } from '../data/business.js'
import { scoreJob, satisfactionStars, runInspection } from '../game/scoring.js'
import { Card, Button, Badge, SectionTitle, money } from '../components/ui.jsx'
import DiagnosisChecklist from './servicecall/DiagnosisChecklist.jsx'
import RepairWorkspace from './servicecall/RepairWorkspace.jsx'
import CustomerResult from './servicecall/CustomerResult.jsx'
import InspectionReport from './servicecall/InspectionReport.jsx'

const DIFF_TIME = { easy: 1.5, normal: 1, hard: 0.75 }

export default function ServiceCall({ jobId }) {
  const { state, dispatch } = useGame()
  const { navigate } = useNav()
  const job = jobById[jobId]

  const timeLimit = useMemo(() => {
    if (!job) return 0
    const mult = DIFF_TIME[state.settings.difficulty] || 1
    return Math.round(job.timeLimitSec * mult * (1 + vanTimeBonus(state)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job])

  // Phases: brief → loadout → diagnose → repair → result → inspection
  const [phase, setPhase] = useState('brief')
  const [selectedTools, setSelectedTools] = useState([])
  const [selectedParts, setSelectedParts] = useState([])
  const [checkedItems, setCheckedItems] = useState([])
  const [diagnosisId, setDiagnosisId] = useState(null)
  const [performedSteps, setPerformedSteps] = useState([])
  const [secondsLeft, setSecondsLeft] = useState(timeLimit)
  const [report, setReport] = useState(null)
  const finishedRef = useRef(false)

  const timerActive = phase === 'diagnose' || phase === 'repair'

  useEffect(() => {
    if (!timerActive) return
    const t = setInterval(() => setSecondsLeft(s => s - 1), 1000)
    return () => clearInterval(t)
  }, [timerActive])

  useEffect(() => {
    if (timerActive && secondsLeft <= 0) finishJob(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [secondsLeft, timerActive])

  if (!job) {
    return (
      <Card className="p-8 text-center">
        <p className="text-slate-300">Job not found.</p>
        <Button className="mt-4" onClick={() => navigate('job-board')}>Back to Job Board</Button>
      </Card>
    )
  }

  function finishJob(timedOut = false) {
    if (finishedRef.current) return
    finishedRef.current = true

    const timeUsedSec = timedOut ? timeLimit : timeLimit - secondsLeft
    const play = { selectedTools, selectedParts, diagnosisId, checkedItems, performedSteps, timeUsedSec, timeLimitSec: timeLimit }
    const result = scoreJob(job, play)

    // Apprentice bonus
    const apprenticeBonus = state.apprenticeHired ? 8 : 0
    const score = Math.max(0, Math.min(100, result.score + apprenticeBonus))

    const tier = PRICING_TIERS.find(t => t.id === state.pricingTier) || PRICING_TIERS[1]
    const stars = satisfactionStars(score, tier.satisfactionBonus)

    // Parts actually consumed = steps performed that install a part the player
    // brought. Parts burned on wrong (distractor) repairs still leave the van —
    // you installed them — but only correct-repair parts get billed to the
    // customer; the company eats the cost of wasted ones.
    const canConsume = s => s.usesPart && performedSteps.includes(s.id)
      && selectedParts.includes(s.usesPart) && (state.partsStock[s.usesPart] || 0) > 0
    const partsUsed = []
    const partsWasted = []
    for (const s of job.repairSteps) {
      if (canConsume(s)) partsUsed.push(s.usesPart)
    }
    for (const d of job.distractors || []) {
      if (canConsume(d)) { partsUsed.push(d.usesPart); partsWasted.push(d.usesPart) }
    }
    const partsCost = partsUsed.reduce((sum, p) => sum + (partById[p]?.cost || 0), 0)
    const partsBilled = partsUsed
      .filter(p => !partsWasted.includes(p))
      .reduce((sum, p) => sum + (partById[p]?.charge || 0), 0)

    let revenue = Math.round(job.laborCharge * tier.multiplier + partsBilled)
    let disputed = false
    if (score < 50) { revenue = Math.round(revenue * 0.6); disputed = true } // unhappy customer disputes the bill

    const wages = state.apprenticeHired ? 40 : 0
    const profit = revenue - partsCost - wages
    const xpEarned = Math.max(10, Math.round(job.xp * (score / 100)))
    const inspection = runInspection(job, play)
    const pool = REVIEW_SNIPPETS[stars]
    const review = pool[Math.floor(Math.random() * pool.length)]

    const fullReport = {
      jobId: job.id, title: job.title, icon: job.icon,
      score, base: result.base, breakdown: result.breakdown, mistakes: result.mistakes,
      apprenticeBonus, stars, review, disputed, timedOut,
      revenue, partsCost, wages, profit, xpEarned,
      partsUsed, partsWasted, inspection, inspectionPassed: inspection ? inspection.passed : null,
      timeUsedSec, timeLimitSec: timeLimit,
    }
    setReport(fullReport)
    dispatch({ type: 'COMPLETE_JOB', report: fullReport })
    setPhase('result')
  }

  const mmss = s => `${Math.floor(Math.max(0, s) / 60)}:${String(Math.max(0, s) % 60).padStart(2, '0')}`

  // ---------- Phase: job brief ----------
  if (phase === 'brief') {
    return (
      <div className="animate-pop">
        <SectionTitle sub={`${job.propertyType} · Customer: ${job.customer}`}>{job.icon} {job.title}</SectionTitle>
        <Card className="mb-4 p-5">
          <h3 className="mb-1 text-sm font-bold uppercase tracking-wider text-flame-300">Customer Complaint</h3>
          <p className="text-lg italic text-slate-200">{job.complaint}</p>
        </Card>
        <Card className="mb-4 p-5">
          <h3 className="mb-2 text-sm font-bold uppercase tracking-wider text-pipe-300">Visible Symptoms</h3>
          <ul className="space-y-1.5">
            {job.symptoms.map((s, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-300"><span>👁️</span> {s}</li>
            ))}
          </ul>
        </Card>
        <Card className="mb-6 p-5">
          <div className="flex flex-wrap gap-4 text-sm text-slate-300">
            <span>⏱️ Time limit: <b>{mmss(timeLimit)}</b></span>
            <span>💵 Base labor: <b className="text-emerald-400">{money(job.laborCharge)}</b></span>
            {job.inspectionRequired && <Badge tone="orange">City inspection required</Badge>}
          </div>
        </Card>
        <div className="flex flex-wrap gap-3">
          <Button size="lg" variant="accent" onClick={() => setPhase('loadout')}>🚐 Load the van & head out</Button>
          <Button size="lg" variant="ghost" onClick={() => navigate('job-board')}>Decline call</Button>
        </div>
      </div>
    )
  }

  // ---------- Phase: loadout (tool + parts selection) ----------
  if (phase === 'loadout') {
    const toggle = (list, setList, id) => setList(list.includes(id) ? list.filter(x => x !== id) : [...list, id])
    return (
      <div className="animate-pop">
        <SectionTitle sub="Pick the tools and parts you think this job needs. Wrong picks cost points; missing picks cost more.">🧰 Load Out — {job.title}</SectionTitle>

        <Card className="mb-4 p-5">
          <h3 className="mb-3 font-bold text-slate-100">Tool Bag <span className="text-xs font-normal text-slate-400">({selectedTools.length} selected)</span></h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {state.ownedTools.map(id => {
              const t = toolById[id]
              const on = selectedTools.includes(id)
              return (
                <button key={id} onClick={() => toggle(selectedTools, setSelectedTools, id)}
                  className={`flex items-center gap-2 rounded-xl border p-2.5 text-left text-xs font-medium transition ${on ? 'border-pipe-500 bg-pipe-500/20 text-pipe-200' : 'border-ink-600/60 bg-ink-900/50 text-slate-300 hover:border-slate-500'}`}>
                  <span className="text-xl">{t.icon}</span>
                  <span className="min-w-0 truncate">{t.name}</span>
                </button>
              )
            })}
          </div>
        </Card>

        <Card className="mb-6 p-5">
          <h3 className="mb-3 font-bold text-slate-100">Parts From the Van <span className="text-xs font-normal text-slate-400">({selectedParts.length} selected)</span></h3>
          <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
            {Object.entries(state.partsStock).filter(([, qty]) => qty > 0).map(([id]) => {
              const p = partById[id]
              const on = selectedParts.includes(id)
              return (
                <button key={id} onClick={() => toggle(selectedParts, setSelectedParts, id)}
                  className={`flex items-center gap-2 rounded-xl border p-2.5 text-left text-xs font-medium transition ${on ? 'border-flame-500 bg-flame-500/20 text-flame-200' : 'border-ink-600/60 bg-ink-900/50 text-slate-300 hover:border-slate-500'}`}>
                  <span className="text-xl">{p.icon}</span>
                  <span className="min-w-0">
                    <span className="block truncate">{p.name}</span>
                    <span className="text-[10px] text-slate-500">×{state.partsStock[id]} in van</span>
                  </span>
                </button>
              )
            })}
          </div>
          {state.settings.showHints && (
            <p className="mt-3 text-xs text-slate-500">💡 Hint: read the symptoms again. This job likely needs {job.requiredTools.length} tool{job.requiredTools.length !== 1 ? 's' : ''} and {job.requiredParts.length || 'no'} part{job.requiredParts.length !== 1 ? 's' : ''}.</p>
          )}
        </Card>

        <div className="flex flex-wrap gap-3">
          <Button size="lg" variant="accent" onClick={() => { setSecondsLeft(timeLimit); setPhase('diagnose') }}>
            🚪 Knock on the door — start the clock
          </Button>
          <Button size="lg" variant="ghost" onClick={() => setPhase('brief')}>Back to brief</Button>
        </div>
      </div>
    )
  }

  // ---------- Timer header shared by active phases ----------
  const TimerBar = (
    <div className={`mb-4 flex items-center justify-between rounded-2xl border px-4 py-2.5 ${secondsLeft < timeLimit * 0.2 ? 'border-red-500/60 bg-red-500/10' : 'border-ink-600/60 bg-ink-800/80'}`}>
      <span className="text-sm font-semibold text-slate-200">{job.icon} {job.title}</span>
      <span className={`font-mono text-lg font-bold ${secondsLeft < timeLimit * 0.2 ? 'animate-pulse text-red-400' : 'text-pipe-300'}`}>⏱️ {mmss(secondsLeft)}</span>
    </div>
  )

  if (phase === 'diagnose') {
    return (
      <div className="animate-pop">
        {TimerBar}
        <DiagnosisChecklist
          job={job}
          checkedItems={checkedItems}
          setCheckedItems={setCheckedItems}
          diagnosisId={diagnosisId}
          setDiagnosisId={setDiagnosisId}
          onCommit={() => setPhase('repair')}
        />
      </div>
    )
  }

  if (phase === 'repair') {
    return (
      <div className="animate-pop">
        {TimerBar}
        <RepairWorkspace
          job={job}
          selectedParts={selectedParts}
          partsStock={state.partsStock}
          performedSteps={performedSteps}
          setPerformedSteps={setPerformedSteps}
          onFinish={() => finishJob(false)}
        />
      </div>
    )
  }

  if (phase === 'result' && report) {
    return (
      <CustomerResult
        job={job}
        report={report}
        onInspection={report.inspection ? () => setPhase('inspection') : null}
        onDone={() => navigate('job-board')}
        onCareer={() => navigate('career')}
      />
    )
  }

  if (phase === 'inspection' && report?.inspection) {
    return <InspectionReport job={job} report={report} onBack={() => setPhase('result')} />
  }

  return null
}
