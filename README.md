# leet-info-graph-gpt-5.2

> This project is being developed by an autonomous coding agent.

## Overview

Product Requirements Document: Research Infograph Assistant

1. Purpose

Build a full-stack web app with Gmail OAuth login that lets users ask for web research, 
generates an infographic, and provides...

## Features

*Features will be documented here as they are implemented.*


- Backend API scaffold (FastAPI) with SQLite storage and session CRUD endpoints.
- Dev-only login endpoint to simulate OAuth during local development.
- Minimal React SPA scaffold with prompt input, history filtering, and session detail pane (messages, sources, infographic preview + exports) (uses API cookies).

- Web search pipeline endpoint (MVP): `POST /api/search/sessions/{session_id}?query=...` attaches top results as Sources and updates session status.
- Basic rate limiting + in-memory TTL cache for search results (process-local, replaceable with Redis later).

- Natural-language prompt input validation (backend + UI): prompts must be non-empty, >= 3 chars, <= 4000 chars; UI disables send for short prompts and supports Ctrl/Cmd+Enter.


- **Infographic generation (MVP)**: `POST /api/sessions/{id}/infographic` generates and stores a simple, deterministic SVG infographic for a session, returned as a `data:image/svg+xml` URL with `layout_meta` (title, bullets, and source provenance).

- **Google OAuth callback (backend)**: `GET /api/auth/google/callback?code=...` exchanges the authorization code for Google OIDC userinfo, upserts a local User, and sets a signed `session` cookie.
  - Config via env vars: `INFOGRAPH_GOOGLE_CLIENT_ID`, `INFOGRAPH_GOOGLE_CLIENT_SECRET`, `INFOGRAPH_GOOGLE_REDIRECT_URI`, `INFOGRAPH_COOKIE_SECURE`.
  - Note: `state`/CSRF validation is not yet implemented (planned hardening item).

- **History view with filters (topic, tag, date)**: In the UI, use the History panel filters to narrow sessions by:
  - Topic (substring match on prompt)
  - Tag (MVP: looks for `#tag` in the prompt)
  - From/To date (local day boundaries)


### Export research sessions (F7)

Backend now supports exporting:

- **Session data (JSON)**: `GET /api/sessions/{session_id}/export.json`
- **Infographic (SVG)**: `GET /api/sessions/{session_id}/infographic.svg`

Both endpoints require authentication and return `Content-Disposition: attachment` for the SVG.

## Getting Started

### Prerequisites

*Prerequisites will be documented here.*

### Installation

```bash
# Installation instructions will be added
```

### Usage

```bash
# Usage examples will be added
```

## Development

See .leet/.todos.json for the current development status.

## Testing

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm test
```


## License

MIT
