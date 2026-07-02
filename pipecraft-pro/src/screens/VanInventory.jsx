import { useGame, vanCapacity, totalStock, vanTimeBonus } from '../state/GameContext.jsx'
import { rankForXp, RANKS } from '../data/ranks.js'
import { VAN_UPGRADES } from '../data/business.js'
import { TOOLS } from '../data/tools.js'
import { PARTS } from '../data/parts.js'
import { Card, SectionTitle, Badge, Button, Stat, money } from '../components/ui.jsx'

export default function VanInventory() {
  const { state, dispatch } = useGame()
  const rank = rankForXp(state.xp)
  const ownedTools = TOOLS.filter(t => state.ownedTools.includes(t.id))
  const stockedParts = PARTS.filter(p => (state.partsStock[p.id] || 0) > 0)

  return (
    <div className="animate-pop">
      <SectionTitle sub="Everything that rolls with you: tools, stock, and the rig itself.">🚐 Van Inventory</SectionTitle>

      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Tools Aboard" value={ownedTools.length} icon="🧰" />
        <Stat label="Parts Stocked" value={`${totalStock(state)} / ${vanCapacity(state)}`} icon="🔩" />
        <Stat label="Time Bonus" value={`+${Math.round(vanTimeBonus(state) * 100)}%`} icon="⏱️" tone="text-pipe-300" />
        <Stat label="Upgrades" value={`${state.vanUpgrades.length} / ${VAN_UPGRADES.length}`} icon="⭐" />
      </div>

      <Card className="mb-6 p-5">
        <h3 className="mb-3 font-bold text-slate-100">On the Shelves</h3>
        <div className="mb-3 flex flex-wrap gap-2">
          {ownedTools.map(t => <Badge key={t.id} tone="blue">{t.icon} {t.name}</Badge>)}
        </div>
        <div className="flex flex-wrap gap-2">
          {stockedParts.length === 0
            ? <span className="text-sm text-slate-500">No parts stocked — visit Parts Inventory before your next call.</span>
            : stockedParts.map(p => <Badge key={p.id} tone="orange">{p.icon} {p.name} ×{state.partsStock[p.id]}</Badge>)}
        </div>
      </Card>

      <SectionTitle sub="Upgrades are permanent and stack. Unlock at Lead Tech.">🔧 Van Upgrades</SectionTitle>
      <div className="grid gap-3 sm:grid-cols-2">
        {VAN_UPGRADES.map(u => {
          const ownedUp = state.vanUpgrades.includes(u.id)
          const locked = u.minRank > rank.level
          const cantAfford = state.money < u.price
          return (
            <Card key={u.id} className={`flex flex-col p-4 ${locked && !ownedUp ? 'opacity-60' : ''}`}>
              <div className="flex items-start justify-between">
                <div className="text-3xl">{u.icon}</div>
                {ownedUp ? <Badge tone="green">✓ Installed</Badge> : <Badge tone="orange">{money(u.price)}</Badge>}
              </div>
              <div className="mt-1 text-sm font-bold text-slate-100">{u.name}</div>
              <div className="mb-3 mt-0.5 flex-1 text-xs text-slate-500">{u.desc}</div>
              {!ownedUp && (
                locked
                  ? <Button size="sm" variant="ghost" disabled>🔒 {RANKS[u.minRank].title}+</Button>
                  : <Button size="sm" disabled={cantAfford} onClick={() => dispatch({ type: 'BUY_UPGRADE', id: u.id })}>{cantAfford ? 'Not enough funds' : 'Install'}</Button>
              )}
            </Card>
          )
        })}
      </div>
    </div>
  )
}
