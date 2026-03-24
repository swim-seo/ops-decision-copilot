"""
뷰티 AI 운영 코파일럿
회의록·운영문서 → RAG 검색 + 지식그래프 + AI 분석 (요약/액션/원인/보고서)
"""
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components

from config import APP_TITLE, APP_ICON, COMPANY_NAME, ENTITY_COLORS

# ── 페이지 설정 (반드시 최상단) ─────────────────────────────────────────────────
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS 테마 (뷰티 핑크) ──────────────────────────────────────────────────────
st.markdown(
    """
<style>
    /* 배경 */
    .main { background-color: #fff5f8; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg,#fce4ec,#f8bbd0); }

    /* 버튼 */
    .stButton>button {
        background: linear-gradient(135deg,#e91e8c,#c2185b);
        color: white; border: none; border-radius: 24px;
        padding: 0.5rem 1.4rem; font-weight: 600;
        transition: all .2s;
    }
    .stButton>button:hover { opacity:.88; transform:translateY(-1px); }

    /* 헤더 */
    h1,h2,h3 { color: #880e4f !important; }

    /* 메트릭 카드 */
    div[data-testid="metric-container"] {
        background: white;
        border: 1px solid #f8bbd0;
        border-left: 4px solid #e91e8c;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(233,30,140,.1);
    }

    /* 탭 */
    .stTabs [data-baseweb="tab"] { color: #c2185b; font-weight: 600; }
    .stTabs [aria-selected="true"] { border-bottom: 3px solid #e91e8c; }

    /* 업로드 박스 */
    [data-testid="stFileUploader"] {
        border: 2px dashed #f48fb1;
        border-radius: 12px;
        padding: .5rem;
        background: #fff;
    }

    /* 범례 뱃지 */
    .badge {
        display:inline-block; padding:3px 10px;
        border-radius:20px; font-size:.78em; font-weight:700;
        margin:2px;
    }
</style>
""",
    unsafe_allow_html=True,
)


# ── 세션 스테이트 초기화 ──────────────────────────────────────────────────────
def _init_session():
    if "documents" not in st.session_state:
        st.session_state.documents = {}  # {filename: text}
    if "rag_ready" not in st.session_state:
        st.session_state.rag_ready = False
    if "rag" not in st.session_state:
        st.session_state.rag = None
    if "claude" not in st.session_state:
        st.session_state.claude = None
    if "kg" not in st.session_state:
        st.session_state.kg = None
    if "api_ok" not in st.session_state:
        st.session_state.api_ok = False


_init_session()


# ── 모듈 지연 로딩 (API 키 확인 후) ──────────────────────────────────────────
def _load_modules():
    """모듈을 처음 필요할 때 한 번만 초기화합니다."""
    if st.session_state.claude is not None:
        return True
    try:
        from modules.claude_client import ClaudeClient
        from modules.rag_engine import RAGEngine
        from modules.knowledge_graph import KnowledgeGraph

        st.session_state.claude = ClaudeClient()
        st.session_state.rag = RAGEngine()
        st.session_state.kg = KnowledgeGraph()
        st.session_state.api_ok = True
        return True
    except Exception as e:
        st.error(f"❌ 초기화 실패: {e}")
        return False


# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"# {APP_ICON} {APP_TITLE}")
    st.caption(f"*{COMPANY_NAME} 운영 지원 AI*")
    st.divider()

    page = st.radio(
        "메뉴",
        [
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
# 페이지: 홈
# ════════════════════════════════════════════════════════════════════════════════
if page == "🏠 홈":
    st.title(f"{APP_ICON} {APP_TITLE}")
    st.markdown("#### 회의록·운영문서를 AI가 분석해 인사이트를 제공합니다")
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
    st.markdown("### 주요 기능")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
**📄 문서 업로드**
- PDF, DOCX, TXT/MD 지원
- 자동 청킹 & 벡터 인덱싱
- 멀티 문서 동시 처리

**🤖 AI 분석**
- 📋 핵심 요약
- ✅ 액션 아이템 추출
- 🔬 원인 분석 (5-Why)
- 📊 보고서 초안 자동 생성
""")
    with c2:
        st.markdown("""
**🔍 문서 검색 (RAG)**
- 의미 기반 시맨틱 검색
- 멀티 문서 교차 검색
- 출처 근거 표시

**🕸️ 지식 그래프**
- 엔티티 자동 추출
- 관계 시각화
- 인터랙티브 네트워크 뷰
""")

    st.divider()
    st.info("👈 왼쪽 메뉴에서 **📄 문서 업로드**를 선택해 시작하세요.")


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
        "파일을 드래그하거나 클릭하여 업로드 (PDF, DOCX, TXT, MD)",
        type=["pdf", "docx", "txt", "md"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        from modules.document_parser import parse_file

        with st.spinner("문서를 처리 중입니다..."):
            new_files = []
            for uf in uploaded:
                if uf.name not in st.session_state.documents:
                    try:
                        text = parse_file(uf)
                        if text.strip():
                            st.session_state.documents[uf.name] = text
                            new_files.append(uf.name)
                        else:
                            st.warning(f"⚠️ `{uf.name}` 에서 텍스트를 추출할 수 없습니다.")
                    except Exception as e:
                        st.error(f"❌ `{uf.name}` 파싱 오류: {e}")

            if new_files:
                # RAG 인덱싱
                st.markdown("#### RAG 인덱싱")
                prog = st.progress(0)
                for i, fname in enumerate(new_files):
                    text = st.session_state.documents[fname]
                    n = st.session_state.rag.add_document(text, fname)
                    prog.progress((i + 1) / len(new_files))
                    st.write(f"  ✅ `{fname}` → {n}개 청크 인덱싱 완료")

                # 지식 그래프 업데이트
                st.markdown("#### 지식 그래프 엔티티 추출")
                from modules.knowledge_graph import ENTITY_EXTRACTION_PROMPT

                for fname in new_files:
                    text = st.session_state.documents[fname]
                    excerpt = text[:3000]  # 첫 3000자만 사용
                    with st.spinner(f"  `{fname}` 엔티티 추출 중..."):
                        prompt = ENTITY_EXTRACTION_PROMPT.replace("{document}", excerpt)
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

    # 분석할 문서 선택
    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
        doc_names = list(st.session_state.documents.keys())
        options = ["📚 전체 문서 합치기"] + doc_names
        selected = st.selectbox("분석할 문서 선택", options)

    if selected == "📚 전체 문서 합치기":
        analysis_text = "\n\n---\n\n".join(
            f"[문서: {k}]\n{v}" for k, v in st.session_state.documents.items()
        )
    else:
        analysis_text = st.session_state.documents[selected]

    # 텍스트 길이 제한 (API 토큰 제한 대비)
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
                prompt = load_prompt("summarize", document=analysis_text)
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
                prompt = load_prompt("action_items", document=analysis_text)
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
            placeholder="예: 신제품 출시 지연 원인 분석",
        )
        if st.button("🔬 원인 분석 실행", key="btn_root"):
            text_for_analysis = analysis_text
            if issue_hint:
                text_for_analysis = f"[분석 초점: {issue_hint}]\n\n{analysis_text}"
            with st.spinner("Claude가 원인을 분석 중..."):
                prompt = load_prompt("root_cause", document=text_for_analysis)
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

    question = st.text_area(
        "질문을 입력하세요",
        placeholder="예: 3월 캠페인 예산이 얼마인가요? / 신제품 출시 일정은? / 주요 이슈가 뭔가요?",
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
            # 컨텍스트 조합
            context_parts = []
            for i, h in enumerate(hits, 1):
                context_parts.append(f"[출처 {i}: {h['filename']}]\n{h['text']}")
            context = "\n\n---\n\n".join(context_parts)

            # Claude 답변
            with st.spinner("Claude가 답변 생성 중..."):
                prompt = load_prompt("rag_query", question=question, context=context)
                answer = st.session_state.claude.generate(prompt)

            st.markdown("### 💬 AI 답변")
            st.markdown(answer)

            # 검색된 청크 표시
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

    kg = st.session_state.kg
    stats = kg.get_stats()

    # 통계
    c1, c2, c3 = st.columns(3)
    c1.metric("🔵 노드 (엔티티)", stats["nodes"])
    c2.metric("↔️ 엣지 (관계)", stats["edges"])
    c3.metric("📄 분석 문서", len(st.session_state.documents))

    # 엔티티 유형 분포
    if stats["entity_types"]:
        st.markdown("**엔티티 유형 분포**")
        type_cols = st.columns(min(len(stats["entity_types"]), 4))
        type_labels = {
            "person": "👤 사람",
            "product": "🧴 제품",
            "brand": "🏷️ 브랜드",
            "department": "🏢 부서",
            "campaign": "📣 캠페인",
            "issue": "⚠️ 이슈",
            "decision": "✅ 결정",
            "ingredient": "🌿 성분",
            "metric": "📊 지표",
            "default": "❓ 기타",
        }
        for i, (t, cnt) in enumerate(stats["entity_types"].items()):
            type_cols[i % 4].metric(type_labels.get(t, t), cnt)

    st.divider()

    if stats["nodes"] == 0:
        st.info("📂 문서를 업로드하면 자동으로 지식 그래프가 생성됩니다.")
    else:
        # 그래프 렌더링
        html_path = kg.render_html()
        if html_path and os.path.exists(html_path):
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            components.html(html_content, height=600, scrolling=False)
        else:
            st.error("그래프 렌더링 실패")

        # 개별 문서 재분석
        st.divider()
        st.markdown("### 🔄 특정 문서 그래프 재추출")
        if st.session_state.documents:
            sel_doc = st.selectbox(
                "재분석할 문서",
                list(st.session_state.documents.keys()),
                key="kg_doc_sel",
            )
            if st.button("🔄 엔티티 재추출", key="btn_reextract"):
                from modules.knowledge_graph import ENTITY_EXTRACTION_PROMPT

                text = st.session_state.documents[sel_doc][:3000]
                with st.spinner(f"`{sel_doc}` 엔티티 추출 중..."):
                    prompt = ENTITY_EXTRACTION_PROMPT.replace("{document}", text)
                    response = st.session_state.claude.generate(prompt, max_tokens=4096)
                    ok = kg.build_from_claude_json(response)
                if ok:
                    st.success(f"✅ 재추출 완료! 노드 {kg.get_stats()['nodes']}개")
                    st.rerun()
                else:
                    st.error("엔티티 추출 결과 파싱 실패")
                    with st.expander("Claude 원본 응답"):
                        st.text(response)

    # 색상 범례
    st.divider()
    st.markdown("**노드 색상 범례**")
    legend_items = {
        "person": "👤 사람/담당자",
        "product": "🧴 제품",
        "brand": "🏷️ 브랜드",
        "department": "🏢 부서/팀",
        "campaign": "📣 캠페인",
        "issue": "⚠️ 이슈/문제",
        "decision": "✅ 결정사항",
        "ingredient": "🌿 원료/성분",
        "metric": "📊 지표/KPI",
    }
    legend_html = "".join(
        f'<span class="badge" style="background:{ENTITY_COLORS[k]};color:white">'
        f"{v}</span>"
        for k, v in legend_items.items()
    )
    st.markdown(legend_html, unsafe_allow_html=True)
