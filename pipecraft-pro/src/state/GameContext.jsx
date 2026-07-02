import { createContext, useContext, useEffect, useReducer } from 'react'
import { TOOLS } from '../data/tools.js'
import { PARTS } from '../data/parts.js'
import { VAN_UPGRADES } from '../data/business.js'

const SAVE_KEY = 'pipecraft-pro-save-v1'
export const BASE_VAN_CAPACITY = 40

export function initialState() {
  return {
    playerName: 'You',
    companyName: 'PipeCraft Plumbing',
    xp: 0,
    money: 250,
    reputation: 50,
    ownedTools: TOOLS.filter(t => t.owned).map(t => t.id),
    partsStock: Object.fromEntries(PARTS.map(p => [p.id, p.stock])),
    vanUpgrades: [],
    apprenticeHired: false,
    pricingTier: 'standard',
    completedJobs: [],   // newest first: {jobId, title, icon, score, stars, revenue, partsCost, wages, profit, review, inspectionPassed, seq}
    ledger: [],          // newest first: {label, amount, seq}
    lessonsDone: [],
    bestScores: {},
    buildBestScore: null,
    seq: 1,              // monotonically increasing event counter (mock clock)
    settings: { difficulty: 'normal', sound: true, showHints: true },
  }
}

function loadState() {
  try {
    const raw = localStorage.getItem(SAVE_KEY)
    if (!raw) return initialState()
    const saved = JSON.parse(raw)
    // Merge over defaults so new fields added in updates don't break old saves.
    const base = initialState()
    return { ...base, ...saved, settings: { ...base.settings, ...saved.settings } }
  } catch {
    return initialState()
  }
}

export function vanCapacity(state) {
  return BASE_VAN_CAPACITY + state.vanUpgrades
    .map(id => VAN_UPGRADES.find(u => u.id === id)?.effect?.capacity || 0)
    .reduce((a, b) => a + b, 0)
}

export function vanTimeBonus(state) {
  return state.vanUpgrades
    .map(id => VAN_UPGRADES.find(u => u.id === id)?.effect?.timeBonus || 0)
    .reduce((a, b) => a + b, 0)
}

export function totalStock(state) {
  return Object.values(state.partsStock).reduce((a, b) => a + b, 0)
}

const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n))

function reducer(state, action) {
  switch (action.type) {
    case 'COMPLETE_JOB': {
      const r = action.report
      const stock = { ...state.partsStock }
      for (const partId of r.partsUsed) {
        if (stock[partId] > 0) stock[partId] -= 1
      }
      const repDelta = (r.stars - 3) * 3
      const seq = state.seq + 1
      const ledger = [
        { label: `Job: ${r.title} — labor & parts`, amount: r.revenue, seq },
        ...(r.wages ? [{ label: 'Apprentice wages', amount: -r.wages, seq }] : []),
        ...state.ledger,
      ].slice(0, 60)
      return {
        ...state,
        seq,
        money: Math.round((state.money + r.revenue - r.wages) * 100) / 100,
        xp: state.xp + r.xpEarned,
        reputation: clamp(state.reputation + repDelta, 0, 100),
        partsStock: stock,
        completedJobs: [{ ...r, seq }, ...state.completedJobs].slice(0, 40),
        bestScores: { ...state.bestScores, [r.jobId]: Math.max(state.bestScores[r.jobId] || 0, r.score) },
        ledger,
      }
    }
    case 'BUY_TOOL': {
      const tool = TOOLS.find(t => t.id === action.id)
      if (!tool || state.ownedTools.includes(tool.id) || state.money < tool.price) return state
      const seq = state.seq + 1
      return {
        ...state, seq,
        money: state.money - tool.price,
        ownedTools: [...state.ownedTools, tool.id],
        ledger: [{ label: `Bought tool: ${tool.name}`, amount: -tool.price, seq }, ...state.ledger].slice(0, 60),
      }
    }
    case 'BUY_PART': {
      const part = PARTS.find(p => p.id === action.id)
      const qty = action.qty || 1
      const cost = part.cost * qty
      if (!part || state.money < cost) return state
      if (totalStock(state) + qty > vanCapacity(state)) return state
      const seq = state.seq + 1
      return {
        ...state, seq,
        money: Math.round((state.money - cost) * 100) / 100,
        partsStock: { ...state.partsStock, [part.id]: (state.partsStock[part.id] || 0) + qty },
        ledger: [{ label: `Restocked: ${part.name} ×${qty}`, amount: -cost, seq }, ...state.ledger].slice(0, 60),
      }
    }
    case 'BUY_UPGRADE': {
      const up = VAN_UPGRADES.find(u => u.id === action.id)
      if (!up || state.vanUpgrades.includes(up.id) || state.money < up.price) return state
      const seq = state.seq + 1
      return {
        ...state, seq,
        money: state.money - up.price,
        reputation: clamp(state.reputation + (up.effect?.reputation || 0), 0, 100),
        vanUpgrades: [...state.vanUpgrades, up.id],
        ledger: [{ label: `Van upgrade: ${up.name}`, amount: -up.price, seq }, ...state.ledger].slice(0, 60),
      }
    }
    case 'HIRE_APPRENTICE': {
      if (state.apprenticeHired || state.money < action.price) return state
      const seq = state.seq + 1
      return {
        ...state, seq,
        money: state.money - action.price,
        apprenticeHired: true,
        ledger: [{ label: 'Hired an apprentice', amount: -action.price, seq }, ...state.ledger].slice(0, 60),
      }
    }
    case 'SET_PRICING':
      return { ...state, pricingTier: action.tier }
    case 'COMPLETE_LESSON': {
      if (state.lessonsDone.includes(action.id)) return state
      return { ...state, lessonsDone: [...state.lessonsDone, action.id], xp: state.xp + action.xp }
    }
    case 'BUILD_RESULT':
      return {
        ...state,
        buildBestScore: Math.max(state.buildBestScore || 0, action.score),
        xp: state.xp + (action.xpEarned || 0),
      }
    case 'SET_SETTING':
      return { ...state, settings: { ...state.settings, [action.key]: action.value } }
    case 'SET_NAME':
      return { ...state, [action.field]: action.value }
    case 'RESET':
      return initialState()
    default:
      return state
  }
}

const GameContext = createContext(null)

export function GameProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, undefined, loadState)

  useEffect(() => {
    try { localStorage.setItem(SAVE_KEY, JSON.stringify(state)) } catch { /* storage full/blocked */ }
  }, [state])

  return <GameContext.Provider value={{ state, dispatch }}>{children}</GameContext.Provider>
}

export function useGame() {
  const ctx = useContext(GameContext)
  if (!ctx) throw new Error('useGame must be used inside <GameProvider>')
  return ctx
}
