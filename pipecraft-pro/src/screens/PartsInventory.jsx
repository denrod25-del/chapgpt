import { useGame, vanCapacity, totalStock } from '../state/GameContext.jsx'
import { PARTS } from '../data/parts.js'
import { Card, SectionTitle, Badge, Button, ProgressBar, money } from '../components/ui.jsx'

export default function PartsInventory() {
  const { state, dispatch } = useGame()
  const cap = vanCapacity(state)
  const used = totalStock(state)

  return (
    <div className="animate-pop">
      <SectionTitle sub="Parts get consumed on jobs. Run out mid-week and you're eating a supply-house run.">🔩 Parts Inventory</SectionTitle>

      <Card className="mb-5 p-4">
        <div className="mb-1.5 flex justify-between text-sm">
          <span className="font-semibold text-slate-200">Van stock capacity</span>
          <span className={used >= cap ? 'font-bold text-red-400' : 'text-slate-400'}>{used} / {cap} slots</span>
        </div>
        <ProgressBar value={used} max={cap} color={used >= cap ? 'bg-red-500' : 'bg-flame-500'} />
      </Card>

      <div className="grid gap-3 sm:grid-cols-2">
        {PARTS.map(p => {
          const qty = state.partsStock[p.id] || 0
          const full = used >= cap
          const cantAfford = state.money < p.cost
          return (
            <Card key={p.id} className="flex items-center gap-3 p-4">
              <div className="text-3xl">{p.icon}</div>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-bold text-slate-100">{p.name}</div>
                <div className="text-xs text-slate-500">Cost {money(p.cost)} · Bills at {money(p.charge)}</div>
              </div>
              <Badge tone={qty === 0 ? 'red' : qty <= 1 ? 'yellow' : 'green'}>×{qty}</Badge>
              <Button size="sm" variant="ghost" disabled={full || cantAfford} onClick={() => dispatch({ type: 'BUY_PART', id: p.id, qty: 1 })}>
                +1 ({money(p.cost)})
              </Button>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
