import { useGame } from '../state/GameContext.jsx'
import { rankForXp, nextRank } from '../data/ranks.js'
import { ProgressBar, money } from './ui.jsx'

// Persistent top bar: rank, XP bar, money tracker, reputation meter.
export default function HUD() {
  const { state } = useGame()
  const rank = rankForXp(state.xp)
  const next = nextRank(state.xp)
  const xpInto = state.xp - rank.xp
  const xpSpan = next ? next.xp - rank.xp : 1

  const repTone = state.reputation >= 70 ? 'bg-emerald-500' : state.reputation >= 40 ? 'bg-yellow-500' : 'bg-red-500'

  return (
    <div className="sticky top-0 z-40 border-b border-ink-600/60 bg-ink-900/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5">
        <div className="flex items-center gap-2">
          <span className="text-xl">{rank.icon}</span>
          <div>
            <div className="text-sm font-bold leading-tight text-slate-100">{rank.title}</div>
            <div className="text-[11px] leading-tight text-slate-400">Level {rank.level + 1} of 7</div>
          </div>
        </div>

        <div className="min-w-36 flex-1">
          <div className="mb-1 flex justify-between text-[11px] text-slate-400">
            <span>XP {state.xp}</span>
            <span>{next ? `${next.xp} → ${next.title}` : 'MAX RANK'}</span>
          </div>
          <ProgressBar value={next ? xpInto : 1} max={next ? xpSpan : 1} color="bg-gradient-to-r from-pipe-500 to-flame-500" />
        </div>

        <div className="flex items-center gap-1.5" title="Company funds">
          <span className="text-lg">💵</span>
          <span className={`text-sm font-bold ${state.money < 0 ? 'text-red-400' : 'text-emerald-400'}`}>{money(Math.round(state.money))}</span>
        </div>

        <div className="flex items-center gap-2" title={`Reputation ${state.reputation}/100`}>
          <span className="text-lg">⭐</span>
          <div className="w-20">
            <ProgressBar value={state.reputation} color={repTone} />
          </div>
          <span className="text-xs font-semibold text-slate-300">{state.reputation}</span>
        </div>
      </div>
    </div>
  )
}
