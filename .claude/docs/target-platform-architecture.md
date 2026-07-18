# Ops Decision Copilot — 목표 플랫폼 아키텍처 설계

> **문서 목적**: 기능 위주로 만들어진 현재 앱에 "플랫폼 단"을 설계한다.
> **작성일**: 2026-07-18 · **상태**: 초안 (Codex 리뷰 예정)
> **관련**: 현재 코드 분석은 [`research/current-platform-analysis.md`](research/current-platform-analysis.md)

---

## 0. 이 문서를 읽는 법 (설계 사고법)

플랫폼 설계 = **"요청 하나가 들어와 나갈 때까지 거치는 정거장(request spine)을 설계하는 일"**.
모든 요청이 공통으로 거치는 관심사(cross-cutting concern)를 한 번씩 정의한다.

```
요청 → ① 인증(누구?) → ② 테넌시(누구 데이터?) → ③ 기능 로직 → ④ 영속성(어디 저장?)
      → ⑤ 비동기(오래 걸리면 미룸) → ⑥ 관측(뭐가 있었나 기록) → 응답
```

현재 앱은 **③만 있고 ①②④⑤⑥이 비어있다.** 이 문서는 그 빈칸을 채우는 설계다.

---

## 1. 현재 → 목표 갭 요약

| 정거장 | 현재 (파일:라인) | 문제 | 목표 |
|--------|------------------|------|------|
| ① 인증 | 없음 (`main.py:17-29` CORS만) | 신원 개념 0 | Supabase Auth (JWT) |
| ② 테넌시 | 클라 `collection_name` (`domain.py:13`) | 위조 가능·격리 아님 | 서버 도출 `org_id`/`user_id` + **부서별 가중치 RAG** |
| ③ 기능 | ✅ 완성 | — | 유지 |
| ④ 영속성 | KG in-memory `_graphs` (`upload.py:15`) | 재시작 시 소실·확장 불가 | KG를 Supabase에 직렬화 |
| ⑤ 비동기 | 없음 (요청 내 동기) | 큰 업로드 타임아웃 | 잡 큐 + 워커 |
| ⑥ 관측 | 로깅 설정 없음 (`upload.py:139` `except:pass`) | 문제 파악 불가 | 구조화 로깅 + 요청ID + 에러추적 |

**발견된 즉시 수정 대상 (분석 결과):**
- 🔴 `build_community_summaries()` (`community_summarizer.py:30`)가 **호출되지 않음** → GraphRAG 커뮤니티 요약이 생성·저장 안 됨 (읽기만 함)
- 🔴 RLS 정책 전부 `USING (true)` (`vector_migration.sql:32`) + 백엔드가 service key 사용 → **RLS 무력화**
- 🔴 in-memory KG로 인해 다중 워커/인스턴스 시 빈 그래프 반환

---

## 2. 목표 아키텍처 — 3층 구조

```
┌────────────────────────────────────────────────────────────┐
│  ② AI 오케스트레이션 층   ← 채용공고 핵심, 구현 1순위        │
│    • Agent (LangGraph)     : detect_route() → 상태그래프 재구성 │
│    • Function Calling      : RAG·데이터분석·KG조회 = 툴 스키마  │
│    • MCP Server (FastMCP)  : 위 툴을 표준 프로토콜로 노출       │
├────────────────────────────────────────────────────────────┤
│  ① 인프라 플랫폼 층                                           │
│    인증(Supabase Auth) · 테넌시(부서 가중치 RAG) · 영속성      │
│    · 비동기(큐+워커) · 관측(로깅·요청ID·에러추적)             │
├────────────────────────────────────────────────────────────┤
│  ③ 기능 층 (이미 완성) : GraphRAG Q&A · 데이터분석 · 브리핑    │
└────────────────────────────────────────────────────────────┘
```

**설계 원칙**: ②는 ③ 위에 얹혀 인증 없이도 데모 가능(포폴 우선). ①의 내부 순서(인증→영속성→비동기→관측)는 의존성 때문에 지켜야 함.

---

## 3. AI 오케스트레이션 층 (구현 1순위)

