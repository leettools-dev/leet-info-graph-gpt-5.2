---
project_name: leet-info-graph-gpt-5.2
created_at: 2026-02-03T21:51:00.083690+00:00
status: in_progress
---

# Goal Description

Product Requirements Document: Research Infograph Assistant

1. Purpose

Build a full-stack web app with Gmail OAuth login that lets users ask for web research, 
generates an infographic, and provides a library to browse past infographics and related sources.

2. Scope

- Input: natural-language research prompt
- Output: generated infographic (image + metadata), supporting sources, and a saved “research session”
- Core: OAuth login, chat UI, web search + summarization + infographic generation, history browsing

3. Users

- Students and educators
- Product/market researchers
- Knowledge workers who need quick visual summaries

4. Requirements

4.1 Functional
- F1: Gmail OAuth login and account management
- F2: Chat UI to submit research prompts and follow-ups
- F3: Web search pipeline to collect sources; show source list
- F4: Generate infographic (title, key stats, bullets, charts, references)
- F5: Save each research session with prompt, sources, and infographic
- F6: History view with filters (topic, date, tags) and detail page
- F7: Export infographic (PNG/SVG) and session data (JSON)

4.2 Non-functional
- N1: Rate-limit external calls; cache source fetches
- N2: Secure OAuth and API secrets; no secrets in repo
- N3: Traceable provenance (source links per claim)
- N4: Responsive UI; core pages render under 2s on broadband
- N5: Accessibility: keyboard nav, ARIA labels, contrast checks

5. Architecture

- Frontend: SPA (chat, history, detail pages)
- Backend API: auth, session CRUD, job orchestration
- Search/ingest: web fetch + source parser + summarizer
- Infographic generator: template-based layout + chart rendering
- Storage: relational DB for users/sessions; object storage for images
- Queue/worker: async research + rendering jobs

6. Data Model

- User: id, email, name, created_at
- ResearchSession: id, user_id, prompt, status, created_at
- Source: id, session_id, title, url, snippet, fetched_at, confidence
- Infographic: id, session_id, image_url, layout_meta, created_at
- Message: id, session_id, role, content, created_at

7. Implementation Plan

- Phase 1: OAuth login, chat UI, basic backend CRUD, search + source list
- Phase 2: Infographic generation MVP (static template + charts), session save
- Phase 3: Advanced layouts, tagging, exports, improved source scoring

8. Risks

- Web content quality and reliability
- Rate limits or blocking on sources
- Hallucinated claims without solid sources
- Cost spikes from heavy rendering/search

9. Success Metrics

- Adoption: % of users who create >=2 sessions
- Quality: user rating >=4/5 on infographic usefulness
- Latency: end-to-end research + render < 90s (P50)
- Provenance: 90% of claims have at least one source link

10. Next Steps

- Confirm OAuth scope and UI flows
- Define infographic templates and chart types
- Implement search ingest and caching strategy

Appendix: sample user flow

1) Sign in with Google  
2) Ask: “Summarize current EV market trends”  
3) Review sources + infographic  
4) Browse past sessions in History


## Requirements

- [x] Purpose
- [ ] Scope
- [x] Input: natural-language research prompt
- [x] Output: generated infographic (image + metadata), supporting sources, and a saved “research session”
- [ ] Core: OAuth login, chat UI, web search + summarization + infographic generation, history browsing
- [ ] Users
- [ ] Students and educators
- [ ] Product/market researchers
- [ ] Knowledge workers who need quick visual summaries
- [ ] Requirements
- [ ] 1 Functional
- [ ] F1: Gmail OAuth login and account management
- [ ] F2: Chat UI to submit research prompts and follow-ups
- [x] F3: Web search pipeline to collect sources; show source list
- [ ] F4: Generate infographic (title, key stats, bullets, charts, references)
- [ ] F5: Save each research session with prompt, sources, and infographic
- [ ] F6: History view with filters (topic, date, tags) and detail page
- [ ] F7: Export infographic (PNG/SVG) and session data (JSON)
- [ ] 2 Non-functional
- [ ] N1: Rate-limit external calls; cache source fetches
- [ ] N2: Secure OAuth and API secrets; no secrets in repo
- [ ] N3: Traceable provenance (source links per claim)
- [ ] N4: Responsive UI; core pages render under 2s on broadband
- [ ] N5: Accessibility: keyboard nav, ARIA labels, contrast checks
- [ ] Architecture
- [ ] Frontend: SPA (chat, history, detail pages)
- [ ] Backend API: auth, session CRUD, job orchestration
- [ ] Search/ingest: web fetch + source parser + summarizer
- [ ] Infographic generator: template-based layout + chart rendering
- [ ] Storage: relational DB for users/sessions; object storage for images
- [ ] Queue/worker: async research + rendering jobs
- [ ] Data Model
- [ ] User: id, email, name, created_at
- [ ] ResearchSession: id, user_id, prompt, status, created_at
- [ ] Source: id, session_id, title, url, snippet, fetched_at, confidence
- [ ] Infographic: id, session_id, image_url, layout_meta, created_at
- [ ] Message: id, session_id, role, content, created_at
- [ ] Implementation Plan
- [ ] Phase 1: OAuth login, chat UI, basic backend CRUD, search + source list
- [ ] Phase 2: Infographic generation MVP (static template + charts), session save
- [ ] Phase 3: Advanced layouts, tagging, exports, improved source scoring
- [ ] Risks
- [ ] Web content quality and reliability
- [ ] Rate limits or blocking on sources
- [ ] Hallucinated claims without solid sources
- [ ] Cost spikes from heavy rendering/search
- [ ] Success Metrics
- [ ] Adoption: % of users who create >=2 sessions
- [ ] Quality: user rating >=4/5 on infographic usefulness
- [ ] Latency: end-to-end research + render < 90s (P50)
- [ ] Provenance: 90% of claims have at least one source link
- [ ] Next Steps
- [ ] Confirm OAuth scope and UI flows
- [ ] Define infographic templates and chart types
- [ ] Implement search ingest and caching strategy
- [ ] Sign in with Google
- [ ] Ask: “Summarize current EV market trends”
- [ ] Review sources + infographic
- [ ] Browse past sessions in History

## Acceptance Criteria

- [ ] All requirements implemented
- [ ] All features have unit tests
- [ ] README.md documents all features
- [ ] All tests pass
