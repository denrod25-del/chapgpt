import { useState } from 'react'
import { useGame } from '../state/GameContext.jsx'
import { FIXTURES, DRAIN_FITTINGS, SUPPLY_SOURCES, SLOPES, emptyBuild, validateBuild } from '../data/buildMode.js'
import { Card, SectionTitle, Badge, Button, ProgressBar } from '../components/ui.jsx'

// Build Mode: rough-in a starter house, then call for inspection.
// The validator enforces basic plumbing logic (hot/cold, slope, venting,
// traps, shutoffs, fittings, dead ends, cross connections).
export default function BuildMode() {
  const { state, dispatch } = useGame()
  const [build, setBuild] = useState(emptyBuild)
  const [result, setResult] = useState(null)

  const setFixture = (fid, patch) => {
    setBuild(b => ({ ...b, fixtures: { ...b.fixtures, [fid]: { ...b.fixtures[fid], ...patch } } }))
    setResult(null)
  }
  const setSystem = patch => {
    setBuild(b => ({ ...b, system: { ...b.system, ...patch } }))
    setResult(null)
  }

  const inspect = () => {
    const r = validateBuild(build)
    setResult(r)
    const xpEarned = r.passed ? 120 : Math.round(r.score / 4)
    dispatch({ type: 'BUILD_RESULT', score: r.score, xpEarned })
    window.scrollTo({ top: 0 })
  }

  const Toggle = ({ on, onChange, label }) => (
    <button onClick={() => onChange(!on)}
      className={`flex items-center gap-2 rounded-lg border px-2.5 py-1.5 text-xs font-medium transition ${on ? 'border-emerald-500/60 bg-emerald-500/15 text-emerald-300' : 'border-ink-600/60 bg-ink-900/50 text-slate-400 hover:border-slate-500'}`}>
      <span className={`h-2 w-2 rounded-full ${on ? 'bg-emerald-400' : 'bg-slate-600'}`} /> {label}
    </button>
  )

  const Select = ({ value, onChange, options, label }) => (
    <label className="block text-xs">
      <span className="mb-0.5 block text-slate-500">{label}</span>
      <select value={value} onChange={e => onChange(e.target.value)}
        className="w-full rounded-lg border border-ink-600/60 bg-ink-900 px-2 py-1.5 text-xs text-slate-200 outline-none focus:border-pipe-500">
        {options.map(o => <option key={o.id} value={o.id}>{o.label}</option>)}
      </select>
    </label>
  )

  return (
    <div className="animate-pop">
      <SectionTitle sub="Rough-in the Maple Street starter house: supply, drains, vents, and equipment — then call for inspection.">🏗️ Build Mode</SectionTitle>

      {state.buildBestScore != null && (
        <div className="mb-4"><Badge tone="blue">🏆 Best inspection score: {state.buildBestScore}/100</Badge></div>
      )}

      {/* Inspection result banner */}
      {result && (
        <Card className={`mb-5 p-5 ${result.passed ? 'border-emerald-500/50' : 'border-red-500/50'}`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <div className={`text-2xl font-black ${result.passed ? 'text-emerald-400' : 'text-red-400'}`}>
                {result.passed ? '✅ INSPECTION PASSED' : '❌ INSPECTION FAILED'}
              </div>
              <div className="text-sm text-slate-400">{result.violations.filter(v => v.severity === 'fail').length} code violations · rough-in score {result.score}/100</div>
            </div>
            <div className="w-40"><ProgressBar value={result.score} color={result.passed ? 'bg-emerald-500' : 'bg-red-500'} /></div>
          </div>
          {result.violations.length > 0 && (
            <ul className="mt-4 max-h-56 space-y-1.5 overflow-y-auto pr-1 text-sm">
              {result.violations.map((v, i) => (
                <li key={i} className={`flex items-start gap-2 rounded-lg px-3 py-1.5 ${v.severity === 'fail' ? 'bg-red-500/10 text-red-200' : 'bg-yellow-500/10 text-yellow-200'}`}>
                  <Badge tone={v.severity === 'fail' ? 'red' : 'yellow'} className="mt-0.5 shrink-0">{v.code}</Badge>
                  <span>{v.message}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      )}

      {/* System equipment */}
      <Card className="mb-4 p-5">
        <h3 className="mb-3 font-bold text-slate-100">⚙️ System & Equipment</h3>
        <div className="mb-4 flex flex-wrap gap-2">
          <Toggle on={build.system.mainShutoff} onChange={v => setSystem({ mainShutoff: v })} label="Main shutoff valve" />
          <Toggle on={build.system.whTprInstalled} onChange={v => setSystem({ whTprInstalled: v })} label="Water heater T&P valve" />
          <Toggle on={build.system.cleanoutInstalled} onChange={v => setSystem({ cleanoutInstalled: v })} label="Building drain cleanout" />
          <Toggle on={build.system.hoseBibVacuumBreaker} onChange={v => setSystem({ hoseBibVacuumBreaker: v })} label="Hose bib vacuum breaker" />
        </div>
        <div className="max-w-xs">
          <Select label="Water heater cold inlet fed from" value={build.system.whColdIn} onChange={v => setSystem({ whColdIn: v })}
            options={[{ id: 'none', label: '— not connected —' }, { id: 'cold-main', label: 'Cold main' }, { id: 'wh-hot', label: 'Its own hot outlet (?)' }]} />
        </div>
      </Card>

      {/* Fixtures */}
      <div className="grid gap-4 lg:grid-cols-2">
        {FIXTURES.map(f => {
          const c = build.fixtures[f.id]
          return (
            <Card key={f.id} className="p-5">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-2xl">{f.icon}</span>
                <div>
                  <h3 className="font-bold text-slate-100">{f.name}</h3>
                  <div className="text-[11px] text-slate-500">{f.room}{f.builtInTrap ? ' · has a built-in trap' : ''}</div>
                </div>
              </div>

              <div className="mb-3 grid grid-cols-2 gap-2">
                {f.needsHot && (
                  <Select label="Hot supply" value={c.hotSource} onChange={v => setFixture(f.id, { hotSource: v })} options={SUPPLY_SOURCES} />
                )}
                <Select label="Cold supply" value={c.coldSource} onChange={v => setFixture(f.id, { coldSource: v })} options={SUPPLY_SOURCES} />
              </div>

              <div className="mb-3 grid grid-cols-2 gap-2">
                <Select label="Drain slope" value={c.drainSlope} onChange={v => setFixture(f.id, { drainSlope: v })} options={SLOPES} />
                <Select
                  label={`Drain fitting (${f.drainOrientation} connection)`}
                  value={c.drainFitting}
                  onChange={v => setFixture(f.id, { drainFitting: v })}
                  options={[{ id: '', label: '— pick a fitting —' }, ...f.drainFittings.map(id => ({ id, label: DRAIN_FITTINGS[id].name }))]}
                />
              </div>

              <div className="flex flex-wrap gap-2">
                <Toggle on={c.drainConnected} onChange={v => setFixture(f.id, { drainConnected: v })} label="Drain connected" />
                {!f.builtInTrap && <Toggle on={c.hasTrap} onChange={v => setFixture(f.id, { hasTrap: v })} label="Trap installed" />}
                <Toggle on={c.hasVent} onChange={v => setFixture(f.id, { hasVent: v })} label="Vented" />
                {!f.noShutoffOk && <Toggle on={c.hasShutoff} onChange={v => setFixture(f.id, { hasShutoff: v })} label="Shutoff (angle stop)" />}
                <Toggle on={c.stubCapped} onChange={v => setFixture(f.id, { stubCapped: v })} label="Stub-out capped" />
              </div>
            </Card>
          )
        })}
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <Button size="lg" variant="accent" onClick={inspect}>📋 Call for Inspection</Button>
        <Button size="lg" variant="ghost" onClick={() => { setBuild(emptyBuild()); setResult(null) }}>↺ Tear out & restart</Button>
      </div>
      <p className="mt-3 text-xs text-slate-500">
        Passing pays 120 XP. Fitting cheat sheet: sanitary tee = vertical drops · wye+45 = horizontal branches · vent tees never live in a drain path.
      </p>
    </div>
  )
}