### 3.1 Function Calling — 기능을 "툴"로 정의

현재 `chat_copilot.detect_route()`의 if-else 규칙 라우팅을, LLM이 스스로 툴을 고르는 방식으로 전환. 각 기능을 툴 스키마로 정의한다.

| 툴 이름 | 역할 | 기존 모듈 |
|---------|------|-----------|
| `search_documents(query)` | 문서 청크 검색 | `rag_engine.py` |
| `search_graph(query)` | GraphRAG 커뮤니티+2hop 검색 | `community_summarizer.py` |
| `analyze_data(question)` | CSV/DB 분석 (차트·랭킹·리스크) | `data_analyst.py` |
| `get_briefing()` | 일일 브리핑 4카드 | `briefing` 라우터 |

```python
# 예시 툴 스키마 (Anthropic tool-use 형식)
{
  "name": "search_graph",
  "description": "관계 기반 질문(원인/영향/연결)에 GraphRAG로 답하기 위해 사용",
  "input_schema": {
    "type": "object",
    "properties": {"query": {"type": "string"}},
    "required": ["query"],
  },
}
```

### 3.2 Agent — LangGraph 상태 그래프

단순 라우팅 대신, **계획 → 툴 실행 → 결과 평가 → (필요시 추가 툴) → 종합**의 루프.

```
        ┌──────────┐
  질문 →│  plan    │ (어떤 툴이 필요한가?)
        └────┬─────┘
             ↓
        ┌──────────┐   결과 부족
        │  act     │←──────────┐  (툴 호출: search_graph 등)
        └────┬─────┘           │
             ↓                 │
        ┌──────────┐  더 필요? ─┘
        │ reflect  │
        └────┬─────┘  충분함
             ↓
        ┌──────────┐
        │synthesize│ → 최종 답변 (근거 배지 포함)
        └──────────┘
```

- **State**: `{question, tenant_ctx, tool_results[], plan, done}`
- **왜 LangGraph?**: 조건부 루프·상태 관리를 선언적으로 표현 → 공고의 "Agentic Workflow" 요구 정면 충족. (대안: 직접 while 루프 — 원리는 같으나 프레임워크 경험이 자격요건)

### 3.3 MCP Server — FastMCP로 툴 노출

3.1의 툴들을 MCP 서버로 감싸면 Claude Desktop·Cursor가 ops 데이터를 직접 조회 가능.

```python
# mcp_server.py (FastMCP)
from fastmcp import FastMCP
mcp = FastMCP("ops-decision-copilot")

@mcp.tool()
def search_graph(query: str, department: str | None = None) -> str:
    """부서 렌즈로 GraphRAG 검색."""
    ...
```

- **왜 별도 서버?**: 기능 로직(modules/)을 재사용하되, HTTP API와 MCP 두 진입점이 같은 코어를 공유 → 결합도 낮춤.
- **공고 매핑**: 제목의 "MCP 기반 서비스 개발" + 자격요건 "FastMCP" 정면 충족.

---

## 4. 인프라 플랫폼 층

### 4.1 인증 — Supabase Auth

- JWT 기반. `backend/main.py`에 미들웨어/`Depends(get_current_user)` 추가.
- 클라가 보내던 `collection_name`을 **토큰에서 서버가 도출**하는 `org_id`/`user_id`로 대체.
- **왜 기성품(Supabase Auth)?**: 인증 직접 구현은 보안 리스크·시간 낭비. 포폴은 "올바른 선택"을 보여주는 게 점수.

### 4.2 테넌시 — 부서별 가중치 RAG (핵심 차별화)

**두 층위 분리:**
- **하드 격리 (조직 간)**: `org_id`로 RLS 강제. A사는 B사 데이터 절대 못 봄.
- **소프트 테넌시 (부서 간)**: **하나의 공유 그래프**에, 부서마다 검색 가중치 프로파일.

```sql
-- 부서별 검색 정책
create table retrieval_profiles (
  org_id uuid, department text,
  community_weight float default 1.0,      -- 커뮤니티 요약 비중
  node_type_boost jsonb default '{}',      -- 예: {"paper":1.5,"sales":0.8}
  primary key (org_id, department)
);
```

