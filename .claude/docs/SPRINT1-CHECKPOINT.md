# Sprint 1 체크포인트 — AI 오케스트레이션 층

> **작성**: 2026-07-20 · **목적**: 세션 재개용. 컴퓨터 재부팅 후 여기서부터 이어간다.
> **설계 기준**: [`target-platform-architecture.md`](target-platform-architecture.md) (Codex 리뷰 완료)

---

## 0. 지금 어디까지 왔나 (한눈에)

```
[Step 1] Function Calling 툴 4종     ✅ 완료 (modules/agent_tools.py)
[Step 2] LangGraph 에이전트          ✅ 완료·라이브 검증됨 (modules/agent.py)
[Step 3] 데모데이터 bootstrap        ✅ 완료·검증됨 (modules/kg_store.py)
[Step 4] FastMCP 서버                ✅ 완료·부팅 검증됨 (mcp_server.py)  ← 방금 완료
[wiring] 에이전트를 chat 라우터에 연결 ✅ 완료 (POST /api/chat/agent)      ← 방금 완료

=> Sprint 1 (AI 오케스트레이션 층) 전체 완료. 다음은 Sprint 2 (영속성).
```

**진행 방식**: 설명→구현→diff리뷰 루프 (사용자가 학습하며 진행, 코드는 Claude가 작성).

---

## 1. 환경 (⚠️ 중요 — 재부팅 후 반드시 확인)

- **기존 32비트 Python(`C:\Python311_32`)로는 langgraph/fastmcp 설치 불가** (cryptography·ormsgpack 휠 없음).
- **해결**: 프로젝트 전용 uv venv 생성 = **64비트 Python 3.12.13**.
  - 위치: `ops-decision-copilot/.venv/` (gitignore됨)
  - 실행 명령이 바뀜:
    ```bash
    # 기존: uvicorn backend.main:app --reload --port 8000
    # 지금: .venv/Scripts/python -m uvicorn backend.main:app --reload --port 8000
    # (또는 먼저:  .venv\Scripts\activate)
    ```
  - 테스트 시 콘솔 한글/이모지 깨지면: `PYTHONUTF8=1 PYTHONIOENCODING=utf-8` 앞에 붙일 것 (cp949 콘솔).
- **설치된 주요 버전**: langgraph 1.2.9 · fastmcp 3.4.4 · pandas 3.0.3 · anthropic 0.117.0.
  - pandas 3.0으로 올라갔으나 `analyze_data`(data_analyst) 라이브 테스트에서 정상 확인됨.
- **HuggingFace 임베딩**: 이 개발 샌드박스에선 `api-inference.huggingface.co` DNS 차단 →
  `search_documents`/`search_graph` 툴은 임베딩 실패(에러 격리로 루프는 안 죽음).
  실제 배포/네트워크 환경(HUGGINGFACE_API_KEY 있음)에선 정상. `analyze_data`는 로컬 CSV라 무관.

---

## 2. 완료된 코드 (커밋됨)

### `modules/agent_tools.py` (신규) — Function Calling 툴 4종
- `ToolContext` (dataclass): 요청별 의존성 주입(claude/rag/kg/domain_context/collection_name). 전역 상태 없음 → 멀티테넌시 대비.
- `TOOL_SCHEMAS`: Anthropic tool-use 형식 명세 4개.
- 실행함수(기존 모듈 래핑):
  - `search_documents` → `rag_engine.query()`
  - `search_graph` → `community_summarizer.retrieve_community_context` + `kg.multi_hop_query`
  - `analyze_data` → `data_chat_engine.analyze()` (차트는 개수만 표기)
  - `get_briefing` → RAG 4종 컨텍스트 + Claude 1회
- `run_tool()`: 이름 디스패치 + try/except 에러 격리(툴 실패가 에이전트 안 죽임).
- 원칙: modules/는 프레임워크 독립 → backend/ import 안 함.

### `modules/agent.py` (신규) — LangGraph ReAct 에이전트
- 그래프: `call_model`(plan/reflect) →[tool_use?]→ `run_tools`(act) → `call_model` → … → END(synthesize).
- `AgentState` (TypedDict): messages / ctx / iterations / tool_trace / final_text.
- `MAX_ITERATIONS=5`: 비용 가드레일(Codex 지적).
- `run_agent(question, ctx)` → `{text, tools_used, iterations}`. sanitize_input로 인젝션 방어 재사용.
- **라이브 검증**: "여름 잘팔리는 상품 top3+재고위험" → LLM이 analyze_data 자율 선택 → 실제 데이터 답변 생성 확인.

