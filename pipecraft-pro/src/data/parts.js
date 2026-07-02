// Master parts catalog. `stock` is the starting van stock.
// cost = what the player pays to restock, charge = what the customer is billed.
export const PARTS = [
  { id: 'toilet-flapper',   name: 'Toilet Flapper',          icon: '🔴', cost: 6,   charge: 18,  stock: 3 },
  { id: 'fill-valve',       name: 'Fill Valve',              icon: '🗼', cost: 11,  charge: 32,  stock: 2 },
  { id: 'angle-stop-half',  name: '1/2" Angle Stop',         icon: '🚰', cost: 9,   charge: 28,  stock: 4 },
  { id: 'supply-line',      name: 'Braided Supply Line',     icon: '🐍', cost: 7,   charge: 20,  stock: 4 },
  { id: 'wh-element',       name: 'Water Heater Element 4500W', icon: '🌡️', cost: 14, charge: 45, stock: 2 },
  { id: 'wh-thermostat',    name: 'Water Heater Thermostat', icon: '🎛️', cost: 12,  charge: 38,  stock: 1 },
  { id: 'p-trap',           name: '1-1/2" P-Trap Kit',       icon: '↩️', cost: 8,   charge: 24,  stock: 3 },
  { id: 'wax-ring',         name: 'Wax Ring',                icon: '🟡', cost: 5,   charge: 16,  stock: 2 },
  { id: 'washer-kit',       name: 'Faucet Washer Kit',       icon: '⭕', cost: 4,   charge: 12,  stock: 5 },
  { id: 'teflon-tape',      name: 'PTFE Thread Tape',        icon: '🎞️', cost: 2,   charge: 5,   stock: 10 },
  { id: 'disposal-unit',    name: 'Garbage Disposal 1/2 HP', icon: '🌪️', cost: 85,  charge: 190, stock: 0 },
  { id: 'shower-cartridge', name: 'Shower Valve Cartridge',  icon: '🎯', cost: 28,  charge: 75,  stock: 1 },
]

export const partById = Object.fromEntries(PARTS.map(p => [p.id, p]))
