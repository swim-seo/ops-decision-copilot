import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.observability import RequestIdMiddleware, setup_logging
from backend.routers import domain, upload, briefing, chat, graph

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

@app.get("/api/health")
def health():
    return {"status": "ok"}
