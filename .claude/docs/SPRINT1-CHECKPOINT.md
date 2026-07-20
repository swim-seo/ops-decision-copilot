# Sprint 1 체크포인트 — AI 오케스트레이션 층

> **작성**: 2026-07-20 · **목적**: 세션 재개용. 컴퓨터 재부팅 후 여기서부터 이어간다.
> **설계 기준**: [`target-platform-architecture.md`](target-platform-architecture.md) (Codex 리뷰 완료)

---

## 0. 지금 어디까지 왔나 (한눈에)

```
[Step 1] Function Calling 툴 4종     ✅ 완료 (modules/agent_tools.py)
[Step 2] LangGraph 에이전트          ✅ 완료·라이브 검증됨 (modules/agent.py)
[Step 3] 데모데이터 bootstrap        ⬜ 미착수  ← 다음 재개 지점
[Step 4] FastMCP 서버                ⬜ 미착수
[wiring] 에이전트를 chat 라우터에 연결 ⬜ 미착수 (현재 agent는 standalone만 검증)
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

## 3. 다음 재개 지점 (Step 3부터)

### Step 3 — 데모데이터 bootstrap (Codex 조건)
- **왜**: in-memory KG(`upload.py` `_graphs`)가 재시작 시 소실 → LangGraph 데모가 빈 그래프로 깨짐.
- **할 일**: 서버 시작(또는 최초 요청) 시 고정 데모 도메인의 문서/CSV를 자동 재적재하고 KG를 다시 빌드하는 bootstrap 루틴.
- 참고: `upload.py`의 `_get_or_create_kg()`, `build_community_summaries()`(현재 미호출 — Step에서 함께 연결 검토).

### Step 4 — FastMCP 서버
- `TOOL_SCHEMAS`/`run_tool`을 재사용해 `mcp_server.py`(FastMCP)로 노출 → Cursor/Claude Desktop 데모.
- 같은 코어(agent_tools) 공유 = HTTP·MCP 두 진입점.

### wiring — 에이전트를 chat 라우터에 연결
- 현재 `backend/routers/chat.py`는 여전히 `chat_copilot.respond/respond_stream`(detect_route) 사용.
- 계획: `POST /chat/agent` 신규 엔드포인트로 `run_agent` 노출(기존 /message 유지 → 안전). tools_used를 응답에 포함해 "근거 배지" 데모.
- 스트리밍은 추후(현재 agent.invoke는 블로킹).

---

## 4. 로드맵 태스크 상태

| # | 태스크 | 상태 |
|---|--------|------|
| 1 | Codex 설계 리뷰 | ✅ 완료 |
| 2 | 스프린트1 AI 오케스트레이션 | 🔄 진행중 (Step 1·2 완료, Step 3·4·wiring 남음) |
| 3 | 스프린트2 영속성 + build_community_summaries | ⬜ |
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
4. 이 문서 읽고 **Step 3(bootstrap)**부터 진행.
