import { useState } from 'react'
import { useGame } from '../state/GameContext.jsx'
import { Card, SectionTitle, Button, Badge } from '../components/ui.jsx'

export default function Settings() {
  const { state, dispatch } = useGame()
  const [confirmReset, setConfirmReset] = useState(false)

  const set = (key, value) => dispatch({ type: 'SET_SETTING', key, value })

  return (
    <div className="animate-pop">
      <SectionTitle sub="Game options and save management. Progress autosaves to this browser.">⚙️ Settings</SectionTitle>

      <Card className="mb-4 p-5">
        <h3 className="mb-3 font-bold text-slate-100">Company</h3>
        <label className="block max-w-sm text-sm">
          <span className="mb-1 block text-slate-400">Company name</span>
          <input
            value={state.companyName}
            onChange={e => dispatch({ type: 'SET_NAME', field: 'companyName', value: e.target.value })}
            className="w-full rounded-xl border border-ink-600/60 bg-ink-900 px-3 py-2 text-slate-100 outline-none focus:border-pipe-500"
            maxLength={32}
          />
        </label>
      </Card>

      <Card className="mb-4 p-5">
        <h3 className="mb-3 font-bold text-slate-100">Difficulty</h3>
        <div className="flex flex-wrap gap-2">
          {[
            { id: 'easy', label: '🟢 Easy', desc: '+50% time on every job' },
            { id: 'normal', label: '🔵 Normal', desc: 'Standard time limits' },
            { id: 'hard', label: '🔴 Hard', desc: '−25% time on every job' },
          ].map(d => (
            <button key={d.id} onClick={() => set('difficulty', d.id)}
              className={`rounded-xl border p-3 text-left text-sm transition ${state.settings.difficulty === d.id ? 'border-pipe-500 bg-pipe-500/15' : 'border-ink-600/60 hover:border-slate-500'}`}>
              <div className="font-semibold text-slate-100">{d.label}</div>
              <div className="text-xs text-slate-500">{d.desc}</div>
            </button>
          ))}
        </div>
      </Card>

      <Card className="mb-4 p-5">
        <h3 className="mb-3 font-bold text-slate-100">Gameplay</h3>
        <div className="space-y-3">
          <ToggleRow
            label="Loadout hints"
            desc="Show how many tools/parts a job probably needs on the load-out screen."
            on={state.settings.showHints}
            onChange={v => set('showHints', v)}
          />
          <ToggleRow
            label="Sound effects"
            desc="Reserved for a future update — flip it now so you're ready."
            on={state.settings.sound}
            onChange={v => set('sound', v)}
          />
        </div>
      </Card>

      <Card className="p-5">
        <h3 className="mb-1 font-bold text-red-300">Danger Zone</h3>
        <p className="mb-3 text-xs text-slate-500">Wipes XP, money, inventory, history — everything. No undo.</p>
        {confirmReset ? (
          <div className="flex flex-wrap items-center gap-3">
            <Badge tone="red">Are you sure?</Badge>
            <Button variant="danger" size="sm" onClick={() => { dispatch({ type: 'RESET' }); setConfirmReset(false) }}>Yes, reset everything</Button>
            <Button variant="ghost" size="sm" onClick={() => setConfirmReset(false)}>Cancel</Button>
          </div>
        ) : (
          <Button variant="danger" size="sm" onClick={() => setConfirmReset(true)}>Reset all progress</Button>
        )}
      </Card>

      <p className="mt-6 text-center text-xs text-slate-600">PipeCraft Pro v0.1 — prototype build · mock data, no backend</p>
    </div>
  )
}

function ToggleRow({ label, desc, on, onChange }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <div className="text-sm font-semibold text-slate-200">{label}</div>
        <div className="text-xs text-slate-500">{desc}</div>
      </div>
      <button onClick={() => onChange(!on)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition ${on ? 'bg-pipe-500' : 'bg-ink-600'}`}
        aria-pressed={on}>
        <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${on ? 'left-5.5' : 'left-0.5'}`} />
      </button>
    </div>
  )
}
