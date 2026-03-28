"""
[역할] 업무 문장 → 필요한 데이터 자동 추천 엔진

3-pass 추천 로직:
  Pass 1 (rule)   : 키워드 매칭 → 후보 테이블 점수화
  Pass 2 (schema) : FK 연관 테이블 자동 확장 + Claude로 이유 정제
  Pass 3 (doc)    : RAG로 관련 문서 추천

모든 비즈니스 도메인(마케팅/커머스/공급망/글로벌/운영)에 적용 가능하도록
키워드 + 도메인 태그 기반으로 설계되어 있습니다.
"""
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ══════════════════════════════════════════════════════════════════════════════
# 스키마 레지스트리 (도메인 확장 가능)
# ══════════════════════════════════════════════════════════════════════════════

_SCHEMA_REGISTRY: Dict[str, Dict] = {
    "FACT_MONTHLY_SALES": {
        "description": "채널별 상품 월별 판매 실적",
        "csv_file":    "FACT_MONTHLY_SALES.csv",
        "key_columns": ["PRODUCT_ID", "CHANNEL_ID", "YEAR_MONTH", "NET_SALES_QTY", "SALES_AMOUNT"],
        "keywords":    ["판매", "매출", "sales", "판매량", "실적", "판매실적", "수요", "월별", "분기", "연간",
                        "top", "상위", "비교", "추이"],
        "domains":     ["sales", "marketing", "commerce"],
        "related":     ["MST_PRODUCT", "MST_CHANNEL"],
        "reason_template": "판매 실적·수량 데이터 필요",
    },
    "FACT_INVENTORY": {
        "description": "창고별 재고 스냅샷 (분기말 기준)",
        "csv_file":    "FACT_INVENTORY.csv",
        "key_columns": ["PRODUCT_ID", "STOCK_QTY", "SAFETY_STOCK_QTY", "STOCK_STATUS", "COVERAGE_WEEKS"],
        "keywords":    ["재고", "inventory", "stock", "재고현황", "보유량", "창고", "출하",
                        "프로모션 가능", "가용재고", "결품", "품절"],
        "domains":     ["inventory", "operations", "supply_chain"],
        "related":     ["MST_PRODUCT", "MST_LOCATION"],
        "reason_template": "재고 현황·가용 수량 확인 필요",
    },
    "MST_CHANNEL": {
        "description": "판매 채널 마스터 (온·오프라인, 글로벌)",
        "csv_file":    "MST_CHANNEL.csv",
        "key_columns": ["CHANNEL_ID", "CHANNEL_NAME", "CHANNEL_TYPE", "REGION"],
        "keywords":    ["채널", "틱톡", "쿠팡", "네이버", "오프라인", "온라인", "글로벌", "해외",
                        "플랫폼", "D2C", "이커머스", "SEA", "미국"],
        "domains":     ["sales", "marketing", "commerce"],
        "related":     ["FACT_MONTHLY_SALES"],
        "reason_template": "채널 식별·매핑 필요",
    },
    "MST_PRODUCT": {
        "description": "상품 마스터 (SKU·카테고리·시즌·라이프사이클)",
        "csv_file":    "MST_PRODUCT.csv",
        "key_columns": ["PRODUCT_ID", "PRODUCT_NAME", "CATEGORY", "SEASONAL_PEAK", "STATUS"],
        "keywords":    ["상품", "제품", "sku", "선크림", "립스틱", "스킨케어", "화장품",
                        "카테고리", "시즌", "신제품", "단종", "성장기", "성숙기", "세럼",
                        "에센스", "클렌징", "마스크"],
        "domains":     ["product", "marketing", "commerce"],
        "related":     ["MST_SUPPLIER", "FACT_MONTHLY_SALES", "FACT_INVENTORY"],
        "reason_template": "상품 정보·SKU 매핑 필요",
    },
    "MST_SUPPLIER": {
        "description": "원료·용기 공급업체 마스터",
        "csv_file":    "MST_SUPPLIER.csv",
        "key_columns": ["SUPPLIER_ID", "SUPPLIER_NAME", "LEAD_TIME_DAYS", "MOQ"],
        "keywords":    ["공급업체", "supplier", "납품", "납기", "리드타임", "lead time",
                        "moq", "원료", "용기", "외주"],
        "domains":     ["supply_chain", "procurement"],
        "related":     ["MST_PRODUCT"],
        "reason_template": "공급업체 리드타임·MOQ 확인 필요",
    },
    "FACT_REPLENISHMENT_ORDER": {
        "description": "발주·입고 이력 (PENDING/IN_TRANSIT/DELIVERED)",
        "csv_file":    "FACT_REPLENISHMENT_ORDER.csv",
        "key_columns": ["PART_CD", "ORDER_DT", "ORDER_QTY", "STATUS", "DELAY_DAYS"],
        "keywords":    ["발주", "주문", "입고", "order", "replenishment", "납기",
                        "지연", "딜레이", "발주량"],
        "domains":     ["supply_chain", "procurement", "operations"],
        "related":     ["MST_PART", "MST_SUPPLIER"],
        "reason_template": "발주·입고 현황 및 납기 지연 확인 필요",
    },
    "FACT_STOCKOUT_EVENT": {
        "description": "품절 이벤트 이력 (기간·손실 판매량·원인)",
        "csv_file":    "FACT_STOCKOUT_EVENT.csv",
        "key_columns": ["PART_CD", "STOCKOUT_YM", "DURATION_DAYS", "LOST_SALES_QTY", "CAUSE_CODE"],
        "keywords":    ["품절", "stockout", "결품", "재고 없음", "손실", "lost sales", "기회손실"],
        "domains":     ["inventory", "operations", "supply_chain"],
        "related":     ["MST_PART"],
        "reason_template": "품절 이력·손실 판매량 분석 필요",
    },
    "MST_PART": {
        "description": "완제품·원자재 Part 마스터 (FG-XXX 코드 기준)",
        "csv_file":    "MST_PART.csv",
        "key_columns": ["PART_CD", "PART_NAME", "PART_TYPE", "LINKED_PRODUCT_ID", "UNIT_COST_KRW"],
        "keywords":    ["파트", "part", "완제품", "fg-", "부품", "단가", "원가", "bom"],
        "domains":     ["product", "supply_chain", "procurement"],
        "related":     ["MST_PRODUCT", "FACT_REPLENISHMENT_ORDER"],
        "reason_template": "Part 코드·원가 매핑 필요",
    },
    "FACT_MONTHLY_DEMAND": {
        "description": "월별 수요 예측 vs 실적 비교",
        "csv_file":    "FACT_MONTHLY_DEMAND.csv",
        "key_columns": ["PRODUCT_ID", "YEAR_MONTH", "FORECAST_QTY", "ACTUAL_QTY"],
        "keywords":    ["수요예측", "forecast", "예측", "수요", "계획 대비", "달성률",
                        "S&OP", "수요계획"],
        "domains":     ["demand_planning", "operations"],
        "related":     ["MST_PRODUCT"],
        "reason_template": "수요 예측 vs 실적 비교 필요",
    },
    "MST_LOCATION": {
        "description": "창고·거점 위치 마스터",
        "csv_file":    "MST_LOCATION.csv",
        "key_columns": ["LOCATION_ID", "LOCATION_NAME", "LOCATION_TYPE", "REGION"],
        "keywords":    ["창고", "location", "거점", "물류센터", "지역", "위치", "센터"],
        "domains":     ["logistics", "operations"],
        "related":     ["FACT_INVENTORY"],
        "reason_template": "창고·거점 위치 식별 필요",
    },
    "MST_WAREHOUSE": {
        "description": "창고 운영 정보 (용량·운영사)",
        "csv_file":    "MST_WAREHOUSE.csv",
        "key_columns": ["WAREHOUSE_ID", "WAREHOUSE_NAME", "CAPACITY"],
        "keywords":    ["창고", "warehouse", "용량", "적재", "보관", "3PL"],
        "domains":     ["logistics", "operations"],
        "related":     ["MST_LOCATION"],
        "reason_template": "창고 용량·운영 정보 확인 필요",
    },
    "MST_OFFICE": {
        "description": "법인·오피스 마스터",
        "csv_file":    "MST_OFFICE.csv",
        "key_columns": ["OFFICE_CD", "OFFICE_NAME", "COUNTRY"],
        "keywords":    ["법인", "office", "지사", "국가", "글로벌", "해외법인"],
        "domains":     ["global", "operations"],
        "related":     ["FACT_REPLENISHMENT_ORDER"],
        "reason_template": "법인·오피스 코드 매핑 필요",
    },
    "MST_SUPPLY_ROUTE": {
        "description": "공급 루트 마스터 (공급업체→법인 경로)",
        "csv_file":    "MST_SUPPLY_ROUTE.csv",
        "key_columns": ["ROUTE_ID", "SUPPLIER_ID", "OFFICE_CD", "LEAD_TIME_DAYS"],
        "keywords":    ["공급루트", "supply route", "루트", "납품경로", "운송", "routing"],
        "domains":     ["supply_chain", "logistics"],
        "related":     ["MST_SUPPLIER", "MST_OFFICE"],
        "reason_template": "공급 경로·리드타임 확인 필요",
    },
    "FACT_INVENTORY_SNAPSHOT": {
        "description": "재고 스냅샷 상세 이력 (일별·주별)",
        "csv_file":    "FACT_INVENTORY_SNAPSHOT.csv",
        "key_columns": ["PRODUCT_ID", "SNAPSHOT_DATE", "STOCK_QTY"],
        "keywords":    ["재고 이력", "스냅샷", "snapshot", "재고 변동", "추이"],
        "domains":     ["inventory", "operations"],
        "related":     ["MST_PRODUCT"],
        "reason_template": "재고 변동 이력·추세 분석 필요",
    },
}

