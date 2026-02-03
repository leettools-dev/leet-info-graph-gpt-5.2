# leet-info-graph-gpt-5.2

> This project is being developed by an autonomous coding agent.

## Overview

Product Requirements Document: Research Infograph Assistant

1. Purpose

Build a full-stack web app with Gmail OAuth login that lets users ask for web research, 
generates an infographic, and provides...

## Features

- **OAuth hardening (N2)**: Google OAuth now includes `state` generation and callback validation to protect against CSRF. The backend also requires `INFOGRAPH_SECRET_KEY` (no default secret in code) and supports loading configuration from a local `.env` file (ignored by git). See `backend/.env.example`.


- **Source ingest pipeline (fetch + parse + summarize)**: `POST /api/ingest/sessions/{session_id}` fetches saved source URLs, extracts title/text, generates a deterministic summary, and fills `Source.snippet` + updates session status to `ingested`.

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

### CI/Local test commands

Backend:
```bash
cd backend
python3 -m pytest
```

Frontend:
```bash
cd frontend
npm test
```

Note: in some environments `pytest`/`python` may not be on PATH; prefer `python3 -m pytest`.
## License

MIT
