# OPS Decision Copilot

> **도메인 적응형 AI 운영 코파일럿 플랫폼**
> 문서, 데이터, 지식그래프를 결합하여 운영 의사결정을 지원합니다.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://ops-decision-copilot.streamlit.app)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Claude API](https://img.shields.io/badge/LLM-Claude%20Sonnet-orange.svg)](https://anthropic.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 개요

OPS Decision Copilot은 **어떤 비즈니스 도메인에도 적응하는** AI 코파일럿 플랫폼입니다.
문서, CSV, 회의록을 업로드하면 다음 기능을 즉시 사용할 수 있습니다.

- **지식그래프 자동 구성** (Claude + NetworkX + pyvis)
- **RAG 기반 문서 Q&A** (ChromaDB + sentence-transformers)
- **CSV 데이터 자동 분석** (pandas + plotly) 및 구조화 답변
- **의사결정 지원**: 데이터 추천 → 확인 질문 → 다음 액션
- **일일 브리핑** 4개 카드 자동 생성
- **스트리밍 응답**으로 실시간 채팅 경험

7개 도메인 프리셋 내장 (뷰티, 공급망, 에너지, 제조, 물류, 금융, 범용).
도메인명을 직접 입력하면 Claude가 즉시 적응합니다.

---

## 아키텍처

```
+-------------------------------------------------------------+
|                    app.py  (UI 오케스트레이션)                |
|  Step 1: 도메인 설정 -> Step 2: 파일 업로드 -> Step 3: 결과  |
+---------+---------------------+--------------------+----------+
          |                     |                    |
 +--------v--------+  +---------v--------+  +-------v--------+
 | 문서              |  | 분석 엔진         |  | 채팅 엔진       |
 | 파이프라인         |  |                  |  |                |
 |                  |  | data_analyst     |  | chat_copilot   |
 | RAGEngine        |  | data_chat_engine |  | 라우팅:         |
 | (ChromaDB)       |  | query_planner    |  |  data /        |
 |                  |  |                  |  |  doc /         |
 | KnowledgeGraph   |  | 5가지 질문 유형   |  |  combined      |
 | (NetworkX)       |  | CHART / RANKING  |  |                |
 |                  |  | COMPARISON /     |  | DataAnswer ->  |
 | document_parser  |  | RISK / DESCRIBE  |  | ChatResult     |
 +-----------------+   +------------------+  +----------------+
                               |
          +--------------------+--------------------+
          |                    |                    |
+---------v-----+  +-----------v---+  +------------v--+
| Claude API    |  | domains/      |  | prompts/      |
| (Anthropic)   |  | 프리셋         |  | 템플릿         |
|               |  |               |  |               |
| claude_client |  | beauty        |  | system_base   |
| domain_adapter|  | supply_chain  |  | summarize     |
+---------------+  | energy / ...  |  | rag_query     |
                   +---------------+  +---------------+
```

### 핵심 설계 원칙

| 원칙 | 구현 방식 |
|------|----------|
| **도메인 무관** | `domains/` 프리셋 + Claude 동적 도메인 분석 |
| **모듈 독립성** | `data_analyst.py`는 Streamlit 의존성 없이 단독 테스트 가능 |
| **3단계 라우팅** | 질문 → data / doc / combined 자동 분류 |
| **근거 기반 답변** | 모든 답변에 CSV·문서·KG 노드 수 뱃지 표시 |
| **의사결정 지원** | 모든 데이터 질문에 "오늘/이번주/이번달" 액션 제안 |
| **스트리밍** | `st.write_stream`으로 실시간 Claude 응답 스트리밍 |
| **병렬 처리** | KG 추출 및 combined 라우팅에 ThreadPoolExecutor 적용 |

---

## 핵심 기능

### 1. 도메인 적응
- 7개 내장 도메인: 뷰티, 공급망, 에너지, 제조, 물류, 금융, 범용
- 커스텀 도메인 입력 → Claude가 entity_types, 용어, 테마 컬러 자동 생성
- 도메인별 ChromaDB 컬렉션 분리

### 2. 지식그래프 (3가지 뷰)
- **노드 그래프**: pyvis 인터랙티브 드릴다운 (Level 1→2→3)
- **ERD 테이블 뷰**: 컬럼·FK·관계가 표시된 카드형 테이블 스키마
- **데이터 흐름 뷰**: MST → FACT 방향성 흐름 + JOIN 키 표시

### 3. 데이터 채팅 엔진
5가지 질문 유형 자동 분류:

| 유형 | 트리거 | 출력 |
|------|--------|------|
| CHART | 제품 코드(FG-XXX) / 차트 키워드 | Plotly 라인/막대 차트 |
| RANKING | TOP / 잘팔리는 / 계절 | 가로 막대 + 순위 |
| COMPARISON | 비교 / 전년 대비 | YoY 막대 차트 |
| RISK | 위험 / 결품 / CRITICAL | 커버리지 차트 + 발주 현황 |
| DESCRIPTION | 그 외 모두 | RAG + KG 결합 |

모든 답변: **한 줄 요약** + **핵심 수치 3개** + **차트** + **해석** + **다음 할 일 (오늘/이번주/이번달)**

### 4. 쿼리 플래너
비즈니스 문장 한 줄 → 데이터셋 자동 추천:
- 1단계: 키워드 매칭 (스키마 레지스트리)
- 2단계-a: FK 체인 확장 (연관 테이블 50% 신뢰도 추가)
- 2단계-b: Claude 이유 정제 → **이유 + 확인 질문 + 다음 액션**
- 3단계: RAG 문서 추천