# ── 엔티티 패턴 (도메인 확장 가능) ───────────────────────────────────────────
_ENTITY_PATTERNS: Dict[str, List[str]] = {
    "channel":   ["틱톡샵", "틱톡", "tiktok", "쿠팡", "coupang", "네이버", "naver",
                  "오프라인", "온라인", "D2C", "로컬", "글로벌"],
    "product":   ["선크림", "sun", "spf", "립스틱", "클렌징", "스킨케어", "에센스",
                  "세럼", "마스크팩", "토너", "로션", "크림", "파운데이션"],
    "geography": ["글로벌", "해외", "국내", "KR", "US", "SEA", "동남아", "미국", "유럽"],
    "time":      ["작년", "올해", "이번", "다음", "분기", "상반기", "하반기",
                  "동기", "전년", "YoY", "MoM", "전월", "전분기", "월별", "연간"],
    "operation": ["프로모션", "promotion", "캠페인", "마케팅", "기획전", "할인",
                  "발주", "입고", "출고", "재고보충"],
}

# ── 시간 표현 정규식 ──────────────────────────────────────────────────────────
_TIME_RE = re.compile(
    r"(\d{4}년|\d+월|\d+분기|작년|올해|이번\s*분기|다음\s*분기|"
    r"상반기|하반기|전년|동기|최근\s*\d+[개월분기년])"
)


