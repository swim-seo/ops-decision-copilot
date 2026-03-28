# OPS Decision Copilot

> **도메인 적응형 내부 AI 코파일럿 플랫폼**
> 문서·데이터·지식 그래프를 결합해 운영 의사결정을 지원하는 실용적 AI 시스템

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ops-decision-copilot.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Claude API](https://img.shields.io/badge/LLM-Claude%20Sonnet-orange.svg)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 플랫폼 개요

OPS Decision Copilot은 **어떤 비즈니스 도메인에도** 적용 가능한 AI 코파일럿 플랫폼입니다.
운영 담당자가 문서·CSV·회의록을 올리면 즉시:

- **문서 → 지식 그래프** 자동 구축 (Claude + NetworkX)
- **RAG 기반 문서 Q&A** (ChromaDB + sentence-transformers)
- **CSV 데이터 자동 분석** (pandas + plotly) + 구조화 답변
- **판단 보조**: 데이터 추천 → 확인 질문 → 다음 액션 자동 제시
- **일일 브리핑** 4카드 자동 생성

뷰티 이커머스, 공급망, 에너지, 제조, 물류, 금융 등 **기본 제공 도메인 7개**,
직접 입력하면 **어떤 도메인도 즉시 적응**합니다.

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    app.py  (UI Orchestration)                   │
│  Step 1: 도메인 설정 → Step 2: 파일 업로드 → Step 3: 결과 보기  │
└─────────┬─────────────────────┬────────────────────┬────────────┘
          │                     │                    │
 ┌────────▼────────┐  ┌─────────▼────────┐  ┌───────▼────────┐
 │ Document        │  │ Analytics        │  │ Chat Engine    │
 │ Pipeline        │  │ Engine           │  │                │
 │                 │  │                  │  │ chat_copilot   │
 │ RAGEngine       │  │ data_analyst     │  │ route:         │
 │ (ChromaDB)      │  │ data_chat_engine │  │  data /        │
 │                 │  │ query_planner    │  │  doc /         │
 │ KnowledgeGraph  │  │                  │  │  combined      │
 │ (NetworkX)      │  │ 5 question types │  │                │
 │                 │  │ CHART / RANKING  │  │ DataAnswer →   │
 │ document_parser │  │ COMPARISON /     │  │ ChatResult     │
 └─────────────────┘  │ RISK / DESCRIBE  │  └────────────────┘
                      └──────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
  ┌────────▼──────┐  ┌──────────▼────┐  ┌───────────▼───┐
  │ Claude API    │  │ domains/      │  │ prompts/      │
  │ (Anthropic)   │  │ presets       │  │ templates     │
  │               │  │               │  │               │
  │ claude_client │  │ beauty        │  │ action_items  │
  │ domain_adapter│  │ supply_chain  │  │ report_draft  │
  └───────────────┘  │ energy / ...  │  │ rag_query     │
                     └───────────────┘  └───────────────┘
```

### 핵심 설계 원칙

| 원칙 | 구현 |
|------|------|
| **도메인 무관** | `domains/` 프리셋 + Claude 동적 도메인 분석 |
| **모듈 독립성** | `data_analyst.py` — Streamlit 의존 없음, 단독 테스트 가능 |
| **3-Layer 라우팅** | 질문 → data / doc / combined 자동 분류 후 전문 엔진 위임 |
| **증거 기반 답변** | 모든 답변에 사용 CSV·문서·KG 노드 수 badge 표시 |
| **판단 보조** | 데이터 조회 후 항상 "오늘/이번 주/이번 달 할 일" 제시 |

---

## 핵심 기능

### 1. 도메인 적응 (Domain Adaptation)
- 기본 제공 7개 도메인: 뷰티, 공급망, 에너지, 제조, 물류, 금융, 범용
- 직접 입력 → Claude가 entity_types·terminology·theme_color 자동 생성
- 도메인별 ChromaDB 컬렉션 분리 (collection_name 자동 생성)

### 2. 지식 그래프 (Knowledge Graph)
- CSV 스키마 → FK 관계 자동 추출
- PDF·DOCX·TXT → Claude 엔티티·관계 추출
- JSON 스키마 → ERD 구조 직접 변환
- pyvis 인터랙티브 드릴다운 (Level 1→2→3)

### 3. 데이터 채팅 엔진 (Data Chat Engine)
5가지 질문 유형 자동 분류:

| 유형 | 트리거 | 반환 |
|------|--------|------|
| CHART | 제품 코드(FG-XXX) / 차트·그래프 키워드 | Plotly 라인/바 차트 |
| RANKING | TOP·상위·잘팔리·계절 키워드 | 수평 바 차트 + 순위 |
| COMPARISON | 비교·YoY·전년 키워드 | 연도별 바 차트 |
| RISK | 위험·품절·CRITICAL 키워드 | 커버리지 차트 + 발주 현황 |
| DESCRIPTION | 기타 | RAG + KG 결합 답변 |

모든 답변: **요약 1줄** + **핵심 수치 3개** + **차트** + **해석** + **다음 할 일 (오늘/이번 주/이번 달)**

### 4. 쿼리 플래너 (Query Planner)
업무 문장 한 줄 → 필요한 데이터셋 자동 추천:
- Pass 1: 키워드 매칭 (13개 테이블 스키마 레지스트리)
- Pass 2a: FK 체인 확장 (연관 테이블 50% confidence로 추가)
- Pass 2b: Claude 이유 정제 → **추천 이유 + 지금 확인할 질문 + 다음 액션**
- Pass 3: RAG 문서 추천

### 5. 일일 브리핑 (Daily Briefing)
4개 카드 자동 생성:
- 🚨 재고 위험 상품 (CRITICAL/WARNING)
- 📈 채널별 판매 TOP3 (최근 월)
- 📦 발주 필요 상품 (발주 없는 위험 재고)
- ⚡ 이상 변화 감지 (최근 2개월 vs 직전 2개월 ±50%)

각 카드: **한 줄 요약** + **핵심 수치** + **지금 해야 할 일 3개** + **채팅으로 이어서 질문** 버튼

### 6. 문서 분석 (Document Analysis)
- 요약 / 액션 아이템 추출 / 원인 분석 / 보고서 초안
- 액션 아이템 추출 → **연관 데이터셋 badge 자동 연결**
- RAG 문서 검색 + 번호/코드 드릴다운 조회

---

## 도메인 확장 구조

새 도메인을 추가하는 방법:

```python
# 1. domains/healthcare.py 파일 생성
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
    "terminology":       ["EMR", "DRG", "처방전", "진단코드", "원무"],
    "document_patterns": ["진료기록", "원무보고서", "감염관리보고서"],
    "analysis_focus":    ["환자 안전", "진료 효율", "비용 최적화"],
    "theme_color":       "#0284c7",
    "app_icon":          "🏥",
}

