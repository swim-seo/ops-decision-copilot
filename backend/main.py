import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.observability import RequestIdMiddleware, setup_logging
from backend.routers import domain, upload, briefing, chat, graph, jobs

# 구조화 로깅 설정 — 라우터/모듈 import 전에 루트 로거를 잡아둔다.
setup_logging()

app = FastAPI(title="Ops Copilot API", version="1.0.0")

# 요청 ID 미들웨어 — 요청당 id 발급, 모든 로그에 태깅 + X-Request-ID 응답 헤더.
app.add_middleware(RequestIdMiddleware)

_ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://*.vercel.app",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(domain.router,   prefix="/api/domain",   tags=["domain"])
app.include_router(upload.router,   prefix="/api/upload",   tags=["upload"])
app.include_router(briefing.router, prefix="/api/briefing", tags=["briefing"])
app.include_router(chat.router,     prefix="/api/chat",     tags=["chat"])
app.include_router(graph.router,    prefix="/api/graph",    tags=["graph"])
app.include_router(jobs.router,     prefix="/api/jobs",     tags=["jobs"])


# ── embedded 잡 워커 (Sprint 4 ②) ────────────────────────────────────────────
# WORKER_EMBEDDED=1(기본) 이면 startup 시 백그라운드 스레드로 큐 폴러를 띄운다.
# 데모는 한 프로세스로 "그냥 돌게" — 멀티워커 배포에선 0으로 끄고 독립 worker.py 사용.
_WORKER_EMBEDDED = os.getenv("WORKER_EMBEDDED", "1").lower() in ("1", "true", "yes")


@app.on_event("startup")
def _start_worker():
    if _WORKER_EMBEDDED:
        from modules import worker
        worker.start_embedded_worker(
            interval=float(os.getenv("WORKER_POLL_INTERVAL", "2.0"))
        )


@app.on_event("shutdown")
def _stop_worker():
    if _WORKER_EMBEDDED:
        from modules import worker
        worker.stop_embedded_worker()


@app.get("/api/health")
def health():
    return {"status": "ok"}
