"""
도메인 적응형 AI 운영 코파일럿
회의록·운영문서 → RAG 검색 + 지식그래프 + AI 분석 (요약/액션/원인/보고서)
어떤 도메인이든 Claude가 자동으로 적응합니다.
"""
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from config import APP_TITLE, APP_ICON, DEFAULT_ENTITY_COLORS

# ── 페이지 설정 (반드시 최상단) ─────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── 동적 CSS 테마 ─────────────────────────────────────────────────────────────
def _apply_theme(primary: str = "#2196F3"):
    """도메인 테마 컬러를 기반으로 CSS를 동적으로 주입합니다."""
    st.markdown(
        f"""
<style>
    .stButton>button {{
        background: linear-gradient(135deg, {primary}, {primary}cc);
        color: white; border: none; border-radius: 24px;
        padding: 0.5rem 1.4rem; font-weight: 600;
        transition: all .2s;
    }}
    .stButton>button:hover {{ opacity:.88; transform:translateY(-1px); }}

    div[data-testid="metric-container"] {{
        background: white;
        border: 1px solid {primary}44;
        border-left: 4px solid {primary};
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px {primary}22;
    }}

    .stTabs [data-baseweb="tab"] {{ color: {primary}; font-weight: 600; }}
    .stTabs [aria-selected="true"] {{ border-bottom: 3px solid {primary}; }}

    [data-testid="stFileUploader"] {{
        border: 2px dashed {primary}88;
        border-radius: 12px;
        padding: .5rem;
        background: #fff;
    }}

    .badge {{
        display:inline-block; padding:3px 10px;
        border-radius:20px; font-size:.78em; font-weight:700;
        margin:2px;
    }}

    .domain-card {{
        background: linear-gradient(135deg, {primary}11, {primary}22);
        border: 1px solid {primary}44;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.5rem;
    }}
</style>
""",
        unsafe_allow_html=True,
    )


