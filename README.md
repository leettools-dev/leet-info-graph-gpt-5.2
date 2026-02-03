# leet-info-graph-gpt-5.2

> This project is being developed by an autonomous coding agent.

## Overview

Product Requirements Document: Research Infograph Assistant

1. Purpose

Build a full-stack web app with Gmail OAuth login that lets users ask for web research, 
generates an infographic, and provides...

## Features

- **OAuth hardening (N2)**: Google OAuth now includes `state` generation and callback validation to protect against CSRF. The backend also requires `INFOGRAPH_SECRET_KEY` (no default secret in code) and supports loading configuration from a local `.env` file (ignored by git). See `backend/.env.example`.

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