# ══════════════════════════════════════════════════════════════════════════════
# 데이터 클래스
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class DatasetRecommendation:
    table_name:       str
    csv_file:         str
    description:      str
    key_columns:      List[str]
    reason:           str
    confidence:       float          # 0.0–1.0
    matched_keywords: List[str]
    is_expanded:      bool = False   # FK 체인으로 추가된 경우 True


@dataclass
class QueryPlan:
    raw_input:        str
    intent:           str            # 업무 의도 요약
    entities:         Dict[str, List[str]]
    time_expressions: List[str]
    datasets:         List[DatasetRecommendation]
    documents:        List[str]      # RAG 추천 문서 파일명


# ══════════════════════════════════════════════════════════════════════════════
# Pass 1: 키워드/rule 기반 스코어링
# ══════════════════════════════════════════════════════════════════════════════

def _keyword_score(text: str, keywords: List[str]) -> Tuple[float, List[str]]:
    """텍스트에서 키워드 매칭 점수 계산. Returns (score, matched_list)"""
    tl     = text.lower()
    matched = [kw for kw in keywords if kw.lower() in tl]
    score   = min(len(matched) / max(len(keywords) * 0.3, 1), 1.0)
    return score, matched


def _extract_entities(text: str) -> Dict[str, List[str]]:
    entities: Dict[str, List[str]] = {}
    for etype, patterns in _ENTITY_PATTERNS.items():
        found = [p for p in patterns if p.lower() in text.lower()]
        if found:
            entities[etype] = list(dict.fromkeys(found))  # unique, ordered
    return entities


