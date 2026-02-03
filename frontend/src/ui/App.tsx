import React, { useEffect, useState } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

type Session = {
  id: number
  prompt: string
  status: string
  created_at: string
}

export function App() {
  const [sessions, setSessions] = useState<Session[] | null>(null)
  const [prompt, setPrompt] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function loadSessions() {
    setError(null)
    const res = await fetch(`${API_BASE}/api/sessions`, { credentials: 'include' })
    if (!res.ok) {
      setSessions(null)
      return
    }
    const data = (await res.json()) as Session[]
    setSessions(data)
  }

  async function createSession() {
    setError(null)
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
    setPrompt('')
    await loadSessions()
  }

  useEffect(() => {
    loadSessions().catch((e) => setError(String(e)))
  }, [])

  return (
    <div style={{ maxWidth: 900, margin: '0 auto', padding: 16, fontFamily: 'system-ui' }}>
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
          disabled={prompt.trim().length < 3}
          title="Send (Ctrl+Enter)"
        >
          Send
        </button>
      </section>

      {error && (
        <div role="alert" style={{ color: 'crimson', marginBottom: 16 }}>
          {error}
        </div>
      )}

      <section aria-label="History">
        <h2>History</h2>
        {sessions === null ? (
          <p>
            Not logged in. Use Dev login above.
          </p>
        ) : sessions.length === 0 ? (
          <p>No sessions yet.</p>
        ) : (
          <ul>
            {sessions.map((s) => (
              <li key={s.id}>
                <strong>#{s.id}</strong> {s.prompt} <em>({s.status})</em>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