### `modules/claude_client.py` (수정)
- `create_message(messages, tools, system, max_tokens)` 추가: 툴 넘기고 원본 Message 객체 반환(재시도 포함). 에이전트 루프용.

### `backend/requirements.txt` (수정)
- `langgraph>=0.2.0`, `fastmcp>=2.0.0` 추가.

---

## 3. 다음 재개 지점 (Step 4부터)

### Step 3 — 데모데이터 bootstrap ✅ 완료 (2026-07-22)
- **구현**: `modules/kg_store.py` 신규.
  - `KnowledgeGraphStore` (ABC) — Sprint 2 Supabase 구현체 교체용 seam. `get()`/`save()`.
  - `InMemoryKnowledgeGraphStore` — 현재 구현. get() 최초 호출 시 데모 데이터로 결정적 재구축.
  - 재구축은 **결정적 경로만**: `SCHEMA_DEFINITION.json` + CSV 스키마(2-pass FK). **Claude(LLM) 호출 없음**. LOGIC_DOCUMENT.txt 등 LLM 추출 경로는 스킵.
  - **2-pass FK**: upload.py 는 `all_table_names` 를 안 넘겨 CSV-only 도메인(beauty)이 엣지 0개였음 → 부트스트랩은 전체 테이블명을 넘겨 관계선 복원. (beauty: 8노드 **8엣지** 확인)
  - 동시성: `threading.Lock` + double-checked locking (호출부가 sync/async 혼재라 asyncio.Lock 불가).
  - 프로덕션 안전: `OPS_DEMO_BOOTSTRAP` env 로 게이트, **기본 비활성**. `OPS_DEMO_SAMPLE`(기본 beauty), `OPS_DEMO_COLLECTION`(기본 domain_sample).
- **wiring**: `upload.py` `_graphs` dict 제거 → `_kg_store` 위임. `_get_or_create_kg()` 시그니처 유지(chat.py/graph.py 안 깨짐). 업로드 핸들러에 `_kg_store.save()` 추가(Sprint 2 seam).
- **검증**: 재시작 시나리오 end-to-end — 부트스트랩 ON 시 `_get_or_create_kg('domain_sample')` → 8노드/8엣지. OFF 시 0노드(프로덕션 안전). 에이전트 빌드 무결성 확인.
- **미해결(설계상 의도)**: 멀티 워커 불일치(워커별 `_graphs` 분리)는 부트스트랩으로 못 고침 → **Sprint 2 진짜 영속화(KG→Supabase JSON blob)**가 답. Codex도 이걸 최대 리스크로 지목.
- **참고**: `build_community_summaries()` 여전히 미호출 — Sprint 2에서 연결 검토.

### Step 4 — FastMCP 서버 ✅ 완료 (2026-07-23)
- **구현**: `mcp_server.py` 신규 (프로젝트 루트, backend/main.py 와 병렬 진입점).
  - `agent_tools.run_tool` 로 위임하는 4개 `@mcp.tool` (search_documents/search_graph/analyze_data/get_briefing).
    → 같은 코어 공유 = HTTP·MCP 두 진입점, 에러 격리 로직 단일화.
  - FastMCP **3.4.4** API 실측 확정: `@mcp.tool`(괄호 없이) 데코레이터 → docstring=설명·타입힌트=스키마 자동. `mcp.run(transport="http"|"stdio"|"sse"|"streamable-http")`.
  - `collection_name`/`domain_context` 를 툴 파라미터로 노출(MCP 클라이언트가 도메인 선택). 기본 stdio, `--http` 로 127.0.0.1:8001.
  - **별도 프로세스라 uvicorn 과 KG 공유 불가** → 자체 `_kg_store` 소유. 데모는 `OPS_DEMO_BOOTSTRAP=1` 로 결정적 재구축. (Sprint 2 Supabase 영속화되면 두 진입점이 같은 그래프 공유 가능.)
- **검증**: 4개 툴 등록·스키마 확인 + `--http` 부팅 성공(FastMCP 배너·리스닝). tools/list 400 은 세션 핸드셰이크 전이라 정상(크래시 아님).

### wiring — 에이전트를 chat 라우터에 연결 ✅ 완료 (2026-07-23)
- **구현**: `backend/routers/chat.py` 에 `POST /agent` 신규(`AgentRequest` → `run_agent`).
  - 기존 `/message`(chat_copilot.respond, detect_route)는 **그대로 유지** → 안전한 병행 진입점.
  - 응답에 `tools_used`/`iterations` 포함 → "어떤 근거로 답했나" 배지·관측용.
  - ToolContext 조립은 `/message` 와 동일 패턴(RAGEngine + `_get_or_create_kg` + ClaudeClient).
