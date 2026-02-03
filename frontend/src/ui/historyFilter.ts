export type Session = {
  id: number
  prompt: string
  status: string
  created_at: string
}

export type HistoryFilters = {
  topic?: string
  tag?: string
  fromDate?: string // YYYY-MM-DD
  toDate?: string // YYYY-MM-DD
}

export function applyHistoryFilters(sessions: Session[], filters: HistoryFilters): Session[] {
  let result = sessions

  const topic = (filters.topic ?? '').trim().toLowerCase()
  if (topic) {
    result = result.filter((s) => s.prompt.toLowerCase().includes(topic))
  }

  const tag = (filters.tag ?? '').trim().toLowerCase().replace(/^#/, '')
  if (tag) {
    result = result.filter((s) => s.prompt.toLowerCase().includes(`#${tag}`))
  }

  if (filters.fromDate) {
    // Interpret YYYY-MM-DD as local date boundary.
    const from = new Date(`${filters.fromDate}T00:00:00`)
    if (!Number.isNaN(from.getTime())) {
      result = result.filter((s) => new Date(s.created_at) >= from)
    }
  }

  if (filters.toDate) {
    const to = new Date(`${filters.toDate}T00:00:00`)
    if (!Number.isNaN(to.getTime())) {
      const inclusive = new Date(to)
      inclusive.setHours(23, 59, 59, 999)
      result = result.filter((s) => new Date(s.created_at) <= inclusive)
    }
  }

  return result
}
