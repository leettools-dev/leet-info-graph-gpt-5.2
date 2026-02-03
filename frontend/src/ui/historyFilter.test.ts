import { describe, expect, it } from 'vitest'
import { applyHistoryFilters, type Session } from './historyFilter'

function s(id: number, prompt: string, created_at: string): Session {
  return { id, prompt, created_at, status: 'created' }
}

describe('applyHistoryFilters', () => {
  const sessions = [
    s(1, 'Summarize EV market trends #ev #market', '2026-02-01T10:00:00Z'),
    s(2, 'AI regulation overview #policy', '2026-02-02T10:00:00Z'),
    s(3, 'Battery supply chain #ev', '2026-02-03T10:00:00Z')
  ]

  it('filters by topic substring', () => {
    expect(applyHistoryFilters(sessions, { topic: 'battery' }).map((x) => x.id)).toEqual([3])
  })

  it('filters by tag (accepts leading #)', () => {
    expect(applyHistoryFilters(sessions, { tag: '#ev' }).map((x) => x.id)).toEqual([1, 3])
  })

  it('filters by date range inclusive of toDate day', () => {
    const out = applyHistoryFilters(sessions, { fromDate: '2026-02-02', toDate: '2026-02-02' })
    expect(out.map((x) => x.id)).toEqual([2])
  })

  it('combines filters', () => {
    const out = applyHistoryFilters(sessions, { tag: 'ev', topic: 'supply' })
    expect(out.map((x) => x.id)).toEqual([3])
  })
})
