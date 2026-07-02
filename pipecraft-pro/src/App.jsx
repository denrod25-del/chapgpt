import { NavProvider, useNav } from './state/NavContext.jsx'
import HUD from './components/HUD.jsx'
import Home from './screens/Home.jsx'
import CareerDashboard from './screens/CareerDashboard.jsx'
import JobBoard from './screens/JobBoard.jsx'
import ServiceCall from './screens/ServiceCall.jsx'
import ToolBag from './screens/ToolBag.jsx'
import PartsInventory from './screens/PartsInventory.jsx'
import VanInventory from './screens/VanInventory.jsx'
import BusinessDashboard from './screens/BusinessDashboard.jsx'
import TrainingAcademy from './screens/TrainingAcademy.jsx'
import BuildMode from './screens/BuildMode.jsx'
import Settings from './screens/Settings.jsx'

const NAV_ITEMS = [
  { id: 'home', label: 'Home', icon: '🏠' },
  { id: 'career', label: 'Career', icon: '📈' },
  { id: 'job-board', label: 'Job Board', icon: '📋' },
  { id: 'academy', label: 'Academy', icon: '🎓' },
  { id: 'build', label: 'Build Mode', icon: '🏗️' },
  { id: 'toolbag', label: 'Tool Bag', icon: '🧰' },
  { id: 'parts', label: 'Parts', icon: '🔩' },
  { id: 'van', label: 'Van', icon: '🚐' },
  { id: 'business', label: 'Business', icon: '💼' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
]

const SCREENS = {
  home: Home,
  career: CareerDashboard,
  'job-board': JobBoard,
  'service-call': ServiceCall,
  toolbag: ToolBag,
  parts: PartsInventory,
  van: VanInventory,
  business: BusinessDashboard,
  academy: TrainingAcademy,
  build: BuildMode,
  settings: Settings,
}

function Shell() {
  const { route, navigate } = useNav()
  const Screen = SCREENS[route.screen] || Home
  const inCall = route.screen === 'service-call'

  return (
    <div className="flex min-h-screen flex-col">
      <HUD />
      <div className="mx-auto flex w-full max-w-6xl flex-1 gap-6 px-4 py-6">
        {/* Sidebar (desktop) — hidden during an active service call for focus */}
        {!inCall && (
          <nav className="hidden w-44 shrink-0 flex-col gap-1 md:flex">
            {NAV_ITEMS.map(item => (
              <button
                key={item.id}
                onClick={() => navigate(item.id)}
                className={`flex items-center gap-2.5 rounded-xl px-3 py-2 text-left text-sm font-medium transition ${
                  route.screen === item.id
                    ? 'bg-pipe-500/20 text-pipe-300 shadow-inner'
                    : 'text-slate-400 hover:bg-ink-700/60 hover:text-slate-200'
                }`}
              >
                <span className="text-base">{item.icon}</span> {item.label}
              </button>
            ))}
          </nav>
        )}
        <main className="min-w-0 flex-1 pb-20 md:pb-4">
          <Screen key={route.screen + (route.params.jobId || '')} {...route.params} />
        </main>
      </div>

      {/* Bottom nav (mobile) */}
      {!inCall && (
        <nav className="fixed inset-x-0 bottom-0 z-40 flex justify-around border-t border-ink-600/60 bg-ink-900/95 py-1.5 backdrop-blur md:hidden">
          {NAV_ITEMS.slice(0, 5).map(item => (
            <button
              key={item.id}
              onClick={() => navigate(item.id)}
              className={`flex flex-col items-center rounded-lg px-2 py-1 text-[10px] font-medium ${
                route.screen === item.id ? 'text-pipe-300' : 'text-slate-400'
              }`}
            >
              <span className="text-lg">{item.icon}</span>
              {item.label}
            </button>
          ))}
          <button
            onClick={() => navigate('business')}
            className={`flex flex-col items-center rounded-lg px-2 py-1 text-[10px] font-medium ${
              ['business', 'toolbag', 'parts', 'van', 'settings'].includes(route.screen) ? 'text-pipe-300' : 'text-slate-400'
            }`}
          >
            <span className="text-lg">💼</span>
            More
          </button>
        </nav>
      )}
    </div>
  )
}

export default function App() {
  return (
    <NavProvider>
      <Shell />
    </NavProvider>
  )
}
