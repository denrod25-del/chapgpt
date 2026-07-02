// Training Academy — Apprentice Mode lessons. Each lesson has teaching
// content plus a short quiz. Passing awards XP once.
export const LESSONS = [
  {
    id: 'water-supply',
    title: 'How Water Supply Works',
    icon: '🚰',
    xp: 30,
    sections: [
      { heading: 'From the street to the fixture', body: 'Water enters the home from the utility main (or a well) through the water service line, passing through the meter and the main shutoff valve. City pressure is typically 50–70 PSI; a pressure regulator (PRV) protects the house if street pressure is higher.' },
      { heading: 'Hot and cold', body: 'The cold line feeds every fixture plus the water heater. The water heater sends a parallel hot line to sinks, tubs, showers, dishwashers, and washing machines. Toilets and hose bibs get cold only. Convention: hot is ALWAYS on the left, cold on the right.' },
      { heading: 'Shutoffs everywhere', body: 'Every fixture should have its own shutoff (angle stop) so you can work on one fixture without shutting down the whole house. The first thing a plumber locates on any job: where do I shut the water off?' },
    ],
    quiz: [
      { q: 'Which side is the hot water on a properly plumbed faucet?', options: ['Left', 'Right', 'Either side', 'Top'], answer: 0 },
      { q: 'What protects a house from excessive street pressure?', options: ['A pressure regulator (PRV)', 'A bigger meter', 'A check valve on the hose bib', 'The water heater'], answer: 0 },
      { q: 'Which fixture normally gets COLD water only?', options: ['The toilet', 'The kitchen sink', 'The shower', 'The dishwasher'], answer: 0 },
    ],
  },
  {
    id: 'drainage',
    title: 'How Drainage Works',
    icon: '⬇️',
    xp: 30,
    sections: [
      { heading: 'Gravity does the work', body: 'Drain-waste (DWV) piping carries wastewater by gravity — no pressure. That means slope matters: horizontal drains must fall 1/4 inch per foot (1/8 inch for 3" and larger) toward the sewer. Too flat and solids sit; too steep and water outruns the solids.' },
      { heading: 'Traps hold the line', body: 'Every fixture drains through a P-trap: a U-shaped bend that stays full of water. That water plug is the only thing standing between the living space and sewer gas. A trap that dries out (an unused floor drain, a guest shower) lets sewer smell straight in.' },
      { heading: 'Cleanouts', body: 'Cleanouts are capped access points that let you run a cable or camera into the drain system without cutting pipe. Code requires them at the building drain and at changes of direction.' },
    ],
    quiz: [
      { q: 'What is the standard slope for a 2" horizontal drain?', options: ['1/4 inch per foot', '1 inch per foot', 'Dead level', '1/16 inch per foot'], answer: 0 },
      { q: 'What stops sewer gas from entering through a fixture?', options: ['The water seal in the P-trap', 'The pop-up stopper', 'The vent cap', 'The angle stop'], answer: 0 },
      { q: 'A guest bathroom smells like sewage but nothing leaks. Most likely cause?', options: ['A dried-out trap', 'A failed PRV', 'Hard water', 'A bad flapper'], answer: 0 },
    ],
  },
  {
    id: 'venting',
    title: 'How Venting Works',
    icon: '🌬️',
    xp: 30,
    sections: [
      { heading: 'Air behind the water', body: 'When a slug of water moves down a drain, air must replace it. Vent pipes rise from the drain system through the roof to supply that air. Without a vent, draining water pulls a vacuum that siphons nearby traps dry.' },
      { heading: 'Symptoms of bad venting', body: 'Gurgling drains, slow drainage with no clog, traps that keep losing their seal, and sewer smells are all classic bad-vent symptoms. The fixture drains, but it fights for air every time.' },
      { heading: 'Rules of thumb', body: 'Every trap needs a vent within a code-limited distance (its trap arm length). Vents must rise above the fixture flood rim before running horizontal, and the main stack terminates above the roof — never into an attic.' },
    ],
    quiz: [
      { q: 'What happens to a trap on an unvented drain?', options: ['It can get siphoned dry', 'It overfills', 'Nothing — vents are optional', 'It freezes'], answer: 0 },
      { q: 'A sink gurgles loudly as it drains. Classic sign of…', options: ['A venting problem', 'High water pressure', 'A bad angle stop', 'A worn flapper'], answer: 0 },
      { q: 'Where must the main vent stack terminate?', options: ['Above the roof', 'In the attic', 'Under the eave', 'In the garage'], answer: 0 },
    ],
  },
  {
    id: 'tools',
    title: 'Common Tools',
    icon: '🧰',
    xp: 25,
    sections: [
      { heading: 'The everyday carry', body: 'Channel locks (tongue-and-groove pliers) grip slip nuts and valve bodies. The adjustable wrench handles hex nuts on supply lines and angle stops. A basin wrench reaches the faucet nuts hidden behind a sink bowl. Buckets and towels are tools too — dry work is professional work.' },
      { heading: 'Drain tools', body: 'A flange plunger seals into a toilet outlet (a flat cup plunger is for sinks). The hand auger — a drum snake — feeds a cable into trap arms and branch drains to hook or break up clogs.' },
      { heading: 'Electric water heater tools', body: 'A multimeter verifies power is dead before you touch wiring — non-negotiable. The element wrench is a cheap socket that removes screw-in heating elements.' },
    ],
    quiz: [
      { q: 'Which tool verifies power is OFF before working on a water heater?', options: ['Multimeter', 'Element wrench', 'Channel locks', 'Basin wrench'], answer: 0 },
      { q: 'Which plunger belongs on a toilet?', options: ['Flange plunger', 'Flat cup plunger', 'Accordion sponge', 'Any of them'], answer: 0 },
      { q: 'What is a basin wrench for?', options: ['Faucet nuts hidden behind the sink bowl', 'Cutting pipe', 'Soldering', 'Removing toilets'], answer: 0 },
    ],
  },
  {
    id: 'fittings',
    title: 'Common Fittings',
    icon: '🔗',
    xp: 25,
    sections: [
      { heading: 'Change direction, change size', body: 'Elbows (90° and 45°) turn corners. Couplings join straight runs. Reducers step pipe sizes down. Caps close a line permanently; plugs close a threaded opening.' },
      { heading: 'Tees and wyes', body: 'A tee joins three lines. On drains, a sanitary tee sweeps flow downward and is used for vertical drops; a wye plus 45° (a combo) is used for horizontal drain branches because it keeps flow moving smoothly. Using a vent tee in a drain path is a code violation.' },
      { heading: 'Traps and stops', body: 'The P-trap kit connects a fixture tailpiece to the drain arm. Angle stops are the little quarter-turn shutoffs at each fixture; supply lines run from the stop to the faucet or toilet.' },
    ],
    quiz: [
      { q: 'Which fitting is correct for a horizontal drain branch?', options: ['Wye + 45 (combo)', 'Vent tee', 'Cross', 'Union'], answer: 0 },
      { q: 'What does a sanitary tee do that a regular tee does not?', options: ['Sweeps flow in the direction of drainage', 'Handles higher pressure', 'Reduces pipe size', 'Nothing — same thing'], answer: 0 },
      { q: 'What is an angle stop?', options: ['A fixture shutoff valve', 'A drain fitting', 'A vent termination', 'A pipe hanger'], answer: 0 },
    ],
  },
  {
    id: 'service-calls',
    title: 'Running a Service Call',
    icon: '📋',
    xp: 35,
    sections: [
      { heading: 'Listen first', body: 'The customer complaint is your first diagnostic tool. When did it start? What changed? What have they tried? Half the diagnosis happens before you open the tool bag.' },
      { heading: 'Diagnose before you repair', body: 'Confirm the cause before selling the fix. Test, observe, isolate: does it affect one fixture or all? Hot, cold, or both? Wrong diagnosis = wrong parts = callback.' },
      { heading: 'Test before you leave', body: 'Every repair gets tested under real conditions: flush it, run it, pressurize it, cycle it. Then show the customer. An untested repair is an unfinished repair.' },
    ],
    quiz: [
      { q: 'What is the FIRST diagnostic step on any service call?', options: ['Listen to the customer', 'Open the wall', 'Replace the likely part', 'Shut off the main'], answer: 0 },
      { q: 'Every fixture in a house has low flow. Where does the problem live?', options: ['At the supply (main/PRV)', 'In one faucet aerator', 'In the toilet flapper', 'In the P-trap'], answer: 0 },
      { q: 'When is a repair finished?', options: ['After it is tested under real conditions', 'When the part is installed', 'When the customer pays', 'When the tools are packed'], answer: 0 },
    ],
  },
  {
    id: 'safety',
    title: 'Safety Rules',
    icon: '⚠️',
    xp: 40,
    sections: [
      { heading: 'Water off, pressure off', body: 'Before opening any pressurized line: shut off the water and bleed the pressure at a faucet. Skipping this floods cabinets, walls, and your reputation.' },
      { heading: 'Electricity and water', body: 'Electric water heaters and disposals can kill. Breaker off, then VERIFY with a meter — breakers get mislabeled. Never energize a water heater element in a dry tank; it burns out in seconds.' },
      { heading: 'Protect yourself and the home', body: 'Gloves against sewage and sharp edges. Eye protection when cutting or snaking overhead. Drop cloths and shoe covers protect floors. Never bypass a gas or flame safety device — ever.' },
    ],
    quiz: [
      { q: 'The breaker for the water heater is off. Before touching wiring you…', options: ['Verify 0 volts with a meter', 'Trust the label', 'Tap the wires quickly', 'Ask the customer'], answer: 0 },
      { q: 'What happens if you power a water heater element in an empty tank?', options: ['It burns out almost instantly', 'It heats faster', 'Nothing', 'It self-primes'], answer: 0 },
      { q: 'Before opening a pressurized water line you must…', options: ['Shut off water AND bleed pressure', 'Put down a towel', 'Loosen it slowly', 'Warn the customer'], answer: 0 },
    ],
  },
]

export const lessonById = Object.fromEntries(LESSONS.map(l => [l.id, l]))