### 5. 일일 브리핑
자동 생성 4개 카드:
- 재고 위험 품목 (CRITICAL/WARNING)
- 채널별 판매 TOP3 (최근 월)
- 발주 필요 품목 (활성 발주 없음)
- 이상 감지 (최근 2개월 vs 직전 2개월 ±50%)

각 카드: **한 줄 요약** + **핵심 수치** + **즉시 실행 액션 3개** + **"채팅에서 이어보기"** 버튼

### 6. 보안
- 프롬프트 인젝션 방어 (패턴 기반 정제)
- XSS 방지 (JS 임베딩 시 ensure_ascii=True)
- 경로 탐색 방어 (pathlib 기반 safe_csv_path)
- 데모 사용 제한 (세션당 API 호출 20회)

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

## 시작하기

```bash
git clone https://github.com/swim-seo/ops-decision-copilot.git
cd ops-decision-copilot
pip install -r requirements.txt

# API 키 설정 (둘 중 하나)
cp .env.example .env                    # .env에 ANTHROPIC_API_KEY 추가
# 또는
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

streamlit run app.py
```

---

## 데모 시나리오

### 시나리오 1: 공급망 재고 위험 분석
1. "샘플 데이터"를 클릭해 데모 데이터 로드
2. "브리핑 생성" 클릭 → 4개 카드로 재고 위험 현황 확인
3. 채팅: `FG-002 수요 그래프` → 월별 추이 차트
4. 채팅: `CRITICAL 재고 품목과 발주 우선순위 알려줘`

### 시나리오 2: 회의록 → 데이터 연결
1. 회의록 TXT 파일 업로드
2. AI 분석 탭 → "액션 아이템 추출" → 데이터셋 뱃지 자동 연결
3. "데이터 추천 보기" 클릭 → 이유·확인 질문·다음 액션 확인

### 시나리오 3: 신규 도메인 적응
1. Step 1에서 커스텀 도메인 입력 (예: "의료")
2. Claude가 도메인별 엔티티 유형, 용어, 테마 자동 생성
3. 도메인 문서 업로드 → 도메인 특화 지식그래프 구성

---

## 기술 스택

| 레이어 | 기술 | 선택 이유 |
|--------|------|----------|
| LLM | Claude Sonnet (Anthropic) | 한국어 문서 처리, 긴 컨텍스트 지원 |
| 벡터 DB | ChromaDB | 경량 임베딩 DB, 로컬/클라우드 호환 |
| 임베딩 | paraphrase-multilingual-MiniLM-L12-v2 | 한국어 의미 검색 최적화 |
| UI | Streamlit | 빠른 프로토타이핑, 인터랙티브 컴포넌트 |
| 그래프 | NetworkX + pyvis | 직관적 KG 구성 + 인터랙티브 HTML 렌더링 |
| 데이터 분석 | pandas + plotly | 경량 분석, 인터랙티브 차트 |
| 도메인 적응 | DomainConfig 데이터클래스 | 설정 변경 없이 도메인 전환 |

---

## 프로젝트 구조

```
ops-decision-copilot/
+-- app.py                    # UI 오케스트레이션 (Streamlit 3단계 플로우)
+-- config.py                 # 전역 설정 (API 키, 경로, 색상)
|
+-- domains/                  # 도메인 프리셋 패키지
|   +-- __init__.py           # ALL_PRESETS, get_preset()
|   +-- beauty.py             # 뷰티/이커머스
|   +-- supply_chain.py       # 공급망/재고
|   +-- energy.py / manufacturing.py / logistics.py / finance.py / generic.py
|
+-- modules/                  # 핵심 비즈니스 로직
|   +-- claude_client.py      # Claude API 래퍼 (스트리밍, 재시도)
|   +-- rag_engine.py         # ChromaDB 벡터 검색
|   +-- knowledge_graph.py    # 엔티티 관계 그래프 + 3가지 뷰
|   +-- domain_adapter.py     # Claude 동적 도메인 분석
|   +-- document_parser.py    # PDF/DOCX/CSV 파서
|   +-- data_analyst.py       # pandas 데이터 분석 함수
|   +-- data_chat_engine.py   # 5가지 질문 유형 분류/응답
|   +-- query_planner.py      # 비즈니스 문장 → 데이터셋 추천
|   +-- chat_copilot.py       # 라우터 (data/doc/combined) + 스트리밍
|   +-- prompt_loader.py      # 프롬프트 템플릿 로더 (system_base 주입)
|
+-- prompts/                  # Claude 프롬프트 템플릿
|   +-- system_base.txt       # 공통 베이스 프롬프트 (역할, 규칙, domain_context)
|   +-- summarize.txt / action_items.txt / root_cause.txt / report_draft.txt
|   +-- rag_query.txt / chat_routing.txt
|
+-- scripts/                  # 데이터 생성 스크립트
+-- tests/                    # 테스트 파일
+-- data/                     # 샘플 데이터 (공급망 도메인 데모)
```

---

## 배포

- **라이브 데모**: [ops-decision-copilot.streamlit.app](https://ops-decision-copilot.streamlit.app)
  *(데모: 세션당 API 호출 20회 제한)*

---

## 라이선스

MIT
