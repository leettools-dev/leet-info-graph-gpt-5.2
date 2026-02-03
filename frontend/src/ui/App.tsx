import React, { useEffect, useMemo, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

type Session = {
  id: number
  prompt: string
  status: string
  created_at: string
}

type Source = {
  id: number
  title: string
  url: string
  snippet: string | null
  fetched_at: string
  confidence: number | null
}

type Message = {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

type Infographic = {
  id: number
  image_url: string
  layout_meta: any
  created_at: string
}

type SessionDetail = Session & {
  sources: Source[]
  messages: Message[]
  infographic: Infographic | null
}

function formatDate(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString()
}

export function App() {
  const [sessions, setSessions] = useState<Session[] | null>(null)
  const [selectedSession, setSelectedSession] = useState<SessionDetail | null>(null)
  const [prompt, setPrompt] = useState('')
  const [q, setQ] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const filteredSessions = useMemo(() => {
    if (!sessions) return sessions
    const qq = q.trim().toLowerCase()
    if (!qq) return sessions
    return sessions.filter((s) => s.prompt.toLowerCase().includes(qq))
  }, [sessions, q])

  async function loadSessions() {
    setError(null)
    const res = await fetch(`${API_BASE}/api/sessions`, { credentials: 'include' })
    if (!res.ok) {
      setSessions(null)
      setSelectedSession(null)
      return
    }
    const data = (await res.json()) as Session[]
    setSessions(data)
  }

  async function loadSessionDetail(sessionId: number) {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${sessionId}`, { credentials: 'include' })
      if (!res.ok) {
        setSelectedSession(null)
        setError(`Failed to load session (${res.status})`)
        return
      }
      const detail = (await res.json()) as SessionDetail
      setSelectedSession(detail)
    } finally {
      setLoading(false)
    }
  }

  async function createSession() {
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/sessions`, {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ prompt })
      })
      if (!res.ok) {
        let detail: string | null = null
        try {
          const data = (await res.json()) as any
          detail = typeof data?.detail === 'string' ? data.detail : null
        } catch {
          // ignore
        }
        setError(`Failed to create session (${res.status})${detail ? `: ${detail}` : ''}`)
        return
      }
      const created = (await res.json()) as Session
      setPrompt('')
      await loadSessions()
      await loadSessionDetail(created.id)
    } finally {
      setLoading(false)
    }
  }

  async function generateInfographic() {
    if (!selectedSession) return
    setError(null)
    setLoading(true)
    try {
      const res = await fetch(`${API_BASE}/api/sessions/${selectedSession.id}/infographic`, {
        method: 'POST',
        credentials: 'include'
      })
      if (!res.ok) {
        setError(`Failed to generate infographic (${res.status})`)
        return
      }
      await loadSessionDetail(selectedSession.id)
      await loadSessions()
    } finally {
      setLoading(false)
    }
  }

  function exportSessionJSON() {
    if (!selectedSession) return
    const blob = new Blob([JSON.stringify(selectedSession, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `session-${selectedSession.id}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  function exportInfographicSVG() {
    if (!selectedSession?.infographic?.image_url) return
    const imageUrl = selectedSession.infographic.image_url
    if (!imageUrl.startsWith('data:image/svg+xml')) {
      setError('Infographic export only supports SVG data URLs in MVP')
      return
    }
    const svgText = decodeURIComponent(imageUrl.split(',')[1] ?? '')
    const blob = new Blob([svgText], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `infographic-${selectedSession.id}.svg`
    a.click()
    URL.revokeObjectURL(url)
  }

  useEffect(() => {
    loadSessions().catch((e) => setError(String(e)))
  }, [])

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 16, fontFamily: 'system-ui' }}>
      <h1>Research Infograph Assistant</h1>

      <section aria-label="Authentication" style={{ marginBottom: 16 }}>
        <p>
          Dev login:{' '}
          <a href={`${API_BASE}/api/auth/dev/login?email=demo@example.com`}>Login as demo@example.com</a>
        </p>
      </section>

      <section aria-label="Chat input" style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          aria-label="Research prompt"
          style={{ flex: 1, padding: 8 }}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
              void createSession()
            }
          }}
          placeholder="Ask for research..."
        />
        <button
          aria-label="Submit prompt"
          onClick={() => void createSession()}
          disabled={loading || prompt.trim().length < 3}
          title="Send (Ctrl+Enter)"
        >
          {loading ? 'Working…' : 'Send'}
        </button>
      </section>

      {error && (
        <div role="alert" style={{ color: 'crimson', marginBottom: 16 }}>
          {error}
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <section aria-label="History">
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between' }}>
            <h2 style={{ margin: 0 }}>History</h2>
            <label style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <span>Filter</span>
              <input
                aria-label="Filter history"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="topic…"
              />
            </label>
          </div>

          {sessions === null ? (
            <p>Not logged in. Use Dev login above.</p>
          ) : filteredSessions && filteredSessions.length === 0 ? (
            <p>No sessions match your filter.</p>
          ) : (
            <ul aria-label="Session list">
              {(filteredSessions ?? []).map((s) => (
                <li key={s.id}>
                  <button
                    aria-label={`Open session ${s.id}`}
                    onClick={() => void loadSessionDetail(s.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    <strong>#{s.id}</strong> {s.prompt} <em>({s.status})</em>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-label="Session detail">
          <h2 style={{ marginTop: 0 }}>Detail</h2>
          {!selectedSession ? (
            <p>Select a session to view messages, sources, and infographic.</p>
          ) : (
            <div>
              <div style={{ display: 'flex', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                <button aria-label="Export session JSON" onClick={exportSessionJSON}>
                  Export JSON
                </button>
                <button
                  aria-label="Export infographic SVG"
                  onClick={exportInfographicSVG}
                  disabled={!selectedSession.infographic}
                >
                  Export SVG
                </button>
                <button aria-label="Generate infographic" onClick={() => void generateInfographic()}>
                  Generate infographic
                </button>
              </div>

              <div aria-label="Session metadata" style={{ marginBottom: 12 }}>
                <div>
                  <strong>Prompt:</strong> {selectedSession.prompt}
                </div>
                <div>
                  <strong>Created:</strong> {formatDate(selectedSession.created_at)}
                </div>
                <div>
                  <strong>Status:</strong> {selectedSession.status}
                </div>
              </div>

              <div aria-label="Messages" style={{ marginBottom: 12 }}>
                <h3>Messages</h3>
                <ul>
                  {selectedSession.messages.map((m) => (
                    <li key={m.id}>
                      <strong>{m.role}:</strong> {m.content}
                    </li>
                  ))}
                </ul>
              </div>

              <div aria-label="Sources" style={{ marginBottom: 12 }}>
                <h3>Sources</h3>
                {selectedSession.sources.length === 0 ? (
                  <p>No sources yet.</p>
                ) : (
                  <ul>
                    {selectedSession.sources.map((s) => (
                      <li key={s.id}>
                        <a href={s.url} target="_blank" rel="noreferrer">
                          {s.title || s.url}
                        </a>
                        {s.confidence !== null ? ` (confidence ${s.confidence})` : ''}
                        {s.snippet ? <div style={{ color: '#374151' }}>{s.snippet}</div> : null}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              <div aria-label="Infographic">
                <h3>Infographic</h3>
                {!selectedSession.infographic ? (
                  <p>No infographic generated yet.</p>
                ) : (
                  <div>
                    <img
                      alt="Generated infographic"
                      src={selectedSession.infographic.image_url}
                      style={{ maxWidth: '100%', border: '1px solid #e5e7eb' }}
                    />
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
