"""
[역할] Streamlit 메인 앱 (v2 - 3단계 UI)
파일을 올리면 시스템 구조를 자동으로 파악합니다.
Step1 도메인설정 → Step2 파일업로드 → Step3 결과(KG+AI분석)
"""
import os
import time
import json as _json
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components

from config import APP_TITLE, APP_ICON, DEFAULT_ENTITY_COLORS

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI 운영 코파일럿",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS (화이트 클린 테마) ────────────────────────────────────────────────────
def _apply_css(primary: str = "#2563EB"):
    st.markdown(f"""<style>
.stApp {{ background:#f8fafc; }}
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700&display=swap');
.app-header {{ text-align:center; padding:1.8rem 0 .4rem; }}
.app-header h1 {{ font-family:'Poppins',sans-serif; font-size:1.85rem;
                  color:#1e293b; margin:0 0 .25rem; letter-spacing:-.02em; }}
.app-header p  {{ font-size:1.05rem; color:#64748b; margin:0; font-weight:400; }}
/* 단계 표시기 */
.steps {{ display:flex; justify-content:center; align-items:center;
          margin:1rem 0 1.8rem; gap:0; }}
.step  {{ display:flex; flex-direction:column; align-items:center; width:150px; }}
.s-dot {{ width:36px; height:36px; border-radius:50%; display:flex;
          align-items:center; justify-content:center; font-weight:700;
          font-size:.9rem; background:white; color:#94a3b8;
          border:2px solid #cbd5e1; }}
.s-dot.active {{ background:{primary}; color:white; border-color:{primary};
                 box-shadow:0 0 0 4px {primary}22; }}
.s-dot.done   {{ background:#10b981; color:white; border-color:#10b981; }}
.s-lbl {{ font-size:.72rem; color:#94a3b8; margin-top:.22rem; font-weight:500; }}
.s-lbl.active {{ color:{primary}; font-weight:700; }}
.s-line {{ flex:1; height:2px; background:#e2e8f0; margin-bottom:1rem;
           max-width:65px; }}
.s-line.done {{ background:#10b981; }}
/* 카드 */
.card {{ background:white; border-radius:14px; padding:1.4rem;
         box-shadow:0 1px 4px rgba(0,0,0,.07); margin-bottom:.8rem; }}
/* 도메인 배너 */
.dom-banner {{ background:linear-gradient(135deg,{primary}0d,{primary}1a);
               border:1.5px solid {primary}55; border-radius:12px;
               padding:1rem 1.4rem; margin:.8rem 0;
               font-size:1.05rem; }}
/* 버튼 */
.stButton>button {{ border-radius:10px; font-weight:600; transition:all .15s; }}
/* 메트릭 */
div[data-testid="metric-container"] {{
  background:white; border-radius:12px;
  border:1px solid #e2e8f0; border-left:4px solid {primary}; padding:.8rem; }}
/* 탭 */
.stTabs [data-baseweb="tab"] {{ color:#64748b; font-weight:600; }}
.stTabs [aria-selected="true"] {{ border-bottom:3px solid {primary}; color:{primary}; }}
/* 업로더 */
[data-testid="stFileUploader"] {{
  border:2px dashed {primary}66; border-radius:12px; background:white; }}
/* 배지 */
.badge {{ display:inline-block; padding:3px 10px; border-radius:20px;
          font-size:.78em; font-weight:700; margin:2px; }}
/* 사이드바 */
section[data-testid="stSidebar"] {{ background:#1e293b !important; }}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] div {{ color:#e2e8f0 !important; }}
section[data-testid="stSidebar"] .stButton>button {{
  background:#334155 !important; color:#e2e8f0 !important;
  border:1px solid #475569 !important; }}
</style>""", unsafe_allow_html=True)


