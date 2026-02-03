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
- Minimal React SPA scaffold with prompt input and history list (uses API cookies).

- Web search pipeline endpoint (MVP): `POST /api/search/sessions/{session_id}?query=...` attaches top results as Sources and updates session status.
- Basic rate limiting + in-memory TTL cache for search results (process-local, replaceable with Redis later).
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

```bash
# Test instructions will be added
```

## License

MIT
