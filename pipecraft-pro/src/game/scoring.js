import { partById } from '../data/parts.js'

// Score a completed service call.
//
// play = {
//   selectedTools: string[], selectedParts: string[],
//   diagnosisId: string, performedSteps: string[],
//   timeUsedSec: number, timeLimitSec: number,
// }
//
// Rubric (out of 100):
//   Correct diagnosis 25 · Correct tools 15 · Correct parts 15
//   Correct repair order 25 · Safety steps 10 · Time efficiency 10
// Mistake deductions are listed per-item in the result breakdown.
export function scoreJob(job, play) {
  const breakdown = []
  const mistakes = []
  let score = 0

  // --- Diagnosis (25) ---
  const correctDx = job.diagnosisOptions.find(d => d.correct)
  const dxCorrect = play.diagnosisId === correctDx.id
  breakdown.push({ label: 'Correct diagnosis', earned: dxCorrect ? 25 : 0, max: 25 })
  score += dxCorrect ? 25 : 0

  // --- Tools (15, proportional to required tools brought) ---
  const reqTools = job.requiredTools
  const broughtRequired = reqTools.filter(t => play.selectedTools.includes(t))
  const toolPts = reqTools.length === 0 ? 15 : Math.round(15 * (broughtRequired.length / reqTools.length))
  breakdown.push({ label: 'Correct tools', earned: toolPts, max: 15 })
  score += toolPts
  const wrongTools = play.selectedTools.filter(t => !reqTools.includes(t))
  for (const t of wrongTools) mistakes.push({ label: `Wrong tool brought (${t.replace(/-/g, ' ')})`, points: -10 })

  // --- Parts (15) ---
  const reqParts = job.requiredParts
  const broughtParts = reqParts.filter(p => play.selectedParts.includes(p))
  const partPts = reqParts.length === 0
    ? (play.selectedParts.length === 0 ? 15 : 15)
    : Math.round(15 * (broughtParts.length / reqParts.length))
  breakdown.push({ label: 'Correct parts', earned: partPts, max: 15 })
  score += partPts
  const wrongParts = play.selectedParts.filter(p => !reqParts.includes(p))
  for (const p of wrongParts) mistakes.push({ label: `Wrong part used (${partById[p]?.name || p})`, points: -15 })

  // --- Repair order (25): longest common subsequence of the performed
  // correct-step sequence against the required order. ---
  const correctIds = job.repairSteps.map(s => s.id)
  const performedCorrect = play.performedSteps.filter(s => correctIds.includes(s))
  const lcsLen = lcs(performedCorrect, correctIds)
  const orderPts = Math.round(25 * (lcsLen / correctIds.length))
  breakdown.push({ label: 'Correct repair order', earned: orderPts, max: 25 })
  score += orderPts

  // --- Safety (10) + safety-rule violations ---
  let safetyOk = true
  for (const rule of job.safetyRules || []) {
    const guardIdx = play.performedSteps.indexOf(rule.stepId)
    for (const dep of rule.beforeSteps) {
      const depIdx = play.performedSteps.indexOf(dep)
      if (depIdx === -1) continue // the risky step never happened
      if (guardIdx === -1 || guardIdx > depIdx) {
        safetyOk = false
        mistakes.push({ label: rule.label, points: rule.penalty })
        break
      }
    }
  }
  breakdown.push({ label: 'Safety steps', earned: safetyOk ? 10 : 0, max: 10 })
  score += safetyOk ? 10 : 0

  // --- Time efficiency (10): full points if ≤60% of limit used ---
  const frac = play.timeLimitSec > 0 ? play.timeUsedSec / play.timeLimitSec : 1
  const timePts = frac <= 0.6 ? 10 : frac >= 1 ? 0 : Math.round(10 * (1 - (frac - 0.6) / 0.4))
  breakdown.push({ label: 'Time efficiency', earned: timePts, max: 10 })
  score += timePts

  // --- Did-not-test deduction ---
  const tested = (job.testStepIds || []).every(t => play.performedSteps.includes(t))
  if (!tested) mistakes.push({ label: 'Did not test the repair', points: -15 })

  // --- Distractor penalties (created leak, unsafe shortcut, …) ---
  for (const stepId of play.performedSteps) {
    const d = (job.distractors || []).find(x => x.id === stepId)
    if (d?.penalty) mistakes.push({ label: d.penalty.label, points: d.penalty.points })
  }

  const deductions = mistakes.reduce((s, m) => s + m.points, 0)
  const finalScore = Math.max(0, Math.min(100, score + deductions))
  return { score: finalScore, base: score, breakdown, mistakes, dxCorrect, tested }
}

function lcs(a, b) {
  const dp = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0))
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      dp[i][j] = a[i - 1] === b[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1])
  return dp[a.length][b.length]
}

export function satisfactionStars(score, pricingBonus = 0) {
  const adj = score + pricingBonus
  if (adj >= 88) return 5
  if (adj >= 72) return 4
  if (adj >= 55) return 3
  if (adj >= 38) return 2
  return 1
}

// Inspection report for jobs that require one.
// - requiresStep:  the step must have been performed.
// - requiresOrder: [first, second] — both performed, first before second.
// - requiresPart:  the repair step that installs this part must have been
//   performed with the part on hand (not merely loaded in the bag).
export function runInspection(job, play) {
  if (!job.inspectionRequired) return null
  const checks = (job.inspectionChecks || []).map(c => {
    let passed = true
    if (c.requiresStep) passed = play.performedSteps.includes(c.requiresStep)
    if (c.requiresOrder) {
      const [first, second] = c.requiresOrder
      const i = play.performedSteps.indexOf(first)
      const j = play.performedSteps.indexOf(second)
      passed = i !== -1 && j !== -1 && i < j
    }
    if (c.requiresPart) {
      const installStep = job.repairSteps.find(s => s.usesPart === c.requiresPart)
      passed = !!installStep
        && play.performedSteps.includes(installStep.id)
        && play.selectedParts.includes(c.requiresPart)
    }
    return { ...c, passed }
  })
  return { checks, passed: checks.every(c => c.passed) }
}
