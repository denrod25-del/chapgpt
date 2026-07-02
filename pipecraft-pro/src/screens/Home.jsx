import { useGame } from '../state/GameContext.jsx'
import { useNav } from '../state/NavContext.jsx'
import { rankForXp } from '../data/ranks.js'
import { JOBS } from '../data/jobs.js'
import { LESSONS } from '../data/lessons.js'
import { Card, Button, Badge, money } from '../components/ui.jsx'

export default function Home() {
  const { state } = useGame()
  const { navigate } = useNav()
  const rank = rankForXp(state.xp)
  const jobsDone = state.completedJobs.length
  const availableJobs = JOBS.filter(j => j.minRank <= rank.level).length
  const lessonsLeft = LESSONS.length - state.lessonsDone.length

  const modes = [
    { id: 'academy', icon: '🎓', title: 'Apprentice Mode', desc: `Training Academy — learn supply, drainage, venting, tools & safety. ${lessonsLeft > 0 ? `${lessonsLeft} lessons to go.` : 'All lessons complete!'}`, cta: 'Enter Academy', screen: 'academy' },
    { id: 'service', icon: '🚨', title: 'Service Call Mode', desc: `Take real service calls: diagnose, repair, get paid. ${availableJobs} jobs on the board at your rank.`, cta: 'Open Job Board', screen: 'job-board' },
    { id: 'build', icon: '🏗️', title: 'Build Mode', desc: 'Rough-in a whole house: water, drains, vents, fixtures — then pass inspection.', cta: 'Start Building', screen: 'build' },
    { id: 'business', icon: '💼', title: 'Business Mode', desc: `Run ${state.companyName}: tools, stock, pricing, reviews, and reputation.`, cta: 'Manage Company', screen: 'business' },
  ]

  return (
    <div className="animate-pop">
      {/* Hero */}
      <Card className="relative mb-6 overflow-hidden p-6 sm:p-10">
        <div className="absolute -right-8 -top-8 text-[10rem] opacity-10 select-none">🔧</div>
        <div className="relative">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <Badge tone="orange">v0.1 Prototype</Badge>
            <Badge tone="blue">{rank.icon} {rank.title}</Badge>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-5xl">
            PipeCraft <span className="bg-gradient-to-r from-pipe-400 to-flame-400 bg-clip-text text-transparent">Pro</span>
          </h1>
          <p className="mt-3 max-w-xl text-slate-300">
            The plumbing career simulator. Diagnose real problems, make the repair, keep the customer happy —
            and build your way from shop helper to company owner.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Button size="lg" onClick={() => navigate('job-board')}>🚨 Take a Service Call</Button>
            <Button size="lg" variant="ghost" onClick={() => navigate('career')}>📈 Career Dashboard</Button>
          </div>
        </div>
      </Card>

      {/* Quick stats strip */}
      <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Card className="p-4 text-center">
          <div className="text-2xl font-extrabold text-emerald-400">{money(Math.round(state.money))}</div>
          <div className="text-xs text-slate-400">Company Funds</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-extrabold text-pipe-300">{jobsDone}</div>
          <div className="text-xs text-slate-400">Jobs Completed</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-extrabold text-flame-300">{state.xp}</div>
          <div className="text-xs text-slate-400">Total XP</div>
        </Card>
        <Card className="p-4 text-center">
          <div className="text-2xl font-extrabold text-yellow-400">{state.reputation}</div>
          <div className="text-xs text-slate-400">Reputation</div>
        </Card>
      </div>

      {/* Game modes */}
      <div className="grid gap-4 sm:grid-cols-2">
        {modes.map(m => (
          <Card key={m.id} className="flex flex-col p-5">
            <div className="mb-2 text-3xl">{m.icon}</div>
            <h3 className="text-lg font-bold text-slate-100">{m.title}</h3>
            <p className="mb-4 mt-1 flex-1 text-sm text-slate-400">{m.desc}</p>
            <Button variant={m.id === 'service' ? 'accent' : 'ghost'} onClick={() => navigate(m.screen)}>{m.cta}</Button>
          </Card>
        ))}
      </div>
    </div>
  )
}
