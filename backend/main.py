import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import domain, upload, briefing, chat, graph

app = FastAPI(title="Ops Copilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
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
