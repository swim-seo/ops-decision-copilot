"""
[역할] Streamlit 메인 앱 (v2 - 3단계 UI)
파일을 올리면 시스템 구조를 자동으로 파악합니다.
Step1 도메인설정 → Step2 파일업로드 → Step3 결과(KG+AI분석)
"""
import os
import time
import json as _json
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from config import APP_TITLE, APP_ICON, DEFAULT_ENTITY_COLORS

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 운영 코파일럿",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
def _apply_css(primary: str = "#2563EB"):
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp {{ background:#f8fafc; font-family:'Inter',sans-serif; }}
.app-header {{ text-align:center; padding:2rem 0 .5rem; }}
.app-header h1 {{ font-family:'Inter',sans-serif; font-size:1.7rem;
                  color:#0f172a; margin:0 0 .3rem; letter-spacing:-.03em; font-weight:700; }}
.app-header p  {{ font-size:.9rem; color:#64748b; margin:0; font-weight:400; }}
.steps {{ display:flex; justify-content:center; align-items:center;
          margin:1rem 0 1.8rem; gap:0; }}
.step  {{ display:flex; flex-direction:column; align-items:center; width:150px; }}
.s-dot {{ width:30px; height:30px; border-radius:50%; display:flex;
          align-items:center; justify-content:center; font-weight:600;
          font-size:.82rem; background:white; color:#94a3b8;
          border:2px solid #e2e8f0; }}
.s-dot.active {{ background:{primary}; color:white; border-color:{primary}; }}
.s-dot.done   {{ background:{primary}; color:white; border-color:{primary}; }}
.s-lbl {{ font-size:.68rem; color:#94a3b8; margin-top:.25rem; font-weight:500; }}
.s-lbl.active {{ color:{primary}; font-weight:600; }}
.s-line {{ flex:1; height:2px; background:#e2e8f0; margin-bottom:1rem; max-width:65px; }}
.s-line.done {{ background:{primary}; }}
.card {{ background:white; border-radius:8px; padding:1.2rem;
         box-shadow:0 1px 3px rgba(0,0,0,.05); border:1px solid #e2e8f0;
         margin-bottom:.8rem; }}
.dom-banner {{ background:{primary}08; border:1px solid {primary}33;
               border-radius:6px; padding:.9rem 1.2rem; margin:.8rem 0;
               font-size:.95rem; }}
.stButton>button {{ border-radius:6px !important; font-weight:500 !important;
                    font-size:.85rem !important; transition:all .1s !important; }}
div[data-testid="metric-container"] {{
  background:white; border-radius:6px;
  border:1px solid #e2e8f0; border-left:3px solid {primary};
  padding:.4rem .6rem; overflow:visible; min-width:0; }}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {{
  font-size:1.05rem !important; overflow:visible; white-space:nowrap; }}
div[data-testid="metric-container"] [data-testid="stMetricLabel"] {{
  font-size:.68rem !important; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }}
.stTabs [data-baseweb="tab"] {{ color:#64748b; font-weight:500; font-size:.875rem; }}
.stTabs [aria-selected="true"] {{ border-bottom:2px solid {primary}; color:{primary}; font-weight:600; }}
[data-testid="stFileUploader"] {{
  border:1.5px dashed #cbd5e1; border-radius:8px; background:white; }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:4px;
          font-size:.75em; font-weight:600; margin:2px; }}
section[data-testid="stSidebar"] {{ background:#f8fafc !important;
  border-right:1px solid #e2e8f0 !important;
  width:380px !important; min-width:380px !important; }}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {{ color:#1e293b !important; }}
section[data-testid="stSidebar"] .stButton>button {{
  background:white !important; color:#334155 !important;
  border:1px solid #e2e8f0 !important; font-size:.8rem !important; }}
</style>""", unsafe_allow_html=True)


# ── 도메인 프리셋 (domains/ 패키지에서 로드) ─────────────────────────────────
from domains import ALL_PRESETS as _PRESETS

# ── 도메인별 채팅 예시 질문 ────────────────────────────────────────────────────
_DOMAIN_CHAT_PRESETS = {
    # ── beauty_ecommerce ─────────────────────────────────────────────────────
    # 실제 데이터: 클린잇제로 클렌징밤(PRD001), 선프로텍터 선크림 SPF50+(PRD002),
    #              인텐시브 수분크림(PRD003), 앰플 에센스(PRD005) / 채널 CH001=틱톡샵_KR
    #              컬럼: SALES_QTY, NET_SALES_QTY, STOCK_QTY, SAFETY_STOCK_QTY, COVERAGE_WEEKS
    "뷰티": [
        ("선프로텍터 선크림(PRD002) 월별 판매량 그래프",
         "선프로텍터 선크림 SPF50+(PRD002) 2024년 월별 SALES_QTY 추이 그래프 그려줘"),
        ("COVERAGE_WEEKS 기준 재고 부족 위험 제품 순위",
         "COVERAGE_WEEKS 기준으로 재고 부족 위험이 높은 제품 순위 알려줘. SAFETY_STOCK_QTY 대비 현황도 포함해줘"),
        ("클린잇제로 클렌징밤 틱톡샵 채널 순매출 분석",
         "클린잇제로 클렌징밤(PRD001) CH001 틱톡샵 채널의 NET_SALES_QTY 추이 분석하고 RETURN_QTY 비율도 알려줘"),
        ("여름 시즌 SEASONAL_PEAK 제품 재고 현황 비교",
         "SEASONAL_PEAK가 '여름'인 제품들의 현재 STOCK_QTY와 REORDER_POINT 비교해서 시즌 대비 준비 현황 알려줘"),
    ],
    # ── supply_chain ─────────────────────────────────────────────────────────
    # 실제 데이터: 엔진블록 어셈블리(PT001), 트랜스미션 어셈블리(PT002),
    #              터보차저(PT003), ECU 제어모듈(PT004), 인젝터 세트(PT005)
    #              컬럼: STOCK_QTY, REORDER_POINT, INVENTORY_VALUE_KRW, DELAY_DAYS, ORDER_TYPE
    "공급망": [
        ("엔진블록 어셈블리(PT001) 창고별 재고 현황",
         "엔진블록 어셈블리(PT001) 창고별 STOCK_QTY 현황 보여줘. SAFETY_STOCK_QTY 대비 위험도도 분석해줘"),
        ("DELAY_DAYS 기준 납기 지연 발주 현황",
         "DELAY_DAYS가 가장 긴 발주 건 TOP5와 해당 부품·공급업체 알려줘. 반복 지연 패턴이 있는지도 확인해줘"),
        ("터보차저(PT003) 재발주점 도달 여부 확인",
         "터보차저(PT003) 현재 STOCK_QTY가 REORDER_POINT에 도달했는지 확인하고 긴급 발주 필요 여부 알려줘"),
        ("A급 부품 재고 금액 및 회전율 분석",
         "PART_CLASS가 A인 부품들의 INVENTORY_VALUE_KRW 총액과 창고별 분포, 재고 회전율 분석해줘"),
    ],
    # ── energy ───────────────────────────────────────────────────────────────
    # 실제 데이터: 서울화력(PLT001), 영동원자력(PLT002), 전남태양광단지(PLT004), 제주풍력(PLT005)
    #              서울강남산업단지(MTR001), 수원전자공단(MTR003)
    #              컬럼: USAGE_KWH, PEAK_KW, OFFPEAK_KW, POWER_FACTOR, IS_PEAK_DAY
    "에너지": [
        ("서울강남산업단지(MTR001) 월별 전력 소비 추이",
         "서울강남산업단지(MTR001) 월별 USAGE_KWH 소비 추이 그래프 그려줘. IS_PEAK_DAY 일수도 함께 표시해줘"),
        ("수원전자공단 피크 전력 TOP5 일자",
         "수원전자공단(MTR003) PEAK_KW가 가장 높은 날 TOP5 알려줘. 해당 날의 OFFPEAK_KW와 비교도 해줘"),
        ("전남태양광 vs 제주풍력 발전 설비 비교",
         "전남태양광단지(PLT004)와 제주풍력(PLT005) CAPACITY_MW와 CO2_EMISSION_FACTOR 비교해서 친환경 효율 분석해줘"),
        ("역률(POWER_FACTOR) 0.9 이하 계량기 현황",
         "POWER_FACTOR가 0.9 이하인 계량기 목록과 해당 고객사 알려줘. 역률 개선 우선순위도 제안해줘"),
    ],
    # ── manufacturing ────────────────────────────────────────────────────────
    # 실제 데이터: 엔진블록_V6(PRD001), 크랭크샤프트(PRD002), 실린더헤드(PRD003)
    #              CNC선반_A1(EQP001), 프레스_B1(EQP003), 용접로봇_C1(EQP004)
    #              컬럼: PLANNED_OUTPUT, ACTUAL_OUTPUT, UTILIZATION_RATE_PCT, DOWNTIME_HOURS, YIELD_RATE_PCT
    "제조": [
        ("엔진블록_V6(PRD001) LINE-01 생산 달성률 그래프",
         "엔진블록_V6(PRD001) LINE-01의 ACTUAL_OUTPUT/PLANNED_OUTPUT 생산 달성률 추이 그래프 그려줘. SHIFT별로 구분해줘"),
        ("CNC선반_A1 다운타임 원인 분석",
         "CNC선반_A1(EQP001) DOWNTIME_HOURS를 DOWNTIME_REASON별로 분류해서 주요 원인 TOP3 알려줘"),
        ("YIELD_RATE_PCT 기준 불량률 높은 라인·제품 TOP3",
         "YIELD_RATE_PCT 기준으로 불량률이 가장 높은 라인과 제품 TOP3 알려줘. DEFECT_THRESHOLD_PCT 초과 여부도 확인해줘"),
        ("용접로봇_C1(EQP004) 가동률 주간 추이",
         "용접로봇_C1(EQP004) UTILIZATION_RATE_PCT 주간 추이 보여줘. OEE_TARGET_PCT 대비 달성 여부도 분석해줘"),
    ],
    # ── logistics ────────────────────────────────────────────────────────────
    # 실제 데이터: 서울→부산 간선(RTE001), 서울→대구 간선(RTE002), 서울→광주 간선(RTE003)
    #              5톤트럭 002호(VHC002), 5톤트럭 003호(VHC003)
    #              컬럼: DELIVERY_SUCCESS_COUNT, DELIVERY_FAIL_COUNT, FAIL_REASON, PACKAGE_COUNT
    "물류": [
        ("서울→부산 간선(RTE001) 배송 성공률 추이",
         "서울→부산 간선(RTE001) 월별 DELIVERY_SUCCESS_COUNT와 DELIVERY_FAIL_COUNT 추이 그래프 그려줘"),
        ("5톤트럭 002호(VHC002) 배송 실패 원인 분석",
         "5톤트럭 002호(VHC002) DELIVERY_FAIL_COUNT와 FAIL_REASON 현황 알려줘. 반복 실패 패턴도 확인해줘"),
        ("DISTANCE_KM 대비 비효율 노선 탐지",
         "DISTANCE_KM 대비 STANDARD_TIME_HOURS 비율이 높은 비효율 노선 TOP3 찾아줘. 개선 방안도 제안해줘"),
        ("HUB001 출발 PACKAGE_COUNT 월별 트렌드",
         "HUB001 출발 배송의 PACKAGE_COUNT 월별 트렌드 분석하고 물동량 증감 패턴 알려줘"),
    ],
    # ── finance ──────────────────────────────────────────────────────────────
    # 실제 데이터: 정기예금(1년)(PRD001), 자유적금(PRD003), 주택담보대출(PRD004), 신용대출(PRD005)
    #              CUS001(VVIP/40대/서울), CUS002(VIP/30대/경기)
    #              컬럼: AMOUNT_KRW, BALANCE_AFTER_KRW, IS_ANOMALY, ANOMALY_TYPE, CREDIT_SCORE
    "금융": [
        ("정기예금(1년)(PRD001) 월별 가입 금액 추이",
         "정기예금(1년)(PRD001) 월별 가입 건수와 AMOUNT_KRW 총액 추이 그래프 그려줘. 채널별 비중도 포함해줘"),
        ("이상 거래(IS_ANOMALY) 유형별 분포 분석",
         "IS_ANOMALY가 True인 거래의 ANOMALY_TYPE별 건수·금액 분포 알려줘. 고위험 유형 TOP3도 강조해줘"),
        ("VVIP·VIP 고객 자산 및 신용점수 현황",
         "CUSTOMER_GRADE가 VVIP·VIP인 고객의 평균 CREDIT_SCORE와 TOTAL_ASSETS_MILLION_KRW 현황 비교해줘"),
        ("신용대출(PRD005) CREDIT_SCORE 구간별 잔액",
         "신용대출(PRD005) CREDIT_SCORE 구간별 잔액(BALANCE_AFTER_KRW) 분포와 연체 위험 고객 비율 분석해줘"),
    ],
}
_DEFAULT_CHAT_PRESETS = [
    ("핵심 데이터 현황 분석해줘",  "핵심 데이터 현황 분석해줘"),
    ("현재 위험 요소 알려줘",    "현재 위험 요소 알려줘"),
    ("상위 항목 TOP3 알려줘",   "상위 항목 TOP3 알려줘"),
    ("카테고리별 현황 비교해줘",  "카테고리별 현황 비교해줘"),
]

def _get_chat_presets() -> list:
    """현재 도메인에 맞는 채팅 예시 질문 목록을 반환합니다."""
    dc = st.session_state.get("domain_config")
    if not dc:
        return _DEFAULT_CHAT_PRESETS
    name = dc.get("name", "")
    for key, presets in _DOMAIN_CHAT_PRESETS.items():
        if key in name:
            return presets
    return _DEFAULT_CHAT_PRESETS

_DEFAULT_DOMAIN_CONTEXT = (
    "도메인: 일반 비즈니스\n핵심 용어: 전략, 목표, 성과, 리스크, 의사결정\n"
    "주요 문서: 회의록, 보고서, 정책 문서\n분석 포커스: 핵심 의사결정, 리스크, 성과 지표"
)


# ── 세션 초기화 ───────────────────────────────────────────────────────────────
def _init_session():
    defaults = {
        "documents": {}, "rag": None, "claude": None, "kg": None,
        "api_ok": False, "domain_config": None,
        "step": 1,
        "domain_suggestion": None,
        "suggest_countdown": None,
        "chat_history": [],
        "chat_api_calls": 0,
        "chat_preset_input": None,
        "pending_chat_message": None,
        "qp_input": "",
        "qp_result": None,
        "briefing_cards": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_session()


# ── 헬퍼: 도메인 ─────────────────────────────────────────────────────────────
def _get_domain_context() -> str:
    dc = st.session_state.get("domain_config")
    if dc:
        from modules.domain_adapter import DomainConfig
        return DomainConfig.from_dict(dc).to_context_string()
    return _DEFAULT_DOMAIN_CONTEXT

def _get_entity_colors() -> dict:
    dc = st.session_state.get("domain_config")
    if dc:
        return dc.get("entity_types", DEFAULT_ENTITY_COLORS)
    return DEFAULT_ENTITY_COLORS

def _get_theme_color() -> str:
    dc = st.session_state.get("domain_config")
    if dc:
        return dc.get("theme_color", "#2563EB")
    return "#2563EB"

def _get_collection_name() -> str:
    dc = st.session_state.get("domain_config")
    if dc:
        from modules.domain_adapter import DomainConfig
        return DomainConfig.from_dict(dc).collection_name
    from config import DEFAULT_COLLECTION_NAME
    return DEFAULT_COLLECTION_NAME

def _quick_detect_domain(file_names: list) -> str:
    names = " ".join(file_names).upper()
    if any(k in names for k in ["REPLENISH","SUPPLY_ROUTE","OFFICE","PART","STOCKOUT"]):
        return "공급망·재고 관리"
    if any(k in names for k in ["PRODUCT","SALES","CHANNEL","SKU"]):
        if any(k in names for k in ["INVENTORY","SUPPLY","ORDER","WAREHOUSE"]):
            return "공급망·재고 관리"
        return "이커머스"
    if any(k in names for k in ["PATIENT","MEDICAL","HOSPITAL","DRUG"]):
        return "의료·헬스케어"
    if any(k in names for k in ["FINANCE","BUDGET","REVENUE","ACCOUNT"]):
        return "금융·회계"
    if any(k in names for k in ["FACTORY","PRODUCTION","MACHINE","DEFECT"]):
        return "제조·생산"
    if any(k in names for k in ["DELIVER","LOGISTIC","ROUTE","SHIPMENT"]):
        return "물류"
    return "비즈니스 운영"

def _preset_for(name: str) -> dict:
    from domains import get_preset
    return get_preset(name)

def _build_domain_from_name(name: str):
    from modules.domain_adapter import DomainConfig
    p = _preset_for(name)
    return DomainConfig(
        name=name, description=f"{name} 도메인 운영 문서 분석",
        entity_types=p["entity_types"], terminology=p["terminology"],
        document_patterns=p["document_patterns"], analysis_focus=p["analysis_focus"],
        theme_color=p["theme_color"], app_title=f"{name} AI 코파일럿",
        app_icon=p["app_icon"],
    )


# ── 헬퍼: 모듈 로딩 ──────────────────────────────────────────────────────────
def _load_modules() -> bool:
    try:
        from modules.claude_client import ClaudeClient
        from modules.rag_engine import RAGEngine
        from modules.knowledge_graph import KnowledgeGraph

        if st.session_state.claude is None:
            st.session_state.claude = ClaudeClient()
            st.session_state.api_ok = True

        desired_col = _get_collection_name()
        current_col = getattr(st.session_state.rag, "collection_name", None)
        if st.session_state.rag is None or current_col != desired_col:
            st.session_state.rag = RAGEngine(collection_name=desired_col)

        if st.session_state.kg is None:
            st.session_state.kg = KnowledgeGraph()
        return True
    except Exception as e:
        st.error(f"❌ 초기화 실패: {e}")
        return False


# ── 헬퍼: 파일 처리 ──────────────────────────────────────────────────────────
def _schema_to_text(schema: dict) -> str:
    lines = []
    tables = schema.get("tables", {})
    # tables가 dict인 경우 (SCHEMA_DEFINITION.json 형식)
    if isinstance(tables, dict):
        for tname, tinfo in tables.items():
            desc = tinfo.get("description", "") if isinstance(tinfo, dict) else ""
            lines.append(f"[테이블] {tname} — {desc}")
            cols = tinfo.get("columns", {}) if isinstance(tinfo, dict) else {}
            if isinstance(cols, dict):
                for cname, cinfo in cols.items():
                    pk = " (PK)" if cname == tinfo.get("primary_key") else ""
                    ctype = cinfo.get("type", "") if isinstance(cinfo, dict) else ""
                    lines.append(f"  컬럼: {cname} ({ctype}){pk}")
            else:
                for c in cols:
                    pk = " (PK)" if c.get("pk") else ""
                    lines.append(f"  컬럼: {c['name']} ({c.get('type','')}){pk}")
    # tables가 list인 경우 (기존 형식)
    else:
        for t in tables:
            lines.append(f"[테이블] {t['table_name']} — {t.get('description','')}")
            for c in t.get("columns", []):
                pk = " (PK)" if c.get("pk") else ""
                lines.append(f"  컬럼: {c['name']} ({c.get('type','')}){pk}")
    rels = schema.get("relationships", [])
    if isinstance(rels, dict):
        rels = list(rels.values()) if rels else []
    for r in rels:
        lines.append(f"[JOIN] {r['from']} → {r['to']}  키: {r.get('join_key','')}")
    return "\n".join(lines)

def _extract_kg_with_domain(text: str, _dc=None, _claude=None, _kg=None):
    """도메인 컨텍스트를 포함해 Claude로 엔티티·관계 추출.
    _dc:     스레드 안전을 위해 domain_config dict를 직접 전달
    _claude: ClaudeClient 인스턴스 (스레드에서 session_state 접근 불가)
    _kg:     KnowledgeGraph 인스턴스 (동일 이유)
    """
    from modules.knowledge_graph import build_entity_extraction_prompt
    dc = _dc if _dc is not None else st.session_state.get("domain_config")
    if dc:
        from modules.domain_adapter import DomainConfig
        dc_obj = DomainConfig.from_dict(dc)
        entity_types_desc = dc_obj.get_entity_types_description()
        domain_ctx_header = f"[도메인 컨텍스트]\n{dc_obj.to_context_string()}\n\n"
    else:
        entity_types_desc = (
            "- person: 사람, 담당자\n- organization: 조직, 팀\n"
            "- issue: 문제, 이슈\n- decision: 결정 사항\n- metric: 지표, 수치"
        )
        domain_ctx_header = ""
    template = build_entity_extraction_prompt(entity_types_desc)
    from modules.chat_copilot import sanitize_input
    safe_text = sanitize_input(text, max_len=3000)
    prompt = domain_ctx_header + template.replace("{document}", safe_text)
    claude = _claude if _claude is not None else st.session_state.claude
    kg    = _kg    if _kg    is not None else st.session_state.kg
    response = claude.generate(prompt, max_tokens=4096)
    kg.build_from_claude_json(response)

def _process_file_contents(entries: list) -> int:
    """파일 콘텐츠 통합 처리. entries: [(filename, raw_bytes_or_text, source), ...]
    source: 'upload' | 'disk'
    """
    from modules.document_parser import (
        parse_file, extract_csv_schema,
        extract_python_graph_data, _csv_schema_to_text,
    )
    new_files, kg_direct, pending_csv = [], set(), []

    for fname, content, source in entries:
        if fname in st.session_state.documents:
            continue
        try:
            fl = fname.lower()
            if fl.endswith(".json"):
                raw = content if isinstance(content, str) else content.decode("utf-8")
                data = _json.loads(raw)
                if "tables" in data and "relationships" in data:
                    st.session_state.kg.build_from_schema_json(data)
                    text = _schema_to_text(data)
                else:
                    text = _json.dumps(data, ensure_ascii=False) if isinstance(data, dict) else raw
                st.session_state.documents[fname] = text
                new_files.append(fname); kg_direct.add(fname)

            elif fl.endswith(".csv"):
                raw = content if isinstance(content, str) else content.decode("utf-8-sig", errors="replace")
                schema = extract_csv_schema(fname, raw)
                pending_csv.append((fname, schema))
                st.session_state.documents[fname] = _csv_schema_to_text(schema)
                new_files.append(fname); kg_direct.add(fname)

            elif fl.endswith(".py"):
                src = content if isinstance(content, str) else content.decode("utf-8")
                gd = extract_python_graph_data(src, fname)
                st.session_state.kg.build_from_python_ast(gd)
                st.session_state.documents[fname] = src
                new_files.append(fname); kg_direct.add(fname)

            else:
                if source == "upload":
                    text = parse_file(content)  # content is UploadedFile
                else:
                    text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
                if text.strip():
                    st.session_state.documents[fname] = text
                    new_files.append(fname)
        except (ValueError, _json.JSONDecodeError, UnicodeDecodeError) as e:
            st.warning(f"⚠️ `{fname}` 파싱 오류: {e}")
        except IOError as e:
            st.warning(f"⚠️ `{fname}` 파일 오류: {e}")

    # CSV 2-pass FK
    if pending_csv:
        for fn, sc in pending_csv:
            st.session_state.kg.build_from_csv_schema(sc, [])
        all_tables = list(st.session_state.kg.graph.nodes)
        for fn, sc in pending_csv:
            st.session_state.kg.build_from_csv_schema(sc, all_tables)

    # RAG 인덱싱
    for fname in new_files:
        st.session_state.rag.add_document(st.session_state.documents[fname], fname)

    # Claude KG 추출 (TXT/PDF/DOCX — 도메인 컨텍스트 포함, 병렬화)
    # ※ 스레드 안전: session_state 객체를 메인 스레드에서 캡처해 전달
    _captured_dc     = st.session_state.get("domain_config")
    _captured_claude = st.session_state.claude
    _captured_kg     = st.session_state.kg
    kg_targets = [fname for fname in new_files if fname not in kg_direct]
    if kg_targets:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(
                    _extract_kg_with_domain,
                    st.session_state.documents[fname],
                    _captured_dc,
                    _captured_claude,
                    _captured_kg,
                ): fname
                for fname in kg_targets
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except (ValueError, IOError) as e:
                    st.warning(f"⚠️ KG 추출 실패 ({futures[future]}): {e}")

    # GraphRAG: KG 구축 완료 후 커뮤니티 요약 빌드
    # 커뮤니티 탐지 → Claude 요약 생성 → Supabase community_summaries 저장
    if new_files and len(st.session_state.kg.graph.nodes) >= 2:
        try:
            from modules.community_summarizer import build_community_summaries
            n_communities = build_community_summaries(
                st.session_state.kg,
                st.session_state.claude,
                _get_collection_name(),
            )
            if n_communities:
                st.toast(f"GraphRAG: {n_communities}개 커뮤니티 요약 생성 완료", icon="🕸️")
        except Exception as _e:
            st.warning(f"⚠️ GraphRAG 커뮤니티 요약 실패: {_e}")

    return len(new_files)


def _process_uploaded_files(uploaded_files) -> int:
    from modules.document_parser import parse_file
    entries = []
    for uf in uploaded_files:
        fl = uf.name.lower()
        if fl.endswith((".json", ".csv", ".py")):
            entries.append((uf.name, uf.read(), "upload"))
        else:
            entries.append((uf.name, uf, "upload"))
    return _process_file_contents(entries)


# ── 도메인별 Supabase 접두어 / 서브디렉터리 / 테이블 매핑 ─────────────────────
_DOMAIN_PREFIX_MAP = {
    "뷰티": "beauty", "이커머스": "beauty",
    "공급망": "supply", "재고": "supply",
    "에너지": "energy",
    "제조": "manufacturing", "생산": "manufacturing",
    "물류": "logistics",
    "금융": "finance",
}
_DOMAIN_DIR_MAP = {
    "beauty":        ".",               # data/ 루트
    "supply":        "supply_chain",
    "energy":        "energy",
    "manufacturing": "manufacturing",
    "logistics":     "logistics",
    "finance":       "finance",
}
_DOMAIN_TABLES = {
    "beauty":        ["MST_SUPPLIER","MST_CHANNEL","MST_PRODUCT","MST_LOCATION",
                      "FACT_MONTHLY_SALES","FACT_INVENTORY"],
    "supply":        ["MST_PART","MST_SUPPLIER","MST_WAREHOUSE",
                      "FACT_MONTHLY_DEMAND","FACT_INVENTORY","FACT_ORDER"],
    "energy":        ["MST_REGION","MST_PLANT","MST_METER",
                      "FACT_DAILY_USAGE","FACT_MONTHLY_BILL","FACT_OUTAGE"],
    "manufacturing": ["MST_LINE","MST_EQUIPMENT","MST_PRODUCT",
                      "FACT_PRODUCTION","FACT_DEFECT","FACT_MAINTENANCE"],
    "logistics":     ["MST_HUB","MST_VEHICLE","MST_ROUTE",
                      "FACT_DELIVERY","FACT_DELAY","FACT_COST"],
    "finance":       ["MST_PRODUCT","MST_CUSTOMER","MST_BRANCH",
                      "FACT_TRANSACTION","FACT_RISK","FACT_PERFORMANCE"],
}

def _get_domain_prefix() -> str:
    dc = st.session_state.get("domain_config")
    if not dc:
        return "beauty"
    name = dc.get("name", "")
    for key, prefix in _DOMAIN_PREFIX_MAP.items():
        if key in name:
            return prefix
    return "beauty"


def _load_sample_data() -> int:
    from modules.supabase_client import is_connected, query_table as _sb_query

    prefix = _get_domain_prefix()

    # ── 1) Supabase 연결 시: DB에서 도메인 테이블 로드 ──────────────────────
    if is_connected():
        tables = _DOMAIN_TABLES.get(prefix, [])
        entries: list = []
        for tbl in tables:
            tname = f"{prefix}_{tbl.lower()}"
            df = _sb_query(tname)
            if df is not None and len(df) > 0:
                csv_text = df.to_csv(index=False)
                entries.append((f"{tbl}.csv", csv_text, "disk"))

        # SCHEMA_DEFINITION.json / LOGIC_DOCUMENT.txt 는 로컬 파일에서 보완
        sub = _DOMAIN_DIR_MAP.get(prefix, ".")
        loaded_names = {e[0] for e in entries}
        for meta in ["SCHEMA_DEFINITION.json", "LOGIC_DOCUMENT.txt"]:
            if meta in loaded_names:
                continue
            candidates = [
                os.path.join("./data", sub, meta),
                os.path.join("./data", meta),
            ]
            for p in candidates:
                if os.path.isfile(p):
                    try:
                        with open(p, encoding="utf-8", errors="replace") as f:
                            entries.append((meta, f.read(), "disk"))
                        break
                    except IOError:
                        pass

        if entries:
            return _process_file_contents(entries)

    # ── 2) CSV fallback: 도메인 서브디렉터리 → data/ 루트 순 탐색 ───────────
    sub = _DOMAIN_DIR_MAP.get(prefix, ".")
    candidates_dirs = []
    if sub != ".":
        candidates_dirs.append(os.path.join("./data", sub))
    candidates_dirs.append("./data")

    data_dir = next((d for d in candidates_dirs if os.path.isdir(d)), None)
    if not data_dir:
        return 0

    entries = []
    for fname in sorted(os.listdir(data_dir)):
        fpath = os.path.join(data_dir, fname)
        if not os.path.isfile(fpath) or fname in st.session_state.documents:
            continue
        fl = fname.lower()
        if fl.endswith((".json", ".csv", ".txt")):
            try:
                enc = "utf-8-sig" if fl.endswith(".csv") else "utf-8"
                with open(fpath, encoding=enc, errors="replace") as f:
                    entries.append((fname, f.read(), "disk"))
            except IOError:
                pass
    return _process_file_contents(entries)

def _process_text_paste(title: str, text: str) -> bool:
    key = f"{title.strip()}.txt"
    if key in st.session_state.documents or not text.strip():
        return False
    st.session_state.documents[key] = text
    st.session_state.rag.add_document(text, key)
    _extract_kg_with_domain(text)
    return True


# ── 채팅 헬퍼 (modules/chat_copilot, modules/data_analyst 위임) ───────────────

def _generate_daily_briefing():
    """일일 브리핑: data_analyst 함수로 데이터 수집 → Claude 요약.
    Returns (summary_text, charts, datasets_used)
    """
    from modules.data_analyst import (
        inventory_risk_summary, inventory_coverage_chart,
        channel_top3_chart, replenishment_status,
    )
    sections: list = []
    charts:   list = []
    all_ds:   list = []

    inv_text, ds = inventory_risk_summary()
    sections.append(inv_text); all_ds.extend(ds)

    fig1, ds = inventory_coverage_chart()
    if fig1: charts.append(fig1)
    all_ds.extend(ds)

    fig2, ds = channel_top3_chart()
    if fig2: charts.append(fig2)
    all_ds.extend(ds)

    rep_text, ds = replenishment_status()
    sections.append(rep_text); all_ds.extend(ds)

    data_summary = "\n\n".join(sections)
    prompt = (
        f"{_get_domain_context()}\n\n"
        f"[오늘의 운영 현황]\n{data_summary}\n\n"
        f"운영 담당자를 위한 간결한 일일 브리핑을 작성하세요.\n"
        f"형식:\n"
        f"## 🌅 일일 운영 브리핑 ({datetime.now().strftime('%Y년 %m월 %d일')})\n"
        f"### 🚨 즉시 조치 필요\n"
        f"### 📊 핵심 지표\n"
        f"### ✅ 권장 액션"
    )
    summary = st.session_state.claude.generate(prompt, max_tokens=1500)
    return summary, charts, list(set(all_ds))


def _generate_briefing_cards():
    """4개 카드형 일일 브리핑 데이터를 생성합니다.
    Returns list of card dicts: {id, title, icon, data_text, metrics, chart, chat_prompt, summary, actions}
    """
    from modules.data_analyst import (
        inventory_risk_summary, inventory_coverage_chart,
        channel_top3_chart, replenishment_status,
        detect_anomaly_products, season_top_products,
    )
    import json as _json2

    cards_raw = []

    # ── 카드 1: 재고 위험 ───────────────────────────────────
    inv_text, _ = inventory_risk_summary()
    inv_fig, _  = inventory_coverage_chart()
    # CRITICAL/WARNING 수치 파싱
    import re as _re
    _m = _re.search(r"CRITICAL\s*(\d+)개\s*/\s*WARNING\s*(\d+)개", inv_text)
    inv_critical = int(_m.group(1)) if _m else 0
    inv_warning  = int(_m.group(2)) if _m else 0
    cards_raw.append({
        "id": "inventory",
        "title": "재고 위험 상품",
        "icon": "🚨",
        "data_text": inv_text,
        "metrics": [
            {"label": "CRITICAL", "value": str(inv_critical), "delta": None},
            {"label": "WARNING",  "value": str(inv_warning),  "delta": None},
        ],
        "chart": inv_fig,
        "chat_prompt": "재고 위험 CRITICAL 상품 목록과 즉시 조치 방법을 알려줘",
    })

    # ── 카드 2: 채널별 판매 TOP3 ────────────────────────────
    from modules.data_analyst import load_csv as _load_csv
    _ch_sales = _load_csv("FACT_MONTHLY_SALES.csv")
    _ch_mst   = _load_csv("MST_CHANNEL.csv")
    ch_summary = ""
    ch_channels = 0
    if _ch_sales is not None and _ch_mst is not None:
        _recent_m = sorted(_ch_sales["YEAR_MONTH"].unique())[-1:]
        _recent_s = _ch_sales[_ch_sales["YEAR_MONTH"].isin(_recent_m)]
        _merged   = _recent_s.merge(_ch_mst[["CHANNEL_ID","CHANNEL_NAME"]], on="CHANNEL_ID", how="left")
        ch_channels = _merged["CHANNEL_NAME"].nunique()
        _top = _merged.groupby("CHANNEL_NAME")["NET_SALES_QTY"].sum().nlargest(3)
        ch_summary = "\n".join(f"  · {ch}: {qty:,}개" for ch, qty in _top.items())
    ch_fig, _ = channel_top3_chart()
    cards_raw.append({
        "id": "channel",
        "title": "채널별 판매 TOP3",
        "icon": "📈",
        "data_text": f"[최근 채널별 판매]\n{ch_summary}" if ch_summary else "채널 데이터 없음",
        "metrics": [
            {"label": "활성 채널", "value": str(ch_channels), "delta": None},
        ],
        "chart": ch_fig,
        "chat_prompt": "채널별 판매 현황 비교하고 가장 성장하는 채널 알려줘",
    })

    # ── 카드 3: 발주 필요 상품 ──────────────────────────────
    rep_text, _ = replenishment_status()
    _orders = _load_csv("FACT_REPLENISHMENT_ORDER.csv")
    pending_cnt = 0
    if _orders is not None:
        pending_cnt = len(_orders[_orders["STATUS"].isin(["PENDING","IN_TRANSIT"])])
    _no_order = rep_text.count("발주 없음")
    cards_raw.append({
        "id": "replenishment",
        "title": "발주 필요 상품",
        "icon": "📦",
        "data_text": rep_text,
        "metrics": [
            {"label": "진행중 발주",  "value": str(pending_cnt), "delta": None},
            {"label": "발주 미처리", "value": str(_no_order),   "delta": None},
        ],
        "chart": None,
        "chat_prompt": "발주 없는 위험 상품 목록 보여주고 발주 우선순위 제안해줘",
    })

    # ── 카드 4: 이상 변화 감지 ──────────────────────────────
    anom_text, _ = detect_anomaly_products(top_n=5)
    _surge_cnt = anom_text.count("🔺")
    _drop_cnt  = anom_text.count("🔻")
    cards_raw.append({
        "id": "anomaly",
        "title": "이상 변화 감지",
        "icon": "⚡",
        "data_text": anom_text,
        "metrics": [
            {"label": "급등 상품", "value": str(_surge_cnt), "delta": None},
            {"label": "급락 상품", "value": str(_drop_cnt),  "delta": None},
        ],
        "chart": None,
        "chat_prompt": "급등/급락 상품 원인 분석하고 대응 방안 알려줘",
    })

    # ── Claude 한 번 호출: 4개 섹션의 요약 + 액션 생성 ────
    all_data = "\n\n".join(c["data_text"] for c in cards_raw)
    ai_prompt = (
        f"{_get_domain_context()}\n\n"
        f"[운영 현황 데이터]\n{all_data}\n\n"
        "위 4개 섹션에 대해 운영 담당자를 위한 JSON을 작성하세요.\n"
        "각 섹션: 한 줄 요약(summary)과 즉시 해야 할 일 3개(actions 배열).\n"
        '출력 형식 (JSON only, 다른 텍스트 없이):\n'
        '{"inventory":{"summary":"...","actions":["...","...","..."]},'
        '"channel":{"summary":"...","actions":["...","...","..."]},'
        '"replenishment":{"summary":"...","actions":["...","...","..."]},'
        '"anomaly":{"summary":"...","actions":["...","...","..."]}}'
    )
    raw_ai = st.session_state.claude.generate(ai_prompt, max_tokens=800)

    # JSON 파싱 시도
    ai_data = {}
    try:
        _start = raw_ai.find("{")
        _end   = raw_ai.rfind("}") + 1
        if _start >= 0 and _end > _start:
            ai_data = _json2.loads(raw_ai[_start:_end])
    except (ValueError, KeyError, _json2.JSONDecodeError):
        pass

    _default_ai = {"summary": "데이터 분석 완료", "actions": ["현황 확인", "담당자 공유", "조치 계획 수립"]}
    for card in cards_raw:
        ai = ai_data.get(card["id"], _default_ai)
        card["summary"] = ai.get("summary", _default_ai["summary"])
        card["actions"] = ai.get("actions", _default_ai["actions"])[:3]

    return cards_raw


# ── CSS 적용 ──────────────────────────────────────────────────────────────────
_apply_css(_get_theme_color())


# ── DB 연결 상태 표시 헬퍼 ────────────────────────────────────────────────────
def _render_db_status():
    """사이드바에 Supabase/CSV 연결 상태를 표시합니다."""
    try:
        from modules.supabase_client import get_status
        status = get_status()
    except Exception:
        status = {"connected": False, "mode": "CSV (로컬)", "error": ""}

    if status["connected"]:
        st.markdown(
            '<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:6px;'
            'padding:4px 10px;font-size:.78rem;margin-bottom:.5rem">'
            '🟢 <b>Supabase</b> 연결됨</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="background:#fef3c7;border:1px solid #fcd34d;border-radius:6px;'
            'padding:4px 10px;font-size:.78rem;margin-bottom:.5rem">'
            '🟡 <b>CSV 모드</b> (로컬 파일)</div>',
            unsafe_allow_html=True,
        )
        if status.get("error"):
            st.caption(f"DB: {status['error'][:80]}")


# ── 사이드바: Step 1/2는 최소 정보, Step 3는 채팅 (아래에서 추가) ───────────
if st.session_state.step != 3:
    with st.sidebar:
        dc = st.session_state.domain_config
        dname = dc["name"] if dc else "AI 운영 코파일럿"
        st.markdown(f"### {dname}")
        _render_db_status()
        st.divider()

        if st.session_state.documents:
            st.markdown(f"**로드된 문서 {len(st.session_state.documents)}개**")
            for fname in list(st.session_state.documents.keys())[:6]:
                st.caption(f"• {fname}")
            if len(st.session_state.documents) > 6:
                st.caption(f"  ... 외 {len(st.session_state.documents)-6}개")
            st.divider()
            if st.button("초기화", use_container_width=True):
                st.session_state.documents = {}
                if st.session_state.rag:
                    try: st.session_state.rag.delete_collection()
                    except Exception: pass
                if st.session_state.kg:
                    st.session_state.kg.clear()
                st.session_state.update({
                    "step": 1, "domain_config": None,
                    "domain_suggestion": None, "suggest_countdown": None,
                })
                st.rerun()
        else:
            st.info("아직 문서 없음")

        st.divider()
        st.markdown("**단계 이동**")
        for lbl, n in [("도메인 설정", 1), ("파일 업로드", 2), ("결과 보기", 3)]:
            if st.button(lbl, use_container_width=True, key=f"nav_{n}"):
                st.session_state.step = n; st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 메인 콘텐츠
# ════════════════════════════════════════════════════════════════════════════════

# 헤더
st.markdown("""
<div class="app-header">
  <h1>AI 운영 코파일럿</h1>
  <p>문서와 데이터를 연결해 의사결정을 돕습니다</p>
</div>
""", unsafe_allow_html=True)

# 단계 표시기
step = st.session_state.step

def _sc(n):   # dot class
    return "done" if step > n else ("active" if step == n else "")
def _sl(n):   # line class
    return "done" if step > n else ""

st.markdown(f"""
<div class="steps">
  <div class="step">
    <div class="s-dot {_sc(1)}">{"✓" if step>1 else "1"}</div>
    <div class="s-lbl {_sc(1)}">도메인 설정</div>
  </div>
  <div class="s-line {_sl(1)}"></div>
  <div class="step">
    <div class="s-dot {_sc(2)}">{"✓" if step>2 else "2"}</div>
    <div class="s-lbl {_sc(2)}">파일 업로드</div>
  </div>
  <div class="s-line {_sl(2)}"></div>
  <div class="step">
    <div class="s-dot {_sc(3)}">3</div>
    <div class="s-lbl {_sc(3)}">결과 보기</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════════
# Step 1: 도메인 설정
# ════════════════════════════════════════════════════════════════════════════════
if step == 1:

    # ── 파일 업로드 후 돌아온 경우: 도메인 자동 감지 확인 ─────────────────────
    if st.session_state.get("domain_suggestion") and not st.session_state.domain_config:
        suggestion = st.session_state["domain_suggestion"]
        countdown  = st.session_state.get("suggest_countdown", 3)

        st.markdown(f"""
        <div class="dom-banner">
          🤖 &nbsp;<strong>{suggestion}</strong> 도메인으로 인식했습니다.
          &nbsp;·&nbsp; {countdown}초 후 자동 진행됩니다.
        </div>
        """, unsafe_allow_html=True)

        override = st.text_input(
            "다른 도메인이라면 이름을 수정하세요:",
            value=suggestion, key="domain_override_input"
        )
        c1, c2 = st.columns([1, 3])
        with c1:
            if st.button("이 도메인으로 시작", type="primary"):
                final = (override or suggestion).strip()
                cfg = _build_domain_from_name(final)
                st.session_state.domain_config = cfg.to_dict()
                st.session_state.pop("domain_suggestion", None)
                st.session_state.pop("suggest_countdown", None)
                _apply_css(cfg.theme_color)
                st.session_state.step = 2; st.rerun()

        # 카운트다운: 1초 sleep 후 재실행
        if countdown > 0:
            time.sleep(1)
            st.session_state["suggest_countdown"] = countdown - 1
            st.rerun()
        else:
            final = (st.session_state.get("domain_override_input") or suggestion).strip()
            cfg = _build_domain_from_name(final)
            st.session_state.domain_config = cfg.to_dict()
            st.session_state.pop("domain_suggestion", None)
            st.session_state.pop("suggest_countdown", None)
            st.session_state.step = 2; st.rerun()

    else:
        # ── 안내 가이드 ──────────────────────────────────────────────────
        st.markdown("""
<div style="background:linear-gradient(135deg,#eff6ff,#f0fdf4);border:1px solid #bfdbfe;
border-radius:12px;padding:1.2rem 1.5rem;margin-bottom:1.5rem">
<p style="font-size:1.05rem;font-weight:700;margin:0 0 .6rem 0">3단계만 따라오세요</p>
<table style="width:100%;border:none;border-collapse:collapse;font-size:.92rem">
<tr>
<td style="padding:6px 10px;border:none;vertical-align:top;white-space:nowrap"><strong>Step 1</strong></td>
<td style="padding:6px 10px;border:none">아래에서 <strong>도메인을 선택</strong>하세요. 잘 모르겠으면 "설정 없이 시작"을 눌러도 됩니다.</td>
</tr>
<tr>
<td style="padding:6px 10px;border:none;vertical-align:top;white-space:nowrap"><strong>Step 2</strong></td>
<td style="padding:6px 10px;border:none">파일을 업로드하거나 <strong>"샘플 데이터로 시작"</strong>을 누르면 바로 체험할 수 있습니다.</td>
</tr>
<tr>
<td style="padding:6px 10px;border:none;vertical-align:top;white-space:nowrap"><strong>Step 3</strong></td>
<td style="padding:6px 10px;border:none">지식그래프와 분석 결과가 자동 생성됩니다. <strong>왼쪽 사이드바 채팅</strong>으로 자유롭게 질문하세요.</td>
</tr>
</table>
</div>
""", unsafe_allow_html=True)

        # ── 처음 보시는 분을 위한 흐름 설명 ───────────────────────────────
        with st.expander("📖 처음 오셨나요? 이 앱이 어떻게 동작하는지 보여드릴게요", expanded=False):
            st.markdown("""
<style>
.flow-box{background:#fff;border:1.5px solid #e2e8f0;border-radius:10px;padding:1rem 1.2rem;margin:.5rem 0}
.flow-arrow{text-align:center;font-size:1.4rem;color:#94a3b8;margin:.1rem 0;line-height:1}
.flow-tag{display:inline-block;background:#f1f5f9;border-radius:6px;padding:2px 8px;font-size:.78rem;font-weight:600;margin:2px 3px;color:#475569}
.flow-tag-blue{background:#dbeafe;color:#1d4ed8}
.flow-tag-green{background:#dcfce7;color:#166534}
.flow-tag-purple{background:#ede9fe;color:#6d28d9}
.flow-tag-orange{background:#ffedd5;color:#c2410c}
.flow-tag-pink{background:#fce7f3;color:#be185d}
.kv{font-size:.82rem;margin:.15rem 0;color:#334155}
.kv b{color:#0f172a}
.section-title{font-size:.95rem;font-weight:700;color:#0f172a;margin:0 0 .4rem}
.mini-table{width:100%;border-collapse:collapse;font-size:.78rem;margin:.4rem 0}
.mini-table th{background:#f8fafc;padding:4px 8px;border:1px solid #e2e8f0;color:#475569;font-weight:600;text-align:left}
.mini-table td{padding:4px 8px;border:1px solid #e2e8f0;color:#334155}
.arrow-row{display:flex;align-items:center;gap:.5rem;margin:.3rem 0;flex-wrap:wrap}
.arrow-cell{background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:3px 10px;font-size:.8rem;color:#334155;white-space:nowrap}
.arrow-line{color:#94a3b8;font-size:1rem}
.highlight-box{background:#f0f9ff;border-left:3px solid #0284c7;padding:.5rem .8rem;border-radius:0 6px 6px 0;font-size:.83rem;color:#0c4a6e;margin:.4rem 0}
</style>

## 전체 흐름 한눈에

<div class="arrow-row" style="justify-content:center;flex-wrap:wrap;gap:.4rem;margin-bottom:1rem">
  <div class="arrow-cell" style="background:#eff6ff;border-color:#bfdbfe;font-weight:700">📂 파일 업로드</div>
  <div class="arrow-line">→</div>
  <div class="arrow-cell" style="background:#f0fdf4;border-color:#86efac;font-weight:700">🏷️ 도메인 인식</div>
  <div class="arrow-line">→</div>
  <div class="arrow-cell" style="background:#faf5ff;border-color:#d8b4fe;font-weight:700">🔗 FK 자동 감지</div>
  <div class="arrow-line">→</div>
  <div class="arrow-cell" style="background:#fff7ed;border-color:#fed7aa;font-weight:700">🕸️ 지식그래프</div>
  <div class="arrow-line">+</div>
  <div class="arrow-cell" style="background:#fdf2f8;border-color:#f9a8d4;font-weight:700">🔍 RAG 인덱싱</div>
  <div class="arrow-line">→</div>
  <div class="arrow-cell" style="background:#f0fdf4;border-color:#86efac;font-weight:700">🤖 AI 분석 + 채팅</div>
</div>

---

### 1️⃣ 도메인(Domain)이란?

> **앱에게 "어떤 업종 문서인지" 미리 알려주는 것입니다.**

같은 단어도 업종마다 의미가 다릅니다. 도메인을 설정하면 AI가 해당 업종 언어로 이해합니다.

<div style="display:flex;gap:.8rem;flex-wrap:wrap;margin:.5rem 0">
<div class="flow-box" style="flex:1;min-width:180px">
<div class="section-title">🛒 뷰티 선택 시</div>
<div class="kv">• <span class="flow-tag flow-tag-pink">SKU</span> = 개별 제품 단위</div>
<div class="kv">• <span class="flow-tag flow-tag-pink">MOQ</span> = 최소 주문 수량</div>
<div class="kv">• <span class="flow-tag flow-tag-pink">리드타임</span> = 발주~입고 기간</div>
<div class="kv">• <span class="flow-tag flow-tag-pink">CPNP</span> = 유럽 화장품 신고</div>
</div>
<div class="flow-box" style="flex:1;min-width:180px">
<div class="section-title">🏭 공급망 선택 시</div>
<div class="kv">• <span class="flow-tag flow-tag-blue">재발주점</span> = 발주 시작 재고</div>
<div class="kv">• <span class="flow-tag flow-tag-blue">안전재고</span> = 최소 보유량</div>
<div class="kv">• <span class="flow-tag flow-tag-blue">DELAY_DAYS</span> = 납기 지연일</div>
<div class="kv">• <span class="flow-tag flow-tag-blue">A/B/C 등급</span> = 부품 중요도</div>
</div>
<div class="flow-box" style="flex:1;min-width:180px">
<div class="section-title">⚡ 에너지 선택 시</div>
<div class="kv">• <span class="flow-tag flow-tag-orange">USAGE_KWH</span> = 전력 소비량</div>
<div class="kv">• <span class="flow-tag flow-tag-orange">PEAK_KW</span> = 최대 순간전력</div>
<div class="kv">• <span class="flow-tag flow-tag-orange">역률</span> = 전력 효율</div>
<div class="kv">• <span class="flow-tag flow-tag-orange">CAPACITY_MW</span> = 발전 용량</div>
</div>
</div>

<div class="highlight-box">💡 도메인 없이 파일을 올려도 됩니다. AI가 내용을 보고 자동으로 감지합니다.</div>

---

### 2️⃣ FK(Foreign Key, 외래키)란?

> **여러 테이블을 이어주는 공통 열쇠입니다.** 엑셀 시트 여러 개를 VLOOKUP으로 연결하는 것과 같습니다.

예를 들어, 뷰티 도메인 데이터:

<table class="mini-table">
<tr><th colspan="4">📋 MST_PRODUCT (제품 마스터)</th></tr>
<tr><th>PRODUCT_ID</th><th>PRODUCT_NAME</th><th>CATEGORY</th><th>SUPPLIER_ID</th></tr>
<tr><td style="color:#1d4ed8;font-weight:700">PRD001</td><td>클린잇제로 클렌징밤</td><td>스킨케어</td><td>SUP001</td></tr>
<tr><td style="color:#1d4ed8;font-weight:700">PRD002</td><td>선프로텍터 선크림 SPF50+</td><td>스킨케어</td><td>SUP004</td></tr>
</table>

<table class="mini-table" style="margin-top:.6rem">
<tr><th colspan="5">📊 FACT_MONTHLY_SALES (월별 판매 실적)</th></tr>
<tr><th>SALE_ID</th><th>PRODUCT_ID</th><th>YEAR_MONTH</th><th>SALES_QTY</th><th>SALES_AMOUNT</th></tr>
<tr><td>SL000001</td><td style="color:#1d4ed8;font-weight:700">PRD001</td><td>2024-01</td><td>370</td><td>8,140,000</td></tr>
<tr><td>SL000002</td><td style="color:#1d4ed8;font-weight:700">PRD001</td><td>2024-02</td><td>324</td><td>7,128,000</td></tr>
</table>

<div style="text-align:center;margin:.5rem 0;font-size:.85rem;color:#475569">
⬆️ 두 테이블의 <b style="color:#1d4ed8">PRODUCT_ID</b>가 일치 → 앱이 자동으로 감지해 연결
</div>

<div class="highlight-box">💡 앱은 컬럼명 끝이 <b>_ID, _CD, _NO</b>인 열을 FK 후보로 자동 감지합니다. SQL JOIN 없이 관계를 파악합니다.</div>

---

### 3️⃣ 지식그래프(Knowledge Graph)란?

> **개념(노드)과 연결(엣지)로 이루어진 관계 지도입니다.**

위에서 감지한 FK를 바탕으로 아래 같은 그래프가 자동 생성됩니다:

<div style="background:#0f172a;border-radius:10px;padding:1rem 1.5rem;font-family:monospace;font-size:.82rem;margin:.5rem 0">
<div style="color:#93c5fd">[ MST_PRODUCT ]</div>
<div style="color:#6ee7b7;margin-left:1rem">PRD001 "클린잇제로 클렌징밤"</div>
<div style="color:#6ee7b7;margin-left:1rem">PRD002 "선프로텍터 선크림"</div>
<div style="color:#fbbf24;margin:.4rem 0 0 1.5rem">↓ PRODUCT_ID (FK)</div>
<div style="color:#f9a8d4">[ FACT_MONTHLY_SALES ]</div>
<div style="color:#6ee7b7;margin-left:1rem">370개 / 8,140,000원 (2024-01)</div>
<div style="color:#6ee7b7;margin-left:1rem">324개 / 7,128,000원 (2024-02)</div>
<div style="color:#fbbf24;margin:.4rem 0 0 1.5rem">↓ PRODUCT_ID (FK)</div>
<div style="color:#c4b5fd">[ FACT_INVENTORY ]</div>
<div style="color:#6ee7b7;margin-left:1rem">재고 346개 / 안전재고 394개 (LOC001)</div>
</div>

<div class="highlight-box">💡 이 그래프 덕분에 "PRD001이 어느 창고에 얼마나 있고, 지난달 얼마나 팔렸는지"를 <b>한 번에</b> 추적할 수 있습니다.</div>

---

### 4️⃣ RAG(검색 증강 생성)란?

> **문서를 잘게 쪼개 저장해두고, 질문하면 관련 부분만 찾아 AI에게 전달하는 방식입니다.**

<div style="display:flex;gap:.5rem;align-items:flex-start;flex-wrap:wrap;margin:.5rem 0">
<div class="flow-box" style="flex:1;min-width:160px">
<div class="section-title">① 청킹</div>
<div style="font-size:.8rem;color:#475569">문서를 약 500토큰(200~300단어) 단위로 자름</div>
<div style="background:#f8fafc;border-radius:6px;padding:.4rem .6rem;margin-top:.4rem;font-size:.75rem;color:#334155">
"PRD001 클린잇제로 클렌징밤, 스킨케어, 재고 346개, 안전재고 394개, 커버리지 2.3주..." → <b>[청크 1]</b>
</div>
</div>
<div style="align-self:center;color:#94a3b8;font-size:1.3rem">→</div>
<div class="flow-box" style="flex:1;min-width:160px">
<div class="section-title">② 벡터 저장</div>
<div style="font-size:.8rem;color:#475569">각 청크를 숫자 배열(벡터)로 변환 → ChromaDB에 저장</div>
<div style="background:#f8fafc;border-radius:6px;padding:.4rem .6rem;margin-top:.4rem;font-size:.75rem;color:#334155">
[0.23, -0.41, 0.87, ...] <span style="color:#94a3b8">(768차원)</span>
</div>
</div>
<div style="align-self:center;color:#94a3b8;font-size:1.3rem">→</div>
<div class="flow-box" style="flex:1;min-width:160px">
<div class="section-title">③ 유사도 검색</div>
<div style="font-size:.8rem;color:#475569">"재고 위험 제품?" 질문 → 가장 유사한 청크 TOP 3 추출</div>
<div style="background:#dbeafe;border-radius:6px;padding:.4rem .6rem;margin-top:.4rem;font-size:.75rem;color:#1d4ed8">
FACT_INVENTORY 중 STOCK_STATUS=CRITICAL 청크 발견!
</div>
</div>
</div>

<div class="highlight-box">💡 전체 문서를 매번 읽지 않고 <b>관련 부분만</b> 찾아주므로, 수백 페이지 문서도 빠르고 정확하게 답할 수 있습니다.</div>

---

### 5️⃣ AI 분석 + 채팅

> **RAG 검색 결과 + 지식그래프 관계를 합쳐 Claude가 최종 답변을 생성합니다.**

<div class="flow-box" style="margin:.5rem 0">
<div style="font-size:.85rem;color:#475569;margin-bottom:.5rem">예시: <b>"선크림 재고 지금 괜찮아?"</b> 라고 채팅에 입력하면</div>
<div class="arrow-row">
  <div class="arrow-cell">① RAG</div>
  <div class="arrow-line">→</div>
  <div style="font-size:.8rem;color:#334155">FACT_INVENTORY에서 PRD002 관련 청크 추출<br><span style="color:#94a3b8">재고 309개, 안전재고 384개, 커버리지 2.1주</span></div>
</div>
<div class="arrow-row" style="margin-top:.3rem">
  <div class="arrow-cell">② KG</div>
  <div class="arrow-line">→</div>
  <div style="font-size:.8rem;color:#334155">PRD002 → SEASONAL_PEAK:여름 → LOC003(미국 창고) 관계 파악</div>
</div>
<div class="arrow-row" style="margin-top:.3rem">
  <div class="arrow-cell">③ Claude</div>
  <div class="arrow-line">→</div>
  <div style="font-size:.8rem;color:#334155;background:#f0fdf4;border-radius:6px;padding:.3rem .6rem;flex:1">
  "선프로텍터 선크림(PRD002) 현재 재고 309개로 안전재고(384개) 미달입니다. 여름 시즌 피크가 예정되어 있어 <b>긴급 발주를 권장</b>합니다."
  </div>
</div>
</div>
""", unsafe_allow_html=True)

        # ── 일반 도메인 선택 화면 ──────────────────────────────────────────
        st.markdown("### 어떤 도메인의 문서를 분석하시나요?")
        st.caption("도메인을 선택하면 AI가 해당 분야 용어·관계를 파악해 더 정확하게 분석합니다.")

        preset_items = [
            ("뷰티 / 이커머스", "뷰티 이커머스"),
            ("공급망 / 재고",   "공급망·재고 관리"),
            ("에너지",          "에너지"),
            ("제조 / 생산",     "제조·생산"),
            ("물류",            "물류"),
            ("금융",            "금융"),
        ]
        cols = st.columns(3)
        for i, (label, name) in enumerate(preset_items):
            with cols[i % 3]:
                if st.button(label, use_container_width=True, key=f"preset_{i}"):
                    cfg = _build_domain_from_name(name)
                    st.session_state.domain_config = cfg.to_dict()
                    _apply_css(cfg.theme_color)
                    st.session_state.step = 2; st.rerun()

        st.divider()
        st.markdown("**직접 입력:**")
        ca, cb = st.columns([3, 1])
        with ca:
            custom = st.text_input("도메인명",
                placeholder="예: 의료·병원, 법률, 반도체 제조...",
                label_visibility="collapsed", key="custom_domain")
        with cb:
            if st.button("확인", type="primary", use_container_width=True):
                if custom.strip():
                    cfg = _build_domain_from_name(custom.strip())
                    st.session_state.domain_config = cfg.to_dict()
                    _apply_css(cfg.theme_color)
                    st.session_state.step = 2; st.rerun()
                else:
                    st.error("도메인명을 입력해주세요.")

        st.divider()
        st.caption("💡 도메인 없이 바로 파일을 올려도 됩니다. 파일 내용으로 자동 감지합니다.")

        # ── 파일 형식 예시 미리보기 ───────────────────────────────────────────
        with st.expander("📂 어떤 파일을 올릴 수 있나요? (예시 미리보기)", expanded=False):
            tab_csv, tab_txt, tab_json, tab_py = st.tabs(["📊 CSV", "📄 TXT", "🔧 JSON", "🐍 Python"])

            with tab_csv:
                import pandas as _pd
                _sample_csv = _pd.DataFrame({
                    "id":         ["A001", "A002", "A003", "A004", "A005"],
                    "name":       ["항목 Alpha", "항목 Beta", "항목 Gamma", "항목 Delta", "항목 Epsilon"],
                    "category":   ["유형-1", "유형-2", "유형-1", "유형-3", "유형-2"],
                    "related_id": ["A003", "A001", "A005", "A002", "A004"],
                    "value":      [1240, 870, 3050, 420, 1980],
                    "date":       ["2024-01", "2024-02", "2024-02", "2024-03", "2024-03"],
                })
                st.dataframe(_sample_csv, use_container_width=True, hide_index=True)
                st.caption("💡 related_id처럼 다른 테이블을 참조하는 컬럼을 자동 감지해 관계를 연결합니다")

            with tab_txt:
                _sample_txt = """[2024-03-15] 주간 운영 회의록
참석자: 김운영(팀장), 이기획, 박데이터, 최개발

안건 1 — A003 항목 처리 지연 원인 분석
  - A003은 A005와 연동되어 있어 동시 검토 필요
  - 담당자 박데이터가 다음 주까지 원인 보고서 작성

안건 2 — 신규 유형-3 카테고리 분류 기준 수립
  - A004 항목을 기준 사례로 활용하기로 결정"""
                st.code(_sample_txt, language=None)
                st.caption("💡 텍스트 안의 ID·이름·관계를 추출해 기존 데이터와 연결합니다")

            with tab_json:
                _sample_json = {
                    "entities": [
                        {"id": "A001", "name": "항목 Alpha", "type": "유형-1", "parent_id": None,  "tags": ["핵심", "운영"]},
                        {"id": "A002", "name": "항목 Beta",  "type": "유형-2", "parent_id": "A001", "tags": ["보조"]},
                        {"id": "A003", "name": "항목 Gamma", "type": "유형-1", "parent_id": "A001", "tags": ["핵심", "지연"]},
                        {"id": "A004", "name": "항목 Delta", "type": "유형-3", "parent_id": None,  "tags": ["신규"]},
                        {"id": "A005", "name": "항목 Epsilon","type": "유형-2", "parent_id": "A002", "tags": ["보조", "연동"]},
                    ]
                }
                st.json(_sample_json, expanded=1)
                st.caption("💡 중첩 구조와 참조 키를 파악해 계층 관계를 그래프로 변환합니다")

            with tab_py:
                _sample_py = """import data_loader
import relation_mapper
from config import ENTITY_TYPES

def build_graph(source_file):
    records = data_loader.load(source_file)
    entities = [e for e in records if e["type"] in ENTITY_TYPES]
    return relation_mapper.connect(entities)"""
                st.code(_sample_py, language="python")
                st.caption("💡 import 관계를 분석해 모듈 간 의존성 그래프를 자동 생성합니다")

        if st.button("설정 없이 시작"):
            st.session_state.step = 2; st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# Step 2: 파일 업로드
# ════════════════════════════════════════════════════════════════════════════════
elif step == 2:
    if not _load_modules():
        st.stop()

    dc = st.session_state.domain_config
    header = f"{dc['app_icon']} {dc['name']} · 문서 업로드" if dc else "📂 문서 업로드"
    st.markdown(f"### {header}")
    st.caption("CSV·JSON·TXT·PDF·DOCX·MD 파일을 올리면 자동으로 구조를 파악하고 지식그래프를 만듭니다.")

    # ── 샘플 데이터 버튼 ─────────────────────────────────────────────────────
    st.markdown("""
    <style>div[data-testid="stButton"] button.sample {
      background:linear-gradient(135deg,#f0fdf4,#dcfce7) !important;
      color:#166534 !important; border:1.5px solid #86efac !important; }</style>
    """, unsafe_allow_html=True)

    col_s, _ = st.columns([2, 3])
    with col_s:
        sample_clicked = st.button(
            "샘플 데이터로 시작",
            use_container_width=True,
            help="data/ 폴더의 샘플 데이터를 자동으로 불러옵니다",
        )

    if sample_clicked:
        if not _load_modules():
            st.stop()
        with st.spinner("샘플 데이터를 불러오는 중..."):
            n = _load_sample_data()
        if n > 0:
            st.success(f"샘플 데이터 {n}개 파일 로드 완료!")
            if not st.session_state.domain_config:
                # 샘플 데이터 파일명으로 도메인 자동 감지
                _sample_files = [f for f in os.listdir("./data") if os.path.isfile(os.path.join("./data", f))]
                _detected = _quick_detect_domain(_sample_files)
                cfg = _build_domain_from_name(_detected)
                st.session_state.domain_config = cfg.to_dict()
                _apply_css(cfg.theme_color)
            st.session_state.step = 3; st.rerun()
        else:
            st.warning("data/ 폴더에 샘플 파일이 없습니다.")

    st.divider()

    # ── 탭: 파일 업로드 | 텍스트 직접 입력 ─────────────────────────────────
    tab_file, tab_text = st.tabs(["파일 업로드", "텍스트 직접 입력"])

    with tab_file:
        uploaded = st.file_uploader(
            "파일 업로드 (PDF, DOCX, TXT, MD, JSON, CSV, PY)",
            type=["pdf","docx","txt","md","json","csv","py"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )
        if uploaded:
            with st.spinner("파일 분석 중..."):
                n = _process_uploaded_files(uploaded)
            if n > 0:
                st.success(f"✅ {n}개 파일 처리 완료!")
                # 도메인 미설정 시 자동 감지 후 Step1 확인 화면으로
                if not st.session_state.domain_config:
                    detected = _quick_detect_domain([uf.name for uf in uploaded])
                    st.session_state["domain_suggestion"] = detected
                    st.session_state["suggest_countdown"] = 3
                    st.session_state.step = 1; st.rerun()
                else:
                    st.session_state.step = 3; st.rerun()

    with tab_text:
        st.markdown("회의록, 보고서, 메모 등 텍스트를 붙여넣으면 바로 분석합니다.")
        title_in = st.text_input("제목", placeholder="예: 2025년 1월 운영회의록",
                                  key="txt_title")
        body_in  = st.text_area("내용을 붙여넣으세요",
                                 height=280, key="txt_body",
                                 label_visibility="collapsed")
        if st.button("분석 시작", type="primary", key="btn_txt"):
            if not title_in.strip():
                st.error("제목을 입력해주세요.")
            elif not body_in.strip():
                st.error("내용을 입력해주세요.")
            else:
                with st.spinner("분석 중..."):
                    ok = _process_text_paste(title_in, body_in)
                if ok:
                    st.success("✅ 완료!")
                    if not st.session_state.domain_config:
                        cfg = _build_domain_from_name("비즈니스 운영")
                        st.session_state.domain_config = cfg.to_dict()
                    st.session_state.step = 3; st.rerun()
                else:
                    st.warning("이미 같은 제목의 문서가 있습니다.")

    # 기존 문서 있으면 바로 진행 버튼
    if st.session_state.documents:
        st.divider()
        st.info(f"📁 현재 {len(st.session_state.documents)}개 문서 로드됨")
        if st.button("결과 보기", type="primary"):
            st.session_state.step = 3; st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# Step 3: 결과 보기
# ════════════════════════════════════════════════════════════════════════════════
elif step == 3:
    if not _load_modules():
        st.stop()

    if not st.session_state.documents:
        st.warning("📂 문서가 없습니다.")
        if st.button("파일 업로드로 돌아가기"):
            st.session_state.step = 2; st.rerun()
        st.stop()

    dc = st.session_state.domain_config
    title_str = f"{dc['app_icon']} {dc['name']} · 분석 결과" if dc else "📊 분석 결과"
    st.markdown(f"### {title_str}")

    kg = st.session_state.kg
    stats = kg.get_stats()
    entity_colors = _get_entity_colors()
    domain_context = _get_domain_context()

    # 통계 바
    c1, c2, c3, c4 = st.columns(4)
    rag_cnt = 0
    try: rag_cnt = st.session_state.rag.document_count()
    except Exception: pass
    c1.metric("📄 로드된 파일", f"{len(st.session_state.documents)}개")
    c2.metric("🔵 테이블 연결됨", f"{stats['nodes']}개")
    c3.metric("↔️ 관계 파악", f"{stats['edges']}개")
    c4.metric("🔗 검색 청크", f"{rag_cnt}개")

    st.divider()

    # ════════════════════════════════════════════════════════════════════════
    # 업무 문장 → 데이터 추천 섹션
    # ════════════════════════════════════════════════════════════════════════
    with st.expander("🔍 업무 문장 → 필요한 데이터 추천", expanded=bool(st.session_state.qp_result)):
        qp_col1, qp_col2 = st.columns([4, 1])
        with qp_col1:
            qp_input = st.text_area(
                "업무 문장 입력",
                value=st.session_state.qp_input,
                height=80,
                placeholder="예: 다음 분기 신제품 프로모션 준비. 재고 현황 파악하고 작년 동기 판매량 비교 필요.",
                label_visibility="collapsed",
                key="qp_text",
            )
        with qp_col2:
            st.markdown("<div style='height:1.6rem'></div>", unsafe_allow_html=True)
            run_qp = st.button("분석", type="primary",
                               use_container_width=True, key="btn_qp")

        if run_qp and qp_input.strip():
            st.session_state.qp_input = qp_input
            st.session_state.qp_result = None  # 이전 결과 초기화
            with st.spinner("데이터 추천 분석 중..."):
                from modules.query_planner import plan as qp_plan
                st.session_state.qp_result = qp_plan(
                    qp_input.strip(),
                    rag            = st.session_state.rag,
                    kg             = st.session_state.kg,
                    claude         = st.session_state.claude,
                    domain_context = domain_context,
                )
            st.rerun()

        qp = st.session_state.qp_result
        if qp:
            # ── 의도 + 엔티티 요약 ───────────────────────────────────────
            st.markdown(
                f'<div style="background:#f0f9ff;border-left:4px solid #0284c7;'
                f'border-radius:8px;padding:.6rem 1rem;margin:.5rem 0;font-size:.9rem">'
                f'<b>📌 감지된 의도:</b> {qp.intent}</div>',
                unsafe_allow_html=True,
            )

            entity_badges = []
            _etype_colors = {
                "channel":   "#7c3aed", "product":  "#be185d",
                "geography": "#0369a1", "time":     "#b45309",
                "operation": "#065f46",
            }
            for etype, vals in qp.entities.items():
                color = _etype_colors.get(etype, "#475569")
                for v in vals[:3]:
                    entity_badges.append(
                        f'<span style="background:{color}1a;color:{color};border:1px solid {color}55;'
                        f'border-radius:12px;padding:1px 9px;font-size:.75rem;margin:2px">{v}</span>'
                    )
            if entity_badges:
                st.markdown("".join(entity_badges), unsafe_allow_html=True)

            qp_hdr_c1, qp_hdr_c2 = st.columns([4, 1])
            with qp_hdr_c1:
                st.markdown(f"**추천 데이터셋 {len(qp.datasets)}개**")
            with qp_hdr_c2:
                if st.button("닫기", key="qp_dismiss",
                             use_container_width=True):
                    st.session_state.qp_result = None
                    st.session_state.qp_input  = ""
                    st.rerun()

            # ── 데이터셋 카드 (3열 그리드) ───────────────────────────────
            card_cols = st.columns(3)
            for i, ds in enumerate(qp.datasets):
                conf_color = (
                    "#10b981" if ds.confidence >= 0.5
                    else "#f59e0b" if ds.confidence >= 0.2
                    else "#94a3b8"
                )
                tag = "🔗 FK 연관" if ds.is_expanded else "🎯 직접 매칭"

                with card_cols[i % 3]:
                    # 카드 헤더 + 추천 이유
                    st.markdown(
                        f'<div style="background:white;border:1px solid #e2e8f0;'
                        f'border-top:3px solid {conf_color};border-radius:10px;'
                        f'padding:.85rem;margin-bottom:.4rem">'
                        f'<div style="display:flex;justify-content:space-between;align-items:center">'
                        f'<b style="font-size:.95rem">{ds.table_name}</b>'
                        f'<span style="font-size:.7rem;color:{conf_color};font-weight:700">'
                        f'{int(ds.confidence*100)}%</span></div>'
                        f'<div style="font-size:.75rem;color:#64748b;margin:.2rem 0">{ds.description}</div>'
                        f'<div style="font-size:.78rem;color:#334155;margin:.2rem 0;'
                        f'padding:.3rem .5rem;background:#f8fafc;border-radius:6px">'
                        f'💡 <b>추천 이유:</b> {ds.reason}</div>'
                        + (
                            f'<div style="font-size:.77rem;color:#0369a1;margin:.2rem 0;'
                            f'padding:.3rem .5rem;background:#f0f9ff;border-radius:6px">'
                            f'🔍 <b>지금 확인할 질문:</b> {ds.check_question}</div>'
                            if ds.check_question else ""
                        )
                        + (
                            f'<div style="font-size:.77rem;color:#065f46;margin:.2rem 0;'
                            f'padding:.3rem .5rem;background:#f0fdf4;border-radius:6px">'
                            f'⚡ <b>다음 액션:</b> {ds.next_action}</div>'
                            if ds.next_action else ""
                        )
                        + f'<div style="font-size:.7rem;color:#94a3b8;margin-top:.3rem">{tag}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                    # 버튼 행
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("미리보기", key=f"qp_prev_{i}",
                                     use_container_width=True):
                            st.session_state[f"qp_preview_{i}"] = \
                                not st.session_state.get(f"qp_preview_{i}", False)
                            st.rerun()
                    with b2:
                        # check_question이 있으면 그걸 채팅 질문으로
                        chat_q = ds.check_question if ds.check_question else \
                                 f"{ds.table_name} 데이터 분석해줘. {qp.raw_input[:40]}"
                        if st.button("채팅으로 보내기", key=f"qp_chat_{i}",
                                     use_container_width=True):
                            st.session_state.pending_chat_message = chat_q
                            st.rerun()

                    # 미리보기 패널
                    if st.session_state.get(f"qp_preview_{i}", False):
                        import os
                        import pandas as _pd
                        from pathlib import Path as _Path
                        # Path traversal 방어: DATA_DIR 밖으로 나가는 경로 차단
                        _base = _Path("./data").resolve()
                        _target = (_base / _Path(ds.csv_file).name).resolve()
                        csv_path = str(_target) if str(_target).startswith(str(_base)) else None
                        if csv_path and os.path.exists(csv_path):
                            try:
                                _df = _pd.read_csv(csv_path, encoding="utf-8-sig", nrows=20)
                                st.caption(
                                    f"📊 {ds.csv_file} · {len(_df.columns)}컬럼 "
                                    f"· 상위 20행 표시"
                                )
                                st.dataframe(_df, use_container_width=True, height=200)
                                _pk_cols = [c for c in _df.columns
                                            if any(s in c.upper() for s in ["_ID","_CD","_NO","_KEY"])]
                                if _pk_cols:
                                    st.caption(f"🔑 주요 키 컬럼: {', '.join(_pk_cols[:5])}")
                            except Exception as _e:
                                st.warning(f"미리보기 실패: {_e}")
                        else:
                            st.caption(f"📁 `{ds.csv_file}` 파일 없음")

            # ── 관련 문서 추천 ───────────────────────────────────────────
            if qp.documents:
                st.markdown("**📄 관련 문서**")
                for docf in qp.documents:
                    st.caption(f"• {docf}")

    # ── 업무 문장 아래 채팅 예시 안내 (도메인별 동적 표시) ────
    _example_presets = _get_chat_presets()
    _example_label   = _example_presets[0][0] if _example_presets else "현재 운영 현황 요약해줘"
    _example_prompt  = _example_presets[0][1] if _example_presets else "현재 운영 현황 요약해줘"
    st.markdown(f"""
<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;
padding:.8rem 1rem;margin-top:.5rem">
<p style="margin:0;font-size:.85rem;color:#64748b">
<span style="font-weight:600;color:#475569">왼쪽 사이드바 채팅창에 이런 질문을 해보세요&nbsp;</span><code style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:4px;font-size:.85rem">{_example_label}</code>&nbsp;&larr; 복사해서 바로 입력해 보세요
</p>
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ════════════════════════════════════════════════════════════════════════
    # 일일 브리핑 섹션
    # ════════════════════════════════════════════════════════════════════════
    _DEMO_LIMIT_BRIEF = 20
    _brief_exhausted = st.session_state.chat_api_calls >= _DEMO_LIMIT_BRIEF

    with st.expander("📋 일일 브리핑 — 오늘의 운영 현황 4대 요약", expanded=bool(st.session_state.briefing_cards)):
        bc_col1, bc_col2 = st.columns([2, 1])
        with bc_col1:
            st.caption("재고 위험·채널 판매·발주 필요·이상 변화를 한눈에 파악하고 채팅으로 이어서 분석하세요.")
        with bc_col2:
            if _brief_exhausted:
                st.button("브리핑 생성", use_container_width=True, disabled=True, key="btn_brief_top")
            elif st.button("브리핑 생성", type="primary", use_container_width=True, key="btn_brief_top"):
                with st.spinner("4개 섹션 분석 중... (약 20~30초)"):
                    try:
                        st.session_state.briefing_cards = _generate_briefing_cards()
                        st.session_state.chat_api_calls += 1
                    except Exception as _e:
                        st.error(f"브리핑 생성 실패: {_e}")
                st.rerun()

        if st.session_state.briefing_cards:
            _bc_x_col, _ = st.columns([1, 4])
            with _bc_x_col:
                if st.button("닫기", key="brief_dismiss",
                             use_container_width=True):
                    st.session_state.briefing_cards = None
                    st.rerun()

        cards = st.session_state.briefing_cards
        if cards:
            _CARD_COLORS = {
                "inventory":     "#ef4444",
                "channel":       "#0284c7",
                "replenishment": "#d97706",
                "anomaly":       "#7c3aed",
            }
            # 2×2 그리드 — 첫 줄(0,1), 둘째 줄(2,3)
            for row in range(2):
                row_cols = st.columns(2, gap="large")
                for col in range(2):
                    i = row * 2 + col
                    if i >= len(cards):
                        break
                    card = cards[i]
                    clr = _CARD_COLORS.get(card["id"], "#64748b")
                    with row_cols[col]:
                        # 카드 헤더
                        st.markdown(
                            f'<div style="border-top:3px solid {clr};border-radius:8px 8px 0 0;'
                            f'background:{clr}0d;padding:.6rem 1rem;font-weight:700;font-size:1rem;'
                            f'margin-bottom:.4rem">'
                            f'{card["icon"]} {card["title"]}</div>',
                            unsafe_allow_html=True,
                        )
                        # 한 줄 요약
                        st.caption(card["summary"])
                        # 핵심 수치
                        if card["metrics"]:
                            m_cols = st.columns(len(card["metrics"]))
                            for mi, met in enumerate(card["metrics"]):
                                m_cols[mi].metric(met["label"], met["value"])
                        # 차트 — 2열이므로 높이 여유 확보
                        if card.get("chart"):
                            st.plotly_chart(card["chart"], use_container_width=True,
                                            key=f"brief_chart_{card['id']}")
                        # 지금 해야 할 일
                        st.markdown("**지금 해야 할 일**")
                        for act in card["actions"]:
                            st.markdown(f"• {act}")
                        # 채팅으로 이어서 질문 버튼
                        if st.button("채팅으로 이어서 질문",
                                     key=f"brief_chat_{card['id']}",
                                     use_container_width=True):
                            st.session_state.pending_chat_message = card["chat_prompt"]
                            st.rerun()
                if row == 0 and len(cards) > 2:
                    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    st.divider()

    # ── Step 3 사이드바: 채팅 패널 ─────────────────────────────────────────────
    _DEMO_LIMIT = 20
    _ROUTE_BADGE = {
        "data":     ("📊", "#0284c7", "데이터 기반"),
        "doc":      ("📄", "#7c3aed", "문서 기반"),
        "combined": ("🔗", "#059669", "결합 분석"),
        "briefing": ("📋", "#d97706", "일일 브리핑"),
    }
    with st.sidebar:
        _render_db_status()
        used      = st.session_state.chat_api_calls
        left      = _DEMO_LIMIT - used
        exhausted = used >= _DEMO_LIMIT

        # ── 헤더: 제목 + 사용량 배지 ─────────────────────────
        badge_color = "#10b981" if left > 5 else ("#f59e0b" if left > 0 else "#ef4444")
        st.markdown(
            f'<div style="display:flex;align-items:center;justify-content:space-between;'
            f'margin-bottom:.3rem">'
            f'<span style="font-size:1.1rem;font-weight:700">데이터 채팅</span>'
            f'<span style="background:{badge_color};color:white;border-radius:20px;'
            f'padding:2px 10px;font-size:.78rem;font-weight:700">'
            f'데모 사용량: {used}/{_DEMO_LIMIT}</span></div>',
            unsafe_allow_html=True,
        )
        # ── 예시 질문 버튼 (세로 한 줄, 컴팩트) ─────────────
        _PRESETS_Q = _get_chat_presets()
        st.markdown(
            '<style>section[data-testid="stSidebar"] div[data-testid="stButton"]>button{'
            'font-size:11px!important;padding:2px 8px!important;'
            'min-height:26px!important;height:auto!important;line-height:1.3!important;'
            'white-space:nowrap!important;overflow:hidden!important;'
            'text-overflow:ellipsis!important;}'
            'section[data-testid="stSidebar"] div[data-testid="stButton"]{'
            'margin-top:0!important;margin-bottom:0!important;}</style>'
            '<p style="margin:0 0 2px;font-size:.8rem;color:#64748b">'
            '질문만 입력하면 문서·데이터·지식그래프를 자동으로 결합해 답변합니다.</p>'
            '<div style="margin-bottom:-1rem">'
            '<p style="margin:0;font-size:.75rem;color:#94a3b8">클릭하면 바로 질문됩니다</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        for idx, (label, prompt) in enumerate(_PRESETS_Q):
            if st.button(label, key=f"qbtn_{idx}",
                         use_container_width=True, disabled=exhausted):
                st.session_state.chat_preset_input = prompt
                st.rerun()

        # ── 채팅 히스토리 표시 ───────────────────────────────
        chat_box = st.container(height=460)
        with chat_box:
            if not st.session_state.chat_history:
                st.markdown(
                    '<div style="color:#94a3b8;font-size:.85rem;padding:.5rem 0">'
                    '위 버튼을 클릭하거나 아래에 직접 입력하세요.</div>',
                    unsafe_allow_html=True,
                )
            else:
                for entry in st.session_state.chat_history:
                    with st.chat_message(entry["role"]):
                        st.markdown(entry["content"])

                        # 메트릭 카드 렌더링
                        metrics = entry.get("metrics", [])
                        if metrics and entry["role"] == "assistant":
                            m_cols = st.columns(min(len(metrics), 3))
                            for mi, met in enumerate(metrics):
                                m_cols[mi % 3].metric(
                                    met.get("label", ""),
                                    met.get("value", ""),
                                    delta=met.get("delta"),
                                )

                        # 차트 렌더링
                        for chart in entry.get("charts", []):
                            st.plotly_chart(chart, use_container_width=True)

                        # 근거 표시 (assistant 메시지만)
                        if entry["role"] == "assistant":
                            route      = entry.get("route", "combined")
                            datasets   = entry.get("datasets", [])
                            documents  = entry.get("documents", [])
                            kg_nodes   = entry.get("kg_nodes", 0)
                            icon_r, clr, lbl = _ROUTE_BADGE.get(
                                route, ("🔗", "#059669", "결합 분석")
                            )
                            parts_html = [
                                f'<span style="background:{clr};color:white;border-radius:12px;'
                                f'padding:1px 8px;font-size:.72rem;font-weight:700;margin-right:4px">'
                                f'{icon_r} {lbl}</span>'
                            ]
                            for ds in datasets:
                                parts_html.append(
                                    f'<span style="background:#f1f5f9;color:#475569;border-radius:10px;'
                                    f'padding:1px 7px;font-size:.7rem;margin-right:3px">📊 {ds}</span>'
                                )
                            for doc in documents:
                                parts_html.append(
                                    f'<span style="background:#f1f5f9;color:#475569;border-radius:10px;'
                                    f'padding:1px 7px;font-size:.7rem;margin-right:3px">📄 {doc}</span>'
                                )
                            if kg_nodes > 0:
                                parts_html.append(
                                    f'<span style="background:#f1f5f9;color:#475569;border-radius:10px;'
                                    f'padding:1px 7px;font-size:.7rem">🕸️ KG {kg_nodes}노드</span>'
                                )
                            if len(parts_html) > 1:  # 라우트 배지 외 근거가 있을 때만
                                st.markdown(
                                    '<div style="margin-top:.5rem;opacity:.85">'
                                    + "".join(parts_html) + "</div>",
                                    unsafe_allow_html=True,
                                )

        # ── 사용량 초과 배너 ─────────────────────────────────
        if exhausted:
            st.error(
                "🚫 **데모 버전 사용량 초과** — 이번 세션에서 최대 20회 사용 가능합니다.",
                icon=None,
            )

        # ── 채팅 입력 ────────────────────────────────────────
        # pending_chat_message: 브리핑/추천 버튼에서 자동 전송할 메시지
        preset = (
            st.session_state.pop("pending_chat_message", None)
            or st.session_state.pop("chat_preset_input", None)
        )
        user_input = st.chat_input(
            "예: 재고 위험 상품 알려줘, 판매 TOP3는?",
            key="chat_in",
            disabled=exhausted,
        ) or preset

        if user_input and not exhausted:
            # 사용자 메시지 즉시 히스토리에 추가
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input,
                 "charts": [], "datasets": [], "documents": [], "kg_nodes": 0, "route": ""}
            )
            _chat_success = False
            try:
                from modules.chat_copilot import respond_stream
                gen, meta = respond_stream(
                    user_input,
                    claude         = st.session_state.claude,
                    rag            = st.session_state.rag,
                    kg             = st.session_state.kg,
                    domain_context = domain_context,
                )
                with chat_box:
                    with st.chat_message("assistant"):
                        streamed_text = st.write_stream(gen)
                _chat_success = True
            except Exception as e:
                streamed_text = f"오류가 발생했습니다: {e}"
                meta = None

            # 성공 시에만 카운트 증가
            if _chat_success:
                st.session_state.chat_api_calls += 1
            st.session_state.chat_history.append({
                "role":      "assistant",
                "content":   streamed_text if isinstance(streamed_text, str) else str(streamed_text),
                "charts":    meta.charts if meta else [],
                "datasets":  meta.datasets if meta else [],
                "documents": meta.documents if meta else [],
                "kg_nodes":  meta.kg_nodes if meta else 0,
                "route":     meta.route if meta else "combined",
                "metrics":   getattr(meta, "metrics", []) if meta else [],
            })
            st.rerun()

    # ════════════════════════════════════════════════════════
    # 메인: 지식그래프 + AI 분석 탭 (full width)
    # ════════════════════════════════════════════════════════
    # ── 지식그래프 ───────────────────────────────────────
    st.markdown("#### 지식 그래프")

    if stats["nodes"] == 0:
        st.info("CSV·JSON·TXT·PDF 문서를 업로드하면 엔티티 관계 그래프가 나타납니다.")
    else:
        if stats["entity_types"]:
            legend_html = "".join(
                f'<span class="badge" style="background:{entity_colors.get(t,"#9E9E9E")};color:white">'
                f'{t} ({cnt})</span>'
                for t, cnt in stats["entity_types"].items()
            )
            st.markdown(legend_html, unsafe_allow_html=True)

        kg_tab_erd, kg_tab_graph, kg_tab_flow = st.tabs(["ERD 테이블 뷰", "노드 그래프", "데이터 흐름 뷰"])

        with kg_tab_graph:
            html_path = kg.render_html(entity_colors=entity_colors)
            if html_path and os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                components.html(html_content, height=620, scrolling=False)
            else:
                st.error("그래프 렌더링 실패")

        with kg_tab_erd:
            _table_nodes = {nid: attrs for nid, attrs in kg.graph.nodes(data=True)
                           if attrs.get("type") in ("master_table", "fact_table", "csv_table")}
            if not _table_nodes:
                st.info("테이블 노드가 없습니다. CSV나 JSON 스키마를 업로드하세요.")
            else:
                _erd_cols = st.columns(min(len(_table_nodes), 3))
                for idx, (nid, attrs) in enumerate(_table_nodes.items()):
                    _ttype = attrs.get("type", "default")
                    _color = {"master_table": "#7C3AED", "fact_table": "#2563EB", "csv_table": "#0D9488"}.get(_ttype, "#6B7280")
                    _label = {"master_table": "MASTER", "fact_table": "FACT", "csv_table": "CSV"}.get(_ttype, "TABLE")
                    _cols = attrs.get("columns", [])
                    _fk_cols = attrs.get("fk_cols", [])
                    # FK edges
                    _out = [(t, kg.graph[nid][t].get("relation", "")) for t in kg.graph.successors(nid)]
                    _in  = [(s, kg.graph[s][nid].get("relation", "")) for s in kg.graph.predecessors(nid)]

                    col_html = ""
                    for c in _cols[:20]:
                        is_fk = c in _fk_cols
                        col_html += f'<div style="padding:1px 6px;font-size:.78rem;color:{"#fbbf24" if is_fk else "#e2e8f0"}">{c}{"  🔑" if is_fk else ""}</div>'
                    if len(_cols) > 20:
                        col_html += f'<div style="font-size:.72rem;color:#64748b">... 외 {len(_cols)-20}개</div>'

                    edge_html = ""
                    for tgt, rel in _out:
                        edge_html += f'<div style="font-size:.75rem;color:#6ee7b7">→ {tgt} <span style="color:#475569">({rel})</span></div>'
                    for src, rel in _in:
                        edge_html += f'<div style="font-size:.75rem;color:#93c5fd">← {src} <span style="color:#475569">({rel})</span></div>'

                    with _erd_cols[idx % min(len(_table_nodes), 3)]:
                        st.markdown(
                            f'<div style="background:#0f172a;border:2px solid {_color};border-radius:8px;'
                            f'padding:.6rem;margin-bottom:.5rem">'
                            f'<div style="font-weight:700;color:white;font-size:.9rem;border-bottom:1px solid #1e293b;padding-bottom:4px;margin-bottom:4px">{nid}</div>'
                            f'<span style="background:{_color};color:white;border-radius:4px;padding:1px 6px;font-size:.65rem;font-weight:700">{_label}</span>'
                            f'<div style="margin-top:6px">{col_html}</div>'
                            f'{"<div style=\"margin-top:6px;border-top:1px solid #1e293b;padding-top:4px\">" + edge_html + "</div>" if edge_html else ""}'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                        if st.button(f"{nid} 분석", key=f"erd_chat_{nid}", use_container_width=True):
                            st.session_state.pending_chat_message = f"{nid} 테이블 설명해줘"
                            st.rerun()

        with kg_tab_flow:
            _mst_nodes = [nid for nid, attrs in kg.graph.nodes(data=True)
                          if attrs.get("type") == "master_table"]
            _fact_nodes = [nid for nid, attrs in kg.graph.nodes(data=True)
                           if attrs.get("type") == "fact_table"]
            if not _mst_nodes and not _fact_nodes:
                st.info("MST/FACT 테이블 구조가 없습니다.")
            else:
                # MST → FACT 방향 흐름도 (HTML)
                flow_lines = []
                for src in _mst_nodes:
                    for tgt in kg.graph.successors(src):
                        if tgt in _fact_nodes:
                            rel = kg.graph[src][tgt].get("relation", "")
                            flow_lines.append(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                                f'<span style="background:#7C3AED;color:white;padding:4px 10px;border-radius:6px;font-size:.82rem;font-weight:600;min-width:140px;text-align:center">{src}</span>'
                                f'<span style="color:#64748b;font-size:1.2rem">→</span>'
                                f'<span style="background:#475569;color:#e2e8f0;padding:2px 8px;border-radius:10px;font-size:.72rem">{rel}</span>'
                                f'<span style="color:#64748b;font-size:1.2rem">→</span>'
                                f'<span style="background:#2563EB;color:white;padding:4px 10px;border-radius:6px;font-size:.82rem;font-weight:600;min-width:180px;text-align:center">{tgt}</span>'
                                f'</div>')
                for src in _fact_nodes:
                    for tgt in kg.graph.successors(src):
                        if tgt in _mst_nodes:
                            rel = kg.graph[src][tgt].get("relation", "")
                            flow_lines.append(f'<div style="display:flex;align-items:center;gap:8px;margin:4px 0">'
                                f'<span style="background:#2563EB;color:white;padding:4px 10px;border-radius:6px;font-size:.82rem;font-weight:600;min-width:180px;text-align:center">{src}</span>'
                                f'<span style="color:#64748b;font-size:1.2rem">→</span>'
                                f'<span style="background:#475569;color:#e2e8f0;padding:2px 8px;border-radius:10px;font-size:.72rem">{rel}</span>'
                                f'<span style="color:#64748b;font-size:1.2rem">→</span>'
                                f'<span style="background:#7C3AED;color:white;padding:4px 10px;border-radius:6px;font-size:.82rem;font-weight:600;min-width:140px;text-align:center">{tgt}</span>'
                                f'</div>')
                if flow_lines:
                    st.markdown(
                        '<div style="display:flex;gap:12px;margin-bottom:8px">'
                        '<span style="background:#7C3AED;color:white;padding:2px 10px;border-radius:4px;font-size:.75rem">MST (마스터)</span>'
                        '<span style="background:#2563EB;color:white;padding:2px 10px;border-radius:4px;font-size:.75rem">FACT (팩트)</span>'
                        '</div>',
                        unsafe_allow_html=True)
                    st.markdown("".join(flow_lines), unsafe_allow_html=True)
                else:
                    st.info("MST ↔ FACT 간 직접 연결이 없습니다.")

        with st.expander("특정 문서 그래프 재추출"):
            sel_doc = st.selectbox("문서 선택", list(st.session_state.documents.keys()),
                                    key="kg_re_sel")
            if st.button("재추출", key="btn_reextract"):
                with st.spinner("재추출 중..."):
                    _extract_kg_with_domain(st.session_state.documents[sel_doc])
                st.success(f"완료! 노드 {kg.get_stats()['nodes']}개")
                st.rerun()

    st.divider()

    # ── 하단 탭 ──────────────────────────────────────────
    tab_ai, tab_rag, tab_num = st.tabs(["AI 분석", "문서 검색 (RAG)", "번호 조회"])

    with tab_ai:
        from modules.prompt_loader import load_prompt

        _ai_exhausted = st.session_state.chat_api_calls >= _DEMO_LIMIT
        if _ai_exhausted:
            st.warning("🚫 데모 사용량 초과 — AI 분석 기능이 비활성화되었습니다.")

        doc_names = list(st.session_state.documents.keys())
        sel = st.selectbox("분석 문서", ["📚 전체 합치기"] + doc_names, key="ai_sel")
        if sel == "📚 전체 합치기":
            atxt = "\n\n---\n\n".join(f"[{k}]\n{v}" for k, v in st.session_state.documents.items())
        else:
            atxt = st.session_state.documents[sel]
        MAX_C = 8000
        if len(atxt) > MAX_C:
            st.caption(f"ℹ️ 처음 {MAX_C:,}자만 분석합니다.")
            atxt = atxt[:MAX_C]

        # ── 4개 버튼 + 선택 입력 ──────────────────────────────
        _opt_cols = st.columns([3, 2])
        with _opt_cols[0]:
            issue = st.text_input("원인분석 초점 (선택)", placeholder="예: 납기 지연 원인",
                                   key="issue_h", label_visibility="collapsed")
        with _opt_cols[1]:
            rdate = st.date_input("보고서 날짜", value=datetime.today(),
                                   key="rpt_dt", label_visibility="collapsed")

        _ab1, _ab2, _ab3, _ab4 = st.columns(4)
        with _ab1:
            _run_sum  = st.button("📝 요약",       use_container_width=True,
                                   disabled=_ai_exhausted, key="btn_sum")
        with _ab2:
            _run_act  = st.button("✅ 액션 아이템", use_container_width=True,
                                   disabled=_ai_exhausted, key="btn_act")
        with _ab3:
            _run_root = st.button("🔍 원인 분석",  use_container_width=True,
                                   disabled=_ai_exhausted, key="btn_root")
        with _ab4:
            _run_rpt  = st.button("📊 보고서",     use_container_width=True,
                                   disabled=_ai_exhausted, key="btn_rpt")

        st.divider()

        if _run_sum:
            with st.spinner("요약 중..."):
                r = st.session_state.claude.generate(
                    load_prompt("summarize", document=atxt, domain_context=domain_context))
            st.session_state.chat_api_calls += 1
            st.markdown(r)
            st.download_button("💾 다운로드", r,
                f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

        elif _run_act:
            with st.spinner("액션 아이템 추출 중..."):
                r = st.session_state.claude.generate(
                    load_prompt("action_items", document=atxt, domain_context=domain_context))
            st.session_state.chat_api_calls += 1
            st.markdown(r)
            st.download_button("💾 다운로드", r,
                f"actions_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")
            # 연관 데이터셋 badge
            with st.spinner("연관 데이터셋 분석 중..."):
                try:
                    from modules.query_planner import plan as _qp_plan
                    _act_plan = _qp_plan(r[:500], rag=None, kg=None, claude=None,
                                         domain_context=domain_context)
                    if _act_plan.datasets:
                        st.markdown("---\n**📊 이 액션과 관련된 데이터셋**")
                        _ds_badges = []
                        for _ds in _act_plan.datasets[:6]:
                            _c = "#10b981" if _ds.confidence >= 0.5 else "#f59e0b"
                            _ds_badges.append(
                                f'<span style="background:{_c}1a;color:{_c};'
                                f'border:1px solid {_c}55;border-radius:12px;'
                                f'padding:2px 10px;font-size:.78rem;margin:2px;display:inline-block">'
                                f'📊 {_ds.table_name} '
                                f'<span style="opacity:.7">{int(_ds.confidence*100)}%</span></span>'
                            )
                        st.markdown("".join(_ds_badges), unsafe_allow_html=True)
                        if st.button("데이터 추천 자세히 보기", key="act_to_qp"):
                            st.session_state.qp_input  = r[:200]
                            st.session_state.qp_result = _act_plan
                            st.rerun()
                except (ImportError, ValueError, KeyError):
                    pass

        elif _run_root:
            doc = f"[분석초점: {issue}]\n\n{atxt}" if issue.strip() else atxt
            with st.spinner("원인 분석 중..."):
                r = st.session_state.claude.generate(
                    load_prompt("root_cause", document=doc, domain_context=domain_context))
            st.session_state.chat_api_calls += 1
            st.markdown(r)
            st.download_button("💾 다운로드", r,
                f"rootcause_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

        elif _run_rpt:
            with st.spinner("보고서 작성 중..."):
                r = st.session_state.claude.generate(
                    load_prompt("report_draft", document=atxt,
                        date=rdate.strftime("%Y년 %m월 %d일"), domain_context=domain_context))
            st.session_state.chat_api_calls += 1
            st.markdown(r, unsafe_allow_html=True)
            st.download_button("💾 다운로드", r,
                f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

    with tab_rag:
        from modules.prompt_loader import load_prompt
        q = st.text_area("질문 입력", placeholder="업로드한 문서에 대해 질문하세요.",
                          height=80, key="rag_q")
        rc1, rc2 = st.columns([1, 3])
        with rc1: top_k = st.slider("검색 수", 1, 10, 5, key="rag_k")
        with rc2: show_src = st.checkbox("출처 청크 보기", value=True, key="rag_src")

        if st.button("검색 및 답변", type="primary", key="btn_rag") and q.strip():
            with st.spinner("검색 중..."):
                hits = st.session_state.rag.query(q, n_results=top_k)
            if not hits:
                st.warning("검색 결과 없음")
            else:
                context = "\n\n---\n\n".join(f"[출처 {i+1}: {h['filename']}]\n{h['text']}"
                                              for i, h in enumerate(hits))
                with st.spinner("답변 생성 중..."):
                    ans = st.session_state.claude.generate(
                        load_prompt("rag_query", question=q, context=context,
                                    domain_context=domain_context))
                st.markdown("#### 💬 답변")
                st.markdown(ans)
                if show_src:
                    st.markdown("#### 📎 출처")
                    for i, h in enumerate(hits, 1):
                        with st.expander(f"출처 {i}: `{h['filename']}` (유사도: {h['score']:.3f})"):
                            st.write(h["text"])

    with tab_num:
        if stats["nodes"] == 0:
            st.info("지식그래프가 필요합니다. CSV·JSON·문서를 업로드하세요.")
        else:
            qi = st.text_input("번호 또는 이름 입력",
                placeholder="예: PRD001, order_id, 고객테이블, 제품코드...", key="num_q")
            nc1, nc2 = st.columns([1, 3])
            with nc1: depth = st.selectbox("탐색 깊이", [1, 2, 3], key="num_d")
            with nc2: use_rag = st.checkbox("문서에서도 검색 (RAG)", value=True, key="num_r")

            if st.button("조회", type="primary", key="btn_num") and qi.strip():
                query = qi.strip()
                visited, frontier = set(), set()
                init_r = kg.query_by_id(query)

                if not init_r["matched_nodes"]:
                    st.warning(f"'{query}' 와 일치하는 노드가 없습니다.")
                    st.caption(f"현재 노드: {', '.join(list(kg.graph.nodes)[:20])}")
                else:
                    for n in init_r["matched_nodes"]: frontier.add(n["id"])
                    visited.update(frontier)
                    all_nodes = list(init_r["matched_nodes"])
                    all_edges = list(init_r["edges"])

                    for _ in range(depth - 1):
                        nxt = set()
                        for nid in frontier:
                            sub = kg.query_by_id(nid)
                            for n in sub["connected_nodes"] + sub["matched_nodes"]:
                                if n["id"] not in visited:
                                    visited.add(n["id"]); nxt.add(n["id"]); all_nodes.append(n)
                            for e in sub["edges"]:
                                if e not in all_edges: all_edges.append(e)
                        frontier = nxt

                    st.markdown(f"##### 🔵 연결 노드 {len(all_nodes)}개")
                    ncols = st.columns(min(len(all_nodes), 3))
                    for i, node in enumerate(all_nodes):
                        color = entity_colors.get(node.get("type", "default"), "#9E9E9E")
                        with ncols[i % 3]:
                            st.markdown(
                                f'<div class="card">'
                                f'<span class="badge" style="background:{color};color:white">'
                                f'{node.get("type","?")}</span><br>'
                                f'<b>{node["label"]}</b><br><code>{node["id"]}</code></div>',
                                unsafe_allow_html=True
                            )
                    if all_edges:
                        st.markdown("##### ↔️ 관계")
                        for e in all_edges[:20]:
                            st.caption(f"  {e['source']} → **{e['relation']}** → {e['target']}")

                    if use_rag and st.session_state.rag:
                        from modules.prompt_loader import load_prompt
                        hits = st.session_state.rag.query(query, n_results=3)
                        if hits:
                            ctx = "\n\n".join(f"[{h['filename']}]\n{h['text']}" for h in hits)
                            with st.spinner("문서 검색 중..."):
                                ans = st.session_state.claude.generate(
                                    load_prompt("rag_query",
                                        question=f"{query}에 대한 정보를 알려주세요",
                                        context=ctx, domain_context=domain_context))
                            st.markdown("##### 📄 관련 문서 내용")
                            st.markdown(ans)

