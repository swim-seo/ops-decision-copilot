# Current Platform Architecture Analysis — ops-decision-copilot

**Date:** 2026-07-18
**Scope:** How the app currently handles concerns a "platform layer" would own.
**Stack:** Next.js 15 (`frontend/`) → FastAPI (`backend/`) → `modules/` (business logic at project root) → Claude API + Supabase pgvector + HuggingFace Inference API.

> Read the way to learn from this: the app is a **single-process, single-tenant, in-request monolith**. Almost every platform concern (identity, isolation, background work, observability, horizontal scale) is either absent or implicitly assumed away. The sections below cite the exact code that makes each assumption.

---

## 1. Request Lifecycle

FastAPI app is assembled in `backend/main.py:10-33`: 5 routers mounted under `/api/*`, one CORS middleware, one `/api/health` endpoint. No other middleware, no lifespan/startup hooks, no dependency injection.

### 1a. File upload — `POST /api/upload/files`

Handler: `backend/routers/upload.py:148-173` (`upload_files`, `async def`).

Flow:
1. Construct per-request objects: `RAGEngine(collection_name)` (upload.py:154), `_get_or_create_kg(collection_name)` (upload.py:155), `ClaudeClient()` (upload.py:156). All three are **created fresh on every request** — no pooling, no reuse (except the KG, see §2).
2. For each `UploadFile`: write bytes to a `tempfile.NamedTemporaryFile` on local disk (upload.py:161-163), call `await _process_file(...)` (upload.py:166), then `os.unlink` the temp file (upload.py:171).
3. `_process_file` (upload.py:91-145) does **heavy synchronous work inside the request**:
   - CSV: `pandas.read_csv`, `extract_csv_schema`, `kg.build_from_csv_schema` (upload.py:96-102).
   - PDF/DOCX/TXT/PY: text extraction, then a **blocking Claude API call** `claude.generate(prompt, max_tokens=1000)` for KG entity extraction (upload.py:136), wrapped in a bare `except Exception: pass` (upload.py:139-140).
   - `rag.add_document(text, filename)` (upload.py:144) → chunk → **batch embedding via remote HF API** → HTTP POST to Supabase (`rag_engine.py:49-89`).

