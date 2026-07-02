// Build Mode: rough-in a small house. The player configures each fixture's
// supply, drain, vent, trap, shutoff, and fitting choices plus system-level
// equipment, then runs an inspection. validateBuild() returns code violations.

export const FIXTURES = [
  { id: 'kitchen-sink', name: 'Kitchen Sink', icon: '🍳', room: 'Kitchen',  needsHot: true,  needsCold: true,  needsTrap: true,  drainFittings: ['san-tee', 'wye-45', 'vent-tee'], correctDrainFitting: 'wye-45', drainOrientation: 'horizontal' },
  { id: 'bath-lav',     name: 'Bathroom Sink', icon: '🧼', room: 'Bathroom', needsHot: true,  needsCold: true,  needsTrap: true,  drainFittings: ['san-tee', 'wye-45', 'vent-tee'], correctDrainFitting: 'san-tee', drainOrientation: 'vertical' },
  { id: 'toilet',       name: 'Toilet', icon: '🚽', room: 'Bathroom', needsHot: false, needsCold: true,  needsTrap: false, builtInTrap: true, drainFittings: ['closet-bend', 'san-tee', 'vent-tee'], correctDrainFitting: 'closet-bend', drainOrientation: 'vertical' },
  { id: 'tub-shower',   name: 'Tub / Shower', icon: '🛁', room: 'Bathroom', needsHot: true,  needsCold: true,  needsTrap: true,  drainFittings: ['san-tee', 'wye-45', 'vent-tee'], correctDrainFitting: 'san-tee', drainOrientation: 'vertical', noShutoffOk: true },
  { id: 'washer',       name: 'Washing Machine', icon: '🌀', room: 'Laundry', needsHot: true, needsCold: true, needsTrap: true,  drainFittings: ['san-tee', 'wye-45', 'vent-tee'], correctDrainFitting: 'san-tee', drainOrientation: 'vertical' },
]

export const DRAIN_FITTINGS = {
  'san-tee':     { name: 'Sanitary Tee', desc: 'Sweeps flow downward — for VERTICAL drops.' },
  'wye-45':      { name: 'Wye + 45° (Combo)', desc: 'Smooth entry — for HORIZONTAL branch drains.' },
  'vent-tee':    { name: 'Vent Tee', desc: 'Sharp turn — legal in VENT piping only, never in a drain path.' },
  'closet-bend': { name: 'Closet Bend', desc: 'The 3" sweep that a toilet flange sits on.' },
}

export const SUPPLY_SOURCES = [
  { id: 'none',     label: '— not connected —' },
  { id: 'cold-main', label: 'Cold main' },
  { id: 'wh-hot',   label: 'Water heater HOT out' },
]

export const SLOPES = [
  { id: 'toward-sewer', label: '1/4" per foot toward sewer' },
  { id: 'level',        label: 'Dead level' },
  { id: 'away',         label: 'Sloped away from sewer' },
]

export function emptyBuild() {
  const fixtures = {}
  for (const f of FIXTURES) {
    fixtures[f.id] = {
      hotSource: 'none',
      coldSource: 'none',
      hasShutoff: false,
      drainConnected: false,
      drainSlope: 'level',
      drainFitting: '',
      hasTrap: false,
      hasVent: false,
      stubCapped: true, // uncapped stub = dead end / open line
    }
  }
  return {
    fixtures,
    system: {
      mainShutoff: false,
      whColdIn: 'none',   // should be 'cold-main'
      whHotOutLabeled: false,
      whTprInstalled: false,
      cleanoutInstalled: false,
      hoseBibVacuumBreaker: false,
      hoseBibInstalled: true,
    },
  }
}

