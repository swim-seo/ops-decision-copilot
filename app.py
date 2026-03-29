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
  border:1px solid #e2e8f0; border-left:3px solid {primary}; padding:.75rem; }}
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
    "뷰티":    [("수요 분석",  "FG-002 선크림 수요 그래프 그려줘"),
                ("재고 위험",  "재고 위험 상품 알려줘"),
                ("판매 TOP3", "여름에 잘 팔리는 상품 TOP3"),
                ("채널 비교",  "채널별 판매 현황 비교해줘"),
                ("품절 위험",  "품절 위험 상품 있어?")],
    "공급망":  [("수요 예측",  "주요 상품 수요 그래프 그려줘"),
                ("재고 위험",  "재고 위험 상품 알려줘"),
                ("발주 현황",  "발주가 필요한 상품 알려줘"),
                ("채널 비교",  "채널별 판매 현황 비교해줘"),
                ("품절 위험",  "품절 위험 상품 있어?")],
    "에너지":  [("소비 분석",  "에너지 소비 추이 그려줘"),
                ("위험 설비",  "위험 설비 현황 알려줘"),
                ("피크 시간",  "피크 소비 시간대 알려줘"),
                ("비용 분석",  "에너지 비용 분석해줘"),
                ("이상 감지",  "이상 소비 있어?")],
    "제조":    [("생산 현황",  "생산 실적 그래프 그려줘"),
                ("불량 현황",  "불량률 높은 라인 알려줘"),
                ("설비 위험",  "설비 위험 현황 알려줘"),
                ("납기 분석",  "납기 지연 현황 분석해줘"),
                ("가동률",     "라인별 가동률 비교해줘")],
    "물류":    [("배송 현황",  "배송 현황 그래프 그려줘"),
                ("지연 위험",  "납기 지연 위험 알려줘"),
                ("재고 현황",  "창고별 재고 현황 알려줘"),
                ("비용 분석",  "운송 비용 분석해줘"),
                ("SLA 현황",   "SLA 달성률 알려줘")],
    "금융":    [("수익 분석",  "포트폴리오 수익 그래프 그려줘"),
                ("리스크",     "고위험 자산 알려줘"),
                ("수익 TOP3",  "수익률 TOP3 알려줘"),
                ("VaR 현황",   "VaR 현황 분석해줘"),
                ("이상 감지",  "이상 변동 있어?")],
}
_DEFAULT_CHAT_PRESETS = [
    ("데이터 분석",  "핵심 데이터 현황 분석해줘"),
    ("위험 파악",   "현재 위험 요소 알려줘"),
    ("TOP 항목",   "상위 항목 TOP3 알려줘"),
    ("비교 분석",   "카테고리별 현황 비교해줘"),
    ("이상 감지",   "이상 변화 있어?"),
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
    if st.session_state.domain_config:
        from modules.domain_adapter import DomainConfig
        return DomainConfig.from_dict(st.session_state.domain_config).to_context_string()
    return _DEFAULT_DOMAIN_CONTEXT

def _get_entity_colors() -> dict:
    if st.session_state.domain_config:
        return st.session_state.domain_config.get("entity_types", DEFAULT_ENTITY_COLORS)
    return DEFAULT_ENTITY_COLORS

def _get_theme_color() -> str:
    if st.session_state.domain_config:
        return st.session_state.domain_config.get("theme_color", "#2563EB")
    return "#2563EB"

def _get_collection_name() -> str:
    if st.session_state.domain_config:
        from modules.domain_adapter import DomainConfig
        return DomainConfig.from_dict(st.session_state.domain_config).collection_name
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
    for t in schema.get("tables", []):
        lines.append(f"[테이블] {t['table_name']} — {t.get('description','')}")
        for c in t.get("columns", []):
            pk = " (PK)" if c.get("pk") else ""
            lines.append(f"  컬럼: {c['name']} ({c.get('type','')}){pk}")
    for r in schema.get("relationships", []):
        lines.append(f"[JOIN] {r['from']} → {r['to']}  키: {r.get('join_key','')}")
    return "\n".join(lines)

def _extract_kg_with_domain(text: str):
    """도메인 컨텍스트를 포함해 Claude로 엔티티·관계 추출 (Issue#1 수정)."""
    from modules.knowledge_graph import build_entity_extraction_prompt
    if st.session_state.domain_config:
        from modules.domain_adapter import DomainConfig
        dc_obj = DomainConfig.from_dict(st.session_state.domain_config)
        entity_types_desc = dc_obj.get_entity_types_description()
        domain_ctx_header = f"[도메인 컨텍스트]\n{_get_domain_context()}\n\n"
    else:
        entity_types_desc = (
            "- person: 사람, 담당자\n- organization: 조직, 팀\n"
            "- issue: 문제, 이슈\n- decision: 결정 사항\n- metric: 지표, 수치"
        )
        domain_ctx_header = ""
    template = build_entity_extraction_prompt(entity_types_desc)
    # 프롬프트 인젝션 방어: 문서 내 역할 덮어쓰기 패턴 필터링
    from modules.chat_copilot import sanitize_input
    safe_text = sanitize_input(text, max_len=3000)
    prompt = domain_ctx_header + template.replace("{document}", safe_text)
    response = st.session_state.claude.generate(prompt, max_tokens=4096)
    st.session_state.kg.build_from_claude_json(response)

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
    kg_targets = [fname for fname in new_files if fname not in kg_direct]
    if kg_targets:
        from concurrent.futures import ThreadPoolExecutor, as_completed
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(_extract_kg_with_domain, st.session_state.documents[fname]): fname
                for fname in kg_targets
            }
            for future in as_completed(futures):
                try:
                    future.result()
                except (ValueError, IOError) as e:
                    st.warning(f"⚠️ KG 추출 실패 ({futures[future]}): {e}")

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


