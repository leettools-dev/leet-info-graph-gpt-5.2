# leet-info-graph-gpt-5.2

> This project is being developed by an autonomous coding agent.

## Overview

Product Requirements Document: Research Infograph Assistant

1. Purpose

Build a full-stack web app with Gmail OAuth login that lets users ask for web research, 
generates an infographic, and provides...

## Features

- **Upstream rate-limit resilience (MVP):** external web search and source fetch calls use an in-process token-bucket limiter. When the limiter is saturated, calls *wait for an available token* instead of failing fast, reducing user-visible errors during temporary throttling.


### Cost/latency guardrails for research jobs
- Caps web-search results and number of sources ingested per session.
- Truncates fetched source text before summarization to avoid runaway processing.

Config (env):
- `INFOGRAPH_SEARCH_MAX_RESULTS` (default: 5)
- `INFOGRAPH_INGEST_MAX_SOURCES_PER_SESSION` (default: 5)
- `INFOGRAPH_INGEST_MAX_FAILURES_PER_SESSION` (default: 10)
- `INFOGRAPH_INGEST_MAX_SOURCE_CHARS_FOR_SUMMARIZATION` (default: 20000)


### Adoption metrics (MVP)

Backend exposes a simple per-user adoption metric: whether the signed-in user has created **>=2 research sessions** within a given time window.

**Endpoint**
- `GET /api/metrics/adoption?days=30` (requires authentication cookie)

**Response**
Returns a small JSON payload including:
- `sessions_in_window`
- `eligible_users` (0/1)
- `users_with_2plus_sessions` (0/1)
- `adoption_rate` (0.0 or 1.0 in MVP)

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

Backend (note: in some environments `pytest` isn’t on PATH):
```bash
cd backend
python3 -m pytest
```

If you want to run the lightweight schema/unit tests in `backend/tests` explicitly:
```bash
cd backend
python3 -m pytest backend/tests
```

## License

MIT