# ── 세션 스테이트 초기화 ──────────────────────────────────────────────────────
def _init_session():
    defaults = {
        "documents": {},        # {filename: text}
        "rag": None,
        "claude": None,
        "kg": None,
        "api_ok": False,
        "domain_config": None,  # DomainConfig.to_dict() 저장
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


_init_session()

# 현재 도메인 컨텍스트 (없으면 기본값)
_DEFAULT_DOMAIN_CONTEXT = (
    "도메인: 일반 비즈니스\n"
    "도메인 설명: 다양한 비즈니스 운영 문서 분석\n"
    "핵심 용어/개념: 전략, 목표, 성과, 리스크, 의사결정\n"
    "주요 문서 유형: 회의록, 보고서, 정책 문서\n"
    "분석 포커스: 핵심 의사결정, 리스크, 실행 과제, 성과 지표\n"
    "주요 엔티티 유형: person, organization, issue, decision, metric"
)


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
        return st.session_state.domain_config.get("theme_color", "#2196F3")
    return "#2196F3"


def _get_collection_name() -> str:
    if st.session_state.domain_config:
        from modules.domain_adapter import DomainConfig
        return DomainConfig.from_dict(st.session_state.domain_config).collection_name
    from config import DEFAULT_COLLECTION_NAME
    return DEFAULT_COLLECTION_NAME


# ── 업종별 기본 프리셋 ────────────────────────────────────────────────────────
_INDUSTRY_PRESETS = {
    "뷰티": {
        "entity_types": {
            "person": "#2196F3", "product": "#E91E63", "supplier": "#9C27B0",
            "process": "#FF9800", "issue": "#F44336", "decision": "#4CAF50",
            "metric": "#607D8B", "default": "#9E9E9E",
        },
        "base_terminology": ["SKU", "OEM", "ODM", "성분", "포뮬레이션", "충전량", "용기", "안전성시험"],
        "document_patterns": ["회의록", "품질보고서", "원가분석", "VOC 리포트", "출하검사보고서"],
        "analysis_focus": ["제품 품질", "원가 관리", "공급망 리스크", "규제 준수", "고객 만족"],
        "theme_color": "#E91E63",
        "app_icon": "💄",
    },
    "에너지": {
        "entity_types": {
            "person": "#2196F3", "facility": "#FF9800", "resource": "#00BCD4",
            "process": "#795548", "issue": "#F44336", "decision": "#4CAF50",
            "metric": "#607D8B", "default": "#9E9E9E",
        },
        "base_terminology": ["발전량", "수요예측", "그리드", "ESS", "탄소중립", "PPA", "설비이용률"],
        "document_patterns": ["운영보고서", "설비점검보고서", "안전보고서", "에너지진단서"],
        "analysis_focus": ["에너지 효율", "설비 안전", "비용 최적화", "환경 규제", "공급 안정성"],
        "theme_color": "#FF9800",
        "app_icon": "⚡",
    },
    "제조": {
        "entity_types": {
            "person": "#2196F3", "product": "#795548", "process": "#FF9800",
            "resource": "#00BCD4", "issue": "#F44336", "decision": "#4CAF50",
            "metric": "#607D8B", "default": "#9E9E9E",
        },
        "base_terminology": ["생산계획", "불량률", "공정개선", "납기", "재고", "설비가동률", "품질관리"],
        "document_patterns": ["생산일보", "품질보고서", "불량분석보고서", "설비점검일지"],
        "analysis_focus": ["생산 효율", "품질 관리", "설비 유지보수", "공급망", "원가 절감"],
        "theme_color": "#607D8B",
        "app_icon": "🏭",
    },
    "물류": {
        "entity_types": {
            "person": "#2196F3", "location": "#4CAF50", "process": "#FF9800",
            "resource": "#00BCD4", "issue": "#F44336", "decision": "#795548",
            "metric": "#607D8B", "default": "#9E9E9E",
        },
        "base_terminology": ["배송", "재고", "창고", "운송비", "적재율", "납기", "반품", "라스트마일"],
        "document_patterns": ["배송보고서", "재고현황", "운영회의록", "사고보고서", "비용분석"],
        "analysis_focus": ["배송 효율", "재고 관리", "비용 최적화", "고객 서비스", "안전 관리"],
        "theme_color": "#2196F3",
        "app_icon": "🚚",
    },
    "금융": {
        "entity_types": {
            "person": "#2196F3", "organization": "#9C27B0", "product": "#795548",
            "process": "#FF9800", "issue": "#F44336", "decision": "#4CAF50",
            "metric": "#607D8B", "default": "#9E9E9E",
        },
        "base_terminology": ["포트폴리오", "리스크", "수익률", "규제준수", "AUM", "신용등급", "유동성"],
        "document_patterns": ["투자보고서", "리스크보고서", "규제보고", "이사회회의록", "실적보고"],
        "analysis_focus": ["리스크 관리", "수익 극대화", "규제 준수", "고객 자산 보호", "운영 효율"],
        "theme_color": "#4CAF50",
        "app_icon": "💰",
    },
    "기타": {
        "entity_types": {
            "person": "#2196F3", "organization": "#9C27B0", "process": "#FF9800",
            "resource": "#00BCD4", "issue": "#F44336", "decision": "#4CAF50",
            "metric": "#607D8B", "default": "#9E9E9E",
        },
        "base_terminology": ["전략", "목표", "성과", "리스크", "의사결정", "KPI", "예산"],
        "document_patterns": ["회의록", "보고서", "기획서", "정책문서", "분석자료"],
        "analysis_focus": ["핵심 의사결정", "리스크 관리", "성과 측정", "실행 과제", "자원 배분"],
        "theme_color": "#2196F3",
        "app_icon": "🤖",
    },
}

_INDUSTRY_OPTIONS = ["뷰티", "에너지", "제조", "물류", "금융", "기타"]


def _build_domain_config_simple(company_name: str, industry: str, key_terms_str: str):
    """사이드바 간단 입력으로 DomainConfig를 생성합니다 (Claude 호출 없이)."""
    from modules.domain_adapter import DomainConfig
    preset = _INDUSTRY_PRESETS.get(industry, _INDUSTRY_PRESETS["기타"])
    user_terms = [t.strip() for t in key_terms_str.split(",") if t.strip()]
    combined_terms = user_terms + [t for t in preset["base_terminology"] if t not in user_terms]
    return DomainConfig(
        name=f"{company_name} ({industry})",
        description=f"{company_name}의 {industry} 업종 운영 문서 분석",
        entity_types=preset["entity_types"],
        terminology=combined_terms[:15],
        document_patterns=preset["document_patterns"],
        analysis_focus=preset["analysis_focus"],
        theme_color=preset["theme_color"],
        app_title=f"{company_name} AI 운영 코파일럿",
        app_icon=preset["app_icon"],
    )


# ── 모듈 지연 로딩 ────────────────────────────────────────────────────────────
def _load_modules() -> bool:
    """Claude / RAG / KG 모듈을 초기화합니다. 도메인이 바뀌면 RAG를 재초기화합니다."""
    try:
        from modules.claude_client import ClaudeClient
        from modules.rag_engine import RAGEngine
        from modules.knowledge_graph import KnowledgeGraph

        # Claude 초기화 (한 번만)
        if st.session_state.claude is None:
            st.session_state.claude = ClaudeClient()
            st.session_state.api_ok = True

        # RAG: 컬렉션명이 바뀌면 재초기화
        desired_col = _get_collection_name()
        current_col = getattr(st.session_state.rag, "collection_name", None)
        if st.session_state.rag is None or current_col != desired_col:
            st.session_state.rag = RAGEngine(collection_name=desired_col)

        # KG 초기화 (한 번만)
        if st.session_state.kg is None:
            st.session_state.kg = KnowledgeGraph()

        return True
    except Exception as e:
        st.error(f"❌ 초기화 실패: {e}")
        return False


# ── CSS 적용 ──────────────────────────────────────────────────────────────────
_apply_theme(_get_theme_color())


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # 도메인 정보 표시
    if st.session_state.domain_config:
        dc = st.session_state.domain_config
        st.markdown(f"# {dc['app_icon']} {dc['app_title']}")
        st.caption(f"*도메인: {dc['name']}*")
    else:
        st.markdown(f"# {APP_ICON} {APP_TITLE}")
        st.caption("*도메인 미설정*")

    st.divider()

    # ── 도메인 설정 (빠른 설정) ──────────────────────────────────────────────
    _domain_set = bool(st.session_state.domain_config)
    with st.expander("⚙️ 도메인 설정", expanded=not _domain_set):
        _sb_company = st.text_input(
            "회사명",
            placeholder="예: 아모레퍼시픽, 한화에너지",
            key="sb_company_name",
        )
        _sb_industry = st.selectbox(
            "업종",
            _INDUSTRY_OPTIONS,
            key="sb_industry",
        )
        _sb_terms = st.text_input(
            "주요 용어 (쉼표로 구분)",
            placeholder="예: SKU, 성분, 충전량",
            key="sb_key_terms",
        )
        if st.button("✅ 도메인 설정 완료", use_container_width=True, key="sb_domain_btn"):
            if not _sb_company.strip():
                st.error("회사명을 입력해주세요.")
            else:
                _new_cfg = _build_domain_config_simple(
                    _sb_company.strip(), _sb_industry, _sb_terms
                )
                st.session_state.domain_config = _new_cfg.to_dict()
                st.session_state.documents = {}
                if st.session_state.kg:
                    st.session_state.kg.clear()
                st.session_state.rag = None  # 재초기화 트리거
                st.rerun()

    st.divider()

    page = st.radio(
        "메뉴",
        [
            "⚙️ 도메인 설정 (고급)",
            "🏠 홈",
            "📄 문서 업로드",
            "🤖 AI 분석",
            "🔍 문서 검색 (RAG)",
            "🕸️ 지식 그래프",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    # 업로드된 문서 목록
    if st.session_state.documents:
        st.markdown("**📁 로드된 문서**")
        for fname in st.session_state.documents:
            char_count = len(st.session_state.documents[fname])
            st.markdown(f"✅ `{fname}` ({char_count:,}자)")
        st.caption(f"총 {len(st.session_state.documents)}개 문서")

        if st.button("🗑️ 전체 초기화", use_container_width=True):
            st.session_state.documents = {}
            if st.session_state.rag:
                st.session_state.rag.delete_collection()
            if st.session_state.kg:
                st.session_state.kg.clear()
            st.rerun()
    else:
        st.info("📂 문서를 업로드해주세요")

    # RAG 상태
    st.divider()
    if st.session_state.rag and st.session_state.documents:
        cnt = st.session_state.rag.document_count()
        st.success(f"🔗 RAG 인덱스: {cnt}개 청크")
    else:
        st.warning("RAG 인덱스 비어있음")


# ════════════════════════════════════════════════════════════════════════════════
# 페이지: 도메인 설정
# ════════════════════════════════════════════════════════════════════════════════
if page == "⚙️ 도메인 설정 (고급)":
    st.title("⚙️ 도메인 설정")
    st.markdown(
        "사용할 도메인을 설명하면 Claude가 해당 도메인의 언어·용어·맥락을 파악하여 "
        "이후 모든 분석을 그 도메인에 맞게 조정합니다."
    )
    st.divider()

    # 현재 설정된 도메인 표시
    if st.session_state.domain_config:
        dc = st.session_state.domain_config
        st.success(f"**현재 도메인:** {dc['app_icon']} {dc['name']}")
        with st.expander("현재 도메인 설정 상세 보기"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**앱 제목:** {dc['app_title']}")
                st.markdown(f"**테마 색상:** `{dc['theme_color']}`")
                st.markdown("**핵심 용어:**")
                st.write(", ".join(dc.get("terminology", [])))
                st.markdown("**주요 문서 유형:**")
                st.write(", ".join(dc.get("document_patterns", [])))
            with col2:
                st.markdown("**분석 포커스:**")
                for focus in dc.get("analysis_focus", []):
                    st.write(f"• {focus}")
                st.markdown("**엔티티 유형:**")
                entity_html = "".join(
                    f'<span class="badge" style="background:{color};color:white">{etype}</span>'
                    for etype, color in dc.get("entity_types", {}).items()
                )
                st.markdown(entity_html, unsafe_allow_html=True)
        st.divider()

    # 도메인 입력 폼
    st.markdown("### 새 도메인 설정")

    # 예시 도메인 빠른 선택
    st.markdown("**예시 도메인 (클릭하면 자동 입력):**")
    example_cols = st.columns(6)
    examples = [
        ("💄 뷰티", "화장품 제조·판매, 원료 소싱, 품질 관리, 트렌드 분석, OEM/ODM 운영"),
        ("⚡ 에너지", "발전소 운영, 설비 점검, 에너지 수급 관리, 탄소중립, 안전 관리"),
        ("🏭 제조", "공장 운영, 생산 계획, 불량률 관리, 공급망, 설비 유지보수"),
        ("🚚 물류", "배송 관리, 창고 운영, 재고 최적화, 라스트마일, 반품 처리"),
        ("💰 금융", "투자 관리, 리스크 분석, 규제 준수, 포트폴리오, 고객 자산"),
        ("🤖 기타", "비즈니스 운영, 전략 기획, 성과 관리, 리스크 관리, 의사결정"),
    ]
    example_domain_name = ""
    example_domain_desc = ""
    for i, (label, desc) in enumerate(examples):
        with example_cols[i % 6]:
            if st.button(label, use_container_width=True, key=f"ex_{i}"):
                example_domain_name = label.split(" ", 1)[1]
                example_domain_desc = desc
                st.session_state["_ex_name"] = example_domain_name
                st.session_state["_ex_desc"] = example_domain_desc

    st.divider()

    domain_name = st.text_input(
        "도메인명 *",
        value=st.session_state.get("_ex_name", ""),
        placeholder="예: 의료, 제조, 금융, 물류, 법률...",
    )
    domain_description = st.text_area(
        "도메인 설명 *",
        value=st.session_state.get("_ex_desc", ""),
        placeholder=(
            "이 도메인에서 다루는 업무, 핵심 용어, 문서 유형 등을 자유롭게 설명해주세요.\n"
            "예: 병원 운영 부서로 환자 입퇴원 관리, 의료진 스케줄링, 의약품 재고 관리, "
            "의료기기 유지보수, 보험 청구 업무를 다룹니다."
        ),
        height=120,
    )

    if st.button("🚀 도메인 분석 시작", use_container_width=True, type="primary"):
        if not domain_name.strip():
            st.error("도메인명을 입력해주세요.")
        elif not domain_description.strip():
            st.error("도메인 설명을 입력해주세요.")
        else:
            if not _load_modules():
                st.stop()

            with st.spinner(f"Claude가 '{domain_name}' 도메인을 분석 중입니다..."):
                from modules.domain_adapter import DomainAdapter
                adapter = DomainAdapter(st.session_state.claude)
                domain_config = adapter.analyze_domain(domain_name.strip(), domain_description.strip())

            st.success("✅ 도메인 분석 완료!")

            # 결과 미리보기
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{domain_config.app_icon} {domain_config.app_title}**")
                st.markdown(f"테마 색상: `{domain_config.theme_color}`")
                st.markdown("**핵심 용어:**")
                st.write(", ".join(domain_config.terminology))
                st.markdown("**주요 문서 유형:**")
                st.write(", ".join(domain_config.document_patterns))
            with col2:
                st.markdown("**분석 포커스:**")
                for focus in domain_config.analysis_focus:
                    st.write(f"• {focus}")
                st.markdown("**엔티티 유형:**")
                entity_html = "".join(
                    f'<span class="badge" style="background:{color};color:white">{etype}</span>'
                    for etype, color in domain_config.entity_types.items()
                )
                st.markdown(entity_html, unsafe_allow_html=True)

            # 도메인 설정 저장
            st.session_state.domain_config = domain_config.to_dict()

            # RAG 컬렉션 초기화 (도메인 변경)
            from modules.rag_engine import RAGEngine
            st.session_state.rag = RAGEngine(collection_name=domain_config.collection_name)
            st.session_state.documents = {}
            if st.session_state.kg:
                st.session_state.kg.clear()

            # 임시 예시 입력 초기화
            for k in ["_ex_name", "_ex_desc"]:
                st.session_state.pop(k, None)

            st.info("도메인이 설정되었습니다. 이제 문서를 업로드하세요.")
            _apply_theme(domain_config.theme_color)
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════════
# 페이지: 홈
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🏠 홈":
    dc = st.session_state.domain_config
    title = f"{dc['app_icon']} {dc['app_title']}" if dc else f"{APP_ICON} {APP_TITLE}"
    st.title(title)
    st.markdown("#### 회의록·운영문서를 AI가 분석해 도메인 맞춤 인사이트를 제공합니다")

    if not dc:
        st.warning("⚙️ 먼저 **도메인 설정** 메뉴에서 도메인을 설정하면 더 정확한 분석이 가능합니다.")

    st.divider()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📄 업로드 문서", len(st.session_state.documents))
    rag_cnt = st.session_state.rag.document_count() if st.session_state.rag else 0
    col2.metric("🔗 RAG 청크", rag_cnt)
    kg_nodes = st.session_state.kg.get_stats()["nodes"] if st.session_state.kg else 0
    kg_edges = st.session_state.kg.get_stats()["edges"] if st.session_state.kg else 0
    col3.metric("🕸️ 그래프 노드", kg_nodes)
    col4.metric("↔️ 그래프 엣지", kg_edges)

    st.divider()

    if dc:
        st.markdown(f"### 현재 도메인: {dc['app_icon']} {dc['name']}")
        st.markdown(
            f'<div class="domain-card">'
            f"<b>분석 포커스:</b> {' · '.join(dc.get('analysis_focus', []))}<br>"
            f"<b>핵심 용어:</b> {', '.join(dc.get('terminology', [])[:8])}"
            f"</div>",
            unsafe_allow_html=True,
        )
        st.divider()

    st.markdown("### 주요 기능")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**⚙️ 도메인 설정**
- 도메인 설명 입력 한 번으로 완전 적응
- Claude가 용어·엔티티·분석 포커스 자동 추출
- 언제든 도메인 전환 가능

**🤖 AI 분석**
- 📋 핵심 요약
- ✅ 액션 아이템 추출
- 🔬 원인 분석 (5-Why)
- 📊 보고서 초안 자동 생성
""")
    with c2:
        st.markdown("""
**📄 문서 업로드**
- PDF, DOCX, TXT/MD 지원
- 자동 청킹 & 벡터 인덱싱
- 멀티 문서 동시 처리

**🔍 문서 검색 (RAG) + 🕸️ 지식 그래프**
- 의미 기반 시맨틱 검색 & 출처 근거 표시
- 도메인 맞춤 엔티티 자동 추출 & 관계 시각화
""")

    st.divider()
    if not dc:
        st.info("👈 먼저 **⚙️ 도메인 설정**을 완료한 뒤 **📄 문서 업로드**를 시작하세요.")
    else:
        st.info("👈 **📄 문서 업로드**를 선택해 분석을 시작하세요.")


# ════════════════════════════════════════════════════════════════════════════════
# 페이지: 문서 업로드
# ════════════════════════════════════════════════════════════════════════════════
elif page == "📄 문서 업로드":
    st.title("📄 문서 업로드")
    st.markdown("회의록, 운영 보고서, 전략 문서를 업로드하면 자동으로 분석 준비됩니다.")
    st.divider()

    if not _load_modules():
        st.stop()

    uploaded = st.file_uploader(
        "파일을 드래그하거나 클릭하여 업로드 (PDF, DOCX, TXT, MD, JSON)",
        type=["pdf", "docx", "txt", "md", "json"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    def _schema_to_text(schema: dict) -> str:
        """스키마 JSON을 RAG 인덱싱용 가독성 텍스트로 변환합니다."""
        lines = []
        for t in schema.get("tables", []):
            lines.append(f"[테이블] {t['table_name']} — {t.get('description', '')}")
            for c in t.get("columns", []):
                pk = " (PK)" if c.get("pk") else ""
                lines.append(
                    f"  컬럼: {c['name']} ({c.get('type', '')}){pk} — {c.get('description', '')}"
                )
        lines.append("")
        for r in schema.get("relationships", []):
            lines.append(
                f"[JOIN] {r['from']} → {r['to']}  키: {r.get('join_key', '')}  ({r.get('relation', 'JOIN')})"
            )
        return "\n".join(lines)

    if uploaded:
        import json as _json
        from modules.document_parser import parse_file

        with st.spinner("문서를 처리 중입니다..."):
            new_files = []
            schema_files = set()  # 스키마 JSON은 Claude 엔티티 추출 생략
            for uf in uploaded:
                if uf.name not in st.session_state.documents:
                    try:
                        if uf.name.lower().endswith(".json"):
                            raw = uf.read().decode("utf-8")
                            data = _json.loads(raw)
                            if "tables" in data and "relationships" in data:
                                # ── 스키마 JSON: 그래프 직접 구성 ────────
                                ok = st.session_state.kg.build_from_schema_json(data)
                                if ok:
                                    stats = st.session_state.kg.get_stats()
                                    st.write(
                                        f"  ✅ `{uf.name}` 스키마 파싱 완료 "
                                        f"→ 노드 {stats['nodes']}개, 엣지 {stats['edges']}개"
                                    )
                                text = _schema_to_text(data)
                                st.session_state.documents[uf.name] = text
                                new_files.append(uf.name)
                                schema_files.add(uf.name)
                            else:
                                st.warning(
                                    f"⚠️ `{uf.name}` — tables/relationships 키가 없는 JSON입니다."
                                )
                        else:
                            text = parse_file(uf)
                            if text.strip():
                                st.session_state.documents[uf.name] = text
                                new_files.append(uf.name)
                            else:
                                st.warning(f"⚠️ `{uf.name}` 에서 텍스트를 추출할 수 없습니다.")
                    except Exception as e:
                        st.error(f"❌ `{uf.name}` 파싱 오류: {e}")

            if new_files:
                # RAG 인덱싱 (스키마 포함 전체)
                st.markdown("#### RAG 인덱싱")
                prog = st.progress(0)
                for i, fname in enumerate(new_files):
                    text = st.session_state.documents[fname]
                    n = st.session_state.rag.add_document(text, fname)
                    prog.progress((i + 1) / len(new_files))
                    st.write(f"  ✅ `{fname}` → {n}개 청크 인덱싱 완료")

                # 지식 그래프 엔티티 추출 (스키마 JSON은 건너뜀)
                non_schema = [f for f in new_files if f not in schema_files]
                if non_schema:
                    st.markdown("#### 지식 그래프 엔티티 추출")
                    from modules.knowledge_graph import build_entity_extraction_prompt

                    if st.session_state.domain_config:
                        from modules.domain_adapter import DomainConfig
                        dc_obj = DomainConfig.from_dict(st.session_state.domain_config)
                        entity_types_desc = dc_obj.get_entity_types_description()
                    else:
                        entity_types_desc = (
                            "- person: 사람, 담당자\n"
                            "- organization: 조직, 팀\n"
                            "- issue: 문제, 이슈\n"
                            "- decision: 결정 사항\n"
                            "- metric: 지표, 수치"
                        )

                    extraction_prompt_template = build_entity_extraction_prompt(entity_types_desc)

                    for fname in non_schema:
                        text = st.session_state.documents[fname]
                        excerpt = text[:3000]
                        with st.spinner(f"  `{fname}` 엔티티 추출 중..."):
                            prompt = extraction_prompt_template.replace("{document}", excerpt)
                            response = st.session_state.claude.generate(prompt, max_tokens=4096)
                            ok = st.session_state.kg.build_from_claude_json(response)
                            if ok:
                                stats = st.session_state.kg.get_stats()
                                st.write(
                                    f"  ✅ `{fname}` → 노드 {stats['nodes']}개, "
                                    f"엣지 {stats['edges']}개"
                                )
                            else:
                                st.write(f"  ⚠️ `{fname}` 엔티티 추출 결과 파싱 실패")

                st.success(f"🎉 {len(new_files)}개 문서 처리 완료!")

    # 문서 미리보기
    if st.session_state.documents:
        st.divider()
        st.markdown("### 📋 업로드된 문서 미리보기")
        sel = st.selectbox("문서 선택", list(st.session_state.documents.keys()))
        if sel:
            preview_text = st.session_state.documents[sel]
            st.text_area(
                f"{sel} (처음 2000자)",
                value=preview_text[:2000],
                height=300,
                disabled=True,
            )
            st.caption(f"전체 길이: {len(preview_text):,}자")


# ════════════════════════════════════════════════════════════════════════════════
# 페이지: AI 분석
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🤖 AI 분석":
    st.title("🤖 AI 분석")

    if not _load_modules():
        st.stop()

    if not st.session_state.documents:
        st.warning("📂 먼저 문서를 업로드해주세요.")
        st.stop()

    domain_context = _get_domain_context()

    # 분석할 문서 선택
    doc_names = list(st.session_state.documents.keys())
    selected = st.selectbox("분석할 문서 선택", ["📚 전체 문서 합치기"] + doc_names)

    if selected == "📚 전체 문서 합치기":
        analysis_text = "\n\n---\n\n".join(
            f"[문서: {k}]\n{v}" for k, v in st.session_state.documents.items()
        )
    else:
        analysis_text = st.session_state.documents[selected]

    MAX_ANALYSIS_CHARS = 8000
    if len(analysis_text) > MAX_ANALYSIS_CHARS:
        st.info(f"ℹ️ 문서가 길어 처음 {MAX_ANALYSIS_CHARS:,}자만 분석합니다.")
        analysis_text = analysis_text[:MAX_ANALYSIS_CHARS]

    st.divider()

    from modules.prompt_loader import load_prompt

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 요약", "✅ 액션 아이템", "🔬 원인 분석", "📊 보고서 초안"]
    )

    # ── 요약 ─────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 핵심 내용 요약")
        st.caption("회의록/운영문서의 핵심을 구조화된 형태로 요약합니다.")
        if st.button("📋 요약 생성", key="btn_summary"):
            with st.spinner("Claude가 요약 중..."):
                prompt = load_prompt(
                    "summarize",
                    document=analysis_text,
                    domain_context=domain_context,
                )
                result = st.session_state.claude.generate(prompt)
            st.markdown(result)
            st.download_button(
                "💾 요약 다운로드",
                data=result,
                file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

    # ── 액션 아이템 ──────────────────────────────────────────────────────────
    with tab2:
        st.markdown("#### 액션 아이템 추출")
        st.caption("문서에서 실행해야 할 작업들을 담당자·기한·우선순위와 함께 추출합니다.")
        if st.button("✅ 액션 아이템 추출", key="btn_action"):
            with st.spinner("Claude가 액션 아이템을 추출 중..."):
                prompt = load_prompt(
                    "action_items",
                    document=analysis_text,
                    domain_context=domain_context,
                )
                result = st.session_state.claude.generate(prompt)
            st.markdown(result)
            st.download_button(
                "💾 액션 아이템 다운로드",
                data=result,
                file_name=f"action_items_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

    # ── 원인 분석 ────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### 원인 분석 (5-Why)")
        st.caption("문서에서 언급된 문제점의 근본 원인을 5-Why 방법론으로 분석합니다.")
        issue_hint = st.text_input(
            "특정 문제 입력 (선택사항)",
            placeholder="예: 시스템 장애 원인 분석 / 납기 지연 원인",
        )
        if st.button("🔬 원인 분석 실행", key="btn_root"):
            text_for_analysis = analysis_text
            if issue_hint:
                text_for_analysis = f"[분석 초점: {issue_hint}]\n\n{analysis_text}"
            with st.spinner("Claude가 원인을 분석 중..."):
                prompt = load_prompt(
                    "root_cause",
                    document=text_for_analysis,
                    domain_context=domain_context,
                )
                result = st.session_state.claude.generate(prompt)
            st.markdown(result)
            st.download_button(
                "💾 원인분석 다운로드",
                data=result,
                file_name=f"root_cause_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )

    # ── 보고서 초안 ──────────────────────────────────────────────────────────
    with tab4:
        st.markdown("#### 경영진 보고서 초안")
        st.caption("문서 내용을 바탕으로 공식 보고서 초안을 자동 생성합니다.")
        report_date = st.date_input("보고서 날짜", value=datetime.today())
        if st.button("📊 보고서 초안 생성", key="btn_report"):
            with st.spinner("Claude가 보고서를 작성 중..."):
                prompt = load_prompt(
                    "report_draft",
                    document=analysis_text,
                    date=report_date.strftime("%Y년 %m월 %d일"),
                    domain_context=domain_context,
                )
                result = st.session_state.claude.generate(prompt)
            st.markdown(result)
            st.download_button(
                "💾 보고서 초안 다운로드",
                data=result,
                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                mime="text/markdown",
            )


# ════════════════════════════════════════════════════════════════════════════════
# 페이지: 문서 검색 (RAG)
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🔍 문서 검색 (RAG)":
    st.title("🔍 문서 검색 (RAG)")
    st.markdown("업로드된 문서에서 의미 기반으로 검색하고, Claude가 출처를 밝혀 답변합니다.")
    st.divider()

    if not _load_modules():
        st.stop()

    if not st.session_state.documents:
        st.warning("📂 먼저 문서를 업로드해주세요.")
        st.stop()

    from modules.prompt_loader import load_prompt

    domain_context = _get_domain_context()

    question = st.text_area(
        "질문을 입력하세요",
        placeholder="업로드한 문서에 대해 자유롭게 질문하세요.",
        height=100,
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        top_k = st.slider("검색 결과 수", 1, 10, 5)
    with col2:
        show_sources = st.checkbox("검색된 청크 원문 보기", value=True)

    if st.button("🔍 검색 & 답변", use_container_width=True) and question.strip():
        with st.spinner("문서 검색 중..."):
            hits = st.session_state.rag.query(question, n_results=top_k)

        if not hits:
            st.warning("검색 결과가 없습니다. 문서를 먼저 업로드해주세요.")
        else:
            context_parts = []
            for i, h in enumerate(hits, 1):
                context_parts.append(f"[출처 {i}: {h['filename']}]\n{h['text']}")
            context = "\n\n---\n\n".join(context_parts)

            with st.spinner("Claude가 답변 생성 중..."):
                prompt = load_prompt(
                    "rag_query",
                    question=question,
                    context=context,
                    domain_context=domain_context,
                )
                answer = st.session_state.claude.generate(prompt)

            st.markdown("### 💬 AI 답변")
            st.markdown(answer)

            if show_sources:
                st.divider()
                st.markdown("### 📎 검색된 문서 청크")
                for i, h in enumerate(hits, 1):
                    with st.expander(
                        f"출처 {i}: `{h['filename']}` (청크 #{h['chunk_index']}, 유사도: {h['score']:.3f})"
                    ):
                        st.write(h["text"])


# ════════════════════════════════════════════════════════════════════════════════
# 페이지: 지식 그래프
# ════════════════════════════════════════════════════════════════════════════════
elif page == "🕸️ 지식 그래프":
    st.title("🕸️ 지식 그래프")
    st.markdown("문서에서 추출된 엔티티와 관계를 인터랙티브 네트워크로 시각화합니다.")
    st.divider()

    if not _load_modules():
        st.stop()

    entity_colors = _get_entity_colors()
    kg = st.session_state.kg
    stats = kg.get_stats()

    # 통계
    c1, c2, c3 = st.columns(3)
    c1.metric("🔵 노드 (엔티티)", stats["nodes"])
    c2.metric("↔️ 엣지 (관계)", stats["edges"])
    c3.metric("📄 분석 문서", len(st.session_state.documents))

    # 엔티티 유형 분포 (도메인 동적 레이블)
    if stats["entity_types"]:
        st.markdown("**엔티티 유형 분포**")
        type_cols = st.columns(min(len(stats["entity_types"]), 4))
        for i, (t, cnt) in enumerate(stats["entity_types"].items()):
            color = entity_colors.get(t, "#9E9E9E")
            label = f"● {t}"
            type_cols[i % 4].metric(label, cnt)

    st.divider()

    if stats["nodes"] == 0:
        st.info("📂 문서를 업로드하면 자동으로 지식 그래프가 생성됩니다.")
    else:
        # 도메인 컬러로 그래프 렌더링
        html_path = kg.render_html(entity_colors=entity_colors)
        if html_path and os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=600, scrolling=False)
        else:
            st.error("그래프 렌더링 실패")

        # 특정 문서 재분석
        st.divider()
        st.markdown("### 🔄 특정 문서 그래프 재추출")
        if st.session_state.documents:
            sel_doc = st.selectbox(
                "재분석할 문서",
                list(st.session_state.documents.keys()),
                key="kg_doc_sel",
            )
            if st.button("🔄 엔티티 재추출", key="btn_reextract"):
                from modules.knowledge_graph import build_entity_extraction_prompt

                if st.session_state.domain_config:
                    from modules.domain_adapter import DomainConfig
                    dc_obj = DomainConfig.from_dict(st.session_state.domain_config)
                    entity_types_desc = dc_obj.get_entity_types_description()
                else:
                    entity_types_desc = (
                        "- person: 사람, 담당자\n"
                        "- organization: 조직, 팀\n"
                        "- issue: 문제, 이슈\n"
                        "- decision: 결정 사항\n"
                        "- metric: 지표, 수치"
                    )

                text = st.session_state.documents[sel_doc][:3000]
                with st.spinner(f"`{sel_doc}` 엔티티 추출 중..."):
                    prompt_template = build_entity_extraction_prompt(entity_types_desc)
                    prompt = prompt_template.replace("{document}", text)
                    response = st.session_state.claude.generate(prompt, max_tokens=4096)
                    ok = kg.build_from_claude_json(response)
                if ok:
                    st.success(f"✅ 재추출 완료! 노드 {kg.get_stats()['nodes']}개")
                    st.rerun()
                else:
                    st.error("엔티티 추출 결과 파싱 실패")
                    with st.expander("Claude 원본 응답"):
                        st.text(response)

    # 색상 범례 (도메인 동적)
    st.divider()
    st.markdown("**노드 색상 범례**")
    legend_html = "".join(
        f'<span class="badge" style="background:{color};color:white">{etype}</span>'
        for etype, color in entity_colors.items()
        if etype != "default"
    )
    st.markdown(legend_html, unsafe_allow_html=True)
