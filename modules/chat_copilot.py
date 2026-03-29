"""
[역할] 채팅 코파일럿 라우터
사용자 질문을 분석하여 최적의 답변 경로를 선택하고 근거 정보를 함께 반환합니다.

라우팅 규칙:
  - "data"     : 제품코드/판매/재고/발주/차트 키워드 → CSV+pandas 기반
  - "doc"      : 회의록/보고서/정책/의사결정 키워드 → RAG+KG 기반
  - "combined" : 두 키워드 동시 또는 분류 불가 → RAG+KG+데이터 결합

반환: ChatResult (text, route, charts, datasets, documents, kg_nodes)
"""
import re
from dataclasses import dataclass, field
from typing import Any, List, Optional

# ── 보안: 프롬프트 인젝션 방어 ─────────────────────────────────────────────────

_INJECTION_PATTERNS = re.compile(
    r"(ignore\s+(all\s+)?previous\s+instructions?"
    r"|forget\s+(all\s+)?previous"
    r"|you\s+are\s+now"
    r"|새로운\s+지시"
    r"|이전\s+지시.*무시"
    r"|역할.*변경"
    r"|system\s*:)",
    re.IGNORECASE | re.DOTALL,
)

def sanitize_input(text: str, max_len: int = 2000) -> str:
    """사용자 입력에서 역할 덮어쓰기 패턴을 제거하고 길이를 제한합니다."""
    text = text[:max_len]
    text = _INJECTION_PATTERNS.sub("[필터됨]", text)
    return text


# ── 결과 데이터클래스 ─────────────────────────────────────────────────────────

@dataclass
class ChatResult:
    text:      str
    route:     str                        # "data" | "doc" | "combined"
    charts:    List[Any]   = field(default_factory=list)
    datasets:  List[str]   = field(default_factory=list)   # 사용한 CSV 파일명
    documents: List[str]   = field(default_factory=list)   # 사용한 문서 파일명
    kg_nodes:  int         = 0                              # 매칭된 KG 노드 수
    metrics:   List[Any]   = field(default_factory=list)   # [{label, value, delta}]


# ── 키워드 정의 ───────────────────────────────────────────────────────────────

_GRAPH_KW = ["그래프", "차트", "시각화", "그려줘", "보여줘", "플롯"]
_DATA_KW  = _GRAPH_KW + [
    "잘팔리", "잘 팔리", "판매", "매출", "분석", "재고", "발주",
    "수요", "상위", "여름", "봄", "가을", "겨울", "계절",
    "top", "채널", "품절", "stockout",
]
_DOC_KW   = ["회의록", "보고서", "정책", "분석자료", "문서", "의사결정", "액션", "요약"]
# 범용 제품/코드 패턴: FG-001, SKU-123, PRD001, P-001, ITEM-99 등 도메인 무관하게 매칭
_PROD_RE  = re.compile(r"\b([A-Z]{1,5}-\d+|[A-Z]{2,5}\d{2,})\b", re.IGNORECASE)
_SEASON   = {"여름": [6,7,8], "봄": [3,4,5], "가을": [9,10,11], "겨울": [12,1,2]}


# ── 라우팅 ───────────────────────────────────────────────────────────────────

def detect_route(msg: str) -> str:
    """질문 유형 분류: 'data' | 'doc' | 'combined'"""
    m        = msg.lower()
    has_data = any(k in m for k in _DATA_KW) or bool(_PROD_RE.search(msg))
    has_doc  = any(k in m for k in _DOC_KW)

    if has_data and not has_doc:
        return "data"
    if has_doc and not has_data:
        return "doc"
    return "combined"   # 둘 다 있거나 둘 다 없을 때


def _detect_season(msg: str) -> Optional[str]:
    for s in _SEASON:
        if s in msg:
            return s
    return None


# ── 경로별 처리 ───────────────────────────────────────────────────────────────