- **검증**: OpenAPI 스키마에 `/api/chat/agent [POST]` 등록 확인 + 앱 import 무결성.
- **미해결(추후)**: 스트리밍 없음(agent.invoke 블로킹). 프론트엔드 연결(현재 UI 는 /message 사용) 미착수 — Sprint 2/포폴 재작성 때 검토.

---

## 3.5 Sprint 2 — 영속성 + build_community_summaries ✅ 코드 완료 (2026-07-23)

**설계**: Codex 리뷰 재확인(3개 질문). Q2 KG=도메인별 JSON blob은 기존 확정.

- **KG 영속화** (`modules/kg_store.py`):
  - `_serialize_kg`/`_deserialize_kg` — networkx `node_link_data`/`node_link_graph(directed=True)`. 노드·엣지·속성·방향성 왕복 보존(실측).
  - `SupabaseKnowledgeGraphStore` — **read-through(캐시 없음)**. 캐시는 멀티워커 불일치를 재생성(Codex Q1). 전환 기준: 지연/비용 or 노드 수천개↑ → updated_at 버전체크+짧은 TTL.
  - `get_kg_store()` 팩토리 — **명시적 env `KG_STORE=supabase`**(auto-detect 아님, Codex Q2). 기본 in-memory.
  - **부트스트랩 save-back(필수)**: supabase 스토어에서 행 부재+`OPS_DEMO_BOOTSTRAP` 시 재구축 후 **DB 저장** → 워커별 재시딩 발산 차단(결정적이라 double-save도 수렴).
- **Supabase 헬퍼** (`modules/supabase_client.py`): `select_one`(단일행) + `upsert_rows`(dict 리스트 upsert) 추가.
- **커뮤니티 요약 배선** (`backend/routers/upload.py`): `_build_summaries_safe()` — save() 직후 **동기** 호출, 스토어에서 **재읽기** 후 `build_community_summaries`, try/except 격리(임베딩 불가 시 skip). `upload_files`·`load_sample` 양쪽. → 🔴 "build_community_summaries 미호출" 버그 해소.
- **마이그레이션**: `scripts/kg_persistence_migration.sql` 신규(`knowledge_graphs` 테이블, DROP 안 함=재실행 안전).

**검증**: 팩토리 선택·직렬화 왕복(beauty 8노드/8엣지, 속성보존)·앱 import·Supabase 스토어 우아한 실패(테이블 부재→빈 그래프, 크래시 없음) 모두 OK.

**⚠️ 남은 실행(사용자)**: Supabase SQL Editor 에서 `scripts/kg_persistence_migration.sql` 실행 → 그 후 `KG_STORE=supabase` 로 실제 DB 왕복 검증 가능(현재 테이블 PGRST205 미존재). DDL 은 REST 로 불가.

**미검증(테이블 생성 후 가능)**: 실제 save→get DB 왕복, 재시작 후 그래프 생존, 멀티워커 수렴.

## 3.6 Sprint 3 Step 1 — 부서별 가중치 RAG ✅ 코드 완료 (2026-07-23)

**설계**: Codex 리뷰 4개 질문. Q1 타입있는 신호만 가중(문서청크 미가중) / Q2 Python 재랭킹(over-fetch→재정렬) / Q3 가중RAG 먼저(인증 뒤) / Q4 `resolve_department` seam(파라미터→Step2 JWT). +Codex 리스크: 소스별 정규화(스케일 상이) → 후보 내 max 정규화 적용.

- **마이그레이션**: `scripts/retrieval_profiles_migration.sql` — `retrieval_profiles(org_id, department, community_weight, node_type_boost jsonb, PK(org_id,dept))` + 데모 시드(영업부: fact 1.6/master 0.9, 재고부: master 1.5/csv 1.2/fact 0.9). org_id=collection_name 임시.
- **`modules/retrieval_profiles.py`** 신규: `RetrievalProfile`(불변) · `get_profile(org_id,dept)`(없으면 DEFAULT=무가중) · `resolve_department()` seam · `rerank_communities()`(norm_sim×community_weight×mean(node_type_boost[type])) · `_community_type_boost`(kg에서 타입 조회).
- **`community_summarizer.py`**: `fetch_community_candidates`(원시 후보) + `format_community_rows` 분리, `retrieve_community_context`는 이 둘로 재구성(하위호환).
- **`agent_tools.py`**: `ToolContext.department` 추가. `_run_search_graph`가 프로파일 로드→후보 over-fetch→`rerank_communities`→포맷(무가중이면 유사도순 그대로).
- **`chat.py`**: `AgentRequest.department` + `resolve_department()`로 ToolContext 주입.

