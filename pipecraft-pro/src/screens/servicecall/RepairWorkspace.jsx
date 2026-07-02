import { useMemo } from 'react'
import { partById } from '../../data/parts.js'
import { Card, Button, SectionTitle, Badge } from '../../components/ui.jsx'

// Phase 2 on site: perform repair actions in order. Correct steps are mixed
// with distractors; order, safety, and testing all feed the score.
export default function RepairWorkspace({ job, selectedParts, partsStock, performedSteps, setPerformedSteps, onFinish }) {
  // Shuffle once per job mount so the answer isn't just "click top to bottom".
  const actions = useMemo(() => {
    const all = [
      ...job.repairSteps.map(s => ({ ...s, correct: true })),
      ...(job.distractors || []).map(s => ({ ...s, correct: false })),
    ]
    for (let i = all.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[all[i], all[j]] = [all[j], all[i]]
    }
    return all
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [job.id])

  const perform = id => {
    if (!performedSteps.includes(id)) setPerformedSteps([...performedSteps, id])
  }

  const stepLabel = id => actions.find(a => a.id === id)?.label || id

  return (
    <div>
      <SectionTitle sub="Do the repair — in the right order. Not every action on the bench belongs in this job.">🔧 Repair Workspace</SectionTitle>

      <div className="grid gap-4 lg:grid-cols-5">
        <Card className="p-5 lg:col-span-3">
          <h3 className="mb-3 font-bold text-slate-100">Available Actions</h3>
          <div className="space-y-2">
            {actions.map(a => {
              const done = performedSteps.includes(a.id)
              const needsPart = a.usesPart
              const missingPart = needsPart && (!selectedParts.includes(needsPart) || (partsStock[needsPart] || 0) === 0)
              return (
                <button
                  key={a.id}
                  onClick={() => perform(a.id)}
                  disabled={done || missingPart}
                  className={`flex w-full items-center gap-3 rounded-xl border p-3 text-left text-sm transition ${
                    done
                      ? 'border-emerald-500/40 bg-emerald-500/10 text-slate-400'
                      : missingPart
                        ? 'cursor-not-allowed border-ink-600/40 bg-ink-900/40 text-slate-600'
                        : 'border-ink-600/60 bg-ink-900/50 text-slate-200 hover:border-flame-500/60 hover:bg-flame-500/5'
                  }`}
                >
                  <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${done ? 'bg-emerald-500 text-white' : 'bg-ink-700 text-slate-400'}`}>
                    {done ? performedSteps.indexOf(a.id) + 1 : '·'}
                  </span>
                  <span className="flex-1">{a.label}</span>
                  {needsPart && (
                    <Badge tone={missingPart ? 'gray' : 'orange'}>
                      {partById[needsPart]?.icon} {missingPart ? 'not in bag' : 'uses part'}
                    </Badge>
                  )}
                </button>
              )
            })}
          </div>
        </Card>

        <div className="lg:col-span-2">
          <Card className="mb-4 p-5">
            <h3 className="mb-3 font-bold text-slate-100">Work Log</h3>
            {performedSteps.length === 0 ? (
              <p className="text-sm text-slate-500">Nothing done yet. Where do you start? <span className="text-slate-400">(Think safety first…)</span></p>
            ) : (
              <ol className="space-y-1.5 text-sm text-slate-300">
                {performedSteps.map((id, i) => (
                  <li key={id} className="flex gap-2">
                    <span className="font-mono text-pipe-300">{i + 1}.</span> {stepLabel(id)}
                  </li>
                ))}
              </ol>
            )}
          </Card>

          <Button
            size="lg"
            variant="success"
            className="w-full"
            disabled={performedSteps.length === 0}
            onClick={onFinish}
          >
            ✅ Job done — face the customer
          </Button>
          <p className="mt-2 text-center text-xs text-slate-500">Finishing early saves time points — but unfinished work costs more.</p>
        </div>
      </div>
    </div>
  )
}
