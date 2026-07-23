"""
[역할] AI 오케스트레이션 층 — Function Calling 툴 정의 (Sprint 1)

기존 기능(RAG 검색·GraphRAG 검색·데이터 분석·브리핑)을 LLM이 스스로 고를 수 있는
"툴"로 노출합니다. chat_copilot.detect_route()의 if-else 규칙 라우팅을 대체하기 위한
기반이며, Step 2의 LangGraph 에이전트와 Step 4의 FastMCP 서버가 이 파일을 공유합니다.

툴 = 두 조각으로 구성:
  1) 스키마(TOOL_SCHEMAS) — LLM이 읽는 JSON 명세 (Anthropic tool-use 형식)
  2) 실행함수(_run_*)      — 기존 modules/ 를 감싸는 얇은 래퍼

설계 원칙:
  - 요청별 의존성(rag/kg/claude/...)은 ToolContext로 주입 → 전역 상태 없음
    (테스트 용이 + 향후 org_id 멀티테넌시 격리 대비)
  - modules/ 는 프레임워크 독립 → 이 파일은 backend/ 를 import 하지 않음
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict

logger = logging.getLogger(__name__)


# ── 요청별 컨텍스트 ────────────────────────────────────────────────────────────

@dataclass
class ToolContext:
    """툴 실행에 필요한 요청 범위 의존성 묶음.

    전역 변수 대신 이 객체로 주입해 테스트·멀티테넌시(향후 org_id 격리)에 대비합니다.
    """
    claude:          Any                       # ClaudeClient
    rag:             Any = None                 # RAGEngine | None
    kg:              Any = None                 # KnowledgeGraph | None
    domain_context:  str = ""
    collection_name: str = "domain_docs"
    department:      str = ""                    # 부서 렌즈 (Sprint 3 Step 1) — 이미 resolve 됨


# ── 툴 스키마 (LLM이 읽는 명세, Anthropic tool-use 형식) ────────────────────────

TOOL_SCHEMAS = [
    {
        "name": "search_documents",
        "description": (
            "업로드된 문서(회의록·보고서·정책 등)에서 근거 문장을 찾을 때 사용. "
            "특정 사실·정의·서술형 내용을 문서에서 인용해야 할 때 적합."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query":     {"type": "string",  "description": "검색할 자연어 질의"},
                "n_results": {"type": "integer", "description": "가져올 청크 수 (기본 4)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_graph",
        "description": (
            "원인·영향·연결 등 개체 간 '관계'를 묻는 질문에 사용. "
            "지식그래프 커뮤니티 요약 + 2-hop 관계 체인을 함께 검색한다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "관계 탐색용 자연어 질의"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "analyze_data",
        "description": (
            "수치·랭킹·재고·발주·판매추이 등 CSV/테이블 기반 정량 분석이 필요할 때 사용. "
            "차트가 필요한 질문도 포함."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "분석할 자연어 질문"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "get_briefing",
        "description": (
            "업로드된 자료 전반의 요약·리스크·인사이트·추천 액션을 한 번에 보고 싶을 때 사용."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]


# ── 툴 실행함수 (기존 modules/ 래핑) ───────────────────────────────────────────

def _run_search_documents(ctx: ToolContext, query: str, n_results: int = 4) -> str:
    """rag_engine.query() 래퍼 — 유사 청크를 출처와 함께 텍스트로 반환."""
    if not ctx.rag:
        return "(RAG 엔진이 없어 문서 검색 불가)"
    hits = ctx.rag.query(query, n_results=n_results)
    if not hits:
        return "관련 문서를 찾지 못했습니다."
    return "\n\n".join(
        f"[{h['filename']} | 관련도 {h['score']:.2f}]\n{h['text']}" for h in hits
    )


# GraphRAG 커뮤니티 검색 파라미터
_COMMUNITY_TOP_K = 3
_COMMUNITY_OVER_FETCH = 4   # 부서 가중 재랭킹용 후보 풀 배수 (Codex Q2: over-fetch → 재정렬)


def _run_search_graph(ctx: ToolContext, query: str) -> str:
    """GraphRAG 래퍼 — 커뮤니티 요약 검색 + 2-hop 멀티홉 탐색을 결합해 반환.

    부서 렌즈(ctx.department)가 있으면 커뮤니티 후보를 넓게 받아 retrieval_profiles
    로 재랭킹한다("같은 그래프, 부서별 렌즈" — Sprint 3 Step 1). 없으면 유사도순 그대로.
    (chat_copilot._build_graphrag_context 와 동일 로직 — 툴 인터페이스로 재노출)
    """
    if not ctx.kg:
        return "(지식그래프가 없어 관계 탐색 불가)"
    from modules.community_summarizer import (
        fetch_community_candidates,
        format_community_rows,
    )
    from modules.retrieval_profiles import get_profile, rerank_communities

    parts = []

    # ① 커뮤니티 요약 검색 (+ 부서 가중 재랭킹) — 질문과 유사한 개념 묶음
    #    org_id 는 Step 1 임시로 collection_name 사용(Step 2: JWT org_id).
    profile = get_profile(ctx.collection_name, ctx.department)
    match_count = (
        _COMMUNITY_TOP_K * _COMMUNITY_OVER_FETCH
        if not profile.is_default else _COMMUNITY_TOP_K
    )
    candidates = fetch_community_candidates(query, ctx.collection_name, match_count=match_count)
    ranked = rerank_communities(candidates, ctx.kg, profile, top_k=_COMMUNITY_TOP_K)
    community_ctx = format_community_rows(ranked)
    if community_ctx:
        parts.append(community_ctx)

    # ② 멀티홉 탐색 — 질문 단어들로 관계 체인(A→B→C) 추적
    entities = [w for w in query.split() if len(w) > 1]
    multihop = ctx.kg.multi_hop_query(entities, max_hops=2)
    if multihop["nodes"]:
        nodes_str = ", ".join(
            f"{n.get('label', n.get('id', ''))}({n.get('type', '')})"
            for n in multihop["nodes"][:8]
        )
        edges_str = "; ".join(
            f"{e['source']}→{e['relation']}→{e['target']}"
            for e in multihop["edges"][:10]
        )
        parts.append(f"[지식그래프 멀티홉 탐색]\n노드: {nodes_str}\n관계: {edges_str}")

    return "\n\n".join(parts) or "관련 관계를 찾지 못했습니다."


def _run_analyze_data(ctx: ToolContext, question: str) -> str:
    """data_chat_engine.analyze() 래퍼 — 정량 분석 결과를 텍스트로 요약해 반환.

    주의: 차트(plotly figure)는 텍스트로 직렬화할 수 없으므로 개수만 표기한다.
          (차트 자체의 전달은 Step 2 에이전트가 별도 메타로 처리)
    """
    from modules.data_chat_engine import analyze
    answer = analyze(
        question, claude=ctx.claude, rag=ctx.rag, kg=ctx.kg,
        domain_context=ctx.domain_context,
    )
    parts = []
    if answer.summary:
        parts.append(f"요약: {answer.summary}")
    if answer.interpretation:
        parts.append(answer.interpretation)
    if answer.datasets:
        parts.append(f"(사용 데이터: {', '.join(answer.datasets)})")
    if answer.charts:
        parts.append(f"[차트 {len(answer.charts)}개 생성됨]")
    return "\n\n".join(parts) or "관련 데이터를 찾지 못했습니다."


# 브리핑 4개 항목별 검색 질의 (backend/routers/briefing.py 의 카드 정의와 의미상 대응.
# modules/ 프레임워크 독립 원칙 때문에 router 를 import 하지 않고 여기 자체 정의)
_BRIEFING_QUERIES = {
    "핵심 요약":  "전체 내용 핵심 요약",
    "주요 리스크": "리스크 문제 이슈 위험",
    "인사이트":   "성과 트렌드 기회 개선",
    "추천 액션":  "액션 결정 다음단계 개선방안",
}


def _run_get_briefing(ctx: ToolContext) -> str:
    """4개 항목(요약/리스크/인사이트/액션)의 컨텍스트를 모아 Claude로 1회 브리핑 생성."""
    if not ctx.rag:
        return "(RAG 엔진이 없어 브리핑 불가)"

    context_parts = []
    for label, q in _BRIEFING_QUERIES.items():
        ctx_str = ctx.rag.get_context(q)
        if ctx_str:
            context_parts.append(f"### {label} 관련 자료\n{ctx_str}")

    if not context_parts:
        return "업로드된 자료가 없어 브리핑할 내용이 없습니다."

    combined = "\n\n".join(context_parts)
    prompt = (
        f"{ctx.domain_context}\n\n"
        f"[참고 자료]\n{combined}\n\n"
        "위 자료를 바탕으로 다음 4개 항목을 각각 2~3문장으로 브리핑하세요:\n"
        "핵심 요약 / 주요 리스크 / 인사이트 / 추천 액션."
    )
    return ctx.claude.generate(prompt, max_tokens=1500)


# ── 디스패치 ───────────────────────────────────────────────────────────────────

TOOL_EXECUTORS: Dict[str, Callable[..., str]] = {
    "search_documents": _run_search_documents,
    "search_graph":     _run_search_graph,
    "analyze_data":     _run_analyze_data,
    "get_briefing":     _run_get_briefing,
}


def run_tool(ctx: ToolContext, name: str, tool_input: Dict[str, Any]) -> str:
    """이름으로 툴 실행함수를 찾아 실행한다.

    예외는 문자열로 감싸 반환한다 — 툴 하나의 실패가 에이전트 루프 전체를 죽이지
    않도록 하기 위함 (Codex 리뷰에서 지적한 '멱등성·에러 격리' 대응의 일부).
    """
    fn = TOOL_EXECUTORS.get(name)
    if not fn:
        return f"(알 수 없는 툴: {name})"
    try:
        return fn(ctx, **tool_input)
    except Exception as e:  # noqa: BLE001 — 의도적 광범위 캐치 (툴 실패 격리)
        logger.exception("툴 실행 실패: %s", name)
        return f"(툴 '{name}' 실행 중 오류: {e})"
