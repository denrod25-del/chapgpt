# 🔧 PipeCraft Pro — Plumbing Career Simulator

A web-based plumbing simulation game and future trade-school training tool.
Play as a plumber working real service calls: diagnose the problem, bring the
right tools and parts, do the repair in the right order (safety first!), keep
the customer happy, and grow from shop Helper to Plumbing Company Owner.

**Stack:** React 19 · Vite · Tailwind CSS v4 · React Context + reducer state ·
localStorage save · mock data, no backend.

## Run it

```bash
cd pipecraft-pro
npm install
npm run dev      # local dev server
npm run build    # production build in dist/
```

## What's in the first playable (v0.1)

### Game modes
| Mode | What it is |
|---|---|
| 🎓 **Apprentice Mode** | Training Academy: 7 lessons (water supply, drainage, venting, tools, fittings, service calls, safety) each with a quiz that pays XP. |
| 🚨 **Service Call Mode** | 10 fully-scripted jobs (5 unlocked at start, 5 gated by rank): brief → load-out → timed diagnosis checklist → repair workspace → customer result → inspection report where required. |
| 🏗️ **Build Mode** | Rough-in a starter house — supply sources, drain slope, fittings, traps, vents, shutoffs, cleanout, T&P — then call for inspection. The validator flags hot/cold cross connections, missing vents, wrong fittings, bad slope, dead ends, and more. |
| 💼 **Business Mode** | Buy tools, restock parts, upgrade the van, hire an apprentice, set pricing tiers, read customer reviews, watch reputation and the ledger. |

### The first five service calls
1. **Running Toilet** — bad flapper
2. **Leaking Angle Stop** — failed shutoff valve
3. **Clogged Kitchen Sink** — grease clog in the trap
4. **Water Heater, No Hot Water** — burned-out element (city inspection required)
5. **Sewer Smell in Bathroom** — dry trap

Plus rank-gated calls: disposal jam, whole-house low pressure, tub/shower valve,
tankless error code, and a slab leak.

### Scoring (per job, out of 100)
- Correct diagnosis **25** · Correct tools **15** · Correct parts **15**
- Correct repair order **25** · Safety steps **10** · Time efficiency **10**

Deductions: forgot to shut off water **−25**, wrong part **−15**, wrong tool
**−10**, unsafe electrical step **−30**, did not test repair **−15**, created a
leak **−20**.

### Progression
Helper → Apprentice → Service Tech → Lead Tech → Licensed Plumber → Contractor
→ Plumbing Company Owner. Ranks unlock tools, harder jobs, van upgrades,
staff, tankless work, leak detection, and sewer camera equipment.

### Screens
Home · Career Dashboard · Job Board · Service Call (brief/load-out) ·
Diagnosis Checklist · Repair Workspace · Customer Result · Inspection Report ·
Tool Bag · Parts Inventory · Van Inventory · Business Dashboard ·
Training Academy · Build Mode · Settings.

## Project layout

```
src/
  data/        jobs, tools, parts, ranks, lessons, business, build-mode rules
  game/        scoring engine (rubric, mistakes, inspection)
  state/       GameContext (reducer + localStorage), NavContext (screen router)
  components/  UI kit (cards, buttons, bars, stars) + persistent HUD
  screens/     one file per screen; service-call sub-screens in screens/servicecall/
```

## Long-term roadmap
- 3D pipe layout builder & drag-and-drop fittings
- Camera inspection + leak-detection audio mini-games
- Tankless diagnostic mode, water filtration sales mode
- Multiplayer apprentice training
- Real plumbing code quiz & Palm Beach County inspection mode
- Customer negotiation/sales system
- AI-generated service calls
