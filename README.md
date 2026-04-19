# 사내 문서·데이터 기반 AI 의사결정 지원 시스템(OPS Decision Copilot)

> **도메인 적응형 AI 운영 코파일럿 플랫폼**
> 문서, 데이터, GraphRAG 지식그래프를 결합하여 운영 의사결정을 지원합니다.

[![Next.js](https://img.shields.io/badge/Frontend-Next.js%2015-black.svg)](https://nextjs.org)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Claude API](https://img.shields.io/badge/LLM-Claude%20Sonnet-orange.svg)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 개요

사내 문서·데이터 기반 AI 의사결정 지원 시스템(OPS Decision Copilot)은 **어떤 비즈니스 도메인에도 적응하는** AI 코파일럿 플랫폼입니다.
문서, CSV, 회의록을 업로드하면 다음 기능을 즉시 사용할 수 있습니다.

- **GraphRAG 기반 문서 Q&A** — 커뮤니티 요약 검색 + 멀티홉 관계 탐색
- **지식그래프 자동 구성** (Claude + NetworkX + pyvis)
- **CSV 데이터 자동 분석** (pandas + plotly) 및 구조화 답변
- **의사결정 지원**: 데이터 추천 → 확인 질문 → 다음 액션
- **일일 브리핑** 4개 카드 자동 생성
- **스트리밍 응답**으로 실시간 채팅 경험

7개 도메인 프리셋 내장 (뷰티, 공급망, 에너지, 제조, 물류, 금융, 범용).
도메인명을 직접 입력하면 Claude가 즉시 적응합니다.

---

## 아키텍처

```
+---------------------------+        +-----------------------------+
|   frontend/  (Next.js 15) |  HTTP  |   backend/  (FastAPI)       |
|                           | <----> |                             |
|  /app 랜딩 + 앱 페이지     |        |  /api/domain   도메인 설정  |
|  도메인 선택               |        |  /api/upload   파일 업로드  |
|  샘플/파일 업로드           |        |  /api/briefing 일일 브리핑  |
|  브리핑·그래프 대시보드     |        |  /api/chat     SSE 스트리밍 |
|  플로팅 AI 채팅 위젯 (FAB) |        |  /api/graph    KG 시각화   |
|  Amber + Slate 다크 테마   |        |                             |
+---------------------------+        +----------+------------------+
                                                |
                         +----------------------+--------------------+
                         |                      |                    |
               +---------v-----+  +-------------v-+  +-------------v--+
               | modules/      |  | domains/      |  | Supabase       |
               |               |  | 프리셋 7개     |  | pgvector       |
               | RAGEngine     |  | (beauty 등)   |  |                |
               | KnowledgeGraph|  |               |  | document_chunks|
               | chat_copilot  |  | + Claude 동적  |  | community_     |
               | data_analyst  |  |   도메인 생성  |  | summaries      |
               | community_    |  +---------------+  +----------------+
               | summarizer    |
               | claude_client |
               +---------------+
```

### GraphRAG 처리 흐름

```
【문서 업로드 시】
문서 → RAG 청킹 → Supabase document_chunks (pgvector)
     → Claude KG 추출 → KnowledgeGraph
     → detect_communities() (Louvain 알고리즘)
     → Claude 커뮤니티 요약 생성
     → Supabase community_summaries (pgvector)

【채팅 질문 시】
질문
 ├─ ① 커뮤니티 요약 검색: 질문 임베딩 → 유사 커뮤니티 요약 TOP-3
 ├─ ② 멀티홉 탐색: 질문 단어 → KG 2-hop 관계 체인 (A→B→C)
 └─ ③ 문서 청크 검색: 질문 임베딩 → 유사 청크 TOP-5
      세 결과 합산 → Claude 최종 답변
```

### 기존 방식 vs GraphRAG 비교

| 항목 | 기존 방식 | GraphRAG |
|------|---------|---------|
| KG 검색 | 첫 단어로 노드 ID 키워드 매칭 | 질문 임베딩 → 커뮤니티 요약 유사도 검색 |
| 관계 탐색 | 1-hop 이웃 노드만 | 2-hop 관계 체인 (A→B→C) |
| 컨텍스트 범위 | 문장 수준 (청크) | 개념 묶음 수준 (커뮤니티) + 청크 |
| 벡터 저장소 | ChromaDB (로컬) | Supabase pgvector (클라우드) |

### 핵심 설계 원칙

| 원칙 | 구현 방식 |
|------|----------|
| **도메인 무관** | `domains/` 프리셋 + Claude 동적 도메인 분석 |
| **모듈 독립성** | `modules/`는 FastAPI·Next.js 의존성 없이 단독 테스트 가능 |
| **3단계 라우팅** | 질문 → data / doc / combined 자동 분류 |
| **근거 기반 답변** | 모든 답변에 CSV·문서·KG 노드 수 뱃지 표시 |
| **의사결정 지원** | 모든 데이터 질문에 "오늘/이번주/이번달" 액션 제안 |
| **스트리밍** | FastAPI SSE(`/api/chat`)로 실시간 Claude 응답 스트리밍 |
| **병렬 처리** | KG 추출 및 combined 라우팅에 ThreadPoolExecutor 적용 |

---

## 핵심 기능

### 1. 도메인 적응
- 7개 내장 도메인: 뷰티, 공급망, 에너지, 제조, 물류, 금융, 범용
- 커스텀 도메인 입력 → Claude가 entity_types, 용어, 테마 컬러 자동 생성
- 도메인별 컬렉션 분리 (Supabase `collection_name` 컬럼)

### 2. GraphRAG 기반 문서 Q&A

문서를 업로드하면 두 단계로 처리됩니다.

**빌드 단계 (업로드 시 1회)**
1. 문서 청킹 → 임베딩 → Supabase `document_chunks` 저장
2. Claude가 엔티티·관계 추출 → NetworkX KG 구성
3. Louvain 알고리즘으로 커뮤니티 탐지 (서로 밀접한 노드 묶음 자동 분류)
4. 커뮤니티마다 Claude가 요약 생성 → Supabase `community_summaries` 저장

**검색 단계 (질문마다)**
1. 커뮤니티 요약 유사도 검색 → 관련 개념 묶음 컨텍스트
2. 멀티홉 그래프 탐색 (2-hop) → 관계 체인 컨텍스트
3. 문서 청크 유사도 검색 → 세부 내용 컨텍스트

### 3. 지식그래프 (3가지 뷰)
- **노드 그래프**: pyvis 인터랙티브 드릴다운 (Level 1→2→3)
- **ERD 테이블 뷰**: 컬럼·FK·관계가 표시된 카드형 테이블 스키마
- **데이터 흐름 뷰**: MST → FACT 방향성 흐름 + JOIN 키 표시

### 4. 데이터 채팅 엔진
5가지 질문 유형 자동 분류:

| 유형 | 트리거 | 출력 |
|------|--------|------|
| CHART | 제품 코드(FG-XXX) / 차트 키워드 | Plotly 라인/막대 차트 |
| RANKING | TOP / 잘팔리는 / 계절 | 가로 막대 + 순위 |
| COMPARISON | 비교 / 전년 대비 | YoY 막대 차트 |
| RISK | 위험 / 결품 / CRITICAL | 커버리지 차트 + 발주 현황 |
| DESCRIPTION | 그 외 모두 | GraphRAG + 문서 청크 결합 |

모든 답변: **한 줄 요약** + **핵심 수치 3개** + **차트** + **해석** + **다음 할 일 (오늘/이번주/이번달)**

### 5. 쿼리 플래너
비즈니스 문장 한 줄 → 데이터셋 자동 추천:
- 1단계: 키워드 매칭 (스키마 레지스트리)
- 2단계-a: FK 체인 확장 (연관 테이블 50% 신뢰도 추가)
- 2단계-b: Claude 이유 정제 → **이유 + 확인 질문 + 다음 액션**
- 3단계: RAG 문서 추천

### 6. 일일 브리핑
자동 생성 4개 카드:
- 재고 위험 품목 (CRITICAL/WARNING)
- 채널별 판매 TOP3 (최근 월)
- 발주 필요 품목 (활성 발주 없음)
- 이상 감지 (최근 2개월 vs 직전 2개월 ±50%)

각 카드: **한 줄 요약** + **핵심 수치** + **즉시 실행 액션 3개** + **"채팅에서 이어보기"** 버튼

### 7. 보안
- 프롬프트 인젝션 방어 (패턴 기반 정제)
- XSS 방지 (JS 임베딩 시 ensure_ascii=True)
- 경로 탐색 방어 (pathlib 기반 safe_csv_path)
- 데모 사용 제한 (세션당 API 호출 20회)

---

## 시작하기

### 1. Supabase 설정 (필수)

Supabase 프로젝트에서 아래 SQL을 순서대로 실행합니다.

```bash
# Supabase SQL Editor에서 순서대로 실행
scripts/vector_migration.sql      # pgvector 확장 + document_chunks 테이블 + RPC 함수
scripts/graphrag_migration.sql    # community_summaries 테이블 + RPC 함수
create_all_tables.sql             # 비즈니스 데이터 테이블 (선택)
```

### 2. 환경변수 설정

`.env.example`을 복사해 `.env` 파일 생성:

```bash
ANTHROPIC_API_KEY=your_key_here
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```

### 3. Backend 실행 (FastAPI)

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
# API 문서: http://localhost:8000/docs
```

### 4. Frontend 실행 (Next.js)

```bash
cd frontend
pnpm install
pnpm dev
# http://localhost:3000
```

---

## 데모 시나리오

### 시나리오 1: 공급망 재고 위험 분석
1. 도메인 선택 화면에서 "공급망" 선택 후 샘플 데이터 로드
2. "브리핑 생성" 클릭 → 4개 카드로 재고 위험 현황 확인
3. 채팅: `FG-002 수요 그래프` → 월별 추이 차트
4. 채팅: `CRITICAL 재고 품목과 발주 우선순위 알려줘`

### 시나리오 2: 회의록 → GraphRAG 연결
1. 회의록 TXT 파일 업로드
2. 자동으로 KG 구성 → 커뮤니티 탐지 → 요약 저장
3. 대시보드에서 "액션 아이템 추출" → 데이터셋 뱃지 자동 연결
4. 채팅 위젯: `공급망 리스크가 뭐야?` → 커뮤니티 요약 + 멀티홉 관계 기반 답변

### 시나리오 3: 신규 도메인 적응
1. 도메인 선택 화면에서 커스텀 도메인 직접 입력 (예: "의료")
2. Claude가 도메인별 엔티티 유형, 용어, 테마 자동 생성
3. 도메인 문서 업로드 → 도메인 특화 KG + GraphRAG 커뮤니티 구성

---

## 기술 스택

| 레이어 | 기술 | 선택 이유 |
|--------|------|----------|
| LLM | Claude Sonnet (Anthropic) | 한국어 문서 처리, 긴 컨텍스트 지원 |
| 벡터 DB | Supabase pgvector | 문서 청크 + 커뮤니티 요약 통합 저장, 클라우드 관리형 |
| 임베딩 | paraphrase-multilingual-MiniLM-L12-v2 | 한국어 의미 검색 최적화, 384차원 |
| GraphRAG | NetworkX (Louvain) + community_summarizer | 커뮤니티 탐지 + Claude 요약 + pgvector 검색 |
| UI | Next.js 15 (App Router) | 서버 컴포넌트, SSE 스트리밍, Amber+Slate 다크 테마 |
| API 서버 | FastAPI | 비동기 SSE 스트리밍, 자동 OpenAPI 문서화 |
| 그래프 시각화 | NetworkX + pyvis | 직관적 KG 구성 + 인터랙티브 HTML 렌더링 |
| 데이터 분석 | pandas + plotly | 경량 분석, 인터랙티브 차트 |
| 도메인 적응 | DomainConfig 데이터클래스 | 설정 변경 없이 도메인 전환 |

---

## 프로젝트 구조

```
ops-decision-copilot/
├── config.py                 # 전역 설정 (API 키, 경로, 색상)
│
├── frontend/                 # Next.js 15 앱 (git 서브모듈)
│   └── /app: 랜딩·앱 페이지, 플로팅 AI 채팅 위젯 (FAB)
│
├── backend/                  # FastAPI 서버
│   ├── main.py               # FastAPI 앱 + CORS 설정
│   ├── requirements.txt      # Python 의존성
│   └── routers/
│       ├── domain.py         # 도메인 설정 API
│       ├── upload.py         # 파일 업로드 + RAG/KG 처리
│       ├── briefing.py       # 일일 브리핑 생성
│       ├── chat.py           # SSE 스트리밍 채팅
│       └── graph.py          # KG 시각화
│
├── domains/                  # 도메인 프리셋 패키지
│   ├── __init__.py           # ALL_PRESETS, get_preset()
│   └── beauty.py / supply_chain.py / energy.py / manufacturing.py / logistics.py / finance.py / generic.py
│
├── modules/                  # 핵심 비즈니스 로직 (프레임워크 독립)
│   ├── claude_client.py      # Claude API 래퍼 (스트리밍, 재시도)
│   ├── rag_engine.py         # Supabase pgvector 벡터 검색
│   ├── knowledge_graph.py    # 엔티티 관계 그래프 + 커뮤니티 탐지 + 3가지 뷰
│   ├── community_summarizer.py  # GraphRAG 핵심 — 커뮤니티 요약 생성·저장·검색
│   ├── supabase_client.py    # Supabase REST API 클라이언트
│   ├── domain_adapter.py     # Claude 동적 도메인 분석
│   ├── document_parser.py    # PDF/DOCX/CSV 파서
│   ├── data_analyst.py       # pandas 데이터 분석 함수
│   ├── data_chat_engine.py   # 5가지 질문 유형 분류/응답
│   ├── query_planner.py      # 비즈니스 문장 → 데이터셋 추천
│   ├── chat_copilot.py       # 라우터 (data/doc/combined) + GraphRAG 컨텍스트 조합
│   └── prompt_loader.py      # 프롬프트 템플릿 로더 (system_base 주입)
│
├── prompts/                  # Claude 프롬프트 템플릿
│   ├── system_base.txt       # 공통 베이스 프롬프트 (역할, 규칙, domain_context)
│   └── summarize.txt / action_items.txt / root_cause.txt / report_draft.txt
│      / rag_query.txt / chat_routing.txt
│
├── scripts/                  # SQL 마이그레이션 + 데이터 생성 스크립트
├── eval/                     # 평가 테스트셋 (domain / fk / llm / rag)
└── data/                     # 샘플 데이터 (6개 도메인)
```

---

## 새 도메인 추가하기

```python
# 1. domains/healthcare.py 생성
PRESET = {
    "entity_types": {
        "patient":   "#2196F3",
        "doctor":    "#4CAF50",
        "facility":  "#FF9800",
        "issue":     "#F44336",
        "decision":  "#4CAF50",
        "metric":    "#607D8B",
        "default":   "#9E9E9E",
    },
    "terminology":       ["EMR", "DRG", "처방전", "진단 코드"],
    "document_patterns": ["의무 기록", "행정 보고서"],
    "analysis_focus":    ["환자 안전", "진료 효율", "비용 최적화"],
    "theme_color":       "#0284c7",
    "app_icon":          "hospital",
}

# 2. domains/__init__.py에 한 줄 추가
from domains.healthcare import PRESET as _healthcare
ALL_PRESETS["healthcare"] = _healthcare
```

또는 도메인명을 직접 입력하면 Claude가 즉시 설정을 생성합니다.

---

## 배포

- **Backend**: FastAPI → Render / Railway / EC2 등 Python 서버 환경
- **Frontend**: Next.js → Vercel 배포 권장 (`NEXT_PUBLIC_API_URL` 환경변수로 backend URL 지정)
- *(데모: 세션당 API 호출 20회 제한)*

---

## 라이선스

MIT
