import { Card, Button, SectionTitle } from '../../components/ui.jsx'

// Phase 1 on site: work the inspection checklist to reveal findings,
// then commit to a diagnosis. The diagnosis is worth 25 points.
export default function DiagnosisChecklist({ job, checkedItems, setCheckedItems, diagnosisId, setDiagnosisId, onCommit }) {
  const check = id => {
    if (!checkedItems.includes(id)) setCheckedItems([...checkedItems, id])
  }

  return (
    <div>
      <SectionTitle sub="Investigate before you commit. Each check reveals a finding — some crack the case.">🔍 Diagnosis Checklist</SectionTitle>

      <Card className="mb-4 p-5">
        <div className="space-y-2.5">
          {job.checklist.map(item => {
            const done = checkedItems.includes(item.id)
            return (
              <button
                key={item.id}
                onClick={() => check(item.id)}
                className={`block w-full rounded-xl border p-3 text-left transition ${done ? 'border-emerald-500/50 bg-emerald-500/10' : 'border-ink-600/60 bg-ink-900/50 hover:border-pipe-500/60'}`}
              >
                <div className="flex items-center gap-2.5 text-sm font-medium text-slate-200">
                  <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md border text-xs ${done ? 'border-emerald-400 bg-emerald-500 text-white' : 'border-slate-500'}`}>
                    {done ? '✓' : ''}
                  </span>
                  {item.label}
                </div>
                {done && (
                  <div className={`mt-2 ml-7 rounded-lg px-3 py-2 text-sm animate-pop ${item.key ? 'bg-flame-500/15 text-flame-200' : 'bg-ink-700/60 text-slate-300'}`}>
                    {item.key ? '🔑 ' : '📝 '}{item.finding}
                  </div>
                )}
              </button>
            )
          })}
        </div>
      </Card>

      <Card className="mb-6 p-5">
        <h3 className="mb-3 font-bold text-slate-100">Commit to a diagnosis <span className="text-xs font-normal text-flame-300">(25 pts)</span></h3>
        <div className="space-y-2">
          {job.diagnosisOptions.map(opt => (
            <label
              key={opt.id}
              className={`flex cursor-pointer items-center gap-3 rounded-xl border p-3 text-sm transition ${diagnosisId === opt.id ? 'border-pipe-500 bg-pipe-500/15 text-pipe-200' : 'border-ink-600/60 bg-ink-900/50 text-slate-300 hover:border-slate-500'}`}
            >
              <input
                type="radio"
                name="diagnosis"
                className="accent-pipe-500"
                checked={diagnosisId === opt.id}
                onChange={() => setDiagnosisId(opt.id)}
              />
              {opt.label}
            </label>
          ))}
        </div>
      </Card>

      <Button size="lg" variant="accent" disabled={!diagnosisId} onClick={onCommit}>
        🛠️ Lock in diagnosis & start the repair
      </Button>
      {!diagnosisId && <p className="mt-2 text-xs text-slate-500">Pick a diagnosis to continue.</p>}
    </div>
  )
}
