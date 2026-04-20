# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the App

```bash
# Backend (FastAPI) — project root
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
# API docs: http://localhost:8000/docs

# Frontend (Next.js) — separate terminal
cd frontend
pnpm install
pnpm dev
# http://localhost:3000
```

Set `ANTHROPIC_API_KEY`, `SUPABASE_URL`, `SUPABASE_KEY` in `.env` at project root.

## Running Tests

```bash
# 단위 테스트 (CSV → KG 엣지 생성 검증)
python tests/test_csv_kg.py

# 평가 전체 실행
python eval/run_all.py

# 개별 평가
python eval/test_domain.py
python eval/test_fk.py
python eval/test_llm.py
python eval/test_rag.py
```

## Architecture

**3-layer 구조**: Next.js 15 (frontend) ↔ FastAPI (backend) ↔ modules/ (business logic)

`modules/`는 FastAPI·Next.js 의존성이 없어 독립적으로 테스트 가능.

### Frontend (`frontend/`)

Next.js 15 App Router, pnpm, Tailwind CSS 4.

라우트 그룹:
- `(app)/app/` — 실제 앱: 3단계 플로우(도메인 → 업로드 → 결과), `page.tsx`가 `step` state로 흐름 제어
- `(default)/` — 랜딩 페이지 (features, guide, knowledge-graph, domains 소개)
- `(auth)/` — 로그인·회원가입·비밀번호 재설정

앱 핵심 컴포넌트 (`frontend/app/(app)/app/components/`):

| 컴포넌트 | 역할 |
|---------|------|
| `DomainSelector` | 도메인 선택·설정 → `POST /api/domain/setup` |
| `FileUpload` | 파일 업로드·샘플 로드 → `POST /api/upload/files`, `/sample` |
| `BriefingCards` | 4개 AI 브리핑 카드 → `POST /api/briefing/generate` |
| `GraphViewer` | KG HTML iframe → `GET /api/graph/html` |
| `ChatWidget` | 우측 하단 FAB 채팅, SSE 스트리밍 → `POST /api/chat/message` |

Backend URL: `process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"` (모든 컴포넌트 공통)

### Backend (`backend/`)

FastAPI, CORS 허용: `localhost:3000` + `*.vercel.app`

라우터별 핵심 동작:

| 라우터 | 엔드포인트 | 동작 |
|--------|-----------|------|
| `domain.py` | `POST /api/domain/setup` | `DomainAdapter.analyze_domain()` or preset lookup → collection_name, domain_context 반환 |
| `upload.py` | `POST /api/upload/files` | 파일 파싱 → RAG 청킹 → Claude KG 추출 (ThreadPoolExecutor) |
| `upload.py` | `POST /api/upload/sample` | `data/{domain}/` CSV 로드 → 동일 파이프라인 |
| `upload.py` | `GET /api/upload/samples` | 6개 도메인 샘플 목록 반환 |
| `briefing.py` | `POST /api/briefing/generate` | RAG 검색 × 4 카드 → Claude 생성 |
| `chat.py` | `POST /api/chat/message` | `chat_copilot.respond_stream()` → SSE `data: chunk\n\n` … `data: [DONE]\n\n` |
| `graph.py` | `GET /api/graph/html` | KG pyvis HTML 반환 |

KG 인스턴스는 `upload.py`의 `_graphs: dict[str, KnowledgeGraph]` 딕셔너리에 collection_name 키로 메모리 보관. `chat.py`는 `_get_or_create_kg()`로 같은 인스턴스 공유.

샘플 데이터 경로: `data/{domain}/` (beauty, supply_chain, energy, manufacturing, logistics, finance)

### Modules (`modules/`)

- `claude_client.py` — `generate()`, `generate_with_system()`, `stream()`. 429/529 → 최대 3회 exponential backoff. `TOKENS` dict로 용도별 max_tokens 관리.
- `rag_engine.py` — Supabase pgvector 기반. `add_document()` 전 `delete_document()`로 중복 방지. 임베딩 싱글턴(paraphrase-multilingual-MiniLM-L12-v2, 384차원).
- `knowledge_graph.py` — NetworkX + pyvis. 4가지 build path: `build_from_claude_json()` / `build_from_schema_json()` / `build_from_csv_schema()` (2-pass FK) / `build_from_python_ast()`. `render_html()`은 `net.generate_html()` 사용 (save_graph() 아님), UTF-8 인코딩 명시.
- `chat_copilot.py` — `detect_route()` → `"data"` | `"doc"` | `"combined"` 분류. `respond_stream()`은 doc 라우트만 진짜 스트리밍, data/combined는 전체 텍스트 한 번에 yield.
- `document_parser.py` — PDF/DOCX/TXT/MD `parse_file()`, CSV `extract_csv_schema()` (FK 후보 자동 감지), Python `extract_python_graph_data()` (AST).
- `community_summarizer.py` — GraphRAG 핵심: Louvain 커뮤니티 탐지 → Claude 요약 → Supabase `community_summaries` 저장·검색.

### Domain System (`domains/`)

7개 프리셋 (beauty, supply_chain, energy, manufacturing, logistics, finance, generic). 각 파일 `PRESET` dict: `entity_types`, `terminology`, `document_patterns`, `analysis_focus`, `theme_color`, `app_icon`.

`domains/__init__.py`의 `get_preset(name)` — 키워드 매칭으로 유사 도메인 자동 선택. 미매칭 시 `DomainAdapter.analyze_domain()`이 Claude 1회 호출로 동적 생성.

### Prompt System (`prompts/`)

`system_base.txt`가 공통 역할 정의 + `{domain_context}` 주입. `prompt_loader.load_prompt("name", key=value)` 호출 시 `{system_base}`가 자동으로 삽입됨.

## Key Config (`config.py`)

- API 키 우선순위: `st.secrets` → `.env` → 환경변수
- `CHUNK_SIZE=800`, `CHUNK_OVERLAP=150`
- `GRAPH_OUTPUT_PATH="./data/graph.html"` — `render_html()` 호출 시 덮어씀
- 디렉토리 (`./data/`, `./data/uploads/`) import 시 자동 생성

## Deployment

- **Frontend** → Vercel (`frontend/` 루트 디렉토리 지정, `NEXT_PUBLIC_API_URL` 환경변수 설정)
- **Backend** → Render/Railway (`backend/` 루트, start: `uvicorn main:app --host 0.0.0.0 --port $PORT`)
- Supabase SQL 순서: `scripts/vector_migration.sql` → `scripts/graphrag_migration.sql` → `create_all_tables.sql`