Even though the handler is `async`, `_process_file` calls **synchronous, blocking** libraries (pandas, pypdf, the Anthropic SDK's sync client, `requests`). Nothing is offloaded to a thread pool, so a large upload **blocks the event loop** for the whole request. There is no timeout budget, no size cap, no progress/streaming — the client waits for the entire loop over all files to finish.

> **Notable gap:** `build_community_summaries()` (`modules/community_summarizer.py:30`) — the GraphRAG "community summary" tier — is **never called** anywhere in the codebase (grep confirms only its definition + docstring). So the `community_summaries` table is only ever *read* (`retrieve_community_context`, chat_copilot.py:186/231), never populated by the upload path. The advertised "3-tier RAG" top tier is effectively dead on the write side.

### 1b. Chat — `POST /api/chat/message`

Handler: `backend/routers/chat.py:19-40` (`chat_message`, note: **`def`, not `async def`** — FastAPI runs it in a threadpool worker).

Flow:
1. Fresh `RAGEngine`, `_get_or_create_kg`, `ClaudeClient` per request (chat.py:21-23).
2. If `stream=True` (default): returns `StreamingResponse` over a generator that yields SSE `data:` frames from `chat_copilot.respond_stream(...)` (chat.py:25-33).
3. `respond_stream` (chat_copilot.py:368-410) routes via `detect_route()` (keyword/regex classifier, chat_copilot.py:71-82):
   - `"doc"` → true token streaming from `claude.stream()` (chat_copilot.py:398, claude_client.py:84-99).
   - `"recommend"`, `"data"`, `"combined"` → computed **synchronously in full**, then yielded as a single chunk (chat_copilot.py:379-381, 403-406). Only `"doc"` actually streams.
4. `"combined"` fans out RAG/KG/CSV fetches across a `ThreadPoolExecutor(max_workers=3)` created **per request** (chat_copilot.py:311-314).

Long-running work in-request: every branch makes 1+ blocking Claude calls and (for doc/combined) a blocking HF embedding call + Supabase RPC. All inside the request lifecycle.

---

## 2. State & Persistence

### In-process (lost on restart)

| State | Location | Notes |
|-------|----------|-------|
| **Knowledge graphs** | `backend/routers/upload.py:15` → `_graphs: dict[str, KnowledgeGraph] = {}` | The single most important piece of volatile state. Keyed by `collection_name`. Accessor `_get_or_create_kg()` at `upload.py:65-68`. |
| Supabase connection flags | `modules/supabase_client.py:22-24` (`_url`, `_key`, `_connected`) | Module-level singleton, memoized by `_init()` (supabase_client.py:42-73). |
| Embedding LRU cache | `modules/embedding.py:35` (`@lru_cache(maxsize=256)` on `embed`) | Query-dedup only; per-process. |
| Anthropic client | `modules/claude_client.py:34` | Recreated per request (not a singleton), so no real caching benefit. |

The `_graphs` dict is **the** platform liability: the NetworkX `DiGraph` built during upload (nodes/edges/columns) lives only in the uploading process's heap. `chat.py` and `graph.py` both import `_get_or_create_kg` **from `upload.py`** (chat.py:7, graph.py:4) and rely on it already being populated.

**What is lost on restart:** every knowledge graph. After a restart, `_get_or_create_kg()` returns a fresh empty `KnowledgeGraph()`, so:
- `GET /api/graph/html` and `/api/graph/data` return "empty graph" (graph.py:11-13).
- Chat's multi-hop KG context (`_build_graphrag_context`, chat_copilot.py:169-209) silently returns `("", 0)` — the KG tier of RAG degrades to nothing with **no error and no rebuild**. Only pgvector document chunks survive.

### Persisted to Supabase (survives restart)

- `document_chunks` — RAG vectors (`rag_engine.py:26`, `_TABLE`); written in `add_document` (rag_engine.py:49-89), read via RPC `match_document_chunks` (rag_engine.py:96). Schema: `scripts/vector_migration.sql`.
- `community_summaries` — GraphRAG community tier (`community_summarizer.py:25`); read via RPC `match_community_summaries`. **Write path (`build_community_summaries`) is never invoked** — see §1a. Schema: `scripts/graphrag_migration.sql`.
- Domain fact/master tables (`mst_*`, `fact_*`, `data_dictionary`) — `scripts/create_tables.sql`; read by `data_analyst.py` via `supabase_client.query_table()`.

**Asymmetry to note:** the KG (in memory) and its derived vectors (in Supabase) can drift out of sync across restarts — chunks persist, the graph they were extracted from does not.

---

## 3. Identity & Isolation

**There is no authentication and no user concept anywhere.** No login, session, JWT, cookie, or `user_id` exists in `backend/` (the only grep hits for "token"/"Bearer" are `max_tokens` and the Supabase service-key header in `supabase_client.py:34-38`).

- No auth middleware or `Depends(...)` guard on any route (`main.py:17-29` adds only CORS). Every endpoint is fully public.
- CORS is configured with `allow_credentials=True` and origins from `ALLOWED_ORIGINS` env (default includes `https://*.vercel.app`) (`main.py:12-23`).

**How data is "separated" today — `collection_name`:**
- The frontend derives a `collection_name` from the domain name via `domain.py:13-16` (`_collection_name`: sanitize → `domain_<slug>`, truncated to 63 chars).
- That string is passed as a **client-supplied parameter** on every request (upload `Form`, chat/briefing/graph `collection_name` fields) and used as a filter column in Supabase queries (`rag_engine.py:34-41`) and as the `_graphs` dict key.
- This is **namespacing, not isolation**: any client can pass any `collection_name` and read/write another domain's chunks and KG. There is no ownership check, no tenant binding, nothing preventing enumeration.

**Supabase RLS:** enabled on every table but with a wide-open policy — `CREATE POLICY "Allow all" ... USING (true) WITH CHECK (true)` (`scripts/vector_migration.sql:32-33`, `graphrag_migration.sql:25-26`, and all `create_tables.sql` tables). Combined with the backend using the Supabase **service key** (`SUPABASE_KEY`, supabase_client.py:34-38), RLS provides **zero** effective access control today.

**Biggest gap:** no identity primitive at all. Per-tenant isolation would require (a) auth at the FastAPI edge, (b) deriving `collection_name`/tenant server-side from the authenticated principal rather than trusting the client, and (c) real RLS keyed on that principal.

---

## 4. Concurrency & Scaling

The app **assumes a single process**. It breaks behind a load balancer / with >1 replica or >1 Uvicorn worker:

1. **In-memory `_graphs` is not shared** (upload.py:15). Upload hits instance A → KG lives in A's heap. A later chat/graph request routed to instance B sees an **empty** KG. Same failure with `uvicorn --workers N` (each worker is a separate process). This is the headline scaling break.
2. **Event-loop blocking:** the `async def upload_files` handler runs blocking pandas/pypdf/Anthropic/`requests` calls inline (§1a), so a single big upload stalls all concurrent requests on that worker.
3. **Per-request thread pools:** `ThreadPoolExecutor(max_workers=3)` is created and torn down on every `"combined"` chat (chat_copilot.py:311) — unbounded thread churn under load; no global cap.
4. **Module-level Supabase singleton** (`supabase_client.py:22-24`) is per-process; fine functionally but means connection state isn't shared and re-inits per process.
5. **`embed` LRU cache** (embedding.py:35) is per-process, so cache hit rate drops with more replicas (minor).

**Net:** the current deployment is only correct as **one process, one worker**. Any horizontal or multi-worker scale silently corrupts KG-dependent features (graph views, GraphRAG multi-hop) with no error surfaced.

---

## 5. Config & Secrets

- `config.py` loads `.env` via `python-dotenv` at import (`config.py:5-6`, `override=True`) and exposes `_get_secret(key)` = thin `os.getenv(key, "")` wrapper (config.py:9-10).
- Secrets read: `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY`, `HF_API_TOKEN` (config.py:14-31). `CLAUDE_MODEL` defaults to `claude-sonnet-4-6` (config.py:15).
- `ClaudeClient` re-reads `ANTHROPIC_API_KEY` and raises if missing (claude_client.py:31-33). `supabase_client` re-reads creds lazily via `config._get_secret` (supabase_client.py:28-30).
- **Hardcoded assumptions / magic values:** local filesystem paths `./data/uploads`, `./data/graph.html` created at import (config.py:29,38,60-61) — assumes a writable local disk and a **single node** (graph HTML is written to one shared local path `GRAPH_OUTPUT_PATH`, knowledge_graph.py:250-257, which collides across concurrent renders and doesn't exist on other replicas). Tuning constants (`CHUNK_SIZE=800`, `SIMILARITY_THRESHOLD=0.25`, `TOP_K_RESULTS=5`) are module constants, not per-request/tenant configurable.
- No secret manager, no config validation (missing Supabase creds just silently flips to "not connected" mode, supabase_client.py:49-51), no environment separation (dev/stage/prod) beyond raw env vars.
- **Missing-secret behavior differs by dependency:** Anthropic key missing → hard `ValueError` at request time; Supabase creds missing → soft degrade (queries return `[]`/`None`); HF token missing → embedding calls will fail at the HF API. Inconsistent failure modes.

---

## 6. Observability

Essentially **none** at the platform level.

- No `logging.basicConfig`, no log formatter, no handlers configured anywhere. Modules call `logging.getLogger(__name__)` (e.g. rag_engine.py:24, supabase_client.py:19, claude_client.py:15, embedding.py:9, community_summarizer.py:23) but with **no root configuration**, so most `logger.info`/`logger.debug` output is dropped by default.
- No request IDs, no correlation IDs, no structured logging, no access logging beyond Uvicorn's default.
- No metrics (no Prometheus/OpenTelemetry), no tracing, no APM, no error tracker (no Sentry).
- **Error swallowing hides failures:** upload KG extraction is `except Exception: pass` (upload.py:139-140); per-file errors are captured into the response dict (upload.py:168-169) but not logged; Supabase helpers catch and `logger.debug` (which is invisible without config) then return `None`/`0`/`[]` (supabase_client.py:121-123, 138-139, 157-160, 177-178). Failures degrade silently.
- Only health signal is `GET /api/health` → `{"status":"ok"}` (main.py:31-33) — a liveness ping that checks nothing (not Supabase, not Anthropic, not KG state).

---

## 7. Background / Async Infrastructure

**None. Everything runs in-request.**

- No task queue (no Celery/RQ/Arq), no worker process, no cron/scheduler, no `BackgroundTasks`, no message broker.
- Document parsing, KG construction, Claude entity extraction, embedding, and vector upsert all execute **synchronously within the HTTP request** (§1a). A multi-file or large-PDF upload is a long, blocking request with no async job handle, no retry, no idempotency, and no way to poll status.
- Community-summary generation (the one operation clearly meant to be a post-upload batch job) is not wired in at all (§1a/§2), so there isn't even an in-request version of it running.

---

## 8. API Surface

All routes mounted in `backend/main.py:25-29`.

| Method & Path | Handler | Sync/Async | Purpose |
|---------------|---------|-----------|---------|
| `POST /api/domain/setup` | `domain.py:19-34` | sync | Name → preset (`collection_name`, theme, entity types, terminology, `domain_context`). Pure/stateless. |
| `POST /api/upload/files` | `upload.py:148-173` | async (blocking inside) | Multipart upload → parse → KG + RAG ingest. |
| `POST /api/upload/sample` | `upload.py:181-209` | async | Load a bundled sample dataset from `data/<domain>/` into a collection. |
| `GET /api/upload/samples` | `upload.py:212-222` | sync | List available sample datasets. |
| `POST /api/briefing/generate` | `briefing.py:45-75` | sync | 4 fixed cards (summary/risk/insight/action); each does a RAG `get_context` + Claude call. |
| `POST /api/chat/message` | `chat.py:19-40` | sync (returns `StreamingResponse` when `stream=True`) | Main chat; routes data/doc/combined/recommend. |
| `GET /api/graph/html` | `graph.py:9-21` | sync | Rendered pyvis HTML of the in-memory KG for a collection. |
| `GET /api/graph/data` | `graph.py:24-35` | sync | Raw nodes/edges JSON of the in-memory KG. |
| `GET /api/health` | `main.py:31-33` | sync | Static liveness `{"status":"ok"}`. |

Cross-router coupling worth noting: `chat.py:7` and `graph.py:4` both **import `_get_or_create_kg` from `upload.py`**, making `upload.py`'s module-level `_graphs` dict the de-facto shared KG store across the whole API.

---

## Summary Table — Concern → Current State → Gap

| Platform concern | Current state (file:line) | Biggest gap |
|------------------|---------------------------|-------------|
| **Request lifecycle** | Heavy sync work inline in requests; `upload_files` async but blocks event loop (upload.py:91-173); only `"doc"` chat truly streams (chat_copilot.py:398) | No async job model; large uploads block worker; no timeouts/size caps |
| **State & persistence** | KGs in-memory `_graphs` dict (`upload.py:15`), lost on restart; chunks + community summaries in Supabase (`rag_engine.py:26`, `community_summarizer.py:25`) | KG is volatile & unshared; `build_community_summaries` **never called** (dead write path) — KG/vector drift after restart |
| **Identity & isolation** | No auth at all; separation only by client-supplied `collection_name` (`domain.py:13-16`); RLS = "Allow all" (`vector_migration.sql:32-33`) + service key | No identity primitive; client can access any tenant's data; needs auth at FastAPI edge + server-derived tenant + real RLS |
| **Concurrency & scaling** | Single-process assumption; in-mem `_graphs` unshared (`upload.py:15`); per-request `ThreadPoolExecutor` (chat_copilot.py:311) | Any 2nd replica/worker → empty KG on the other instance; correct only at 1 process/1 worker |
| **Config & secrets** | `config.py` + `os.getenv` (`config.py:9-10`); local disk paths created at import (config.py:29,38,60-61) | No secret manager/validation/env separation; local-disk & single-node assumptions (shared `graph.html` path) |
| **Observability** | `getLogger` calls but **no logging config**; no metrics/tracing/error tracking; errors swallowed (upload.py:139) | No request IDs, no structured logs, no APM; health check verifies nothing |
| **Background/async** | None — everything in-request | No queue/worker/cron; no job handles, retries, or idempotency for ingestion |
| **API surface** | 9 endpoints across 5 routers (`main.py:25-29`) | KG-dependent endpoints (graph, GraphRAG chat) silently degrade when `_graphs` is empty |

---

## Where the two hinge points are

- **In-memory KG store:** `backend/routers/upload.py:15` — `_graphs: dict[str, KnowledgeGraph] = {}`; accessor `_get_or_create_kg()` at `upload.py:65-68`; imported into `chat.py:7` and `graph.py:4`. This is what must move to shared/persistent storage (e.g., serialize the graph to Supabase, or rebuild-on-read from chunks) before any multi-instance deploy.
- **Where auth would plug in:** `backend/main.py:17-29` — today only `CORSMiddleware` is added there. An auth layer (middleware or a shared `Depends(get_current_principal)` on every router) belongs at this edge; the authenticated principal should then drive `collection_name`/tenant selection **server-side** (replacing the client-supplied values in `upload.py:148-153`, `chat.py:12-16`, `briefing.py:40-42`, `graph.py:10/25`), and Supabase RLS (`scripts/*.sql`) must be rewritten from `USING (true)` to tenant-scoped policies with a non-service key.