def _extract_time_expressions(text: str) -> List[str]:
    return list(dict.fromkeys(_TIME_RE.findall(text)))


def _pass1_rule(text: str) -> List[Tuple[str, float, List[str]]]:
    """Returns [(table_name, score, matched_keywords), ...] sorted by score desc"""
    results = []
    for tname, meta in _SCHEMA_REGISTRY.items():
        score, matched = _keyword_score(text, meta["keywords"])
        if score > 0 or matched:
            results.append((tname, score, matched))
    results.sort(key=lambda x: x[1], reverse=True)
    return results


# ══════════════════════════════════════════════════════════════════════════════
# Pass 2: FK 체인 확장 + 이유 정제 (Claude 선택적 사용)
# ══════════════════════════════════════════════════════════════════════════════

def _expand_via_fk(
    scored: List[Tuple[str, float, List[str]]]
) -> List[Tuple[str, float, List[str], bool]]:
    """
    직접 매칭된 테이블의 related 테이블을 낮은 confidence로 추가합니다.
    Returns [(table_name, score, matched, is_expanded), ...]
    """
    included   = {t for t, _, _ in scored}
    expanded   = [(t, s, m, False) for t, s, m in scored]
    to_add     = {}

    for tname, score, matched in scored:
        meta = _SCHEMA_REGISTRY.get(tname, {})
        for rel in meta.get("related", []):
            if rel not in included and rel not in to_add:
                to_add[rel] = score * 0.5  # FK 연관 테이블은 50% confidence

    for rel_name, rel_score in to_add.items():
        if rel_name in _SCHEMA_REGISTRY:
            expanded.append((rel_name, rel_score, [], True))

    expanded.sort(key=lambda x: x[1], reverse=True)
    return expanded


def _build_reason_rule(
    table_name: str, matched: List[str], entities: Dict[str, List[str]], is_expanded: bool
) -> str:
    """규칙 기반 이유 생성 (Claude fallback용)"""
    meta        = _SCHEMA_REGISTRY.get(table_name, {})
    base_reason = meta.get("reason_template", f"{table_name} 데이터 필요")

    extras = []
    if entities.get("channel"):
        ch = entities["channel"][0]
        if table_name == "MST_CHANNEL":
            extras.append(f"'{ch}' 채널 식별")
        elif table_name == "FACT_MONTHLY_SALES":
            extras.append(f"'{ch}' 채널 판매 실적 조회")
    if entities.get("product"):
        prod = entities["product"][0]
        if table_name in ("MST_PRODUCT", "MST_PART"):
            extras.append(f"'{prod}' 상품 매핑")
        elif table_name == "FACT_INVENTORY":
            extras.append(f"'{prod}' 재고 확인")
    if entities.get("time") and table_name.startswith("FACT_"):
        extras.append("기간별 필터링")
    if is_expanded:
        extras.append("FK 연관 조회 필요")

    if extras:
        return f"{base_reason} ({'; '.join(extras)})"
    if matched:
        return f"{base_reason} (매칭: {', '.join(matched[:3])})"
    return base_reason


def _pass2_refine_with_claude(
    text: str,
    candidates: List[Tuple[str, float, List[str], bool]],
    entities: Dict[str, List[str]],
    claude,
    domain_context: str,
) -> Dict[str, str]:
    """
    Claude를 사용해 각 테이블의 추천 이유를 자연어로 정제합니다.
    Returns {table_name: refined_reason}
    """
    # 스키마 요약 구성
    schema_lines = []
    for tname, score, matched, is_exp in candidates[:8]:  # 상위 8개만
        meta = _SCHEMA_REGISTRY.get(tname, {})
        cols = ", ".join(meta.get("key_columns", [])[:4])
        schema_lines.append(f"- {tname}: {meta.get('description', '')} (주요 컬럼: {cols})")

    schema_summary = "\n".join(schema_lines)
    entity_summary = "; ".join(
        f"{k}: {', '.join(v)}" for k, v in entities.items()
    )

    prompt = f"""{domain_context}

[업무 문장]
{text}

[추출된 엔티티]
{entity_summary or "없음"}

[추천 데이터셋 후보]
{schema_summary}

각 데이터셋이 왜 이 업무에 필요한지 1줄로 설명하세요.
형식 (JSON):
{{
  "FACT_MONTHLY_SALES": "이유",
  "MST_CHANNEL": "이유",
  ...
}}
JSON만 출력하세요."""

    try:
        response = claude.generate(prompt, max_tokens=800)
        # JSON 파싱
        import json
        # 코드블록 제거
        clean = re.sub(r"```(?:json)?\s*([\s\S]*?)```", r"\1", response).strip()
        json_match = re.search(r"\{[\s\S]*\}", clean)
        if json_match:
            return json.loads(json_match.group())
    except Exception:
        pass
    return {}