def _handle_data(msg: str, claude, domain_context: str) -> ChatResult:
    from modules.data_analyst import (
        product_sales_chart, channel_sales_chart,
        season_top_products, inventory_risk_summary,
        pending_orders_summary,
    )
    m        = msg.lower()
    ctx      : List[str] = []
    datasets : List[str] = []
    charts   : List[Any] = []

    # ── 차트/그래프 요청 ──────────────────────────────────
    if any(k in m for k in _GRAPH_KW) or bool(_PROD_RE.search(msg)):
        match = _PROD_RE.search(msg)
        if match:
            fig, name, ds = product_sales_chart(match.group(1))
            datasets.extend(ds)
            if fig:
                charts.append(fig)
            text = f"**{name}** 월별 판매 추이입니다." if fig else f"'{match.group(1)}' 판매 데이터를 찾을 수 없습니다."
        else:
            recent = 3 if "최근" in m else 0
            fig, ds = channel_sales_chart(recent_months=recent)
            datasets.extend(ds)
            if fig:
                charts.append(fig)
            text = "채널별 월별 판매 추이입니다."
        return ChatResult(text=text, route="data", charts=charts,
                          datasets=list(set(datasets)))

    # ── 판매 / 계절 ───────────────────────────────────────
    if any(k in m for k in ["판매", "매출", "잘팔리", "잘 팔리", "수요", "상위",
                              "여름", "봄", "가을", "겨울", "계절", "top"]):
        season = _detect_season(m)
        summary, ds = season_top_products(season, top_n=5)
        ctx.append(summary); datasets.extend(ds)

    # ── 재고 / 품절 ───────────────────────────────────────
    if any(k in m for k in ["재고", "inventory", "위험", "critical", "stock", "품절", "stockout"]):
        summary, ds = inventory_risk_summary()
        ctx.append(summary); datasets.extend(ds)

    # ── 발주 ─────────────────────────────────────────────
    if any(k in m for k in ["발주", "주문", "order", "replenishment"]):
        summary, ds = pending_orders_summary()
        ctx.append(summary); datasets.extend(ds)

    # ── 채널 ─────────────────────────────────────────────
    if "채널" in m:
        fig, ds = channel_sales_chart(recent_months=3)
        datasets.extend(ds)
        if fig:
            charts.append(fig)

    if not ctx and not charts:
        return ChatResult(
            text="관련 데이터를 찾을 수 없습니다. 다른 질문을 시도해보세요.",
            route="data",
        )

    if ctx:
        from modules.prompt_loader import load_prompt
        data_summary = "\n\n".join(ctx)
        prompt = load_prompt("chat_routing",
                             domain_context=domain_context,
                             data_summary=data_summary,
                             question=msg)
        text = claude.generate(prompt, max_tokens=1000)
    else:
        text = "차트를 생성했습니다."

    return ChatResult(text=text, route="data", charts=charts,
                      datasets=list(set(datasets)))


def _build_kg_context(msg: str, kg) -> tuple:
    """KG에서 노드/엣지 컨텍스트를 추출합니다. Returns (kg_context_str, kg_nodes_count)."""
    if not kg:
        return "", 0
    first_word = msg.split()[0] if msg.split() else ""
    result = kg.query_by_id(first_word)
    if not result["matched_nodes"]:
        return "", 0
    kg_nodes = len(result["matched_nodes"])
    nodes_str = ", ".join(f"{n.get('label', n.get('id',''))}({n.get('type','')})" for n in result["matched_nodes"][:5])
    edges_str = "; ".join(
        f"{e['source']}→{e['relation']}→{e['target']}" for e in result["edges"][:5])
    return f"[지식그래프]\n노드: {nodes_str}\n관계: {edges_str}\n\n", kg_nodes


def _handle_doc(msg: str, claude, rag, kg, domain_context: str) -> ChatResult:
    from modules.prompt_loader import load_prompt

    kg_context, kg_nodes = _build_kg_context(msg, kg)

    doc_files: List[str] = []
    rag_context = ""
    if rag:
        hits = rag.query(msg, n_results=4)
        if hits:
            doc_files   = list(dict.fromkeys(h["filename"] for h in hits))
            rag_context = "\n\n".join(f"[{h['filename']}]\n{h['text']}" for h in hits)

    combined = (kg_context + rag_context) or "관련 문서를 찾지 못했습니다."
    response = claude.generate(
        load_prompt("rag_query", question=msg, context=combined,
                    domain_context=domain_context),
        max_tokens=1000,
    )
    return ChatResult(text=response, route="doc",
                      documents=doc_files, kg_nodes=kg_nodes)