# 2. domains/__init__.py에 한 줄 추가
from domains.healthcare import PRESET as _healthcare
ALL_PRESETS["의료"] = _healthcare
```

도메인 파일 없이 텍스트만 입력해도 Claude가 즉시 맞춤 설정을 생성합니다.

---

## 실행 방법

```bash
git clone https://github.com/swim-seo/ops-decision-copilot.git
cd ops-decision-copilot
pip install -r requirements.txt

# API 키 설정 (두 방법 중 하나)
cp .env.example .env                                      # .env에 ANTHROPIC_API_KEY 입력
# 또는
cp .streamlit/secrets.toml.example .streamlit/secrets.toml  # secrets에 입력

streamlit run app.py
```

---

## 데모 시나리오

### 시나리오 1: 공급망 재고 위험 분석
1. "🚀 샘플 데이터로 바로 시작" 클릭
2. "📋 브리핑 생성" → 재고 위험 현황 4카드 확인
3. 채팅: `FG-002 선크림 수요 그래프 그려줘` → 월별 추이 차트
4. 채팅: `재고 위험 CRITICAL 상품 발주 우선순위 알려줘` → 다음 액션 제시

### 시나리오 2: 회의록 → 데이터 연결
1. 회의록 TXT 파일 업로드
2. AI 분석 탭 → "✅ 액션 아이템 추출" → 연관 데이터셋 badge 자동 표시
3. "🔍 데이터 추천 자세히 보기" → 추천 이유·확인 질문·다음 액션 확인

### 시나리오 3: 신규 도메인 적응
1. Step 1에서 "의료·병원" 직접 입력
2. Claude가 의료 도메인 맞춤 entity_types·용어·테마 자동 생성
3. 의료 문서 업로드 → 의료 전문 지식 그래프 구축

---

## 기술 스택

| 레이어 | 기술 | 선택 이유 |
|--------|------|-----------|
| LLM | Claude Sonnet 4.6 (Anthropic) | 한국어 문서 처리 최적, 긴 컨텍스트 |
| 벡터 DB | ChromaDB | 경량 임베딩 DB, 로컬/클라우드 동일 동작 |
| 임베딩 | paraphrase-multilingual-MiniLM-L12-v2 | 한국어 시맨틱 검색 최적화 |
| UI | Streamlit | 빠른 프로토타입, 인터랙티브 컴포넌트 |
| 그래프 | NetworkX + pyvis | 직관적 KG 구축 + HTML 인터랙티브 렌더링 |
| 데이터 분석 | pandas + plotly | 경량 분석, 인터랙티브 차트 |
| 도메인 적응 | DomainConfig dataclass | 설정 변경 없이 도메인 전환 |

---

## 프로젝트 구조

```
ops-decision-copilot/
├── app.py                    # UI Orchestration (Streamlit 3-step flow)
├── config.py                 # 전역 설정 (API 키, 경로, 색상)
│
├── domains/                  # 도메인 프리셋 패키지 (신규 도메인 추가 위치)
│   ├── __init__.py           # ALL_PRESETS, get_preset()
│   ├── beauty.py             # 뷰티·이커머스
│   ├── supply_chain.py       # 공급망·재고
│   ├── energy.py             # 에너지
│   ├── manufacturing.py      # 제조·생산
│   ├── logistics.py          # 물류·배송
│   ├── finance.py            # 금융·투자
│   └── generic.py            # 범용 비즈니스
│
├── modules/                  # 핵심 비즈니스 로직
│   ├── claude_client.py      # [LLM]      Claude API 래퍼
│   ├── rag_engine.py         # [RAG]      ChromaDB 벡터 검색
│   ├── knowledge_graph.py    # [KG]       엔티티 관계 그래프
│   ├── domain_adapter.py     # [Domain]   Claude 동적 도메인 분석
│   ├── document_parser.py    # [Docs]     PDF/DOCX/CSV 파서
│   ├── data_analyst.py       # [Analytics] pandas 데이터 분석 함수
│   ├── data_chat_engine.py   # [Analytics] 5종 질문 유형 분류·답변
│   ├── query_planner.py      # [Analytics] 업무 문장 → 데이터 추천
│   ├── chat_copilot.py       # [Chat]     라우터 (data/doc/combined)
│   └── prompt_loader.py      # [Prompts]  프롬프트 템플릿 로더
│
├── prompts/                  # Claude 프롬프트 템플릿
│   ├── summarize.txt
│   ├── action_items.txt
│   ├── root_cause.txt
│   ├── report_draft.txt
│   └── rag_query.txt
│
└── data/                     # 샘플 데이터 (공급망 도메인 데모)
    ├── FACT_MONTHLY_SALES.csv
    ├── FACT_INVENTORY.csv
    ├── FACT_REPLENISHMENT_ORDER.csv
    ├── MST_PRODUCT.csv
    ├── MST_CHANNEL.csv
    └── SCHEMA_DEFINITION.json
```

---

## 배포

- **라이브 데모**: [ops-decision-copilot.streamlit.app](https://ops-decision-copilot.streamlit.app)
  *(데모 환경: API 호출 20회 제한 적용)*

---

## 포트폴리오 노트

이 프로젝트가 증명하는 것:

| 역량 | 구현 |
|------|------|
| **실제 동작하는 내부 도구 설계** | 단순 RAG챗봇을 넘어 문서·데이터·KG를 결합한 복합 AI 시스템 |
| **도메인 확장 가능한 구조** | `domains/` 프리셋 + Claude 동적 분석으로 무한 도메인 확장 |
| **운영 적용 가능한 아키텍처** | 일일 브리핑·이상 감지·발주 액션 등 실무 의사결정 흐름 구현 |
| **LLM + 전통 분석 결합** | Claude 언어 추론 + pandas 정확한 수치 분석의 효과적 역할 분담 |
| **모듈 독립성** | 각 모듈이 독립적으로 테스트·재사용 가능 (Streamlit 비의존) |