# ── 업종 프리셋 ───────────────────────────────────────────────────────────────
_PRESETS = {
    "뷰티": {
        "entity_types": {"person":"#2196F3","product":"#E91E63","supplier":"#9C27B0",
                         "process":"#FF9800","issue":"#F44336","decision":"#4CAF50",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["SKU","OEM","ODM","성분","포뮬레이션","충전량","용기","안전성시험"],
        "document_patterns": ["회의록","품질보고서","원가분석","VOC리포트"],
        "analysis_focus": ["제품 품질","원가 관리","공급망 리스크","고객 만족"],
        "theme_color": "#E91E63", "app_icon": "💄",
    },
    "공급망": {
        "entity_types": {"person":"#2196F3","supplier":"#9C27B0","product":"#795548",
                         "location":"#4CAF50","issue":"#F44336","decision":"#2563EB",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["리드타임","재고","발주","공급업체","SKU","창고","납기","안전재고"],
        "document_patterns": ["발주서","재고현황","공급망보고서","납기분석"],
        "analysis_focus": ["재고 최적화","납기 준수","공급업체 관리","수요 예측"],
        "theme_color": "#2563EB", "app_icon": "📦",
    },
    "에너지": {
        "entity_types": {"person":"#2196F3","facility":"#FF9800","resource":"#00BCD4",
                         "process":"#795548","issue":"#F44336","decision":"#4CAF50",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["발전량","수요예측","그리드","ESS","탄소중립","PPA","설비이용률"],
        "document_patterns": ["운영보고서","설비점검보고서","안전보고서"],
        "analysis_focus": ["에너지 효율","설비 안전","비용 최적화","환경 규제"],
        "theme_color": "#FF9800", "app_icon": "⚡",
    },
    "제조": {
        "entity_types": {"person":"#2196F3","product":"#795548","process":"#FF9800",
                         "resource":"#00BCD4","issue":"#F44336","decision":"#4CAF50",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["생산계획","불량률","공정개선","납기","재고","설비가동률"],
        "document_patterns": ["생산일보","품질보고서","불량분석보고서"],
        "analysis_focus": ["생산 효율","품질 관리","설비 유지보수","원가 절감"],
        "theme_color": "#607D8B", "app_icon": "🏭",
    },
    "물류": {
        "entity_types": {"person":"#2196F3","location":"#4CAF50","process":"#FF9800",
                         "resource":"#00BCD4","issue":"#F44336","decision":"#795548",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["배송","재고","창고","운송비","적재율","납기","반품"],
        "document_patterns": ["배송보고서","재고현황","운영회의록","비용분석"],
        "analysis_focus": ["배송 효율","재고 관리","비용 최적화","고객 서비스"],
        "theme_color": "#0284c7", "app_icon": "🚚",
    },
    "금융": {
        "entity_types": {"person":"#2196F3","organization":"#9C27B0","product":"#795548",
                         "process":"#FF9800","issue":"#F44336","decision":"#4CAF50",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["포트폴리오","리스크","수익률","규제준수","AUM","신용등급"],
        "document_patterns": ["투자보고서","리스크보고서","이사회회의록","실적보고"],
        "analysis_focus": ["리스크 관리","수익 극대화","규제 준수","운영 효율"],
        "theme_color": "#4CAF50", "app_icon": "💰",
    },
    "기타": {
        "entity_types": {"person":"#2196F3","organization":"#9C27B0","process":"#FF9800",
                         "resource":"#00BCD4","issue":"#F44336","decision":"#4CAF50",
                         "metric":"#607D8B","default":"#9E9E9E"},
        "terminology": ["전략","목표","성과","리스크","의사결정","KPI","예산"],
        "document_patterns": ["회의록","보고서","기획서","정책문서"],
        "analysis_focus": ["핵심 의사결정","리스크 관리","성과 측정","실행 과제"],
        "theme_color": "#2563EB", "app_icon": "🤖",
    },
}

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
    if any(k in names for k in ["VANILLAECO","BEAUTY","COSMETIC","LIPSTICK","SKINCARE"]):
        return "뷰티 이커머스"
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
    n = name.upper()
    if any(k in n for k in ["뷰티","BEAUTY","화장품","COSMETIC","이커머스"]):
        return _PRESETS["뷰티"]
    if any(k in n for k in ["공급","SUPPLY","재고","INVENTORY","발주","창고"]):
        return _PRESETS["공급망"]
    if any(k in n for k in ["에너지","ENERGY","발전"]):
        return _PRESETS["에너지"]
    if any(k in n for k in ["제조","MANUF","생산","FACTORY"]):
        return _PRESETS["제조"]
    if any(k in n for k in ["물류","LOGISTIC","배송"]):
        return _PRESETS["물류"]
    if any(k in n for k in ["금융","FINANC","투자","회계"]):
        return _PRESETS["금융"]
    return _PRESETS["기타"]

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
    # ── Issue#1: 도메인 컨텍스트를 프롬프트 앞에 주입 ──────────────────────
    prompt = domain_ctx_header + template.replace("{document}", text[:3000])
    response = st.session_state.claude.generate(prompt, max_tokens=4096)
    st.session_state.kg.build_from_claude_json(response)

def _process_uploaded_files(uploaded_files) -> int:
    from modules.document_parser import (
        parse_file, extract_csv_schema,
        extract_python_graph_data, _csv_schema_to_text,
    )
    new_files, kg_direct, pending_csv = [], set(), []

    for uf in uploaded_files:
        if uf.name in st.session_state.documents:
            continue
        try:
            fl = uf.name.lower()
            if fl.endswith(".json"):
                raw = uf.read().decode("utf-8")
                data = _json.loads(raw)
                if "tables" in data and "relationships" in data:
                    st.session_state.kg.build_from_schema_json(data)
                    text = _schema_to_text(data)
                else:
                    text = raw
                st.session_state.documents[uf.name] = text
                new_files.append(uf.name); kg_direct.add(uf.name)

            elif fl.endswith(".csv"):
                raw = uf.read().decode("utf-8", errors="replace")
                schema = extract_csv_schema(uf.name, raw)
                pending_csv.append((uf.name, schema))
                st.session_state.documents[uf.name] = _csv_schema_to_text(schema)
                new_files.append(uf.name); kg_direct.add(uf.name)

            elif fl.endswith(".py"):
                source = uf.read().decode("utf-8")
                gd = extract_python_graph_data(source, uf.name)
                st.session_state.kg.build_from_python_ast(gd)
                st.session_state.documents[uf.name] = source
                new_files.append(uf.name); kg_direct.add(uf.name)

            else:
                text = parse_file(uf)
                if text.strip():
                    st.session_state.documents[uf.name] = text
                    new_files.append(uf.name)
        except Exception as e:
            st.warning(f"⚠️ `{uf.name}` 오류: {e}")

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

    # Claude KG 추출 (TXT/PDF/DOCX — 도메인 컨텍스트 포함)
    for fname in new_files:
        if fname not in kg_direct:
            _extract_kg_with_domain(st.session_state.documents[fname])

    return len(new_files)

def _load_sample_data() -> int:
    from modules.document_parser import extract_csv_schema, _csv_schema_to_text
    data_dir = "./data"
    if not os.path.isdir(data_dir):
        return 0

    new_files, kg_direct, pending_csv = [], set(), []

    for fname in sorted(os.listdir(data_dir)):
        fpath = os.path.join(data_dir, fname)
        if not os.path.isfile(fpath) or fname in st.session_state.documents:
            continue
        try:
            fl = fname.lower()
            if fl.endswith(".json"):
                with open(fpath, encoding="utf-8") as f:
                    data = _json.load(f)
                if "tables" in data and "relationships" in data:
                    st.session_state.kg.build_from_schema_json(data)
                    text = _schema_to_text(data)
                else:
                    text = _json.dumps(data, ensure_ascii=False)
                st.session_state.documents[fname] = text
                new_files.append(fname); kg_direct.add(fname)

            elif fl.endswith(".csv"):
                with open(fpath, encoding="utf-8-sig", errors="replace") as f:
                    raw = f.read()
                schema = extract_csv_schema(fname, raw)
                pending_csv.append((fname, schema))
                st.session_state.documents[fname] = _csv_schema_to_text(schema)
                new_files.append(fname); kg_direct.add(fname)

            elif fl.endswith(".txt"):
                with open(fpath, encoding="utf-8", errors="replace") as f:
                    text = f.read()
                if text.strip():
                    st.session_state.documents[fname] = text
                    new_files.append(fname)
        except Exception:
            pass

    if pending_csv:
        for fn, sc in pending_csv:
            st.session_state.kg.build_from_csv_schema(sc, [])
        all_tables = list(st.session_state.kg.graph.nodes)
        for fn, sc in pending_csv:
            st.session_state.kg.build_from_csv_schema(sc, all_tables)

    for fname in new_files:
        st.session_state.rag.add_document(st.session_state.documents[fname], fname)

    return len(new_files)

def _process_text_paste(title: str, text: str) -> bool:
    key = f"{title.strip()}.txt"
    if key in st.session_state.documents or not text.strip():
        return False
    st.session_state.documents[key] = text
    st.session_state.rag.add_document(text, key)
    _extract_kg_with_domain(text)
    return True


# ── 채팅 헬퍼 ─────────────────────────────────────────────────────────────────

def _load_csv(filename: str):
    """data/ 폴더에서 CSV를 DataFrame으로 로드합니다."""
    path = os.path.join("./data", filename)
    if os.path.exists(path):
        try:
            return pd.read_csv(path, encoding="utf-8-sig")
        except Exception:
            return None
    return None


def _detect_chat_intent(msg: str) -> str:
    m = msg.lower()
    if any(k in m for k in ["그래프", "차트", "시각화", "그려줘", "보여줘", "플롯"]):
        return "graph"
    if any(k in m for k in ["잘팔리", "잘 팔리", "판매", "매출", "분석",
                              "재고", "발주", "수요", "상위", "여름", "계절"]):
        return "analysis"
    return "rag"


def _handle_chat_graph(msg: str):
    """그래프 생성: 제품 코드 감지 → 월별 판매 line chart."""
    import re
    prod_match = re.search(r"(FG-\d+|PRD\d+)", msg.upper())
    sales_df   = _load_csv("FACT_MONTHLY_SALES.csv")
    parts_df   = _load_csv("MST_PART.csv")

    if prod_match and sales_df is not None and parts_df is not None:
        code = prod_match.group(1)
        if code.startswith("FG-"):
            row = parts_df[parts_df["PART_CD"] == code]
            if row.empty:
                return None, f"'{code}' 제품을 찾을 수 없습니다."
            product_id = row.iloc[0]["LINKED_PRODUCT_ID"]
            product_name = row.iloc[0]["PART_NAME"]
        else:
            product_id = code
            mst = _load_csv("MST_PRODUCT.csv")
            if mst is not None:
                r2 = mst[mst["PRODUCT_ID"] == product_id]
                product_name = r2.iloc[0]["PRODUCT_NAME"] if not r2.empty else product_id
            else:
                product_name = product_id

        filtered = sales_df[sales_df["PRODUCT_ID"] == product_id].sort_values("YEAR_MONTH")
        if filtered.empty:
            return None, f"'{code}' 판매 데이터가 없습니다."
        fig = px.line(filtered, x="YEAR_MONTH", y="NET_SALES_QTY",
                      title=f"{product_name} 월별 수요",
                      labels={"YEAR_MONTH": "월", "NET_SALES_QTY": "판매량"},
                      markers=True)
        fig.update_layout(height=280, margin=dict(t=40, b=30))
        return fig, f"**{product_name}** 월별 판매 추이입니다."

    # 제품 코드 없으면 채널별 전체 차트
    ch_df = _load_csv("MST_CHANNEL.csv")
    if sales_df is not None and ch_df is not None:
        merged = sales_df.merge(ch_df[["CHANNEL_ID", "CHANNEL_NAME"]], on="CHANNEL_ID", how="left")
        grouped = merged.groupby(["YEAR_MONTH", "CHANNEL_NAME"])["NET_SALES_QTY"].sum().reset_index()
        fig = px.line(grouped, x="YEAR_MONTH", y="NET_SALES_QTY", color="CHANNEL_NAME",
                      title="채널별 월별 판매량",
                      labels={"YEAR_MONTH": "월", "NET_SALES_QTY": "판매량"},
                      markers=True)
        fig.update_layout(height=280, margin=dict(t=40, b=30))
        return fig, "채널별 월별 판매 추이입니다."

    return None, "그래프를 생성할 데이터가 없습니다."


def _handle_chat_analysis(msg: str) -> str:
    """CSV 데이터 요약 → Claude 답변."""
    m = msg.lower()
    context_parts = []
    parts_df = _load_csv("MST_PART.csv")

    # 판매 / 계절
    if any(k in m for k in ["잘팔리", "잘 팔리", "판매", "매출", "상위", "수요",
                              "여름", "봄", "가을", "겨울", "계절"]):
        sales = _load_csv("FACT_MONTHLY_SALES.csv")
        if sales is not None:
            season_kw = {"여름": [6,7,8], "봄": [3,4,5], "가을": [9,10,11], "겨울": [12,1,2]}
            target_months = None
            season_label  = None
            for sname, months in season_kw.items():
                if sname in m:
                    target_months = months
                    season_label  = sname
                    break

            if target_months:
                sales["_month"] = sales["YEAR_MONTH"].str[-2:].astype(int)
                filtered = sales[sales["_month"].isin(target_months)]
                top5 = filtered.groupby("PRODUCT_ID")["NET_SALES_QTY"].sum().nlargest(5)
                context_parts.append(f"[{season_label} 판매 TOP5]")
            else:
                top5 = sales.groupby("PRODUCT_ID")["NET_SALES_QTY"].sum().nlargest(5)
                context_parts.append("[전체 판매 TOP5]")

            for pid, qty in top5.items():
                name = pid
                if parts_df is not None:
                    row = parts_df[parts_df["LINKED_PRODUCT_ID"] == pid]
                    if not row.empty:
                        name = row.iloc[0]["PART_NAME"]
                context_parts.append(f"  · {name}: {qty:,}개")

    # 재고
    if any(k in m for k in ["재고", "inventory", "위험", "critical", "stock"]):
        inv = _load_csv("FACT_INVENTORY.csv")
        if inv is not None:
            latest = inv.sort_values("SNAPSHOT_DATE").groupby("PRODUCT_ID").last().reset_index()
            critical = latest[latest["STOCK_STATUS"] == "CRITICAL"]
            context_parts.append(f"[재고 CRITICAL {len(critical)}개]")
            for _, row in critical.iterrows():
                name = row["PRODUCT_ID"]
                if parts_df is not None:
                    pr = parts_df[parts_df["LINKED_PRODUCT_ID"] == row["PRODUCT_ID"]]
                    if not pr.empty:
                        name = pr.iloc[0]["PART_NAME"]
                context_parts.append(f"  · {name}: {row['STOCK_QTY']}개 (안전재고 {row['SAFETY_STOCK_QTY']}개)")

    # 발주
    if any(k in m for k in ["발주", "주문", "order", "replenishment"]):
        orders = _load_csv("FACT_REPLENISHMENT_ORDER.csv")
        if orders is not None:
            pending = orders[orders["STATUS"].isin(["PENDING", "IN_TRANSIT"])]
            context_parts.append(f"[진행중 발주 {len(pending)}건]")
            if parts_df is not None and not pending.empty:
                top5 = pending.groupby("PART_CD")["ORDER_QTY"].sum().nlargest(5)
                for part_cd, qty in top5.items():
                    pr = parts_df[parts_df["PART_CD"] == part_cd]
                    name = pr.iloc[0]["PART_NAME"] if not pr.empty else part_cd
                    context_parts.append(f"  · {name}: {qty:,}개 발주중")

    if not context_parts:
        return _handle_chat_rag(msg)

    data_summary = "\n".join(context_parts)
    prompt = (
        f"{_get_domain_context()}\n\n"
        f"[데이터 요약]\n{data_summary}\n\n"
        f"[질문] {msg}\n\n"
        "위 데이터를 바탕으로 질문에 간결하게 답변하세요."
    )
    return st.session_state.claude.generate(prompt, max_tokens=1000)


def _handle_chat_rag(msg: str) -> str:
    """지식그래프 + RAG 결합 답변."""
    kg_context = ""
    if st.session_state.kg:
        first_word = msg.split()[0] if msg.split() else ""
        result = st.session_state.kg.query_by_id(first_word)
        if result["matched_nodes"]:
            nodes_str = ", ".join(
                f"{n['label']}({n['type']})" for n in result["matched_nodes"][:5]
            )
            edges_str = "; ".join(
                f"{e['source']}→{e['relation']}→{e['target']}"
                for e in result["edges"][:5]
            )
            kg_context = f"[지식그래프]\n노드: {nodes_str}\n관계: {edges_str}\n\n"

    rag_context = ""
    if st.session_state.rag:
        hits = st.session_state.rag.query(msg, n_results=3)
        if hits:
            rag_context = "\n\n".join(
                f"[{h['filename']}]\n{h['text']}" for h in hits
            )

    from modules.prompt_loader import load_prompt
    combined = (kg_context + rag_context) or "관련 데이터를 찾지 못했습니다."
    return st.session_state.claude.generate(
        load_prompt("rag_query", question=msg,
                    context=combined, domain_context=_get_domain_context()),
        max_tokens=1000,
    )


def _generate_daily_briefing():
    """일일 브리핑: 재고위험 · 채널TOP3 · 발주필요 → (text, [charts])."""
    parts_df = _load_csv("MST_PART.csv")
    sections = []
    charts   = []

    # ── 1. 재고 위험 ──────────────────────────────────────────────────────────
    inv = _load_csv("FACT_INVENTORY.csv")
    latest = None
    if inv is not None:
        latest = inv.sort_values("SNAPSHOT_DATE").groupby("PRODUCT_ID").last().reset_index()
        critical = latest[latest["STOCK_STATUS"] == "CRITICAL"]
        warning  = latest[latest["STOCK_STATUS"] == "WARNING"]
        lines = [f"🚨 재고 위험 {len(critical)}개 / 경고 {len(warning)}개"]
        for _, row in critical.iterrows():
            name = row["PRODUCT_ID"]
            if parts_df is not None:
                pr = parts_df[parts_df["LINKED_PRODUCT_ID"] == row["PRODUCT_ID"]]
                if not pr.empty:
                    name = pr.iloc[0]["PART_NAME"]
            lines.append(f"  · {name}: {row['STOCK_QTY']}개 (안전재고 {row['SAFETY_STOCK_QTY']}개)")
        sections.append("\n".join(lines))

        if parts_df is not None and not latest.empty:
            top_risk = latest.nsmallest(8, "COVERAGE_WEEKS").copy()
            top_risk = top_risk.merge(
                parts_df[["LINKED_PRODUCT_ID", "PART_NAME"]],
                left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left"
            )
            top_risk["label"] = top_risk["PART_NAME"].fillna(top_risk["PRODUCT_ID"])
            fig1 = px.bar(
                top_risk, x="label", y="COVERAGE_WEEKS",
                color="STOCK_STATUS",
                color_discrete_map={"CRITICAL": "#EF4444", "WARNING": "#F59E0B", "OK": "#10B981"},
                title="📦 재고 커버리지 (주 단위, 낮을수록 위험)",
                labels={"label": "상품", "COVERAGE_WEEKS": "재고 커버 주수"},
            )
            fig1.update_layout(height=250, margin=dict(t=40, b=30))
            charts.append(fig1)

    # ── 2. 채널별 판매 TOP3 ───────────────────────────────────────────────────
    sales = _load_csv("FACT_MONTHLY_SALES.csv")
    ch_df = _load_csv("MST_CHANNEL.csv")
    if sales is not None and ch_df is not None:
        recent_months = sorted(sales["YEAR_MONTH"].unique())[-3:]
        recent = sales[sales["YEAR_MONTH"].isin(recent_months)]
        merged = recent.merge(ch_df[["CHANNEL_ID", "CHANNEL_NAME"]], on="CHANNEL_ID", how="left")
        ch_top = merged.groupby("CHANNEL_NAME")["NET_SALES_QTY"].sum().nlargest(5).reset_index()

        lines = ["📊 최근 3개월 채널별 판매 TOP5"]
        for i, row in ch_top.iterrows():
            lines.append(f"  {i+1}. {row['CHANNEL_NAME']}: {row['NET_SALES_QTY']:,}개")
        sections.append("\n".join(lines))

        if parts_df is not None:
            prod_ch = merged.merge(
                parts_df[["LINKED_PRODUCT_ID", "PART_NAME"]],
                left_on="PRODUCT_ID", right_on="LINKED_PRODUCT_ID", how="left"
            )
            prod_ch["label"] = prod_ch["PART_NAME"].fillna(prod_ch["PRODUCT_ID"])
        else:
            prod_ch = merged.copy()
            prod_ch["label"] = prod_ch["PRODUCT_ID"]

        top3_per_ch = (
            prod_ch.groupby(["CHANNEL_NAME", "label"])["NET_SALES_QTY"]
            .sum().reset_index()
            .sort_values("NET_SALES_QTY", ascending=False)
            .groupby("CHANNEL_NAME").head(3)
        )
        fig2 = px.bar(
            top3_per_ch, x="CHANNEL_NAME", y="NET_SALES_QTY", color="label",
            title="📈 채널별 TOP3 상품 (최근 3개월)",
            labels={"CHANNEL_NAME": "채널", "NET_SALES_QTY": "판매량", "label": "상품"},
        )
        fig2.update_layout(height=250, margin=dict(t=40, b=30))
        charts.append(fig2)

    # ── 3. 발주 필요 ──────────────────────────────────────────────────────────
    orders = _load_csv("FACT_REPLENISHMENT_ORDER.csv")
    if orders is not None and latest is not None and parts_df is not None:
        critical_pids  = set(latest[latest["STOCK_STATUS"] == "CRITICAL"]["PRODUCT_ID"])
        active_parts   = set(orders[orders["STATUS"].isin(["PENDING", "IN_TRANSIT"])]["PART_CD"])
        lines = ["📋 발주 필요 상품"]
        for pid in critical_pids:
            pr = parts_df[parts_df["LINKED_PRODUCT_ID"] == pid]
            if pr.empty:
                continue
            pcd  = pr.iloc[0]["PART_CD"]
            name = pr.iloc[0]["PART_NAME"]
            if pcd in active_parts:
                lines.append(f"  · {name}: 발주 진행중 ✓")
            else:
                lines.append(f"  · {name}: 발주 없음 ⚠️")
        sections.append("\n".join(lines))

    # ── Claude 브리핑 요약 ─────────────────────────────────────────────────
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
    return summary, charts


# ── CSS 적용 ──────────────────────────────────────────────────────────────────
_apply_css(_get_theme_color())


# ── 사이드바 (최소화) ─────────────────────────────────────────────────────────
with st.sidebar:
    dc = st.session_state.domain_config
    icon = dc["app_icon"] if dc else "🤖"
    dname = dc["name"] if dc else "AI 코파일럿"
    st.markdown(f"### {icon} {dname}")
    st.divider()

    if st.session_state.documents:
        st.markdown(f"**📁 로드된 문서 ({len(st.session_state.documents)}개)**")
        for fname in list(st.session_state.documents.keys())[:8]:
            st.caption(f"• {fname}")
        if len(st.session_state.documents) > 8:
            st.caption(f"  ... 외 {len(st.session_state.documents)-8}개")
        st.divider()
        if st.button("🗑️ 전체 초기화", use_container_width=True):
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
    if st.session_state.kg:
        s = st.session_state.kg.get_stats()
        st.caption(f"🕸️ 노드 {s['nodes']} / 엣지 {s['edges']}")
    if st.session_state.rag:
        try: st.caption(f"🔗 RAG 청크 {st.session_state.rag.document_count()}개")
        except Exception: pass

    st.divider()
    st.markdown("**단계 이동**")
    for lbl, n in [("1️⃣ 도메인 설정", 1), ("2️⃣ 파일 업로드", 2), ("3️⃣ 결과 보기", 3)]:
        if st.button(lbl, use_container_width=True, key=f"nav_{n}"):
            st.session_state.step = n; st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 메인 콘텐츠
# ════════════════════════════════════════════════════════════════════════════════

# 헤더
st.markdown("""
<div class="app-header">
  <h1>✨ AI 운영 코파일럿</h1>
  <p>파일을 올리면 시스템 구조를 자동으로 파악합니다</p>
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
            if st.button("✅ 이 도메인으로 시작", type="primary"):
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
            ("💄 뷰티·이커머스", "뷰티 이커머스"),
            ("📦 공급망·재고",   "공급망·재고 관리"),
            ("⚡ 에너지",        "에너지"),
            ("🏭 제조·생산",     "제조·생산"),
            ("🚚 물류",          "물류"),
            ("💰 금융",          "금융"),
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
            if st.button("✅ 확인", type="primary", use_container_width=True):
                if custom.strip():
                    cfg = _build_domain_from_name(custom.strip())
                    st.session_state.domain_config = cfg.to_dict()
                    _apply_css(cfg.theme_color)
                    st.session_state.step = 2; st.rerun()
                else:
                    st.error("도메인명을 입력해주세요.")

        st.divider()
        st.caption("💡 도메인 없이 바로 파일을 올려도 됩니다. 파일 내용으로 자동 감지합니다.")
        if st.button("⏩ 설정 없이 바로 파일 올리기"):
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
            "🚀 샘플 데이터로 바로 시작",
            use_container_width=True,
            help="data/ 폴더의 바닐라코 데모 데이터를 자동으로 불러옵니다",
        )

    if sample_clicked:
        with st.spinner("샘플 데이터를 불러오는 중..."):
            n = _load_sample_data()
        if n > 0:
            st.success(f"✅ 샘플 데이터 {n}개 파일 로드 완료!")
            if not st.session_state.domain_config:
                cfg = _build_domain_from_name("뷰티 이커머스")
                st.session_state.domain_config = cfg.to_dict()
                _apply_css(cfg.theme_color)
            st.session_state.step = 3; st.rerun()
        else:
            st.warning("data/ 폴더에 샘플 파일이 없습니다.")

    st.divider()

    # ── 탭: 파일 업로드 | 텍스트 직접 입력 ─────────────────────────────────
    tab_file, tab_text = st.tabs(["📁 파일 업로드", "✏️ 텍스트 직접 입력"])

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
        if st.button("📊 분석 시작", type="primary", key="btn_txt"):
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
        if st.button("▶ 결과 보기", type="primary"):
            st.session_state.step = 3; st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# Step 3: 결과 보기
# ════════════════════════════════════════════════════════════════════════════════
elif step == 3:
    if not _load_modules():
        st.stop()

    if not st.session_state.documents:
        st.warning("📂 문서가 없습니다.")
        if st.button("← 파일 업로드"):
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

    # ── 2컬럼 레이아웃: 왼쪽(KG+분석탭) / 오른쪽(채팅) ─────────────────────
    col_main, col_chat = st.columns([3, 2], gap="medium")

    # ════════════════════════════════════════════════════════
    # 왼쪽: 지식그래프 + AI 분석 탭
    # ════════════════════════════════════════════════════════
    with col_main:
        # ── 지식그래프 ───────────────────────────────────────
        st.markdown("#### 🕸️ 지식 그래프")

        if stats["nodes"] == 0:
            st.info("📂 CSV·JSON·TXT·PDF 문서를 업로드하면 엔티티 관계 그래프가 나타납니다.")
        else:
            if stats["entity_types"]:
                legend_html = "".join(
                    f'<span class="badge" style="background:{entity_colors.get(t,"#9E9E9E")};color:white">'
                    f'{t} ({cnt})</span>'
                    for t, cnt in stats["entity_types"].items()
                )
                st.markdown(legend_html, unsafe_allow_html=True)

            html_path = kg.render_html(entity_colors=entity_colors)
            if html_path and os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                components.html(html_content, height=620, scrolling=False)
            else:
                st.error("그래프 렌더링 실패")

            with st.expander("🔄 특정 문서 그래프 재추출"):
                sel_doc = st.selectbox("문서 선택", list(st.session_state.documents.keys()),
                                        key="kg_re_sel")
                if st.button("🔄 재추출", key="btn_reextract"):
                    with st.spinner("재추출 중..."):
                        _extract_kg_with_domain(st.session_state.documents[sel_doc])
                    st.success(f"✅ 완료! 노드 {kg.get_stats()['nodes']}개")
                    st.rerun()

        st.divider()

        # ── 하단 탭 ──────────────────────────────────────────
        tab_ai, tab_rag, tab_num = st.tabs(["🤖 AI 분석", "🔍 문서 검색 (RAG)", "🔎 번호 조회"])

        with tab_ai:
            from modules.prompt_loader import load_prompt

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

            s1, s2, s3, s4 = st.tabs(["📋 요약", "✅ 액션 아이템", "🔬 원인 분석", "📊 보고서"])

            with s1:
                if st.button("📋 요약 생성", key="btn_sum"):
                    with st.spinner("요약 중..."):
                        r = st.session_state.claude.generate(
                            load_prompt("summarize", document=atxt, domain_context=domain_context))
                    st.markdown(r)
                    st.download_button("💾 다운로드", r,
                        f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

            with s2:
                if st.button("✅ 액션 아이템 추출", key="btn_act"):
                    with st.spinner("추출 중..."):
                        r = st.session_state.claude.generate(
                            load_prompt("action_items", document=atxt, domain_context=domain_context))
                    st.markdown(r)
                    st.download_button("💾 다운로드", r,
                        f"actions_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

            with s3:
                issue = st.text_input("특정 문제 (선택)", placeholder="예: 납기 지연 원인", key="issue_h")
                if st.button("🔬 원인 분석", key="btn_root"):
                    doc = f"[분석초점: {issue}]\n\n{atxt}" if issue else atxt
                    with st.spinner("분석 중..."):
                        r = st.session_state.claude.generate(
                            load_prompt("root_cause", document=doc, domain_context=domain_context))
                    st.markdown(r)
                    st.download_button("💾 다운로드", r,
                        f"rootcause_{datetime.now().strftime('%Y%m%d_%H%M')}.md", "text/markdown")

            with s4:
                rdate = st.date_input("날짜", value=datetime.today(), key="rpt_dt")
                if st.button("📊 보고서 초안", key="btn_rpt"):
                    with st.spinner("작성 중..."):
                        r = st.session_state.claude.generate(
                            load_prompt("report_draft", document=atxt,
                                date=rdate.strftime("%Y년 %m월 %d일"), domain_context=domain_context))
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

            if st.button("🔍 검색 & 답변", type="primary", key="btn_rag") and q.strip():
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
                    placeholder="예: PRD001, FG-002, order_id, 주문테이블...", key="num_q")
                nc1, nc2 = st.columns([1, 3])
                with nc1: depth = st.selectbox("탐색 깊이", [1, 2, 3], key="num_d")
                with nc2: use_rag = st.checkbox("문서에서도 검색 (RAG)", value=True, key="num_r")

                if st.button("🔎 조회", type="primary", key="btn_num") and qi.strip():
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

    # ════════════════════════════════════════════════════════
    # 오른쪽: 데이터 채팅 + 일일 브리핑
    # ════════════════════════════════════════════════════════
    with col_chat:
        st.markdown("#### 💬 데이터 채팅")
        st.caption("CSV 데이터 기반 질문·그래프 생성, 지식그래프+RAG 결합 답변")

        # ── 일일 브리핑 버튼 ─────────────────────────────────
        if st.button("📋 일일 브리핑 생성", type="primary",
                     use_container_width=True, key="btn_briefing"):
            with st.spinner("브리핑 생성 중... (약 20~30초)"):
                try:
                    brief_text, brief_charts = _generate_daily_briefing()
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": brief_text,
                        "charts": brief_charts,
                    })
                except Exception as e:
                    st.error(f"브리핑 생성 실패: {e}")
            st.rerun()

        st.divider()

        # ── 채팅 히스토리 표시 ───────────────────────────────
        chat_box = st.container(height=520)
        with chat_box:
            if not st.session_state.chat_history:
                st.caption("💡 예시 질문:")
                st.caption("• FG-002 선크림 수요 그래프 그려줘")
                st.caption("• 여름에 잘 팔리는 상품 뭐야?")
                st.caption("• 재고 위험 상품 알려줘")
                st.caption("• 이 상품 특징 알려줘")
            else:
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        for chart in msg.get("charts", []):
                            st.plotly_chart(chart, use_container_width=True)

        # ── 채팅 입력 ────────────────────────────────────────
        user_input = st.chat_input(
            "FG-002 수요 그래프 / 여름 판매 상품 / 재고 위험...",
            key="chat_in",
        )
        if user_input:
            st.session_state.chat_history.append(
                {"role": "user", "content": user_input, "charts": []}
            )
            with st.spinner("답변 생성 중..."):
                try:
                    intent = _detect_chat_intent(user_input)
                    if intent == "graph":
                        fig, text = _handle_chat_graph(user_input)
                        charts   = [fig] if fig else []
                        response = text
                    elif intent == "analysis":
                        response = _handle_chat_analysis(user_input)
                        charts   = []
                    else:
                        response = _handle_chat_rag(user_input)
                        charts   = []
                except Exception as e:
                    response = f"오류가 발생했습니다: {e}"
                    charts   = []
            st.session_state.chat_history.append(
                {"role": "assistant", "content": response, "charts": charts}
            )
            st.rerun()