**검증(로직 수준)**: 앱 import · **부서 렌즈 top 뒤집힘**(영업부→fact커뮤니티 c0, 재고부→master커뮤니티 c1, 기본→유사도순) · seam sanitize · get_profile 테이블부재 시 DEFAULT 폴백. 전부 OK.

**⚠️ 검증 한계 — 합성 데이터였음 (사용자 지적, 2026-07-23)**: 위 "top 뒤집힘"은 **손으로 만든 합성 커뮤니티 후보**(유사도·node_list 직접 지정)로 rerank_communities 로직만 증명한 것. 실제 파이프라인(질문→임베딩→match_community_summaries RPC→실제 후보→가중)은 **미검증**. 이유: dev 샌드박스 임베딩 DNS 차단 + community_summaries/retrieval_profiles 테이블 부재.
→ **실데이터 검증 TODO** (임베딩 되는 환경 + 마이그레이션 후): ① 샘플 업로드로 community_summaries 실제 생성 → ② retrieval_profiles 시드 → ③ 같은 질문을 department=영업부/재고부로 /chat/agent 호출해 tools_used·근거 커뮤니티가 실제로 다르게 뽑히는지 확인. 노드 타입 분포가 시드 부스트와 맞물려 의미있는 차이를 내는지(데모 신뢰성)까지 점검.

**✅ 실데이터 검증 완료 (2026-07-23)**: 마이그레이션 4종(kg_persistence·retrieval_profiles·graphrag) 실행 + **임베딩 fastembed 전환** 후 실측:
- 실제 community_summaries 생성(c0=매출/반품, c1=공급망/제품) + 실제 질문 임베딩 + 실제 RPC + DB 프로파일 로드.
- **핵심 발견**: 초기 부스트(fact 1.6/master 0.9)는 커뮤니티 base 유사도 격차보다 약해 top 순위를 못 바꿈 → **강한 스프레드(2.5/0.5)로 시드 튜닝**. 결과: '애매한 질문'(실적+재고)에서 영업부→c0 재고부→c1 **뒤집힘**, '명확한 질문'에선 base 유사도가 정상 지배.
- **설계 통찰**: `community_weight`는 프로파일 내 모든 커뮤니티에 동일 곱 → 커뮤니티 간 순위 무영향(소스 병합용 스케일). 순위는 오직 node_type_boost 가 가른다.

**⚠️ 지연 TODO (사용자 요청 2026-07-23)**: **합성 데모 데이터(data/*/ CSV) 생성 품질·로직·아이디어 검토** — 데이터가 어떻게 만들어졌는지 흐름을 꼼꼼히 안 봤음. 플랫폼 개발 먼저 진행, 데이터 검토는 나중에.

**다음(Step 2/3)**: Supabase Auth(JWT→user_id/org_id) → org_id 기반 RLS 재작성. resolve_department 를 JWT 클레임 소스로 교체.

## 4. 로드맵 태스크 상태

| # | 태스크 | 상태 |
|---|--------|------|
| 1 | Codex 설계 리뷰 | ✅ 완료 |
| 2 | 스프린트1 AI 오케스트레이션 | ✅ 완료 (Step 1~4 + wiring 전부) |
| 3 | 스프린트2 영속성 + build_community_summaries | ✅ 코드완료 (⚠️ Supabase 마이그레이션 실행 대기) |
| 4 | 스프린트3 인증 + 부서 가중치 RAG | ⬜ |
| 5 | 스프린트4 비동기 큐 + 관측 | ⬜ |
| 6 | 포폴 재작성(구현 결과 반영) | ⬜ |

---

## 5. 재부팅 후 빠른 재개 체크리스트

1. `cd ops-decision-copilot`
2. venv 확인: `.venv/Scripts/python -c "import langgraph, fastmcp; print('ok')"`
   - 안 되면 재생성: `uv venv --python 3.12.13 .venv && uv pip install -r backend/requirements.txt`
3. 에이전트 스모크 테스트:
   ```bash
   PYTHONUTF8=1 .venv/Scripts/python -c "from modules.agent import build_agent; build_agent(); print('agent ok')"
   ```
4. Sprint 1 완료 — 다음은 **Sprint 2 (영속성: KG→Supabase JSON blob + build_community_summaries 연결)**.
   - 스모크: `PYTHONUTF8=1 .venv/Scripts/python -c "import mcp_server; from backend.main import app; print('ok')"`
   - MCP 데모: `OPS_DEMO_BOOTSTRAP=1 .venv/Scripts/python mcp_server.py --http`
   - 에이전트 HTTP: 서버 기동 후 `POST /api/chat/agent {"message": "..."}`
