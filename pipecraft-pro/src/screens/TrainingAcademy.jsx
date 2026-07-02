import { useState } from 'react'
import { useGame } from '../state/GameContext.jsx'
import { LESSONS } from '../data/lessons.js'
import { Card, SectionTitle, Badge, Button, ProgressBar } from '../components/ui.jsx'

// Apprentice Mode: lessons + quizzes. Passing a quiz (all correct) awards XP once.
export default function TrainingAcademy() {
  const { state, dispatch } = useGame()
  const [openLesson, setOpenLesson] = useState(null)
  const [answers, setAnswers] = useState({})
  const [graded, setGraded] = useState(false)

  const done = state.lessonsDone.length

  if (openLesson) {
    const lesson = LESSONS.find(l => l.id === openLesson)
    const complete = state.lessonsDone.includes(lesson.id)
    const allAnswered = lesson.quiz.every((_, i) => answers[i] != null)
    const allCorrect = lesson.quiz.every((q, i) => answers[i] === q.answer)

    const grade = () => {
      setGraded(true)
      if (allCorrect && !complete) {
        dispatch({ type: 'COMPLETE_LESSON', id: lesson.id, xp: lesson.xp })
      }
    }

    return (
      <div className="animate-pop">
        <Button variant="ghost" size="sm" className="mb-4" onClick={() => { setOpenLesson(null); setAnswers({}); setGraded(false) }}>
          ← Back to Academy
        </Button>
        <SectionTitle sub={complete ? '✅ Lesson complete — review any time.' : `Pass the quiz to earn ${lesson.xp} XP.`}>
          {lesson.icon} {lesson.title}
        </SectionTitle>

        {lesson.sections.map((s, i) => (
          <Card key={i} className="mb-3 p-5">
            <h3 className="mb-1.5 font-bold text-pipe-300">{s.heading}</h3>
            <p className="text-sm leading-relaxed text-slate-300">{s.body}</p>
          </Card>
        ))}

        <Card className="mt-5 p-5">
          <h3 className="mb-4 font-bold text-slate-100">📝 Knowledge Check</h3>
          {lesson.quiz.map((q, qi) => (
            <div key={qi} className="mb-5">
              <p className="mb-2 text-sm font-semibold text-slate-200">{qi + 1}. {q.q}</p>
              <div className="grid gap-1.5 sm:grid-cols-2">
                {q.options.map((opt, oi) => {
                  const picked = answers[qi] === oi
                  let tone = picked ? 'border-pipe-500 bg-pipe-500/15 text-pipe-200' : 'border-ink-600/60 text-slate-300 hover:border-slate-500'
                  if (graded && picked) tone = oi === q.answer ? 'border-emerald-500 bg-emerald-500/15 text-emerald-200' : 'border-red-500 bg-red-500/15 text-red-200'
                  if (graded && !picked && oi === q.answer) tone = 'border-emerald-500/50 text-emerald-300'
                  return (
                    <button key={oi} onClick={() => { setAnswers({ ...answers, [qi]: oi }); setGraded(false) }}
                      className={`rounded-xl border p-2.5 text-left text-sm transition ${tone}`}>
                      {opt}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}
          <Button variant="accent" disabled={!allAnswered} onClick={grade}>Grade my answers</Button>
          {graded && (
            <p className={`mt-3 text-sm font-semibold ${allCorrect ? 'text-emerald-400' : 'text-red-400'}`}>
              {allCorrect
                ? complete ? '✅ Perfect score!' : `✅ Perfect score! +${lesson.xp} XP earned.`
                : '❌ Not quite — fix the red answers and grade again.'}
            </p>
          )}
        </Card>
      </div>
    )
  }

  return (
    <div className="animate-pop">
      <SectionTitle sub="Apprentice Mode — the fundamentals every plumber runs on. Each lesson pays XP.">🎓 Training Academy</SectionTitle>

      <Card className="mb-5 p-4">
        <div className="mb-1.5 flex justify-between text-sm">
          <span className="font-semibold text-slate-200">Curriculum progress</span>
          <span className="text-slate-400">{done} / {LESSONS.length} lessons</span>
        </div>
        <ProgressBar value={done} max={LESSONS.length} color="bg-gradient-to-r from-pipe-500 to-flame-500" />
      </Card>

      <div className="grid gap-3 sm:grid-cols-2">
        {LESSONS.map(l => {
          const complete = state.lessonsDone.includes(l.id)
          return (
            <Card key={l.id} className="flex flex-col p-5" onClick={() => setOpenLesson(l.id)}>
              <div className="flex items-start justify-between">
                <div className="text-3xl">{l.icon}</div>
                {complete ? <Badge tone="green">✓ Complete</Badge> : <Badge tone="orange">+{l.xp} XP</Badge>}
              </div>
              <h3 className="mt-2 font-bold text-slate-100">{l.title}</h3>
              <p className="mt-1 text-xs text-slate-500">{l.sections.length} sections · {l.quiz.length}-question quiz</p>
            </Card>
          )
        })}
      </div>
    </div>
  )
}
