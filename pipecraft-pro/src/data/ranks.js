// Career ladder. `xp` is the total XP needed to reach the rank.
export const RANKS = [
  { level: 0, title: 'Helper',                 xp: 0,     icon: '🧹', unlocks: ['Basic service calls', 'Training Academy'] },
  { level: 1, title: 'Apprentice',             xp: 150,   icon: '🔩', unlocks: ['Basin wrench in the shop', 'Garbage disposal jobs'] },
  { level: 2, title: 'Service Tech',           xp: 400,   icon: '🔧', unlocks: ['Whole-house pressure jobs', 'Tub/shower valve jobs', 'Pipe wrench'] },
  { level: 3, title: 'Lead Tech',              xp: 800,   icon: '🛠️', unlocks: ['Torch kit', 'Van upgrades', 'Hire an apprentice'] },
  { level: 4, title: 'Licensed Plumber',       xp: 1400,  icon: '📜', unlocks: ['Tankless water heater jobs', 'Press tool', 'Build Mode inspections'] },
  { level: 5, title: 'Contractor',             xp: 2200,  icon: '🏗️', unlocks: ['Slab leak detection', 'Sewer camera', 'Commercial pricing'] },
  { level: 6, title: 'Plumbing Company Owner', xp: 3200,  icon: '👑', unlocks: ['Jetter', 'Full business controls', 'Excavation contracts (coming soon)'] },
]

export function rankForXp(xp) {
  let rank = RANKS[0]
  for (const r of RANKS) if (xp >= r.xp) rank = r
  return rank
}

export function nextRank(xp) {
  return RANKS.find(r => r.xp > xp) || null
}
