# PRAHARI — Scalability Issues & Mitigation Roadmap

## Current Architecture Snapshot

| Component | Technology | Bottleneck Class |
|-----------|-----------|-----------------|
| Backend | FastAPI (single process, Uvicorn) | CPU / IO bound |
| AI Inference | Gemini API (synchronous per-bidder) | External API quota |
| Database | PostgreSQL (single node) | Read/Write contention |
| File Storage | Cloudinary CDN | Upload bandwidth |
| Auth | JWT (8-hour tokens, no refresh) | Stateless — no revocation |
| Rate Limiting | slowapi in-process | Single-node only |

---

## Issue 1 — Synchronous Gemini Calls Block the Event Loop

**Location:** `backend/gemini_client.py`, `backend/app.py` evaluate endpoints  
**Impact:** Evaluating 10 bidders × 15 criteria = 150 sequential Gemini calls. At ~3 s/call → 7+ minutes blocking all other requests.

**Current behaviour:** `evaluate_all_bidders` calls `evaluate_bidder` in a `for` loop synchronously. Each call blocks the FastAPI worker.

**Mitigation (short-term):** Wrap Gemini calls in `asyncio.to_thread()` — already done for DB calls, apply the same pattern to Gemini calls.

**Mitigation (long-term):** Move heavy evaluation to a background task queue (Celery + Redis or FastAPI BackgroundTasks). Return a `task_id` immediately; frontend polls `GET /api/tasks/{task_id}/status`.

---

## Issue 2 — No Horizontal Scaling for the Backend

**Location:** `docker-compose.yml`, `Dockerfile`  
**Impact:** A single Uvicorn worker process handles all HTTP traffic. Under concurrent admin sessions (e.g. 5 officers reviewing simultaneously), requests queue behind running evaluations.

**Mitigation (short-term):** Run multiple Uvicorn workers: `uvicorn backend.app:app --workers 4`.

**Mitigation (long-term):** Deploy behind a load balancer (nginx, Traefik) with 2–4 replicas. The current `in-memory` Gemini chat sessions (`qa_sessions` dict in `app.py`) must be moved to Redis before horizontal scaling is possible — otherwise Q&A chat history is lost on pod routing changes.

---

## Issue 3 — In-Memory QA Chat Sessions

**Location:** `backend/app.py`, `qa_sessions` dict  
**Impact:** Each Q&A session is stored as a Python dict in the process heap. Any restart, crash, or second worker instance clears all sessions. Scaling to 2+ workers causes session-affinity bugs.

**Mitigation:** Serialise Gemini `ChatSession` history to Redis (or Postgres JSONB). Key: `qa:{project_id}`. TTL: 1 hour.

---

## Issue 4 — No JWT Refresh / Token Revocation

**Location:** `backend/app.py` (`/api/admin/login`), `frontend/src/contexts/RoleContext.tsx`  
**Impact:** Issued 8-hour JWT tokens cannot be invalidated before expiry. A compromised token is valid until it expires. There is no refresh flow — after 8 hours the officer must log in again.

**Mitigation (short-term):** Add a `POST /api/admin/logout` endpoint that writes the `jti` claim to a Postgres deny-list table; validate against it on each request.

**Mitigation (long-term):** Implement refresh tokens (short-lived access token + long-lived refresh token stored httpOnly cookie). Use `python-jose` for RS256 signing with key rotation.

---

## Issue 5 — PostgreSQL Single Node, No Connection Pooling

**Location:** `backend/db_config.py`, `backend/db.py`  
**Impact:** All DB calls use a single `psycopg2` connection (or a tiny pool). Under 50+ concurrent requests the Postgres `max_connections` limit (default 100) is hit quickly. Long-running evaluation transactions lock rows.

**Mitigation (short-term):** Add `pgbouncer` as a connection pooler sidecar in `docker-compose.yml` (transaction mode, pool size 20–50).

**Mitigation (long-term):** Migrate to `asyncpg` + SQLAlchemy async engine. Add a read replica for audit trail and report queries.

---

## Issue 6 — No Pagination on List Endpoints

**Location:** `GET /api/tenders/{id}/verdicts`, `GET /api/tenders/{id}/audit-trail`, `GET /dprs`  
**Impact:** A tender with 50 bidders × 20 criteria returns 1,000 verdict rows in a single response. The audit trail can grow to tens of thousands of rows.

**Mitigation:** Add `?page=1&per_page=50` query parameters. Return `{ items: [...], total: N, page: 1, pages: 20 }`. Frontend switches to paginated tables.

---

## Issue 7 — Large PDF Upload Size Limit Not Enforced

**Location:** `backend/app.py` upload endpoints  
**Impact:** No `MAX_UPLOAD_SIZE` check. A 500 MB PDF will exhaust server memory before Cloudinary receives it, potentially crashing the process.

**Mitigation:** Add a FastAPI dependency that checks `Content-Length` header before reading the body. Enforce 50 MB max for bidder documents, 20 MB for tenders.

```python
async def limit_upload_size(request: Request, max_mb: int = 50):
    if int(request.headers.get("content-length", 0)) > max_mb * 1024 * 1024:
        raise HTTPException(413, "File too large")
```

---

## Issue 8 — Rate Limiter is In-Process (Single Node Only)

**Location:** `backend/app.py`, `slowapi`  
**Impact:** `slowapi` stores rate limit counters in process memory. With 2+ Uvicorn workers or container replicas, each worker has its own independent counter — a client can make `N × rate_limit` requests by hitting different workers.

**Mitigation:** Configure `slowapi` with a Redis backend:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address
limiter = Limiter(key_func=get_remote_address, storage_uri="redis://redis:6379")
```
Add Redis service to `docker-compose.yml`.

---

## Issue 9 — No Background Job Visibility

**Location:** Entire backend  
**Impact:** Long-running operations (evaluate-all, collusion detection, criteria extraction) have no progress reporting. The frontend shows a spinner with no ETA. If the operation fails after 90 s the client receives a generic 500.

**Mitigation:** Return a `job_id` immediately. Persist job state to Postgres (`jobs` table: `id, type, status, progress_pct, result_json, error, created_at`). Expose `GET /api/jobs/{job_id}`. Frontend polls every 3 s and shows a progress bar.

---

## Issue 10 — Differential Privacy Epsilon Budget Not Tracked

**Location:** `backend/privacy.py`  
**Impact:** Each analytics query consumes privacy budget (epsilon). There is no per-project epsilon budget counter. Repeated queries can exhaust the budget, making outputs less private over time.

**Mitigation:** Track cumulative epsilon per `(project_id, query_type)` in Postgres. Reject queries where `cumulative_epsilon > EPSILON_BUDGET` (e.g. 10.0).

---

## Priority Matrix

| # | Issue | Severity | Effort | Priority |
|---|-------|----------|--------|----------|
| 1 | Sync Gemini blocks event loop | High | Medium | **P0** |
| 3 | In-memory QA sessions | High | Low | **P0** |
| 5 | No connection pooling | High | Low | **P1** |
| 6 | No pagination | Medium | Low | **P1** |
| 2 | No horizontal scaling | Medium | High | **P2** |
| 4 | No JWT revocation | Medium | Medium | **P2** |
| 8 | In-process rate limiting | Medium | Low | **P2** |
| 7 | Upload size not enforced | Low | Low | **P3** |
| 9 | No job visibility | Low | High | **P3** |
| 10 | DP epsilon budget | Low | Medium | **P3** |
