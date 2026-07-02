// Business Mode catalog: van upgrades, staff, and pricing presets.
export const VAN_UPGRADES = [
  { id: 'van-shelving',  name: 'Van Shelving Package', icon: '🗄️', price: 600,  minRank: 3, desc: '+8 slots of parts capacity. Stop losing fittings under the seat.', effect: { capacity: 8 } },
  { id: 'van-wrap',      name: 'Pro Vehicle Wrap',     icon: '🎨', price: 1200, minRank: 3, desc: '+5 reputation. The van IS the billboard.', effect: { reputation: 5 } },
  { id: 'van-gps',       name: 'GPS Dispatch System',  icon: '🛰️', price: 900,  minRank: 3, desc: '+10% time bonus on every job — less windshield time.', effect: { timeBonus: 0.10 } },
  { id: 'van-lift',      name: 'Ladder & Pipe Rack',   icon: '🪜', price: 750,  minRank: 4, desc: 'Carry 20-ft sticks of pipe. Required for repipes (future).', effect: { capacity: 4 } },
  { id: 'van-new',       name: 'New High-Roof Van',    icon: '🚐', price: 8500, minRank: 5, desc: '+15% time bonus, +10 reputation, +12 capacity. The dream rig.', effect: { timeBonus: 0.15, reputation: 10, capacity: 12 } },
]

export const STAFF = [
  { id: 'apprentice-hire', name: 'Hire an Apprentice', icon: '🧑‍🔧', price: 500, wagePerJob: 40, minRank: 3, desc: 'An extra pair of hands: +8 points on every job score, but costs $40/job in wages.' },
]

export const PRICING_TIERS = [
  { id: 'budget',   label: 'Budget',   multiplier: 0.85, satisfactionBonus: +8,  desc: 'Undercut the market. Customers love it; margins hurt.' },
  { id: 'standard', label: 'Standard', multiplier: 1.0,  satisfactionBonus: 0,   desc: 'Fair market rate.' },
  { id: 'premium',  label: 'Premium',  multiplier: 1.25, satisfactionBonus: -6,  desc: 'Top-shelf pricing. Great margins, tougher reviews.' },
  { id: 'luxury',   label: 'White Glove', multiplier: 1.5, satisfactionBonus: -12, desc: 'Concierge plumbing. Only strong reputations survive it.' },
]

export const REVIEW_SNIPPETS = {
  5: ['Absolute pro. Fixed it fast and left the place spotless!', 'Explained everything, fair price, perfect work. 10/10.', 'Best plumber we\'ve ever had. Saving this number.'],
  4: ['Solid work, arrived on time. Would call again.', 'Good job overall, just a bit pricey.', 'Fixed it right the first time.'],
  3: ['Got it done but took longer than quoted.', 'Work was okay. Communication could improve.', 'Average experience. It works now, at least.'],
  2: ['Left a mess and had to come back to finish.', 'Charged for parts we didn\'t seem to need.', 'The "fix" barely outlasted the invoice.'],
  1: ['Made it WORSE. Water everywhere. Never again.', 'Wrong diagnosis, wrong part, wasted day.', 'I want a refund and an apology, in that order.'],
}
