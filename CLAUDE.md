# CLAUDE.md

## Running the App

```bash
# Frontend (Next.js)
cd frontend && pnpm dev

# Backend (FastAPI)
python -m uvicorn backend.main:app --port 8000
```

Set `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` in `.env`.

## Architecture

**Frontend**: Next.js 15 (App Router) + Tailwind CSS — `frontend/`
**Backend**: FastAPI — `backend/`
**Storage**: Supabase pgvector (RAG), NetworkX + pyvis (Knowledge Graph)
**AI**: Claude API (claude-sonnet-4-6)

## Backend Routes

- `POST /api/domain/setup` — 도메인 설정
- `POST /api/upload/files` — 파일 업로드 + 인덱싱
- `POST /api/upload/sample` — 샘플 데이터 로드
- `GET  /api/upload/samples` — 사용 가능한 샘플 목록
- `POST /api/briefing/generate` — AI 브리핑 생성
- `POST /api/chat/message` — 스트리밍 채팅
- `GET  /api/graph/html` — 지식 그래프 HTML

## Module Overview

- `modules/rag_engine.py` — Supabase pgvector 기반 RAG
- `modules/knowledge_graph.py` — NetworkX KG 구축 + pyvis 시각화
- `modules/claude_client.py` — Claude API 래퍼 (retry, stream)
- `modules/document_parser.py` — PDF/DOCX/CSV/TXT 파싱
- `modules/chat_copilot.py` — 채팅 라우팅 및 응답
- `domains/` — 도메인 프리셋 (beauty, supply_chain, energy, ...)
- `prompts/` — Claude 프롬프트 텍스트