def _handle_combined(msg: str, claude, rag, kg, domain_context: str) -> ChatResult:
    from modules.data_analyst import season_top_products, inventory_risk_summary
    from concurrent.futures import ThreadPoolExecutor

    m             = msg.lower()
    charts        : List[Any] = []

    # 병렬로 RAG/KG/CSV 데이터 수집
    def _fetch_data():
        data_parts, datasets = [], []
        season = _detect_season(m)
        if season or any(k in m for k in ["판매", "매출", "수요"]):
            summary, ds = season_top_products(season, top_n=3)
            data_parts.append(summary); datasets.extend(ds)
        if any(k in m for k in ["재고", "품절"]):
            summary, ds = inventory_risk_summary()
            data_parts.append(summary); datasets.extend(ds)
        return data_parts, datasets

    def _fetch_rag():
        if not rag:
            return [], ""
        hits = rag.query(msg, n_results=3)
        if hits:
            doc_files = list(dict.fromkeys(h["filename"] for h in hits))
            rag_ctx = "\n\n".join(f"[{h['filename']}]\n{h['text']}" for h in hits)
            return doc_files, rag_ctx
        return [], ""

    def _fetch_kg():
        return _build_kg_context(msg, kg)

    with ThreadPoolExecutor(max_workers=3) as executor:
        f_data = executor.submit(_fetch_data)
        f_rag = executor.submit(_fetch_rag)
        f_kg = executor.submit(_fetch_kg)

    data_parts, all_datasets = f_data.result()
    doc_files, rag_context = f_rag.result()
    kg_prefix, kg_nodes = f_kg.result()

    data_section = "\n\n".join(data_parts)
    combined_ctx = "\n\n".join(filter(None, [data_section, kg_prefix + rag_context]))
    combined_ctx = combined_ctx or "관련 데이터를 찾지 못했습니다."

    prompt = (
        f"{domain_context}\n\n"
        f"[참고 데이터 및 문서]\n{combined_ctx}\n\n"
        f"[질문] {msg}\n\n"
        "데이터와 문서를 결합하여 종합적으로 답변하세요."
    )
    response = claude.generate(prompt, max_tokens=1200)
    return ChatResult(
        text=response, route="combined",
        charts=charts,
        datasets=list(set(all_datasets)),
        documents=doc_files,
        kg_nodes=kg_nodes,
    )


# ── 메인 진입점 ───────────────────────────────────────────────────────────────

def respond(msg: str, claude, rag, kg, domain_context: str) -> ChatResult:
    """사용자 질문 → ChatResult 반환 (라우팅 자동 결정)."""
    msg   = sanitize_input(msg)
    route = detect_route(msg)
    if route == "doc":
        return _handle_doc(msg, claude, rag, kg, domain_context)
    # data or combined → data_chat_engine 사용
    from modules.data_chat_engine import analyze
    answer = analyze(msg, claude=claude, rag=rag, kg=kg, domain_context=domain_context)
    text = ""
    if answer.summary:
        text = f"**{answer.summary}**\n\n"
    text += answer.interpretation or "관련 데이터를 찾을 수 없습니다."
    return ChatResult(
        text      = text,
        route     = route,
        charts    = answer.charts,
        datasets  = answer.datasets,
        documents = answer.documents,
        kg_nodes  = answer.kg_nodes,
        metrics   = answer.metrics,
    )


def respond_stream(msg: str, claude, rag, kg, domain_context: str):
    """스트리밍 응답 — 텍스트는 generator로, 나머지 메타는 ChatResult로 반환.
    Returns (text_generator, partial_result_fn)
    partial_result_fn()을 스트리밍 완료 후 호출하면 ChatResult(text='')를 반환합니다.
    """
    msg   = sanitize_input(msg)
    route = detect_route(msg)

    # doc 라우트는 RAG 컨텍스트 수집 후 스트리밍
    if route == "doc":
        from modules.prompt_loader import load_prompt
        kg_context, kg_nodes = "", 0
        if kg:
            first_word = msg.split()[0] if msg.split() else ""
            result = kg.query_by_id(first_word)
            if result["matched_nodes"]:
                kg_nodes = len(result["matched_nodes"])
                nodes_str = ", ".join(f"{n.get('label', n.get('id',''))}({n.get('type','')})" for n in result["matched_nodes"][:5])
                edges_str = "; ".join(
                    f"{e['source']}→{e['relation']}→{e['target']}" for e in result["edges"][:5])
                kg_context = f"[지식그래프]\n노드: {nodes_str}\n관계: {edges_str}\n\n"
        doc_files = []
        rag_context = ""
        if rag:
            hits = rag.query(msg, n_results=4)
            if hits:
                doc_files = list(dict.fromkeys(h["filename"] for h in hits))
                rag_context = "\n\n".join(f"[{h['filename']}]\n{h['text']}" for h in hits)
        combined = (kg_context + rag_context) or "관련 문서를 찾지 못했습니다."
        prompt = load_prompt("rag_query", question=msg, context=combined,
                             domain_context=domain_context)
        gen = claude.stream(prompt, max_tokens=1000)
        meta = ChatResult(text="", route="doc", documents=doc_files, kg_nodes=kg_nodes)
        return gen, meta

    # data / combined → 동기 처리 (pandas 분석 필요) 후 결과 반환
    result = respond(msg, claude, rag, kg, domain_context)
    def _text_gen():
        yield result.text
    return _text_gen(), ChatResult(
        text="", route=result.route, charts=result.charts,
        datasets=result.datasets, documents=result.documents,
        kg_nodes=result.kg_nodes, metrics=result.metrics,
    )