// Returns { violations: [{fixture, code, message, severity}], passed: bool, score }
export function validateBuild(build) {
  const v = []
  const add = (fixture, code, message, severity = 'fail') => v.push({ fixture, code, message, severity })
  const sys = build.system

  // --- System level ---
  if (!sys.mainShutoff) add('System', 'SHUTOFF', 'No main shutoff valve installed on the water service.', 'fail')
  if (sys.whColdIn === 'none') add('Water Heater', 'SUPPLY', 'Water heater has no cold supply — it will never fill.', 'fail')
  if (sys.whColdIn === 'wh-hot') add('Water Heater', 'CROSS', 'Water heater inlet looped from its own hot outlet — cross connection.', 'fail')
  if (!sys.whTprInstalled) add('Water Heater', 'SAFETY', 'No T&P relief valve on the water heater. Major safety violation.', 'fail')
  if (!sys.cleanoutInstalled) add('Building Drain', 'CLEANOUT', 'No cleanout installed on the building drain.', 'fail')
  if (sys.hoseBibInstalled && !sys.hoseBibVacuumBreaker) add('Hose Bib', 'CROSS', 'Hose bib has no vacuum breaker — potential cross connection back into the potable system.', 'fail')

  // --- Per fixture ---
  for (const f of FIXTURES) {
    const c = build.fixtures[f.id]
    const name = f.name

    // Supply connections
    if (f.needsCold) {
      if (c.coldSource === 'none') add(name, 'SUPPLY', `${name}: cold side is not connected.`, 'fail')
      else if (c.coldSource === 'wh-hot') add(name, 'CROSS', `${name}: COLD side is fed from the water heater — hot/cold reversed.`, 'fail')
    }
    if (f.needsHot) {
      if (c.hotSource === 'none') add(name, 'SUPPLY', `${name}: hot side is not connected.`, 'fail')
      else if (c.hotSource === 'cold-main') add(name, 'CROSS', `${name}: HOT side is fed from the cold main — hot/cold reversed.`, 'fail')
    }
    if (!f.needsHot && c.hotSource !== 'none') add(name, 'SUPPLY', `${name}: has a hot line it should not have.`, 'warn')

    // Shutoffs
    if (!c.hasShutoff && !f.noShutoffOk) add(name, 'SHUTOFF', `${name}: no fixture shutoff (angle stop) installed.`, 'fail')

    // Drainage
    if (!c.drainConnected) {
      add(name, 'DRAIN', `${name}: drain is not connected to the DWV system.`, 'fail')
    } else {
      if (c.drainSlope === 'level') add(name, 'SLOPE', `${name}: horizontal drain is dead level — needs 1/4" per foot fall.`, 'fail')
      if (c.drainSlope === 'away') add(name, 'SLOPE', `${name}: drain slopes AWAY from the sewer. Water will not leave.`, 'fail')
      if (!c.drainFitting) add(name, 'FITTING', `${name}: no drain fitting selected.`, 'fail')
      else if (c.drainFitting !== f.correctDrainFitting) {
        const chosen = DRAIN_FITTINGS[c.drainFitting]?.name || c.drainFitting
        const correct = DRAIN_FITTINGS[f.correctDrainFitting].name
        add(name, 'FITTING', `${name}: ${chosen} is the wrong fitting for a ${f.drainOrientation} connection — use a ${correct}.`, 'fail')
      }
      if (!c.hasTrap && f.needsTrap) add(name, 'TRAP', `${name}: no trap installed — direct path for sewer gas.`, 'fail')
      if (c.hasTrap && f.builtInTrap) add(name, 'TRAP', `${name}: has a built-in trap; adding another double-traps it.`, 'fail')
      if (!c.hasVent) add(name, 'VENT', `${name}: trap is not vented — it will siphon dry.`, 'fail')
    }

    // Dead ends
    if (!c.stubCapped) add(name, 'DEADEND', `${name}: open/uncapped stub-out — dead end left in the system.`, 'fail')
  }

  const fails = v.filter(x => x.severity === 'fail').length
  const totalChecks = 6 + FIXTURES.length * 7
  const score = Math.max(0, Math.round(100 * (1 - fails / totalChecks)))
  return { violations: v, passed: fails === 0, score }
}