def _load_sample_data() -> int:
    data_dir = "./data"
    if not os.path.isdir(data_dir):
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
    except ImportError:
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
    c1.metric("📄 문서", len(st.session_state.documents))
    c2.metric("🔵 노드", stats["nodes"])
    c3.metric("↔️ 엣지", stats["edges"])
    rag_cnt = 0
    try: rag_cnt = st.session_state.rag.document_count()
    except Exception: pass
    c4.metric("🔗 RAG 청크", rag_cnt)

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
        st.caption("질문만 입력하면 문서·데이터·지식그래프를 자동으로 결합해 답변합니다.")

        # ── 예시 질문 버튼 (도메인에 따라 동적) ─────────────
        _PRESETS_Q = _get_chat_presets()
        cols_q = st.columns(len(_PRESETS_Q))
        for i, (label, prompt) in enumerate(_PRESETS_Q):
            with cols_q[i]:
                if st.button(label, key=f"qbtn_{i}",
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

        kg_tab_graph, kg_tab_erd, kg_tab_flow = st.tabs(["노드 그래프", "ERD 테이블 뷰", "데이터 흐름 뷰"])

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

        s1, s2, s3, s4 = st.tabs(["요약", "액션 아이템", "원인 분석", "보고서"])

        with s1:
            if st.button("요약 생성", key="btn_sum", disabled=_ai_exhausted):
                with st.spinner("요약 중..."):
                    r = st.session_state.claude.generate(
                        load_prompt("summarize", document=atxt, domain_context=domain_context))
                st.session_state.chat_api_calls += 1
                st.markdown(r)
                st.download_button("💾 다운로드", r,
                    f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

        with s2:
            if st.button("액션 아이템 추출", key="btn_act", disabled=_ai_exhausted):
                with st.spinner("추출 중..."):
                    r = st.session_state.claude.generate(
                        load_prompt("action_items", document=atxt, domain_context=domain_context))
                st.session_state.chat_api_calls += 1
                st.markdown(r)
                st.download_button("💾 다운로드", r,
                    f"actions_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

                # ── 연관 데이터셋 badge 표시 ─────────────────────────
                with st.spinner("연관 데이터셋 분석 중..."):
                    try:
                        from modules.query_planner import plan as _qp_plan, _SCHEMA_REGISTRY
                        _act_plan = _qp_plan(
                            r[:500],  # 액션 아이템 텍스트 첫 500자 기준
                            rag=None, kg=None, claude=None,  # rule-only (빠르게)
                            domain_context=domain_context,
                        )
                        if _act_plan.datasets:
                            st.markdown("---\n**📊 이 액션과 관련된 데이터셋**")
                            _ds_badges = []
                            for _ds in _act_plan.datasets[:6]:
                                _c = "#10b981" if _ds.confidence >= 0.5 else "#f59e0b"
                                _ds_badges.append(
                                    f'<span style="background:{_c}1a;color:{_c};'
                                    f'border:1px solid {_c}55;border-radius:12px;'
                                    f'padding:2px 10px;font-size:.78rem;margin:2px;'
                                    f'display:inline-block">'
                                    f'📊 {_ds.table_name} '
                                    f'<span style="opacity:.7">{int(_ds.confidence*100)}%</span></span>'
                                )
                                if _ds.next_action:
                                    _ds_badges.append(
                                        f'<div style="font-size:.73rem;color:#475569;'
                                        f'margin:1px 0 4px 8px">⚡ {_ds.next_action}</div>'
                                    )
                            st.markdown("".join(_ds_badges), unsafe_allow_html=True)
                            # 쿼리 플래너로 보내기
                            if st.button("데이터 추천 자세히 보기",
                                         key="act_to_qp", use_container_width=False):
                                st.session_state.qp_input  = r[:200]
                                st.session_state.qp_result = _act_plan
                                st.rerun()
                    except (ImportError, ValueError, KeyError):
                        pass

        with s3:
            issue = st.text_input("특정 문제 (선택)", placeholder="예: 납기 지연 원인", key="issue_h")
            if st.button("원인 분석", key="btn_root", disabled=_ai_exhausted):
                doc = f"[분석초점: {issue}]\n\n{atxt}" if issue else atxt
                with st.spinner("분석 중..."):
                    r = st.session_state.claude.generate(
                        load_prompt("root_cause", document=doc, domain_context=domain_context))
                st.session_state.chat_api_calls += 1
                st.markdown(r)
                st.download_button("💾 다운로드", r,
                    f"rootcause_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

        with s4:
            rdate = st.date_input("날짜", value=datetime.today(), key="rpt_dt")
            if st.button("보고서 초안", key="btn_rpt", disabled=_ai_exhausted):
                with st.spinner("작성 중..."):
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

