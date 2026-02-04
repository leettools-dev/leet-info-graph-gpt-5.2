# leet-info-graph-gpt-5.2

> This project is being developed by an autonomous coding agent.

## Overview

Product Requirements Document: Research Infograph Assistant

1. Purpose

Build a full-stack web app with Gmail OAuth login that lets users ask for web research, 
generates an infographic, and provides...

## Features


### Latency instrumentation (MVP)
The research worker now returns step-level timing metadata to support latency SLO tracking.

- Job status `result` includes `timing_ms` with: `total`, `search`, `ingest`, `render`, `store`.

This enables measuring end-to-end latency (P50) from the backend without external APM.

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
