import { Card, Button, SectionTitle, Badge } from '../../components/ui.jsx'

// City inspection report for jobs that require sign-off (water heaters, etc.).
export default function InspectionReport({ job, report, onBack }) {
  const insp = report.inspection

  return (
    <div className="animate-pop">
      <SectionTitle sub="Permit work gets checked. The inspector saw everything you did — and didn't do.">📄 Inspection Report</SectionTitle>

      <Card className="mb-4 p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3 border-b border-ink-600/60 pb-4">
          <div>
            <div className="text-xs uppercase tracking-widest text-slate-500">City of Palmwater — Plumbing Division</div>
            <div className="text-lg font-bold text-slate-100">Permit #{String(1000 + (report.seq || 1)).padStart(5, '0')} · {job.title}</div>
            <div className="text-xs text-slate-500">{job.propertyType} · Contractor: PipeCraft Plumbing</div>
          </div>
          <div className={`rounded-xl border-2 px-4 py-2 text-xl font-black tracking-widest ${insp.passed ? 'rotate-2 border-emerald-500 text-emerald-400' : '-rotate-2 border-red-500 text-red-400'}`}>
            {insp.passed ? 'PASSED' : 'FAILED'}
          </div>
        </div>

        <div className="space-y-2.5">
          {insp.checks.map(c => (
            <div key={c.id} className={`flex items-center justify-between gap-3 rounded-xl p-3 text-sm ${c.passed ? 'bg-emerald-500/10' : 'bg-red-500/10'}`}>
              <span className={c.passed ? 'text-emerald-200' : 'text-red-200'}>{c.label}</span>
              <Badge tone={c.passed ? 'green' : 'red'}>{c.passed ? '✓ PASS' : '✗ FAIL'}</Badge>
            </div>
          ))}
        </div>

        {!insp.passed && (
          <p className="mt-4 rounded-xl bg-yellow-500/10 p-3 text-sm text-yellow-300">
            📎 Corrections required. In a future update, failed inspections will trigger a re-inspection visit and a fee.
          </p>
        )}
      </Card>

      <Button variant="accent" onClick={onBack}>← Back to job results</Button>
    </div>
  )
}