검색 시 `final_score = base_similarity × node_type_boost[type] × community_weight`.
- 연구부: `{paper:1.5, experiment:1.3}` / 영업부: `{sales:1.5, customer:1.4}`
- **왜 강력한 소재?**: 공고 1순위 "RAG 최적화"를 구조적으로 증명. "같은 지식그래프, 부서별 렌즈."

### 4.3 영속성 — KG를 DB로

- `_graphs` in-memory dict → KG를 노드/엣지 테이블로 직렬화, 요청 시 로드(캐시).
- **동시에 🔴버그 수정**: `build_community_summaries()`를 업로드 파이프라인에 실제 연결 → "빌드 단계"와 "검색 단계"의 진실 일치.

### 4.4 비동기 — 잡 큐 + 워커

- 업로드/KG빌드를 요청에서 분리: `POST /upload` → job 생성 → 즉시 job_id 반환 → 워커가 백그라운드 처리 → 클라 폴링/SSE.
- **왜?**: 큰 문서 타임아웃 해결 + 수평 확장 가능. (기술: Supabase 큐 테이블 또는 경량 큐)

### 4.5 관측 — 최소 3종

1. **구조화 로깅**: `logging.config` 설정 (지금은 설정이 없어 로그가 버려짐)
2. **요청 ID**: 미들웨어에서 request_id 발급 → 전 로그에 태깅
3. **에러 추적**: `except: pass` 제거 → 로깅 + (선택) Sentry

---

## 5. 기술 선택 & 근거

| 영역 | 선택 | 근거 | 대안 |
|------|------|------|------|
| Agent | LangGraph | 상태그래프 선언적, 공고 자격요건 | 직접 루프, LlamaIndex |
| Tool schema | PydanticAI or Anthropic tool-use | 타입 안전, 공고 자격요건 | 수동 dict |
| MCP | FastMCP | 공고 명시, 파이썬 네이티브 | 저수준 MCP SDK |
| 인증 | Supabase Auth | 기존 Supabase 스택 재사용 | Clerk, Auth0 |
| 비동기 | Supabase 큐 테이블 | 인프라 추가 없음 | Celery+Redis |
| 관측 | stdlib logging + Sentry | 경량 | OpenTelemetry |

---

## 6. 구현 로드맵 (AI 오케스트레이션 우선)

```
[스프린트 1] AI 오케스트레이션 층 ← 공고 정조준, 데모 가능
  1. 기능 4종을 Function Calling 툴로 래핑
  2. LangGraph 에이전트로 라우팅 재구성
  3. FastMCP 서버로 툴 노출 → Cursor에서 데모
  ▶ 산출: "MCP·Agent 동작" 데모 영상/GIF = 포폴 킬러 콘텐츠

[스프린트 2] 영속성 + 버그 수정
  4. KG를 DB로 직렬화
  5. build_community_summaries() 파이프 연결 (🔴 수정)

[스프린트 3] 인증 + 테넌시
  6. Supabase Auth
  7. RLS를 org_id 기반으로 재작성 (service key → 사용자 키)
  8. 부서별 가중치 RAG (retrieval_profiles)

[스프린트 4] 비동기 + 관측
  9. 업로드/KG빌드 잡 큐
  10. 로깅·요청ID·에러추적
```

---

## 7. 미해결 질문 (Codex 리뷰 대상)

- [ ] LangGraph vs 직접 구현 — 포폴에서 프레임워크 사용이 +인가, 직접 구현이 원리 증명에 +인가?
- [ ] KG 영속성 모델: 노드/엣지 정규화 테이블 vs JSON 통째 저장 — 조회 패턴 대비 트레이드오프?
- [ ] 부서 가중치를 검색 시점 계산 vs 사전계산 인덱스 — 데이터 규모별 선택?
- [ ] 비동기 큐: Supabase 큐 테이블로 충분한가, 별도 브로커가 필요한가?

---

## Changelog
| 날짜 | 변경 |
|------|------|
| 2026-07-18 | 초안 작성 (현재 코드 분석 기반 3층 아키텍처 설계) |
