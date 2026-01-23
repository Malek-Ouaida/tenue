# Tenue — System Architecture

This document is the **authoritative architecture reference** for Tenue.
Once stabilized, architectural decisions should not be revisited lightly.

---

## Overview

Tenue is a social platform built with strict separation of concerns:

Clients (Web + Mobile) talk ONLY to the API.
The API owns all business logic and persistence.
Infrastructure services are internal only.

---

## System Diagram

Clients → API → (Postgres / Redis / MinIO)

---

## Monorepo Layout

tenue/
- apps/api   → FastAPI backend
- apps/web   → Next.js web client
- apps/app   → Expo mobile client
- infra      → Docker services
- ARCHITECTURE.md
- REQUIREMENTS.md
- AGENTS.md

---

## API (FastAPI)

Responsibilities:
- Authentication & authorization
- Business logic
- Validation
- Persistence
- Media upload orchestration
- Pagination semantics

Rules:
- Routers = HTTP only
- Services = logic only
- Models = persistence only
- No client-specific logic
- Cursor-based pagination everywhere

---

## Database (Postgres)

Source of truth for all persistent data.

Rules:
- Alembic migrations only
- UUID primary keys
- No runtime schema creation

---

## Cache (Redis)

Used only for ephemeral data:
- caching
- rate limits
- sessions

Rules:
- TTL everything
- Never assume Redis data exists

---

## Object Storage (MinIO / S3)

Used for:
- images
- media assets

Rules:
- API mediates uploads
- DB stores only keys/metadata
- Public read allowed in local dev

---

## Clients (Web + Mobile)

Rules:
- No business logic
- API is source of truth
- Shared contracts
- Environment-driven URLs

---

## Philosophy

- Local-first
- Production parity
- Explicit over clever
- Boring, proven tech
- Architecture > speed

---

Status:
Infrastructure locked.
Foundation complete.
Ready for feature development.
