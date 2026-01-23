# Tenue — Agent Instructions

This file defines how assistants must reason about this project.

---

## Global Rules

- Never change architecture casually
- Never introduce new infra without justification
- Prefer explicit, boring solutions
- Avoid premature abstraction
- Respect boundaries between layers

---

## API Rules

- FastAPI only
- Pydantic v2
- SQLAlchemy 2.x
- Cursor pagination everywhere
- No leaking DB models to clients

---

## Client Rules

- No business logic
- API-first
- Environment-driven config
- Same behavior across web & mobile

---

## Infra Rules

- Docker Compose is source of truth
- Local parity with prod assumptions
- Redis is disposable
- S3-compatible storage only

---

If unsure, re-read:
ARCHITECTURE.md → REQUIREMENTS.md → this file
