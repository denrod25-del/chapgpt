import { useGame } from '../state/GameContext.jsx'
import { rankForXp, RANKS } from '../data/ranks.js'
import { TOOLS } from '../data/tools.js'
import { Card, SectionTitle, Badge, Button, money } from '../components/ui.jsx'

export default function ToolBag() {
  const { state, dispatch } = useGame()
  const rank = rankForXp(state.xp)
  const owned = TOOLS.filter(t => state.ownedTools.includes(t.id))
  const shop = TOOLS.filter(t => !state.ownedTools.includes(t.id))

  return (
    <div className="animate-pop">
      <SectionTitle sub="Every tool you own rides on every call. Buy new capability in the shop below.">🧰 Tool Bag</SectionTitle>

      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {owned.map(t => (
          <Card key={t.id} className="p-4">
            <div className="text-3xl">{t.icon}</div>
            <div className="mt-1 text-sm font-bold text-slate-100">{t.name}</div>
            <div className="mt-0.5 text-xs text-slate-500">{t.desc}</div>
          </Card>
        ))}
      </div>

      <SectionTitle sub="Tools unlock as you rank up. Buying the right tool unlocks harder (better-paying) jobs.">🛒 Supply House</SectionTitle>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {shop.map(t => {
          const locked = (t.minRank || 0) > rank.level
          const cantAfford = state.money < t.price
          return (
            <Card key={t.id} className={`flex flex-col p-4 ${locked ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between">
                <div className="text-3xl">{t.icon}</div>
                <Badge tone="orange">{money(t.price)}</Badge>
              </div>
              <div className="mt-1 text-sm font-bold text-slate-100">{t.name}</div>
              <div className="mb-3 mt-0.5 flex-1 text-xs text-slate-500">{t.desc}</div>
              {locked ? (
                <Button size="sm" variant="ghost" disabled>🔒 {RANKS[t.minRank].title}+</Button>
              ) : (
                <Button size="sm" disabled={cantAfford} onClick={() => dispatch({ type: 'BUY_TOOL', id: t.id })}>
                  {cantAfford ? 'Not enough funds' : 'Buy'}
                </Button>
              )}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
