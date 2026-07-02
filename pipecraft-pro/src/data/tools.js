// Master tool catalog. `owned: true` tools are in the starting tool bag.
// Others must be purchased in Business Mode and may be gated by rank.
export const TOOLS = [
  { id: 'gloves',           name: 'Work Gloves',        icon: '🧤', price: 0,    owned: true,  desc: 'Basic hand protection for every job.' },
  { id: 'sponge',           name: 'Sponge',             icon: '🧽', price: 0,    owned: true,  desc: 'Soaks up leftover tank and trap water.' },
  { id: 'towel',            name: 'Shop Towel',         icon: '🧻', price: 0,    owned: true,  desc: 'Catches drips and keeps the work area dry.' },
  { id: 'flashlight',       name: 'Flashlight',         icon: '🔦', price: 0,    owned: true,  desc: 'Lights up dark cabinets and crawl spaces.' },
  { id: 'bucket',           name: 'Bucket',             icon: '🪣', price: 0,    owned: true,  desc: 'Catches trap water before you open a drain.' },
  { id: 'adjustable-wrench',name: 'Adjustable Wrench',  icon: '🔧', price: 0,    owned: true,  desc: 'The everyday nut-and-fitting turner.' },
  { id: 'channel-locks',    name: 'Channel Locks',      icon: '🗜️', price: 0,    owned: true,  desc: 'Grips slip nuts, supply lines, and valves.' },
  { id: 'plunger',          name: 'Flange Plunger',     icon: '🪠', price: 12,   owned: true,  desc: 'First response for toilet and drain clogs.' },
  { id: 'hand-auger',       name: 'Hand Auger',         icon: '🌀', price: 45,   owned: false, desc: '25 ft drum snake for sink and tub clogs.', minRank: 0 },
  { id: 'multimeter',       name: 'Multimeter',         icon: '⚡', price: 60,   owned: false, desc: 'Verifies power is OFF before electrical work.', minRank: 0 },
  { id: 'element-wrench',   name: 'Element Wrench',     icon: '🛠️', price: 18,   owned: false, desc: 'Removes water heater heating elements.', minRank: 0 },
  { id: 'basin-wrench',     name: 'Basin Wrench',       icon: '🦾', price: 30,   owned: false, desc: 'Reaches faucet nuts behind deep sinks.', minRank: 1 },
  { id: 'pipe-wrench',      name: 'Pipe Wrench',        icon: '🔩', price: 40,   owned: false, desc: 'Heavy grip for threaded iron and steel pipe.', minRank: 2 },
  { id: 'torch-kit',        name: 'Torch Kit',          icon: '🔥', price: 95,   owned: false, desc: 'Solders copper joints. Fire safety required.', minRank: 3 },
  { id: 'press-tool',       name: 'Press Tool',         icon: '🤖', price: 1800, owned: false, desc: 'Presses copper fittings without a flame.', minRank: 4 },
  { id: 'sewer-camera',     name: 'Sewer Camera',       icon: '📹', price: 2500, owned: false, desc: 'Inspects main lines. Unlocks camera jobs.', minRank: 5 },
  { id: 'leak-detector',    name: 'Acoustic Leak Detector', icon: '🎧', price: 1400, owned: false, desc: 'Hears slab leaks through concrete.', minRank: 5 },
  { id: 'jetter',           name: 'Mini Jetter',        icon: '💦', price: 3200, owned: false, desc: 'Blasts grease from drain lines.', minRank: 6 },
]

export const toolById = Object.fromEntries(TOOLS.map(t => [t.id, t]))