# ══════════════════════════════════════════════════════════════════════════════
# Pass 3: RAG 문서 추천
# ══════════════════════════════════════════════════════════════════════════════

def _pass3_doc_recommend(text: str, rag) -> List[str]:
    """RAG로 관련 문서 파일명 추천"""
    try:
        hits = rag.query(text, n_results=3)
        return list(dict.fromkeys(h["filename"] for h in hits))
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# 메인 진입점
# ══════════════════════════════════════════════════════════════════════════════

def plan(
    text: str,
    rag=None,
    kg=None,
    claude=None,
    domain_context: str = "",
    top_n: int = 6,
) -> QueryPlan:
    """
    업무 문장 → QueryPlan 반환.
    rag/claude가 None이어도 Pass1(rule) 결과로 동작합니다.
    """
    entities         = _extract_entities(text)
    time_expressions = _extract_time_expressions(text)

    # ── Pass 1 ───────────────────────────────────────────────────────────────
    scored = _pass1_rule(text)

    # ── Pass 2a: FK 확장 ─────────────────────────────────────────────────────
    candidates = _expand_via_fk(scored)
    candidates = candidates[:top_n]

    # ── Pass 2b: Claude 이유 정제 (optional) ─────────────────────────────────
    refined_reasons: Dict[str, str] = {}
    if claude and candidates:
        refined_reasons = _pass2_refine_with_claude(
            text, candidates, entities, claude, domain_context
        )

    # ── DatasetRecommendation 구성 ───────────────────────────────────────────
    datasets: List[DatasetRecommendation] = []
    for tname, score, matched, is_exp in candidates:
        meta = _SCHEMA_REGISTRY.get(tname, {})
        reason = (
            refined_reasons.get(tname)
            or _build_reason_rule(tname, matched, entities, is_exp)
        )
        datasets.append(DatasetRecommendation(
            table_name       = tname,
            csv_file         = meta.get("csv_file", f"{tname}.csv"),
            description      = meta.get("description", ""),
            key_columns      = meta.get("key_columns", []),
            reason           = reason,
            confidence       = round(score, 2),
            matched_keywords = matched,
            is_expanded      = is_exp,
        ))

    # ── Pass 3: 문서 추천 ─────────────────────────────────────────────────────
    doc_files = _pass3_doc_recommend(text, rag) if rag else []

    # ── 의도 요약 ─────────────────────────────────────────────────────────────
    intent = _summarize_intent(text, entities, time_expressions)

    return QueryPlan(
        raw_input        = text,
        intent           = intent,
        entities         = entities,
        time_expressions = time_expressions,
        datasets         = datasets,
        documents        = doc_files,
    )


def _summarize_intent(
    text: str,
    entities: Dict[str, List[str]],
    time_expressions: List[str],
) -> str:
    """간단한 rule 기반 의도 요약"""
    parts = []
    if entities.get("channel"):
        parts.append(f"채널: {', '.join(entities['channel'][:2])}")
    if entities.get("product"):
        parts.append(f"상품: {', '.join(entities['product'][:2])}")
    if time_expressions:
        parts.append(f"기간: {', '.join(time_expressions[:2])}")
    if entities.get("operation"):
        parts.append(f"업무: {', '.join(entities['operation'][:2])}")

    base = text[:60].rstrip() + ("..." if len(text) > 60 else "")
    return f"{base}  [{', '.join(parts)}]" if parts else base
